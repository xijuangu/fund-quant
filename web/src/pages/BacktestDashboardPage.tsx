import { useEffect, useState } from 'react';
import { Table, Card, Typography, Tag, Space, Button, message, Descriptions } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../api/client';
import type { BacktestResult, BacktestMetrics } from '../api/types';

interface EnrichedBacktestResult extends BacktestResult {
  _experiment_name?: string;
  _role?: string;
  _group_name?: string;
}

const { Title, Text } = Typography;

export default function BacktestDashboardPage() {
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<BacktestResult | null>(null);
  const [report, setReport] = useState<string | null>(null);

  // In a v1, we'd need an endpoint that lists all backtest results.
  // For now, we'll show results from known experiments.
  const fetchResults = async () => {
    setLoading(true);
    try {
      // Fetch experiments and their backtest results
      const groups = await api.get<{ experiment_group_id: string; group_name: string; }[]>('/experiment-groups');
      const allResults: EnrichedBacktestResult[] = [];
      for (const g of groups) {
        try {
          const exps = await api.get<{ experiment_id: string; experiment_name: string; role: string; }[]>(`/experiments?group_id=${g.experiment_group_id}`);
          for (const exp of exps) {
            try {
              const bt = await api.get<BacktestResult>(`/backtests/results/${exp.experiment_id}`);
              if (bt.result_id) {
                allResults.push({ ...bt, _experiment_name: exp.experiment_name, _role: exp.role, _group_name: g.group_name });
              }
            } catch { /* no backtest result for this experiment */ }
          }
        } catch { /* skip */ }
      }
      setResults(allResults);
    } catch {
      message.error('获取回测结果失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchResults(); }, []);

  const handleViewReport = async (resultId: string) => {
    try {
      const data = await api.get<{ report: string }>(`/backtests/results/${resultId}/report`);
      setReport(data.report);
    } catch {
      message.error('获取报告失败');
    }
  };

  const columns: ColumnsType<EnrichedBacktestResult> = [
    { title: '组', dataIndex: '_group_name', key: 'group', width: 150, render: (v: string) => v || '-' },
    { title: '实验', dataIndex: '_experiment_name', key: 'experiment', render: (v: string) => v || '-' },
    {
      title: '角色',
      dataIndex: '_role',
      key: 'role',
      width: 80,
      render: (role: string) => {
        const labels: Record<string, string> = { main: '主实验', benchmark: '基准', variant: '变体' };
        return labels[role] || role;
      },
    },
    {
      title: '年化收益',
      key: 'ann_ret',
      width: 100,
      render: (_, r) => <Text style={{ color: r.metrics.annualized_return >= 0 ? '#3f8600' : '#cf1322' }}>{(r.metrics.annualized_return * 100).toFixed(2)}%</Text>,
    },
    {
      title: '最大回撤',
      key: 'max_dd',
      width: 100,
      render: (_, r) => <Text style={{ color: '#cf1322' }}>{(r.metrics.max_drawdown * 100).toFixed(2)}%</Text>,
    },
    { title: '夏普比率', key: 'sharpe', width: 90, render: (_, r) => r.metrics.sharpe_ratio.toFixed(2) },
    { title: '年化波动率', key: 'vol', width: 100, render: (_, r) => (r.metrics.annualized_volatility * 100).toFixed(2) + '%' },
    {
      title: '数据质量',
      dataIndex: 'data_quality_level',
      key: 'quality',
      width: 90,
      render: (level: string) => {
        const colors: Record<string, string> = { A: 'green', B: 'blue', C: 'orange', D: 'red' };
        return <Tag color={colors[level] || 'default'}>{level}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button size="small" icon={<FileTextOutlined />} onClick={() => handleViewReport(record.result_id)}>
          报告
        </Button>
      ),
    },
  ];

  return (
    <>
      <Table
        columns={columns}
        dataSource={results}
        rowKey="result_id"
        loading={loading}
        size="middle"
        style={{ marginBottom: 24 }}
      />
      {report && (
        <Card
          title="研究报告"
          extra={<Button onClick={() => setReport(null)}>关闭</Button>}
        >
          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: 14, lineHeight: 1.6 }}>
            {report}
          </pre>
        </Card>
      )}
    </>
  );
}
