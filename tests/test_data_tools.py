import csv
import tempfile
import unittest
from pathlib import Path

from sabor_agent.data_tools import (
    DataNotFoundError,
    DataValidationError,
    get_producer_summary,
    lookup_lot,
    lookup_price,
)


class DataToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self._write_csv(
            "produtores.csv",
            ["id", "nome_completo", "cpf", "status"],
            [
                ["P001", "Produtor de Teste", "11111111111", "ativo"],
                ["P002", "Outra Pessoa", "22222222222", "ativo"],
            ],
        )
        self._write_csv(
            "financeiro.csv",
            [
                "id_transacao",
                "data",
                "produtor_id",
                "tipo",
                "produto",
                "quantidade_kg",
                "valor_total",
                "status_pagamento",
            ],
            [
                ["FIN-1", "2026-10-01", "P001", "venda", "goiaba", "2", "20.00", "pago"],
                ["FIN-2", "2026-10-31", "P001", "venda", "queijo", "3.5", "30.00", "pendente"],
                ["FIN-3", "2026-10-20", "P001", "venda", "mel", "1", "2.50", "em análise"],
                ["FIN-4", "2026-11-01", "P001", "venda", "goiaba", "100", "900.00", "pago"],
                ["FIN-5", "2026-10-15", "P001", "despesa", "insumo", "0", "15.00", "pago"],
                ["FIN-6", "2026-10-15", "P002", "venda", "goiaba", "1", "5.00", "pago"],
            ],
        )
        self._write_csv(
            "tabela_precos_outubro_2026.csv",
            [
                "produto",
                "unidade",
                "preco_convencional",
                "preco_organico",
                "desconto_atacado_pct",
                "volume_minimo_atacado_kg",
                "observacao",
            ],
            [
                ["maracujá", "kg", "8.00", "10.00", "5", "50", ""],
                ["goiaba paluma extra", "kg", "4.00", "5.50", "10", "100", ""],
                ["goiaba paluma especial", "kg", "3.50", "4.50", "10", "100", ""],
            ],
        )
        self._write_csv(
            "lotes.csv",
            [
                "lote_id",
                "data_colheita",
                "data_entrega",
                "produtor_id",
                "produtor_nome",
                "produtor_cpf",
                "produto",
                "quantidade_kg",
                "comprador",
                "pedido_id",
                "temperatura_transporte_c",
                "validade",
                "inspecao_visual",
                "observacao",
            ],
            [
                [
                    "LOT-2026-0089",
                    "2026-09-01",
                    "2026-09-02",
                    "P003",
                    "Produtor de Teste",
                    "33333333333",
                    "queijo coalho",
                    "45",
                    "Restaurante Raízes",
                    "PED-2026-SEP-003",
                    "8",
                    "2026-10-02",
                    "aprovado",
                    "",
                ]
            ],
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_csv(self, filename, headers, rows):
        with (self.data_dir / filename).open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)

    def test_summary_uses_inclusive_dates_and_separates_payment_statuses(self):
        summary = get_producer_summary(
            "P001", "2026-10-01", "2026-10-31", data_dir=self.data_dir
        )

        self.assertEqual(summary["transaction_count"], 3)
        self.assertEqual(summary["total_sales"], "52.50")
        self.assertEqual(summary["total_quantity_kg"], "6.5")
        self.assertEqual(summary["payments"]["paid"], {"amount": "20.00", "transactions": 1})
        self.assertEqual(summary["payments"]["pending"], {"amount": "30.00", "transactions": 1})
        self.assertEqual(summary["payments"]["unclassified"], {"amount": "2.50", "transactions": 1})
        self.assertNotIn("cpf", summary)

    def test_summary_returns_zero_totals_when_period_has_no_sales(self):
        summary = get_producer_summary(
            "P001", "2026-12-01", "2026-12-31", data_dir=self.data_dir
        )

        self.assertEqual(summary["transaction_count"], 0)
        self.assertEqual(summary["total_sales"], "0.00")
        self.assertEqual(summary["total_quantity_kg"], "0")

    def test_summary_rejects_unknown_producer(self):
        with self.assertRaises(DataNotFoundError):
            get_producer_summary(
                "P999", "2026-10-01", "2026-10-31", data_dir=self.data_dir
            )

    def test_summary_rejects_reversed_date_range(self):
        with self.assertRaises(DataValidationError):
            get_producer_summary(
                "P001", "2026-11-01", "2026-10-01", data_dir=self.data_dir
            )

    def test_summary_rejects_blank_required_financial_amount(self):
        with (self.data_dir / "financeiro.csv").open(
            "a", encoding="utf-8", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(
                ["FIN-7", "2026-10-15", "P001", "venda", "mel", "1", "", "pendente"]
            )

        with self.assertRaises(DataValidationError):
            get_producer_summary(
                "P001", "2026-10-01", "2026-10-31", data_dir=self.data_dir
            )

    def test_price_lookup_matches_case_and_accent_normalized_product(self):
        result = lookup_price("  MARACUJA  ", data_dir=self.data_dir)

        self.assertEqual(result["period"], "2026-10")
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["product"], "maracujá")
        self.assertEqual(result["matches"][0]["conventional_price"], "8.00")
        self.assertEqual(result["matches"][0]["unit"], "kg")

    def test_price_lookup_rejects_blank_query(self):
        with self.assertRaises(DataValidationError):
            lookup_price("   ", data_dir=self.data_dir)

    def test_price_lookup_suggests_variants_without_selecting_one(self):
        result = lookup_price("goiaba paluma", data_dir=self.data_dir)

        self.assertEqual(result["matches"], [])
        self.assertEqual(
            [item["product"] for item in result["suggestions"]],
            ["goiaba paluma especial", "goiaba paluma extra"],
        )

    def test_price_lookup_returns_exact_match_and_nearby_variants_separately(self):
        with (self.data_dir / "tabela_precos_outubro_2026.csv").open(
            "a", encoding="utf-8", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["tomate", "kg", "5.00", "7.00", "5", "20", ""])
            writer.writerow(["tomate cereja", "kg", "8.00", "10.00", "0", "0", ""])

        result = lookup_price(" TOMATE ", data_dir=self.data_dir)

        self.assertEqual([item["product"] for item in result["matches"]], ["tomate"])
        self.assertEqual(
            [item["product"] for item in result["suggestions"]], ["tomate cereja"]
        )

    def test_lot_lookup_is_case_insensitive_and_omits_personal_identifiers(self):
        lot = lookup_lot(" lot-2026-0089 ", data_dir=self.data_dir)

        self.assertEqual(lot["producer_id"], "P003")
        self.assertEqual(lot["product"], "queijo coalho")
        self.assertEqual(lot["quantity_kg"], "45")
        self.assertIsNone(lot["notes"])
        self.assertNotIn("producer_name", lot)
        self.assertNotIn("producer_cpf", lot)

    def test_lot_lookup_returns_none_for_blank_optional_fields(self):
        lot = lookup_lot("LOT-2026-0089", data_dir=self.data_dir)

        self.assertIsNone(lot["notes"])

    def test_lot_lookup_returns_none_when_lot_does_not_exist(self):
        self.assertIsNone(lookup_lot("LOT-MISSING", data_dir=self.data_dir))

    def test_lot_lookup_rejects_duplicate_ids(self):
        with (self.data_dir / "lotes.csv").open("a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "LOT-2026-0089",
                    "2026-09-01",
                    "2026-09-02",
                    "P003",
                    "Outro nome",
                    "44444444444",
                    "queijo coalho",
                    "1",
                    "Comprador",
                    "PED-2",
                    "8",
                    "2026-10-02",
                    "aprovado",
                    "",
                ]
            )

        with self.assertRaises(DataValidationError):
            lookup_lot("LOT-2026-0089", data_dir=self.data_dir)


if __name__ == "__main__":
    unittest.main()
