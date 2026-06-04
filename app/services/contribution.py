"""Return and drawdown contribution calculation."""


def compute_daily_contributions(
    weights_before_return: dict[str, float],
    daily_returns: dict[str, float],
) -> dict[str, float]:
    """Compute daily return contribution for each fund.

    contribution_i = weight_i_before_return * daily_return_i
    """
    contribs: dict[str, float] = {}
    for code in weights_before_return:
        w = weights_before_return.get(code, 0.0)
        r = daily_returns.get(code, 0.0)
        contribs[code] = round(w * r, 10)
    return contribs


def aggregate_contributions(
    daily_contributions: list[dict],
) -> dict[str, float]:
    """Aggregate daily contributions over a period (approximate)."""
    totals: dict[str, float] = {}
    for day in daily_contributions:
        for code, contrib in day["contributions"].items():
            totals[code] = totals.get(code, 0.0) + contrib
    return totals
