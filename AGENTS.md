# Repository agent instructions

## Evolution documentation

`PROJECT_EVOLUTION.md` is the repository's living source of truth for goals, roadmap, cartography, decisions, fixes, rollout, rollback, evidence, and the next action.

For every meaningful change:

1. Read **Start Here**, the affected map, roadmap items, decisions, and release plan before editing.
2. Update `PROJECT_EVOLUTION.md` in the same change as behavior, interfaces, dependencies, architecture, operational risk, fixes, or delivery sequencing.
3. Preserve history: mark abandoned plans and choices `superseded`; never silently delete them.
4. Record expected and actual outcomes. Completed work must link to evidence.
5. Keep rollout gates and rollback triggers executable, including data recovery where relevant.
6. Append the timeline and leave exactly one concrete next step with an owner.

Formatting-only and comment-only edits are exempt.
