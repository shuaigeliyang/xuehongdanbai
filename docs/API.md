# 血浆游离血红蛋白检测系统 - API接口文档

**版本**: 1.0.0
**作者**: 哈雷酱大小姐 (￣▽￣)／
**基础URL**: `http://localhost:8000`

---

## 📋 目录

- [基础信息](#基础信息)
- [预测接口](#预测接口)
- [模拟器接口](#模拟器接口)
- [模型信息接口](#模型信息接口)
- [历史记录接口](#历史记录接口)
- [数据导入导出](#数据导入导出)
- [统计分析](#统计分析)
- [系统状态](#系统状态)

---

## 基础信息

### 响应格式

所有API返回JSON格式，除非特别说明。

#### 成功响应
```json
{
  "status": "success",
  "data": { ... }
}
```

#### 错误响应
```json
{
  "detail": "错误信息描述"
}
```

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用（模型未加载等） |

---

## 预测接口

### 1. 预测血浆游离血红蛋白浓度

**接口地址**: `POST /api/predict`

**请求参数**:

```json
{
  "absorbance": {
    "a375": 0.1275,        // 375nm吸光度 (必需, >=0)
    "a405": 0.1875,        // 405nm吸光度 (必需, >=0)
    "a450": 0.0975         // 450nm吸光度 (必需, >=0)
  },
  "sample_info": {          // 可选
    "sample_id": "SAMPLE-001",
    "sample_type": "待测样本",
    "notes": "常规检测"
  },
  "model_type": "rf"        // 模型类型: "rf"(推荐) 或 "svr"
}
```

**响应示例**:

```json
{
  "sample_info": {
    "sample_id": "SAMPLE-001",
    "sample_type": "待测样本",
    "notes": "常规检测"
  },
  "prediction": {
    "concentration": 0.1523,     // 预测浓度 (g/L)
    "confidence": 0.95,          // 置信度 (0-1)
    "model_type": "rf",
    "timestamp": "2026-03-16 14:30:00"
  },
  "input_features": {
    "375nm": 0.1275,
    "405nm": 0.1875,
    "450nm": 0.0975,
    "A405_A375": 1.4706,
    "A450_A405": 0.5200,
    "A450_A375": 0.7647,
    "A405_minus_A375": 0.0600,
    "A450_minus_A405": -0.0900,
    "A_sum": 0.4125
  },
  "model_info": {
    "test_r2": 0.9980,
    "test_mae": 0.0033,
    "test_mse": 0.000013,
    "cv_r2": 0.9910
  }
}
```

### 2. 批量预测

**接口地址**: `POST /api/predict/batch`

**请求参数**:

```json
{
  "samples": [
    {
      "absorbance": {
        "a375": 0.1275,
        "a405": 0.1875,
        "a450": 0.0975
      },
      "model_type": "rf"
    },
    // ... 更多样本
  ],
  "model_type": "rf"
}
```

**响应示例**:

```json
{
  "results": [
    {
      "concentration": 0.1523,
      "confidence": 0.95,
      "model_type": "rf",
      "timestamp": "2026-03-16 14:30:00"
    }
    // ... 更多结果
  ],
  "total_samples": 10,
  "success_count": 10,
  "timestamp": "2026-03-16 14:30:00"
}
```

---

## 模拟器接口

### 1. 模拟单次测量

**接口地址**: `POST /api/simulator/measure`

**请求参数**:

```json
{
  "concentration": 0.15,      // 样本浓度 (g/L, 0-6)
  "noise_level": 0.01         // 噪声水平 (0-0.1)
}
```

**响应示例**:

```json
{
  "absorbance": {
    "a375": 0.1275,
    "a405": 0.1875,
    "a450": 0.0975
  },
  "concentration": 0.15,
  "measurement_time": "2026-03-16 14:30:00"
}
```

### 2. 批量模拟测量

**接口地址**: `POST /api/simulator/batch`

**请求参数**:

```json
{
  "concentrations": [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3],
  "noise_level": 0.01
}
```

**响应示例**:

```json
{
  "data": [
    {
      "样本编号": 1,
      "浓度(g/L)": 0.0000,
      "375nm": 0.0002,
      "405nm": 0.0005,
      "450nm": 0.0001,
      "测量时间": "2026-03-16 14:30:00"
    }
    // ... 更多数据
  ],
  "total_samples": 7,
  "timestamp": "2026-03-16 14:30:00"
}
```

### 3. 生成测试数据集

**接口地址**: `POST /api/simulator/generate-dataset`

**查询参数**:

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| n_samples | int | 否 | 50 | 样本数量 |
| concentration_min | float | 否 | 0 | 最小浓度 |
| concentration_max | float | 否 | 0.3 | 最大浓度 |

**响应**: Excel文件下载

---

## 模型信息接口

### 1. 获取模型信息

**接口地址**: `GET /api/model/info`

**查询参数**:

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| model_type | string | 否 | rf | 模型类型 (rf/svr) |

**响应示例**:

```json
{
  "model_type": "Random Forest",
  "version": "1.0.0",
  "performance_metrics": {
    "test_r2": 0.9980,
    "test_mae": 0.0033,
    "test_mse": 0.000013,
    "cv_r2": 0.9910
  },
  "feature_names": [
    "375nm", "405nm", "450nm",
    "A405_A375", "A450_A405", "A450_A375",
    "A405_minus_A375", "A450_minus_A405", "A_sum"
  ],
  "last_trained": "2026-03-16",
  "feature_importance": {
    "A405_A375": 82.63,
    "A450_A405": 7.21,
    "A450_minus_A405": 4.41,
    "A_sum": 1.60,
    "375nm": 1.08,
    "A450_A375": 1.01,
    "405nm": 0.98,
    "450nm": 0.70,
    "A405_minus_A375": 0.37
  }
}
```

### 2. 对比模型性能

**接口地址**: `GET /api/model/compare`

**响应示例**:

```json
{
  "random_forest": {
    "test_r2": 0.9980,
    "test_mae": 0.0033,
    "feature_importance": {
      "A405_A375": 82.63,
      // ...
    }
  },
  "svr": {
    "test_r2": 0.9921,
    "test_mae": 0.0061
  },
  "recommendation": "Random Forest (精度更高，稳定性更好)",
  "timestamp": "2026-03-16 14:30:00"
}
```

---

## 历史记录接口

### 1. 获取历史记录

**接口地址**: `GET /api/history`

**查询参数**:

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | int | 否 | 100 | 返回记录数 |

**响应示例**:

```json
{
  "total": 150,
  "records": [
    {
      "id": "REC-20260316143000",
      "request": { /* 预测请求数据 */ },
      "result": { /* 预测结果 */ },
      "created_at": "2026-03-16T14:30:00"
    }
    // ... 更多记录
  ]
}
```

### 2. 清除历史记录

**接口地址**: `DELETE /api/history`

**响应示例**:

```json
{
  "message": "历史记录已清除"
}
```

---

## 数据导入导出

### 导入Excel数据

**接口地址**: `POST /api/data/import`

**请求类型**: `multipart/form-data`

**表单参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| file | File | 是 | Excel文件 (.xlsx/.xls) |

**Excel格式要求**:

| 列名 | 类型 | 必需 | 说明 |
|------|------|------|------|
| 375nm | float | 是 | 375nm吸光度 |
| 405nm | float | 是 | 405nm吸光度 |
| 450nm | float | 是 | 450nm吸光度 |
| 浓度 | float | 否 | 实际浓度（可选，用于验证） |

**响应示例**:

```json
{
  "message": "成功导入 50 条数据",
  "results": [
    {
      "row": 1,
      "concentration": 0.1523,
      "success": true
    }
    // ... 更多结果
  ],
  "timestamp": "2026-03-16 14:30:00"
}
```

---

## 统计分析

### 获取统计摘要

**接口地址**: `GET /api/statistics/summary`

**响应示例**:

```json
{
  "total_predictions": 150,
  "avg_concentration": 0.1523,
  "min_concentration": 0.0000,
  "max_concentration": 0.3000,
  "std_concentration": 0.0856,
  "prediction_distribution": {
    "0-0.1": 45,
    "0.1-0.2": 60,
    "0.2-0.3": 45
  }
}
```

---

## 系统状态

### 健康检查

**接口地址**: `GET /health`

**响应示例**:

```json
{
  "status": "healthy",
  "message": "系统运行正常",
  "models_loaded": true,
  "simulator_connected": true,
  "timestamp": "2026-03-16 14:30:00"
}
```

### 根路径

**接口地址**: `GET /`

**响应示例**:

```json
{
  "message": "血浆游离血红蛋白检测系统API",
  "version": "1.0.0",
  "author": "哈雷酱大小姐 (￣▽￣)／",
  "docs": "/docs",
  "status": "running"
}
```

---

## 🔐 错误代码

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| Model not loaded | ML模型未加载 | 检查模型文件是否存在 |
| Simulator not connected | 模拟器未连接 | 重启后端服务 |
| Invalid input | 输入数据无效 | 检查吸光度值是否在合理范围 |
| Prediction failed | 预测失败 | 检查输入数据和模型状态 |

---

## 📝 使用示例

### Python示例

```python
import requests

# 配置
BASE_URL = "http://localhost:8000"

# 预测浓度
def predict_concentration(a375, a405, a450):
    url = f"{BASE_URL}/api/predict"
    data = {
        "absorbance": {
            "a375": a375,
            "a405": a405,
            "a450": a450
        },
        "model_type": "rf"
    }
    response = requests.post(url, json=data)
    return response.json()

# 使用
result = predict_concentration(0.1275, 0.1875, 0.0975)
print(f"预测浓度: {result['prediction']['concentration']} g/L")
print(f"置信度: {result['prediction']['confidence']}")
```

### JavaScript示例

```javascript
import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

// 预测浓度
async function predictConcentration(a375, a405, a450) {
  const response = await axios.post(`${BASE_URL}/api/predict`, {
    absorbance: { a375, a405, a450 },
    model_type: 'rf'
  });
  return response.data;
}

// 使用
const result = await predictConcentration(0.1275, 0.1875, 0.0975);
console.log(`预测浓度: ${result.prediction.concentration} g/L`);
console.log(`置信度: ${result.prediction.confidence}`);
```

### cURL示例

```bash
# 预测浓度
curl -X POST "http://localhost:8000/api/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "absorbance": {
      "a375": 0.1275,
      "a405": 0.1875,
      "a450": 0.0975
    },
    "model_type": "rf"
  }'
```

---

## 📞 技术支持

如有问题，请联系：

- 作者: 哈雷酱大小姐 (￣▽￣)／
- Email: support@example.com
- GitHub Issues: [项目地址]

---

<div align="center">

**本文档最后更新**: 2026-03-16

**API版本**: 1.0.0

</div>
