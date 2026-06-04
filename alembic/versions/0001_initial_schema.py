"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fund_basic",
        sa.Column("fund_code", sa.String(16), nullable=False),
        sa.Column("fund_name", sa.String(128), nullable=False),
        sa.Column("fund_type", sa.String(32), nullable=False, server_default=""),
        sa.Column("asset_bucket", sa.String(64), nullable=False, server_default=""),
        sa.Column("inception_date", sa.Date(), nullable=True),
        sa.Column("fund_company", sa.String(128), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("fund_code"),
    )

    op.create_table(
        "fund_nav_daily",
        sa.Column("fund_code", sa.String(16), nullable=False),
        sa.Column("nav_date", sa.Date(), nullable=False),
        sa.Column("unit_nav", sa.Float(), nullable=True),
        sa.Column("accumulated_nav", sa.Float(), nullable=True),
        sa.Column("adjusted_nav", sa.Float(), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="csv"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("fund_code", "nav_date"),
    )

    op.create_table(
        "experiment_group",
        sa.Column("experiment_group_id", sa.Uuid(), nullable=False),
        sa.Column("group_name", sa.String(256), nullable=False),
        sa.Column("research_question", sa.Text(), nullable=False, server_default=""),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("experiment_group_id"),
    )

    op.create_table(
        "stress_period",
        sa.Column("period_id", sa.Uuid(), nullable=False),
        sa.Column("period_name", sa.String(256), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("period_id"),
    )

    op.create_table(
        "portfolio_experiment",
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_name", sa.String(256), nullable=False),
        sa.Column("experiment_group_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="main"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("rebalance_rule", sa.String(64), nullable=False, server_default="no_rebalance"),
        sa.Column("cost_model", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("experiment_id"),
        sa.ForeignKeyConstraint(
            ["experiment_group_id"],
            ["experiment_group.experiment_group_id"],
        ),
    )

    op.create_table(
        "portfolio_position",
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("fund_code", sa.String(16), nullable=False),
        sa.Column("target_weight", sa.Float(), nullable=False),
        sa.Column("asset_bucket_snapshot", sa.String(64), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("experiment_id", "fund_code"),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["portfolio_experiment.experiment_id"],
        ),
        sa.ForeignKeyConstraint(
            ["fund_code"],
            ["fund_basic.fund_code"],
        ),
    )

    op.create_table(
        "backtest_result",
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column(
            "run_time",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("metrics_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("contribution_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("rebalance_records_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("nav_policy_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("missing_data_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("data_quality_level", sa.String(1), nullable=False, server_default="B"),
        sa.Column("data_quality_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("report_markdown", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("result_id"),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["portfolio_experiment.experiment_id"],
        ),
    )

    op.create_table(
        "backtest_nav_daily",
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("nav_date", sa.Date(), nullable=False),
        sa.Column("portfolio_nav", sa.Float(), nullable=False),
        sa.Column("portfolio_return", sa.Float(), nullable=True),
        sa.Column("drawdown", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("result_id", "nav_date"),
        sa.ForeignKeyConstraint(
            ["result_id"],
            ["backtest_result.result_id"],
        ),
    )


def downgrade() -> None:
    op.drop_table("backtest_nav_daily")
    op.drop_table("backtest_result")
    op.drop_table("portfolio_position")
    op.drop_table("portfolio_experiment")
    op.drop_table("stress_period")
    op.drop_table("experiment_group")
    op.drop_table("fund_nav_daily")
    op.drop_table("fund_basic")
