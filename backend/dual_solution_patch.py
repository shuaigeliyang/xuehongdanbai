"""
双溶液支持补丁 - 添加到main.py
作者: 哈雷酱大小姐 (￣▽￣)／
"""

from fastapi import HTTPException
from typing import Literal
import pickle
import numpy as np
from pathlib import Path

# 双溶液配置
SOLUTION_CONFIGS = {
    'solution_a': {
        'name': '溶液A',
        'description': '2025年7月31日测量的标准溶液',
        'model_file': 'solution_a_svr.pkl',
        'scaler_file': 'solution_a_scaler.pkl',
        'accuracy': 0.9657
    },
    'solution_b': {
        'name': '溶液B',
        'description': '2025年8月12日测量的实验溶液',
        'model_file': 'solution_b_svr.pkl',
        'scaler_file': 'solution_b_scaler.pkl',
        'accuracy': 0.9987
    }
}

# 全局变量存储双溶液模型
dual_solution_models = {}
dual_solution_scalers = {}

def load_dual_solution_models():
    """加载双溶液模型"""
    global dual_solution_models, dual_solution_scalers

    backend_dir = Path(__file__).parent
    models_dir = backend_dir.parent / 'models'

    try:
        for sol_key, config in SOLUTION_CONFIGS.items():
            # 加载模型
            model_path = models_dir / config['model_file']
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    dual_solution_models[sol_key] = pickle.load(f)
                logger.info(f"✓ {config['name']} 模型加载成功")

            # 加载标准化器
            scaler_path = models_dir / config['scaler_file']
            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    dual_solution_scalers[sol_key] = pickle.load(f)

        logger.info("双溶液模型加载完成！")
        return True
    except Exception as e:
        logger.error(f"双溶液模型加载失败: {e}")
        return False

def extract_features(a375, a405, a450):
    """特征提取"""
    eps = 0.001
    return np.array([[
        a375, a405, a450,
        a405 / (a375 + eps),
        a450 / (a405 + eps),
        a450 / (a375 + eps),
        a405 - a375,
        a450 - a405,
        a375 + a405 + a450
    ]])

# ==================== 新增API接口 ====================

@app.get("/api/solutions")
async def get_solutions():
    """获取所有溶液信息"""
    return {
        "solutions": {
            key: {
                "name": config["name"],
                "description": config["description"],
                "accuracy": config["accuracy"],
                "available": key in dual_solution_models
            }
            for key, config in SOLUTION_CONFIGS.items()
        },
        "count": len(SOLUTION_CONFIGS)
    }

@app.post("/api/predict/dual")
async def predict_dual_solution(
    a375: float,
    a405: float,
    a450: float,
    solution_type: Literal['solution_a', 'solution_b']
):
    """
    双溶液预测接口

    Args:
        a375: 375nm吸光度
        a405: 405nm吸光度
        a450: 450nm吸光度
        solution_type: 溶液类型
    """
    if solution_type not in dual_solution_models:
        raise HTTPException(
            status_code=400,
            detail=f"溶液类型 {solution_type} 的模型未加载"
        )

    try:
        # 特征提取
        features = extract_features(a375, a405, a450)

        # 标准化
        scaler = dual_solution_scalers.get(solution_type)
        if scaler:
            features_scaled = scaler.transform(features)
        else:
            features_scaled = features

        # 预测
        model = dual_solution_models[solution_type]
        concentration = model.predict(features_scaled)[0]

        config = SOLUTION_CONFIGS[solution_type]

        return {
            "concentration": round(float(concentration), 4),
            "solution_type": solution_type,
            "solution_name": config["name"],
            "model_type": "svr",
            "accuracy": config["accuracy"],
            "input_absorbance": {"a375": a375, "a405": a405, "a450": a450},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 在lifespan函数中添加
# 在启动时调用 load_dual_solution_models()
