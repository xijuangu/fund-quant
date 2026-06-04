import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BacktestResult(Base):
    __tablename__ = "backtest_result"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_experiment.experiment_id"), nullable=False
    )
    run_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    contribution_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    rebalance_records_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    nav_policy_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    missing_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    data_quality_level: Mapped[str] = mapped_column(String(1), nullable=False, default="B")
    data_quality_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    report_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)


class BacktestNavDaily(Base):
    __tablename__ = "backtest_nav_daily"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("backtest_result.result_id"), primary_key=True
    )
    nav_date: Mapped[date] = mapped_column(Date, primary_key=True)
    portfolio_nav: Mapped[float] = mapped_column(Float, nullable=False)
    portfolio_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    drawdown: Mapped[float | None] = mapped_column(Float, nullable=True)
