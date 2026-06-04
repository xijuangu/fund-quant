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

// ── Asset bucket mapping (English DB keys → Chinese labels) ──

export const BUCKET_KEYS = [
  'a_share_equity',
  'overseas_qdii',
  'bond',
  'gold_commodity',
  'money_market',
] as const;

export const BUCKET_LABELS: Record<string, string> = {
  a_share_equity: 'A股权益',
  overseas_qdii: '海外/QDII权益',
  bond: '债券',
  gold_commodity: '黄金/商品',
  money_market: '货币/现金替代',
};

export const BUCKET_COLORS: Record<string, string> = {
  a_share_equity: '#1677ff',
  overseas_qdii: '#13c2c2',
  bond: '#52c41a',
  gold_commodity: '#fa8c16',
  money_market: '#8c8c8c',
};

export const BUCKET_ORDER: Record<string, number> = {
  a_share_equity: 0,
  overseas_qdii: 1,
  bond: 2,
  gold_commodity: 3,
  money_market: 4,
};
