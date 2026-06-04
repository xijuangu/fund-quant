import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, Space, Typography } from 'antd';
import {
  ExperimentOutlined,
  FundOutlined,
  DashboardOutlined,
  ThunderboltOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons';
import FundPoolPage from './pages/FundPoolPage';
import ExperimentGroupsPage from './pages/ExperimentGroupsPage';
import ExperimentDetailPage from './pages/ExperimentDetailPage';
import BacktestDashboardPage from './pages/BacktestDashboardPage';
import StressPeriodsPage from './pages/StressPeriodsPage';
import { useState } from 'react';

const { Header, Sider, Content } = Layout;
const { Text, Title } = Typography;

const menuItems = [
  { key: '/funds', icon: <FundOutlined />, label: <Link to="/funds">基金池</Link>, title: '基金池' },
  { key: '/experiments', icon: <ExperimentOutlined />, label: <Link to="/experiments">实验组</Link>, title: '实验组' },
  { key: '/backtests', icon: <DashboardOutlined />, label: <Link to="/backtests">回测看板</Link>, title: '回测看板' },
  { key: '/stress-periods', icon: <ThunderboltOutlined />, label: <Link to="/stress-periods">压力区间</Link>, title: '压力区间' },
];

export default function App() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const activeItem = menuItems.find((item) => location.pathname.startsWith(item.key)) || menuItems[0];

  return (
    <Layout className="app-shell">
      <Sider className="app-sider" width={228} collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div className="brand-block">
          <div className="brand-mark">FQ</div>
          {!collapsed && (
            <div className="brand-copy">
              <Title level={5}>基金组合实验室</Title>
              <Text>Fund Portfolio Lab</Text>
            </div>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[activeItem.key]}
          items={menuItems.map(({ title: _title, ...item }) => item)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <div>
            <Title level={4}>Fund Quant Research Desk</Title>
            <Text type="secondary">当前模块：{activeItem.title} · 净值口径 / 回测参数 / 数据质量可追溯</Text>
          </div>
          <Space className="header-status">
            <SafetyCertificateOutlined />
            <Text>研究模式</Text>
          </Space>
        </Header>
        <Content className="app-content">
          <Routes>
            <Route path="/" element={<FundPoolPage />} />
            <Route path="/funds" element={<FundPoolPage />} />
            <Route path="/experiments" element={<ExperimentGroupsPage />} />
            <Route path="/experiments/:groupId" element={<ExperimentDetailPage />} />
            <Route path="/backtests" element={<BacktestDashboardPage />} />
            <Route path="/stress-periods" element={<StressPeriodsPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}
