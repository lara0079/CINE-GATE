# Vertex AI Agent Engine package

This package contains a bounded Google ADK multi-agent workflow for CINE-GATE.

## Workflow

1. `rights_scout` discovers possible rights-bearing categories.
2. `evidence_gap_scout` inspects the declared inventory and expected metadata.
3. `parallel_rights_discovery` runs the two specialists concurrently.
4. `release_brief_agent` synthesizes a bounded advisory brief.
5. `cine_gate_agentic_workflow` is the sequential root agent.

The workflow cannot grant clearance or override the FastAPI deterministic policy.

## Account-stage deployment

```bash
cd deployment/agent_engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-agent-engine.txt
export GOOGLE_CLOUD_PROJECT="your-project"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_CLOUD_STAGING_BUCKET="gs://your-bucket"
gcloud auth application-default login
python deploy_agent.py
```

Retain the Agent Engine resource name, installation output, successful query, Cloud Trace, and relevant logs. Do not claim deployment before these steps are actually completed through the entrant account.
