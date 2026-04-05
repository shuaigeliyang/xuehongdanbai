/**
 * 数据模拟器组件（双溶液版）
 * 作者: 哈雷酱大小姐 (￣▽￣)／
 */

import React, { useState, useEffect } from 'react';
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
  Tabs,
  Checkbox,
  Select,
  Divider,
  Descriptions,
} from 'antd';
import {
  ExperimentOutlined,
  DownloadOutlined,
  PlayCircleOutlined,
 ThunderboltOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import {
  simulateMeasurement,
  batchSimulate,
  generateDataset,
  getSolutionsInfo,
  predictDualSolution,
  getSimulatorSolutions,
  simulateDualSolution,
  batchSimulateDual,
  generateDualDataset,
} from '../services/api';

const SimulatorPanel = ({ systemStatus }) => {
  const [singleForm] = Form.useForm();
  const [batchForm] = Form.useForm();
  const [dualSingleForm] = Form.useForm();
  const [dualBatchForm] = Form.useForm();
  const [singleResult, setSingleResult] = useState(null);
  const [batchResults, setBatchResults] = useState([]);
  const [dualSingleResult, setDualSingleResult] = useState(null);
  const [dualBatchResults, setDualBatchResults] = useState(null);
  const [dualSolutionsData, setDualSolutionsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [simulatorSolutions, setSimulatorSolutions] = useState(null);
  const [solutionsInfo, setSolutionsInfo] = useState(null);
  const [selectedSolution, setSelectedSolution] = useState('solution_a');
  const [useDualMode, setUseDualMode] = useState(false);

  // 加载溶液信息
  useEffect(() => {
    loadSolutionsInfo();
    loadSimulatorSolutions();
  }, []);

  const loadSolutionsInfo = async () => {
    try {
      const info = await getSolutionsInfo();
      setSolutionsInfo(info);
    } catch (error) {
      console.error('加载溶液信息失败:', error);
    }
  };

  const loadSimulatorSolutions = async () => {
    try {
      const info = await getSimulatorSolutions();
      setSimulatorSolutions(info);
    } catch (error) {
      console.error('加载模拟器溶液信息失败:', error);
    }
  };

  // ==================== 单溶液模拟 ====================

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

  // ==================== 双溶液模拟 ====================

  const handleDualSingleSimulate = async (values) => {
    setLoading(true);
    try {
      const response = await simulateDualSolution({
        concentration: values.concentration,
        solution_type: selectedSolution,
        noise_level: values.noise_level || 0.01,
      });
      setDualSingleResult(response);
      message.success(`${response.sample_info.solution_name} 模拟测量完成！`);
    } catch (error) {
      console.error('双溶液模拟失败:', error);
      message.error('模拟失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDualBatchSimulate = async (values) => {
    setLoading(true);
    try {
      // 生成浓度列表
      const concentrations = [];
      const step = (values.max_conc - values.min_conc) / (values.n_points - 1);
      for (let i = 0; i < values.n_points; i++) {
        concentrations.push(values.min_conc + step * i);
      }

      const response = await batchSimulateDual({
        concentrations,
        solution_type: selectedSolution,
        noise_level: values.noise_level || 0.01,
      });

      setDualBatchResults(response.data || []);
      message.success(`${response.total_samples} 个样本模拟完成！`);
    } catch (error) {
      console.error('双溶液批量模拟失败:', error);
      message.error('批量模拟失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDualDataset = async () => {
    setLoading(true);
    try {
      const response = await generateDualDataset(20, 20, 0.01);
      setDualSolutionsData(response);
      message.success(`双溶液数据集生成完成！共 ${response.total_count} 个样本`);
    } catch (error) {
      console.error('生成双溶液数据集失败:', error);
      message.error('生成失败: ' + (error.response?.data?.detail || error.message));
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

  // ==================== 图表配置 ====================

  const getScatterChartOption = () => {
    if (batchResults.length === 0) return {};

    return {
      title: {
        text: '浓度-吸光度曲线',
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

  // 双溶液批量结果图表
  const getDualBatchChartOption = () => {
    if (!dualBatchResults || dualBatchResults.length === 0) return {};

    return {
      title: {
        text: `${solutionsInfo?.solutions?.[selectedSolution]?.name || selectedSolution} - 预测结果`,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['真实浓度', '预测浓度'],
        top: 30,
      },
      xAxis: {
        type: 'category',
        name: '样本编号',
        data: dualBatchResults.map((_, i) => i + 1),
      },
      yAxis: {
        type: 'value',
        name: '浓度 (g/L)',
      },
      series: [
        {
          name: '真实浓度',
          type: 'line',
          data: dualBatchResults.map(r => r['真实浓度']),
          itemStyle: { color: '#1890ff' },
        },
        {
          name: '预测浓度',
          type: 'scatter',
          data: dualBatchResults.map(r => r['预测浓度']),
          itemStyle: { color: '#52c41a' },
        },
      ],
    };
  };

  // 双溶液数据集对比图表
  const getDualCompareChartOption = () => {
    if (!dualSolutionsData) return {};

    const dataA = dualSolutionsData.solution_a?.samples || [];
    const dataB = dualSolutionsData.solution_b?.samples || [];

    return {
      title: {
        text: '双溶液预测对比',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['溶液A真实', '溶液A预测', '溶液B真实', '溶液B预测'],
        top: 30,
      },
      xAxis: {
        type: 'category',
        name: '样本编号',
        data: [...Array(dataA.length).keys(), ...Array(dataB.length).keys()].map(i => i + 1),
      },
      yAxis: {
        type: 'value',
        name: '浓度 (g/L)',
      },
      series: [
        {
          name: '溶液A真实',
          type: 'scatter',
          data: dataA.map(r => r.concentration),
          itemStyle: { color: '#722ed1' },
        },
        {
          name: '溶液A预测',
          type: 'scatter',
          data: dataA.map(r => r['预测浓度'] || 0),
          itemStyle: { color: '#d46b08' },
        },
        {
          name: '溶液B真实',
          type: 'scatter',
          data: dataB.map(r => r.concentration),
          itemStyle: { color: '#1890ff' },
        },
        {
          name: '溶液B预测',
          type: 'scatter',
          data: dataB.map(r => r['预测浓度'] || 0),
          itemStyle: { color: '#52c41a' },
        },
      ],
    };
  };

  // 表格列定义
  const columns = [
    {
      title: '样本编号',
      dataIndex: '样本编号',
      key: 'sample_id',
      width: 80,
    },
    {
      title: '浓度 (g/L)',
      dataIndex: 'concentration',
      key: 'concentration',
      width: 100,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '375nm',
      dataIndex: ['absorbance', 'a375'],
      key: 'a375',
      width: 90,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '405nm',
      dataIndex: ['absorbance', 'a405'],
      key: 'a405',
      width: 90,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '450nm',
      dataIndex: ['absorbance', 'a450'],
      key: 'a450',
      width: 90,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
  ];

  // 双溶液批量结果列
  const dualBatchColumns = [
    {
      title: '编号',
      dataIndex: '样本编号',
      key: 'index',
      width: 60,
    },
    {
      title: '真实浓度',
      dataIndex: '真实浓度',
      key: 'true',
      width: 90,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '预测浓度',
      dataIndex: '预测浓度',
      key: 'pred',
      width: 90,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '误差',
      dataIndex: '预测误差',
      key: 'error',
      width: 80,
      render: (val) => (
        <span style={{ color: val < 0.01 ? '#52c41a' : val < 0.05 ? '#faad14' : '#ff4d4f' }}>
          {val?.toFixed(4) || '0.0000'}
        </span>
      ),
    },
    {
      title: 'A375',
      dataIndex: 'a375',
      key: 'a375',
      width: 80,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: 'A405',
      dataIndex: 'a405',
      key: 'a405',
      width: 80,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: 'A450',
      dataIndex: 'a450',
      key: 'a450',
      width: 80,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
  ];

  // 双溶液数据集表格（合并两种溶液）
  const dualDatasetColumns = [
    {
      title: '编号',
      key: 'index',
      width: 60,
      render: (_, __, i) => i + 1,
    },
    {
      title: '溶液',
      dataIndex: '溶液类型',
      key: 'solution',
      width: 100,
      render: (val) => <Tag color={val?.includes('A') ? 'purple' : 'blue'}>{val}</Tag>,
    },
    {
      title: '真实浓度',
      dataIndex: 'concentration',
      key: 'true',
      width: 90,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '预测浓度',
      dataIndex: '预测浓度',
      key: 'pred',
      width: 90,
      render: (val) => val?.toFixed(4) || '0.0000',
    },
    {
      title: '误差',
      dataIndex: '预测误差',
      key: 'error',
      width: 80,
      render: (val) => (
        <span style={{ color: val < 0.01 ? '#52c41a' : val < 0.05 ? '#faad14' : '#ff4d4f' }}>
          {val?.toFixed(4) || '0.0000'}
        </span>
      ),
    },
  ];

  // Tab配置
  const tabItems = [
    {
      key: 'single',
      label: '单溶液模拟',
      children: (
        <Row gutter={24}>
          <Col xs={24} lg={12}>
            <Card title="单次测量模拟" extra={
              <Tag color={systemStatus.simulator_connected ? 'success' : 'error'}>
                {systemStatus.simulator_connected ? '模拟器在线' : '模拟器离线'}
              </Tag>
            }>
              <Form form={singleForm} layout="vertical" onFinish={handleSingleSimulate}
                initialValues={{ concentration: 0.15, noise_level: 0.01 }}>
                <Form.Item label="样本浓度 (g/L)" name="concentration" rules={[{ required: true }]}>
                  <Slider min={0} max={0.5} step={0.01}
                    marks={{ 0: '0', 0.1: '0.1', 0.2: '0.2', 0.3: '0.3', 0.4: '0.4', 0.5: '0.5' }} />
                </Form.Item>
                <Form.Item label="噪声水平" name="noise_level" tooltip="模拟测量噪声，值越大噪声越强">
                  <Slider min={0} max={0.1} step={0.005}
                    marks={{ 0: '0', 0.05: '0.05', 0.1: '0.1' }} />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading} icon={<PlayCircleOutlined />} block>
                    开始模拟
                  </Button>
                </Form.Item>
              </Form>

              {singleResult && (
                <Alert message="模拟结果" type="success" showIcon style={{ marginTop: 16 }}
                  description={
                    <div>
                      <p>浓度: {singleResult.concentration} g/L</p>
                      <p>375nm: {singleResult.absorbance.a375}</p>
                      <p>405nm: {singleResult.absorbance.a405}</p>
                      <p>450nm: {singleResult.absorbance.a450}</p>
                    </div>
                  } />
              )}
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="批量测量模拟">
              <Form form={batchForm} layout="vertical" onFinish={handleBatchSimulate}
                initialValues={{ min_conc: 0, max_conc: 0.3, n_points: 10, noise_level: 0.01 }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="最小浓度" name="min_conc" rules={[{ required: true }]}>
                      <InputNumber min={0} max={0.5} step={0.01} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="最大浓度" name="max_conc" rules={[{ required: true }]}>
                      <InputNumber min={0} max={0.5} step={0.01} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item label="测量点数" name="n_points" rules={[{ required: true }]}>
                  <Slider min={5} max={50} marks={{ 5: '5', 20: '20', 35: '35', 50: '50' }} />
                </Form.Item>
                <Form.Item label="噪声水平" name="noise_level">
                  <Slider min={0} max={0.1} step={0.005}
                    marks={{ 0: '0', 0.05: '0.05', 0.1: '0.1' }} />
                </Form.Item>
                <Form.Item>
                  <Space>
                    <Button type="primary" htmlType="submit" loading={loading} icon={<PlayCircleOutlined />}>
                      批量模拟
                    </Button>
                    <Button icon={<DownloadOutlined />} onClick={handleGenerateDataset} loading={loading}>
                      生成数据集
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: 'dual',
      label: (
        <span>
          <ExperimentOutlined />
          双溶液模拟 ⭐
        </span>
      ),
      children: (
        <div>
          {/* 溶液选择 */}
          <Card style={{ marginBottom: 16 }}>
            <Row gutter={16} align="middle">
              <Col>
                <span style={{ fontWeight: 'bold', marginRight: 8 }}>选择溶液类型：</span>
              </Col>
              <Col>
                <Select value={selectedSolution} onChange={setSelectedSolution} style={{ width: 300 }}>
                  {simulatorSolutions?.solutions ? (
                    Object.entries(simulatorSolutions.solutions).map(([key, info]) => (
                      <Select.Option key={key} value={key}>
                        {info.name} - {info.description}
                        <Tag color={key === 'solution_a' ? 'purple' : 'blue'} style={{ marginLeft: 8 }}>
                          R²={solutionsInfo?.solutions?.[key]?.accuracy?.toFixed(4) || 'N/A'}
                        </Tag>
                      </Select.Option>
                    ))
                  ) : (
                    <>
                      <Select.Option value="solution_a">
                        溶液A - 高吸光度标准溶液 (R²=0.9657)
                      </Select.Option>
                      <Select.Option value="solution_b">
                        溶液B - 低吸光度实验溶液 (R²=0.9987)
                      </Select.Option>
                    </>
                  )}
                </Select>
              </Col>
              <Col>
                <Tag color={selectedSolution === 'solution_a' ? 'purple' : 'blue'} style={{ fontSize: 14 }}>
                  当前选择：{simulatorSolutions?.solutions?.[selectedSolution]?.name || selectedSolution}
                </Tag>
              </Col>
            </Row>
          </Card>

          <Row gutter={24}>
            {/* 双溶液单次模拟 */}
            <Col xs={24} lg={12}>
              <Card title="双溶液单次模拟" extra={<Tag color="purple">⭐ 预测一体化</Tag>}>
                <Form form={dualSingleForm} layout="vertical" onFinish={handleDualSingleSimulate}
                  initialValues={{ concentration: 0.15, noise_level: 0.01 }}>
                  <Form.Item label="样本浓度 (g/L)" name="concentration" rules={[{ required: true }]}>
                    <Slider min={0} max={0.5} step={0.01}
                      marks={{ 0: '0', 0.1: '0.1', 0.2: '0.2', 0.3: '0.3', 0.4: '0.4', 0.5: '0.5' }} />
                  </Form.Item>
                  <Form.Item label="噪声水平" name="noise_level">
                    <Slider min={0} max={0.1} step={0.005}
                      marks={{ 0: '0', 0.05: '0.05', 0.1: '0.1' }} />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}
                      icon={<ThunderboltOutlined />} block size="large">
                      模拟并预测
                    </Button>
                  </Form.Item>
                </Form>

                {dualSingleResult && (
                  <Card size="small" style={{ marginTop: 16, background: '#f6ffed' }}>
                    <Descriptions column={2} size="small" title="模拟+预测结果">
                      <Descriptions.Item label="溶液">
                        <Tag color={selectedSolution === 'solution_a' ? 'purple' : 'blue'}>
                          {dualSingleResult.sample_info.solution_name}
                        </Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="真实浓度">
                        {dualSingleResult.sample_info.concentration_true} g/L
                      </Descriptions.Item>
                      <Descriptions.Item label="预测浓度">
                        <Statistic value={dualSingleResult.prediction.concentration} precision={4} suffix="g/L"
                          valueStyle={{ color: '#52c41a', fontSize: 18 }} />
                      </Descriptions.Item>
                      <Descriptions.Item label="预测误差">
                        <span style={{ color: dualSingleResult.prediction.error < 0.01 ? '#52c41a' : '#faad14' }}>
                          {dualSingleResult.prediction.error} g/L
                        </span>
                      </Descriptions.Item>
                    </Descriptions>
                    <Divider style={{ margin: '12px 0' }} />
                    <Row gutter={16}>
                      <Col span={8}>
                        <Statistic title="A375" value={dualSingleResult.absorbance.a375} precision={4} />
                      </Col>
                      <Col span={8}>
                        <Statistic title="A405" value={dualSingleResult.absorbance.a405} precision={4} />
                      </Col>
                      <Col span={8}>
                        <Statistic title="A450" value={dualSingleResult.absorbance.a450} precision={4} />
                      </Col>
                    </Row>
                  </Card>
                )}
              </Card>
            </Col>

            {/* 双溶液批量模拟 */}
            <Col xs={24} lg={12}>
              <Card title="双溶液批量模拟" extra={<Tag color="purple">⭐ 预测一体化</Tag>}>
                <Form form={dualBatchForm} layout="vertical" onFinish={handleDualBatchSimulate}
                  initialValues={{ min_conc: 0, max_conc: 0.3, n_points: 15, noise_level: 0.01 }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item label="最小浓度" name="min_conc" rules={[{ required: true }]}>
                        <InputNumber min={0} max={0.5} step={0.01} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="最大浓度" name="max_conc" rules={[{ required: true }]}>
                        <InputNumber min={0} max={0.5} step={0.01} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                  </Row>
                  <Form.Item label="测量点数" name="n_points" rules={[{ required: true }]}>
                    <Slider min={5} max={50} marks={{ 5: '5', 20: '20', 35: '35', 50: '50' }} />
                  </Form.Item>
                  <Form.Item label="噪声水平" name="noise_level">
                    <Slider min={0} max={0.1} step={0.005}
                      marks={{ 0: '0', 0.05: '0.05', 0.1: '0.1' }} />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}
                      icon={<ThunderboltOutlined />} block size="large">
                      批量模拟并预测
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
          </Row>

          {/* 批量结果展示 */}
          {dualBatchResults && dualBatchResults.length > 0 && (
            <Card title="📊 批量模拟结果" style={{ marginTop: 16 }}>
              <ReactECharts option={getDualBatchChartOption()} style={{ height: 300 }} />
              <Table columns={dualBatchColumns} dataSource={dualBatchResults} rowKey="样本编号"
                pagination={{ pageSize: 10 }} scroll={{ x: 700 }} size="small" style={{ marginTop: 16 }} />
            </Card>
          )}

          {/* 生成双溶液数据集 */}
          <Card title="📁 生成双溶液测试数据集" style={{ marginTop: 16 }}>
            <Alert message="一键生成两种溶液的测试数据集，每种20个样本，并自动执行预测"
              type="info" showIcon style={{ marginBottom: 16 }} />
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleGenerateDualDataset}
              loading={loading} size="large">
              生成双溶液数据集（溶液A 20样本 + 溶液B 20样本）
            </Button>

            {dualSolutionsData && (
              <div style={{ marginTop: 16 }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Card size="small" title={dualSolutionsData.solution_a?.solution_name}>
                      <Statistic title="样本数" value={dualSolutionsData.solution_a?.count} />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card size="small" title={dualSolutionsData.solution_b?.solution_name}>
                      <Statistic title="样本数" value={dualSolutionsData.solution_b?.count} />
                    </Card>
                  </Col>
                </Row>
                <ReactECharts option={getDualCompareChartOption()} style={{ height: 350, marginTop: 16 }} />
              </div>
            )}
          </Card>
        </div>
      ),
    },
  ];

  return (
    <div>
      <Tabs items={tabItems} size="large" />
    </div>
  );
};

export default SimulatorPanel;
