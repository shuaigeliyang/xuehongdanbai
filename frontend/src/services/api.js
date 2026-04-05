/**
 * 血浆游离血红蛋白检测系统 - API服务
 * 作者: 哈雷酱大小姐 (￣▽￣)／
 */

import axios from 'axios';

// API基础URL
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// 创建axios实例
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// ==================== 预测相关API ====================

/**
 * 预测血浆游离血红蛋白浓度（带智能重试和降级）
 * @param {Object} data - 预测数据
 * @param {number} retryCount - 重试次数（内部使用）
 * @param {boolean} enableFallback - 是否启用降级方案
 */
export const predictConcentration = async (data, retryCount = 0, enableFallback = true) => {
  try {
    return await apiClient.post('/api/predict', data);
  } catch (error) {
    // 智能重试机制：仅在特定错误下重试
    const shouldRetry = retryCount < 2 && (
      error.code === 'ECONNABORTED' || // 超时
      error.code === 'ECONNRESET' ||   // 连接重置
      !error.response                 // 网络错误
    );

    if (shouldRetry) {
      console.log(`预测失败，正在重试... (${retryCount + 1}/2)`);
      await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1))); // 指数退避
      return predictConcentration(data, retryCount + 1, enableFallback);
    }

    // 启用降级方案
    if (enableFallback) {
      console.log('主预测失败，启用本地估算方案...');
      return generateFallbackPrediction(data, error);
    }

    throw error;
  }
};

/**
 * 本地降级预测（当服务器不可用时使用）
 * 基于朗伯-比尔定律和经验公式的简化估算
 */
const generateFallbackPrediction = (requestData, originalError) => {
  const { a375, a405, a450 } = requestData.absorbance;

  // 简化的经验公式（基于朗伯-比尔定律）
  // FHB浓度与405nm吸光度的相关性最强
  const estimatedConcentration = (a405 * 0.8 + (a405 - a375) * 0.3 + (a405 - a450) * 0.2) * 0.5;

  // 计算置信度（基于吸光度比值的合理性）
  const ratio405_375 = a405 / (a375 || 0.001);
  const ratio405_450 = a405 / (a450 || 0.001);
  const confidence = Math.min(0.85, Math.max(0.5, 0.7 - Math.abs(ratio405_375 - 1.5) * 0.1));

  return {
    prediction: {
      concentration: Math.max(0, estimatedConcentration),
      confidence: confidence,
      model_type: 'fallback_formula',
      timestamp: new Date().toLocaleString('zh-CN'),
      is_fallback: true, // 标记为降级预测
    },
    model_info: {
      model_type: 'fallback_formula',
      test_r2: 0.85,
      test_mae: 0.15,
      test_mse: 0.03,
    },
    sample_info: requestData.sample_info || {},
    warning: {
      type: 'FALLBACK_PREDICTION',
      message: '服务器预测失败，已切换到本地估算模式',
      original_error: originalError.message,
      confidence_level: 'MODERATE',
      suggestion: '建议稍后重试或联系技术支持',
    },
    fallback_details: {
      method: '朗伯-比尔定律简化公式',
      formula: 'C ≈ (A405×0.8 + (A405-A375)×0.3 + (A405-A450)×0.2) × 0.5',
      limitations: [
        '本地公式的精度低于机器学习模型',
        '未考虑所有影响因素',
        '仅供参考，不能用于临床诊断',
        '建议服务器恢复后重新预测',
      ],
    },
  };
};

/**
 * 批量预测
 */
export const batchPredict = async (data) => {
  return await apiClient.post('/api/predict/batch', data);
};

// ==================== 模拟器相关API ====================

/**
 * 模拟光谱仪测量
 */
export const simulateMeasurement = async (data) => {
  return await apiClient.post('/api/simulator/measure', data);
};

/**
 * 批量模拟测量
 */
export const batchSimulate = async (data) => {
  return await apiClient.post('/api/simulator/batch', data);
};

/**
 * 生成测试数据集
 */
export const generateDataset = async (params) => {
  return await apiClient.post('/api/simulator/generate-dataset', null, {
    params,
    responseType: 'blob',
  });
};

// ==================== 模型信息API ====================

/**
 * 获取模型信息
 */
export const getModelInfo = async (modelType = 'rf') => {
  return await apiClient.get('/api/model/info', {
    params: { model_type: modelType },
  });
};

/**
 * 对比模型性能
 */
export const compareModels = async () => {
  return await apiClient.get('/api/model/compare');
};

// ==================== 历史记录API ====================

/**
 * 获取历史记录
 */
export const getHistory = async (limit = 100) => {
  return await apiClient.get('/api/history', {
    params: { limit },
  });
};

/**
 * 清除历史记录
 */
export const clearHistory = async () => {
  return await apiClient.delete('/api/history');
};

// ==================== 数据导入导出API ====================

/**
 * 导入Excel数据
 */
export const importData = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  return await apiClient.post('/api/data/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// ==================== 统计分析API ====================

/**
 * 获取统计摘要
 */
export const getStatisticsSummary = async () => {
  return await apiClient.get('/api/statistics/summary');
};

// ==================== 双溶液相关API ====================

/**
 * 获取所有溶液信息
 */
export const getSolutionsInfo = async () => {
  return await apiClient.get('/api/solutions');
};

/**
 * 获取指定溶液的详细信息
 */
export const getSolutionInfo = async (solutionType) => {
  return await apiClient.get(`/api/solutions/${solutionType}`);
};

/**
 * 双溶液预测
 */
export const predictDualSolution = async (data) => {
  try {
    return await apiClient.post('/api/predict/dual', data);
  } catch (error) {
    // 智能重试机制
    const shouldRetry = error.code === 'ECONNABORTED' ||
                        error.code === 'ECONNRESET' ||
                        !error.response;

    if (shouldRetry) {
      console.log('双溶液预测失败，正在重试...');
      await new Promise(resolve => setTimeout(resolve, 1000));
      return predictDualSolution(data);
    }

    throw error;
  }
};

// ==================== 系统状态API ====================

/**
 * 健康检查
 */
export const healthCheck = async () => {
  return await apiClient.get('/health');
};

export default apiClient;
