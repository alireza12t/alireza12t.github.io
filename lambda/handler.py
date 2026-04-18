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

No third-party deps — only stdlib + boto3 (always available in Lambda runtime).
"""

import json
import os
import time
import uuid
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError

# --- non-secret config (env vars) ---
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
SSM_CLIENT_SECRET_PARAM = os.environ.get("SSM_CLIENT_SECRET_PARAM", "/booking/google_client_secret")
SSM_REFRESH_TOKEN_PARAM = os.environ.get("SSM_REFRESH_TOKEN_PARAM", "/booking/google_refresh_token")
HOST_EMAIL = os.environ.get("HOST_EMAIL", "alireza.toghiani@icloud.com")
HOST_NAME = os.environ.get("HOST_NAME", "Alireza Toghiani")
TIMEZONE = os.environ.get("TIMEZONE", "America/Toronto")
DDB_TABLE = os.environ.get("DDB_TABLE", "bookings")
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "https://alireza12t.github.io")

TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_URL = (
    "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    "?conferenceDataVersion=1&sendUpdates=all"
)

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


def _cors_headers():
    return {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "300",
    }


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", **_cors_headers()},
        "body": json.dumps(body),
    }


def _get_access_token():
    data = urllib.parse.urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": _get_secret(SSM_CLIENT_SECRET_PARAM),
        "refresh_token": _get_secret(SSM_REFRESH_TOKEN_PARAM),
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())["access_token"]


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
    return {
        "slot_iso": start_dt.isoformat(),
        "end_iso": end_dt.isoformat(),
        "duration_min": duration_min,
        "name": name,
        "email": email,
    }, None


def _reserve_slot(slot_iso, visitor_name, visitor_email):
    now = int(time.time())
    try:
        _ddb.put_item(
            Item={
                "slot_iso": slot_iso,
                "visitor_name": visitor_name,
                "visitor_email": visitor_email,
                "created_at": now,
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


def _get_booked_slots():
    """Return upcoming slot_iso values so the frontend can hide them."""
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        resp = _ddb.scan(
            FilterExpression="slot_iso > :now",
            ExpressionAttributeValues={":now": now_iso},
            ProjectionExpression="slot_iso",
        )
        return [item["slot_iso"] for item in resp.get("Items", [])]
    except Exception as e:
        print(f"scan error: {e!r}")
        return []


def lambda_handler(event, context):
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or ""
    ).upper()
    print(f"[booking] method={method}")
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": _cors_headers(), "body": ""}
    if method == "GET":
        slots = _get_booked_slots()
        print(f"[booking] GET returning {len(slots)} booked slots")
        return _response(200, {"booked_slots": slots})
    if method != "POST":
        return _response(405, {"error": "method not allowed"})

    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64
        raw = base64.b64decode(raw).decode()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[booking] invalid JSON body: {raw[:200]}")
        return _response(400, {"error": "invalid JSON"})

    print(f"[booking] POST payload: slot_iso={payload.get('slot_iso')} name={payload.get('name')} email={payload.get('email')}")
    parsed, err = _validate(payload)
    if err:
        print(f"[booking] validation error: {err}")
        return _response(400, {"error": err})

    slot_iso = parsed["slot_iso"]

    # 1. reserve slot
    if not _reserve_slot(slot_iso, parsed["name"], parsed["email"]):
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
