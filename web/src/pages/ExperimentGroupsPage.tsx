import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Button, Modal, Form, Input, Space, message, Typography, Tooltip, Popconfirm } from 'antd';
import { PlusOutlined, ExperimentOutlined, ReloadOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../api/client';
import type { ExperimentGroup } from '../api/types';

const { Text } = Typography;

export default function ExperimentGroupsPage() {
  const [groups, setGroups] = useState<ExperimentGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<ExperimentGroup | null>(null);
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

  const openCreate = () => { setEditingGroup(null); form.resetFields(); setModalOpen(true); };
  const openEdit = (g: ExperimentGroup) => { setEditingGroup(g); form.setFieldsValue(g); setModalOpen(true); };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingGroup) {
        await api.put(`/experiment-groups/${editingGroup.experiment_group_id}`, values as Record<string, unknown>);
        message.success('实验组已更新');
      } else {
        await api.post('/experiment-groups', values as Record<string, unknown>);
        message.success('实验组已创建');
      }
      setModalOpen(false);
      form.resetFields();
      setEditingGroup(null);
      fetchGroups();
    } catch { /* handled */ }
  };

  const handleDelete = async (groupId: string) => {
    try {
      await api.del(`/experiment-groups/${groupId}`);
      message.success('实验组已删除');
      fetchGroups();
    } catch {
      message.error('删除失败');
    }
  };

  const columns: ColumnsType<ExperimentGroup> = [
    { title: '实验组名称', dataIndex: 'group_name', key: 'group_name', sorter: (a, b) => a.group_name.localeCompare(b.group_name), render: (v: string) => <Text strong>{v}</Text> },
    { title: '研究问题', dataIndex: 'research_question', key: 'research_question', ellipsis: true, render: (v: string) => v ? <Text type="secondary">{v}</Text> : <Text type="secondary" italic>未设置</Text> },
    { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true, width: 200, render: (v: string) => v || '-' },
    { title: '操作', key: 'actions', width: 200, render: (_, r) => (<Space size={0}><Button type="primary" size="small" icon={<ExperimentOutlined />} onClick={() => navigate(`/experiments/${r.experiment_group_id}`)}>实验列表</Button><Tooltip title="编辑"><Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} /></Tooltip><Popconfirm title="确认删除？该操作会删除组内所有实验！" onConfirm={() => handleDelete(r.experiment_group_id)} okText="删除" cancelText="取消"><Button type="link" danger size="small" icon={<DeleteOutlined />} /></Popconfirm></Space>) },
  ];

  return (
    <>
      <div className="page-header">
        <h2>实验组</h2>
        <Space>
          <Tooltip title="刷新"><Button icon={<ReloadOutlined />} onClick={fetchGroups} /></Tooltip>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>创建实验组</Button>
        </Space>
      </div>

      <Table columns={columns} dataSource={groups} rowKey="experiment_group_id" loading={loading} size="middle" pagination={false} locale={{ emptyText: '暂无实验组，点击"创建实验组"开始' }} />

      <Modal title={editingGroup ? '编辑实验组' : '创建实验组'} open={modalOpen} onOk={handleSubmit} onCancel={() => { setModalOpen(false); form.resetFields(); setEditingGroup(null); }} okText={editingGroup ? '保存' : '创建'} cancelText="取消" width={520}>
        <Form form={form} layout="vertical">
          <Form.Item name="group_name" label="实验组名称" rules={[{ required: true }]}>
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
