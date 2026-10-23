"""
Booking backend — AWS Lambda (Python 3.12) behind a Function URL.

Secrets model:
  - All real secrets (client_secret, refresh_token) live in SSM Parameter Store
    as SecureString params, fetched at cold start and cached.
  - GOOGLE_CLIENT_ID is a plain Lambda env var (not a secret — it's exposed in
    the OAuth redirect flow anyway).
  - Nothing sensitive is ever baked into this file or any file that ships to
    the repo.

Flow:
  1. Receive {slot_iso, duration_min, name, email} POST from the website.
  2. Validate input.
  3. Conditional DynamoDB put on the slot — fails if someone already grabbed it.
  4. Exchange refresh_token -> access_token via Google OAuth token endpoint.
  5. Create a Google Calendar event with conferenceData (Meet link) + invites.
  6. Return {ok: true, meet_link, event_id} to the website.

Env vars (non-secret):
  GOOGLE_CLIENT_ID             — OAuth client id
  SSM_CLIENT_SECRET_PARAM      — default "/booking/google_client_secret"
  SSM_REFRESH_TOKEN_PARAM      — default "/booking/google_refresh_token"
  HOST_EMAIL                   — Alireza's calendar email
  HOST_NAME                    — e.g. "Alireza Toghiani"
  TIMEZONE                     — e.g. "America/Toronto"
  DDB_TABLE                    — "bookings"
  ALLOWED_ORIGIN               — "https://alireza12t.github.io"

Owner admin (/admin/*, used by the website's /admin/ page):
  POST /admin/login     {password, code} -> {token}. Password is checked against
                        an scrypt hash and code against a TOTP secret, both in SSM.
                        5 failures lock logins for 15 min; each code works once.
  GET  /admin/bookings  upcoming bookings and owner blocks
  POST /admin/cancel    {slot_iso} deletes the Google event (guest is emailed) and frees the slot
  POST /admin/block     {start_date, end_date, start_time?, end_time?, note?} hides those times
  POST /admin/unblock   {id}
  Every route but login needs "Authorization: Bearer <token>": an HMAC-signed,
  8-hour token keyed by /booking/admin_session_key. A header, not a cookie,
  because the site and this Function URL are different sites (Safari drops
  third-party cookies), and it means no CSRF.

No third-party deps — only stdlib + boto3 (always available in Lambda runtime).
"""

import base64
import hashlib
import hmac
import json
import os
import struct
import time
import uuid
import re
import urllib.parse
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import boto3
from botocore.exceptions import ClientError

# --- non-secret config (env vars) ---
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
SSM_CLIENT_SECRET_PARAM = os.environ.get("SSM_CLIENT_SECRET_PARAM", "/booking/google_client_secret")
SSM_REFRESH_TOKEN_PARAM = os.environ.get("SSM_REFRESH_TOKEN_PARAM", "/booking/google_refresh_token")
SSM_GITHUB_PAT_PARAM = os.environ.get("SSM_GITHUB_PAT_PARAM", "/booking/github_pat")
SSM_REFRESH_KEY_PARAM = os.environ.get("SSM_REFRESH_KEY_PARAM", "/booking/refresh_key")
SSM_TELEGRAM_TOKEN_PARAM = os.environ.get("SSM_TELEGRAM_TOKEN_PARAM", "/booking/telegram_bot_token")
SSM_TELEGRAM_CHAT_PARAM = os.environ.get("SSM_TELEGRAM_CHAT_PARAM", "/booking/telegram_chat_id")
GH_OWNER = "alireza12t"
GH_REPO  = "alireza12t.github.io"
GH_WORKFLOW = "update-running-dashboard.yml"
HOST_EMAIL = os.environ.get("HOST_EMAIL", "alireza.toghiani@icloud.com")
HOST_NAME = os.environ.get("HOST_NAME", "Alireza Toghiani")
TIMEZONE = os.environ.get("TIMEZONE", "America/Toronto")
DDB_TABLE = os.environ.get("DDB_TABLE", "bookings")

