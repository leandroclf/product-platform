#!/usr/bin/env python3
"""Offline unit tests for G7; no outbound requests."""
import importlib.util
from pathlib import Path
import unittest
from urllib.error import HTTPError, URLError

SPEC = importlib.util.spec_from_file_location("health_gate", Path(__file__).with_name("verify-post-deploy-health.py"))
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeResponse:
    def __init__(self, status):
        self.status = status
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, values):
        self.values = iter(values)
        self.urls = []
    def open(self, request, timeout):
        self.urls.append(request.full_url)
        value = next(self.values)
        if isinstance(value, Exception):
            raise value
        return FakeResponse(value)


class G7Tests(unittest.TestCase):
    def test_success_after_retry(self):
        opener = FakeOpener([503, 200])
        result = module.observe("https://example.com/health", opener=opener,
                                interval=0, sleeper=lambda _: None)
        self.assertEqual(result["decision"], "HEALTH_ENDPOINT_RESPONDING")
        self.assertEqual(result["http_statuses"], [503, 200])
        self.assertFalse(result["authorized_to_deploy"])
        self.assertFalse(result["release_identity_verified"])

    def test_failure_closed(self):
        opener = FakeOpener([URLError("unavailable"), 503, 503])
        result = module.observe("https://example.com/health", opener=opener,
                                interval=0, sleeper=lambda _: None)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertFalse(result["endpoint_health_verified"])

    def test_rejects_unsafe_urls(self):
        for url in ("http://example.com", "https://user:pw@example.com/",
                    "https://example.com:8443/", "file:///tmp/test", "https://example.com/#token"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                module.validate_endpoint(url)

    def test_rejects_unbounded_polling(self):
        for attempts, interval, timeout in ((0, 0, 1), (21, 0, 1), (1, -1, 1), (1, 0, 31)):
            with self.assertRaises(ValueError):
                module.observe("https://example.com/", attempts=attempts,
                               interval=interval, timeout=timeout)


if __name__ == "__main__":
    unittest.main()
