import { useEffect, useMemo, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Tag, Space, message,
  Typography, Tooltip, Badge, Switch, Popconfirm, Input as SearchInput,
} from 'antd';
import {
  PlusOutlined, SearchOutlined, ReloadOutlined,
  ClearOutlined, EditOutlined, DeleteOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../api/client';
import type { FundBasic } from '../api/types';
import { BUCKET_KEYS, BUCKET_LABELS, BUCKET_COLORS, BUCKET_ORDER } from '../api/types';

const { Text } = Typography;

export default function FundPoolPage() {
  const [funds, setFunds] = useState<FundBasic[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingFund, setEditingFund] = useState<FundBasic | null>(null);
  const [form] = Form.useForm();
  const [searchText, setSearchText] = useState('');
  const [bucketFilter, setBucketFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<boolean | null>(null);

  const fetchFunds = async () => {
    setLoading(true);
    try {
      const data = await api.get<FundBasic[]>('/funds');
      setFunds(data);
    } catch {
      message.error('获取基金列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchFunds(); }, []);

  const openCreate = () => { setEditingFund(null); form.resetFields(); setModalOpen(true); };
  const openEdit = (f: FundBasic) => { setEditingFund(f); form.setFieldsValue(f); setModalOpen(true); };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingFund) {
        await api.put(`/funds/${editingFund.fund_code}`, values as Record<string, unknown>);
        message.success('基金已更新');
      } else {
        await api.post('/funds', values as Record<string, unknown>);
        message.success('基金已添加');
      }
      setModalOpen(false);
      form.resetFields();
      setEditingFund(null);
      fetchFunds();
    } catch { /* validation / API */ }
  };

  const handleDelete = async (fundCode: string) => {
    try {
      await api.del(`/funds/${fundCode}`);
      message.success('基金已删除');
      fetchFunds();
    } catch {
      message.error('删除失败');
    }
  };

  const handleToggleActive = async (f: FundBasic) => {
    try {
      await api.put(`/funds/${f.fund_code}`, { is_active: !f.is_active });
      fetchFunds();
    } catch { message.error('更新失败'); }
  };

  const clearFilters = () => { setSearchText(''); setBucketFilter(null); setStatusFilter(null); };

  const filtered = useMemo(() => {
    let list = funds;
    if (searchText) {
      const s = searchText.toLowerCase();
      list = list.filter((f) =>
        f.fund_code.toLowerCase().includes(s) || f.fund_name.toLowerCase().includes(s) || f.fund_company.toLowerCase().includes(s));
    }
    if (bucketFilter) { list = list.filter((f) => f.asset_bucket === bucketFilter); }
    if (statusFilter !== null) { list = list.filter((f) => f.is_active === statusFilter); }
    return list.sort((a, b) => (BUCKET_ORDER[a.asset_bucket] ?? 99) - (BUCKET_ORDER[b.asset_bucket] ?? 99) || a.fund_code.localeCompare(b.fund_code));
  }, [funds, searchText, bucketFilter, statusFilter]);

  const hasFilters = searchText || bucketFilter || statusFilter !== null;

  const columns: ColumnsType<FundBasic> = [
    { title: '基金代码', dataIndex: 'fund_code', key: 'fund_code', width: 110, sorter: (a, b) => a.fund_code.localeCompare(b.fund_code), render: (v: string) => <Text code>{v}</Text> },
    { title: '基金名称', dataIndex: 'fund_name', key: 'fund_name', sorter: (a, b) => a.fund_name.localeCompare(b.fund_name), render: (v: string, r) => (<Space direction="vertical" size={0}><Text strong>{v}</Text><Text type="secondary" style={{ fontSize: 12 }}>{r.fund_company}</Text></Space>) },
    { title: '资产桶', dataIndex: 'asset_bucket', key: 'asset_bucket', width: 140, sorter: (a, b) => (BUCKET_ORDER[a.asset_bucket] ?? 99) - (BUCKET_ORDER[b.asset_bucket] ?? 99), render: (bucket: string) => (bucket && BUCKET_LABELS[bucket] ? <Tag color={BUCKET_COLORS[bucket]} style={{ margin: 0 }}>{BUCKET_LABELS[bucket]}</Tag> : <Tag style={{ margin: 0 }}>{bucket || '未分类'}</Tag>) },
    { title: '类型', dataIndex: 'fund_type', key: 'fund_type', width: 90, responsive: ['md'], render: (v: string) => v || '-' },
    { title: '成立日期', dataIndex: 'inception_date', key: 'inception_date', width: 110, responsive: ['lg'], sorter: (a, b) => (a.inception_date || '').localeCompare(b.inception_date || ''), render: (v: string | null) => v || '-' },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 70, render: (v: boolean, r) => <Switch size="small" checked={v} onChange={() => handleToggleActive(r)} /> },
    { title: '备注', dataIndex: 'note', key: 'note', width: 140, ellipsis: true, responsive: ['lg'], render: (v: string) => v ? <Text type="secondary">{v}</Text> : '-' },
    { title: '操作', key: 'actions', width: 120, render: (_, r) => (<Space size={0}><Tooltip title="编辑"><Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} /></Tooltip><Popconfirm title="确认删除？" onConfirm={() => handleDelete(r.fund_code)} okText="删除" cancelText="取消"><Button type="link" danger size="small" icon={<DeleteOutlined />} /></Popconfirm></Space>) },
  ];

  return (
    <>
      <div className="page-header">
        <h2>基金池</h2>
        <Space>
          <Tooltip title="刷新"><Button icon={<ReloadOutlined />} onClick={fetchFunds} /></Tooltip>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>添加基金</Button>
        </Space>
      </div>

      <div className="table-toolbar">
        <Space wrap>
          <SearchInput placeholder="搜索代码 / 名称 / 公司" prefix={<SearchOutlined />} value={searchText} onChange={(e) => setSearchText(e.target.value)} style={{ width: 260 }} allowClear />
          <Select placeholder="资产桶筛选" value={bucketFilter} onChange={setBucketFilter} allowClear style={{ width: 170 }} options={BUCKET_KEYS.map((key) => ({ label: BUCKET_LABELS[key], value: key }))} />
          <Select placeholder="状态筛选" value={statusFilter} onChange={setStatusFilter} allowClear style={{ width: 120 }} options={[{ label: '启用', value: true }, { label: '停用', value: false }]} />
          {hasFilters && <Button icon={<ClearOutlined />} onClick={clearFilters} size="small">清除</Button>}
        </Space>
        <Text type="secondary" style={{ fontSize: 13 }}>共 {filtered.length} 只基金</Text>
      </div>

      <Table columns={columns} dataSource={filtered} rowKey="fund_code" loading={loading} size="middle" pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `共 ${t} 只` }} locale={{ emptyText: '暂无基金，点击"添加基金"开始' }} />

      <Modal title={editingFund ? '编辑基金' : '添加基金'} open={modalOpen} onOk={handleSubmit} onCancel={() => { setModalOpen(false); form.resetFields(); setEditingFund(null); }} okText={editingFund ? '保存' : '添加'} cancelText="取消">
        <Form form={form} layout="vertical">
          <Form.Item name="fund_code" label="基金代码" rules={[{ required: true }]}>
            <Input placeholder="如 000001" disabled={!!editingFund} />
          </Form.Item>
          <Form.Item name="fund_name" label="基金名称" rules={[{ required: true }]}>
            <Input placeholder="如 华夏成长混合" />
          </Form.Item>
          <Form.Item name="asset_bucket" label="资产桶">
            <Select placeholder="选择资产桶" allowClear options={BUCKET_KEYS.map((key) => ({ label: BUCKET_LABELS[key], value: key }))} />
          </Form.Item>
          <Form.Item name="fund_type" label="基金类型"><Input placeholder="如 混合型" /></Form.Item>
          <Form.Item name="fund_company" label="基金公司"><Input placeholder="如 华夏基金" /></Form.Item>
          <Form.Item name="inception_date" label="成立日期"><Input placeholder="YYYY-MM-DD" /></Form.Item>
          <Form.Item name="note" label="备注"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
