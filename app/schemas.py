from pydantic import BaseModel


# ── Fund ──

class FundCreate(BaseModel):
    fund_code: str
    fund_name: str
    fund_type: str = ""
    asset_bucket: str = ""
    inception_date: str | None = None
    fund_company: str = ""
    note: str = ""


class FundUpdate(BaseModel):
    fund_name: str | None = None
    fund_type: str | None = None
    asset_bucket: str | None = None
    inception_date: str | None = None
    fund_company: str | None = None
    is_active: bool | None = None
    note: str | None = None


# ── Experiment Group ──

class ExperimentGroupCreate(BaseModel):
    group_name: str
    research_question: str = ""
    note: str = ""


class ExperimentGroupUpdate(BaseModel):
    group_name: str | None = None
    research_question: str | None = None
    note: str | None = None


# ── Experiment ──

class ExperimentCreate(BaseModel):
    experiment_name: str
    experiment_group_id: str
    target_weights: dict[str, float]
    role: str = "main"
    start_date: str | None = None
    end_date: str | None = None
    rebalance_rule: str = "no_rebalance"
    cost_model: str = "{}"
    note: str = ""


class ExperimentUpdate(BaseModel):
    experiment_name: str | None = None
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    rebalance_rule: str | None = None
    note: str | None = None
    target_weights: dict[str, float] | None = None


# ── Stress Period ──

class StressPeriodCreate(BaseModel):
    period_name: str
    start_date: str
    end_date: str
    description: str = ""


class StressPeriodUpdate(BaseModel):
    period_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    is_active: bool | None = None
