import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Button, Modal, Form, Input, Space, message } from 'antd';
import { PlusOutlined, ExperimentOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../api/client';
import type { ExperimentGroup } from '../api/types';

export default function ExperimentGroupsPage() {
  const [groups, setGroups] = useState<ExperimentGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const data = await api.get<ExperimentGroup[]>('/experiment-groups');
      setGroups(data);
    } catch {
      message.error('获取实验组列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchGroups(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/experiment-groups', values as Record<string, unknown>);
      message.success('实验组已创建');
      setModalOpen(false);
      form.resetFields();
      fetchGroups();
    } catch { /* handled */ }
  };

  const columns: ColumnsType<ExperimentGroup> = [
    { title: '实验组名称', dataIndex: 'group_name', key: 'group_name' },
    { title: '研究问题', dataIndex: 'research_question', key: 'research_question', ellipsis: true },
    { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Button
          type="link"
          icon={<ExperimentOutlined />}
          onClick={() => navigate(`/experiments/${record.experiment_group_id}`)}
        >
          查看实验
        </Button>
      ),
    },
  ];

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          创建实验组
        </Button>
      </Space>
      <Table
        columns={columns}
        dataSource={groups}
        rowKey="experiment_group_id"
        loading={loading}
        size="middle"
      />
      <Modal
        title="创建实验组"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="group_name" label="实验组名称" rules={[{ required: true, message: '请输入实验组名称' }]}>
            <Input placeholder="如 进取型75/15/10防守资产测试" />
          </Form.Item>
          <Form.Item name="research_question" label="研究问题">
            <Input.TextArea rows={3} placeholder="本次实验组要回答的研究问题" />
          </Form.Item>
          <Form.Item name="note" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