SSM_ADMIN_PASSWORD_PARAM = os.environ.get("SSM_ADMIN_PASSWORD_PARAM", "/booking/admin_password_hash")
SSM_ADMIN_TOTP_PARAM = os.environ.get("SSM_ADMIN_TOTP_PARAM", "/booking/admin_totp_secret")
SSM_ADMIN_SESSION_PARAM = os.environ.get("SSM_ADMIN_SESSION_PARAM", "/booking/admin_session_key")

SESSION_TTL = 8 * 3600
MAX_LOGIN_FAILS = 5
LOCK_SECONDS = 15 * 60
ADMIN_SECRET_TTL = 300   # re-read admin secrets every 5 min so a password change applies without a deploy
SLOT_MIN = 30            # booking grid; owner blocks hide every slot start on it
BLOCK_HORIZON_DAYS = 90
# Rows in the bookings table that are not bookings. Their keys sort before any
# date, and _is_booking() skips them.
AUTH_KEY = "admin#auth"  # login throttling + last used TOTP step
BLOCK_PREFIX = "block#"

TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_URL = (
    "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    "?conferenceDataVersion=1&sendUpdates=all"
)

EVENT_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events/{}?sendUpdates=all"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_ssm = boto3.client("ssm")
_ddb = boto3.resource("dynamodb").Table(DDB_TABLE)

# cached across warm invocations
_secret_cache = {}


def _get_secret(param_name):
    if param_name not in _secret_cache:
        resp = _ssm.get_parameter(Name=param_name, WithDecryption=True)
        _secret_cache[param_name] = resp["Parameter"]["Value"]
    return _secret_cache[param_name]


def _response(status, body, no_store=False):
    # CORS headers are handled by the Function URL config — don't duplicate them here
    headers = {"Content-Type": "application/json"}
    if no_store:
        headers["Cache-Control"] = "no-store"
    return {
        "statusCode": status,
        "headers": headers,
        "body": json.dumps(body),
    }


def _json_body(event):
    """The request body as a dict, or None if it isn't a JSON object."""
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[booking] invalid JSON body: {raw[:200]}")
        return None
    return payload if isinstance(payload, dict) else None


def _alert(text):
    """Best-effort Telegram alert. Never raises: an alert must not break a booking."""
    try:
        token = _get_secret(SSM_TELEGRAM_TOKEN_PARAM)
        chat_id = _get_secret(SSM_TELEGRAM_CHAT_PARAM)
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST"
        )
        urllib.request.urlopen(req, timeout=5).close()
    except Exception as e:
        print(f"[booking] telegram alert failed: {e!r}")


def _format_slot(start_iso, end_iso, tz_name):
    """'Fri, Oct 16 · 10:00–10:30 AM' in the given timezone."""
    tz = ZoneInfo(tz_name)
    start = datetime.fromisoformat(start_iso).astimezone(tz)
    end = datetime.fromisoformat(end_iso).astimezone(tz)
    def t(d):
        return d.strftime("%I:%M").lstrip("0")
    return f"{start:%a, %b} {start.day} · {t(start)}–{t(end)} {end:%p}"


def _booking_failed_alert(parsed, error):
    lines = [
        "🔴 Booking failed — book this call manually",
        f"👤 {parsed['name']} <{parsed['email']}>",
        f"🕒 {_format_slot(parsed['slot_iso'], parsed['end_iso'], TIMEZONE)} ({TIMEZONE})",
    ]
    if parsed.get("visitor_tz") and parsed["visitor_tz"] != TIMEZONE:
        lines.append(
            f"🌍 Their time: {_format_slot(parsed['slot_iso'], parsed['end_iso'], parsed['visitor_tz'])}"
            f" ({parsed['visitor_tz']})"
        )
    lines += [
        f"⏱ {parsed['duration_min']} min · UTC {parsed['slot_iso']}",
        f"Error: {error!r}",
        "If this is invalid_grant, the Google refresh token expired.",
    ]
    return "\n".join(lines)


