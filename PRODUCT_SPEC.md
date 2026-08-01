# Product specification

## Problem

Film and media teams manage permissions across emails, spreadsheets, contracts, releases, and production tools. A proposed public action may include a performer's likeness, cloned voice, third-party footage, music, artwork, location, or script material without one coherent record showing whether the intended use, channel, territory, dates, commercial scope, modification, and synthetic-media conditions are covered.

## Primary user

Production coordinator, producer, rights-clearance officer, post-production supervisor, distribution reviewer, or creative-agency operations lead.

## Product promise

CINE-GATE discovers possible rights-bearing categories in a proposed action, checks supplied permission metadata, produces an asset-level rights matrix, explains identified issues, routes uncertainty to a human reviewer, and preserves an exportable review and correction record.

## Product limits

CINE-GATE does not authenticate evidence, interpret contracts, establish ownership, issue legal advice, infer consent, or replace qualified professional review.

## Workflow

1. The user describes the production action and release context.
2. The user declares rights-bearing assets and permission metadata.
3. An advisory discovery agent identifies possible undeclared asset categories.
4. A deterministic policy checks coverage, status, dates, action, channels, territory, commercial scope, modification scope, synthetic use, minor-subject authorization, attribution, evidence metadata, and conflicts.
5. The system generates an asset-level rights matrix and readiness metrics.
6. Gemini or a local fallback explains the fixed outcome.
7. The review is persisted with case ID, revision number, input checksum, and workflow events.
8. A named human reviewer may approve or reject. A blocked record cannot be approved, and approval of a review-required record requires a substantive resolution note.
9. When metadata must change, the user creates a corrected revision rather than overwriting the prior record.
10. The full record can be downloaded as evidence JSON, rights-matrix CSV, printable report, or a multi-file release-package ZIP.

## Outcomes

- `CLEARED`: no blocking or unresolved condition is identified in the supplied metadata
- `REVIEW_REQUIRED`: ambiguity, incompleteness, missing scope, or an advisory mismatch requires human review
- `BLOCKED`: a missing, denied, revoked, expired, out-of-scope, incompatible, or explicitly unauthorized record prevents release

## Case and revision model

- one case groups the review history for a proposed production action
- every stored review is immutable except for the final human-decision fields
- corrected metadata creates the next sequential revision
- only the latest revision can be revised, preventing ambiguous branches in the demo workflow
- prior outcomes remain visible for accountability and comparison

## Demo success criteria

- all four prepared scenarios are reproducible
- possible undeclared assets are visibly identified
- missing, expired, revoked, territorially incompatible, channel-incompatible, or prohibited permissions are blocked
- pending and uncertain records reach human review
- a blocked record cannot be human-approved
- a corrected revision can be created without erasing the original record
- rights matrix, readiness metrics, workflow events, input checksum, evidence checksum, evidence JSON, CSV, printable report, and release package are generated
- real Google runtime and IBM Bob evidence are added only after account-stage execution
