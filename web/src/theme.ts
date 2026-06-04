import type { ThemeConfig } from 'antd';

const theme: ThemeConfig = {
  token: {
    colorPrimary: '#1677ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1677ff',
    borderRadius: 6,
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'Noto Sans SC', sans-serif",
    fontSize: 14,
    colorBgContainer: '#ffffff',
    colorBgLayout: '#f5f5f5',
  },
  components: {
    Layout: {
      headerBg: '#ffffff',
      siderBg: '#001529',
      bodyBg: '#f0f2f5',
    },
    Menu: {
      darkItemBg: '#001529',
      darkItemSelectedBg: '#1677ff',
      darkItemHoverBg: '#0a2540',
      itemBorderRadius: 6,
    },
    Table: {
      headerBg: '#fafafa',
      headerColor: '#262626',
      rowHoverBg: '#e6f4ff',
      borderColor: '#f0f0f0',
    },
    Card: {
      paddingLG: 24,
    },
    Button: {
      primaryShadow: '0 2px 0 rgba(22, 119, 255, 0.1)',
    },
    Tag: {
      borderRadiusSM: 4,
    },
  },
};

export default theme;
