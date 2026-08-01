# Google Cloud integration plan

## Local foundation complete

The application already separates advisory discovery, deterministic policy, explanation, persistence, and human decision.

## Account-stage tasks

1. Create or select a Google Cloud project.
2. Enable Vertex AI, Cloud Run, Cloud Build, Artifact Registry, and required logging APIs.
3. Configure billing and budget alerts.
4. Create a least-privilege service account.
5. Deploy the ADK rights-discovery agent to Vertex AI Agent Engine.
6. Retain the Agent Engine resource name and successful trace.
7. Configure the FastAPI service for Google mode.
8. Deploy the web service to Cloud Run.
9. Verify runtime calls and application logs.
10. Record a stable public demo URL and final evidence.

## Evidence checklist

- Google Cloud project ID
- enabled API list
- Cloud Run service URL
- Agent Engine resource name
- successful Gemini/Agent Engine trace
- application logs showing real calls
- deployment date and Git commit
- cost and quota notes

## Security

Credentials must remain in environment variables or Secret Manager. Never commit service-account keys, API keys, `.env` files, or private evidence documents.
