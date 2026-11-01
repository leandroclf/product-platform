# UI Skill

## Activate when
The task changes layouts, components, styling, responsiveness, accessibility or user interaction.

## Guidance
- First understand the existing design system and component library.
- Reuse tokens and components before introducing alternatives.
- Preserve responsive behavior across supported breakpoints.
- Treat accessibility as a requirement: semantic structure, keyboard operation, focus, labels and contrast.
- Check loading, empty, error, disabled and success states.
- Avoid visual redesign outside the requested scope.
- Use browser verification for every new or materially changed user flow. A passing build or static code review does not prove that an interface is usable.

## Product experience loop

For a new frontend or a material UI/interaction change, complete this loop within the authorized task and its time/cost budget:

1. **Understand the product.** Identify the user, primary task, successful outcome and existing navigation, data/API contracts, brand and design-system constraints. Inspect the target routes and neighboring flows before editing.
2. **Set a deliberate design direction.** Use an authorized screenshot, mockup, recording or Figma reference when one exists. Otherwise derive a concise direction from the product, audience and existing brand, and record the key assumptions in the task UX spec. Do not default to a generic dashboard or invent a reference.
3. **Build a working vertical slice.** Implement the real user path and meaningful states. Controls must perform their stated action; avoid dead buttons, decorative controls that imply functionality, and success states unsupported by the product behavior.
4. **Render and interact.** Use a browser-capable local/preview runner or a trusted host-controlled frontend check. Inspect the changed route at relevant desktop and mobile viewports. Exercise the actual path with mouse/touch and keyboard as applicable. Check focus, validation, navigation, loading, empty, error, disabled and success states that apply.
5. **Review the rendered result and iterate.** Compare it with the task's direction/reference, inspect accessibility and responsive behavior, then correct visible or interaction defects. For visual-feedback tasks, use the existing v2 task/evidence contract and its bounded iteration budget. Inspect screenshots directly; a report that says a screenshot passed is not a substitute for viewing it.
6. **Report evidence honestly.** Link the tested HEAD, routes/viewports, interaction results, screenshots and checks. Make screenshots and reports available to the independent validator/reviewer. Separate visual, functional, accessibility and performance conclusions. If the browser, reference, evidence handoff, or required state cannot be exercised, mark it not evaluated or blocked; do not report acceptance from code inspection alone.

## Runner responsibilities and current ai-team limit

The profile selects guidance; it does not install Playwright, grant browser access or create a runner. In the canonical `ai-team` workflow, the isolated implementation stage has no Bash or MCP access. A configured `quality_checks.frontend` command runs in the host-controlled offline test container and is the place for browser automation when that image includes a pinned browser runtime. The command configuration is operator-supplied and the host verifies its exit status, not that it truly ran Playwright or the visual-feedback validator.

The current `ai-team` test handoff provides validation/review with bounded text output in `tests.json`; it does not transfer screenshot binaries for direct inspection. Therefore that workflow cannot claim visual acceptance from the check summary alone. Until an approved artifact handoff makes the screenshots and per-criterion evidence available to the independent stages, report visual review as not evaluated/blocked. This documents a platform gap; it is not an implemented browser runner.

Keep the design system and data ownership canonical. Do not copy generated code or assets between products, add a new UI framework, or introduce global event/state abstractions unless the task demonstrates a concrete need. For a copy-only or non-visual change, use the smallest relevant checks instead of producing unnecessary screenshots.

## Reference patterns

- [screenshot-to-code](https://github.com/abi/screenshot-to-code): accept visual references and inspect the rendered result in a browser; generated markup is a starting point, not the product's architecture.
- [Godogen](https://github.com/htdt/godogen): run the generated interactive experience and use observed behavior/recording as evidence, not a successful compile alone.
- [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios): keep UX, implementation, QA and regression responsibilities explicit. Reuse that separation within the existing stages; do not import its large agent hierarchy or human approval flow as a technical dependency.

These are workflow patterns, not adopted runtimes. Preserve the platform's existing agent stages, product-owned UI implementation, and approval gates.

## Note
This is a neutral compatibility layer. When the team's exact external UI skill/plugin is selected, reference or install it explicitly rather than guessing from the informal name `Skill UI`.