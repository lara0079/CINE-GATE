# Decision log

## 2026-08-01: Establish an independent project boundary

CINE-GATE is a narrow film-rights metadata workflow and does not contain unrelated proprietary source code, confidential schemas, private algorithms, internal control mechanisms, or unpublished roadmap material.

## 2026-08-01: Advisory AI, deterministic outcome

The rights-discovery agent may flag possible undeclared asset categories. Permission status, scope, dates, territory, evidence metadata, and the recorded outcome remain deterministic. Gemini explains the result but cannot alter it.

## 2026-08-01: No approval of blocked records

A human reviewer can reject any record and can approve cleared or review-required records. The API refuses approval of a blocked record. Corrected metadata requires a new review.

## 2026-08-01: Evidence references, not private documents

The MVP stores evidence references and types rather than contract contents. This limits accidental disclosure in the open-source demo.

## 2026-08-01: Honest cloud and IBM evidence

Local code and deployment scaffolding can be prepared before account access. Real Google Cloud deployment, Agent Engine traces, and IBM Bob participation will be claimed only after actual execution through Maria Kollia's accounts.

## 2026-08-01: Explicit release scope rather than implicit assumptions

The product records distribution channels, commercial use, modification, synthetic-media use, guardian authorization, and attribution requirements as structured metadata. Missing scope is routed to review; explicit incompatibility is blocking.

## 2026-08-01: Asset-level rights matrix

The product presents one status row per declared asset so a reviewer can identify the exact item requiring correction instead of relying only on a single aggregate outcome.

## 2026-08-01: Content checksum with limited claim

The evidence export includes a reproducible SHA-256 checksum over the stored review and workflow events. It is labelled as a content-integrity checksum, not a signature, timestamp, document authentication mechanism, or legal proof.

## 2026-08-01: Corrected records create revisions

A blocked or incomplete record is not overwritten. The latest review may be used to create one sequential corrected revision. Earlier revisions remain visible, and attempts to branch from a superseded revision are rejected.

## 2026-08-01: Separate input and evidence checksums

The input checksum represents the exact submitted production-action metadata. The evidence checksum represents the stored review and workflow events. Neither checksum is described as a signature or authentication of an underlying permission document.

## 2026-08-01: Multi-file release package

The product exports evidence JSON, rights-matrix CSV, printable report, README, and a manifest in one ZIP. The manifest records a SHA-256 checksum and byte count for each included file.

## 2026-08-01: Accessibility is part of product quality

Milestone 5 adds keyboard tab navigation, a skip link, visible focus, live status announcements, reduced-motion handling, and accessible finding disclosures. Hosted-stage audits remain required.
