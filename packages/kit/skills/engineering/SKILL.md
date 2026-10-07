# Engineering Skill

## Purpose
Provide stack-agnostic implementation discipline.

## Workflow
1. Discover repository instructions, architecture, dependencies and affected boundaries.
2. State important assumptions and resolve blocking ambiguity from code/docs before implementation.
3. Preserve public contracts unless the requested change explicitly modifies them.
4. Follow existing patterns before introducing new abstractions or dependencies.
5. Keep changes cohesive and minimize unrelated formatting/refactoring.
6. Handle errors explicitly and preserve observability where the project has it.
7. Update documentation/configuration when behavior or setup changes.
8. Hand off to the testing skill for verification.

## Quality bar
Changes should be understandable, maintainable, secure by default and supported by evidence rather than agent confidence.
