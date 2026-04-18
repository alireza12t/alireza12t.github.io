"""
Get a Google OAuth refresh token with calendar.events scope.

Credentials are read from environment variables — never hardcoded. Your
personal values live in SECRETS.md (which is gitignored).

Usage:
    # one-time setup:
    python3 -m venv .venv
    source .venv/bin/activate
    pip install google-auth-oauthlib

    # run — export creds first (from SECRETS.md) or use a .env loader
    export GOOGLE_CLIENT_ID='...'
    export GOOGLE_CLIENT_SECRET='...'
    python scripts/get_refresh_token.py

The script opens your browser, asks you to consent, and prints the refresh
token. Store that token in AWS SSM Parameter Store as a SecureString at
`/booking/google_refresh_token` — do NOT paste it into any tracked file.
"""
import os
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit("install first:  pip install google-auth-oauthlib")

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    sys.exit(
        "error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set as env vars.\n"
        "copy them from SECRETS.md (gitignored), then re-run:\n"
        "    export GOOGLE_CLIENT_ID='...'\n"
        "    export GOOGLE_CLIENT_SECRET='...'\n"
    )

# calendar.events lets us CREATE events with Meet links — broader than calendar.readonly
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    },
    scopes=SCOPES,
)

# prompt="consent" forces a fresh refresh_token even if one already exists
creds = flow.run_local_server(
    port=0,
    access_type="offline",
    prompt="consent",
)

print()
print("=" * 60)
print("NEW REFRESH TOKEN (calendar.events scope):")
print(creds.refresh_token)
print("=" * 60)
print()
print("Next: push it into SSM (never commit it) with:")
print('  aws ssm put-parameter \\')
print('    --name /booking/google_refresh_token \\')
print('    --type SecureString \\')
print('    --overwrite \\')
print('    --value "<paste-token>" \\')
print('    --region us-east-1')
