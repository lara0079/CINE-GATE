# Project manifest

## Application

- `app/main.py` — FastAPI routes, security headers, readiness, and capability endpoint
- `app/domain/` — public domain model, deterministic policy, readiness, findings, and risk insights
- `app/agents/` — bounded Gemini discovery and narrative adapters
- `app/services/` — orchestration, evidence, reporting, and human-decision safeguards
- `app/repositories/` — SQLite persistence
- `app/static/` — responsive accessible web interface

## Google Cloud

- `deployment/agent_engine/` — Google ADK multi-agent workflow and Vertex AI Agent Engine deployment
- `deployment/` — Cloud Build and Cloud Run deployment

## IBM Bob

- `.bobignore` — excludes credentials, databases, archives, private evidence, and unrelated proprietary material
- `AGENTS.md` — workspace development contract
- `bob_tasks/` — bounded review and interface tasks
- `docs/IBM_BOB_COMPETITION_RUNBOOK.md` — truthful evidence procedure

## Assurance

- `tests/` — 57 automated tests
- `scripts/run_quality_gate.py` — 8-scenario product quality gate
- `docs/QUALITY_GATE_RESULTS.json` — latest recorded local quality-gate result
- `docs/TEST_RESULTS.txt` — verification summary

## Product boundary

This repository does not contain unrelated proprietary source code, confidential schemas, private algorithms, unpublished research modules, or private evidence.
