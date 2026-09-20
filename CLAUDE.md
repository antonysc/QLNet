# Claude Code instructions

@AGENTS.md

Claude Code MUST treat every rule imported from `AGENTS.md` as mandatory and apply it exactly as Codex Cloud does.

If a nested `CLAUDE.md` or `AGENTS.md` adds stricter directory-specific rules, follow those too. No local instruction may weaken the root safety, branch, CI/readiness, evidence, architecture, or production-approval rules.

<!-- COEVOL-CLAUDE-MODULE-CONTRACT-V1:BEGIN -->
## Module catalog synchronization

Follow the replaceable-module contract in `AGENTS.md`. For every code change and commit, keep `module.yaml`, interface documentation, dependency/call metadata, implementation status, and contract tests synchronized with the implementation. Do not couple consumers to a provider-specific implementation, and never commit secret values.
<!-- COEVOL-CLAUDE-MODULE-CONTRACT-V1:END -->
