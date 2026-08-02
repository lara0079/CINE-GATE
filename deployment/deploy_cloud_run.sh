#!/usr/bin/env bash
set -euo pipefail
: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
REPOSITORY="${GOOGLE_ARTIFACT_REPOSITORY:-cine-gate}"
IMAGE="${REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/${REPOSITORY}/cine-gate:latest"

gcloud artifacts repositories describe "$REPOSITORY" --location "$REGION" >/dev/null 2>&1 || \
  gcloud artifacts repositories create "$REPOSITORY" --repository-format docker --location "$REGION"

gcloud builds submit --config deployment/cloudbuild.yaml --substitutions _IMAGE="$IMAGE"
gcloud run deploy cine-gate \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars CINE_GATE_ENVIRONMENT=production,CINE_GATE_AGENT_MODE=google,GOOGLE_CLOUD_PROJECT="$GOOGLE_CLOUD_PROJECT",GOOGLE_CLOUD_LOCATION="$REGION"
