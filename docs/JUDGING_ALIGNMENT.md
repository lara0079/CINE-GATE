# Judging alignment

## Technical implementation

CINE-GATE provides a functioning FastAPI application, accessible browser interface, persistent case and revision storage, deterministic policy, advisory agent layer, finding catalog, evidence exports, human decision workflow, release-package generation, 50 tests, Cloud Run configuration, and Vertex AI Agent Engine scaffold.

## Product design

The product is organized around a recognizable film-production task. The interface supports repeatable scenarios, structured asset declarations, permission scope, readable outcomes, an asset-level rights matrix, release-readiness indicators, corrective guidance, case revisions, workflow history, reviewer actions, and production-ready exports.

## Potential impact

The product addresses a concrete operational gap between fragmented rights records and a proposed release action. It is relevant to producers, production coordinators, post-production teams, rights-clearance officers, distributors, and creative agencies.

## Originality

The distinctive product choice is not to ask an AI model to make a legal clearance decision. The agent discovers possible rights-bearing material and explains findings, while a transparent deterministic policy evaluates supplied metadata. Unresolved conditions are routed to a named human, and corrected metadata creates a new review revision rather than erasing the original record.

## Demonstration discipline

The final demo should prove:

1. one complete case clears
2. one incomplete case reaches human review
3. one incompatible case is blocked
4. a blocked case cannot be approved
5. a corrected revision preserves the original result and produces a new outcome
6. the release package contains evidence JSON, CSV, report, and file checksums
7. the Google runtime and IBM Bob contribution are real and documented
