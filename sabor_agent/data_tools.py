"""Consultas exatas e locais aos CSVs operacionais do projeto."""

import csv
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "source" / "Facepe"
PRICE_PERIOD = "2026-10"


class DataToolsError(Exception):
    """Erro base das consultas a dados locais."""


class DataNotFoundError(DataToolsError, LookupError):
    """Indica que o identificador consultado não existe na base."""


class DataValidationError(DataToolsError, ValueError):
    """Indica entrada inválida ou dados de origem inconsistentes."""


def get_producer_summary(
    producer_id: str,
    start_date: date | str,
    end_date: date | str,
    *,
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> dict:
    """Resume vendas e pagamentos de um produtor no período inclusivo."""
    normalized_producer_id = _normalize_identifier(producer_id, "producer_id")
    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")
    if start > end:
        raise DataValidationError("start_date deve ser anterior ou igual a end_date.")

    data_path = Path(data_dir)
    producers = _read_csv(data_path / "produtores.csv", {"id"})
    producer_ids = [_normalize_identifier(row.get("id"), "produtores.id") for row in producers]
    if len(producer_ids) != len(set(producer_ids)):
        raise DataValidationError("produtores.csv contém IDs duplicados.")
    if normalized_producer_id not in producer_ids:
        raise DataNotFoundError(f"Produtor {producer_id!s} não encontrado.")
    producer = producers[producer_ids.index(normalized_producer_id)]
    canonical_producer_id = producer["id"].strip()
    producer_name = _optional_value(producer.get("nome_completo"))

    transactions = _read_csv(
        data_path / "financeiro.csv",
        {"data", "produtor_id", "tipo", "quantidade_kg", "valor_total", "status_pagamento"},
    )

    total_sales = Decimal("0")
    total_quantity = Decimal("0")
    payment_totals = {
        "paid": {"amount": Decimal("0"), "transactions": 0},
        "pending": {"amount": Decimal("0"), "transactions": 0},
        "unclassified": {"amount": Decimal("0"), "transactions": 0},
    }
    transaction_count = 0

    for row_number, row in enumerate(transactions, start=2):
        if _normalize_text(row.get("produtor_id", "")) != normalized_producer_id:
            continue
        if _normalize_text(row.get("tipo", "")) != "venda":
            continue

        transaction_date = _parse_date(row.get("data"), f"financeiro.csv linha {row_number}, data")
        if not start <= transaction_date <= end:
            continue

        amount = _parse_decimal(
            row.get("valor_total"), f"financeiro.csv linha {row_number}, valor_total"
        )
        quantity = _parse_decimal(
            row.get("quantidade_kg"), f"financeiro.csv linha {row_number}, quantidade_kg"
        )
        status = _normalize_text(row.get("status_pagamento", ""))
        payment_bucket = {"pago": "paid", "pendente": "pending"}.get(status, "unclassified")

        total_sales += amount
        total_quantity += quantity
        transaction_count += 1
        payment_totals[payment_bucket]["amount"] += amount
        payment_totals[payment_bucket]["transactions"] += 1

    return {
        "producer_id": canonical_producer_id,
        "producer_name": producer_name,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "transaction_count": transaction_count,
        "total_sales": _format_money(total_sales),
        "total_quantity_kg": _format_decimal(total_quantity),
        "payments": {
            name: {
                "amount": _format_money(values["amount"]),
                "transactions": values["transactions"],
            }
            for name, values in payment_totals.items()
        },
        "source_file": "financeiro.csv",
    }


def lookup_price(
    product_query: str,
    *,
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> dict:
    """Busca produto por nome normalizado e lista variantes sem escolhê-las."""
    query = _normalize_product(product_query)
    if not query:
        raise DataValidationError("product_query não pode estar vazio.")

    rows = _read_csv(
        Path(data_dir) / "tabela_precos_outubro_2026.csv",
        {
            "produto",
            "unidade",
            "preco_convencional",
            "preco_organico",
            "desconto_atacado_pct",
            "volume_minimo_atacado_kg",
            "observacao",
        },
    )
    matches = []
    suggestions = []
    for row in rows:
        product = row.get("produto", "").strip()
        normalized_product = _normalize_product(product)
        if normalized_product == query:
            matches.append(_price_result(row))
        elif normalized_product.startswith(query + " "):
            suggestions.append(_price_result(row))

    suggestions.sort(key=lambda item: _normalize_product(item["product"]))

    return {
        "query": product_query.strip(),
        "period": PRICE_PERIOD,
        "matches": matches,
        "suggestions": suggestions,
        "source_file": "tabela_precos_outubro_2026.csv",
    }


def lookup_lot(
    lot_id: str,
    *,
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> dict | None:
    """Busca um lote por ID, sem retornar CPF ou nome pessoal do produtor."""
    normalized_lot_id = _normalize_identifier(lot_id, "lot_id")
    rows = _read_csv(
        Path(data_dir) / "lotes.csv",
        {
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
        },
    )
    matches = [
        row
        for row in rows
        if _normalize_text(row.get("lote_id", "")) == normalized_lot_id
    ]

    if len(matches) > 1:
        raise DataValidationError(f"lotes.csv contém mais de um registro para {lot_id!s}.")
    if not matches:
        return None

    row = matches[0]
    return {
        "lot_id": row["lote_id"].strip(),
        "harvest_date": _optional_value(row.get("data_colheita")),
        "delivery_date": _optional_value(row.get("data_entrega")),
        "producer_id": _optional_value(row.get("produtor_id")),
        "product": _optional_value(row.get("produto")),
        "quantity_kg": _optional_value(row.get("quantidade_kg")),
        "buyer": _optional_value(row.get("comprador")),
        "order_id": _optional_value(row.get("pedido_id")),
        "transport_temperature_c": _optional_value(row.get("temperatura_transporte_c")),
        "expiration_date": _optional_value(row.get("validade")),
        "visual_inspection": _optional_value(row.get("inspecao_visual")),
        "notes": _optional_value(row.get("observacao")),
        "source_file": "lotes.csv",
    }


def _read_csv(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise DataValidationError(f"{path.name} não contém cabeçalho.")
            missing = required_fields - set(reader.fieldnames)
            if missing:
                missing_fields = ", ".join(sorted(missing))
                raise DataValidationError(
                    f"{path.name} não contém os campos obrigatórios: {missing_fields}."
                )
            return [dict(row) for row in reader]
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {path}") from error


def _parse_date(value: date | str | None, field_name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        raise DataValidationError(f"{field_name} deve ser uma data ISO (AAAA-MM-DD).")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as error:
        raise DataValidationError(
            f"{field_name} deve ser uma data ISO (AAAA-MM-DD)."
        ) from error


def _parse_decimal(value: str | None, field_name: str) -> Decimal:
    if value is None or not value.strip():
        raise DataValidationError(f"{field_name} está vazio.")
    try:
        number = Decimal(value.strip().replace(",", "."))
    except InvalidOperation as error:
        raise DataValidationError(f"{field_name} não contém um número válido.") from error
    if not number.is_finite():
        raise DataValidationError(f"{field_name} não contém um número finito.")
    return number


def _normalize_identifier(value: str | None, field_name: str) -> str:
    if not isinstance(value, str):
        raise DataValidationError(f"{field_name} deve ser um texto.")
    normalized = _normalize_text(value)
    if not normalized:
        raise DataValidationError(f"{field_name} não pode estar vazio.")
    return normalized


def _normalize_product(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_accents.split())


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _format_money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def _format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f") if normalized else "0"


def _optional_value(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


def _price_result(row: dict[str, str]) -> dict:
    return {
        "product": row["produto"].strip(),
        "unit": _optional_value(row.get("unidade")),
        "conventional_price": _optional_value(row.get("preco_convencional")),
        "organic_price": _optional_value(row.get("preco_organico")),
        "wholesale_discount_pct": _optional_value(row.get("desconto_atacado_pct")),
        "wholesale_minimum_kg": _optional_value(row.get("volume_minimo_atacado_kg")),
        "notes": _optional_value(row.get("observacao")),
    }
