#!/usr/bin/env sh
# Inicialização do contêiner no Cloud Run.
# Se o índice vetorial do RAG ainda não existe, roda o script do próprio
# módulo de RAG (scripts/build_index.py) antes de subir a interface.
set -e

DB_PATH="${RAG_DB_PATH:-data/chroma}"
if [ -f scripts/build_index.py ] && [ ! -d "$DB_PATH" -o -z "$(ls -A "$DB_PATH" 2>/dev/null)" ]; then
  echo ">> Índice do RAG não encontrado em $DB_PATH: construindo..."
  PYTHONPATH=. python scripts/build_index.py || echo ">> AVISO: falha ao construir o índice; a interface sobe mesmo assim."
fi

exec streamlit run app.py --server.port="${PORT:-8080}" --server.address=0.0.0.0
