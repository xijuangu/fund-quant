"""Portfolio rebalance calculation."""

from datetime import date


def check_rebalance_trigger(
    rule: str,
    current_date: date,
    last_rebalance_date: date | None,
    current_weights: dict[str, float] | None = None,
    target_weights: dict[str, float] | None = None,
) -> bool:
    if rule == "no_rebalance":
        return False
    if last_rebalance_date is None:
        return True
    if rule == "monthly":
        if current_date.year != last_rebalance_date.year:
            return True
        return current_date.month != last_rebalance_date.month
    if rule == "quarterly":
        if current_date.year != last_rebalance_date.year:
            return True
        current_quarter = (current_date.month - 1) // 3
        last_quarter = (last_rebalance_date.month - 1) // 3
        return current_quarter != last_quarter
    if rule == "threshold_5pct":
        return _max_deviation(current_weights, target_weights) >= 0.05
    if rule == "threshold_10pct":
        return _max_deviation(current_weights, target_weights) >= 0.10
    return False


def _max_deviation(
    current: dict[str, float] | None, target: dict[str, float] | None
) -> float:
    if current is None or target is None:
        return 0.0
    max_dev = 0.0
    for k in target:
        max_dev = max(max_dev, abs(target[k] - current.get(k, 0.0)))
    return max_dev


def compute_rebalance_trades(
    target_weights: dict[str, float], current_weights: dict[str, float]
) -> dict[str, float]:
    trades: dict[str, float] = {}
    for k in target_weights:
        trades[k] = target_weights[k] - current_weights.get(k, 0.0)
    return trades


def apply_rebalance(
    target_weights: dict[str, float], current_weights: dict[str, float]
) -> dict[str, float]:
    return dict(target_weights)


def compute_turnover(trades: dict[str, float]) -> float:
    return sum(abs(v) for v in trades.values()) / 2


def estimate_cost(trades: dict[str, float], cost_rates: dict[str, float]) -> float:
    return sum(abs(trades[k]) * cost_rates.get(k, 0.0) for k in trades)
