#!/usr/bin/env python3
"""Build the local U.S. security catalog from public Nasdaq Trader directories."""

from __future__ import annotations

import argparse
import csv
import io
from datetime import date
from pathlib import Path
from urllib.request import urlopen


NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
CATALOG_PATH = Path(__file__).parents[1] / "app" / "data" / "securities.csv"
EXCHANGES = {
    "A": "NYSE American",
    "M": "NYSE Chicago",
    "N": "NYSE",
    "P": "NYSE Arca",
    "V": "IEX",
    "Z": "Cboe BZX",
}


def read_directory(url: str) -> list[dict[str, str]]:
    with urlopen(url, timeout=30) as response:
        data = response.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(data), delimiter="|"))


def catalog_rows(
    nasdaq_rows: list[dict[str, str]],
    other_rows: list[dict[str, str]],
    source: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for row in nasdaq_rows:
        if row.get("Test Issue") != "N":
            continue
        symbol = row["Symbol"].strip()
        if not symbol:
            continue
        rows.append(
            {
                "symbol": symbol,
                "name": row["Security Name"].strip(),
                "exchange": "NASDAQ",
                "asset_type": "etf" if row.get("ETF") == "Y" else "equity",
                "is_active": "true",
                "source": source,
            }
        )

    for row in other_rows:
        if row.get("Test Issue") != "N":
            continue
        symbol = row["ACT Symbol"].strip()
        exchange = EXCHANGES.get(row.get("Exchange", ""))
        if not symbol or exchange is None:
            continue
        rows.append(
            {
                "symbol": symbol,
                "name": row["Security Name"].strip(),
                "exchange": exchange,
                "asset_type": "etf" if row.get("ETF") == "Y" else "equity",
                "is_active": "true",
                "source": source,
            }
        )

    unique_rows = {(row["symbol"], row["exchange"]): row for row in rows}
    return sorted(unique_rows.values(), key=lambda row: (row["symbol"], row["exchange"]))


def write_catalog(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["symbol", "name", "exchange", "asset_type", "is_active", "source"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=CATALOG_PATH)
    parser.add_argument("--source-date", default=date.today().isoformat())
    arguments = parser.parse_args()

    source = f"nasdaq_trader_{arguments.source_date}"
    rows = catalog_rows(read_directory(NASDAQ_LISTED_URL), read_directory(OTHER_LISTED_URL), source)
    write_catalog(rows, arguments.output)
    print(f"Wrote {len(rows)} active U.S.-listed instruments to {arguments.output}")


if __name__ == "__main__":
    main()