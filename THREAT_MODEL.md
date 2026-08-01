# Threat model and safety limits

## Protected interests

- performer and contributor rights
- production decision quality
- integrity of supplied metadata
- traceability of human decisions and corrections
- confidentiality of private evidence documents
- separation of CINE-GATE from unrelated proprietary and confidential material

## Primary threats

### Invented consent

An AI model may phrase an inference as if permission exists. CINE-GATE makes the deterministic record the source of the outcome and instructs the model never to create permission.

### Incomplete asset inventory

A user may omit voice, music, footage, artwork, or likeness material. The advisory discovery agent flags strongly implied undeclared categories and routes them to human review.

### Out-of-scope use

A valid permission may not cover the proposed action, channel, territory, commercial use, modification, or synthetic transformation. The policy checks these conditions explicitly.

### Expired, denied, or revoked permission

The workflow checks the planned action date and treats denied or revoked records as blocking.

### Sensitive synthetic persona use

AI-generated likeness or voice requires explicit synthetic-use authorization and a recorded evidence reference. Missing or negative authorization blocks the record.

### Minor-subject risk

A declared minor subject requires explicit guardian authorization in the permission record.

### Human override of a blocked record

The API rejects attempts to approve a `BLOCKED` review. The records must be corrected in a new revision.

### History erasure or ambiguous correction

The product does not overwrite a prior review. Corrected records create a sequential revision. A superseded revision cannot create a competing branch after a newer revision exists.

### Rewriting a finalized decision

The API prevents a second final human decision on the same stored review.

### Evidence leakage

The MVP stores evidence references and optional fingerprints, not uploaded contract contents. Public demos must use fabricated data. Production deployment should use authenticated private storage and avoid public evidence URLs.

### Checksum overclaim

SHA-256 values are labelled as content checksums only. They are not presented as digital signatures, legal proof, trusted timestamps, or authentication of an underlying document.

### Export tampering

The release-package manifest records a checksum and byte count for every included file. This detects changed export bytes but does not identify the person who changed them.

### Prompt injection

The action description is treated as data. Google prompts define a narrow output schema and the agent cannot call a tool that changes permission status or the final decision.

### Denial through oversized requests

The web service rejects request bodies larger than one megabyte. Pydantic field and collection limits provide additional bounds.

### Proprietary-architecture leakage

The repository excludes unrelated proprietary code, confidential schemas, private algorithms, internal control mechanisms, experimental assets, and unpublished roadmap material.

## Non-goals

CINE-GATE does not verify signatures, interpret contracts, resolve ownership disputes, determine legal validity, or replace professional review.
