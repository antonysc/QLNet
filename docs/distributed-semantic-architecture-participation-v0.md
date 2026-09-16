# Distributed semantic architecture participation V0

Repository: `antonysc/QLNet`  
Registration status: `REGISTERED`  
Runtime status: `NOT_ACTIVATED`  
Readiness claim: `NOT_ASSESSED_BY_THIS_RECORD`  
Trace: `TRACE-20260916-DISTRIBUTED-METAMODEL-V0-PORTFOLIO`

## Authority and boundary

The canonical V0 semantic contract is owned by [Pod at commit `974b94295272b8ddb582b659bc4e012ebe63eeec`](https://github.com/antonysc/Pod/tree/974b94295272b8ddb582b659bc4e012ebe63eeec). This repository does not fork or redefine that authority.

Portfolio role: **domain implementation candidate**.

Provide replaceable quantitative algorithms behind canonical pricing and risk capabilities.

Candidate capability surface: `Pricing.Calculate, Risk.Calculate`.

Primary relation to the portfolio: implements Finance capabilities through an explicitly versioned adapter.

This registration does not change the repository's existing goal, implementation, dependencies, CI readiness, deployment state, credentials, provider connections, or production approval. Repository-owned `PROJECT_EVOLUTION.md`, machine-readable project state, and domain contracts remain authoritative where present.

## Shared semantic invariant

```text
Concept
→ Data Model / Semantic Model
→ Relation
→ Capability / Contract
→ Constraint / Policy
→ Execution Graph
→ Placement Plan
→ Technical Mapping / Implementation
```

Technology names belong only to technical mappings and implementations. Relations are first-class and versioned. Planning consumes an immutable observation snapshot. Missing facts for hard constraints fail closed. Every generated representation declares any semantic loss.

## Integration gate

Before this repository participates in live cross-repository execution, it must:

1. publish a repository-owned, versioned profile that imports the canonical contract;
2. validate identifiers, relations, units, versions, permissions, and hard constraints;
3. resolve a deterministic execution and placement plan from a recorded observation snapshot;
4. bind technology/provider adapters only at the implementation layer;
5. retain evidence, rollback instructions, and any required approval.

Until those gates are evidenced, this file is a documentation-level registration only.

## Evidence

- Canonical design: [`antonysc/Pod@974b942`](https://github.com/antonysc/Pod/commit/974b94295272b8ddb582b659bc4e012ebe63eeec)
- Initial governance record: [`antonysc/Setup@991fabf`](https://github.com/antonysc/Setup/commit/991fabf2ee22acdda1f02c54b20aaee2ea302967)
- Portfolio propagation trace: `TRACE-20260916-DISTRIBUTED-METAMODEL-V0-PORTFOLIO`
