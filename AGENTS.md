# Repository agent instructions

This legacy/default branch is not the working branch for coding agents.

Claude Code, Codex Cloud, and other coding agents must:

1. Switch to `main` before editing.
2. Sync the latest `main`.
3. Read and follow `AGENTS.md` from `main` as the authoritative agent contract, including the QLNet evolution trailers/hooks.
4. Work directly on `main`, run relevant validation, commit, and push `main` without a pull request unless the owner explicitly requests a different workflow.
5. Never modify `develop` as part of normal agent work.

Security, production approvals, CI/readiness semantics, evolution documentation, and non-destructive Git rules from `main/AGENTS.md` remain mandatory.

<!-- COEVOL-MODULE-CONTRACT-V1:BEGIN -->
## Versioned replaceable-module contract

Every external provider, repository subsystem, and internal component is a replaceable module behind a versioned contract.

- Depend on contracts, never directly on provider implementations.
- Keep provider-specific behavior behind adapters.
- Declare provided and required interfaces, implementation status, parameters, exposed calls, dependencies, compatibility, and a concise internal design summary in `module.yaml`.
- Update `module.yaml`, interface documentation, implementation evidence, and relevant contract tests in the same commit whenever code changes those facts.
- A change is incomplete when implementation, tests, documentation, and the module catalog disagree.
- Breaking changes require a new contract version plus an explicit migration and rollback path.
- Keep dependency and call metadata explicit so repository-wide and internal graphs can be generated automatically.
- Never place secret values in the repository or module catalog.

The same boundary rule applies inside the repository: internal components communicate through explicit, testable interfaces.
<!-- COEVOL-MODULE-CONTRACT-V1:END -->

<!-- MAI-ROUTER-V1:BEGIN -->
# Agent Bootstrap — MAI Router V1

This repository participates in the centralized Portfolio / Workflow
orchestration. The canonical routing contract is
`antonysc/Portfolio@main:mai/v1/MAI_CORE.md`; its machine contracts and
registries live beside it in `mai/v1/`.

## Required behavior

- Use MAI Router V1 as the default routing and execution model.
- Determine the active project, repository, and sub-scope before acting.
- Stay strictly inside that scope and activate only the minimum useful domains
  and skills; normally select two to five domains.
- Do not expand into unrelated general knowledge, literary work, or unchecked
  speculation unless the request explicitly requires it.
- Never invent missing project facts. Mark assumptions and uncertainty.
- If a real dependency appears during execution, perform one minimal routing
  expansion and record why it was necessary.
- Prefer concrete outputs: specifications, plans, code, tests, workflows,
  project updates, and validation evidence.
- Follow the repository's local safety, validation, update, and commit rules.
  A local rule may tighten the central contract, but must not silently weaken it.

## Roadmap V0 execution gate

Canonical coordination state lives in `antonysc/Portfolio@main:roadmap/`.
For repository-writing work, route first and then require a Roadmap task claim
before editing. The canonical policy is `roadmap/POLICY.md`.

- A generated mission/prompt must be registered and historized before execution.
- Unclaimed work may be consolidated, split, deduplicated, reordered or superseded while preserving lineage; claimed work is immutable for that execution.
- Before writing, require a valid `task_id` and active lease whose exact write scope covers the intended paths/resources. Never widen scope silently.
- V0 permits exactly one active repository-writing execution per repository. A live writer claim on the same repository blocks every other writing mission even when paths do not overlap.
- Fine-grained write scopes/protected resources remain mandatory for audit, completion checks and a future optimized scheduler, but do not enable intra-repository parallel writers in V0.
- Different repositories may execute concurrently when cross-repository protected resources do not conflict. Read-only overlap is allowed.
- New requirements overlapping active work become pending updates; do not mutate the active mission under the worker.
- Heartbeat/TTL expiry never authorizes blind takeover: mark stale, reconcile branch/commit/PR/diff evidence, then explicitly recover/release with a new lease if reassigned.
- Before completion, compare actual changed paths with the authorized scope and run repository-local validation. Out-of-scope changes are not `DONE`.
- Completion evidence must include all related commits/PRs, evolution updates, requested model/provider, actual model/provider when observable, elapsed time, and input/output/context/total token, credit and EUR-cost metrics when observable. Record `unknown` when unavailable; never fabricate.
- Preserve Roadmap history for ingestion, consolidation, claim, conflict, heartbeat, scope extension, completion, failure, stale/recovery and supersession.
- Durable execution prompts live under `antonysc/Portfolio@main:roadmap/prompts/<mission_id>/`; resolve the mission/task prompt there instead of reconstructing it from chat history.
- Use `roadmap/missions/MISSIONS.md` and mission-local files for durable references; `QUEUE.yaml` remains canonical operational state and `HISTORY.jsonl` canonical lifecycle evidence.
- Before claiming new work, challenge structurally mutable unclaimed tasks for overlap, duplication, dependencies and protected-resource conflicts; merge, deduplicate, split or supersede before dispatch while preserving lineage.

Roadmap coordinates work; it does not replace repository-local validation,
security, ownership or canonical domain contracts.

## Routing result

For each task, determine the routing decision, active scope, active domains,
excluded domains, execution plan, expected artifacts, assumptions, and
out-of-scope items. Render those fields only when they help review or resolve
ambiguity; the routing contract is required even when its presentation remains
implicit.

The governing question is: **what is the smallest useful scope that can move
this task forward correctly?**

Repository routing: `QLNet` uses profile `finance_quant` (revision `1.0.0`); canonical registry: `antonysc/Portfolio@main:mai/v1/PROJECT_SCOPE_REGISTRY.yaml`.
<!-- MAI-ROUTER-V1:END -->
