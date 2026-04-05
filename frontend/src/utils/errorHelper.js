/**
 * 预测错误诊断助手
 * 作者: 哈雷酱大小姐 (￣▽￣)／
 *
 * 提供智能错误分析和解决方案建议
 */

/**
 * 错误类型枚举
 */
export const ErrorTypes = {
  NETWORK_ERROR: 'NETWORK_ERROR',           // 网络连接问题
  SERVER_ERROR: 'SERVER_ERROR',             // 服务器错误 (5xx)
  TIMEOUT: 'TIMEOUT',                       // 请求超时
  VALIDATION_ERROR: 'VALIDATION_ERROR',     // 输入验证失败
  MODEL_NOT_LOADED: 'MODEL_NOT_LOADED',     // 模型未加载
  DATABASE_ERROR: 'DATABASE_ERROR',         // 数据库错误
  UNKNOWN: 'UNKNOWN',                       // 未知错误
};

/**
 * 识别错误类型
 */
export const identifyError = (error) => {
  // 网络错误
  if (!error.response && !error.request) {
    return ErrorTypes.NETWORK_ERROR;
  }

  // 超时
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return ErrorTypes.TIMEOUT;
  }

  // 服务器错误
  if (error.response?.status >= 500) {
    const detail = error.response?.data?.detail || '';
    if (detail.includes('模型') || detail.includes('model')) {
      return ErrorTypes.MODEL_NOT_LOADED;
    }
    if (detail.includes('数据库') || detail.includes('database')) {
      return ErrorTypes.DATABASE_ERROR;
    }
    return ErrorTypes.SERVER_ERROR;
  }

  // 客户端错误
  if (error.response?.status >= 400) {
    return ErrorTypes.VALIDATION_ERROR;
  }

  return ErrorTypes.UNKNOWN;
};

/**
 * 获取错误的友好描述
 */
export const getErrorDescription = (errorType) => {
  const descriptions = {
    [ErrorTypes.NETWORK_ERROR]: '无法连接到服务器，请检查网络连接',
    [ErrorTypes.SERVER_ERROR]: '服务器内部错误，请稍后重试',
    [ErrorTypes.TIMEOUT]: '请求超时，服务器响应时间过长',
    [ErrorTypes.VALIDATION_ERROR]: '输入数据验证失败，请检查数据格式',
    [ErrorTypes.MODEL_NOT_LOADED]: '机器学习模型未加载，请联系管理员',
    [ErrorTypes.DATABASE_ERROR]: '数据库连接失败，请联系技术支持',
    [ErrorTypes.UNKNOWN]: '未知错误，请联系技术支持',
  };
  return descriptions[errorType] || descriptions[ErrorTypes.UNKNOWN];
};

/**
 * 获取解决方案建议
 */
export const getSolutionSuggestions = (errorType, errorDetail = '') => {
  const suggestions = {
    [ErrorTypes.NETWORK_ERROR]: [
      '检查网络连接是否正常',
      '确认服务器地址是否正确',
      '尝试刷新页面重新连接',
      '检查防火墙设置',
    ],
    [ErrorTypes.SERVER_ERROR]: [
      '等待片刻后重试',
      '查看服务器日志获取详细错误',
      '联系技术支持',
      '尝试使用本地估算功能',
    ],
    [ErrorTypes.TIMEOUT]: [
      '检查网络速度是否过慢',
      '减少批量预测的数据量',
      '稍后重试',
      '使用单个样本预测代替批量预测',
    ],
    [ErrorTypes.VALIDATION_ERROR]: [
      '确认所有吸光度值已填写',
      '检查数值范围是否在 0-3 之间',
      '确认小数点位数正确',
      '查看错误详情了解具体问题',
    ],
    [ErrorTypes.MODEL_NOT_LOADED]: [
      '重启服务器',
      '检查模型文件是否存在',
      '查看服务器启动日志',
      '联系系统管理员',
    ],
    [ErrorTypes.DATABASE_ERROR]: [
      '检查数据库服务是否运行',
      '确认数据库连接配置',
      '查看数据库日志',
      '联系技术支持',
    ],
    [ErrorTypes.UNKNOWN]: [
      '记录错误信息',
      '联系技术支持',
      '查看浏览器控制台获取详细信息',
      '尝试刷新页面',
    ],
  };

  // 根据错误详情添加针对性建议
  const baseSuggestions = suggestions[errorType] || suggestions[ErrorTypes.UNKNOWN];

  if (errorDetail) {
    if (errorDetail.includes('a375') || errorDetail.includes('a405') || errorDetail.includes('a450')) {
      baseSuggestions.unshift('请确保输入的吸光度值在合理范围内（0-3）');
    }
    if (errorDetail.includes('sample_id')) {
      baseSuggestions.unshift('样本编号不能为空');
    }
  }

  return baseSuggestions;
};

