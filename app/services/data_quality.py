"""Backtest data quality scoring."""


def compute_data_quality(
    mixed_nav: bool,
    missing_diag: dict[str, dict],
    qdii_count: int = 0,
) -> tuple[str, list[str]]:
    """Compute data quality grade (A/B/C/D) and reasons."""
    reasons: list[str] = []

    total_fills = sum(d.get("forward_fill_count", 0) for d in missing_diag.values())
    total_missing = sum(d.get("still_missing", 0) for d in missing_diag.values())

    if mixed_nav:
        reasons.append("净值口径混用")

    if qdii_count > 0:
        reasons.append(f"{qdii_count} 只 QDII 基金存在潜在净值滞后")

    if total_fills > 0:
        reasons.append(f"共发生 {total_fills} 次短缺口前向填充")

    if mixed_nav and total_fills > 30:
        return ("D", reasons + ["数据质量过低，拒绝生成正式回测报告"])

    if mixed_nav and total_fills > 10:
        return ("C", reasons)

    if mixed_nav:
        return ("C", reasons)

    if total_fills > 20:
        return ("C", reasons)

    if total_fills > 0 or total_missing > 0:
        return ("B", reasons)

    return ("A", reasons)
