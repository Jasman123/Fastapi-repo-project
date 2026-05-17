#!/usr/bin/env bash
# deploy_gcp.sh — Build and deploy to Google Cloud Run
# Usage: ./scripts/deploy_gcp.sh

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
REGION="${GCP_REGION:-asia-southeast1}"
SERVICE="ai-support-agent"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE}"

echo "🔨 Building Docker image …"
gcloud builds submit \
  --tag "${IMAGE}" \
  --project "${PROJECT_ID}"

echo "🚀 Deploying to Cloud Run …"
gcloud run deploy "${SERVICE}" \
  --image          "${IMAGE}" \
  --region         "${REGION}" \
  --platform       managed \
  --allow-unauthenticated \
  --set-env-vars   "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},APP_ENV=production" \
  --memory         512Mi \
  --cpu            1 \
  --max-instances  10 \
  --project        "${PROJECT_ID}"

echo "✅ Deployed! Service URL:"
gcloud run services describe "${SERVICE}" \
  --region  "${REGION}" \
  --project "${PROJECT_ID}" \
  --format  "value(status.url)"
