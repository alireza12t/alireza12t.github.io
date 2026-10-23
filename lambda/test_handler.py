"""
Unit tests for booking-api Lambda handler.
Run: python -m pytest lambda/test_handler.py -v
These tests mock all AWS/external calls — no real credentials needed.
"""
import base64
import json
import urllib.parse
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Stub boto3 before importing handler ──────────────────────────────────────
boto3_stub = types.ModuleType("boto3")
botocore_stub = types.ModuleType("botocore")
exceptions_stub = types.ModuleType("botocore.exceptions")

class _ClientError(Exception):
    def __init__(self, response, op):
        self.response = response
        self.operation_name = op

exceptions_stub.ClientError = _ClientError
botocore_stub.exceptions = exceptions_stub
sys.modules.setdefault("boto3", boto3_stub)
sys.modules.setdefault("botocore", botocore_stub)
sys.modules.setdefault("botocore.exceptions", exceptions_stub)

# Provide boto3.client / boto3.resource stubs
_mock_ssm = MagicMock()
_mock_ddb_table = MagicMock()
_mock_ddb = MagicMock()
_mock_ddb.Table.return_value = _mock_ddb_table
boto3_stub.client = MagicMock(return_value=_mock_ssm)
boto3_stub.resource = MagicMock(return_value=_mock_ddb)

import importlib, os
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("HOST_EMAIL", "test@example.com")
os.environ.setdefault("HOST_NAME", "Test Host")
os.environ.setdefault("TIMEZONE", "America/Toronto")
os.environ.setdefault("DDB_TABLE", "bookings")
os.environ.setdefault("ALLOWED_ORIGIN", "https://alireza12t.github.io")

import handler  # noqa: E402  (after stubs)
from handler import _response, _validate, lambda_handler  # noqa: E402


# ── Helpers ──────────────────────────────────────────────────────────────────
def _event(method="POST", path="/", body=None, headers=None):
    return {
        "requestContext": {"http": {"method": method, "path": path}},
        "headers": headers or {},
        "body": json.dumps(body) if body else "{}",
        "isBase64Encoded": False,
    }


# ── _response ────────────────────────────────────────────────────────────────
class TestResponse(unittest.TestCase):
    def test_status_and_body(self):
        r = _response(200, {"ok": True})
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(json.loads(r["body"]), {"ok": True})

    def test_error_status(self):
        r = _response(400, {"error": "bad"})
        self.assertEqual(r["statusCode"], 400)


# ── _validate ────────────────────────────────────────────────────────────────
class TestValidate(unittest.TestCase):
    def _good(self):
        return {
            "slot_iso": "2099-06-01T10:00:00+00:00",
            "duration_min": 30,
            "name": "Alice",
            "email": "alice@example.com",
        }

    def test_valid_payload(self):
        parsed, err = _validate(self._good())
        self.assertIsNone(err)
        self.assertEqual(parsed["name"], "Alice")
        self.assertEqual(parsed["duration_min"], 30)

    def test_missing_slot(self):
        p = self._good(); del p["slot_iso"]
        _, err = _validate(p)
        self.assertIsNotNone(err)

    def test_bad_duration(self):
        p = self._good(); p["duration_min"] = 999
        _, err = _validate(p)
        self.assertIsNotNone(err)

    def test_bad_email(self):
        p = self._good(); p["email"] = "notanemail"
        _, err = _validate(p)
        self.assertIsNotNone(err)

    def test_past_slot(self):
        p = self._good(); p["slot_iso"] = "2000-01-01T00:00:00+00:00"
        _, err = _validate(p)
        self.assertIsNotNone(err)

    def test_missing_timezone(self):
        p = self._good(); p["slot_iso"] = "2099-06-01T10:00:00"
        _, err = _validate(p)
        self.assertIsNotNone(err)


# ── OPTIONS (CORS preflight) ─────────────────────────────────────────────────
class TestOptions(unittest.TestCase):
    def test_options_returns_204(self):
        r = lambda_handler(_event("OPTIONS"), None)
        self.assertEqual(r["statusCode"], 204)


