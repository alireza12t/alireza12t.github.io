#!/usr/bin/env python3
"""
Set the owner login for the booking admin (the Booking tab of /admin/ on the site).

Asks for a password (never echoed), makes a new authenticator (TOTP) key,
checks one code from your app, then writes SecureString params to SSM:
  /booking/admin_password_hash   scrypt hash, not the password itself
  /booking/admin_totp_secret     the authenticator key
  /booking/admin_session_key     signs login sessions; a new one logs every session out

Nothing is printed to a file or committed. The Lambda picks up changes within 5 minutes.

Usage (needs the AWS CLI signed in to the booking account):
    python3 scripts/setup_booking_admin.py               # all three (first setup)
    python3 scripts/setup_booking_admin.py --password    # change only the password
    python3 scripts/setup_booking_admin.py --totp        # new authenticator only (lost phone)
    python3 scripts/setup_booking_admin.py --logout-all  # new session key only
"""

import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse

REGION = "us-east-1"
PASSWORD_PARAM = "/booking/admin_password_hash"
TOTP_PARAM = "/booking/admin_totp_secret"
SESSION_PARAM = "/booking/admin_session_key"


# Same formats as _hash_password / _totp in lambda/handler.py (a test keeps them in step)
def hash_password(password, n=2**14, r=8, p=1):
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=32)
    return f"scrypt${n}${r}${p}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def new_totp_secret():
    return base64.b32encode(os.urandom(20)).decode().rstrip("=")


def totp(secret_b32, counter):
    key = base64.b32decode(secret_b32.upper() + "=" * (-len(secret_b32) % 8))
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{code:06d}"


def put_secret(name, value):
    """Write via a 0600 temp file so the value never shows up in `ps` or shell history."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "param.json")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump({"Name": name, "Value": value, "Type": "SecureString", "Overwrite": True}, f)
        subprocess.run(
            ["aws", "ssm", "put-parameter", "--region", REGION, "--cli-input-json", f"file://{path}"],
            check=True, stdout=subprocess.DEVNULL,
        )
    print(f"  saved {name}")


def ask_password():
    while True:
        pw = getpass.getpass("New admin password (12+ characters): ")
        if len(pw) < 12:
            print("  Too short.")
            continue
        if getpass.getpass("Again: ") != pw:
            print("  They don't match.")
            continue
        return pw


def setup_totp():
    secret = new_totp_secret()
    uri = "otpauth://totp/{}?{}".format(
        urllib.parse.quote("alireza12t.github.io:booking admin"),
        urllib.parse.urlencode({"secret": secret, "issuer": "alireza12t.github.io"}),
    )
    print("\nAdd this to your authenticator app (Passwords, 1Password, Google Authenticator...).")
    if shutil.which("qrencode"):
        subprocess.run(["qrencode", "-t", "ANSIUTF8", uri], check=False)
    else:
        print("  (brew install qrencode to get a QR code here)")
    print("  Setup key: " + " ".join(secret[i:i + 4] for i in range(0, len(secret), 4)))
    print("  Type: time based, 6 digits, 30 seconds\n")
    while True:
        code = input("Code from the app, to check it: ").strip().replace(" ", "")
        step = int(time.time() // 30)
        if any(hmac.compare_digest(totp(secret, c), code) for c in (step - 1, step, step + 1)):
            return secret
        print("  That code doesn't match. Check the key and the phone's clock, then try again.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--password", action="store_true", help="change only the password")
    ap.add_argument("--totp", action="store_true", help="new authenticator key only")
    ap.add_argument("--logout-all", action="store_true", help="new session key only")
    args = ap.parse_args()
    everything = not (args.password or args.totp or args.logout_all)

    if not shutil.which("aws"):
        sys.exit("The AWS CLI is not installed.")

    password_hash = hash_password(ask_password()) if everything or args.password else None
    totp_secret = setup_totp() if everything or args.totp else None

    print("\nWriting to SSM...")
    if password_hash:
        put_secret(PASSWORD_PARAM, password_hash)
    if totp_secret:
        put_secret(TOTP_PARAM, totp_secret)
    if everything or args.logout_all:
        put_secret(SESSION_PARAM, base64.b64encode(os.urandom(32)).decode())
    print("Done. Log in at https://alireza12t.github.io/admin/ (changes apply within 5 minutes).")


if __name__ == "__main__":
    main()
