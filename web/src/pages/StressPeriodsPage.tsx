import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, DatePicker, Space, message, Tag, Typography, Tooltip, Popconfirm,
} from 'antd';
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import api from '../api/client';
import type { StressPeriod } from '../api/types';
import { KpiCard, PageHeader, StatGrid } from '../components/workspace';

const { Text } = Typography;

export default function StressPeriodsPage() {
  const [periods, setPeriods] = useState<StressPeriod[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPeriod, setEditingPeriod] = useState<StressPeriod | null>(null);
  const [form] = Form.useForm();

  const fetchPeriods = async () => {
    setLoading(true);
    try {
      const data = await api.get<StressPeriod[]>('/stress-periods');
      setPeriods(data);
    } catch {
      message.error('获取压力区间列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPeriods(); }, []);

  const openCreate = () => { setEditingPeriod(null); form.resetFields(); setModalOpen(true); };

  const openEdit = (p: StressPeriod) => {
    setEditingPeriod(p);
    form.setFieldsValue({
      period_name: p.period_name,
      date_range: [dayjs(p.start_date), dayjs(p.end_date)],
      description: p.description,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const body = {
        period_name: values.period_name,
        start_date: values.date_range[0].format('YYYY-MM-DD'),
        end_date: values.date_range[1].format('YYYY-MM-DD'),
        description: values.description || '',
      };
      if (editingPeriod) {
        await api.put(`/stress-periods/${editingPeriod.period_id}`, body as Record<string, unknown>);
        message.success('压力区间已更新');
      } else {
        await api.post('/stress-periods', body as Record<string, unknown>);
        message.success('压力区间已创建');
      }
      setModalOpen(false);
      form.resetFields();
      setEditingPeriod(null);
      fetchPeriods();
    } catch { /* handled */ }
  };

  const handleDelete = async (periodId: string) => {
    try { await api.del(`/stress-periods/${periodId}`); message.success('已删除'); fetchPeriods(); } catch { message.error('删除失败'); }
  };

  const activeCount = periods.filter((p) => p.is_active).length;
  const longestPeriod = periods.reduce((max, period) => {
    const days = dayjs(period.end_date).diff(dayjs(period.start_date), 'day') + 1;
    return days > max ? days : max;
  }, 0);

  const columns: ColumnsType<StressPeriod> = [
    { title: '名称', dataIndex: 'period_name', key: 'period_name', sorter: (a, b) => a.period_name.localeCompare(b.period_name), render: (v: string) => <Text strong>{v}</Text> },
    { title: '日期范围', key: 'date_range', width: 220, sorter: (a, b) => a.start_date.localeCompare(b.start_date), render: (_, r) => (<Space size={4}><Text code>{r.start_date}</Text><Text type="secondary">～</Text><Text code>{r.end_date}</Text></Space>) },
    { title: '持续天数', key: 'duration', width: 90, sorter: (a, b) => dayjs(a.end_date).diff(dayjs(a.start_date), 'day') - dayjs(b.end_date).diff(dayjs(b.start_date), 'day'), render: (_, r) => `${dayjs(r.end_date).diff(dayjs(r.start_date), 'day') + 1} 天` },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true, render: (v: string) => v ? <Text type="secondary">{v}</Text> : '-' },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 70, render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '停用'}</Tag> },
    { title: '操作', key: 'actions', width: 120, render: (_, r) => (<Space size={0}><Tooltip title="编辑"><Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} /></Tooltip><Popconfirm title="确认删除？" onConfirm={() => handleDelete(r.period_id)} okText="删除" cancelText="取消"><Button type="link" danger size="small" icon={<DeleteOutlined />} /></Popconfirm></Space>) },
  ];

  return (
    <>
      <PageHeader
        title="压力区间"
        description="维护可复用的市场压力阶段，用于观察债券、黄金和权益资产在极端环境下的贡献。"
        actions={
          <>
            <Tooltip title="刷新"><Button icon={<ReloadOutlined />} onClick={fetchPeriods} /></Tooltip>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>添加压力区间</Button>
          </>
        }
      />

      <StatGrid>
        <KpiCard label="区间数量" value={periods.length} sub="个压力样本" tone="blue" />
        <KpiCard label="启用区间" value={activeCount} sub="参与报告诊断" tone="green" />
        <KpiCard label="最长区间" value={`${longestPeriod} 天`} sub="样本跨度" tone="gold" />
      </StatGrid>

      <Table columns={columns} dataSource={periods} rowKey="period_id" loading={loading} size="middle" pagination={false} locale={{ emptyText: '暂无压力区间' }} />

      <Modal title={editingPeriod ? '编辑压力区间' : '添加压力区间'} open={modalOpen} onOk={handleSubmit} onCancel={() => { setModalOpen(false); form.resetFields(); setEditingPeriod(null); }} okText={editingPeriod ? '保存' : '添加'} cancelText="取消">
        <Form form={form} layout="vertical">
          <Form.Item name="period_name" label="区间名称" rules={[{ required: true }]}><Input placeholder="如 2018年A股熊市" /></Form.Item>
          <Form.Item name="date_range" label="日期范围" rules={[{ required: true }]}><DatePicker.RangePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="description" label="区间说明"><Input.TextArea rows={3} placeholder="描述该压力区间的市场背景" /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
