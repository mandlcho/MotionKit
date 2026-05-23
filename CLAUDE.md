# sp-cloth Feature Notes

This branch (`feature/sp-cloth-pipeline`) implements the sp-cloth pipeline — driver-driven cloth attachment automation for 3dsmax. Design + plan live under `sp-cloth/plan/`.

## Plan progress tracking (REQUIRED)

The Phase 1 implementation plan lives at `sp-cloth/plan/2026-05-17-phase1-implementation.md`. It uses GitHub-flavored checkboxes (`- [ ]`) at every step.

**When you finish a unit of work that corresponds to one or more checkboxes in the plan, tick them in the same commit that delivers the work.** Change `- [ ]` to `- [x]` for each completed item.

### Rules for ticking
- Only tick when work is genuinely complete: code written, tests passing, manual verification done if the step requires it, commit made.
- Tick at the finest matching granularity (every completed step, not just the task header — unless every sub-step was also completed in the same commit).
- If you complete a whole task, tick all its sub-steps too.
- Never tick speculatively. The plan IS the source of truth for what's done vs not. Keep it honest.
- If you partially complete a step, leave it unticked and note the partial state in the commit message.

### How to recognize "the corresponding checkbox"
Each plan step starts with an owner tag (`[AGENT]` or `[HUMAN]`) and a step number (e.g., `Step 1.2.3`). Use those to match the work you just did to the right checkbox.

## Where things live

| Path | What it is |
|---|---|
| `sp-cloth/plan/` | Design spec + Phase 1 implementation plan (source of truth) |
| `sp-cloth/src/sp_cloth/` | Python package (will populate as Phase 1 lands) |
| `sp-cloth/configs/` | Materials, body types, character presets |
| `sp-cloth/tests/` | pytest tests (no 3dsmax dependency) |
| `max/tools/cloth/` | MotionKit menu entries — currently stubs, replaced as stages land |
| `config/config.json` | "Cloth" category added to `max.tool_categories` |
| `localization/en.json` | `menu.cloth` key added |

## Branch hygiene

- Don't touch existing tools under `max/tools/animation/`, `max/tools/modeling/`, etc. — the sp-cloth feature is fully isolated under `max/tools/cloth/` and `sp-cloth/`.
- Don't merge to `main` until Phase 1 is complete and reviewed.
- Use the existing MotionKit code style (see `AGENTS.md`).
