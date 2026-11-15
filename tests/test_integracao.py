"""Testes da camada de integração (Cloud/Fullstack). Não chamam o Gemini."""
import sys
import types

from core import config, orchestrator
from core.integracao import Rastreio, carregar_ferramentas


def _modulo_falso(nome, **attrs):
    mod = types.ModuleType(nome)
    for k, v in attrs.items():
        if callable(v):
            v.__module__ = nome
        setattr(mod, k, v)
    sys.modules[nome] = mod
    return mod


def test_descobre_tool_do_rag_sem_pegar_imports():
    _, status = carregar_ferramentas(["sabor_rag.tool"])
    assert status[0].ok
    assert status[0].ferramentas == ["consultar_base_documental"]  # ask_rag é importado, não conta


def test_modulo_ausente_fica_aguardando():
    ferramentas, status = carregar_ferramentas(["modulo_que_nao_existe.tool"])
    assert ferramentas == [] and status[0].erro == "aguardando módulo"


def test_lista_TOOLS_tem_prioridade():
    def a(x: str) -> dict:
        """Ferramenta A."""
        return {"a": x}

    def b(x: str) -> dict:
        """Ferramenta B."""
        return {"b": x}

    _modulo_falso("fake_tools_lista", a=a, b=b, TOOLS=[b])
    _, status = carregar_ferramentas(["fake_tools_lista"])
    assert status[0].ferramentas == ["b"]


def test_erro_na_ferramenta_vira_mensagem_e_e_registrado():
    def quebra(pedido_id: str) -> dict:
        """Sempre falha."""
        raise ValueError("bug")

    _modulo_falso("fake_tools_erro", quebra=quebra)
    ferramentas, _ = carregar_ferramentas(["fake_tools_erro"])
    with Rastreio() as chamadas:
        res = ferramentas[0](pedido_id="001")
    assert "erro" in res
    assert chamadas[0]["ferramenta"] == "quebra" and chamadas[0]["ok"] is False


def test_system_prompt_usa_arquivo_do_time_de_prompts(tmp_path, monkeypatch):
    arq = tmp_path / "system_prompt.md"
    arq.write_text("Prompt oficial. Hoje: {hoje}", encoding="utf-8")
    monkeypatch.setattr(config, "SYSTEM_PROMPT_FILE", str(arq))
    assert orchestrator.system_prompt().startswith("Prompt oficial. Hoje: ")


def test_system_prompt_padrao_quando_nao_ha_arquivo(monkeypatch):
    monkeypatch.setattr(config, "SYSTEM_PROMPT_FILE", "nao/existe.md")
    assert "Sabor da Terra" in orchestrator.system_prompt()
