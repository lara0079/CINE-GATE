# Google ADK and Vertex AI Agent Engine runbook

## Architecture

The account-stage package is in `deployment/agent_engine`.

- `rights_scout` discovers possible rights categories.
- `evidence_gap_scout` inspects the declared inventory and expected metadata.
- `parallel_rights_discovery` runs both specialists concurrently.
- `release_brief_agent` synthesizes a bounded advisory brief.
- `cine_gate_agentic_workflow` is the sequential root workflow.

The agents do not produce the final CINE-GATE outcome. The FastAPI deterministic policy remains the source of record.

## Deployment evidence to retain

- enabled Google Cloud APIs
- project and region, without exposing credentials
- successful dependency installation
- Agent Engine resource name
- successful query output
- Cloud Trace showing agent/tool activity
- FastAPI hosted URL and successful Gemini runtime call
- Cloud Run logs for the demo request

## Failure rule

If Agent Engine deployment is unavailable, do not claim it was deployed. The submission should state only the actual runtime integration demonstrated in code and video.