def _get_access_token():
    data = urllib.parse.urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": _get_secret(SSM_CLIENT_SECRET_PARAM),
        "refresh_token": _get_secret(SSM_REFRESH_TOKEN_PARAM),
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())["access_token"]
    except urllib.error.HTTPError as e:
        # Google explains the failure in the body, e.g. {"error": "invalid_grant"}
        body = e.read().decode(errors="replace")[:300]
        raise RuntimeError(f"Google token exchange failed ({e.code}): {body}") from e


def _create_calendar_event(access_token, start_iso, end_iso, visitor_name, visitor_email):
    body = {
        "summary": f"Call with {visitor_name}",
        "description": f"Booked via alireza12t.github.io by {visitor_name} <{visitor_email}>.",
        "start": {"dateTime": start_iso, "timeZone": TIMEZONE},
        "end": {"dateTime": end_iso, "timeZone": TIMEZONE},
        "attendees": [
            {"email": HOST_EMAIL, "displayName": HOST_NAME, "organizer": True},
            {"email": visitor_email, "displayName": visitor_name},
        ],
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        "reminders": {"useDefault": True},
    }
    req = urllib.request.Request(
        CALENDAR_URL,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def _validate(payload):
    slot_iso = payload.get("slot_iso")
    duration_min = payload.get("duration_min", 30)
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()

    if not slot_iso or not isinstance(slot_iso, str):
        return None, "missing slot_iso"
    if not isinstance(duration_min, int) or not (5 <= duration_min <= 240):
        return None, "bad duration_min"
    if not name or len(name) > 100:
        return None, "missing or too-long name"
    if not EMAIL_RE.match(email) or len(email) > 150:
        return None, "bad email"
    try:
        start_dt = datetime.fromisoformat(slot_iso)
    except ValueError:
        return None, "slot_iso must be ISO-8601"
    if start_dt.tzinfo is None:
        return None, "slot_iso must include a timezone offset"
    if start_dt < datetime.now(timezone.utc) - timedelta(minutes=1):
        return None, "slot is in the past"
    end_dt = start_dt + timedelta(minutes=duration_min)
    # Optional: only used to tell the host the visitor's local time
    visitor_tz = payload.get("visitor_tz")
    if not isinstance(visitor_tz, str) or len(visitor_tz) > 64:
        visitor_tz = None
    else:
        try:
            ZoneInfo(visitor_tz)
        except (ZoneInfoNotFoundError, ValueError):
            visitor_tz = None
    return {
        "slot_iso": start_dt.isoformat(),
        "end_iso": end_dt.isoformat(),
        "duration_min": duration_min,
        "name": name,
        "email": email,
        "visitor_tz": visitor_tz,
    }, None


def _reserve_slot(slot_iso, visitor_name, visitor_email, duration_min=30):
    now = int(time.time())
    try:
        _ddb.put_item(
            Item={
                "slot_iso": slot_iso,
                "visitor_name": visitor_name,
                "visitor_email": visitor_email,
                "created_at": now,
                "duration_min": duration_min,
                "status": "pending",
            },
            ConditionExpression="attribute_not_exists(slot_iso)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def _mark_booked(slot_iso, event_id, meet_link):
    _ddb.update_item(
        Key={"slot_iso": slot_iso},
        UpdateExpression="SET #s = :s, event_id = :e, meet_link = :m",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "booked",
            ":e": event_id,
            ":m": meet_link,
        },
    )


def _release_slot(slot_iso):
    try:
        _ddb.delete_item(Key={"slot_iso": slot_iso})
    except Exception:
        pass


def _scan_all():
    items, kwargs = [], {}
    while True:
        resp = _ddb.scan(**kwargs)
        items += resp.get("Items", [])
        if "LastEvaluatedKey" not in resp:
            return items
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def _is_block(item):
    return item.get("slot_iso", "").startswith(BLOCK_PREFIX)


def _is_booking(item):
    return not item.get("slot_iso", "").startswith((BLOCK_PREFIX, "admin#"))


def _iso_z(dt):
    """Same string as the browser's Date.toISOString(), which booking.html compares against."""
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _block_slot_starts(block, now):
    """Every grid slot start overlapping the block, from now to the horizon."""
    start = max(datetime.fromisoformat(block["start_utc"]), now)
    end = min(datetime.fromisoformat(block["end_utc"]), now + timedelta(days=BLOCK_HORIZON_DAYS))
    s = start.replace(second=0, microsecond=0)
    s -= timedelta(minutes=s.minute % SLOT_MIN)
    while s < end:
        yield s
        s += timedelta(minutes=SLOT_MIN)


def _get_booked_slots():
    """Upcoming taken slot starts so the frontend can hide them: real bookings
    plus every slot inside an owner block."""
    now = datetime.now(timezone.utc)
    try:
        items = _scan_all()
    except Exception as e:
        print(f"scan error: {e!r}")
        return []
    slots = set()
    for item in items:
        try:
            if _is_block(item):
                slots.update(_iso_z(s) for s in _block_slot_starts(item, now))
            elif _is_booking(item):
                start = datetime.fromisoformat(item["slot_iso"])
                if start > now:
                    slots.add(_iso_z(start))
        except (KeyError, ValueError, TypeError) as e:
            print(f"[booking] skipping bad row {item.get('slot_iso')!r}: {e!r}")
    return sorted(slots)


def _in_owner_block(start_iso, end_iso):
    """True if [start, end) overlaps an owner block. A failed scan never blocks a booking."""
    start, end = datetime.fromisoformat(start_iso), datetime.fromisoformat(end_iso)
    try:
        blocks = [i for i in _scan_all() if _is_block(i)]
        return any(
            datetime.fromisoformat(b["start_utc"]) < end and datetime.fromisoformat(b["end_utc"]) > start
            for b in blocks
        )
    except Exception as e:
        print(f"[booking] block check failed: {e!r}")
        return False


def _handle_run_refresh(event):
    """Trigger the GitHub Actions dashboard-update workflow."""
    key = (event.get("headers") or {}).get("x-refresh-key", "")
    try:
        expected = _get_secret(SSM_REFRESH_KEY_PARAM)
    except Exception:
        return _response(500, {"error": "refresh_key_not_configured"})
    if not key or key != expected:
        return _response(403, {"error": "forbidden"})

    try:
        pat = _get_secret(SSM_GITHUB_PAT_PARAM)
    except Exception:
        return _response(500, {"error": "github_pat_not_configured"})
    if pat == "PLACEHOLDER":
        return _response(500, {"error": "github_pat_not_set — run: aws ssm put-parameter --name /booking/github_pat --type SecureString --value YOUR_PAT --overwrite"})

    body = json.dumps({"ref": "master"}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/actions/workflows/{GH_WORKFLOW}/dispatches",
        data=body,
        headers={
            "Authorization": f"Bearer {pat}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "misfit-dashboard-lambda",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    if status == 204:
        return _response(200, {"ok": True})
    return _response(status, {"error": f"github_api_{status}"})


# --- owner admin ---------------------------------------------------------------

_admin_secret_cache = {}


def _get_admin_secret(param_name):
    hit = _admin_secret_cache.get(param_name)
    if hit and time.time() - hit[1] < ADMIN_SECRET_TTL:
        return hit[0]
    resp = _ssm.get_parameter(Name=param_name, WithDecryption=True)
    value = resp["Parameter"]["Value"]
    _admin_secret_cache[param_name] = (value, time.time())
    return value


def _hash_password(password, salt=None, n=2**14, r=8, p=1):
    """'scrypt$n$r$p$salt$hash'. scripts/setup_booking_admin.py writes the same format."""
    salt = salt or os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=32)
    return f"scrypt${n}${r}${p}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def _check_password(password, stored):
    try:
        algo, n, r, p, salt, want = stored.split("$")
        if algo != "scrypt":
            return False
        want = base64.b64decode(want)
        dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt),
                            n=int(n), r=int(r), p=int(p), dklen=len(want))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk, want)


