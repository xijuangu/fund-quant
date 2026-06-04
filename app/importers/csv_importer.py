import csv
from datetime import date, datetime
from typing import Any


def _parse_date(raw: str) -> date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _parse_optional_float(raw: str) -> float | None:
    if raw == "":
        return None
    return float(raw)


def parse_nav_csv(fileobj: Any) -> list[dict[str, Any]]:
    reader = csv.DictReader(fileobj)
    rows: list[dict[str, Any]] = []
    for row in reader:
        fund_code = row.get("fund_code", "").strip()
        nav_date_str = row.get("date", "").strip()

        if not fund_code:
            raise ValueError("fund_code must not be empty")
        if not nav_date_str:
            raise ValueError("date must not be empty")

        unit_nav_str = row.get("unit_nav", "").strip()
        accumulated_nav_str = row.get("accumulated_nav", "").strip()
        adjusted_nav_str = row.get("adjusted_nav", "").strip()
        source = row.get("source", "").strip() or "csv"

        rows.append(
            {
                "fund_code": fund_code,
                "nav_date": _parse_date(nav_date_str),
                "unit_nav": _parse_optional_float(unit_nav_str),
                "accumulated_nav": _parse_optional_float(accumulated_nav_str),
                "adjusted_nav": _parse_optional_float(adjusted_nav_str),
                "source": source,
            }
        )
    return rows
