"""ProductEvent v1 runtime. Canonical contract belongs to product-platform-kit."""
from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
import re
from typing import Any, Awaitable, Callable

Sink = Callable[[dict[str, Any]], Awaitable[None]]
_LOG = logging.getLogger(__name__)
_NAMES = {"signup_completed", "activation_completed", "feature_used", "limit_reached", "upgrade_intent", "subscription_changed", "feedback_submitted"}
_REQUIRED = {"schema_version", "event", "product_id", "environment", "release_sha", "occurred_at"}
_OPTIONAL = {"user_id", "account_id", "plan_id", "session_id", "feature", "outcome"}
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)")


def validate_product_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.keys() - (_REQUIRED | _OPTIONAL):
        raise ValueError("invalid product event object or unknown field")
    for key in _REQUIRED:
        if not isinstance(value.get(key), str) or not value[key]:
            raise ValueError("invalid product event metadata: " + key)
    if value["schema_version"] != "1.0" or value["event"] not in _NAMES:
        raise ValueError("invalid product event version or name")
    for key in _OPTIONAL:
        if key in value and value[key] is not None and not isinstance(value[key], str):
            raise ValueError("invalid product event field: " + key)
    raw = value["occurred_at"]
    if not _TIMESTAMP.fullmatch(raw):
        raise ValueError("invalid product event timestamp")
    datetime.fromisoformat(raw.upper().replace("Z", "+00:00"))
    return value


class ProductEvents:
    def __init__(self, product_id: str, sink: Sink, environment_var: str = "APP_ENV") -> None:
        self.product_id = product_id
        self.sink = sink
        self.environment_var = environment_var

    def create(self, event: str, **fields: Any) -> dict[str, Any]:
        if _REQUIRED.intersection(fields):
            raise ValueError("canonical ProductEvent metadata cannot be overridden")
        return validate_product_event({
            **fields, "schema_version": "1.0", "event": event,
            "product_id": self.product_id,
            "environment": os.getenv(self.environment_var, "development"),
            "release_sha": os.getenv("RELEASE_SHA", "local"),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        })

    async def emit(self, event: dict[str, Any]) -> None:
        try:
            await self.sink(validate_product_event(event))
        except Exception:
            _LOG.exception("product_event_delivery_failed")
