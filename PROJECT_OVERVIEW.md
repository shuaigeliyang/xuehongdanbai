# 血浆游离血红蛋白检测系统

基于机器学习的血浆游离血红蛋白(Free Hemoglobin, FHb)浓度预测系统，支持双溶液独立模型检测。

## 项目概述

本项目实现了一个高精度的血浆游离血红蛋白浓度预测系统，采用三波长光谱检测技术（375nm、405nm、450nm），结合支持向量机回归（SVR）机器学习算法，实现了对不同类型溶液的高精度浓度预测。

### 核心特性

- **三波长光谱检测**：利用375nm、405nm、450nm三个波长进行吸光度测量
- **双溶液独立模型**：针对不同类型的溶液训练独立的预测模型
- **高精度预测**：溶液A R²=0.9657，溶液B R²=0.9987
- **RESTful API**：提供完整的API接口，支持前后端分离
- **可视化界面**：提供友好的Web操作界面

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (React + Ant Design)              │
│                   http://localhost:3000                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI + Python)                   │
│                    http://localhost:8000                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐    ┌─────────────┐                       │
│   │   溶液A      │    │   溶液B      │                       │
│   │   SVR模型    │    │   SVR模型    │                       │
│   │  (高吸光度)  │    │  (低吸光度)  │                       │
│   └─────────────┘    └─────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 技术栈

### 后端
- **框架**: FastAPI 0.109.0
- **服务器**: Uvicorn 0.27.0
- **机器学习**: scikit-learn 1.4.0
- **数据处理**: pandas 2.2.0, numpy 1.26.3
- **数据库**: MySQL (可选), SQLite (默认)
- **认证**: JWT Token

### 前端
- **框架**: React 18.2.0
- **UI库**: Ant Design 5.12.0
- **图表**: ECharts 5.4.3
- **HTTP客户端**: Axios 1.6.2

---

## 项目结构

```
血浆游离血红蛋白检测系统/
├── backend/                          # 后端目录
│   ├── main.py                       # 主入口文件
│   ├── api_models.py                 # API数据模型
│   ├── model_inference.py             # 模型推理引擎
│   ├── dual_solution_inference.py     # 双溶液推理引擎
│   ├── dual_solution_api.py          # 双溶液API（独立服务）
│   ├── simulator.py                   # 光谱仪模拟器
│   ├── database.py                   # 数据库模型
│   ├── auth.py                       # 认证模块
│   ├── pdf_generator.py              # PDF报告生成
│   ├── monitoring.py                  # 监控模块
│   ├── requirements.txt              # Python依赖
│   ├── models/                       # 训练好的模型
│   │   ├── solution_a_svr.pkl        # 溶液A SVR模型
│   │   ├── solution_a_scaler.pkl     # 溶液A标准化器
│   │   ├── solution_b_svr.pkl        # 溶液B SVR模型
│   │   └── solution_b_scaler.pkl     # 溶液B标准化器
│   └── data/                         # 数据目录
│
├── frontend/                         # 前端目录
│   ├── src/
│   │   ├── App.js                    # 主应用组件
│   │   ├── App.css                   # 主样式
│   │   ├── components/
│   │   │   ├── DetectionPanel.js     # 检测面板
│   │   │   ├── SimulatorPanel.js      # 模拟器面板
│   │   │   ├── HistoryPanel.js        # 历史记录
│   │   │   └── StatisticsPanel.js     # 统计分析
│   │   ├── services/
│   │   │   └── api.js                # API服务
│   │   └── utils/
│   │       └── errorHelper.js        # 错误处理
│   └── package.json                  # Node依赖
│
├── models/                           # 模型文件（根目录）
│   ├── solution_a_svr.pkl
│   ├── solution_a_scaler.pkl
│   ├── solution_b_svr.pkl
│   └── solution_b_scaler.pkl
│
├── processed_data/                    # 处理后的数据
│   ├── solution_a_processed.csv
│   ├── solution_b_processed.csv
│   └── comparison_report.json
│
├── 双溶液数据预处理脚本.py            # 数据预处理脚本
├── 双溶液模型训练脚本.py              # 模型训练脚本
├── 启动系统.bat                       # Windows启动脚本
├── README.md                          # 项目说明
└── PROJECT_OVERVIEW.md                # 项目概述（本文件）
```

