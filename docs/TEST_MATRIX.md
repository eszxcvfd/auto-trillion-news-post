# Test Matrix

This file maps product behavior to proof.

Product behavior is now defined by `SPEC.md`, split further by
`docs/product/*`, and partially implemented in the current brownfield repo.

The durable story state in `scripts/bin/harness-cli query matrix` is the
operational source for proof status. This file is the human-readable contract
view of that matrix.

## Status Values

| Status | Meaning |
| --- | --- |
| planned | Accepted as intended behavior, not implemented |
| in_progress | Actively being built |
| implemented | Implemented and proof exists |
| changed | Contract changed after earlier implementation |
| retired | No longer part of the product contract |

## Matrix

| Story | Contract | Unit | Integration | E2E | Platform | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US-001 | Local project setup and baseline CLI bootstrap | yes | yes | no | no | implemented | Durable matrix row in Harness CLI |
| US-002 | Keyword search, trillion filtering, and deduplication | yes | yes | no | no | implemented | Durable matrix row in Harness CLI |
| US-003 | Screenshot capture and internal workbook persistence | yes | yes | no | no | implemented | Durable matrix row in Harness CLI |
| US-004 | AI draft generation and post validation | yes | yes | no | no | implemented | `python3 -m unittest discover tests` covering validation and post file writing |
| US-005 | Assisted LinkedIn posting baseline | yes | yes | no | no | implemented | `python3 -m unittest discover tests` covering markdown parsing, path resolution, and Playwright integration mocks |
| US-006 | Business workbook ingestion and dual-contract mapping | no | no | no | no | planned | Spec accepted; implementation not started |
| US-007 | Shared posting core, `Link Post` parser, and selective posting | no | no | no | no | planned | Spec accepted; implementation not started |
| US-008 | Result write-back, backup safety, and retry semantics | no | no | no | no | planned | Spec accepted; implementation not started |
| US-009 | Web UI operator surface | no | no | no | no | planned | Spec accepted; implementation deferred |
| US-010 | Local scheduling and run history | no | no | no | no | planned | Spec accepted; implementation deferred |

## Evidence Rules

- Unit proof covers pure domain and application rules.
- Integration proof covers backend enforcement, data integrity, provider
  behavior, jobs, or service contracts.
- E2E proof covers user-visible browser flows.
- Platform proof covers only shell, deployment, mobile, desktop, or runtime
  behavior that cannot be proven in lower layers.
- A story can be implemented without every proof column if the story packet
  explains why.
- Do not mark `US-006` and later rows implemented until durable Harness story
  state and real validation evidence have both been updated.
