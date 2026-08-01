# CINE-GATE development contract

## Product objective
Build a production-quality, open-source film-production rights workflow for the Google Cloud Agentic Cinema IBM track. The application discovers possible rights-bearing assets, checks supplied permission metadata, creates a reviewable matrix, and routes unresolved cases to a named human reviewer.

## Non-negotiable boundaries
- This repository is new and independent. Do not import, copy, infer, reconstruct, or describe unrelated proprietary code, schemas, endpoints, algorithms, confidential research, or unpublished roadmap material.
- AI is advisory. It may discover categories and explain findings, but it may not invent permission, authenticate documents, provide legal advice, or alter the deterministic outcome.
- A BLOCKED record cannot be approved. Corrected data must create a new linked revision.
- Never place credentials, API keys, personal data, or private evidence in prompts, source files, screenshots, or commits.

## IBM Bob task scope
Use Bob for bounded, reviewable SDLC work such as:
1. review the public CINE-GATE repository against a stated issue
2. propose a plan before editing
3. implement only approved changes
4. run tests and report exact results
5. generate an evidence note describing files changed and commands run

## Quality gate
Before accepting a change, run:

```bash
python -m pytest -q
python scripts/run_quality_gate.py
```

Reject changes that weaken the product boundary, remove safeguards, fabricate integration evidence, or expose private material.
