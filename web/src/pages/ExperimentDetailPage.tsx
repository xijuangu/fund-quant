import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Table, Button, Modal, Form, Input, Select, InputNumber, Space, Tag, message,
  Card, Typography, Tooltip, Statistic, Row, Col, Divider, Popconfirm,
} from 'antd';
import {
  PlusOutlined, PlayCircleOutlined, ReloadOutlined,
  ArrowLeftOutlined, InfoCircleOutlined, FileTextOutlined,
  CheckCircleOutlined, ClockCircleOutlined,
  EditOutlined, DeleteOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../api/client';
import type { PortfolioExperiment, FundBasic, BacktestResult } from '../api/types';
import { BUCKET_LABELS } from '../api/types';

const { Text } = Typography;

const REBALANCE_RULES = [
  { label: '不再平衡', value: 'no_rebalance' },
  { label: '月度再平衡', value: 'monthly' },
  { label: '季度再平衡', value: 'quarterly' },
  { label: '阈值再平衡（5%）', value: 'threshold_5pct' },
  { label: '阈值再平衡（10%）', value: 'threshold_10pct' },
];

const ROLES: Record<string, { label: string; color: string }> = {
  main: { label: '主实验', color: '#1677ff' },
  benchmark: { label: '基准', color: '#fa8c16' },
  variant: { label: '变体', color: '#8c8c8c' },
};

const QUALITY_COLORS: Record<string, string> = { A: '#52c41a', B: '#1677ff', C: '#fa8c16', D: '#ff4d4f' };

interface ExpWithStatus extends PortfolioExperiment {
  _hasResult?: boolean;
  _resultId?: string;
  _qualityLevel?: string;
}

export default function ExperimentDetailPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const [experiments, setExperiments] = useState<ExpWithStatus[]>([]);
  const [funds, setFunds] = useState<FundBasic[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingExp, setEditingExp] = useState<PortfolioExperiment | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [groupName, setGroupName] = useState('');
  const [expDetail, setExpDetail] = useState<PortfolioExperiment | null>(null);
  const [viewingReport, setViewingReport] = useState<string | null>(null);
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [form] = Form.useForm();

  const fetchExperiments = async () => {
    setLoading(true);
    try {
      const data = await api.get<PortfolioExperiment[]>(`/experiments?group_id=${groupId}`);
      const enriched: ExpWithStatus[] = [];
      for (const exp of data) {
        try {
          const bt = await api.get<BacktestResult>(`/backtests/results/by-experiment/${exp.experiment_id}`);
          enriched.push({ ...exp, _hasResult: true, _resultId: bt.result_id, _qualityLevel: bt.data_quality_level });
        } catch {
          enriched.push({ ...exp, _hasResult: false });
        }
      }
      setExperiments(enriched);
    } catch {
      message.error('获取实验列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchFunds = async () => {
    try { const data = await api.get<FundBasic[]>('/funds?is_active=true'); setFunds(data); } catch { /* ignore */ }
  };

  useEffect(() => {
    const load = async () => {
      try { const g = await api.get<{ group_name: string }>(`/experiment-groups/${groupId}`); setGroupName(g.group_name); } catch { /* */ }
    };
    load(); fetchExperiments(); fetchFunds();
  }, [groupId]);

  const openCreate = () => { setEditingExp(null); form.resetFields(); setModalOpen(true); };

  const openEdit = async (experimentId: string) => {
    try {
      const detail = await api.get<PortfolioExperiment>(`/experiments/${experimentId}`);
      setEditingExp(detail);
      form.setFieldsValue({
        experiment_name: detail.experiment_name,
        role: detail.role,
        rebalance_rule: detail.rebalance_rule,
        start_date: detail.start_date,
        end_date: detail.end_date,
        note: detail.note,
        positions: (detail.positions || []).map((p) => ({ fund_code: p.fund_code, target_weight: Math.round(p.target_weight * 100) })),
      });
      setModalOpen(true);
    } catch { message.error('获取实验详情失败'); }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const targetWeights: Record<string, number> = {};
      for (const pos of values.positions || []) { targetWeights[pos.fund_code] = pos.target_weight / 100; }
      const total = Object.values(targetWeights).reduce((a, b) => a + b, 0);
      if (Math.abs(total - 1.0) > 0.01) { message.error('目标权重合计必须为 100%'); return; }

      if (editingExp) {
        await api.put(`/experiments/${editingExp.experiment_id}`, {
          experiment_name: values.experiment_name,
          role: values.role,
          rebalance_rule: values.rebalance_rule,
          start_date: values.start_date || null,
          end_date: values.end_date || null,
          note: values.note || '',
          target_weights: targetWeights,
        });
        message.success('实验已更新');
      } else {
        await api.post('/experiments', {
          experiment_name: values.experiment_name,
          experiment_group_id: groupId!,
          target_weights: targetWeights,
          role: values.role || 'main',
          start_date: values.start_date || null,
          end_date: values.end_date || null,
          rebalance_rule: values.rebalance_rule || 'no_rebalance',
          note: values.note || '',
        });
        message.success('实验已创建');
      }
      setModalOpen(false); form.resetFields(); setEditingExp(null); fetchExperiments();
    } catch { /* handled */ }
  };

  const handleDelete = async (experimentId: string) => {
    try { await api.del(`/experiments/${experimentId}`); message.success('实验已删除'); fetchExperiments(); } catch { message.error('删除失败'); }
  };

  const handleRunBacktest = async (experimentId: string) => {
    setRunningId(experimentId);
    try {
      const result = await api.post(`/backtests/run/${experimentId}`, {});
      message.success(`回测完成 · 数据质量: ${(result as { data_quality_level: string }).data_quality_level}`);
      fetchExperiments();
    } catch { message.error('回测失败'); } finally { setRunningId(null); }
  };

  const handleViewDetail = async (experimentId: string) => {
    try {
      const detail = await api.get<PortfolioExperiment>(`/experiments/${experimentId}`);
      setExpDetail(detail); setViewingReport(null); setReportContent(null);
    } catch { message.error('获取实验详情失败'); }
  };

  const handleViewReport = async (resultId: string, _experimentId: string) => {
    setViewingReport(_experimentId);
    try { const data = await api.get<{ report: string }>(`/backtests/results/${resultId}/report`); setReportContent(data.report); } catch { message.error('获取报告失败'); }
  };

  const fundNameMap = useMemo(() => { const m: Record<string, string> = {}; for (const f of funds) m[f.fund_code] = f.fund_name; return m; }, [funds]);

  const columns: ColumnsType<ExpWithStatus> = [
    { title: '实验名称', dataIndex: 'experiment_name', key: 'experiment_name', sorter: (a, b) => a.experiment_name.localeCompare(b.experiment_name), render: (v: string, r) => (<Space><Text strong>{v}</Text>{r._hasResult ? (<Tooltip title={`已回测 · 质量: ${r._qualityLevel}`}><Tag color={QUALITY_COLORS[r._qualityLevel || 'B']} style={{ margin: 0 }}><CheckCircleOutlined /> {r._qualityLevel}</Tag></Tooltip>) : (<Tooltip title="尚未回测"><Tag style={{ margin: 0 }}><ClockCircleOutlined /> 未回测</Tag></Tooltip>)}</Space>) },
    { title: '角色', dataIndex: 'role', key: 'role', width: 90, render: (role: string) => { const r = ROLES[role] || { label: role, color: '#8c8c8c' }; return <Tag color={r.color}>{r.label}</Tag>; } },
    { title: '再平衡', dataIndex: 'rebalance_rule', key: 'rebalance_rule', width: 150, render: (rule: string) => REBALANCE_RULES.find((r) => r.value === rule)?.label || rule },
    { title: '回测区间', key: 'date_range', width: 210, sorter: (a, b) => (a.start_date || '').localeCompare(b.start_date || ''), render: (_, r) => (<Text style={{ fontSize: 13 }}>{r.start_date || '—'} ～ {r.end_date || '—'}</Text>) },
    { title: '操作', key: 'actions', width: 270, render: (_, record) => (<Space size={0}>{record._hasResult ? (<><Button type="primary" size="small" icon={<PlayCircleOutlined />} loading={runningId === record.experiment_id} onClick={() => handleRunBacktest(record.experiment_id)}>重跑</Button><Button size="small" icon={<InfoCircleOutlined />} onClick={() => handleViewDetail(record.experiment_id)}>详情</Button></>) : (<Button type="primary" size="small" icon={<PlayCircleOutlined />} loading={runningId === record.experiment_id} onClick={() => handleRunBacktest(record.experiment_id)}>回测</Button>)}<Tooltip title="编辑"><Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(record.experiment_id)} /></Tooltip><Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.experiment_id)} okText="删除" cancelText="取消"><Button type="link" danger size="small" icon={<DeleteOutlined />} /></Popconfirm></Space>) },
  ];

  return (
    <>
      <div className="page-header">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/experiments')} />
          <div><h2 style={{ margin: 0 }}>{groupName || '加载中...'}</h2><Text type="secondary" style={{ fontSize: 13 }}>实验组</Text></div>
        </Space>
        <Space><Tooltip title="刷新"><Button icon={<ReloadOutlined />} onClick={fetchExperiments} /></Tooltip><Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>创建实验</Button></Space>
      </div>

      <Table columns={columns} dataSource={experiments} rowKey="experiment_id" loading={loading} size="middle" pagination={false} locale={{ emptyText: '暂无实验，点击"创建实验"开始' }} style={{ marginBottom: 24 }} />

      {expDetail && (
        <Card title={`实验详情：${expDetail.experiment_name}`} className="card-elevated" extra={<Space>{(() => { const extExp = experiments.find((e) => e.experiment_id === expDetail.experiment_id); if (extExp?._hasResult) { return (<Button size="small" type={viewingReport === expDetail.experiment_id ? 'primary' : 'default'} icon={<FileTextOutlined />} onClick={() => { if (viewingReport === expDetail.experiment_id) { setViewingReport(null); setReportContent(null); } else { const expWithStatus = experiments.find((e) => e.experiment_id === expDetail.experiment_id); if (expWithStatus?._resultId) { handleViewReport(expWithStatus._resultId, expDetail.experiment_id); } } }}>{viewingReport === expDetail.experiment_id ? '收起报告' : '查看报告'}</Button>); } return null; })()}<Button size="small" onClick={() => { setExpDetail(null); setViewingReport(null); setReportContent(null); }}>关闭</Button></Space>} style={{ marginBottom: 24 }}>
          <Row gutter={[24, 16]}>
            <Col xs={24} sm={8}><Statistic title="角色" value={ROLES[expDetail.role]?.label || expDetail.role} /></Col>
            <Col xs={24} sm={8}><Statistic title="再平衡规则" value={REBALANCE_RULES.find((r) => r.value === expDetail.rebalance_rule)?.label || expDetail.rebalance_rule} /></Col>
            <Col xs={24} sm={8}><Statistic title="回测区间" value={`${expDetail.start_date || '—'} ～ ${expDetail.end_date || '—'}`} /></Col>
          </Row>
          <Divider />
          <Text strong>持仓配置</Text>
          <Table dataSource={expDetail.positions || []} rowKey="fund_code" pagination={false} size="small" style={{ marginTop: 12, marginBottom: reportContent ? 24 : 0 }}
            columns={[{ title: '基金代码', dataIndex: 'fund_code', width: 110, render: (v: string) => <Text code>{v}</Text> }, { title: '基金名称', key: 'name', render: (_, r) => fundNameMap[r.fund_code] || '-' }, { title: '资产桶', dataIndex: 'asset_bucket_snapshot', width: 140, render: (v: string) => v || '-' }, { title: '目标权重', dataIndex: 'target_weight', width: 120, render: (v: number) => (<div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><div style={{ width: 80, height: 6, background: '#f0f0f0', borderRadius: 3, overflow: 'hidden' }}><div style={{ width: `${Math.round(v * 100)}%`, height: '100%', background: '#1677ff', borderRadius: 3 }} /></div><Text style={{ fontSize: 13 }}>{(v * 100).toFixed(1)}%</Text></div>) }]} />
          {reportContent && (<><Divider /><Text strong style={{ marginBottom: 12, display: 'block' }}>研究报告</Text><div className="report-preview">{reportContent}</div></>)}
        </Card>
      )}

      <Modal title={editingExp ? '编辑实验' : '创建实验'} open={modalOpen} onOk={handleSubmit} onCancel={() => { setModalOpen(false); form.resetFields(); setEditingExp(null); }} okText={editingExp ? '保存' : '创建'} cancelText="取消" width={640}>
        <Form form={form} layout="vertical">
          <Form.Item name="experiment_name" label="实验名称" rules={[{ required: true }]}><Input placeholder="如 75/15/10 月度再平衡" /></Form.Item>
          <Form.Item name="role" label="实验角色" initialValue="main"><Select options={Object.entries(ROLES).map(([k, v]) => ({ label: v.label, value: k }))} /></Form.Item>
          <Form.Item name="rebalance_rule" label="再平衡规则" initialValue="monthly"><Select options={REBALANCE_RULES} /></Form.Item>
          <Space><Form.Item name="start_date" label="开始日期"><Input placeholder="YYYY-MM-DD" /></Form.Item><Form.Item name="end_date" label="结束日期"><Input placeholder="YYYY-MM-DD" /></Form.Item></Space>
          <Card title="基金配置" size="small" style={{ marginBottom: 16 }}>
            <Form.List name="positions">
              {(fields, { add, remove }) => (<>{fields.map(({ key, name, ...rest }) => (<Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline"><Form.Item {...rest} name={[name, 'fund_code']} rules={[{ required: true }]}><Select placeholder="选择基金" style={{ width: 200 }} showSearch filterOption={(input, option) => String(option?.label ?? '').toLowerCase().includes(input.toLowerCase())}>{funds.map((f) => (<Select.Option key={f.fund_code} value={f.fund_code}>{f.fund_code} {f.fund_name}</Select.Option>))}</Select></Form.Item><Form.Item {...rest} name={[name, 'target_weight']} rules={[{ required: true }]}><InputNumber placeholder="权重%" min={0} max={100} style={{ width: 100 }} /></Form.Item><Button type="link" danger onClick={() => remove(name)}>删除</Button></Space>))}<Button type="dashed" onClick={() => add()} block>添加基金</Button></>)}
            </Form.List>
          </Card>
          <Form.Item name="note" label="备注"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
