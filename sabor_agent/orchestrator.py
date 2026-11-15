"""Catálogo e despacho neutro de ferramentas para o agente da cooperativa."""

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from sabor_agent.data_tools import (
    DEFAULT_DATA_DIR,
    get_producer_summary,
    lookup_lot,
    lookup_price,
)


class ToolDispatchError(ValueError):
    """Indica ferramenta desconhecida ou argumentos incompatíveis."""


_TOOL_DEFINITIONS = [
    {
        "name": "get_producer_summary",
        "description": (
            "Resume vendas e pagamentos de um produtor no período informado. "
            "Use para consultas financeiras estruturadas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "producer_id": {"type": "string", "description": "ID do produtor."},
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Data inicial inclusiva no formato AAAA-MM-DD.",
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Data final inclusiva no formato AAAA-MM-DD.",
                },
            },
            "required": ["producer_id", "start_date", "end_date"],
            "additionalProperties": False,
        },
    },
    {
        "name": "lookup_price",
        "description": (
            "Consulta a tabela de preços de outubro de 2026. Correspondências "
            "exatas vêm em matches; variantes possíveis vêm em suggestions. "
            "Não escolhe uma variante nem calcula desconto aplicado."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_query": {
                    "type": "string",
                    "description": "Nome do produto consultado.",
                }
            },
            "required": ["product_query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "lookup_lot",
        "description": "Consulta campos registrados de rastreabilidade por ID do lote.",
        "parameters": {
            "type": "object",
            "properties": {
                "lot_id": {"type": "string", "description": "ID exato do lote."}
            },
            "required": ["lot_id"],
            "additionalProperties": False,
        },
    },
]

_TOOL_NAMES = {tool["name"] for tool in _TOOL_DEFINITIONS}
_REQUIRED_ARGUMENTS = {
    tool["name"]: set(tool["parameters"]["required"])
    for tool in _TOOL_DEFINITIONS
}
_ALLOWED_ARGUMENTS = {
    tool["name"]: set(tool["parameters"]["properties"])
    for tool in _TOOL_DEFINITIONS
}


def get_tool_definitions() -> list[dict[str, Any]]:
    """Retorna cópias das definições JSON Schema das ferramentas disponíveis."""
    return deepcopy(_TOOL_DEFINITIONS)


def dispatch_tool(
    tool_name: str,
    arguments: Mapping[str, Any],
    *,
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> dict | None:
    """Executa uma chamada estruturada sem decidir a intenção em linguagem natural."""
    if tool_name not in _TOOL_NAMES:
        raise ToolDispatchError(f"Ferramenta desconhecida: {tool_name!s}.")
    if not isinstance(arguments, Mapping):
        raise ToolDispatchError("Os argumentos da ferramenta devem ser um objeto.")

    _validate_arguments(tool_name, arguments)

    if tool_name == "get_producer_summary":
        return get_producer_summary(
            arguments["producer_id"],
            arguments["start_date"],
            arguments["end_date"],
            data_dir=data_dir,
        )
    if tool_name == "lookup_price":
        return lookup_price(arguments["product_query"], data_dir=data_dir)
    return lookup_lot(arguments["lot_id"], data_dir=data_dir)


def _validate_arguments(tool_name: str, arguments: Mapping[str, Any]) -> None:
    supplied = set(arguments)
    required = _REQUIRED_ARGUMENTS[tool_name]
    allowed = _ALLOWED_ARGUMENTS[tool_name]
    missing = required - supplied
    unexpected = supplied - allowed

    if missing:
        names = ", ".join(sorted(missing))
        raise ToolDispatchError(f"Argumentos obrigatórios ausentes: {names}.")
    if unexpected:
        names = ", ".join(sorted(str(name) for name in unexpected))
        raise ToolDispatchError(f"Argumentos não esperados: {names}.")
