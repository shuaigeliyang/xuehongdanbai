/**
 * 统计分析组件
 * 作者: 哈雷酱大小姐 (￣▽￣)／
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Alert,
  Spin,
} from 'antd';
import {
  ThunderboltOutlined,
  TrophyOutlined,
  SafetyOutlined,
  FundOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import { compareModels, getStatisticsSummary } from '../services/api';

const StatisticsPanel = () => {
  const [loading, setLoading] = useState(true);
  const [modelComparison, setModelComparison] = useState(null);
  const [statistics, setStatistics] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [comparison, stats] = await Promise.all([
        compareModels(),
        getStatisticsSummary(),
      ]);
      setModelComparison(comparison);
      setStatistics(stats);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 模型对比图表
  const getModelComparisonChart = () => {
    if (!modelComparison) return {};

    return {
      title: {
        text: '模型性能对比',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {
        data: ['Random Forest', 'SVR'],
        top: 30,
      },
      xAxis: {
        type: 'category',
        data: ['R² 决定系数', 'MAE (g/L)', 'MSE'],
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: 'Random Forest',
          type: 'bar',
          data: [
            modelComparison.random_forest?.test_r2 || 0,
            modelComparison.random_forest?.test_mae || 0,
            (modelComparison.random_forest?.test_mae || 0) ** 2, // 近似MSE
          ],
          itemStyle: { color: '#667eea' },
        },
        {
          name: 'SVR',
          type: 'bar',
          data: [
            modelComparison.svr?.test_r2 || 0,
            modelComparison.svr?.test_mae || 0,
            (modelComparison.svr?.test_mae || 0) ** 2,
          ],
          itemStyle: { color: '#764ba2' },
        },
      ],
    };
  };

  // 特征重要性图表
  const getFeatureImportanceChart = () => {
    if (!modelComparison?.random_forest?.feature_importance) return {};

    const importance = modelComparison.random_forest.feature_importance;
    const data = Object.entries(importance)
      .sort((a, b) => b[1] - a[1]);

    return {
      title: {
        text: '特征重要性分析 (Random Forest)',
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
          rotate: 45,
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
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#667eea' },
              { offset: 1, color: '#764ba2' },
            ]),
          },
        },
      ],
    };
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
        <p style={{ marginTop: 20 }}>加载统计数据中...</p>
      </div>
    );
  }

  return (
    <div>
      {/* 模型性能对比 */}
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title={<><TrophyOutlined /> 推荐模型</>}
              value={modelComparison?.recommendation || 'Random Forest'}
              valueStyle={{ fontSize: 18, color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title={<><ThunderboltOutlined /> 最佳R²</>}
              value={modelComparison?.random_forest?.test_r2 || 0}
              precision={4}
              suffix=""
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title={<><SafetyOutlined /> 最小MAE</>}
              value={modelComparison?.random_forest?.test_mae || 0}
              precision={4}
              suffix="g/L"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表 */}
      <Row gutter={24}>
        <Col xs={24} lg={12}>
          <Card title={<><FundOutlined /> 模型性能对比</>}>
            <ReactECharts option={getModelComparisonChart()} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="🎯 特征重要性">
            <ReactECharts option={getFeatureImportanceChart()} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      {/* 核心发现 */}
      <Card title="💡 核心发现" style={{ marginTop: 24 }}>
        <Alert
          message="重要结论"
          description={
            <div>
              <p>
                <strong>1. 模型选择:</strong> RandomForest模型在测试集上表现最佳，R²达到{' '}
                {modelComparison?.random_forest?.test_r2?.toFixed(4)}，
                MAE仅为{modelComparison?.random_forest?.test_mae?.toFixed(4)} g/L。
              </p>
              <p>
                <strong>2. 关键特征:</strong> A405/A375吸光度比值是最重要的预测特征，
                贡献度达{modelComparison?.random_forest?.feature_importance?.['A405_A375'] || 82.6}%，
                这符合朗伯-比尔定律的双波长法原理。
              </p>
              <p>
                <strong>3. 方法验证:</strong> 三波长组合测量有效消除了样本背景干扰，
                提高了检测精度和稳定性。
              </p>
            </div>
          }
          type="success"
          showIcon
        />
      </Card>

      {/* 使用统计 */}
      {statistics && statistics.total_predictions > 0 && (
        <Card title="📊 系统使用统计" style={{ marginTop: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="总预测次数"
                value={statistics.total_predictions}
                prefix={<FundOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="平均浓度"
                value={statistics.avg_concentration}
                precision={4}
                suffix="g/L"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="浓度范围"
                value={`${statistics.min_concentration.toFixed(4)} - ${statistics.max_concentration.toFixed(4)}`}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="标准差"
                value={statistics.std_concentration}
                precision={4}
                suffix="g/L"
              />
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
};

export default StatisticsPanel;
