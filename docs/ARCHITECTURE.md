# CINE-GATE architecture

## Design objective

CINE-GATE demonstrates a focused agentic film-rights workflow without exposing or recreating unrelated proprietary architectures.

## Components

### Browser client

The single-page interface supports scenario loading, release-context entry, multi-asset permission records, review execution, findings, rights matrix, readiness metrics, agent hints, workflow trace, human decision, corrected revisions, case lineage, searchable history, checksum verification, evidence export, CSV export, release packages, and printable reporting.

### Rights-discovery agent

The discovery agent analyses the action description for possible rights-bearing categories. Local mode uses transparent keyword discovery. Google mode uses Gemini with structured JSON output. Its findings are advisory and cannot create consent, alter records, or determine the final outcome.

### Deterministic clearance policy

The policy evaluates supplied records for:

- asset coverage
- granted, pending, denied, unknown, or revoked status
- permitted production action
- distribution-channel coverage
- territory coverage
- validity on the planned action date
- commercial-use scope
- modification or adaptation scope
- explicit synthetic-use authorization
- guardian authorization for a declared minor subject
- attribution requirements
- evidence reference, type, and optional SHA-256 fingerprint
- conflicting permission records
- possible undeclared assets identified by the advisory agent

### Finding catalog

Every finding code maps to a stable category, a reviewer-facing title, and a corrective action. The catalog improves explainability without allowing the agent to change the policy outcome.

### Rights matrix and readiness engine

The engine produces one `covered`, `review`, or `blocked` row for every declared asset. It also calculates asset coverage, evidence completeness, blocking counts, warning counts, and required actions.

### Explanation adapter

Gemini may explain the deterministic findings. It cannot change the outcome or invent missing permissions. A local explanation remains available if Google mode is unavailable.

### Review service

The service coordinates discovery, policy evaluation, matrix assembly, readiness calculation, explanation, persistence, workflow events, revision creation, human decision, evidence checksums, exports, and release-package generation.

### SQLite repository

The local product stores review JSON and workflow events in SQLite. Searchable columns support project, action, outcome, case ID, and revision sequence. File-based deployments use WAL mode and a busy timeout. Readiness includes SQLite `quick_check`. This is a project-specific persistence layer and is not derived from any unrelated proprietary database design.

### Case lineage

Each first review creates a case. Corrected reviews preserve the case ID, increment the revision number, and reference the review they supersede. A linear latest-revision rule prevents ambiguous parallel branches in the demo.

### Evidence and release package

The evidence JSON contains the review, workflow events, and a reproducible SHA-256 checksum calculated over canonical serialized content. The input checksum independently represents the exact submitted metadata. The release-package ZIP contains:

- evidence JSON
- printable HTML report
- rights-matrix CSV
- explanatory README
- manifest with file checksums and byte counts

The checksums are integrity aids, not digital signatures or authentication of the underlying source documents.

### Vertex AI Agent Engine scaffold

A separate ADK package defines the deployable advisory discovery agent and tool functions. It remains separate until real account-stage deployment.

## Request flow

1. The user describes a production action, release context, assets, and permission metadata.
2. The discovery agent identifies possible additional rights-bearing categories.
3. The deterministic policy evaluates the supplied metadata.
4. The system builds the asset-level rights matrix and release-readiness record.
5. The narrative adapter explains the fixed result.
6. The review and workflow events are persisted with case and revision metadata.
7. A human reviewer may approve or reject, except that a blocked record cannot be approved.
8. Corrected metadata creates a new sequential revision.
9. The complete record can be exported as JSON, CSV, HTML, or a release-package ZIP.