# ── GET /run-refresh (wrong method) ─────────────────────────────────────────
class TestRunRefreshRoute(unittest.TestCase):
    def test_get_not_allowed(self):
        r = lambda_handler(_event("GET", "/run-refresh"), None)
        self.assertEqual(r["statusCode"], 405)

    def test_wrong_key_forbidden(self):
        handler._secret_cache[handler.SSM_REFRESH_KEY_PARAM] = "correct-key"
        r = lambda_handler(
            _event("POST", "/run-refresh", headers={"x-refresh-key": "wrong"}),
            None,
        )
        self.assertEqual(r["statusCode"], 403)

    def test_placeholder_pat_returns_500(self):
        handler._secret_cache[handler.SSM_REFRESH_KEY_PARAM] = "misfit2026"
        handler._secret_cache[handler.SSM_GITHUB_PAT_PARAM] = "PLACEHOLDER"
        r = lambda_handler(
            _event("POST", "/run-refresh", headers={"x-refresh-key": "misfit2026"}),
            None,
        )
        self.assertEqual(r["statusCode"], 500)

    @patch("urllib.request.urlopen")
    def test_refresh_success(self, mock_urlopen):
        handler._secret_cache[handler.SSM_REFRESH_KEY_PARAM] = "misfit2026"
        handler._secret_cache[handler.SSM_GITHUB_PAT_PARAM] = "ghp_testtoken"
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=MagicMock(status=204))
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_cm
        r = lambda_handler(
            _event("POST", "/run-refresh", headers={"x-refresh-key": "misfit2026"}),
            None,
        )
        self.assertEqual(r["statusCode"], 200)
        self.assertTrue(json.loads(r["body"])["ok"])


# ── GET booked slots ─────────────────────────────────────────────────────────
class TestGetBookedSlots(unittest.TestCase):
    def test_get_returns_slots(self):
        _mock_ddb_table.scan.return_value = {
            "Items": [{"slot_iso": "2099-06-01T10:00:00+00:00"}]
        }
        r = lambda_handler(_event("GET", "/"), None)
        self.assertEqual(r["statusCode"], 200)
        body = json.loads(r["body"])
        self.assertIn("booked_slots", body)
        # Same string as the browser's toISOString(), which booking.html compares against
        self.assertEqual(body["booked_slots"], ["2099-06-01T10:00:00.000Z"])

    def test_owner_block_hides_every_slot_inside_it(self):
        from datetime import date, timedelta
        day = (date.today() + timedelta(days=2)).isoformat()
        _mock_ddb_table.scan.return_value = {"Items": [
            {"slot_iso": "block#abc", "start_utc": f"{day}T14:15:00+00:00",
             "end_utc": f"{day}T15:00:00+00:00", "status": "blocked"},
            {"slot_iso": "admin#auth", "fails": 0},
            {"slot_iso": "2001-01-01T10:00:00+00:00", "status": "booked"},  # past
        ]}
        body = json.loads(lambda_handler(_event("GET", "/"), None)["body"])
        self.assertEqual(body["booked_slots"], [f"{day}T14:00:00.000Z", f"{day}T14:30:00.000Z"])

    def test_blocks_stop_at_the_horizon(self):
        _mock_ddb_table.scan.return_value = {"Items": [
            {"slot_iso": "block#far", "start_utc": "2099-06-01T00:00:00+00:00",
             "end_utc": "2099-06-30T00:00:00+00:00"}]}
        body = json.loads(lambda_handler(_event("GET", "/"), None)["body"])
        self.assertEqual(body["booked_slots"], [])


