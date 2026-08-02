CINE-GATE

**Bounded multi-agent rights discovery, deterministic release control, and accountable human review for film production.**

CINE-GATE is a new, independent hackathon project for the Google Cloud Agentic Cinema IBM track. It helps production teams identify possible rights-bearing assets, compare supplied permission metadata with a proposed release, explain exceptions, and create a reviewable release package before publication.

CINE-GATE is not a legal oracle. It is a new, domain-specific hackathon project with a deliberately bounded scope.

 Milestone 5 - Competition Edition

- premium responsive production-rights command interface
- five-layer bounded workflow: Rights Scout, Scope Controller, Evidence Mapper, Release Brief Agent, Human Control Plane
- Gemini runtime adapter with fail-safe local fallback
- deployment-ready Google ADK multi-agent package using parallel discovery and sequential synthesis
- Vertex AI Agent Engine deployment configuration with Cloud Trace enabled
- transparent agent run ID, workflow version, model, latency, provider, guardrail, and fallback status
- release-risk profile with explainable signals rather than an opaque legal score
- measurable workflow indicators derived from the actual review record
- deterministic checks for permission status, use, channel, territory, dates, commercial scope, modification scope, synthetic media, minor-subject authorization, attribution, evidence metadata, and conflicting records
- rights matrix, release readiness, human decision safeguards, linked revision history, audit timeline, and evidence checksums
- downloadable evidence JSON, rights-matrix CSV, printable report, and release-package ZIP with manifest checksums
- IBM Bob workspace protection, bounded tasks, and evidence runbook
- Cloud Run deployment assets, security headers, readiness checks, and request timing
- 57 automated tests plus an 8-scenario quality gate

## Decision boundary

Agents may discover possible rights categories and explain recorded findings. They may not:

- invent or establish permission
- authenticate a contract, signature, license, release, or consent form
- provide legal advice
- alter the deterministic `CLEARED`, `REVIEW_REQUIRED`, or `BLOCKED` outcome
- approve a blocked record

A named human records the final workflow decision. Corrected data creates a linked revision rather than overwriting history.

## Local start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Quality gate

```bash
python -m pytest -q
python scripts/run_quality_gate.py
```

Expected Milestone 5 result:

```text
57 passed
quality_gate: passed (8/8 scenarios)
```

## Google mode

Copy `.env.example` to `.env` and configure Google Cloud:

```text
CINE_GATE_AGENT_MODE=google
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-3.5-flash
```

The FastAPI service calls Gemini for advisory rights discovery and explanation. The deterministic policy remains the source of the recorded outcome.

The separate `deployment/agent_engine` package contains the Google ADK multi-agent workflow prepared for Vertex AI Agent Engine. Account-specific deployment and evidence must be completed through the entrant's Google Cloud account.

## IBM track

IBM Bob must be used meaningfully during the development process. This repository includes:

- `AGENTS.md` with the development contract and IP boundary
- `.bobignore` to exclude credentials, databases, private evidence, archives, and unrelated proprietary material
- bounded Bob tasks in `bob_tasks/`
- an evidence runbook in `docs/IBM_BOB_COMPETITION_RUNBOOK.md`

No Bob usage, screenshot, telemetry, or contribution claim should be made until it has actually occurred through the entrant account.

## Intellectual-property separation

The public project uses a new codebase, data model, terminology, API, interface, policy, tests, and domain-specific workflow. Unrelated proprietary systems, confidential research, private evidence, and unpublished material are outside the repository.

## License

MIT License. See `LICENSE`.
