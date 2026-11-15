#!/usr/bin/env bash
# Build (Cloud Build) + deploy no Cloud Run a partir do código-fonte.
# Uso: PROJECT_ID=meu-projeto [APP_PASSWORD=senha] ./deploy/deploy.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Defina PROJECT_ID}"
REGION="${REGION:-southamerica-east1}"
SERVICE="${SERVICE:-sabor-da-terra}"
SA_EMAIL="${SA_NAME:-sabor-da-terra-app}@$PROJECT_ID.iam.gserviceaccount.com"
MODEL="${GEMINI_MODEL:-gemini-3.5-flash}"
APP_PASSWORD="${APP_PASSWORD:-}"

# --session-affinity : Streamlit usa WebSocket e guarda a sessão em memória
# --min-instances 1  : sem cold start durante a demo ao vivo
# --max-instances 1  : o histórico da conversa não se perde entre instâncias
# --memory 2Gi       : ChromaDB do RAG em memória
# --timeout 3600     : conexões WebSocket longas
# --set-secrets      : GEMINI_API_KEY vem do Secret Manager (usada pelo app e pelo sabor_rag)
gcloud run deploy "$SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" \
  --source . \
  --service-account "$SA_EMAIL" \
  --allow-unauthenticated \
  --session-affinity \
  --min-instances 1 --max-instances 1 \
  --cpu 1 --memory 2Gi --cpu-boost \
  --timeout 3600 \
  --set-secrets "GEMINI_API_KEY=gemini-api-key:latest" \
  --set-env-vars "GEMINI_MODEL=$MODEL,APP_PASSWORD=$APP_PASSWORD"

gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'
