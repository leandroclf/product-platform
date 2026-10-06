from __future__ import annotations
import logging, os
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

Sink = Callable[[dict[str, Any]], Awaitable[None]]
_log = logging.getLogger(__name__)

class ProductEvents:
    def __init__(self, product_id: str, sink: Sink, environment_var: str = "APP_ENV") -> None:
        self.product_id, self.sink, self.environment_var = product_id, sink, environment_var

    def create(self, event: str, **fields: Any) -> dict[str, Any]:
        protected={"schema_version","event","product_id","environment","release_sha","occurred_at"}
        if protected.intersection(fields):
            raise ValueError("canonical ProductEvent metadata cannot be overridden")
        return {**fields,"schema_version":"1.0","event":event,"product_id":self.product_id,
                "environment":os.getenv(self.environment_var,"development"),
                "release_sha":os.getenv("RELEASE_SHA","local"),
                "occurred_at":datetime.now(timezone.utc).isoformat()}

    async def emit(self, event: dict[str, Any]) -> None:
        try: await self.sink(event)
        except Exception: _log.exception("product_event_delivery_failed")
