import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExperimentGroup(Base):
    __tablename__ = "experiment_group"

    experiment_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_name: Mapped[str] = mapped_column(String(256), nullable=False)
    research_question: Mapped[str] = mapped_column(Text, nullable=False, default="")
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PortfolioExperiment(Base):
    __tablename__ = "portfolio_experiment"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_name: Mapped[str] = mapped_column(String(256), nullable=False)
    experiment_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiment_group.experiment_group_id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="main")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rebalance_rule: Mapped[str] = mapped_column(String(64), nullable=False, default="no_rebalance")
    cost_model: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PortfolioPosition(Base):
    __tablename__ = "portfolio_position"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_experiment.experiment_id"), primary_key=True
    )
    fund_code: Mapped[str] = mapped_column(
        String(16), ForeignKey("fund_basic.fund_code"), primary_key=True
    )
    target_weight: Mapped[float] = mapped_column(Float, nullable=False)
    asset_bucket_snapshot: Mapped[str] = mapped_column(String(64), nullable=False, default="")
