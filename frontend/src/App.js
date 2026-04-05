/**
 * 血浆游离血红蛋白检测系统 - 主应用组件
 * 作者: 哈雷酱大小姐 (￣▽￣)／
 */

import React, { useState, useEffect } from 'react';
import { Layout, Tabs, message, Spin } from 'antd';
import {
  ExperimentOutlined,
  HistoryOutlined,
  DashboardOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import './App.css';
import DetectionPanel from './components/DetectionPanel';
import SimulatorPanel from './components/SimulatorPanel';
import HistoryPanel from './components/HistoryPanel';
import StatisticsPanel from './components/StatisticsPanel';
import { healthCheck } from './services/api';

const { Header, Content, Footer } = Layout;

function App() {
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState({
    status: 'unknown',
    models_loaded: false,
    simulator_connected: false,
  });
  const [activeTab, setActiveTab] = useState('detection');

  // 检查系统状态
  useEffect(() => {
    checkSystemHealth();
    const interval = setInterval(checkSystemHealth, 30000); // 每30秒检查一次
    return () => clearInterval(interval);
  }, []);

  const checkSystemHealth = async () => {
    try {
      const health = await healthCheck();
      setSystemStatus(health);
      setLoading(false);
    } catch (error) {
      console.error('健康检查失败:', error);
      setSystemStatus({
        status: 'error',
        models_loaded: false,
        simulator_connected: false,
      });
      setLoading(false);
      message.error('无法连接到后端服务！');
    }
  };

  const tabItems = [
    {
      key: 'detection',
      label: (
        <span>
          <ExperimentOutlined />
          检测面板
        </span>
      ),
      children: <DetectionPanel systemStatus={systemStatus} />,
    },
    {
      key: 'simulator',
      label: (
        <span>
          <DashboardOutlined />
          数据模拟器
        </span>
      ),
      children: <SimulatorPanel systemStatus={systemStatus} />,
    },
    {
      key: 'history',
      label: (
        <span>
          <HistoryOutlined />
          历史记录
        </span>
      ),
      children: <HistoryPanel />,
    },
    {
      key: 'statistics',
      label: (
        <span>
          <SettingOutlined />
          统计分析
        </span>
      ),
      children: <StatisticsPanel />,
    },
  ];

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column'
      }}>
        <Spin size="large" />
        <p style={{ marginTop: 20, color: '#666' }}>
          系统启动中... (￣▽￣)／
        </p>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          color: 'white',
          fontSize: '20px',
          fontWeight: 'bold',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <ExperimentOutlined style={{ fontSize: '28px' }} />
          <span>血浆游离血红蛋白检测系统</span>
        </div>
        <div style={{ marginLeft: 'auto', color: 'white', fontSize: '14px' }}>
          状态: {systemStatus.status === 'healthy' ? '✓ 正常运行' : '⚠ 异常'}
        </div>
      </Header>

      <Content style={{ padding: '24px', background: '#f0f2f5' }}>
        <div style={{
          background: 'white',
          borderRadius: '8px',
          padding: '24px',
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
          minHeight: 'calc(100vh - 200px)'
        }}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            size="large"
          />
        </div>
      </Content>

      <Footer style={{
        textAlign: 'center',
        background: '#f0f2f5',
        color: '#666'
      }}>
        血浆游离血红蛋白检测系统 ©2026 | 作者: 哈雷酱大小姐 (￣▽￣)／
        {' '}| Powered by FastAPI + React + Machine Learning
      </Footer>
    </Layout>
  );
}

export default App;
