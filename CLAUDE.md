# Claude Code instructions

@AGENTS.md

Claude Code MUST treat every rule imported from `AGENTS.md` as mandatory and apply it exactly as Codex Cloud does.

If a nested `CLAUDE.md` or `AGENTS.md` adds stricter directory-specific rules, follow those too. No local instruction may weaken the root safety, branch, CI/readiness, evidence, architecture, or production-approval rules.

<!-- COEVOL-CLAUDE-MODULE-CONTRACT-V1:BEGIN -->
## Module catalog synchronization

Follow the replaceable-module contract in `AGENTS.md`. For every code change and commit, keep `module.yaml`, interface documentation, dependency/call metadata, implementation status, and contract tests synchronized with the implementation. Do not couple consumers to a provider-specific implementation, and never commit secret values.
<!-- COEVOL-CLAUDE-MODULE-CONTRACT-V1:END -->

<!-- MAI-ROUTER-V1:BEGIN -->
@AGENTS.md

# Claude Bootstrap — MAI Router V1

Treat the imported `AGENTS.md` rules as normative. Use the centralized MAI
Router V1 contract at `antonysc/Portfolio@main:mai/v1/MAI_CORE.md` and the
current repository's project profile before planning or editing.

- Route first, then resolve inside the selected scope.
- Activate only the minimum relevant domains and skills.
- Keep assumptions explicit and do not manufacture missing facts.
- Justify any limited scope expansion caused by a real dependency.
- Preserve repository-specific validation, update, safety, and commit rules.
- Produce concrete artifacts and exact validation evidence.
- For any repository-writing mission, enforce the canonical Roadmap V0 gate
  imported through `AGENTS.md`: valid task/lease/write scope before editing,
  immutable claimed missions, fail-closed conflicts, scoped completion evidence,
  and `unknown` rather than invented execution metrics.

Do not fork a separate Claude-specific routing or Roadmap policy. All agent entry
points must converge on the same Portfolio / Workflow / Roadmap behavior.
<!-- MAI-ROUTER-V1:END -->
