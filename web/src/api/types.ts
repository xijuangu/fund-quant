export interface FundBasic {
  fund_code: string;
  fund_name: string;
  fund_type: string;
  asset_bucket: string;
  inception_date: string | null;
  fund_company: string;
  is_active: boolean;
  note: string;
}

export interface ExperimentGroup {
  experiment_group_id: string;
  group_name: string;
  research_question: string;
  note: string;
}

export interface PortfolioExperiment {
  experiment_id: string;
  experiment_name: string;
  experiment_group_id: string;
  role: 'main' | 'benchmark' | 'variant';
  start_date: string | null;
  end_date: string | null;
  rebalance_rule: string;
  note: string;
  positions?: PortfolioPosition[];
}

export interface PortfolioPosition {
  fund_code: string;
  target_weight: number;
  asset_bucket_snapshot: string;
}

export interface BacktestResult {
  result_id: string;
  experiment_id: string;
  metrics: BacktestMetrics;
  nav_policy: NavPolicy;
  data_quality_level: string;
  data_quality: string[];
  daily_nav?: DailyNav[];
  report_markdown?: string;
}

export interface BacktestMetrics {
  cumulative_return: number;
  annualized_return: number;
  annualized_volatility: number;
  max_drawdown: number;
  sharpe_ratio: number;
  calmar_ratio: number;
  best_month_return: number;
  worst_month_return: number;
  positive_month_pct: number;
  total_trading_days: number;
  years: number;
}

export interface NavPolicy {
  preferred: string;
  actual_used: Record<string, string>;
  mixed_policy: boolean;
}

export interface DailyNav {
  nav_date: string;
  portfolio_nav: number;
  portfolio_return: number;
  drawdown: number;
}

export interface StressPeriod {
  period_id: string;
  period_name: string;
  start_date: string;
  end_date: string;
  description: string;
  is_active: boolean;
}
