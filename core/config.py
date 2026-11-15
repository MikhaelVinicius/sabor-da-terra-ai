"""Configuração da aplicação (interface + orquestrador), lida do ambiente.

Responsável: Engenheiro(a) Cloud & Fullstack / DevOps.
As variáveis RAG_* continuam sendo lidas pelo próprio sabor_rag/config.py.
"""
from __future__ import annotations

import os

try:  # .env local; no Cloud Run as variáveis vêm do serviço
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Modelo do orquestrador (troque sem mexer no código)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))

# Credenciais: mesma regra do sabor_rag (chave do AI Studio).
# Opcionalmente Vertex AI se não houver chave e o projeto estiver definido.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

# Módulos da equipe que expõem ferramentas ao orquestrador (ver core/integracao.py).
# Cada colega adiciona aqui o caminho do seu arquivo de ferramentas.
TOOL_MODULES = [
    m.strip()
    for m in os.getenv(
        "TOOL_MODULES",
        "sabor_rag.tool,sabor_triagem.tool,sabor_agentes.tool,sabor_dados.tool",
    ).split(",")
    if m.strip()
]

# Prompt de sistema: o texto final é do(a) Arquiteto(a) de Prompts.
SYSTEM_PROMPT_FILE = os.getenv("SYSTEM_PROMPT_FILE", "prompts/system_prompt.md")

# Interface
APP_PASSWORD = os.getenv("APP_PASSWORD", "")  # vazio = sem senha
MOSTRAR_FERRAMENTAS = os.getenv("MOSTRAR_FERRAMENTAS", "1") == "1"
MAX_CHAMADAS_FERRAMENTAS = int(os.getenv("MAX_CHAMADAS_FERRAMENTAS", "12"))
