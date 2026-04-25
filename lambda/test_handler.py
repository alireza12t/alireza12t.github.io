"""
Unit tests for booking-api Lambda handler.
Run: python -m pytest lambda/test_handler.py -v
These tests mock all AWS/external calls — no real credentials needed.
"""
import json
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
        self.assertEqual(len(body["booked_slots"]), 1)


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
