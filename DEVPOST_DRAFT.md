# Devpost project draft

## Project name

CINE-GATE

## Tagline

A bounded multi-agent control plane for film-production rights review before release.

## Inspiration

Film and media teams frequently coordinate likeness, voice, music, footage, artwork, location, and script permissions across contracts, emails, spreadsheets, and production tools. A trailer or release may be technically ready while the permission record is fragmented, out of scope, expired, contradictory, or silent about synthetic use.

## What it does

CINE-GATE turns a proposed production action into a structured, reviewable rights workflow.

A Rights Scout identifies possible rights-bearing material implied by the action. A deterministic Scope Controller compares supplied permission metadata with the intended use, channels, territories, dates, commercial scope, modification scope, synthetic-media use, minor-subject authorization, attribution, and evidence references. An Evidence Mapper creates an asset-level rights matrix and release-readiness indicators. A Release Brief Agent explains recorded findings and corrective actions. A named human then approves an eligible record, rejects it, or creates a corrected linked revision.

The product returns `CLEARED`, `REVIEW_REQUIRED`, or `BLOCKED` and exports evidence JSON, a rights-matrix CSV, a printable report, and a release-package ZIP with manifest checksums.

## How we built it

- FastAPI, Pydantic, SQLite, HTML, CSS, and JavaScript
- Gemini through the Google Gen AI SDK for advisory discovery and explanation
- Google ADK multi-agent package with parallel specialist discovery and sequential synthesis
- Vertex AI Agent Engine deployment package with Cloud Trace enabled
- Cloud Run and Cloud Build deployment assets
- IBM Bob bounded SDLC tasks and evidence workflow

## Responsible agent design

CINE-GATE separates agentic assistance from decision authority. Agents may discover categories and explain findings, but they cannot invent permission, authenticate evidence, provide legal advice, or change the deterministic outcome. A `BLOCKED` record cannot be approved. Corrected information creates a linked revision instead of erasing the original record.

## What is technically distinctive

- concurrent specialist agents for rights discovery and evidence-gap analysis
- deterministic policy as the source of the recorded outcome
- transparent run ID, model, provider, latency, guardrail, and fallback status
- explainable risk signals rather than an opaque legal or confidence score
- case lineage, evidence checksums, asset-level matrix, and human-decision safeguards
- explicit failure behavior when Google runtime services are unavailable

## Challenges

The main challenge was designing a system that feels genuinely agentic without allowing the model to become the authority. We also had to produce a complete product experience while keeping the public project narrow and independent from a broader private research architecture.

## Accomplishments

- complete responsive web product
- bounded five-layer workflow
- Google ADK and Agent Engine package
- 57 automated tests
- 8/8 deterministic quality-gate scenarios
- downloadable release evidence package
- accessible keyboard navigation and reduced-motion support
- strict IBM Bob and intellectual-property workspace controls

## What we learned

Agentic systems become more credible when their authority is explicit. The strongest workflow was not “let the model decide,” but “let agents discover, organize, and explain while deterministic controls and a named human remain accountable for the recorded action.”

## What's next

- deploy the FastAPI service to Cloud Run
- deploy and query the ADK workflow on Vertex AI Agent Engine
- capture Cloud Trace and runtime evidence
- complete the bounded IBM Bob tasks and evidence notes
- publish the open-source repository and hosted demo
- record the three-minute demonstration
