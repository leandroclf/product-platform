## MODIFIED Requirements

### Requirement: R2 work follows repository-specific approval rules
R2 work MUST remain blocked by default in the local CLI. The operator MAY explicitly authorize an individual task up to R2 with `ai-team run --authorize-r2`. The coordinator MUST bind that authorization to the exact repository, base revision and request, MUST independently classify actual changed paths, and MUST require configured specialized checks for sensitive paths. This authorization MUST NOT permit R3 or delivery of an R2 task.

#### Scenario: R2 task lacks explicit operator flag
- **WHEN** a plan is classified R2 and the run was started without `--authorize-r2`
- **THEN** the coordinator stops before implementation

#### Scenario: Operator explicitly authorizes an R2 task
- **WHEN** a plan is classified R2 and the run was started with `--authorize-r2`
- **THEN** the coordinator may continue through isolated implementation, checks and independent review
- **AND** the authorization matches the repository, base SHA and request hash
- **AND** R2 delivery remains blocked

#### Scenario: Plan is classified R3
- **WHEN** any plan is classified R3, including a run started with `--authorize-r2`
- **THEN** the coordinator stops before implementation

#### Scenario: Actual changes touch a sensitive path
- **WHEN** an R2-authorized implementation changes a sensitive path
- **THEN** the independent path classifier applies
- **AND** the required specialized offline quality check must be configured and pass before review

### Requirement: Reviews receive the complete changed-file patch
The coordinator MUST include every changed path in the validation and review patch, including files under `openspec/changes/ai-team-*`. Generated task records MAY be excluded from the no-progress fingerprint only for the current task; files under other `ai-team-*` paths MUST remain visible to risk classification.

#### Scenario: Product file uses the ai-team prefix
- **WHEN** a change modifies `openspec/changes/ai-team-older/security-policy.md`
- **THEN** the file appears in both independent review patches
- **AND** it is included in path classification and requires `security_and_approval`