---

## 核心逻辑

### 1. 双溶液检测原理

不同溶液的吸光度水平差异巨大，因此需要分别训练独立的模型：

| 溶液 | 平均375nm吸光度 | 适用场景 | R² |
|------|----------------|---------|-----|
| 溶液A | 1.9702 | 高吸光度样品 | 0.9657 |
| 溶液B | 0.0875 | 低吸光度样品 | 0.9987 |

### 2. 特征工程

从原始的3个波长吸光度特征扩展到9个特征：

```python
特征 = [
    原始特征: 375nm, 405nm, 450nm,
    比值特征: A405/A375, A450/A405, A450/A375,
    差值特征: A405-A375, A450-A405,
    总和特征: A_sum
]
```

### 3. 预测流程

```
输入吸光度数据
    ↓
特征工程（提取9个特征）
    ↓
选择对应溶液的标准化器
    ↓
数据标准化
    ↓
加载对应溶液的SVR模型
    ↓
模型预测
    ↓
返回预测浓度和置信度
```

### 4. API接口

#### 健康检查
```
GET /health
```

#### 获取溶液信息
```
GET /api/solutions
```

#### 双溶液预测
```
POST /api/predict/dual
{
    "a375": 1.9702,
    "a405": 0.6393,
    "a450": 1.0960,
    "solution_type": "solution_a",
    "sample_id": "TEST-001"
}
```

---

## 安装部署

### 环境要求

- Python 3.9+
- Node.js 16+
- npm 或 yarn

### 1. 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
python main.py
```

### 2. 前端安装

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动前端
npm start
```

### 3. 一键启动（Windows）

双击运行 `启动系统.bat`

---

## 使用指南

### 启动服务

1. **启动后端**（终端1）：
```bash
cd backend
python main.py
```

2. **启动前端**（终端2）：
```bash
cd frontend
npm start
```

3. **访问系统**：
- 前端界面：http://localhost:3000
- API文档：http://localhost:8000/docs

### 双溶液检测

1. 在检测面板中，勾选"启用双溶液检测模式"
2. 选择溶液类型：
   - **溶液A**：适用于高吸光度样品
   - **溶液B**：适用于低吸光度样品
3. 输入吸光度数据
4. 点击"开始预测"

### 示例数据

**溶液A（高吸光度）**：
- 375nm: 1.9702
- 405nm: 0.6393
- 450nm: 1.0960

**溶液B（低吸光度）**：
- 375nm: 0.0875
- 405nm: 0.0146
- 450nm: 0.0535

---

## 模型性能

### 溶液A (标准溶液)
| 指标 | SVR模型 |
|------|---------|
| R² | 0.9657 |
| MAE | 0.0043 g/L |
| MSE | 0.000018 |

### 溶液B (实验溶液)
| 指标 | SVR模型 |
|------|---------|
| R² | 0.9987 |
| MAE | 0.0030 g/L |
| MSE | 0.000009 |

---

## ⚠️ 数据限制说明

**重要提醒：由于当前训练数据量较少，模型存在以下限制：**

1. **数据量**
   - 溶液A: 6个样本（浓度点）
   - 溶液B: 5个样本（浓度点）

2. **建议**
   - 预测结果仅供参考，建议临床验证
   - 建议收集更多实验数据（每种溶液20-30个样本）
   - 每个浓度点进行3-5次重复测量

3. **适用浓度范围**
   - 溶液A: 0-0.3 g/L
   - 溶液B: 0-0.23 g/L
   - 超出范围预测可能不准确

---

## 数据库配置

### Q1: 后端启动失败？
确保已安装所有依赖：`pip install -r requirements.txt`

### Q2: 前端无法连接后端？
检查后端是否正常运行在 http://localhost:8000

### Q3: 模型预测结果为0？
检查吸光度数据是否在合理范围内（0-3）

### Q4: 如何训练自己的模型？
运行 `双溶液模型训练脚本.py` 进行模型训练

---

## 开发团队

- **开发者**: 哈雷酱大小姐 (￣▽￣)／
- **版本**: 2.0.0
- **更新日期**: 2026-04-05

---

## 许可证

MIT License

---

**本项目基于科学研究目的开发，仅供学习和参考使用。**
