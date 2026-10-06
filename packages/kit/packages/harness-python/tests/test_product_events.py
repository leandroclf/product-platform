import asyncio
from ai_kit_harness import ProductEvents

async def main():
    captured=[]
    async def sink(event): captured.append(event)
    events=ProductEvents("test-product", sink)
    event=events.create("feature_used", feature="x")
    assert event["schema_version"]=="1.0"
    assert event["product_id"]=="test-product"
    await events.emit(event)
    assert captured==[event]
    try: events.create("feature_used", product_id="override")
    except ValueError: pass
    else: raise AssertionError("canonical metadata override must fail")

asyncio.run(main())
