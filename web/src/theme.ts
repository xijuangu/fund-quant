import type { ThemeConfig } from 'antd';

const theme: ThemeConfig = {
  token: {
    colorPrimary: '#2563eb',
    colorSuccess: '#0f9f6e',
    colorWarning: '#d9981e',
    colorError: '#dc2626',
    colorInfo: '#0f766e',
    borderRadius: 6,
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'Noto Sans SC', sans-serif",
    fontSize: 13,
    colorBgContainer: '#ffffff',
    colorBgLayout: '#eef2f7',
    colorText: '#162033',
    colorTextSecondary: '#64748b',
    colorBorder: '#d8e0ec',
  },
  components: {
    Layout: {
      headerBg: '#ffffff',
      siderBg: '#07111f',
      bodyBg: '#eef2f7',
    },
    Menu: {
      darkItemBg: '#07111f',
      darkItemSelectedBg: '#14345f',
      darkItemHoverBg: '#101d2e',
      itemBorderRadius: 6,
    },
    Table: {
      headerBg: '#f6f8fb',
      headerColor: '#334155',
      rowHoverBg: '#eef6ff',
      borderColor: '#e2e8f0',
      cellPaddingBlock: 10,
      cellPaddingInline: 12,
    },
    Card: {
      paddingLG: 20,
    },
    Button: {
      primaryShadow: '0 4px 12px rgba(37, 99, 235, 0.18)',
    },
    Tag: {
      borderRadiusSM: 4,
    },
  },
};

export default theme;