/**
 * 获取错误严重程度
 */
export const getErrorSeverity = (errorType) => {
  const severityMap = {
    [ErrorTypes.NETWORK_ERROR]: 'high',      // 高 - 完全无法使用
    [ErrorTypes.SERVER_ERROR]: 'high',       // 高 - 核心功能故障
    [ErrorTypes.TIMEOUT]: 'medium',          // 中 - 可能是临时问题
    [ErrorTypes.VALIDATION_ERROR]: 'low',    // 低 - 用户输入问题
    [ErrorTypes.MODEL_NOT_LOADED]: 'high',   // 高 - 需要管理员介入
    [ErrorTypes.DATABASE_ERROR]: 'high',     // 高 - 数据持久化问题
    [ErrorTypes.UNKNOWN]: 'medium',          // 中 - 需要诊断
  };
  return severityMap[errorType] || 'medium';
};

/**
 * 生成错误报告对象
 */
export const generateErrorReport = (error) => {
  const errorType = identifyError(error);
  const description = getErrorDescription(errorType);
  const suggestions = getSolutionSuggestions(errorType, error.response?.data?.detail);
  const severity = getErrorSeverity(errorType);

  return {
    type: errorType,
    description,
    suggestions,
    severity,
    detail: error.response?.data?.detail || error.message,
    timestamp: new Date().toISOString(),
    canRetry: ['NETWORK_ERROR', 'TIMEOUT', 'SERVER_ERROR'].includes(errorType),
    canUseFallback: ['NETWORK_ERROR', 'SERVER_ERROR', 'TIMEOUT', 'MODEL_NOT_LOADED'].includes(errorType),
  };
};

/**
 * 格式化错误消息用于显示
 */
export const formatErrorMessage = (error) => {
  const report = generateErrorReport(error);

  let message = `❌ ${report.description}\n\n`;
  message += `🔍 错误类型: ${report.type}\n`;
  message += `⏰ 时间: ${report.timestamp}\n`;

  if (report.detail) {
    message += `📝 详情: ${report.detail}\n`;
  }

  if (report.suggestions.length > 0) {
    message += `\n💡 建议解决方案:\n`;
    report.suggestions.forEach((suggestion, idx) => {
      message += `  ${idx + 1}. ${suggestion}\n`;
    });
  }

  if (report.canRetry) {
    message += `\n🔄 您可以稍后重试此操作`;
  }

  if (report.canUseFallback) {
    message += `\n🧮 您也可以使用本地估算功能（精度较低）`;
  }

  return message;
};

/**
 * 检查是否应该启用降级预测
 */
export const shouldEnableFallback = (error) => {
  const report = generateErrorReport(error);
  return report.canUseFallback;
};

export default {
  ErrorTypes,
  identifyError,
  getErrorDescription,
  getSolutionSuggestions,
  getErrorSeverity,
  generateErrorReport,
  formatErrorMessage,
  shouldEnableFallback,
};
