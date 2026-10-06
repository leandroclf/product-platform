#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
schema=json.loads((root/"contracts/product-event/v1.schema.json").read_text())
valid=json.loads((root/"contracts/product-event/fixtures/valid.json").read_text())
invalid=json.loads((root/"contracts/product-event/fixtures/invalid-pii.json").read_text())
required=set(schema["required"]); allowed=set(schema["properties"])
assert required <= set(valid)
assert set(valid) <= allowed
assert valid["schema_version"]=="1.0"
assert invalid.keys()-allowed, "invalid PII fixture must contain forbidden fields"
canonical=set(schema["properties"]["event"]["enum"])
assert canonical=={"signup_completed","activation_completed","feature_used","limit_reached","upgrade_intent","subscription_changed","feedback_submitted"}
print("ProductEvent v1 conformance: OK")