def _totp(secret_b32, counter):
    """RFC 6238 code (SHA-1, 6 digits) for one 30-second step."""
    key = base64.b32decode(secret_b32.strip().upper() + "=" * (-len(secret_b32.strip()) % 8))
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{code:06d}"


def _match_totp(secret_b32, code, now):
    """The step the code belongs to (allowing one step of clock drift), or None."""
    if not re.fullmatch(r"\d{6}", code or ""):
        return None
    step = int(now // 30)
    for counter in (step - 1, step, step + 1):
        if hmac.compare_digest(_totp(secret_b32, counter), code):
            return counter
    return None


def _b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _unb64url(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload):
    key = _get_admin_secret(SSM_ADMIN_SESSION_PARAM).encode()
    return _b64url(hmac.new(key, payload.encode(), hashlib.sha256).digest())


def _make_token(now):
    payload = _b64url(json.dumps({"sub": "owner", "exp": int(now) + SESSION_TTL}).encode())
    return f"{payload}.{_sign(payload)}"


def _token_valid(token, now):
    try:
        payload, sig = token.split(".")
        if not hmac.compare_digest(_sign(payload), sig):
            return False
        claims = json.loads(_unb64url(payload))
        return claims.get("sub") == "owner" and claims.get("exp", 0) > now
    except Exception:
        return False


def _admin_login(event, body, now):
    state = _ddb.get_item(Key={"slot_iso": AUTH_KEY}).get("Item") or {}
    fails, first_fail = int(state.get("fails", 0)), int(state.get("first_fail", 0))
    last_counter = int(state.get("last_counter", 0))
    if now - first_fail >= LOCK_SECONDS:
        fails, first_fail = 0, 0
    if fails >= MAX_LOGIN_FAILS:
        return _response(429, {"error": "locked", "retry_after": int(first_fail + LOCK_SECONDS - now)},
                         no_store=True)
    try:
        pw_hash = _get_admin_secret(SSM_ADMIN_PASSWORD_PARAM)
        totp_secret = _get_admin_secret(SSM_ADMIN_TOTP_PARAM)
        _get_admin_secret(SSM_ADMIN_SESSION_PARAM)
    except Exception as e:
        print(f"[admin] not configured: {e!r}")
        return _response(503, {"error": "admin_not_configured"}, no_store=True)

    password = body.get("password")
    password = password if isinstance(password, str) and len(password) <= 200 else ""
    counter = _match_totp(totp_secret, str(body.get("code") or "").strip(), now)
    ip = event.get("requestContext", {}).get("http", {}).get("sourceIp", "?")

    if not (password and _check_password(password, pw_hash)) or counter is None or counter <= last_counter:
        fails, first_fail = fails + 1, first_fail or int(now)
        _ddb.put_item(Item={"slot_iso": AUTH_KEY, "fails": fails, "first_fail": first_fail,
                            "last_counter": last_counter})
        print(f"[admin] failed login {fails}/{MAX_LOGIN_FAILS} from {ip}")
        if fails >= MAX_LOGIN_FAILS:
            _alert(f"🔒 Booking admin locked for 15 min after {fails} failed logins (last from {ip})")
        return _response(401, {"error": "bad_login"}, no_store=True)

    _ddb.put_item(Item={"slot_iso": AUTH_KEY, "fails": 0, "first_fail": 0, "last_counter": counter})
    print(f"[admin] login from {ip}")
    _alert(f"🔑 Booking admin login from {ip}")
    return _response(200, {"token": _make_token(now), "expires_at": int(now) + SESSION_TTL}, no_store=True)


def _admin_list(now):
    now_dt = datetime.fromtimestamp(now, timezone.utc)
    bookings, blocks = [], []
    for item in _scan_all():
        try:
            if _is_block(item):
                if datetime.fromisoformat(item["end_utc"]) > now_dt:
                    blocks.append({"id": item["slot_iso"], "start_utc": item["start_utc"],
                                   "end_utc": item["end_utc"], "note": item.get("note", "")})
            elif _is_booking(item):
                start = datetime.fromisoformat(item["slot_iso"])
                if start > now_dt - timedelta(hours=1):
                    bookings.append({
                        "slot_iso": item["slot_iso"],
                        "duration_min": int(item.get("duration_min", 30)),
                        "name": item.get("visitor_name", ""),
                        "email": item.get("visitor_email", ""),
                        "status": item.get("status", ""),
                        "meet_link": item.get("meet_link"),
                        "created_at": int(item.get("created_at", 0)),
                    })
        except (KeyError, ValueError, TypeError) as e:
            print(f"[admin] skipping bad row {item.get('slot_iso')!r}: {e!r}")
    bookings.sort(key=lambda b: datetime.fromisoformat(b["slot_iso"]))
    blocks.sort(key=lambda b: b["start_utc"])
    return _response(200, {"bookings": bookings, "blocks": blocks, "timezone": TIMEZONE}, no_store=True)


def _delete_calendar_event(access_token, event_id):
    req = urllib.request.Request(
        EVENT_URL.format(urllib.parse.quote(event_id, safe="")),
        headers={"Authorization": f"Bearer {access_token}"},
        method="DELETE",
    )
    try:
        urllib.request.urlopen(req, timeout=15).close()
    except urllib.error.HTTPError as e:
        if e.code not in (404, 410):  # already gone counts as cancelled
            raise


def _admin_cancel(body):
    slot_iso = body.get("slot_iso")
    if not isinstance(slot_iso, str) or not _is_booking({"slot_iso": slot_iso}):
        return _response(400, {"error": "bad slot_iso"}, no_store=True)
    item = _ddb.get_item(Key={"slot_iso": slot_iso}).get("Item")
    if not item:
        return _response(404, {"error": "not_found"}, no_store=True)
    if item.get("event_id"):
        try:
            _delete_calendar_event(_get_access_token(), item["event_id"])
        except Exception as e:
            print(f"[admin] calendar delete failed: {e!r}")
            return _response(502, {"error": "calendar_error"}, no_store=True)
    _ddb.delete_item(Key={"slot_iso": slot_iso})
    end_iso = (datetime.fromisoformat(slot_iso) + timedelta(minutes=int(item.get("duration_min", 30)))).isoformat()
    _alert(f"❌ Booking cancelled from admin: {item.get('visitor_name')} <{item.get('visitor_email')}>\n"
           f"🕒 {_format_slot(slot_iso, end_iso, TIMEZONE)}")
    return _response(200, {"ok": True}, no_store=True)


HHMM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _admin_block(body, now):
    """Whole days (no times) become one block; with times, one block per day."""
    try:
        first = datetime.strptime(body.get("start_date") or "", "%Y-%m-%d").date()
        last = datetime.strptime(body.get("end_date") or body.get("start_date") or "", "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return _response(400, {"error": "dates must be YYYY-MM-DD"}, no_store=True)
    if last < first or (last - first).days > 366:
        return _response(400, {"error": "bad date range"}, no_store=True)
    start_time, end_time = body.get("start_time"), body.get("end_time")
    note = str(body.get("note") or "")[:100]
    tz = ZoneInfo(TIMEZONE)

    def local(day, hhmm):
        return datetime.strptime(f"{day} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)

    if start_time or end_time:
        if not (isinstance(start_time, str) and isinstance(end_time, str)
                and HHMM_RE.match(start_time) and HHMM_RE.match(end_time) and start_time < end_time):
            return _response(400, {"error": "times must be HH:MM, start before end"}, no_store=True)
        if (last - first).days > 62:
            return _response(400, {"error": "at most 63 days with times"}, no_store=True)
        days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
        ranges = [(local(d, start_time), local(d, end_time)) for d in days]
    else:
        ranges = [(local(first, "00:00"), local(last + timedelta(days=1), "00:00"))]

    now_dt = datetime.fromtimestamp(now, timezone.utc)
    ranges = [(a, b) for a, b in ranges if b > now_dt]
    if not ranges:
        return _response(400, {"error": "that time is already past"}, no_store=True)
    ids = []
    for a, b in ranges:
        block_id = f"{BLOCK_PREFIX}{uuid.uuid4().hex[:12]}"
        _ddb.put_item(Item={
            "slot_iso": block_id,
            "start_utc": a.astimezone(timezone.utc).isoformat(),
            "end_utc": b.astimezone(timezone.utc).isoformat(),
            "note": note,
            "status": "blocked",
            "created_at": int(now),
        })
        ids.append(block_id)
    return _response(200, {"ok": True, "ids": ids}, no_store=True)


def _admin_unblock(body):
    block_id = body.get("id")
    if not isinstance(block_id, str) or not block_id.startswith(BLOCK_PREFIX):
        return _response(400, {"error": "bad id"}, no_store=True)
    _ddb.delete_item(Key={"slot_iso": block_id})
    return _response(200, {"ok": True}, no_store=True)


def _handle_admin(event, method, path):
    now = time.time()
    route = (method, path.rstrip("/"))
    if route == ("POST", "/admin/login"):
        body = _json_body(event)
        if body is None:
            return _response(400, {"error": "invalid JSON"}, no_store=True)
        return _admin_login(event, body, now)

    auth = (event.get("headers") or {}).get("authorization", "")
    if not auth.startswith("Bearer ") or not _token_valid(auth[7:], now):
        return _response(401, {"error": "unauthorized"}, no_store=True)

    if route == ("GET", "/admin/bookings"):
        return _admin_list(now)
    actions = {
        "/admin/cancel": lambda b: _admin_cancel(b),
        "/admin/block": lambda b: _admin_block(b, now),
        "/admin/unblock": lambda b: _admin_unblock(b),
    }
    if method == "POST" and route[1] in actions:
        body = _json_body(event)
        if body is None:
            return _response(400, {"error": "invalid JSON"}, no_store=True)
        return actions[route[1]](body)
    return _response(404, {"error": "not_found"}, no_store=True)


def lambda_handler(event, context):
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or ""
    ).upper()
    path = (event.get("requestContext", {}).get("http", {}).get("path")
            or event.get("path") or "/")
    print(f"[booking] method={method} path={path}")
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": {}, "body": ""}

    # Dashboard refresh trigger — separate from booking flow
    if path.rstrip("/") == "/run-refresh":
        if method != "POST":
            return _response(405, {"error": "method not allowed"})
        return _handle_run_refresh(event)

    if path == "/admin" or path.startswith("/admin/"):
        return _handle_admin(event, method, path)

    if method == "GET":
        slots = _get_booked_slots()
        print(f"[booking] GET returning {len(slots)} booked slots")
        return _response(200, {"booked_slots": slots})
    if method != "POST":
        return _response(405, {"error": "method not allowed"})

    payload = _json_body(event)
    if payload is None:
        return _response(400, {"error": "invalid JSON"})

    print(f"[booking] POST payload: slot_iso={payload.get('slot_iso')} name={payload.get('name')} email={payload.get('email')}")
    parsed, err = _validate(payload)
    if err:
        print(f"[booking] validation error: {err}")
        return _response(400, {"error": err})

    slot_iso = parsed["slot_iso"]

    # 1. reserve slot (owner blocks count as taken)
    if _in_owner_block(slot_iso, parsed["end_iso"]) or not _reserve_slot(
        slot_iso, parsed["name"], parsed["email"], parsed["duration_min"]
    ):
        print(f"[booking] slot already taken: {slot_iso}")
        return _response(409, {"error": "slot_taken"})
    print(f"[booking] slot reserved: {slot_iso}")

    # 2. create calendar event — release reservation on failure
    try:
        access_token = _get_access_token()
        print("[booking] got access token, creating calendar event...")
        ev = _create_calendar_event(
            access_token, slot_iso, parsed["end_iso"], parsed["name"], parsed["email"]
        )
        print(f"[booking] calendar event created: id={ev.get('id')}")
    except Exception as e:
        _release_slot(slot_iso)
        print(f"[booking] calendar error: {e!r}")
        _alert(_booking_failed_alert(parsed, e))
        return _response(502, {"error": "calendar_error"})

    event_id = ev.get("id")
    meet_link = ev.get("hangoutLink") or next(
        (ep.get("uri") for ep in ev.get("conferenceData", {}).get("entryPoints", [])
         if ep.get("entryPointType") == "video"),
        None,
    )
    _mark_booked(slot_iso, event_id, meet_link)

    return _response(200, {
        "ok": True,
        "meet_link": meet_link,
        "event_id": event_id,
        "slot_iso": slot_iso,
    })
