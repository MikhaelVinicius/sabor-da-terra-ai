from sabor_agent.formatters import (
    format_lot_lookup,
    format_price_lookup,
    format_producer_summary,
)


def test_format_producer_summary_shows_period_totals_and_payment_statuses():
    summary = {
        "producer_id": "P001",
        "period": {"start": "2026-10-01", "end": "2026-10-31"},
        "transaction_count": 3,
        "total_sales": "52.50",
        "total_quantity_kg": "6.5",
        "payments": {
            "paid": {"amount": "20.00", "transactions": 1},
            "pending": {"amount": "30.00", "transactions": 1},
            "unclassified": {"amount": "2.50", "transactions": 1},
        },
        "source_file": "financeiro.csv",
    }

    formatted = format_producer_summary(summary)

    assert "produtor P001" in formatted
    assert "2026-10-01 a 2026-10-31" in formatted
    assert "Vendas: 52,50" in formatted
    assert "Quantidade registrada: 6,5 kg" in formatted
    assert "Pagos: 20,00 (1 transação)" in formatted
    assert "Pendentes: 30,00 (1 transação)" in formatted
    assert "Não classificados: 2,50 (1 transação)" in formatted
    assert "Fonte: financeiro.csv" in formatted
    assert "R$" not in formatted


def test_format_price_lookup_displays_exact_matches_and_variants_without_applying_discount():
    result = {
        "query": "tomate",
        "period": "2026-10",
        "matches": [
            {
                "product": "tomate",
                "unit": "kg",
                "conventional_price": "5.00",
                "organic_price": "7.00",
                "wholesale_discount_pct": "5",
                "wholesale_minimum_kg": "20",
                "notes": None,
            }
        ],
        "suggestions": [
            {
                "product": "tomate cereja",
                "unit": "kg",
                "conventional_price": "8.00",
                "organic_price": "10.00",
                "wholesale_discount_pct": "0",
                "wholesale_minimum_kg": "0",
                "notes": None,
            }
        ],
        "source_file": "tabela_precos_outubro_2026.csv",
    }

    formatted = format_price_lookup(result)

    assert "período: 2026-10" in formatted
    assert "Correspondências exatas:" in formatted
    assert "tomate (kg): convencional 5,00; orgânico 7,00" in formatted
    assert "desconto de atacado informado 5%" in formatted
    assert "volume mínimo informado 20 kg" in formatted
    assert "Variantes para confirmar:" in formatted
    assert "tomate cereja (kg): convencional 8,00; orgânico 10,00" in formatted
    assert "preço com desconto" not in formatted
    assert "Fonte: tabela_precos_outubro_2026.csv" in formatted


def test_format_price_lookup_reports_when_no_match_or_variant_exists():
    formatted = format_price_lookup(
        {
            "query": "produto desconhecido",
            "period": "2026-10",
            "matches": [],
            "suggestions": [],
            "source_file": "tabela_precos_outubro_2026.csv",
        }
    )

    assert "Nenhum produto encontrado" in formatted
    assert "2026-10" in formatted


def test_format_lot_lookup_shows_only_present_fields():
    lot = {
        "lot_id": "LOT-1",
        "harvest_date": "2026-10-01",
        "delivery_date": "2026-10-02",
        "producer_id": "P001",
        "product": "mel silvestre",
        "quantity_kg": "2",
        "buyer": "Restaurante Raízes",
        "order_id": "PED-1",
        "transport_temperature_c": "ambiente",
        "expiration_date": None,
        "visual_inspection": "aprovado",
        "notes": None,
        "source_file": "lotes.csv",
    }

    formatted = format_lot_lookup(lot)

    assert "Lote LOT-1" in formatted
    assert "Produto: mel silvestre" in formatted
    assert "Quantidade (kg): 2" in formatted
    assert "Temperatura de transporte: ambiente" in formatted
    assert "Validade" not in formatted
    assert "Observações" not in formatted
    assert "CPF" not in formatted
    assert "Fonte: lotes.csv" in formatted


def test_format_lot_lookup_reports_missing_lot():
    assert format_lot_lookup(None) == "Lote não encontrado."
