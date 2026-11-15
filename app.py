"""Interface conversacional — Assistente Cooperativa Sabor da Terra.

Responsável: Engenheiro(a) Cloud & Fullstack / DevOps.
Rodar localmente:  streamlit run app.py
"""
from __future__ import annotations

import hmac
import json

import streamlit as st

from core import config
from core.llm import backend_descricao
from core.orchestrator import carregar_ferramentas, novo_chat, responder

st.set_page_config(page_title="Sabor da Terra · Assistente", page_icon="🌱", layout="wide")

# Perguntas do roteiro da demo (um clique na barra lateral)
EXEMPLOS = [
    "Faz a triagem do pedido PED-2026-003",
    "Quais produtores têm certificação orgânica vigente para mel?",
    "E a Josefa?",
    "Qual a rastreabilidade do queijo do lote 2024-089?",
    "Faz o resumo do mês da Maria das Graças (P001)",
    "A exportadora pediu os dados bancários dos produtores. Posso mandar?",
]


def _checar_senha() -> bool:
    if not config.APP_PASSWORD or st.session_state.get("autenticado"):
        return True
    senha = st.text_input("Senha de acesso", type="password")
    if senha and hmac.compare_digest(senha, config.APP_PASSWORD):
        st.session_state.autenticado = True
        st.rerun()
    elif senha:
        st.error("Senha incorreta.")
    return False


@st.cache_resource
def _ferramentas():
    """Carregadas uma vez por contêiner e compartilhadas entre sessões."""
    return carregar_ferramentas()


def _nova_conversa():
    ferramentas, _ = _ferramentas()
    st.session_state.chat = novo_chat(ferramentas)
    st.session_state.mensagens = []


def _mostrar_ferramentas(chamadas: list[dict]):
    if not (config.MOSTRAR_FERRAMENTAS and chamadas):
        return
    with st.expander(f"🔧 {len(chamadas)} ferramenta(s) usada(s)"):
        for c in chamadas:
            icone = "✅" if c["ok"] else "❌"
            st.markdown(f"{icone} **{c['ferramenta']}** · `{c['modulo']}` · {c['ms']} ms")
            st.code(json.dumps(c["args"], ensure_ascii=False), language="json")
            st.code(c["resultado"][:1500], language="json")


def _enviar(pergunta: str):
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant", avatar="🌱"):
        with st.spinner("Consultando..."):
            try:
                texto, chamadas = responder(st.session_state.chat, pergunta)
            except Exception as e:  # noqa: BLE001
                texto, chamadas = f"⚠️ Erro ao falar com o modelo: `{e}`", []
        st.markdown(texto)
        _mostrar_ferramentas(chamadas)
    st.session_state.mensagens.append({"role": "assistant", "content": texto, "ferramentas": chamadas})


# ---------------------------------------------------------------------------
if not _checar_senha():
    st.stop()

if "chat" not in st.session_state:
    try:
        _nova_conversa()
    except Exception as e:  # noqa: BLE001
        st.error(f"Não foi possível iniciar o modelo: {e}")
        st.stop()

_, status_modulos = _ferramentas()

with st.sidebar:
    st.title("🌱 Sabor da Terra")
    st.caption("Assistente da cooperativa")
    if st.button("🔄 Nova conversa", use_container_width=True):
        _nova_conversa()
        st.rerun()
    st.divider()
    st.markdown("**Roteiro da demo**")
    pendente = None
    for i, p in enumerate(EXEMPLOS):
        if st.button(p, key=f"ex{i}", use_container_width=True):
            pendente = p
    st.divider()
    st.markdown("**Módulos integrados**")
    for s in status_modulos:
        if s.ok:
            st.caption(f"✅ {s.modulo}: {', '.join(s.ferramentas) or 'sem ferramentas'}")
        else:
            st.caption(f"⏳ {s.modulo}: {s.erro}")
    st.caption(f"Modelo: {backend_descricao()}")
    st.caption(f"Mensagens na sessão: {len(st.session_state.mensagens)}")

st.header("Assistente da Cooperativa")
if not st.session_state.mensagens:
    st.info("Pergunte sobre pedidos, certificações, lotes ou produtores. "
            "O assistente lembra do que foi dito nesta conversa.")

for m in st.session_state.mensagens:
    with st.chat_message(m["role"], avatar="🌱" if m["role"] == "assistant" else None):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            _mostrar_ferramentas(m.get("ferramentas", []))

pergunta = st.chat_input("Escreva aqui...")
if pendente or pergunta:
    _enviar(pendente or pergunta)
