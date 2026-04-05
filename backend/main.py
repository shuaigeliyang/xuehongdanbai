"""
血浆游离血红蛋白检测系统 - FastAPI主应用
作者: 哈雷酱大小姐 (￣▽￣)／
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import json
import logging
import pickle
import numpy as np

# 导入模块
from api_models import *
from model_inference import get_inference_engine
from simulator import SpectrometerSimulator, SpectralDataGenerator
import pandas as pd
import io

# 数据库相关导入
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import Base, PredictionRecord
from dotenv import load_dotenv
import os

load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
inference_engine = None
simulator = None

# 双溶液模型支持
dual_solution_models = {}
dual_solution_scalers = {}

SOLUTION_CONFIGS = {
    'solution_a': {
        'name': '溶液A',
        'description': '2025年7月31日测量的标准溶液',
        'model_file': 'solution_a_svr.pkl',
        'scaler_file': 'solution_a_scaler.pkl',
        'accuracy': 0.9657,
        'test_mae': 0.0043,  # SVR模型MAE
        'test_mse': 0.000018  # SVR模型MSE
    },
    'solution_b': {
        'name': '溶液B',
        'description': '2025年8月12日测量的实验溶液',
        'model_file': 'solution_b_svr.pkl',
        'scaler_file': 'solution_b_scaler.pkl',
        'accuracy': 0.9987,
        'test_mae': 0.0030,  # SVR模型MAE
        'test_mse': 0.000009  # SVR模型MSE
    }
}

# 数据库连接
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:root@localhost:3306/fhb_detection"
)
SYNC_DATABASE_URL = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global inference_engine, simulator

    logger.info("=" * 60)
    logger.info("血浆游离血红蛋白检测系统启动中...")
    logger.info("作者: 哈雷酱大小姐 (￣▽￣)／")
    logger.info("=" * 60)

    # 启动时初始化
    try:
        # 初始化推理引擎（使用绝对路径）
        logger.info("[1/2] 加载ML模型...")
        import os
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        inference_engine = get_inference_engine(backend_dir)
        logger.info("    ✓ ML模型加载成功")

        # 初始化模拟器
        logger.info("[2/3] 启动光谱仪模拟器...")
        simulator = SpectrometerSimulator()
        simulator.connect()
        logger.info("    ✓ 光谱仪模拟器已启动")

        # 加载双溶液模型
        logger.info("[3/3] 加载双溶液模型...")
        load_dual_solution_models()

        logger.info("\n系统启动完成！(￣▽￣)／")
        logger.info("API文档: http://localhost:8000/docs")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise

    yield

    # 关闭时清理
    logger.info("系统关闭中...")
    if simulator:
        simulator.disconnect()


# 创建FastAPI应用
app = FastAPI(
    title="血浆游离血红蛋白检测系统API",
    description="基于机器学习的血浆游离血红蛋白浓度预测系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 基础接口 ====================

@app.get("/", response_model=Dict)
async def root():
    """根路径"""
    return {
        "message": "血浆游离血红蛋白检测系统API",
        "version": "1.0.0",
        "author": "哈雷酱大小姐 (￣▽￣)／",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        message="系统运行正常",
        models_loaded=inference_engine is not None,
        simulator_connected=simulator is not None and simulator.is_connected,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


# ==================== 预测接口 ====================

@app.post("/api/predict", response_model=DetailedPrediction)
async def predict_concentration(request: PredictionRequest):
    """
    预测血浆游离血红蛋白浓度

    Args:
        request: 预测请求数据

    Returns:
        详细预测结果
    """
    try:
        # 提取吸光度数据
        a375 = request.absorbance.a375
        a405 = request.absorbance.a405
        a450 = request.absorbance.a450

        # 验证输入
        is_valid, error_msg = inference_engine.validate_input(a375, a405, a450)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # 执行预测
        concentration, details = inference_engine.predict(
            a375, a405, a450,
            request.model_type
        )

        # 构建响应
        result = DetailedPrediction(
            sample_info=request.sample_info,
            prediction=PredictionResult(
                concentration=round(concentration, 4),
                confidence=round(details['confidence'], 4),
                model_type=request.model_type,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ),
            input_features=details['input_features'],
            model_info=details['model_metrics']
        )

        # 保存历史记录到数据库
        try:
            db = SessionLocal()
            record = PredictionRecord(
                sample_id=request.sample_info.sample_id if request.sample_info else None,
                sample_type=request.sample_info.sample_type if request.sample_info else "待测样本",
                notes=request.sample_info.notes if request.sample_info else None,
                a375=a375,
                a405=a405,
                a450=a450,
                predicted_concentration=round(concentration, 4),
                confidence=round(details['confidence'], 4),
                model_type=request.model_type,
                input_features=details['input_features'],
                created_at=datetime.now()
            )
            db.add(record)
            db.commit()
            db.close()
        except Exception as db_error:
            logger.warning(f"保存到数据库失败: {db_error}")

        logger.info(f"预测成功: {concentration:.4f} g/L (模型: {request.model_type})")
        return result

    except Exception as e:
        logger.error(f"预测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict/batch", response_model=BatchPredictionResponse)
async def batch_predict(request: BatchPredictionRequest):
    """
    批量预测

    Args:
        request: 批量预测请求

    Returns:
        批量预测结果
    """
    try:
        results = []
        success_count = 0

        for sample_req in request.samples:
            try:
                a375 = sample_req.absorbance.a375
                a405 = sample_req.absorbance.a405
                a450 = sample_req.absorbance.a450

                # 验证输入
                is_valid, error_msg = inference_engine.validate_input(a375, a405, a450)
                if not is_valid:
                    results.append(PredictionResult(
                        concentration=0,
                        confidence=0,
                        model_type=sample_req.model_type,
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    continue

                # 预测
                concentration, details = inference_engine.predict(
                    a375, a405, a450,
                    sample_req.model_type
                )

                results.append(PredictionResult(
                    concentration=round(concentration, 4),
                    confidence=round(details['confidence'], 4),
                    model_type=sample_req.model_type,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                success_count += 1

            except Exception as e:
                logger.error(f"样本预测失败: {e}")
                results.append(PredictionResult(
                    concentration=0,
                    confidence=0,
                    model_type=sample_req.model_type,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

        response = BatchPredictionResponse(
            results=results,
            total_samples=len(request.samples),
            success_count=success_count,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        logger.info(f"批量预测完成: {success_count}/{len(request.samples)} 成功")
        return response

    except Exception as e:
        logger.error(f"批量预测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 模拟器接口 ====================

@app.post("/api/simulator/measure", response_model=SimulatorResponse)
async def simulate_measurement(request: SimulatorRequest):
    """
    模拟光谱仪测量

    Args:
        request: 模拟器请求

    Returns:
        测量结果
    """
    try:
        if simulator is None or not simulator.is_connected:
            raise HTTPException(status_code=503, detail="模拟器未连接")

        # 执行测量
        absorbance = simulator.measure_sample(request.concentration)

        result = SimulatorResponse(
            absorbance=AbsorbanceData(
                a375=absorbance[375],
                a405=absorbance[405],
                a450=absorbance[450]
            ),
            concentration=request.concentration,
            measurement_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        logger.info(f"模拟测量: {request.concentration} g/L")
        return result

    except Exception as e:
        logger.error(f"模拟测量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulator/batch")
async def batch_simulate(request: BatchSimulatorRequest):
    """
    批量模拟测量

    Args:
        request: 批量模拟请求

    Returns:
        测量结果DataFrame
    """
    try:
        if simulator is None or not simulator.is_connected:
            raise HTTPException(status_code=503, detail="模拟器未连接")

        results = []
        for i, conc in enumerate(request.concentrations):
            absorbance = simulator.measure_sample(conc)
            results.append({
                "样本编号": i + 1,
                "concentration": conc,
                "absorbance": {
                    "a375": absorbance[375],
                    "a405": absorbance[405],
                    "a450": absorbance[450]
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        return {
            "data": results,
            "total_samples": len(results),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        logger.error(f"批量模拟失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulator/generate-dataset")
async def generate_dataset(
    n_samples: int = 50,
    concentration_min: float = 0,
    concentration_max: float = 0.3
):
    """
    生成测试数据集并下载

    Args:
        n_samples: 样本数量
        concentration_min: 最小浓度
        concentration_max: 最大浓度

    Returns:
        Excel文件
    """
    try:
        if simulator is None or not simulator.is_connected:
            raise HTTPException(status_code=503, detail="模拟器未连接")

        # 生成数据
        df = simulator.generate_test_dataset(
            n_samples=n_samples,
            concentration_range=(concentration_min, concentration_max)
        )

        # 保存到临时文件
        output_path = f"data/simulated_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_path, index=False)

        logger.info(f"生成测试数据集: {len(df)} 样本")
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"simulated_dataset.xlsx"
        )

    except Exception as e:
        logger.error(f"生成数据集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 模型信息接口 ====================

@app.get("/api/model/info", response_model=ModelInfo)
async def get_model_info(model_type: str = "rf"):
    """
    获取模型信息

    Args:
        model_type: 模型类型 (rf/svr)

    Returns:
        模型信息
    """
    try:
        info = inference_engine.get_model_info(model_type)
        return ModelInfo(**info)

    except Exception as e:
        logger.error(f"获取模型信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/model/compare")
async def compare_models():
    """
    对比两个模型的性能

    Returns:
        模型对比结果
    """
    try:
        rf_info = inference_engine.get_model_info('rf')
        svr_info = inference_engine.get_model_info('svr')

        return {
            "random_forest": {
                "test_r2": rf_info['performance_metrics']['test_r2'],
                "test_mae": rf_info['performance_metrics']['test_mae'],
                "feature_importance": rf_info.get('feature_importance', {})
            },
            "svr": {
                "test_r2": svr_info['performance_metrics']['test_r2'],
                "test_mae": svr_info['performance_metrics']['test_mae']
            },
            "recommendation": "Random Forest (精度更高，稳定性更好)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        logger.error(f"模型对比失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 历史记录接口 ====================

@app.get("/api/history", response_model=HistoryList)
async def get_history(limit: int = 100):
    """
    获取预测历史记录

    Args:
        limit: 返回记录数量

    Returns:
        历史记录列表
    """
    try:
        db = SessionLocal()
        records = []
        
        # 从数据库读取历史记录
        db_records = db.query(PredictionRecord).order_by(
            PredictionRecord.created_at.desc()
        ).limit(limit).all()
        
        for r in db_records:
            record = {
                "id": f"REC-{r.id:06d}",
                "sample_info": {
                    "sample_id": r.sample_id,
                    "sample_type": r.sample_type,
                    "notes": r.notes
                },
                "absorbance": {
                    "a375": r.a375,
                    "a405": r.a405,
                    "a450": r.a450
                },
                "prediction": {
                    "concentration": r.predicted_concentration,
                    "confidence": r.confidence,
                    "model_type": r.model_type,
                    "timestamp": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
                },
                "created_at": r.created_at.isoformat() if r.created_at else ""
            }
            records.append(record)
        
        total = db.query(PredictionRecord).count()
        db.close()

        return HistoryList(
            total=total,
            records=records
        )

    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/history")
async def clear_history():
    """清除历史记录"""
    try:
        db = SessionLocal()
        db.query(PredictionRecord).delete()
        db.commit()
        db.close()
        return {"message": "历史记录已清除"}
    except Exception as e:
        logger.error(f"清除历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 数据导入导出 ====================

@app.post("/api/data/import")
async def import_data(file: UploadFile = File(...)):
    """
    导入Excel数据文件

    Args:
        file: Excel文件

    Returns:
        导入结果
    """
    try:
        # 读取Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # 验证格式
        required_cols = ['375nm', '405nm', '450nm']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"缺少必要列: {missing_cols}"
            )

        # 批量预测
        results = []
        for idx, row in df.iterrows():
            try:
                concentration, details = inference_engine.predict(
                    row['375nm'], row['405nm'], row['450nm'], 'rf'
                )
                results.append({
                    'row': idx + 1,
                    'concentration': round(concentration, 4),
                    'success': True
                })
            except Exception as e:
                results.append({
                    'row': idx + 1,
                    'concentration': None,
                    'success': False,
                    'error': str(e)
                })

        return {
            "message": f"成功导入 {len(df)} 条数据",
            "results": results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        logger.error(f"导入数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计分析 ====================

@app.get("/api/statistics/summary")
async def get_statistics_summary():
    """获取统计摘要"""
    try:
        db = SessionLocal()
        
        # 从数据库读取浓度数据
        records = db.query(PredictionRecord.predicted_concentration).filter(
            PredictionRecord.predicted_concentration > 0
        ).all()
        
        if not records:
            db.close()
            return {"message": "暂无有效数据"}
        
        concentrations = [r[0] for r in records]
        
        import numpy as np
        
        result = StatisticsSummary(
            total_predictions=len(concentrations),
            avg_concentration=round(float(np.mean(concentrations)), 4),
            min_concentration=round(float(np.min(concentrations)), 4),
            max_concentration=round(float(np.max(concentrations)), 4),
            std_concentration=round(float(np.std(concentrations)), 4),
            prediction_distribution={}
        )
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"获取统计摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 双溶液支持 ====================

def load_dual_solution_models():
    """加载双溶液模型"""
    global dual_solution_models, dual_solution_scalers

    backend_dir = Path(__file__).parent
    models_dir = backend_dir.parent / 'models'

    loaded_count = 0
    for sol_key, config in SOLUTION_CONFIGS.items():
        try:
            # 加载模型
            model_path = models_dir / config['model_file']
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    dual_solution_models[sol_key] = pickle.load(f)
                logger.info(f"    ✓ {config['name']} 模型加载成功 (R²={config['accuracy']:.4f})")
                loaded_count += 1
            else:
                logger.warning(f"    ✗ {config['name']} 模型文件未找到: {model_path}")

            # 加载标准化器
            scaler_path = models_dir / config['scaler_file']
            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    dual_solution_scalers[sol_key] = pickle.load(f)
        except Exception as e:
            logger.error(f"    ✗ {config['name']} 加载失败: {e}")

    if loaded_count > 0:
        logger.info(f"    ✓ 双溶液模型加载完成 ({loaded_count}/{len(SOLUTION_CONFIGS)})")
    else:
        logger.warning("    ⚠ 双溶液模型未加载，将使用默认模型")

def extract_dual_solution_features(a375, a405, a450):
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

@app.get("/api/solutions")
async def get_solutions_info():
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
        "count": len(SOLUTION_CONFIGS),
        "models_loaded": len(dual_solution_models)
    }

class DualSolutionPredictionRequest(BaseModel):
    """双溶液预测请求模型"""
    a375: float = Field(..., gt=0, description="375nm吸光度")
    a405: float = Field(..., gt=0, description="405nm吸光度")
    a450: float = Field(..., gt=0, description="450nm吸光度")
    solution_type: str = Field(..., description="溶液类型 (solution_a 或 solution_b)")
    sample_id: str = Field(None, description="样本编号")
    sample_type: str = Field("待测样本", description="样本类型")
    notes: str = Field(None, description="备注")

@app.post("/api/predict/dual")
async def predict_dual_solution(request: DualSolutionPredictionRequest):
    solution_type = request.solution_type

    if solution_type not in dual_solution_models:
        available = list(dual_solution_models.keys())
        raise HTTPException(
            status_code=400,
            detail=f"溶液类型 {solution_type} 的模型未加载。可用溶液: {available}"
        )

    try:
        # 特征提取
        features = extract_dual_solution_features(request.a375, request.a405, request.a450)

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

        # 保存到数据库
        try:
            db = SessionLocal()
            record = PredictionRecord(
                sample_id=request.sample_id,
                sample_type=request.sample_type,
                notes=request.notes,
                a375=request.a375,
                a405=request.a405,
                a450=request.a450,
                predicted_concentration=round(float(concentration), 4),
                confidence=config['accuracy'],
                model_type='dual_solution_svr',
                input_features={"solution_type": solution_type},
                created_at=datetime.now()
            )
            db.add(record)
            db.commit()
        except Exception as db_error:
            logger.warning(f"数据库保存失败: {db_error}")

        return {
            "sample_info": {
                "sample_id": request.sample_id,
                "sample_type": request.sample_type,
                "notes": request.notes
            },
            "prediction": {
                "concentration": round(float(concentration), 4),
                "confidence": config["accuracy"],
                "model_type": "dual_solution_svr",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "solution_type": solution_type,
            "solution_name": config["name"],
            "solution_description": config["description"],
            "input_absorbance": {"a375": request.a375, "a405": request.a405, "a450": request.a450},
            "model_info": {
                "model_type": "svr",
                "test_r2": config["accuracy"],
                "test_mae": config.get("test_mae", 0.005),
                "test_mse": config.get("test_mse", 0.000025),
                "solution_accuracy": config["accuracy"]
            }
        }

    except Exception as e:
        logger.error(f"双溶液预测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 主程序入口 ====================

def main():
    """启动服务器"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║        血浆游离血红蛋白检测系统 - FastAPI后端服务            ║
    ║                                                                ║
    ║        作者: 哈雷酱大小姐 (￣▽￣)／                           ║
    ║        版本: 1.0.0                                            ║
    ║                                                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式
        log_level="info"
    )


if __name__ == "__main__":
    main()
