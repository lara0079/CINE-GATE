# Privacy and data handling

## Current MVP

The local MVP stores structured metadata and evidence references in SQLite. It does not require contract files, identity documents, signatures, audio recordings, or production footage to be uploaded.

## Demo-data rule

Use synthetic names, fabricated references, and non-sensitive example metadata in public demos. Do not place private contracts, performer information, personal contact details, unpublished footage, or real signatures in the public repository or hosted demonstration.

## Export rule

Evidence JSON, CSV, reports, and release packages may contain all metadata entered by the user. Before sharing an export, confirm that evidence references and names are suitable for the intended recipient.

## Production recommendations

A production deployment should add:

- authenticated users and role-based access
- private object storage for evidence files
- encryption and managed secrets
- retention and deletion rules
- access logging
- tenant separation
- regional and contractual data-governance controls
- professional legal and security review

## Checksum limitation

Input and evidence checksums detect whether the relevant serialized content has changed between calculations. They are not digital signatures, timestamping services, document authentication mechanisms, or proof that a permission is legally valid.
