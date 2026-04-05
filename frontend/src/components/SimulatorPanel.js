/**
 * 数据模拟器组件
 * 作者: 哈雷酱大小姐 (￣▽￣)／
 */

import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Form,
  InputNumber,
  Button,
  Table,
  Slider,
  Space,
  Alert,
  Statistic,
  message,
  Tag,
} from 'antd';
import {
  ExperimentOutlined,
  DownloadOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { simulateMeasurement, batchSimulate, generateDataset } from '../services/api';

const SimulatorPanel = ({ systemStatus }) => {
  const [singleForm] = Form.useForm();
  const [batchForm] = Form.useForm();
  const [singleResult, setSingleResult] = useState(null);
  const [batchResults, setBatchResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // 单次模拟
  const handleSingleSimulate = async (values) => {
    if (!systemStatus.simulator_connected) {
      message.error('模拟器未连接！');
      return;
    }

    setLoading(true);
    try {
      const response = await simulateMeasurement({
        concentration: values.concentration,
        noise_level: values.noise_level,
      });
      setSingleResult(response);
      message.success('模拟测量完成！');
    } catch (error) {
      console.error('模拟失败:', error);
      message.error('模拟失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 批量模拟
  const handleBatchSimulate = async (values) => {
    if (!systemStatus.simulator_connected) {
      message.error('模拟器未连接！');
      return;
    }

    setLoading(true);
    try {
      const concentrations = [];
      const step = (values.max_conc - values.min_conc) / (values.n_points - 1);
      for (let i = 0; i < values.n_points; i++) {
        concentrations.push(values.min_conc + step * i);
      }

      const response = await batchSimulate({
        concentrations,
        noise_level: values.noise_level,
      });

      setBatchResults(response.data || []);
      message.success(`成功模拟 ${response.total_samples} 个样本！`);
    } catch (error) {
      console.error('批量模拟失败:', error);
      message.error('批量模拟失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 生成并下载数据集
  const handleGenerateDataset = async () => {
    if (!systemStatus.simulator_connected) {
      message.error('模拟器未连接！');
      return;
    }

    setLoading(true);
    try {
      const blob = await generateDataset({
        n_samples: 50,
        concentration_min: 0,
        concentration_max: 0.3,
      });

      // 下载文件
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `simulated_dataset_${Date.now()}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      message.success('数据集生成并下载成功！');
    } catch (error) {
      console.error('生成失败:', error);
      message.error('生成失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 散点图配置
  const getScatterChartOption = () => {
    if (batchResults.length === 0) return {};

    return {
      title: {
        text: '浓度预测曲线',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['375nm', '405nm', '450nm'],
        top: 30,
      },
      xAxis: {
        type: 'category',
        name: '浓度 (g/L)',
        data: batchResults.map((r) => r.concentration?.toFixed(3) || '0.000'),
      },
      yAxis: {
        type: 'value',
        name: '吸光度',
      },
      series: [
        {
          name: '375nm',
          type: 'scatter',
          data: batchResults.map((r) => r.absorbance?.a375 || 0),
          itemStyle: { color: '#FF6B6B' },
        },
        {
          name: '405nm',
          type: 'scatter',
          data: batchResults.map((r) => r.absorbance?.a405 || 0),
          itemStyle: { color: '#4ECDC4' },
        },
        {
          name: '450nm',
          type: 'scatter',
          data: batchResults.map((r) => r.absorbance?.a450 || 0),
          itemStyle: { color: '#45B7D1' },
        },
      ],
    };
  };

  // 批量结果表格列
  const columns = [
    {
      title: '样本编号',
      dataIndex: '样本编号',
      key: 'sample_id',
      width: 100,
    },
    {
      title: '浓度 (g/L)',
      dataIndex: 'concentration',
      key: 'concentration',
      width: 120,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '375nm',
      dataIndex: ['absorbance', 'a375'],
      key: 'a375',
      width: 100,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '405nm',
      dataIndex: ['absorbance', 'a405'],
      key: 'a405',
      width: 100,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '450nm',
      dataIndex: ['absorbance', 'a450'],
      key: 'a450',
      width: 100,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '测量时间',
      dataIndex: 'timestamp',
      key: 'time',
      width: 160,
    },
  ];

  return (
    <div>
      <Row gutter={24}>
        {/* 单次模拟 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <ExperimentOutlined />
                单次测量模拟
              </Space>
            }
            extra={
              <Tag color={systemStatus.simulator_connected ? 'success' : 'error'}>
                {systemStatus.simulator_connected ? '模拟器在线' : '模拟器离线'}
              </Tag>
            }
          >
            <Form
              form={singleForm}
              layout="vertical"
              onFinish={handleSingleSimulate}
              initialValues={{
                concentration: 0.15,
                noise_level: 0.01,
              }}
            >
              <Form.Item
                label="样本浓度 (g/L)"
                name="concentration"
                rules={[{ required: true }]}
              >
                <Slider
                  min={0}
                  max={0.5}
                  step={0.01}
                  marks={{
                    0: '0',
                    0.1: '0.1',
                    0.2: '0.2',
                    0.3: '0.3',
                    0.4: '0.4',
                    0.5: '0.5',
                  }}
                />
              </Form.Item>

              <Form.Item
                label="噪声水平"
                name="noise_level"
                tooltip="模拟测量噪声，值越大噪声越强"
              >
                <Slider
                  min={0}
                  max={0.1}
                  step={0.005}
                  marks={{
                    0: '0',
                    0.05: '0.05',
                    0.1: '0.1',
                  }}
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<PlayCircleOutlined />}
                  block
                >
                  开始模拟
                </Button>
              </Form.Item>
            </Form>

            {singleResult && (
              <Alert
                message="模拟结果"
                description={
                  <div>
                    <p>浓度: {singleResult.concentration} g/L</p>
                    <p>375nm: {singleResult.absorbance.a375}</p>
                    <p>405nm: {singleResult.absorbance.a405}</p>
                    <p>450nm: {singleResult.absorbance.a450}</p>
                  </div>
                }
                type="success"
                showIcon
              />
            )}
          </Card>
        </Col>

        {/* 批量模拟 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <ExperimentOutlined />
                批量测量模拟
              </Space>
            }
          >
            <Form
              form={batchForm}
              layout="vertical"
              onFinish={handleBatchSimulate}
              initialValues={{
                min_conc: 0,
                max_conc: 0.3,
                n_points: 10,
                noise_level: 0.01,
              }}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="最小浓度"
                    name="min_conc"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0} max={0.5} step={0.01} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="最大浓度"
                    name="max_conc"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0} max={0.5} step={0.01} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label="测量点数"
                name="n_points"
                rules={[{ required: true }]}
              >
                <Slider
                  min={5}
                  max={50}
                  marks={{ 5: '5', 20: '20', 35: '35', 50: '50' }}
                />
              </Form.Item>

              <Form.Item
                label="噪声水平"
                name="noise_level"
              >
                <Slider
                  min={0}
                  max={0.1}
                  step={0.005}
                  marks={{
                    0: '0',
                    0.05: '0.05',
                    0.1: '0.1',
                  }}
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<PlayCircleOutlined />}
                  block
                >
                  批量模拟
                </Button>
              </Form.Item>
            </Form>

            <Button
              icon={<DownloadOutlined />}
              onClick={handleGenerateDataset}
              loading={loading}
              block
            >
              生成完整测试数据集
            </Button>
          </Card>
        </Col>
      </Row>

      {/* 批量结果展示 */}
      {batchResults.length > 0 && (
        <>
          <Card title="📊 浓度-吸光度曲线" style={{ marginTop: 24 }}>
            <ReactECharts option={getScatterChartOption()} style={{ height: 400 }} />
          </Card>

          <Card title="📋 测量数据" style={{ marginTop: 24 }}>
            <Table
              columns={columns}
              dataSource={batchResults}
              rowKey="样本编号"
              pagination={{ pageSize: 10 }}
              scroll={{ x: 800 }}
              size="small"
            />
          </Card>
        </>
      )}
    </div>
  );
};

export default SimulatorPanel;
