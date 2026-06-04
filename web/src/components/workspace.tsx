import type { ReactNode } from 'react';
import { Space, Typography } from 'antd';

const { Text } = Typography;

interface PageHeaderProps {
  title: string;
  description?: string;
  meta?: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({ title, description, meta, actions }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-title-block">
        <Space size={10} align="center" wrap>
          <h2>{title}</h2>
          {meta}
        </Space>
        {description && <Text type="secondary">{description}</Text>}
      </div>
      {actions && <Space wrap>{actions}</Space>}
    </div>
  );
}

interface ToolbarProps {
  filters?: ReactNode;
  summary?: ReactNode;
}

export function Toolbar({ filters, summary }: ToolbarProps) {
  return (
    <div className="table-toolbar">
      <Space wrap>{filters}</Space>
      {summary && <Text type="secondary">{summary}</Text>}
    </div>
  );
}

interface KpiCardProps {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: 'blue' | 'green' | 'gold' | 'red' | 'neutral';
}

export function KpiCard({ label, value, sub, tone = 'neutral' }: KpiCardProps) {
  return (
    <div className={`stat-card stat-card-${tone}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

interface StatGridProps {
  children: ReactNode;
}

export function StatGrid({ children }: StatGridProps) {
  return <div className="stats-grid">{children}</div>;
}
