"""Integração dos módulos da equipe com o orquestrador.

Responsável: Engenheiro(a) Cloud & Fullstack / DevOps.

Não implementa nenhuma regra de negócio: só DESCOBRE as ferramentas que cada
colega publicou e as registra no Gemini (function calling).

Contrato para cada módulo listado em config.TOOL_MODULES (ex.: sabor_rag.tool):
  - Opção 1: definir `TOOLS = [funcao_a, funcao_b]`.
  - Opção 2: sem TOOLS, são usadas as funções públicas DEFINIDAS no próprio
    arquivo (não as importadas) que tenham docstring.
  - Cada função: parâmetros com type hints, docstring explicando QUANDO usar
    (é o que o modelo lê) e retorno JSON-serializável (dict/list).
Módulo que ainda não existe aparece na interface como "aguardando".
"""
from __future__ import annotations

import contextvars
import functools
import importlib
import inspect
import json
import time
import traceback
from dataclasses import dataclass, field

from core import config

_trace: contextvars.ContextVar[list | None] = contextvars.ContextVar("trace", default=None)


@dataclass
class StatusModulo:
    modulo: str
    ok: bool
    ferramentas: list[str] = field(default_factory=list)
    erro: str = ""


def _registrar_chamada(fn):
    """Mede e registra cada chamada (mostrada na interface) e transforma
    exceções em mensagem de erro, para um módulo com bug não derrubar o chat."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        try:
            res, ok = fn(*args, **kwargs), True
        except Exception as e:  # noqa: BLE001
            res, ok = {"erro": f"Falha em {fn.__name__}: {e}"}, False
            traceback.print_exc()
        log = _trace.get()
        if log is not None:
            log.append({
                "ferramenta": fn.__name__, "modulo": fn.__module__, "args": kwargs or list(args),
                "ok": ok, "ms": int((time.time() - t0) * 1000),
                "resultado": json.dumps(res, ensure_ascii=False, default=str)[:3000],
            })
        return res
    return wrapper


def _ferramentas_do_modulo(mod) -> list:
    if hasattr(mod, "TOOLS"):
        return list(mod.TOOLS)
    return [
        f for nome, f in inspect.getmembers(mod, inspect.isfunction)
        if not nome.startswith("_") and f.__module__ == mod.__name__ and f.__doc__
    ]


def carregar_ferramentas(modulos: list[str] | None = None) -> tuple[list, list[StatusModulo]]:
    ferramentas, status = [], []
    for nome in modulos or config.TOOL_MODULES:
        try:
            mod = importlib.import_module(nome)
        except ModuleNotFoundError as e:
            if e.name and nome.startswith(e.name):
                status.append(StatusModulo(nome, False, erro="aguardando módulo"))
            else:
                status.append(StatusModulo(nome, False, erro=f"dependência ausente: {e.name}"))
            continue
        except Exception as e:  # noqa: BLE001
            status.append(StatusModulo(nome, False, erro=f"erro ao importar: {e}"))
            continue
        fns = _ferramentas_do_modulo(mod)
        ferramentas += [_registrar_chamada(f) for f in fns]
        status.append(StatusModulo(nome, True, [f.__name__ for f in fns]))
    return ferramentas, status


class Rastreio:
    """Context manager que coleta as chamadas de ferramentas de um turno."""

    def __enter__(self):
        self.chamadas: list = []
        self._token = _trace.set(self.chamadas)
        return self.chamadas

    def __exit__(self, *exc):
        _trace.reset(self._token)
        return False
