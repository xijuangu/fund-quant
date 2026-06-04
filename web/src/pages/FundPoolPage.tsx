import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, Tag, Space, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../api/client';
import type { FundBasic } from '../api/types';

const ASSET_BUCKETS = [
  'A股宽基权益',
  'A股行业/主题权益',
  '主动权益',
  '海外/QDII权益',
  '债券',
  '黄金/商品',
  '货币/现金替代',
];

export default function FundPoolPage() {
  const [funds, setFunds] = useState<FundBasic[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

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

  useEffect(() => {
    fetchFunds();
  }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/funds', values as Record<string, unknown>);
      message.success('基金已添加');
      setModalOpen(false);
      form.resetFields();
      fetchFunds();
    } catch {
      // form validation error or API error
    }
  };

  const columns: ColumnsType<FundBasic> = [
    { title: '基金代码', dataIndex: 'fund_code', key: 'fund_code', width: 120 },
    { title: '基金名称', dataIndex: 'fund_name', key: 'fund_name' },
    { title: '基金类型', dataIndex: 'fund_type', key: 'fund_type', width: 100 },
    {
      title: '资产桶',
      dataIndex: 'asset_bucket',
      key: 'asset_bucket',
      width: 140,
      render: (bucket: string) => {
        const colors: Record<string, string> = {
          'A股宽基权益': 'blue',
          'A股行业/主题权益': 'geekblue',
          '主动权益': 'purple',
          '海外/QDII权益': 'cyan',
          '债券': 'green',
          '黄金/商品': 'gold',
          '货币/现金替代': 'default',
        };
        return bucket ? <Tag color={colors[bucket] || 'default'}>{bucket}</Tag> : '-';
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? '启用' : '停用'}</Tag>,
    },
    { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true },
  ];

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          添加基金
        </Button>
      </Space>
      <Table
        columns={columns}
        dataSource={funds}
        rowKey="fund_code"
        loading={loading}
        size="middle"
      />
      <Modal
        title="添加基金"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        okText="添加"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="fund_code" label="基金代码" rules={[{ required: true, message: '请输入基金代码' }]}>
            <Input placeholder="如 000001" />
          </Form.Item>
          <Form.Item name="fund_name" label="基金名称" rules={[{ required: true, message: '请输入基金名称' }]}>
            <Input placeholder="如 华夏成长混合" />
          </Form.Item>
          <Form.Item name="fund_type" label="基金类型">
            <Input placeholder="如 混合型" />
          </Form.Item>
          <Form.Item name="asset_bucket" label="资产桶">
            <Select placeholder="选择资产桶" allowClear>
              {ASSET_BUCKETS.map((b) => (
                <Select.Option key={b} value={b}>{b}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="fund_company" label="基金公司">
            <Input placeholder="如 华夏基金" />
          </Form.Item>
          <Form.Item name="inception_date" label="成立日期">
            <Input placeholder="YYYY-MM-DD" />
          </Form.Item>
          <Form.Item name="note" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
