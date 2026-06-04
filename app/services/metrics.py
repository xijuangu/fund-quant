from __future__ import annotations


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

