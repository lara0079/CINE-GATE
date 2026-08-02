# Corrected-review revision workflow

## Purpose

A permission record may be corrected after a blocked or review-required result. CINE-GATE preserves the original review and creates a new revision instead of silently editing history.

## Rules

- the first review in a case is revision 1
- a new revision retains the same case ID
- the revision number increases by one
- the new review records the review it supersedes
- only the latest revision may be revised
- every revision receives a new input checksum and independent outcome
- a human decision on one revision does not automatically transfer to another revision

## API

```text
POST /api/reviews/{review_id}/revisions
GET  /api/reviews/{review_id}/lineage
```

The revision request body is a complete `ProductionAction`. The response is a new `ClearanceReview`.

## Scope boundary

This workflow is a narrow correction history for a film-rights record. It does not implement or disclose unrelated proprietary mechanisms or enterprise architecture.
