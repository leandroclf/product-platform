#!/usr/bin/env python3
"""G7: read-only HTTPS health evidence for an already deployed release.

The caller must supply a trusted, explicitly configured endpoint. This tool
never deploys, approves, rolls back or treats HTTP success as release identity.
"""
import argparse
import json
import ssl
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def validate_endpoint(endpoint):
    parts = urlsplit(endpoint)
    if (parts.scheme != "https" or not parts.hostname or
            parts.username is not None or parts.password is not None or
            parts.fragment or parts.port not in (None, 443)):
        raise ValueError("a standard HTTPS endpoint without credentials or fragment is required")
    return endpoint


def observe(endpoint, *, attempts=3, interval=2.0, timeout=5.0, consecutive_successes=1, opener=None, sleeper=time.sleep):
    validate_endpoint(endpoint)
    if (not 1 <= attempts <= 20 or not 0 <= interval <= 60 or not 0.1 <= timeout <= 30
            or not 1 <= consecutive_successes <= attempts):
        raise ValueError("invalid health-check bounds")
    client = opener or build_opener(NoRedirect(), HTTPSHandler(context=ssl.create_default_context()))
    observations = []
    streak = 0
    for index in range(attempts):
        if index:
            sleeper(interval)
        request = Request(endpoint, method="GET", headers={"Accept": "application/json"})
        try:
            # Never consume an arbitrary response body or forward authentication.
            with client.open(request, timeout=timeout) as response:
                status = response.status
        except HTTPError as exc:
            status = exc.code
            exc.close()
        except (URLError, TimeoutError, OSError):
            status = None
        observations.append(status)
        streak = streak + 1 if status == 200 else 0
        if streak >= consecutive_successes:
            break
    healthy = streak >= consecutive_successes
    return {
        "gate": "G7",
        "decision": "HEALTH_ENDPOINT_RESPONDING" if healthy else "BLOCK",
        "checks_performed": len(observations),
        "http_statuses": observations,
        "required_consecutive_successes": consecutive_successes,
        "observed_consecutive_successes": streak,
        "endpoint_health_verified": healthy,
        "release_identity_verified": False,
        "approval_identity_verified": False,
        "rollback_verified": False,
        "authorized_to_deploy": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only HTTPS post-deploy health evidence")
    parser.add_argument("--url", required=True, help="Trusted HTTPS endpoint (not printed)")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--consecutive-successes", type=int, default=1)
    args = parser.parse_args()
    try:
        result = observe(args.url, attempts=args.attempts, interval=args.interval, timeout=args.timeout,
                         consecutive_successes=args.consecutive_successes)
    except (ValueError, OSError):
        result = {"gate": "G7", "decision": "BLOCK", "endpoint_health_verified": False,
                  "release_identity_verified": False, "authorized_to_deploy": False}
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("endpoint_health_verified") else 2


if __name__ == "__main__":
    sys.exit(main())
