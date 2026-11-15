"""Orquestrador: um chat Gemini com as ferramentas de todos os módulos.

Responsável: Engenheiro(a) Cloud & Fullstack / DevOps.

O histórico da sessão fica no objeto Chat (um por usuário/aba do Streamlit),
incluindo as chamadas e resultados de ferramentas: é isso que mantém o
contexto da conversa (requisito funcional).

O prompt de sistema é do(a) Arquiteto(a) de Prompts: basta salvar o texto em
prompts/system_prompt.md (ou apontar SYSTEM_PROMPT_FILE). Enquanto o arquivo
não existir, usamos o prompt mínimo de integração abaixo.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from google.genai import types

from core import config
from core.integracao import Rastreio, carregar_ferramentas
from core.llm import get_client

PROMPT_INTEGRACAO = """Você é o assistente da Cooperativa Sabor da Terra. Hoje é {hoje}.
Use as ferramentas disponíveis para responder; não invente informações.
Se nenhuma ferramenta trouxer a resposta, diga claramente que não encontrou.
Quando uma ferramenta devolver fontes, cite-as.
Considere o histórico desta conversa ao interpretar a pergunta.
Responda em português do Brasil."""


def system_prompt() -> str:
    arq = Path(config.SYSTEM_PROMPT_FILE)
    texto = arq.read_text(encoding="utf-8") if arq.exists() else PROMPT_INTEGRACAO
    return texto.replace("{hoje}", date.today().strftime("%d/%m/%Y"))


def novo_chat(ferramentas: list):
    return get_client().chats.create(
        model=config.GEMINI_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt(),
            temperature=config.TEMPERATURE,
            tools=ferramentas or None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=config.MAX_CHAMADAS_FERRAMENTAS),
        ),
    )


def responder(chat, mensagem: str) -> tuple[str, list[dict]]:
    """Envia a mensagem e devolve (texto, chamadas_de_ferramentas)."""
    with Rastreio() as chamadas:
        resp = chat.send_message(mensagem)
    return resp.text or "Não consegui gerar uma resposta. Tente reformular.", chamadas


__all__ = ["carregar_ferramentas", "novo_chat", "responder", "system_prompt"]
