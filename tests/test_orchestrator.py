import csv

import pytest

from sabor_agent.orchestrator import (
    ToolDispatchError,
    dispatch_tool,
    get_tool_definitions,
)


@pytest.fixture
def data_dir(tmp_path):
    fixtures = {
        "produtores.csv": (
            ["id"],
            [["P001"]],
        ),
        "financeiro.csv": (
            [
                "data",
                "produtor_id",
                "tipo",
                "quantidade_kg",
                "valor_total",
                "status_pagamento",
            ],
            [["2026-10-12", "P001", "venda", "2", "12.50", "pago"]],
        ),
        "tabela_precos_outubro_2026.csv": (
            [
                "produto",
                "unidade",
                "preco_convencional",
                "preco_organico",
                "desconto_atacado_pct",
                "volume_minimo_atacado_kg",
                "observacao",
            ],
            [["mel silvestre", "kg", "20.00", "25.00", "0", "0", ""]],
        ),
        "lotes.csv": (
            [
                "lote_id",
                "data_colheita",
                "data_entrega",
                "produtor_id",
                "produto",
                "quantidade_kg",
                "comprador",
                "pedido_id",
                "temperatura_transporte_c",
                "validade",
                "inspecao_visual",
                "observacao",
            ],
            [["LOT-1", "2026-10-01", "2026-10-02", "P001", "mel", "2", "Cliente", "PED-1", "8", "2026-10-20", "aprovado", ""]],
        ),
    }
    for filename, (headers, rows) in fixtures.items():
        with (tmp_path / filename).open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)
    return tmp_path


def test_tool_definitions_expose_three_structured_tools():
    definitions = get_tool_definitions()

    assert {tool["name"] for tool in definitions} == {
        "get_producer_summary",
        "lookup_price",
        "lookup_lot",
    }


def test_dispatch_uses_structured_tools_with_the_supplied_data_directory(data_dir):
    summary = dispatch_tool(
        "get_producer_summary",
        {"producer_id": "P001", "start_date": "2026-10-01", "end_date": "2026-10-31"},
        data_dir=data_dir,
    )
    price = dispatch_tool("lookup_price", {"product_query": "mel silvestre"}, data_dir=data_dir)
    lot = dispatch_tool("lookup_lot", {"lot_id": "LOT-1"}, data_dir=data_dir)

    assert summary["total_sales"] == "12.50"
    assert price["matches"][0]["product"] == "mel silvestre"
    assert lot["producer_id"] == "P001"


def test_dispatch_rejects_unknown_tool_names():
    with pytest.raises(ToolDispatchError, match="Ferramenta desconhecida"):
        dispatch_tool("send_notification", {})


def test_dispatch_rejects_missing_and_extra_arguments():
    with pytest.raises(ToolDispatchError, match="lot_id"):
        dispatch_tool("lookup_lot", {})

    with pytest.raises(ToolDispatchError, match="Argumentos não esperados"):
        dispatch_tool("lookup_lot", {"lot_id": "LOT-1", "producer_cpf": "000"})