# ── POST booking — slot already taken ────────────────────────────────────────
class TestPostBooking(unittest.TestCase):
    def setUp(self):
        handler._secret_cache.clear()

    def test_slot_taken_returns_409(self):
        _mock_ddb_table.put_item.side_effect = _ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem"
        )
        payload = {
            "slot_iso": "2099-06-01T10:00:00+00:00",
            "duration_min": 30,
            "name": "Bob",
            "email": "bob@example.com",
        }
        # SSM returns a dummy secret
        _mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "dummy"}}
        r = lambda_handler(_event("POST", "/", body=payload), None)
        self.assertEqual(r["statusCode"], 409)

    @patch("urllib.request.urlopen")
    def test_calendar_error_sends_telegram_alert(self, mock_urlopen):
        _mock_ddb_table.put_item.side_effect = None
        _mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "dummy"}}
        # first call: Google token exchange fails; second call: Telegram alert succeeds
        mock_urlopen.side_effect = [Exception("invalid_grant"), MagicMock()]
        payload = {
            "slot_iso": "2099-06-01T10:00:00+00:00",
            "duration_min": 30,
            "name": "Bob",
            "email": "bob@example.com",
            "visitor_tz": "Europe/Paris",
        }
        r = lambda_handler(_event("POST", "/", body=payload), None)
        self.assertEqual(r["statusCode"], 502)
        self.assertEqual(mock_urlopen.call_count, 2)
        alert_req = mock_urlopen.call_args_list[1][0][0]
        self.assertIn("api.telegram.org", alert_req.full_url)
        text = urllib.parse.parse_qs(alert_req.data.decode())["text"][0]
        self.assertIn("invalid_grant", text)
        self.assertIn("bob@example.com", text)
        # 10:00 UTC on June 1 is 6:00 AM in Toronto and 12:00 PM in Paris
        self.assertIn("Mon, Jun 1 · 6:00–6:30 AM (America/Toronto)", text)
        self.assertIn("Their time: Mon, Jun 1 · 12:00–12:30 PM (Europe/Paris)", text)

    @patch("urllib.request.urlopen")
    def test_token_error_includes_google_reason(self, mock_urlopen):
        import io, urllib.error
        _mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "dummy"}}
        mock_urlopen.side_effect = urllib.error.HTTPError(
            handler.TOKEN_URL, 400, "Bad Request", {},
            io.BytesIO(b'{"error": "invalid_grant", "error_description": "Token has been expired or revoked."}'),
        )
        with self.assertRaises(RuntimeError) as ctx:
            handler._get_access_token()
        self.assertIn("invalid_grant", str(ctx.exception))
        self.assertIn("expired or revoked", str(ctx.exception))

    def test_bad_visitor_tz_is_ignored(self):
        parsed, err = handler._validate({
            "slot_iso": "2099-06-01T10:00:00+00:00",
            "name": "Bob",
            "email": "bob@example.com",
            "visitor_tz": "Not/AZone",
        })
        self.assertIsNone(err)
        self.assertIsNone(parsed["visitor_tz"])

    def test_invalid_body_returns_400(self):
        ev = _event("POST", "/")
        ev["body"] = "not-json"
        r = lambda_handler(ev, None)
        self.assertEqual(r["statusCode"], 400)

    def test_missing_fields_returns_400(self):
        r = lambda_handler(_event("POST", "/", body={"name": "Alice"}), None)
        self.assertEqual(r["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()


# ── Owner admin ──────────────────────────────────────────────────────────────
import importlib.util  # noqa: E402
import time as _time  # noqa: E402
from pathlib import Path  # noqa: E402

TOTP_SECRET = "JBSWY3DPEHPK3PXP"
PW_HASH = handler._hash_password("correct horse battery", n=2**10)


def _ssm_values(Name, WithDecryption=True):
    values = {
        "/booking/admin_password_hash": PW_HASH,
        "/booking/admin_totp_secret": TOTP_SECRET,
        "/booking/admin_session_key": "test-session-key",
    }
    return {"Parameter": {"Value": values.get(Name, "dummy")}}


def _now_code():
    return handler._totp(TOTP_SECRET, int(_time.time() // 30))


@patch.object(handler, "_alert")
class TestAdmin(unittest.TestCase):
    def setUp(self):
        handler._admin_secret_cache.clear()
        handler._secret_cache.clear()
        _mock_ssm.get_parameter.side_effect = _ssm_values
        _mock_ddb_table.reset_mock(return_value=True, side_effect=True)
        _mock_ddb_table.get_item.return_value = {}
        _mock_ddb_table.scan.return_value = {"Items": []}

    def tearDown(self):
        _mock_ssm.get_parameter.side_effect = None

    def _login(self, password="correct horse battery", code=None):
        return lambda_handler(_event("POST", "/admin/login",
                                     body={"password": password, "code": code or _now_code()}), None)

    def _authed(self, method, path, body=None):
        token = json.loads(self._login()["body"])["token"]
        return lambda_handler(_event(method, path, body=body,
                                     headers={"authorization": f"Bearer {token}"}), None)

    def test_totp_matches_rfc6238_vector(self, _alert):
        # RFC 6238 SHA-1 vector: secret "12345678901234567890", T=59s -> 94287082 (last 6 digits)
        secret = base64.b32encode(b"12345678901234567890").decode()
        self.assertEqual(handler._totp(secret, 59 // 30), "287082")

    def test_login_success_returns_token_and_alerts(self, alert):
        r = self._login()
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(r["headers"]["Cache-Control"], "no-store")
        self.assertIn("token", json.loads(r["body"]))
        alert.assert_called_once()

    def test_wrong_password_is_401(self, _alert):
        self.assertEqual(self._login(password="nope")["statusCode"], 401)
        saved = _mock_ddb_table.put_item.call_args.kwargs["Item"]
        self.assertEqual(saved["fails"], 1)

    def test_wrong_code_is_401(self, _alert):
        wrong = f"{(int(_now_code()) + 1) % 1_000_000:06d}"
        self.assertEqual(self._login(code=wrong)["statusCode"], 401)

    def test_code_cannot_be_reused(self, _alert):
        step = int(_time.time() // 30)
        _mock_ddb_table.get_item.return_value = {"Item": {"slot_iso": "admin#auth", "fails": 0,
                                                          "first_fail": 0, "last_counter": step + 1}}
        self.assertEqual(self._login()["statusCode"], 401)

    def test_locked_after_five_failures(self, alert):
        _mock_ddb_table.get_item.return_value = {"Item": {"slot_iso": "admin#auth", "fails": 5,
                                                          "first_fail": int(_time.time()) - 60,
                                                          "last_counter": 0}}
        r = self._login()
        self.assertEqual(r["statusCode"], 429)

    def test_lock_expires(self, _alert):
        _mock_ddb_table.get_item.return_value = {"Item": {"slot_iso": "admin#auth", "fails": 5,
                                                          "first_fail": int(_time.time()) - 16 * 60,
                                                          "last_counter": 0}}
        self.assertEqual(self._login()["statusCode"], 200)

    def test_fifth_failure_alerts(self, alert):
        _mock_ddb_table.get_item.return_value = {"Item": {"slot_iso": "admin#auth", "fails": 4,
                                                          "first_fail": int(_time.time()) - 60,
                                                          "last_counter": 0}}
        self.assertEqual(self._login(password="nope")["statusCode"], 401)
        self.assertIn("locked", alert.call_args.args[0])

    def test_not_configured_is_503(self, _alert):
        _mock_ssm.get_parameter.side_effect = Exception("ParameterNotFound")
        self.assertEqual(self._login()["statusCode"], 503)

    def test_routes_need_a_token(self, _alert):
        for method, path in (("GET", "/admin/bookings"), ("POST", "/admin/cancel"),
                             ("POST", "/admin/block"), ("POST", "/admin/unblock")):
            r = lambda_handler(_event(method, path), None)
            self.assertEqual(r["statusCode"], 401, path)

    def test_tampered_and_expired_tokens_rejected(self, _alert):
        token = json.loads(self._login()["body"])["token"]
        payload, sig = token.split(".")
        forged = handler._b64url(json.dumps({"sub": "owner", "exp": 4102444800}).encode())
        self.assertFalse(handler._token_valid(f"{forged}.{sig}", _time.time()))
        self.assertFalse(handler._token_valid(token, _time.time() + handler.SESSION_TTL + 1))
        self.assertTrue(handler._token_valid(token, _time.time()))

    def test_list_bookings_and_blocks(self, _alert):
        _mock_ddb_table.scan.return_value = {"Items": [
            {"slot_iso": "2099-06-02T10:00:00+00:00", "visitor_name": "B", "visitor_email": "b@x.com",
             "status": "booked", "created_at": 1},
            {"slot_iso": "2099-06-01T10:00:00+00:00", "visitor_name": "A", "visitor_email": "a@x.com",
             "status": "booked", "duration_min": 30, "created_at": 1},
            {"slot_iso": "block#1", "start_utc": "2099-07-01T04:00:00+00:00",
             "end_utc": "2099-07-02T04:00:00+00:00", "note": "trip"},
            {"slot_iso": "admin#auth", "fails": 0},
        ]}
        r = self._authed("GET", "/admin/bookings")
        self.assertEqual(r["statusCode"], 200)
        body = json.loads(r["body"])
        self.assertEqual([b["name"] for b in body["bookings"]], ["A", "B"])
        self.assertEqual(body["blocks"][0]["note"], "trip")

    @patch("urllib.request.urlopen")
    def test_cancel_deletes_event_then_row(self, mock_urlopen, alert):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b'{"access_token":"t"}'
        _mock_ddb_table.get_item.side_effect = [
            {},  # login throttle row
            {"Item": {"slot_iso": "2099-06-01T10:00:00+00:00", "event_id": "ev1",
                      "visitor_name": "A", "visitor_email": "a@x.com"}},
        ]
        r = self._authed("POST", "/admin/cancel", body={"slot_iso": "2099-06-01T10:00:00+00:00"})
        self.assertEqual(r["statusCode"], 200)
        delete_req = mock_urlopen.call_args_list[-1].args[0]
        self.assertEqual(delete_req.get_method(), "DELETE")
        self.assertIn("/events/ev1?sendUpdates=all", delete_req.full_url)
        _mock_ddb_table.delete_item.assert_called_once_with(Key={"slot_iso": "2099-06-01T10:00:00+00:00"})

    @patch("urllib.request.urlopen")
    def test_cancel_keeps_row_when_google_fails(self, mock_urlopen, _alert):
        mock_urlopen.side_effect = Exception("invalid_grant")
        _mock_ddb_table.get_item.side_effect = [
            {}, {"Item": {"slot_iso": "2099-06-01T10:00:00+00:00", "event_id": "ev1"}},
        ]
        r = self._authed("POST", "/admin/cancel", body={"slot_iso": "2099-06-01T10:00:00+00:00"})
        self.assertEqual(r["statusCode"], 502)
        _mock_ddb_table.delete_item.assert_not_called()

    def test_cancel_refuses_non_booking_rows(self, _alert):
        r = self._authed("POST", "/admin/cancel", body={"slot_iso": "admin#auth"})
        self.assertEqual(r["statusCode"], 400)

    def test_block_whole_days_is_one_row(self, _alert):
        r = self._authed("POST", "/admin/block",
                         body={"start_date": "2099-12-24", "end_date": "2099-12-26", "note": "holiday"})
        self.assertEqual(r["statusCode"], 200)
        item = _mock_ddb_table.put_item.call_args.kwargs["Item"]
        self.assertTrue(item["slot_iso"].startswith("block#"))
        self.assertEqual(item["start_utc"], "2099-12-24T05:00:00+00:00")  # Toronto midnight, EST
        self.assertEqual(item["end_utc"], "2099-12-27T05:00:00+00:00")

    def test_block_with_times_is_one_row_per_day(self, _alert):
        r = self._authed("POST", "/admin/block", body={"start_date": "2099-07-01", "end_date": "2099-07-03",
                                                       "start_time": "12:00", "end_time": "13:30"})
        self.assertEqual(len(json.loads(r["body"])["ids"]), 3)
        item = _mock_ddb_table.put_item.call_args.kwargs["Item"]
        self.assertEqual(item["start_utc"], "2099-07-03T16:00:00+00:00")  # EDT
        self.assertEqual(item["end_utc"], "2099-07-03T17:30:00+00:00")

    def test_block_rejects_bad_input(self, _alert):
        for body in ({"start_date": "tomorrow"},
                     {"start_date": "2099-07-03", "end_date": "2099-07-01"},
                     {"start_date": "2099-07-01", "start_time": "13:00", "end_time": "12:00"},
                     {"start_date": "2001-07-01"}):
            self.assertEqual(self._authed("POST", "/admin/block", body=body)["statusCode"], 400, body)

    def test_unblock(self, _alert):
        r = self._authed("POST", "/admin/unblock", body={"id": "block#abc"})
        self.assertEqual(r["statusCode"], 200)
        _mock_ddb_table.delete_item.assert_called_once_with(Key={"slot_iso": "block#abc"})
        self.assertEqual(self._authed("POST", "/admin/unblock",
                                      body={"id": "2099-06-01T10:00:00+00:00"})["statusCode"], 400)

    def test_public_booking_inside_block_is_409(self, _alert):
        _mock_ddb_table.scan.return_value = {"Items": [
            {"slot_iso": "block#1", "start_utc": "2099-06-01T00:00:00+00:00",
             "end_utc": "2099-06-02T00:00:00+00:00"}]}
        payload = {"slot_iso": "2099-06-01T10:00:00+00:00", "duration_min": 30,
                   "name": "Bob", "email": "bob@example.com"}
        r = lambda_handler(_event("POST", "/", body=payload), None)
        self.assertEqual(r["statusCode"], 409)
        _mock_ddb_table.put_item.assert_not_called()


class TestSetupScript(unittest.TestCase):
    """scripts/setup_booking_admin.py must write what the Lambda checks."""

    def setUp(self):
        path = Path(__file__).resolve().parent.parent / "scripts" / "setup_booking_admin.py"
        spec = importlib.util.spec_from_file_location("setup_booking_admin", path)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_password_hash_is_accepted_by_lambda(self):
        stored = self.mod.hash_password("hunter2 hunter2")
        self.assertTrue(handler._check_password("hunter2 hunter2", stored))
        self.assertFalse(handler._check_password("hunter3 hunter3", stored))

    def test_totp_agrees_with_lambda(self):
        secret = self.mod.new_totp_secret()
        for step in (0, 1, 55_000_000):
            self.assertEqual(self.mod.totp(secret, step), handler._totp(secret, step))
