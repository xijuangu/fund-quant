import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Table, Button, Modal, Form, Input, Select, InputNumber, Space, Tag, message, Card, Typography,
} from 'antd';
import { PlusOutlined, PlayCircleOutlined, FileTextOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../api/client';
import type { PortfolioExperiment, FundBasic } from '../api/types';

const { Title } = Typography;

const REBALANCE_RULES = [
  { label: '不再平衡', value: 'no_rebalance' },
  { label: '月度再平衡', value: 'monthly' },
  { label: '季度再平衡', value: 'quarterly' },
  { label: '阈值再平衡（5%）', value: 'threshold_5pct' },
  { label: '阈值再平衡（10%）', value: 'threshold_10pct' },
];

const ROLES = [
  { label: '主实验 (main)', value: 'main' },
  { label: '基准实验 (benchmark)', value: 'benchmark' },
  { label: '变体实验 (variant)', value: 'variant' },
];

export default function ExperimentDetailPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const [experiments, setExperiments] = useState<PortfolioExperiment[]>([]);
  const [funds, setFunds] = useState<FundBasic[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const fetchExperiments = async () => {
    setLoading(true);
    try {
      const data = await api.get<PortfolioExperiment[]>(`/experiments?group_id=${groupId}`);
      setExperiments(data);
    } catch {
      message.error('获取实验列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchFunds = async () => {
    try {
      const data = await api.get<FundBasic[]>('/funds?is_active=true');
      setFunds(data);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    fetchExperiments();
    fetchFunds();
  }, [groupId]);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      const targetWeights: Record<string, number> = {};
      for (const pos of values.positions || []) {
        targetWeights[pos.fund_code] = pos.target_weight / 100;
      }
      // Validate weights sum to ~100%
      const total = Object.values(targetWeights).reduce((a, b) => a + b, 0);
      if (Math.abs(total - 1.0) > 0.01) {
        message.error('目标权重合计必须为 100%');
        return;
      }

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
      setModalOpen(false);
      form.resetFields();
      fetchExperiments();
    } catch { /* handled */ }
  };

  const handleRunBacktest = async (experimentId: string) => {
    setRunningId(experimentId);
    try {
      const result = await api.post(`/backtests/run/${experimentId}`, {});
      message.success(`回测完成，数据质量: ${(result as { data_quality_level: string }).data_quality_level}`);
      navigate(`/backtests`);
    } catch {
      message.error('回测失败');
    } finally {
      setRunningId(null);
    }
  };

  const columns: ColumnsType<PortfolioExperiment> = [
    { title: '实验名称', dataIndex: 'experiment_name', key: 'experiment_name' },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 140,
      render: (role: string) => {
        const colors: Record<string, string> = { main: 'blue', benchmark: 'orange', variant: 'default' };
        const labels: Record<string, string> = { main: '主实验', benchmark: '基准', variant: '变体' };
        return <Tag color={colors[role] || 'default'}>{labels[role] || role}</Tag>;
      },
    },
    {
      title: '再平衡规则',
      dataIndex: 'rebalance_rule',
      key: 'rebalance_rule',
      width: 160,
      render: (rule: string) => REBALANCE_RULES.find((r) => r.value === rule)?.label || rule,
    },
    { title: '回测区间', key: 'date_range', width: 220,
      render: (_, r) => `${r.start_date || '—'} 至 ${r.end_date || '—'}`,
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            loading={runningId === record.experiment_id}
            onClick={() => handleRunBacktest(record.experiment_id)}
          >
            运行回测
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          创建实验
        </Button>
      </Space>
      <Table
        columns={columns}
        dataSource={experiments}
        rowKey="experiment_id"
        loading={loading}
        size="middle"
      />
      <Modal
        title="创建实验"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        okText="创建"
        cancelText="取消"
        width={640}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="experiment_name" label="实验名称" rules={[{ required: true }]}>
            <Input placeholder="如 75/15/10 月度再平衡" />
          </Form.Item>
          <Form.Item name="role" label="实验角色" initialValue="main">
            <Select options={ROLES} />
          </Form.Item>
          <Form.Item name="rebalance_rule" label="再平衡规则" initialValue="monthly">
            <Select options={REBALANCE_RULES} />
          </Form.Item>
          <Space>
            <Form.Item name="start_date" label="开始日期">
              <Input placeholder="YYYY-MM-DD" />
            </Form.Item>
            <Form.Item name="end_date" label="结束日期">
              <Input placeholder="YYYY-MM-DD" />
            </Form.Item>
          </Space>
          <Card title="基金配置" size="small" style={{ marginBottom: 16 }}>
            <Form.List name="positions">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...rest }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item {...rest} name={[name, 'fund_code']} rules={[{ required: true }]}>
                        <Select placeholder="选择基金" style={{ width: 180 }}>
                          {funds.map((f) => (
                            <Select.Option key={f.fund_code} value={f.fund_code}>
                              {f.fund_code} {f.fund_name}
                            </Select.Option>
                          ))}
                        </Select>
                      </Form.Item>
                      <Form.Item {...rest} name={[name, 'target_weight']} rules={[{ required: true }]}>
                        <InputNumber placeholder="权重%" min={0} max={100} style={{ width: 100 }} />
                      </Form.Item>
                      <Button type="link" danger onClick={() => remove(name)}>删除</Button>
                    </Space>
                  ))}
                  <Button type="dashed" onClick={() => add()} block>
                    添加基金
                  </Button>
                </>
              )}
            </Form.List>
          </Card>
          <Form.Item name="note" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
