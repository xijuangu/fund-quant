"""Portfolio backtest engine."""

from datetime import date

import pandas as pd

from app.services.contribution import compute_daily_contributions
from app.services.data_quality import compute_data_quality
from app.services.metrics import (
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_calmar_ratio,
    calculate_cumulative_return,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
)
from app.services.nav_alignment import (
    align_nav_dates,
    build_common_date_index,
    select_nav_policy,
)
from app.services.rebalance import (
    apply_rebalance,
    check_rebalance_trigger,
    compute_rebalance_trades,
    compute_turnover,
    estimate_cost,
)


def backtest_portfolio(
    fund_navs: dict[str, pd.DataFrame],
    target_weights: dict[str, float],
    rebalance_rule: str = "no_rebalance",
    nav_column: str | None = None,
    cost_rates: dict[str, float] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Run a portfolio backtest and return full results.

    Args:
        fund_navs: dict of fund_code -> DataFrame with NAV columns indexed by date.
        target_weights: dict of fund_code -> target weight (should sum to 1.0).
        rebalance_rule: one of no_rebalance, monthly, quarterly, threshold_5pct, threshold_10pct.
        nav_column: NAV column to use. Auto-detected if None.
        cost_rates: dict of fund_code -> single-side cost rate for estimating tx costs.

    Returns a dict with keys: daily, metrics, nav_policy, missing_data_diagnostics,
    data_quality, data_quality_level, rebalance_records, contributions.
    """
    # Validate
    if abs(sum(target_weights.values()) - 1.0) > 0.001:
        raise ValueError("Target weights must sum to 1.0")

    for code in target_weights:
        if code not in fund_navs:
            raise ValueError(f"Fund {code} is in target weights but has no NAV data")
        if fund_navs[code].empty:
            raise ValueError(f"Fund {code} has no NAV data for selected backtest range")

    # Filter date range
    if start_date is not None or end_date is not None:
        filtered: dict[str, pd.DataFrame] = {}
        for code, df in fund_navs.items():
            m = df
            if start_date is not None:
                m = m[m.index >= pd.Timestamp(start_date)]
            if end_date is not None:
                m = m[m.index <= pd.Timestamp(end_date)]
            if m.empty:
                raise ValueError(f"Fund {code} has no NAV data for selected backtest range")
            filtered[code] = m
        fund_navs = filtered

    # NAV policy
    if nav_column is None:
        policy = select_nav_policy(fund_navs)
        nav_column = policy["preferred"]
    else:
        policy = select_nav_policy(fund_navs)

    # Common date alignment
    common_dates = build_common_date_index(fund_navs)
    if len(common_dates) < 2:
        raise ValueError("Not enough overlapping trading days for backtest")

    aligned_navs, missing_diag = align_nav_dates(fund_navs, common_dates, nav_column)

    # Drop dates where any fund has NaN (after alignment)
    valid_mask = pd.Series(True, index=common_dates)
    for series in aligned_navs.values():
        valid_mask = valid_mask & ~series.isna()
    valid_dates = common_dates[valid_mask]
    valid_navs = {k: v[valid_dates] for k, v in aligned_navs.items()}

    if len(valid_dates) < 2:
        raise ValueError("Not enough valid overlapping trading days after alignment")

    # Run day-by-day simulation
    current_weights = dict(target_weights)
    last_rebalance_date: date | None = None
    portfolio_nav_series = [1.0]
    portfolio_returns: list[float] = []
    drawdowns: list[float] = [0.0]
    daily_records: list[dict] = []
    rebalance_records: list[dict] = []
    contributions: list[dict] = []

    # Convert NAV to numpy for speed
    nav_arrays = {k: v.values for k, v in valid_navs.items()}

    dates_list = list(valid_dates)
    for i in range(1, len(dates_list)):
        current_date = dates_list[i]

        # Compute daily returns per fund
        fund_returns: dict[str, float] = {}
        for code in target_weights:
            prev_nav = nav_arrays[code][i - 1]
            curr_nav = nav_arrays[code][i]
            if prev_nav and prev_nav != 0:
                fund_returns[code] = curr_nav / prev_nav - 1
            else:
                fund_returns[code] = 0.0

        # Update current weights by market movement
        for code in target_weights:
            current_weights[code] = current_weights[code] * (1 + fund_returns[code])
        total_w = sum(current_weights.values())
        for code in current_weights:
            current_weights[code] /= total_w

        # Check rebalance
        if check_rebalance_trigger(
            rebalance_rule,
            current_date.date(),
            last_rebalance_date,
            current_weights,
            target_weights,
        ):
            trades = compute_rebalance_trades(target_weights, current_weights)
            turnover = compute_turnover(trades)
            cost = estimate_cost(trades, cost_rates or {})

            rebalance_records.append(
                {
                    "date": current_date.date().isoformat(),
                    "trades": {k: round(v, 6) for k, v in trades.items()},
                    "turnover": round(turnover, 6),
                    "estimated_cost": round(cost, 8),
                }
            )
            current_weights = apply_rebalance(target_weights, current_weights)
            last_rebalance_date = current_date.date()

        # Portfolio daily return
        port_return = sum(
            current_weights.get(code, 0.0) * fund_returns.get(code, 0.0)
            for code in target_weights
        )
        portfolio_returns.append(port_return)

        # Portfolio NAV
        portfolio_nav_series.append(portfolio_nav_series[-1] * (1 + port_return))

        # Drawdown
        peak = max(portfolio_nav_series)
        dd = portfolio_nav_series[-1] / peak - 1 if peak > 0 else 0.0
        drawdowns.append(dd)

        # Daily contributions
        daily_contribs = compute_daily_contributions(
            current_weights, fund_returns
        )
        contributions.append(
            {"date": current_date.date().isoformat(), "contributions": daily_contribs}
        )

        daily_records.append(
            {
                "nav_date": current_date.date(),
                "portfolio_nav": round(portfolio_nav_series[-1], 4),
                "portfolio_return": round(port_return, 6),
                "drawdown": round(dd, 6),
            }
        )

    # Compute summary metrics
    full_nav_series = [1.0] + [r["portfolio_nav"] for r in daily_records]
    cum_return = calculate_cumulative_return(full_nav_series)
    years = len(portfolio_returns) / 252
    ann_return = calculate_annualized_return(1.0, full_nav_series[-1], years)
    ann_vol = calculate_annualized_volatility(portfolio_returns)
    max_dd = calculate_max_drawdown(full_nav_series)
    sharpe = calculate_sharpe_ratio(portfolio_returns)
    calmar = calculate_calmar_ratio(ann_return, max_dd)

    # Best/worst month
    monthly_returns = _compute_monthly_returns(dates_list[1:], portfolio_returns)
    best_month = max(monthly_returns.values()) if monthly_returns else 0.0
    worst_month = min(monthly_returns.values()) if monthly_returns else 0.0
    positive_months = sum(1 for v in monthly_returns.values() if v > 0)
    total_months = len(monthly_returns)
    positive_month_pct = positive_months / total_months if total_months > 0 else 0.0

    # Data quality
    quality_level, quality_reasons = compute_data_quality(
        policy["mixed_policy"], missing_diag
    )

    metrics = {
        "cumulative_return": round(cum_return, 6),
        "annualized_return": round(ann_return, 6),
        "annualized_volatility": round(ann_vol, 6),
        "max_drawdown": round(max_dd, 6),
        "sharpe_ratio": round(sharpe, 4),
        "calmar_ratio": round(calmar, 4),
        "best_month_return": round(best_month, 6),
        "worst_month_return": round(worst_month, 6),
        "positive_month_pct": round(positive_month_pct, 4),
        "total_trading_days": len(portfolio_returns),
        "years": round(years, 2),
    }

    return {
        "daily": daily_records,
        "metrics": metrics,
        "nav_policy": policy,
        "missing_data_diagnostics": missing_diag,
        "data_quality": quality_reasons,
        "data_quality_level": quality_level,
        "rebalance_records": rebalance_records,
        "contributions": contributions,
    }


def _compute_monthly_returns(
    dates: list[pd.Timestamp], daily_returns: list[float]
) -> dict[str, float]:
    """Compute monthly returns from daily returns."""
    monthly: dict[str, float] = {}
    for d, r in zip(dates, daily_returns):
        key = d.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0.0) + r  # approximate: sum of daily log-like returns
    return monthly
