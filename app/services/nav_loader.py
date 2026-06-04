from datetime import date, datetime
from typing import Any

import pandas as pd

from app.importers.csv_importer import parse_nav_csv
from app.models.fund import FundBasic, FundNavDaily


def build_fund_basic_from_csv(fileobj: Any) -> list[FundBasic]:
    """Parse a fund-basic CSV and return FundBasic instances (not persisted)."""
    import csv

    reader = csv.DictReader(fileobj)
    funds: list[FundBasic] = []
    for row in reader:
        code = row.get("fund_code", "").strip()
        name = row.get("fund_name", "").strip()
        if not code or not name:
            raise ValueError("fund_code and fund_name must not be empty")

        inception_str = row.get("inception_date", "").strip()
        inception = None
        if inception_str:
            inception = datetime.strptime(inception_str, "%Y-%m-%d").date()

        funds.append(
            FundBasic(
                fund_code=code,
                fund_name=name,
                fund_type=row.get("fund_type", "").strip(),
                asset_bucket=row.get("asset_bucket", "").strip(),
                inception_date=inception,
                fund_company=row.get("fund_company", "").strip(),
                note=row.get("note", "").strip(),
            )
        )
    return funds


def build_nav_daily_from_csv(fileobj: Any) -> list[FundNavDaily]:
    """Parse a NAV CSV and return FundNavDaily instances (not persisted)."""
    rows = parse_nav_csv(fileobj)
    return [
        FundNavDaily(
            fund_code=r["fund_code"],
            nav_date=r["nav_date"],
            unit_nav=r["unit_nav"],
            accumulated_nav=r["accumulated_nav"],
            adjusted_nav=r["adjusted_nav"],
            source=r["source"],
        )
        for r in rows
    ]


def load_nav_dataframe(
    session: Any,
    fund_codes: list[str],
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, pd.DataFrame]:
    """Load NAV data for a set of funds as a dict of fund_code -> DataFrame.

    Each DataFrame has columns: nav_date, unit_nav, accumulated_nav, adjusted_nav.
    """
    from sqlalchemy import select

    result: dict[str, pd.DataFrame] = {}
    for code in fund_codes:
        stmt = select(FundNavDaily).where(FundNavDaily.fund_code == code)
        if start_date is not None:
            stmt = stmt.where(FundNavDaily.nav_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(FundNavDaily.nav_date <= end_date)
        stmt = stmt.order_by(FundNavDaily.nav_date)

        rows = session.execute(stmt).scalars().all()
        if not rows:
            result[code] = pd.DataFrame()
            continue

        df = pd.DataFrame(
            [
                {
                    "nav_date": r.nav_date,
                    "unit_nav": r.unit_nav,
                    "accumulated_nav": r.accumulated_nav,
                    "adjusted_nav": r.adjusted_nav,
                }
                for r in rows
            ]
        )
        df["nav_date"] = pd.to_datetime(df["nav_date"])
        df = df.set_index("nav_date").sort_index()
        result[code] = df

    return result
