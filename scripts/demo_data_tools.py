"""Demonstra as consultas determinísticas aos dados operacionais locais."""

import argparse
import json

from sabor_agent.data_tools import DEFAULT_DATA_DIR, get_producer_summary, lookup_lot, lookup_price


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer", default="P001", help="ID do produtor")
    parser.add_argument("--start", default="2026-09-01", help="Data inicial (AAAA-MM-DD)")
    parser.add_argument("--end", default="2026-10-31", help="Data final (AAAA-MM-DD)")
    parser.add_argument("--product", default="goiaba paluma", help="Produto a consultar")
    parser.add_argument("--lot", default="LOT-2026-0089", help="ID do lote")
    parser.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        help="Pasta que contém os CSVs operacionais",
    )
    args = parser.parse_args()

    result = {
        "producer_summary": get_producer_summary(
            args.producer, args.start, args.end, data_dir=args.data_dir
        ),
        "price_lookup": lookup_price(args.product, data_dir=args.data_dir),
        "lot_lookup": lookup_lot(args.lot, data_dir=args.data_dir),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
