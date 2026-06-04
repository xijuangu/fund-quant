import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FundBasic(Base):
    __tablename__ = "fund_basic"

    fund_code: Mapped[str] = mapped_column(String(16), primary_key=True)
    fund_name: Mapped[str] = mapped_column(String(128), nullable=False)
    fund_type: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    asset_bucket: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    inception_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    fund_company: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FundNavDaily(Base):
    __tablename__ = "fund_nav_daily"

    fund_code: Mapped[str] = mapped_column(String(16), primary_key=True)
    nav_date: Mapped[date] = mapped_column(Date, primary_key=True)
    unit_nav: Mapped[float | None] = mapped_column(nullable=True)
    accumulated_nav: Mapped[float | None] = mapped_column(nullable=True)
    adjusted_nav: Mapped[float | None] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="csv")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
