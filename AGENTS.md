# Repository agent instructions

## Evolution documentation

`PROJECT_EVOLUTION.md` is the living source of truth for goals, roadmap,
cartography, decisions, fixes, rollout, rollback, evidence, and the next action.

For every meaningful source commit:

1. Read **Start Here**, the affected roadmap items, decisions, and release plan.
2. Add every mandatory `Evolution-*` trailer from `.gitmessage-evolution.txt`.
3. Use `Evolution-Refs: auto` only when no stable roadmap, change, fix, decision,
   or release identifier exists yet.
4. Run `python tools/evolution.py generate --commit HEAD` before pushing. The
   pre-push hook rejects a missing immutable record.
5. Do not hand-edit marker-managed blocks. The deterministic renderer owns them.
6. Update human-authored goals, cartography, decisions, risks, and delivery
   choices when the commit changes high-level truth; preserve superseded history.
7. Keep rollout and rollback instructions executable and leave a concrete next
   action with an owner and date.

Install the repository hooks once per clone with:

```text
python tools/evolution.py install-hooks
```

Fork pull requests must include locally generated records because GitHub cannot
write into a fork branch. Markdown, comments, governance, CI rules, and generated
evolution files are exempt from commit trailers.

