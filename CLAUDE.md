# Claude Code instructions

@AGENTS.md

Claude Code MUST treat every rule imported from `AGENTS.md` as mandatory and apply it exactly as ChatGPT/Codex does. Nested `CLAUDE.md` or `AGENTS.md` files may add stricter directory-specific rules but may not weaken the root contract.

## Synchronous multi-agent coordination

Claude Code operates in the same live workstream as ChatGPT/Codex. Git and the repository's tracked coordination artifacts are the shared source of truth; chat context alone is never authoritative.

Before editing:

1. Synchronize and inspect the latest `main`.
2. Read the applicable agent instructions, project evolution, machine-readable project state, task ownership, and lock files when present.
3. Inspect current code, tests, history, and uncommitted or concurrent work before deciding what remains to do.

While working:

- Never assume exclusive repository or file ownership.
- Honor active task claims and locks; avoid duplicating work already completed or in progress.
- Keep the task bounded and changes separable from unrelated concurrent work.
- If `main` or an overlapping file changes, re-read the new state and reconcile both intentions without discarding either agent's work.
- Communicate durable state through tracked project/task/evolution artifacts required by `AGENTS.md`; do not rely on hidden session memory.

Before pushing:

1. Re-check `main` immediately before commit and integrate concurrent changes without force-pushing.
2. Run the relevant validations and review the final diff.
3. Produce one coherent commit per repository for the task, push directly to `main`, and leave an explicit handoff: completed, in progress, blocked, validation evidence, and the single next action.
