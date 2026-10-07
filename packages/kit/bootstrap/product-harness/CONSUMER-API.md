# Minimal consumer API

```ts
const harness = createHarness({
  product: { id, environment, releaseSha },
  tenant: resolveTenant,
  database,
  modules: {
    product: { plans, capabilities },
    growth: { analytics, crm },
    commerce: { gateways },
    economics: { costProviders },
    observability: { enabled: true }
  }
})
```

Required stable surfaces:
- harness.events.emit
- harness.entitlements.check
- harness.usage.record
- harness.payments.checkout
- harness.payments.handleWebhook
- harness.sales.signal
- harness.finops.summary

Modules are opt-in and tree-shakeable where practical. Disabled modules create no background process and no database tables beyond dependencies required by enabled modules.
