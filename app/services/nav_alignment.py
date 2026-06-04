"""NAV date alignment and policy selection."""


import pandas as pd


def build_common_date_index(fund_navs: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    """Find the common date range where all funds have data."""
    if not fund_navs:
        return pd.DatetimeIndex([])
    common = None
    for df in fund_navs.values():
        if df.empty:
            return pd.DatetimeIndex([])
        if common is None:
            common = df.index
        else:
            common = common.intersection(df.index)
    return common.sort_values() if common is not None else pd.DatetimeIndex([])


def select_nav_policy(fund_navs: dict[str, pd.DataFrame]) -> dict:
    """Select NAV column to use for backtesting.

    Prefers adjusted > accumulated > unit nav. Returns policy dict.
    """
    preferred = "adjusted_nav"

    # Check availability across all funds
    nav_columns = ["adjusted_nav", "accumulated_nav", "unit_nav"]
    available = {}
    for col in nav_columns:
        if all(col in df.columns and not df[col].isna().all() for df in fund_navs.values()):
            available[col] = True
        else:
            available[col] = False

    if available["adjusted_nav"]:
        preferred = "adjusted_nav"
    elif available["accumulated_nav"]:
        preferred = "accumulated_nav"
    else:
        preferred = "unit_nav"

    actual_used = {}
    for code, df in fund_navs.items():
        if preferred in df.columns and not df[preferred].isna().all():
            actual_used[code] = preferred
        else:
            # fall back for this specific fund
            for col in nav_columns:
                if col in df.columns and not df[col].isna().all():
                    actual_used[code] = col
                    break
            else:
                actual_used[code] = "unit_nav"

    mixed = len(set(actual_used.values())) > 1

    return {
        "preferred": preferred,
        "actual_used": actual_used,
        "mixed_policy": mixed,
    }


def align_nav_dates(
    fund_navs: dict[str, pd.DataFrame],
    common_dates: pd.DatetimeIndex,
    nav_column: str,
) -> tuple[dict[str, pd.Series], dict[str, dict]]:
    """Align all funds to common_dates using the given nav_column.

    Returns (aligned_navs, diagnostics) where diagnostics tracks forward-fill info.
    """
    aligned: dict[str, pd.Series] = {}
    diag: dict[str, dict] = {}

    for code, df in fund_navs.items():
        series = df[nav_column].reindex(common_dates)
        orig_missing = series.isna().sum()

        # Forward-fill only within existing data range (not before first valid value)
        first_valid = df[nav_column].first_valid_index()
        if first_valid is not None:
            mask_before = series.index < first_valid
            series_ffilled = series.ffill()
            # Don't carry forward into dates before inception
            series = series_ffilled.where(~mask_before | ~series_ffilled.isna(), series_ffilled)

        fill_count = int(orig_missing - series.isna().sum())
        still_missing = int(series.isna().sum())

        diag[code] = {
            "original_missing": int(orig_missing),
            "forward_fill_count": fill_count,
            "still_missing": still_missing,
        }
        aligned[code] = series

    return aligned, diag


def compute_missing_data_diagnostics(
    fund_navs: dict[str, pd.DataFrame], common_dates: pd.DatetimeIndex
) -> dict:
    """Compute missing-data diagnostics for the report."""
    total_dates = len(common_dates)
    diag: dict[str, dict] = {}
    for code, df in fund_navs.items():
        overlap = len(df.index.intersection(common_dates))
        diag[code] = {
            "total_common_dates": total_dates,
            "overlap_count": overlap,
            "missing_count": total_dates - overlap,
            "coverage_pct": round(overlap / total_dates * 100, 1) if total_dates > 0 else 0,
        }
    return diag
