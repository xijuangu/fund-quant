import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, DatePicker, Space, message, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import api from '../api/client';
import type { StressPeriod } from '../api/types';

export default function StressPeriodsPage() {
  const [periods, setPeriods] = useState<StressPeriod[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
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

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/stress-periods', {
        period_name: values.period_name,
        start_date: values.date_range[0].format('YYYY-MM-DD'),
        end_date: values.date_range[1].format('YYYY-MM-DD'),
        description: values.description || '',
      });
      message.success('压力区间已创建');
      setModalOpen(false);
      form.resetFields();
      fetchPeriods();
    } catch { /* handled */ }
  };

  const columns: ColumnsType<StressPeriod> = [
    { title: '名称', dataIndex: 'period_name', key: 'period_name' },
    { title: '开始日期', dataIndex: 'start_date', key: 'start_date', width: 120 },
    { title: '结束日期', dataIndex: 'end_date', key: 'end_date', width: 120 },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '停用'}</Tag>,
    },
  ];

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          添加压力区间
        </Button>
      </Space>
      <Table
        columns={columns}
        dataSource={periods}
        rowKey="period_id"
        loading={loading}
        size="middle"
      />
      <Modal
        title="添加压力区间"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        okText="添加"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="period_name" label="区间名称" rules={[{ required: true }]}>
            <Input placeholder="如 2018年A股熊市" />
          </Form.Item>
          <Form.Item name="date_range" label="日期范围" rules={[{ required: true }]}>
            <DatePicker.RangePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="区间说明">
            <Input.TextArea rows={3} placeholder="描述该压力区间的市场背景" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
