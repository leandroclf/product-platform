# ADR 001: Repository ownership and dependency boundaries

## Decision

Each reusable capability has exactly one canonical owner. Products own domain logic. product-platform-kit owns shared contracts, policies, skills and conformance assets. product-platform-cli owns discovery/proposals. product-platform-engineering-team owns engineering orchestration.

Allowed dependency direction:

- product-platform-cli -> product-platform-kit contracts
- product-platform-engineering-team -> product-platform-kit
- products -> product-platform-kit
- product-platform-kit -/-> products
- product-platform-kit -/-> product-platform-engineering-team
- products -/-> other products

The ai-engineering-control-plane is experimental/reference and is not a required runtime dependency.

## Extraction rule

Contracts, privacy rules and conformance may be centralized immediately. Runtime implementation follows Rule of Three: local at one consumer, evaluate at two, extract at three proven equivalent consumers.

## Communication

Cross-repository engineering communication uses versioned contracts, Git SHAs, pull requests and CI evidence. Runtime HTTP/queues/webhooks are introduced only for genuine runtime boundaries, never merely because code lives in separate repositories.
