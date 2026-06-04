import { useEffect, useState, useMemo } from 'react';
import {
  Table, Typography, Tag, Space, Button, message, Modal, Select, Tooltip, Popconfirm,
} from 'antd';
import {
  FileTextOutlined, ReloadOutlined, DeleteOutlined,
  ArrowUpOutlined, ArrowDownOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../api/client';
import type { BacktestResult } from '../api/types';
import { KpiCard, PageHeader, StatGrid, Toolbar } from '../components/workspace';

const { Text } = Typography;

interface EnrichedBacktestResult extends BacktestResult {
  _experiment_name?: string;
  _role?: string;
  _group_name?: string;
}

const ROLE_LABELS: Record<string, string> = { main: '主实验', benchmark: '基准', variant: '变体' };
const ROLE_COLORS: Record<string, string> = { main: '#1677ff', benchmark: '#fa8c16', variant: '#8c8c8c' };
const QUALITY_COLORS: Record<string, string> = { A: '#52c41a', B: '#1677ff', C: '#fa8c16', D: '#ff4d4f' };

function fmtPct(v: number) { return `${(v * 100).toFixed(2)}%`; }
function fmtNum(v: number, d = 2) { return v.toFixed(d); }

export default function BacktestDashboardPage() {
  const [results, setResults] = useState<EnrichedBacktestResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [reportModal, setReportModal] = useState<{ open: boolean; title: string; content: string }>({ open: false, title: '', content: '' });
  const [roleFilter, setRoleFilter] = useState<string | null>(null);
  const [groupFilter, setGroupFilter] = useState<string | null>(null);

  const fetchResults = async () => {
    setLoading(true);
    try {
      const groups = await api.get<{ experiment_group_id: string; group_name: string }[]>('/experiment-groups');
      const groupResults = await Promise.all(groups.map(async (g) => {
        try {
          const exps = await api.get<{ experiment_id: string; experiment_name: string; role: string }[]>(`/experiments?group_id=${g.experiment_group_id}`);
          const backtests = await Promise.all(exps.map(async (exp): Promise<EnrichedBacktestResult | null> => {
            try {
              const bt = await api.get<BacktestResult>(`/backtests/results/by-experiment/${exp.experiment_id}`);
              if (bt.result_id) {
                return { ...bt, _experiment_name: exp.experiment_name, _role: exp.role, _group_name: g.group_name };
              }
            } catch { /* no result */ }
            return null;
          }));
          return backtests.filter((bt): bt is EnrichedBacktestResult => bt !== null);
        } catch {
          return [];
        }
      }));
      const allResults = groupResults.flat();
      setResults(allResults);
    } catch { message.error('获取回测结果失败'); } finally { setLoading(false); }
  };

  useEffect(() => { fetchResults(); }, []);

  const handleViewReport = async (resultId: string, title: string) => {
    setReportModal({ open: true, title, content: '加载中...' });
    try {
      const data = await api.get<{ report: string }>(`/backtests/results/${resultId}/report`);
      setReportModal({ open: true, title, content: data.report });
    } catch { message.error('获取报告失败'); setReportModal((prev) => ({ ...prev, open: false })); }
  };

  const handleDelete = async (resultId: string) => {
    try { await api.del(`/backtests/results/${resultId}`); message.success('回测结果已删除'); fetchResults(); } catch { message.error('删除失败'); }
  };

  const { groupNames, roleValues } = useMemo(() => {
    const gn = new Set<string>(); const rv = new Set<string>();
    for (const r of results) { if (r._group_name) gn.add(r._group_name); if (r._role) rv.add(r._role); }
    return { groupNames: [...gn], roleValues: [...rv] };
  }, [results]);

  const filtered = useMemo(() => {
    let list = results;
    if (groupFilter) list = list.filter((r) => r._group_name === groupFilter);
    if (roleFilter) list = list.filter((r) => r._role === roleFilter);
    return list.sort((a, b) => (a._experiment_name || '').localeCompare(b._experiment_name || ''));
  }, [results, groupFilter, roleFilter]);

  const bestBySharpe = useMemo(() => [...results].sort((a, b) => b.metrics.sharpe_ratio - a.metrics.sharpe_ratio)[0], [results]);

  const columns: ColumnsType<EnrichedBacktestResult> = [
    { title: '实验', key: 'experiment', width: 200, sorter: (a, b) => (a._experiment_name || '').localeCompare(b._experiment_name || ''), render: (_, r) => (<Space direction="vertical" size={0}><Text strong>{r._experiment_name}</Text><Text type="secondary" style={{ fontSize: 12 }}>{r._group_name}</Text></Space>) },
    { title: '角色', dataIndex: '_role', key: 'role', width: 80, render: (role: string) => <Tag color={ROLE_COLORS[role] || '#8c8c8c'}>{ROLE_LABELS[role] || role}</Tag> },
    { title: '年化收益', key: 'ann_ret', width: 110, sorter: (a, b) => a.metrics.annualized_return - b.metrics.annualized_return, render: (_, r) => { const v = r.metrics.annualized_return; return <Text style={{ color: v >= 0 ? '#3f8600' : '#cf1322' }}>{v >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />} {fmtPct(v)}</Text>; } },
    { title: '年化波动', key: 'ann_vol', width: 100, sorter: (a, b) => a.metrics.annualized_volatility - b.metrics.annualized_volatility, render: (_, r) => fmtPct(r.metrics.annualized_volatility) },
    { title: '最大回撤', key: 'max_dd', width: 100, sorter: (a, b) => b.metrics.max_drawdown - a.metrics.max_drawdown, render: (_, r) => <Text style={{ color: '#cf1322' }}>{fmtPct(r.metrics.max_drawdown)}</Text> },
    { title: '夏普', key: 'sharpe', width: 70, sorter: (a, b) => a.metrics.sharpe_ratio - b.metrics.sharpe_ratio, render: (_, r) => { const v = r.metrics.sharpe_ratio; return <Text strong style={{ color: v >= 0.5 ? '#3f8600' : v >= 0 ? '#262626' : '#cf1322' }}>{fmtNum(v)}</Text>; } },
    { title: '卡玛', key: 'calmar', width: 70, sorter: (a, b) => a.metrics.calmar_ratio - b.metrics.calmar_ratio, render: (_, r) => fmtNum(r.metrics.calmar_ratio) },
    { title: '正收益月', key: 'pos_month', width: 90, sorter: (a, b) => a.metrics.positive_month_pct - b.metrics.positive_month_pct, render: (_, r) => fmtPct(r.metrics.positive_month_pct) },
    { title: '质量', dataIndex: 'data_quality_level', key: 'quality', width: 60, render: (level: string) => <Tag color={QUALITY_COLORS[level]}>{level}</Tag> },
    { title: '操作', key: 'actions', width: 90, render: (_, record) => (<Space size={0}><Tooltip title="报告"><Button type="link" size="small" icon={<FileTextOutlined />} onClick={() => handleViewReport(record.result_id, record._experiment_name || '回测报告')} /></Tooltip><Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.result_id)} okText="删除" cancelText="取消"><Button type="link" danger size="small" icon={<DeleteOutlined />} /></Popconfirm></Space>) },
  ];

  return (
    <>
      <PageHeader
        title="回测看板"
        description="汇总实验组中的最新回测结果，用收益、回撤、波动和数据质量做横向比较。"
        actions={<Tooltip title="刷新"><Button icon={<ReloadOutlined />} onClick={fetchResults} /></Tooltip>}
      />

      {bestBySharpe && (
        <StatGrid>
          <KpiCard label="实验数量" value={results.length} sub="个回测结果" tone="blue" />
          <KpiCard label="最优夏普" value={fmtNum(bestBySharpe.metrics.sharpe_ratio)} sub={bestBySharpe._experiment_name} tone="green" />
          <KpiCard label="质量 A 级" value={results.filter((r) => r.data_quality_level === 'A').length} sub={`/ ${results.length} 个结果`} tone="green" />
          <KpiCard label="质量 D 级" value={results.filter((r) => r.data_quality_level === 'D').length} sub="数据质量过低" tone="red" />
        </StatGrid>
      )}

      <Toolbar
        filters={
          <>
          <Select placeholder="实验组筛选" value={groupFilter} onChange={setGroupFilter} allowClear style={{ width: 200 }} options={groupNames.map((gn) => ({ label: gn, value: gn }))} />
          <Select placeholder="角色筛选" value={roleFilter} onChange={setRoleFilter} allowClear style={{ width: 130 }} options={roleValues.map((rv) => ({ label: ROLE_LABELS[rv] || rv, value: rv }))} />
          </>
        }
        summary={`共 ${filtered.length} / ${results.length} 个结果`}
      />

      <Table columns={columns} dataSource={filtered} rowKey="result_id" loading={loading} size="middle" pagination={false} locale={{ emptyText: '暂无回测结果，请在实验组中运行回测' }} />

      <Modal title={`研究报告：${reportModal.title}`} open={reportModal.open} onCancel={() => setReportModal({ open: false, title: '', content: '' })} footer={null} width={800}>
        <div className="report-preview">{reportModal.content}</div>
      </Modal>
    </>
  );
}
