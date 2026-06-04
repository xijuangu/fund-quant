from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from app.db.session import SessionLocal
from app.models.fund import FundBasic, FundNavDaily


FUND_TYPE_MAP = {
    0: "mixed",
    1: "stock",
    2: "bond",
    3: "index",
    4: "unknown",
}


@dataclass(frozen=True)
class FundTraceDataset:
    funds: list[dict[str, Any]]
    nav_rows: list[dict[str, Any]]
    skipped_orphan_nav_rows: int


def infer_asset_bucket(fund_name: str) -> str:
    if "黄金" in fund_name:
        return "gold_commodity"
    if "恒生" in fund_name or "QDII" in fund_name or "纳斯达克" in fund_name:
        return "overseas_qdii"
    if "债" in fund_name:
        return "bond"
    if "货币" in fund_name or "现金" in fund_name:
        return "money_market"
    if fund_name:
        return "a_share_equity"
    return ""


def _connect_sqlite(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _load_funds(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """
        select code, name, type
        from funds
        order by code
        """
    ).fetchall()
    funds: dict[str, dict[str, Any]] = {}
    for row in rows:
        fund_name = row["name"] or row["code"]
        funds[row["code"]] = {
            "fund_code": row["code"],
            "fund_name": fund_name,
            "fund_type": FUND_TYPE_MAP.get(row["type"], "unknown"),
            "asset_bucket": infer_asset_bucket(fund_name),
            "inception_date": None,
            "fund_company": "",
            "is_active": True,
            "note": "Imported from fund-trace funds table.",
        }
    return funds


def _load_nav_rows(
    conn: sqlite3.Connection,
    known_funds: dict[str, dict[str, Any]],
    include_orphans: bool,
) -> tuple[list[dict[str, Any]], int]:
    rows = conn.execute(
        """
        select fund_code, date, unit_nav, accumulated_nav
        from nav_snapshots
        order by fund_code, date
        """
    ).fetchall()
    nav_rows: list[dict[str, Any]] = []
    skipped_orphan_nav_rows = 0
    for row in rows:
        fund_code = row["fund_code"]
        if fund_code not in known_funds:
            if not include_orphans:
                skipped_orphan_nav_rows += 1
                continue
            known_funds[fund_code] = {
                "fund_code": fund_code,
                "fund_name": fund_code,
                "fund_type": "unknown",
                "asset_bucket": "",
                "inception_date": None,
                "fund_company": "",
                "is_active": False,
                "note": "Imported from fund-trace nav_snapshots without a funds row.",
            }
        nav_rows.append(
            {
                "fund_code": fund_code,
                "nav_date": date.fromisoformat(row["date"]),
                "unit_nav": row["unit_nav"],
                "accumulated_nav": row["accumulated_nav"],
                "adjusted_nav": None,
                "source": "fund-trace",
            }
        )
    return nav_rows, skipped_orphan_nav_rows


def load_fund_trace(db_path: str | Path, include_orphans: bool = False) -> FundTraceDataset:
    db_path = Path(db_path)
    conn = _connect_sqlite(db_path)
    try:
        funds = _load_funds(conn)
        nav_rows, skipped_orphan_nav_rows = _load_nav_rows(conn, funds, include_orphans)
        return FundTraceDataset(
            funds=list(funds.values()),
            nav_rows=nav_rows,
            skipped_orphan_nav_rows=skipped_orphan_nav_rows,
        )
    finally:
        conn.close()


def import_dataset(dataset: FundTraceDataset) -> tuple[int, int]:
    session = SessionLocal()
    try:
        for fund in dataset.funds:
            session.merge(FundBasic(**fund))
        for nav_row in dataset.nav_rows:
            session.merge(FundNavDaily(**nav_row))
        session.commit()
        return len(dataset.funds), len(dataset.nav_rows)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import fund-trace SQLite data into Fund Lab.")
    parser.add_argument("db_path", type=Path, help="Path to fund-trace.db")
    parser.add_argument(
        "--include-orphans",
        action="store_true",
        help="Import nav rows whose fund code is no longer present in fund-trace funds.",
    )
    args = parser.parse_args()

    dataset = load_fund_trace(args.db_path, include_orphans=args.include_orphans)
    fund_count, nav_count = import_dataset(dataset)
    print(f"Imported funds: {fund_count}")
    print(f"Imported nav rows: {nav_count}")
    print(f"Skipped orphan nav rows: {dataset.skipped_orphan_nav_rows}")


if __name__ == "__main__":
    main()
