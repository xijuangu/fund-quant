from __future__ import annotations

import math


def calculate_daily_returns(nav_series: list[float]) -> list[float]:
    """Calculate daily percentage returns from a NAV series."""
    if len(nav_series) < 2:
        return []

    returns: list[float] = []
    for previous_nav, current_nav in zip(nav_series, nav_series[1:]):
        if previous_nav == 0:
            raise ValueError("NAV series cannot contain zero as a previous NAV value")
        returns.append(round(current_nav / previous_nav - 1, 10))
    return returns


def calculate_max_drawdown(nav_series: list[float]) -> float:
    """Calculate maximum drawdown as a negative percentage."""
    if not nav_series:
        return 0.0

    peak = nav_series[0]
    max_drawdown = 0.0
    for nav in nav_series:
        if nav > peak:
            peak = nav
        if peak == 0:
            raise ValueError("NAV series cannot contain zero as a peak NAV value")
        drawdown = nav / peak - 1
        if drawdown < max_drawdown:
            max_drawdown = drawdown
    return max_drawdown


def calculate_cumulative_return(nav_series: list[float]) -> float:
    """Calculate cumulative return from a NAV series."""
    if len(nav_series) < 2:
        return 0.0
    return nav_series[-1] / nav_series[0] - 1


def calculate_annualized_return(
    start_nav: float, end_nav: float, years: float
) -> float:
    """Calculate annualized return given start/end NAV and period in years."""
    if start_nav <= 0 or years <= 0:
        return 0.0
    return (end_nav / start_nav) ** (1 / years) - 1


def calculate_annualized_volatility(daily_returns: list[float]) -> float:
    """Calculate annualized volatility from daily returns."""
    if len(daily_returns) < 2:
        return 0.0
    n = len(daily_returns)
    mean = sum(daily_returns) / n
    variance = sum((r - mean) ** 2 for r in daily_returns) / (n - 1)
    return math.sqrt(variance) * math.sqrt(252)


def calculate_sharpe_ratio(
    daily_returns: list[float], risk_free_rate: float = 0.0
) -> float:
    """Calculate Sharpe ratio from daily returns."""
    if len(daily_returns) < 2:
        return 0.0
    n = len(daily_returns)
    mean_daily = sum(daily_returns) / n
    std_daily = math.sqrt(sum((r - mean_daily) ** 2 for r in daily_returns) / (n - 1))
    if std_daily == 0:
        return 0.0
    excess_daily = mean_daily - risk_free_rate / 252
    return (excess_daily / std_daily) * math.sqrt(252)


def calculate_calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
    """Calculate Calmar ratio = annualized return / abs(max drawdown)."""
    if max_drawdown >= 0:
        return 0.0
    return annualized_return / abs(max_drawdown)

