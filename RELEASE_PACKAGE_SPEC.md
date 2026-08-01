# Release package specification

## Endpoint

```text
GET /api/reviews/{review_id}/release-package
```

## Files

- `evidence.json`: complete stored review and workflow events
- `release-report.html`: printable reviewer-facing report
- `rights-matrix.csv`: asset-level clearance matrix
- `README.txt`: package purpose and limitations
- `manifest.json`: package metadata and file integrity information

## Manifest fields

- schema version
- generation timestamp
- case ID
- review ID
- revision number
- input checksum
- evidence-content checksum
- SHA-256 checksum and byte count for every package file except the manifest itself

## Integrity limitation

The checksums can detect changes to the exported bytes. They do not prove who created a file, when an underlying contract was signed, or whether a permission is legally valid.
