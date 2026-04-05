/**
 * 历史记录组件
 * 作者: 哈雷酱大小姐 (￣▽￣)／
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  message,
  Modal,
  Popconfirm,
} from 'antd';
import {
  DeleteOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { getHistory, clearHistory } from '../services/api';

const HistoryPanel = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // 加载历史记录
  const loadHistory = async () => {
    setLoading(true);
    try {
      const response = await getHistory(100);
      setData(response.records || []);
    } catch (error) {
      console.error('加载历史记录失败:', error);
      message.error('加载失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  // 清除历史
  const handleClearHistory = async () => {
    try {
      await clearHistory();
      setData([]);
      message.success('历史记录已清除');
    } catch (error) {
      console.error('清除失败:', error);
      message.error('清除失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 查看详情
  const viewDetail = (record) => {
    setSelectedRecord(record);
    setDetailModalVisible(true);
  };

  // 表格列
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 180,
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '样本编号',
      key: 'sample_id',
      width: 150,
      render: (_, record) => record.sample_info?.sample_id || '-',
    },
    {
      title: '预测浓度 (g/L)',
      key: 'concentration',
      width: 130,
      render: (_, record) => (
        <span style={{
          fontWeight: 'bold',
          color: record.prediction?.concentration > 0 ? '#3f8600' : '#999',
        }}>
          {record.prediction?.concentration?.toFixed(4) || '-'}
        </span>
      ),
    },
    {
      title: '模型',
      key: 'model_type',
      width: 100,
      render: (_, record) => {
        const type = record.prediction?.model_type;
        return (
          <Tag color={type === 'rf' ? 'blue' : 'green'}>
            {type === 'rf' ? 'RF' : 'SVR'}
          </Tag>
        );
      },
    },
    {
      title: '置信度',
      key: 'confidence',
      width: 120,
      render: (_, record) => {
        const conf = record.prediction?.confidence;
        return conf ? `${(conf * 100).toFixed(2)}%` : '-';
      },
    },
    {
      title: '预测时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text) => text?.split('T')[1]?.split('.')[0] || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => viewDetail(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="📜 预测历史记录"
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadHistory}
              loading={loading}
            >
              刷新
            </Button>
            <Popconfirm
              title="确定要清除所有历史记录吗？"
              onConfirm={handleClearHistory}
              okText="确定"
              cancelText="取消"
            >
              <Button
                danger
                icon={<DeleteOutlined />}
                disabled={data.length === 0}
              >
                清除记录
              </Button>
            </Popconfirm>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 详情模态框 */}
      <Modal
        title="预测详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedRecord && (
          <div>
            <p><strong>记录ID:</strong> {selectedRecord.id}</p>
            <p><strong>样本编号:</strong> {selectedRecord.sample_info?.sample_id || '-'}</p>
            <p><strong>样本类型:</strong> {selectedRecord.sample_info?.sample_type || '-'}</p>

            <p><strong>吸光度数据:</strong></p>
            <ul>
              <li>375nm: {selectedRecord.absorbance?.a375}</li>
              <li>405nm: {selectedRecord.absorbance?.a405}</li>
              <li>450nm: {selectedRecord.absorbance?.a450}</li>
            </ul>

            <p><strong>预测结果:</strong></p>
            <ul>
              <li>浓度: {selectedRecord.prediction?.concentration} g/L</li>
              <li>置信度: {selectedRecord.prediction?.confidence}</li>
              <li>模型: {selectedRecord.prediction?.model_type}</li>
            </ul>

            <p><strong>预测时间:</strong> {selectedRecord.created_at}</p>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default HistoryPanel;
