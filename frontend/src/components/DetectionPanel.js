/**
 * 检测面板组件
 * 作者: 哈雷酱大小姐 (￣▽￣)／
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Form,
  InputNumber,
  Input,
  Button,
  Result,
  Statistic,
  Alert,
  Space,
  Tag,
  Divider,
  Progress,
  Select,
  Descriptions,
  message,
  Checkbox,
} from 'antd';
import {
  CheckCircleOutlined,
  CalculatorOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { predictConcentration, compareModels, getSolutionsInfo, predictDualSolution } from '../services/api';
import { generateErrorReport, shouldEnableFallback } from '../utils/errorHelper';

const DetectionPanel = ({ systemStatus }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [modelComparison, setModelComparison] = useState(null);
  const [errorInfo, setErrorInfo] = useState(null);

  // 双溶液相关状态
  const [solutionsInfo, setSolutionsInfo] = useState(null);
  const [selectedSolution, setSelectedSolution] = useState('solution_a');
  const [useDualSolution, setUseDualSolution] = useState(false);
  const [loadingSolutions, setLoadingSolutions] = useState(false);

  // 加载溶液信息
  useEffect(() => {
    loadSolutionsInfo();
  }, []);

  const loadSolutionsInfo = async () => {
    setLoadingSolutions(true);
    try {
      const info = await getSolutionsInfo();
      setSolutionsInfo(info);
      console.log('溶液信息加载成功:', info);
    } catch (error) {
      console.error('加载溶液信息失败:', error);
      message.warning('无法加载溶液信息，将使用默认单溶液模式');
    } finally {
      setLoadingSolutions(false);
    }
  };

  // 执行预测
  const handlePredict = async (values) => {
    if (!systemStatus.models_loaded) {
      message.error('ML模型未加载，无法进行预测！');
      return;
    }

    setLoading(true);
    try {
      let response;

      // 双溶液预测模式
      if (useDualSolution && selectedSolution) {
        const requestData = {
          a375: values.a375,
          a405: values.a405,
          a450: values.a450,
          solution_type: selectedSolution,
          sample_id: values.sample_id,
          sample_type: values.sample_type || '待测样本',
          notes: values.notes,
        };

        response = await predictDualSolution(requestData);
        message.success(`双溶液预测完成！使用${response.solution_name}`);
      } else {
        // 单溶液预测模式（原有逻辑）
        const requestData = {
          absorbance: {
            a375: values.a375,
            a405: values.a405,
            a450: values.a450,
          },
          sample_info: {
            sample_id: values.sample_id,
            sample_type: values.sample_type || '待测样本',
            notes: values.notes,
          },
          model_type: values.model_type || 'rf',
        };

        response = await predictConcentration(requestData);
      }

      setResult(response);

      // 检查是否为降级预测
      if (response.warning?.type === 'FALLBACK_PREDICTION') {
        message.warning({
          content: '服务器预测失败，已使用本地估算（精度降低）',
          duration: 5,
        });
      } else if (!useDualSolution) {
        message.success('预测完成！');

        // 获取模型对比（如果还没有）
        if (!modelComparison) {
          try {
            const comparison = await compareModels();
            setModelComparison(comparison);
          } catch (err) {
            console.warn('无法获取模型对比信息:', err);
          }
        }
      }
    } catch (error) {
      console.error('预测失败:', error);

      // 生成错误报告
      const errorReport = generateErrorReport(error);
      setErrorInfo(errorReport);

      // 根据错误类型显示不同的消息
      if (errorReport.canUseFallback) {
        message.error({
          content: `预测失败：${errorReport.description}。已启用本地估算模式。`,
          duration: 5,
        });
      } else {
        message.error({
          content: `预测失败：${errorReport.description}`,
          duration: 5,
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // 重置表单
  const handleReset = () => {
    form.resetFields();
    setResult(null);
    setErrorInfo(null);
  };

  // 填充示例数据
  const handleFillExample = () => {
    if (useDualSolution) {
      // 双溶液模式的示例数据
      if (selectedSolution === 'solution_a') {
        // 溶液A的示例数据（高吸光度）
        form.setFieldsValue({
          sample_id: 'SAMPLE-SOLUTION-A-001',
          sample_type: '溶液A样本',
          a375: 1.9702,
          a405: 0.6393,
          a450: 1.0960,
          notes: '溶液A示例数据 - 2025年7月31日测量标准溶液',
        });
        message.info('已填充溶液A示例数据（高吸光度），请点击"开始预测"');
      } else {
        // 溶液B的示例数据（低吸光度）
        form.setFieldsValue({
          sample_id: 'SAMPLE-SOLUTION-B-001',
          sample_type: '溶液B样本',
          a375: 0.0875,
          a405: 0.0146,
          a450: 0.0535,
          notes: '溶液B示例数据 - 2025年8月12日测量实验溶液',
        });
        message.info('已填充溶液B示例数据（低吸光度），请点击"开始预测"');
      }
    } else {
      // 单溶液模式的示例数据
      form.setFieldsValue({
        sample_id: 'SAMPLE-TEST-001',
        sample_type: '待测样本',
        a375: 0.1275,
        a405: 0.1875,
        a450: 0.0975,
        model_type: 'rf',
        notes: '示例数据 - 血浆游离血红蛋白检测',
      });
      message.info('已填充示例数据，请点击"开始预测"');
    }
  };

  // 获取置信度颜色
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.95) return '#52c41a';
    if (confidence >= 0.90) return '#faad14';
    return '#ff4d4f';
  };

  // 特征重要性图表配置
  const getFeatureImportanceChart = () => {
    if (!result || !modelComparison?.random_forest?.feature_importance) {
      return {};
    }

    const importance = modelComparison.random_forest.feature_importance;
    const data = Object.entries(importance)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    return {
      title: {
        text: 'Top 5 特征重要性',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      xAxis: {
        type: 'category',
        data: data.map((item) => item[0]),
        axisLabel: {
          rotate: 30,
        },
      },
      yAxis: {
        type: 'value',
        name: '重要性 (%)',
      },
      series: [
        {
          type: 'bar',
          data: data.map((item) => item[1]),
          itemStyle: {
            color: '#667eea',
          },
        },
      ],
    };
  };

  return (
    <div>
      <Row gutter={24}>
        {/* 左侧：输入表单 */}
        <Col xs={24} lg={10}>
          <Card
            title="📊 数据输入"
            extra={<Tag color={systemStatus.models_loaded ? 'success' : 'error'}>
              {systemStatus.models_loaded ? '模型已加载' : '模型未加载'}
            </Tag>}
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handlePredict}
              initialValues={{
                model_type: 'rf',
                sample_type: '待测样本',
              }}
            >
              {/* 样本信息 */}
              <Divider orientation="left">样本信息</Divider>

              {/* 溶液类型选择 */}
              <Form.Item label={<span>溶液模式 <Tag color="purple">双溶液</Tag></span>}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Checkbox
                    checked={useDualSolution}
                    onChange={(e) => setUseDualSolution(e.target.checked)}
                  >
                    启用双溶液检测模式
                  </Checkbox>

                  {useDualSolution && (
                    <Select
                      value={selectedSolution}
                      onChange={setSelectedSolution}
                      loading={loadingSolutions}
                      style={{ width: '100%' }}
                      placeholder="选择溶液类型"
                    >
                      {solutionsInfo?.solutions ? (
                        Object.entries(solutionsInfo.solutions).map(([key, info]) => (
                          <Select.Option key={key} value={key}>
                            {info.name} - {info.description}
                            {info.available && (
                              <Tag color="success" style={{ marginLeft: 8 }}>
                                R²={info.accuracy?.toFixed(4) || 'N/A'}
                              </Tag>
                            )}
                          </Select.Option>
                        ))
                      ) : (
                        <>
                          <Select.Option value="solution_a">
                            溶液A - 2025年7月31日测量的标准溶液
                          </Select.Option>
                          <Select.Option value="solution_b">
                            溶液B - 2025年8月12日测量的实验溶液
                          </Select.Option>
                        </>
                      )}
                    </Select>
                  )}

                  {useDualSolution && selectedSolution && (
                    <Alert
                      message="双溶液模式说明"
                      description={
                        <div style={{ fontSize: 12 }}>
                          <p>当前选择：{solutionsInfo?.solutions?.[selectedSolution]?.name || selectedSolution}</p>
                          <p>说明：{solutionsInfo?.solutions?.[selectedSolution]?.description || '根据您的实验样品类型选择对应的溶液'}</p>
                          <p style={{ color: '#1890ff', marginTop: 4 }}>
                            💡 提示：不同溶液使用独立训练的模型，预测精度更高
                          </p>
                        </div>
                      }
                      type="info"
                      showIcon
                      style={{ marginTop: 8 }}
                    />
                  )}
                </Space>
              </Form.Item>

              <Form.Item
                label="样本编号"
                name="sample_id"
              >
                <Input placeholder="例如: SAMPLE-001" />
              </Form.Item>

              <Form.Item
                label="样本类型"
                name="sample_type"
              >
                <Select>
                  <Select.Option value="待测样本">待测样本</Select.Option>
                  <Select.Option value="质控样本">质控样本</Select.Option>
                  <Select.Option value="标准品">标准品</Select.Option>
                </Select>
              </Form.Item>

              {/* 吸光度数据 */}
              <Divider orientation="left">吸光度数据</Divider>

              <Form.Item
                label={<span>375nm 吸光度 <Tag color="blue">λ1</Tag></span>}
                name="a375"
                rules={[{ required: true, message: '请输入375nm吸光度' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={3}
                  step={0.0001}
                  precision={4}
                  placeholder="0.0000"
                />
              </Form.Item>

              <Form.Item
                label={<span>405nm 吸光度 <Tag color="red">λ2 (特征峰)</Tag></span>}
                name="a405"
                rules={[{ required: true, message: '请输入405nm吸光度' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={3}
                  step={0.0001}
                  precision={4}
                  placeholder="0.0000"
                />
              </Form.Item>

              <Form.Item
                label={<span>450nm 吸光度 <Tag color="green">λ3</Tag></span>}
                name="a450"
                rules={[{ required: true, message: '请输入450nm吸光度' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={3}
                  step={0.0001}
                  precision={4}
                  placeholder="0.0000"
                />
              </Form.Item>

              {!useDualSolution && (
                <Form.Item
                  label="模型类型"
                  name="model_type"
                >
                  <Select>
                    <Select.Option value="rf">Random Forest (推荐)</Select.Option>
                    <Select.Option value="svr">SVM Regression</Select.Option>
                  </Select>
                </Form.Item>
              )}

              {useDualSolution && (
                <Alert
                  message="双溶液模式使用专用SVR模型"
                  description="双溶液检测模式使用为每种溶液专门训练的SVR模型，精度更高。"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Form.Item
                label="备注"
                name="notes"
              >
                <Input.TextArea
                  rows={2}
                  placeholder="可选备注信息"
                />
              </Form.Item>

              <Form.Item>
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Button onClick={handleReset}>
                    重置
                  </Button>
                  <Button onClick={handleFillExample}>
                    使用示例数据
                  </Button>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    icon={<CalculatorOutlined />}
                    size="large"
                  >
                    开始预测
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* 右侧：结果展示 */}
        <Col xs={24} lg={14}>
          {!result ? (
            <Card style={{ height: '100%' }}>
              <Result
                icon={<CalculatorOutlined style={{ color: '#ccc', fontSize: 72 }} />}
                title="等待预测"
                subTitle='请在左侧输入吸光度数据，然后点击"开始预测"按钮'
                extra={
                  <Alert
                    message="提示"
                    description="本系统基于三波长光谱检测技术（375nm、405nm、450nm），使用机器学习算法预测血浆游离血红蛋白浓度。"
                    type="info"
                    showIcon
                  />
                }
              />
            </Card>
          ) : (
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {/* 降级预测警告 */}
              {result.warning?.type === 'FALLBACK_PREDICTION' && (
                <Alert
                  message="⚠️ 已切换到本地估算模式"
                  description={
                    <div>
                      <p><strong>原因：</strong>{result.warning.message}</p>
                      <p><strong>建议：</strong>{result.warning.suggestion}</p>
                      <p style={{marginTop: 8, fontSize: 12, color: '#666'}}>
                        估算方法：{result.fallback_details?.method}
                      </p>
                    </div>
                  }
                  type="warning"
                  showIcon
                  closable
                />
              )}

              {/* 预测结果卡片 */}
              <Card>
                <Result
                  status={result.warning?.type === 'FALLBACK_PREDICTION' ? 'warning' : 'success'}
                  icon={result.warning?.type === 'FALLBACK_PREDICTION' ? <CalculatorOutlined /> : <CheckCircleOutlined />}
                  title={result.warning?.type === 'FALLBACK_PREDICTION' ? '本地估算完成（降级模式）' : '预测完成！'}
                  subTitle={result.sample_info?.sample_id || `样本检测完成`}
                  extra={
                    // 双溶液模式显示溶液信息
                    useDualSolution && result.solution_name && (
                      <Tag color="purple" style={{ fontSize: 14, padding: '4px 12px' }}>
                        🧪 {result.solution_name}
                      </Tag>
                    )
                  }
                />

                <Row gutter={16} style={{ marginTop: 24 }}>
                  <Col span={12}>
                    <Statistic
                      title="预测浓度"
                      value={result.prediction.concentration}
                      precision={4}
                      suffix="g/L"
                      valueStyle={{
                        color: '#3f8600',
                        fontSize: 32,
                        fontWeight: 'bold',
                      }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="置信度"
                      value={result.prediction.confidence * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{
                        color: getConfidenceColor(result.prediction.confidence),
                        fontSize: 32,
                        fontWeight: 'bold',
                      }}
                    />
                  </Col>
                </Row>

                <Progress
                  percent={Math.round(result.prediction.confidence * 100)}
                  strokeColor={getConfidenceColor(result.prediction.confidence)}
                  showInfo={false}
                  style={{ marginTop: 16 }}
                />

                <Divider />

                <Descriptions column={2} size="small">
                  <Descriptions.Item label="模型类型">
                    <Tag color="blue">
                      {result.model_info?.model_type || result.prediction.model_type}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="预测时间">
                    {result.prediction.timestamp}
                  </Descriptions.Item>
                  {useDualSolution && result.solution_name && (
                    <>
                      <Descriptions.Item label="溶液类型">
                        <Tag color="purple">{result.solution_name}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="溶液描述">
                        {result.solution_description}
                      </Descriptions.Item>
                    </>
                  )}
                </Descriptions>
              </Card>

              {/* 模型性能指标 */}
              <Card
                title={result.warning?.type === 'FALLBACK_PREDICTION' ? '📊 本地估算性能' : '📈 模型性能指标'}
                extra={result.warning?.type === 'FALLBACK_PREDICTION' && <Tag color="warning">降级模式</Tag>}
              >
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="R² 决定系数"
                      value={result.model_info?.test_r2 || 0}
                      precision={4}
                      prefix={<ThunderboltOutlined />}
                      valueStyle={{ color: result.warning?.type === 'FALLBACK_PREDICTION' ? '#faad14' : undefined }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="MAE 平均误差"
                      value={result.model_info?.test_mae || 0}
                      precision={4}
                      suffix="g/L"
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="MSE 均方误差"
                      value={result.model_info?.test_mse || 0}
                      precision={6}
                    />
                  </Col>
                </Row>
              </Card>

              {/* 降级预测局限性说明 */}
              {result.warning?.type === 'FALLBACK_PREDICTION' && result.fallback_details && (
                <Card title="⚠️ 重要提示" type="inner">
                  <Alert
                    message="本地估算的局限性"
                    description={
                      <ul style={{margin: 0, paddingLeft: 20}}>
                        {result.fallback_details.limitations.map((limit, idx) => (
                          <li key={idx}>{limit}</li>
                        ))}
                      </ul>
                    }
                    type="warning"
                    showIcon
                  />
                  <Divider />
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <p><strong>估算公式：</strong></p>
                    <code style={{
                      display: 'block',
                      padding: 12,
                      background: '#f5f5f5',
                      borderRadius: 4,
                      fontSize: 12,
                      color: '#666'
                    }}>
                      {result.fallback_details.formula}
                    </code>
                    <Button
                      type="primary"
                      onClick={() => {
                        message.info('请稍后重试，或联系技术支持检查服务器状态');
                      }}
                      block
                    >
                      重新尝试服务器预测
                    </Button>
                  </Space>
                </Card>
              )}

              {/* 特征重要性 */}
              {modelComparison && (
                <Card title="🎯 特征重要性分析">
                  <ReactECharts
                    option={getFeatureImportanceChart()}
                    style={{ height: 300 }}
                  />
                  <Alert
                    message="核心发现"
                    description={`A405/A375 吸光度比值是最重要的预测特征，贡献度达 ${modelComparison.random_forest?.feature_importance?.['A405_A375'] || 82.6}%，符合朗伯-比尔定律。`}
                    type="info"
                    showIcon
                    style={{ marginTop: 16 }}
                  />
                </Card>
              )}

              {/* 错误诊断卡片 */}
              {errorInfo && !result && (
                <Card
                  title="🔍 错误诊断助手"
                  extra={
                    <Tag color={errorInfo.severity === 'high' ? 'error' : errorInfo.severity === 'medium' ? 'warning' : 'default'}>
                      {errorInfo.severity === 'high' ? '严重' : errorInfo.severity === 'medium' ? '中等' : '轻微'}
                    </Tag>
                  }
                >
                  <Alert
                    message={errorInfo.description}
                    description={
                      <div>
                        <p><strong>错误类型：</strong>{errorInfo.type}</p>
                        {errorInfo.detail && <p><strong>详细信息：</strong>{errorInfo.detail}</p>}
                        <p style={{marginTop: 8, fontSize: 12, color: '#999'}}>
                          发生时间: {new Date(errorInfo.timestamp).toLocaleString('zh-CN')}
                        </p>
                      </div>
                    }
                    type={errorInfo.severity === 'high' ? 'error' : 'warning'}
                    showIcon
                    style={{ marginBottom: 16 }}
                  />

                  <Divider orientation="left">💡 建议解决方案</Divider>
                  <ul style={{paddingLeft: 20}}>
                    {errorInfo.suggestions.map((suggestion, idx) => (
                      <li key={idx} style={{marginBottom: 8}}>
                        {suggestion}
                      </li>
                    ))}
                  </ul>

                  <Divider />

                  <Space>
                    {errorInfo.canRetry && (
                      <Button
                        type="primary"
                        onClick={() => {
                          setErrorInfo(null);
                          message.info('请修改输入后重试');
                        }}
                      >
                        重试预测
                      </Button>
                    )}
                    {errorInfo.canUseFallback && (
                      <Button
                        type="default"
                        onClick={() => {
                          setErrorInfo(null);
                          message.info('请重新提交，系统将自动使用本地估算');
                        }}
                      >
                        使用本地估算
                      </Button>
                    )}
                    <Button
                      danger
                      onClick={() => setErrorInfo(null)}
                    >
                      关闭
                    </Button>
                  </Space>
                </Card>
              )}
            </Space>
          )}
        </Col>
      </Row>
    </div>
  );
};

export default DetectionPanel;
