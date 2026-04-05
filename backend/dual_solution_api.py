"""
血浆游离血红蛋白检测系统 - 双溶液FastAPI后端
作者: 哈雷酱大小姐 (￣▽￣)／
功能: 支持两种不同溶液的预测API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime

# 导入推理引擎
from dual_solution_inference import get_dual_solution_engine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
inference_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global inference_engine

    logger.info("="*60)
    logger.info("双溶液血浆游离血红蛋白检测系统启动中...")
    logger.info("作者: 哈雷酱大小姐 (￣▽￣)／")
    logger.info("="*60)

    try:
        logger.info("[1/1] 加载双溶液ML模型...")
        inference_engine = get_dual_solution_engine()
        logger.info("    ✓ 双溶液模型加载成功")

        logger.info("\n系统启动完成！(￣▽￣)／")
        logger.info("API文档: http://localhost:8000/docs")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise

    yield

    logger.info("系统关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="双溶液血浆游离血红蛋白检测系统API",
    description="支持两种不同溶液的血浆游离血红蛋白浓度预测系统",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 数据模型 ====================

class PredictionRequest(BaseModel):
    """预测请求模型"""
    a375: float = Field(..., gt=0, description="375nm吸光度")
    a405: float = Field(..., gt=0, description="405nm吸光度")
    a450: float = Field(..., gt=0, description="450nm吸光度")
    solution_type: Literal['solution_a', 'solution_b'] = Field(
        ...,
        description="溶液类型: solution_a(溶液A) 或 solution_b(溶液B)"
    )
    model_type: Optional[Literal['rf', 'svr', 'best']] = Field(
        'best',
        description="模型类型: rf, svr, 或 best(使用最佳模型)"
    )


class PredictionResponse(BaseModel):
    """预测响应模型"""
    concentration: float = Field(..., description="预测浓度 (g/L)")
    solution_type: str = Field(..., description="溶液类型")
    solution_name: str = Field(..., description="溶液名称")
    model_type: str = Field(..., description="使用的模型类型")
    input_features: dict = Field(..., description="输入特征")
    timestamp: str = Field(..., description="预测时间")


class SolutionInfo(BaseModel):
    """溶液信息模型"""
    solution_type: str
    solution_name: str
    description: str
    best_model_type: str
    trained_at: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    message: str
    models_loaded: bool
    available_solutions: list
    timestamp: str


# ==================== 基础接口 ====================

@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "message": "双溶液血浆游离血红蛋白检测系统API",
        "version": "2.0.0",
        "author": "哈雷酱大小姐 (￣▽￣)／",
        "docs": "/docs",
        "solutions": {
            "solution_a": "溶液A - 2025年7月31日测量的标准溶液",
            "solution_b": "溶液B - 2025年8月12日测量的实验溶液"
        },
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        message="双溶液系统运行正常",
        models_loaded=inference_engine is not None,
        available_solutions=['solution_a', 'solution_b'],
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@app.get("/api/solutions", response_model=dict)
async def get_solutions_info():
    """获取所有溶液信息"""
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    try:
        all_info = inference_engine.get_all_solutions_info()
        return {
            "solutions": all_info,
            "count": len(all_info)
        }
    except Exception as e:
        logger.error(f"获取溶液信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/solutions/{solution_type}", response_model=SolutionInfo)
async def get_solution_info(solution_type: str):
    """获取指定溶液的信息"""
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    try:
        info = inference_engine.get_solution_info(solution_type)
        return SolutionInfo(**info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取溶液信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 预测接口 ====================

@app.post("/api/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    预测血浆游离血红蛋白浓度

    **溶液类型说明:**
    - `solution_a`: 溶液A - 2025年7月31日测量的标准溶液（高吸光度）
    - `solution_b`: 溶液B - 2025年8月12日测量的实验溶液（低吸光度）

    **使用建议:**
    - 根据您的实验样品类型选择对应的溶液
    - model_type='best' 将自动使用该溶液的最佳模型
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    try:
        # 验证输入
        is_valid, error_msg = inference_engine.validate_input(
            request.a375, request.a405, request.a450
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # 执行预测
        concentration, details = inference_engine.predict(
            request.a375,
            request.a405,
            request.a450,
            request.solution_type,
            request.model_type
        )

        return PredictionResponse(
            concentration=round(concentration, 4),
            solution_type=details['solution_type'],
            solution_name=details['solution_name'],
            model_type=details['model_type'],
            input_features=details['input_features'],
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"预测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 启动服务器 ====================

def main():
    """启动服务器"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   双溶液血浆游离血红蛋白检测系统                          ║
║   Dual-Solution Plasma FHb Detection System              ║
║                                                           ║
║   作者: 哈雷酱大小姐 (￣▽￣)／                            ║
║   版本: 2.0.0                                             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "dual_solution_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
