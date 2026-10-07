import asyncio
import json
import os
from pathlib import Path
import unittest

from product_platform_harness import ProductEvents, validate_product_event


class ProductEventTests(unittest.TestCase):
    def test_canonical_compatibility_corpus(self):
        fixtures = Path(os.getenv("PRODUCT_EVENT_CASES", "../kit/contracts/product-event/fixtures/compatibility-cases.json"))
        for case in json.loads(fixtures.read_text()):
            with self.subTest(case=case["name"]):
                if case["valid"]:
                    self.assertEqual(validate_product_event(case["event"]), case["event"])
                else:
                    with self.assertRaises(ValueError):
                        validate_product_event(case["event"])

    def test_emits_and_preserves_product_identity(self):
        captured = []
        async def sink(event):
            captured.append(event)
        events = ProductEvents("pilot", sink)
        event = events.create("feature_used", feature="risk_score")
        asyncio.run(events.emit(event))
        self.assertEqual(captured, [event])
        with self.assertRaises(ValueError):
            events.create("feature_used", product_id="override")
        with self.assertRaises(ValueError):
            events.create("feature_used", email="private@example.invalid")

    def test_delivery_failure_is_non_fatal(self):
        async def failing_sink(event):
            raise RuntimeError("offline sink")
        events = ProductEvents("pilot", failing_sink)
        with self.assertLogs("product_platform_harness.product_events", level="ERROR"):
            asyncio.run(events.emit(events.create("feature_used")))


if __name__ == "__main__":
    unittest.main()
