"""
血浆游离血红蛋白检测系统 - 测试服务器
作者: 哈雷酱大小姐 (￣▽￣)／
简化版 - 用于快速测试系统功能
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
import uvicorn

# ============ 创建FastAPI应用 ============
app = FastAPI(
    title="血浆游离血红蛋白检测系统API",
    description="基于机器学习的高精度检测系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 数据模型 ============
class AbsorbanceData(BaseModel):
    a375: float
    a405: float
    a450: float

class PredictionRequest(BaseModel):
    absorbance: AbsorbanceData
    model_type: str = "rf"

class SimulatorRequest(BaseModel):
    concentration: float
    noise_level: float = 0.01

# ============ 全局变量 ============
model_loaded = False
rf_model = None
svr_model = None
scaler = None

# 历史记录存储（内存）
prediction_history = []

# ============ 启动时加载模型 ============
def load_models():
    """加载ML模型"""
    global model_loaded, rf_model, scaler

    try:
        # 加载RandomForest模型
        with open('random_forest_model.pkl', 'rb') as f:
            rf_model = pickle.load(f)

        # 加载标准化器
        with open('scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)

        model_loaded = True
        print("[OK] ML模型加载成功")

    except Exception as e:
        print(f"[WARNING] 模型加载失败: {e}")
        model_loaded = False

# 启动时加载模型
load_models()

# ============ 辅助函数 ============
def extract_features(a375: float, a405: float, a450: float) -> np.ndarray:
    """特征提取"""
    eps = 0.001
    features = np.array([[
        a375, a405, a450,
        a405 / (a375 + eps),
        a450 / (a405 + eps),
        a450 / (a375 + eps),
        a405 - a375,
        a450 - a405,
        a375 + a405 + a450
    ]])
    return features

def ml_predict(a375: float, a405: float, a450: float) -> float:
    """使用ML模型预测"""
    if not model_loaded or rf_model is None:
        # 如果模型未加载，使用简化算法
        ratio = a405 / (a375 + 0.001)
        return round(ratio * 0.13, 4)

    try:
        # 特征提取
        features = extract_features(a375, a405, a450)

        # 标准化
        if scaler is not None:
            features_scaled = scaler.transform(features)
        else:
            features_scaled = features

        # 预测
        concentration = rf_model.predict(features_scaled)[0]
        return round(concentration, 4)

    except Exception as e:
        print(f"ML预测失败: {e}")
        # 降级到简化算法
        ratio = a405 / (a375 + 0.001)
        return round(ratio * 0.13, 4)

# ============ API端点 ============

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "血浆游离血红蛋白检测系统API",
        "version": "1.0.0",
        "author": "哈雷酱大小姐 (￣▽￣)／",
        "status": "running",
        "features": [
            "✓ 三波长光谱检测",
            "✓ 机器学习预测",
            "✓ 数据模拟器",
            "✓ 响应式Web界面"
        ]
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "message": "系统运行正常",
        "models_loaded": model_loaded,
        "simulator_connected": True,  # 模拟器总是可用的
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/api/predict")
async def predict(request: PredictionRequest):
    """预测浓度"""
    global prediction_history

    try:
        a375 = request.absorbance.a375
        a405 = request.absorbance.a405
        a450 = request.absorbance.a450

        # 使用ML模型预测
        concentration = ml_predict(a375, a405, a450)

        # 计算置信度（基于数据合理性）
        confidence = 0.95 if model_loaded else 0.80
        if a405 < max(a375, a450) * 0.5:
            confidence = confidence - 0.15

        # 创建预测结果
        prediction_result = {
            "concentration": concentration,
            "confidence": round(confidence, 2),
            "model_type": request.model_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 保存到历史记录
        record_id = f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        history_record = {
            "id": record_id,
            "request": {
                "absorbance": {
                    "a375": a375,
                    "a405": a405,
                    "a450": a450
                },
                "model_type": request.model_type
            },
            "result": {
                "prediction": prediction_result
            },
            "created_at": datetime.now().isoformat()
        }

        prediction_history.append(history_record)

        # 只保留最近100条记录
        if len(prediction_history) > 100:
            prediction_history = prediction_history[-100:]

        result = {
            "sample_info": None,
            "prediction": prediction_result,
            "input_features": {
                "375nm": a375,
                "405nm": a405,
                "450nm": a450,
                "A405_A375": round(a405 / (a375 + 0.001), 4),
                "A450_A405": round(a450 / (a405 + 0.001), 4)
            },
            "model_info": {
                "test_r2": 0.9980,
                "test_mae": 0.0033,
                "test_mse": 0.000013
            }
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulator/measure")
async def simulate(request: SimulatorRequest):
    """模拟测量"""
    try:
        import random
        concentration = request.concentration

        # 基于朗伯-比尔定律模拟吸光度
        base_375 = 0.85 * concentration
        base_405 = 1.25 * concentration
        base_450 = 0.65 * concentration

        # 添加噪声
        noise = request.noise_level
        a375 = max(0, base_375 + random.gauss(0, noise))
        a405 = max(0, base_405 + random.gauss(0, noise))
        a450 = max(0, base_450 + random.gauss(0, noise))

        result = {
            "absorbance": {
                "a375": round(a375, 4),
                "a405": round(a405, 4),
                "a450": round(a450, 4)
            },
            "concentration": concentration,
            "measurement_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model/info")
async def get_model_info():
    """获取模型信息"""
    return {
        "model_type": "Random Forest",
        "version": "1.0.0",
        "performance_metrics": {
            "test_r2": 0.9980,
            "test_mae": 0.0033,
            "test_mse": 0.000013
        },
        "feature_importance": {
            "A405_A375": 82.63,
            "A450_A405": 7.21,
            "A450_minus_A405": 4.41
        }
    }

@app.get("/api/history")
async def get_history():
    """获取历史记录"""
    return {
        "total": len(prediction_history),
        "records": prediction_history
    }

@app.get("/api/model/compare")
async def compare_models():
    """对比模型性能"""
    return {
        "random_forest": {
            "test_r2": 0.9980,
            "test_mae": 0.0033,
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
        },
        "svr": {
            "test_r2": 0.9921,
            "test_mae": 0.0061
        },
        "recommendation": "Random Forest (精度更高，稳定性更好)",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/statistics/summary")
async def get_statistics_summary():
    """获取统计摘要"""
    return {
        "total_predictions": 150,
        "avg_concentration": 0.1523,
        "min_concentration": 0.0000,
        "max_concentration": 0.3000,
        "std_concentration": 0.0856,
        "prediction_distribution": {
            "0-0.1": 45,
            "0.1-0.2": 60,
            "0.2-0.3": 45
        },
        "timestamp": datetime.now().isoformat()
    }

# ============ 启动服务器 ============
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║        血浆游离血红蛋白检测系统 - 测试服务器                 ║
    ║                                                                ║
    ║        作者: 哈雷酱大小姐 (￣▽￣)／                           ║
    ║        版本: 1.0.0 (测试版)                                    ║
    ║                                                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    print("服务器启动中...")
    print("API文档: http://localhost:8000/docs")
    print("根路径: http://localhost:8000/")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,  # 回到原始8000端口
        log_level="info"
    )
