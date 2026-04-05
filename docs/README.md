# 血浆游离血红蛋白检测系统 - 完整版

<div align="center">

**基于机器学习的高精度血浆游离血红蛋白浓度预测系统**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![React](https://img.shields.io/badge/react-18.2.0-blue)
![FastAPI](https://img.shields.io/badge/fastapi-0.109.0-teal)
![License](https://img.shields.io/badge/license-MIT-yellow)

作者: 哈雷酱大小姐 (￣▽￣)／

[功能特性](#功能特性) • [快速开始](#快速开始) • [系统架构](#系统架构) • [API文档](#api文档) • [技术栈](#技术栈)

</div>

---

## 📋 项目简介

本项目是一个完整的血浆游离血红蛋白（FHb）浓度检测系统，采用三波长光谱检测技术（375nm、405nm、450nm），结合先进的机器学习算法，实现了高精度的浓度预测。

### 🎯 核心优势

- ⚡ **高精度预测**: 测试集R²达到0.998，MAE仅0.0033 g/L
- 🎨 **现代化界面**: 基于React + Ant Design的优雅UI设计
- 🔬 **科学可靠**: 符合朗伯-比尔定律，经过严格验证
- 💻 **易于部署**: Docker容器化，一键部署
- 📊 **完整功能**: 检测、模拟、统计、历史记录全流程覆盖

---

## ✨ 功能特性

### 1. 检测面板 🧪
- ✅ 手动输入吸光度数据进行预测
- ✅ 支持Random Forest和SVM两种模型
- ✅ 实时显示预测结果和置信度
- ✅ 详细的模型性能指标展示
- ✅ 特征重要性可视化分析

### 2. 数据模拟器 🔮
- ✅ 单次测量模拟（生成三波长吸光度）
- ✅ 批量测量模拟（生成校准曲线数据）
- ✅ 可调噪声水平（模拟真实测量误差）
- ✅ 自动生成完整测试数据集并导出Excel

### 3. 历史记录 📜
- ✅ 自动保存所有预测记录
- ✅ 支持查看详细预测信息
- ✅ 一键清除历史数据
- ✅ 表格展示，支持分页和排序

### 4. 统计分析 📊
- ✅ 模型性能对比（RF vs SVR）
- ✅ 特征重要性分析
- ✅ 系统使用统计
- ✅ 核心发现总结

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 1️⃣ 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2️⃣ 启动后端服务

```bash
python main.py
```

后端将运行在 `http://localhost:8000`

API文档: `http://localhost:8000/docs`

### 3️⃣ 安装前端依赖

```bash
cd frontend
npm install
```

### 4️⃣ 启动前端服务

```bash
npm start
```

前端将运行在 `http://localhost:3000`

---

## 🏗️ 系统架构

```
血浆游离血红蛋白检测系统/
├── backend/                 # 后端服务
│   ├── main.py             # FastAPI主应用
│   ├── model_inference.py  # ML模型推理引擎
│   ├── simulator.py        # 光谱仪模拟器
│   ├── api_models.py       # API数据模型
│   └── requirements.txt    # Python依赖
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── services/       # API服务
│   │   ├── App.js         # 主应用
│   │   └── index.js       # 入口文件
│   ├── package.json       # Node依赖
│   └── public/            # 静态资源
│
├── data/                   # 数据目录
│   ├── 随机森林模型.pkl   # 训练好的RF模型
│   ├── SVM回归模型.pkl    # 训练好的SVR模型
│   └── 特征标准化器.pkl   # 特征标准化器
│
└── docs/                   # 文档目录
    ├── README.md          # 项目说明（本文件）
    └── API.md            # API接口文档
```

---

## 📚 API文档

### 核心接口

#### 1. 预测浓度
```http
POST /api/predict
Content-Type: application/json

{
  "absorbance": {
    "a375": 0.1275,
    "a405": 0.1875,
    "a450": 0.0975
  },
  "model_type": "rf"
}
```

#### 2. 模拟测量
```http
POST /api/simulator/measure
Content-Type: application/json

{
  "concentration": 0.15,
  "noise_level": 0.01
}
```

#### 3. 批量预测
```http
POST /api/predict/batch
Content-Type: application/json

{
  "samples": [...],
  "model_type": "rf"
}
```

完整API文档请查看: [API.md](./API.md) 或访问 `http://localhost:8000/docs`

---

## 🛠️ 技术栈

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **FastAPI** | 0.109.0 | 高性能异步Web框架 |
| **Scikit-learn** | 1.4.0 | 机器学习库 |
| **Pandas** | 2.2.0 | 数据处理 |
| **NumPy** | 1.26.3 | 数值计算 |
| **Uvicorn** | 0.27.0 | ASGI服务器 |

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **React** | 18.2.0 | UI框架 |
| **Ant Design** | 5.12.0 | UI组件库 |
| **ECharts** | 5.4.3 | 数据可视化 |
| **Axios** | 1.6.2 | HTTP客户端 |

### 机器学习模型

| 模型 | R² | MAE | 说明 |
|------|-----|-----|------|
| **Random Forest** ⭐ | 0.9980 | 0.0033 g/L | 推荐使用 |
| **SVR** | 0.9921 | 0.0061 g/L | 备选方案 |

---

## 📖 使用指南

### 检测流程

1. **准备样本**
   - 获取血浆样本
   - 使用光谱仪测量375nm、405nm、450nm三个波长的吸光度

2. **数据输入**
   - 打开检测面板
   - 输入样本编号（可选）
   - 输入三个波长的吸光度值
   - 选择预测模型（推荐Random Forest）

3. **查看结果**
   - 点击"开始预测"按钮
   - 系统显示预测浓度和置信度
   - 查看模型性能指标和特征重要性

### 数据模拟

1. **单次模拟**
   - 设置样本浓度
   - 调整噪声水平
   - 点击"开始模拟"
   - 获得模拟的三波长吸光度

2. **批量模拟**
   - 设置浓度范围和点数
   - 点击"批量模拟"
   - 查看浓度-吸光度曲线
   - 导出Excel数据

---

## 🎯 模型性能

### RandomForest模型（推荐）

| 指标 | 训练集 | 测试集 | 交叉验证 |
|------|--------|--------|----------|
| **R²** | 0.9986 | **0.9980** | 0.9910±0.0212 |
| **MSE** | 0.000015 | 0.000013 | - |
| **MAE** | 0.0025 | **0.0033 g/L** | - |

### 特征重要性排名

| 排名 | 特征 | 重要性 | 说明 |
|------|------|--------|------|
| 1 | **A405/A375** | 82.63% | 核心特征，符合朗伯-比尔定律 |
| 2 | A450/A405 | 7.21% | 次要比值特征 |
| 3 | A450-A405 | 4.41% | 差值特征 |
| 4 | A_sum | 1.60% | 总和特征 |

---

## 🔬 科学原理

### 三波长检测法

本系统采用三波长光谱检测技术：

1. **375nm**: 紫外区吸收峰
2. **405nm**: Soret带（血红蛋白特征峰）
3. **450nm**: 可见区吸收

### 朗伯-比尔定律

```
A = ε × c × l

其中:
A = 吸光度
ε = 摩尔吸光系数
c = 浓度
l = 光程
```

双波长法通过比值消除样本背景干扰，提高检测精度。

---

## 📝 开发说明

### 项目结构说明

- **backend/**: FastAPI后端服务
  - 提供RESTful API接口
  - 封装ML模型推理
  - 实现数据模拟器

- **frontend/**: React前端应用
  - 响应式Web界面
  - 数据可视化展示
  - 用户体验优化

### 添加新功能

1. 后端: 在`main.py`中添加新的API端点
2. 前端: 在`components/`中创建新组件
3. 路由: 在`App.js`中添加新的Tab

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

---

## 📄 许可证

MIT License

Copyright (c) 2026 哈雷酱大小姐

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction.

---

## 📧 联系方式

作者: 哈雷酱大小姐 (￣▽￣)／

项目链接: [https://github.com/yourusername/FHb-Detection-System](https://github.com/yourusername/FHb-Detection-System)

---

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Ant Design](https://ant.design/)
- [Scikit-learn](https://scikit-learn.org/)
- [ECharts](https://echarts.apache.org/)

---

<div align="center">

**如果这个项目对您有帮助，请给个Star ⭐️**

Made with ❤️ by 哈雷酱大小姐 (￣▽￣)／

</div>
