import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography } from 'antd';
import {
  ExperimentOutlined,
  FundOutlined,
  DashboardOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import FundPoolPage from './pages/FundPoolPage';
import ExperimentGroupsPage from './pages/ExperimentGroupsPage';
import ExperimentDetailPage from './pages/ExperimentDetailPage';
import BacktestDashboardPage from './pages/BacktestDashboardPage';
import StressPeriodsPage from './pages/StressPeriodsPage';
import { useState } from 'react';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

const menuItems = [
  { key: '/funds', icon: <FundOutlined />, label: <Link to="/funds">基金池</Link> },
  { key: '/experiments', icon: <ExperimentOutlined />, label: <Link to="/experiments">实验组</Link> },
  { key: '/backtests', icon: <DashboardOutlined />, label: <Link to="/backtests">回测看板</Link> },
  { key: '/stress-periods', icon: <ThunderboltOutlined />, label: <Link to="/stress-periods">压力区间</Link> },
];

export default function App() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const selectedKey = menuItems.find((item) => location.pathname.startsWith(item.key))?.key || '/funds';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Title level={5} style={{ color: '#fff', margin: 0 }}>
            {collapsed ? 'FQ' : '基金组合实验室'}
          </Title>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0' }}>
          <Title level={4} style={{ margin: '16px 0' }}>
            {menuItems.find((item) => item.key === selectedKey)?.label?.props?.children || '基金组合实验室'}
          </Title>
        </Header>
        <Content style={{ margin: 24 }}>
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
