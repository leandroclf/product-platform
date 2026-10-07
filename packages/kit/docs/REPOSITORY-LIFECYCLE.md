# Repository lifecycle

| Repository | State | Canonical responsibility |
|---|---|---|
| product-platform-kit | PLATFORM | shared contracts, policies, skills, SDK sources, conformance |
| product-platform-engineering-team | PLATFORM | engineering orchestration and evidence |
| product-platform-cli | ACTIVE | discovery, proposal, handoff |
| vehicle-tracking | ACTIVE | vehicle tracking product and first commercial reference |
| ai-docs | ACTIVE | document intelligence product |
| bussola-financeira | ACTIVE | financial insight product |
| vehicle-tracking-v2 | REFERENCE | Teltonika/legacy behavior migration source |
| ai-engineering-control-plane | REFERENCE | experimental architecture/benchmarks |
| agents-workspace | ARCHIVE_CANDIDATE | historical agent workspace |
| agentesautonomos | ARCHIVE_CANDIDATE | historical autonomous-agent implementation |
| codex-kit-skills | ARCHIVE_CANDIDATE | historical skills source |

## Archive gate

A repository is archived only after:
1. unique capabilities are inventoried;
2. retained capabilities have a canonical destination;
3. links/documentation point to the destination;
4. no active runtime or CI depends on it.

Archive candidates are not automatically deleted.
