#!/usr/bin/env bash
# Configuração inicial do Google Cloud (rodar UMA vez, de preferência no Cloud Shell).
# Uso: PROJECT_ID=meu-projeto GEMINI_API_KEY=xxx ./deploy/setup_gcp.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Defina PROJECT_ID}"
REGION="${REGION:-southamerica-east1}"            # São Paulo
SA_NAME="${SA_NAME:-sabor-da-terra-app}"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID"

echo ">> Ativando APIs"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com \
  aiplatform.googleapis.com logging.googleapis.com

echo ">> Service account da aplicação (menor privilégio)"
gcloud iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$SA_NAME" --display-name="Assistente Sabor da Terra"
for ROLE in roles/secretmanager.secretAccessor roles/aiplatform.user roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE" --condition=None --quiet >/dev/null
done

echo ">> Chave do Gemini no Secret Manager (nunca no código nem na imagem)"
if ! gcloud secrets describe gemini-api-key >/dev/null 2>&1; then
  : "${GEMINI_API_KEY:?Defina GEMINI_API_KEY para criar o segredo}"
  printf '%s' "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=- --replication-policy=automatic
fi

echo ">> Repositório de imagens (usado pelo cloudbuild.yaml)"
gcloud artifacts repositories describe sabor-da-terra --location="$REGION" >/dev/null 2>&1 || \
  gcloud artifacts repositories create sabor-da-terra --repository-format=docker --location="$REGION"

echo ">> Permissões para o Cloud Build publicar no Cloud Run (CI/CD)"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
CB_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
for ROLE in roles/run.admin roles/iam.serviceAccountUser roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$CB_SA" \
    --role="$ROLE" --condition=None --quiet >/dev/null
done

echo ""
echo "Pronto. Agora: PROJECT_ID=$PROJECT_ID ./deploy/deploy.sh"
