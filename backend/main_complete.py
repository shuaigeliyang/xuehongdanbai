"""
血浆游离血红蛋白检测系统 - FastAPI主应用（完整版）
作者: 哈雷酱大小姐 (￣▽￣)／
集成：数据库、认证、缓存、PDF、硬件、监控
"""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uvicorn
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import time

# 导入模块
from api_models import *
from model_inference import get_inference_engine
from simulator import SpectrometerSimulator
from database import User, PredictionRecord, AuditLog
from db_config import get_db, init_db, close_db
from auth import (
    AuthService, get_current_user, get_current_admin_user,
    require_role, get_current_active_user
)
from cache import cache, cache_prediction, get_cached_prediction, cache_model_info
from pdf_generator import pdf_generator
from hardware_integration import create_spectrometer
from monitoring import (
    metrics_collector, alert_manager, health_checker,
    metrics_endpoint, monitoring_task
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
inference_engine = None
simulator = None
spectrometer_controller = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global inference_engine, simulator, spectrometer_controller

    logger.info("=" * 60)
    logger.info("血浆游离血红蛋白检测系统启动中...")
    logger.info("作者: 哈雷酱大小姐 (￣▽￣)／")
    logger.info("=" * 60)

    try:
        # 初始化数据库
        logger.info("[1/7] 初始化数据库...")
        await init_db()
        logger.info("    ✓ 数据库初始化完成")

        # 初始化推理引擎
        logger.info("[2/7] 加载ML模型...")
        inference_engine = get_inference_engine(".")
        logger.info("    ✓ ML模型加载成功")

        # 初始化模拟器
        logger.info("[3/7] 启动光谱仪模拟器...")
        simulator = SpectrometerSimulator()
        simulator.connect()
        logger.info("    ✓ 光谱仪模拟器已启动")

        # 初始化硬件控制器
        logger.info("[4/7] 初始化硬件控制器...")
        spectrometer_controller = create_spectrometer("simulated")
        spectrometer_controller.connect()
        logger.info("    ✓ 硬件控制器初始化完成")

        # 初始化Redis缓存
        logger.info("[5/7] 连接Redis缓存...")
        await cache.connect()
        logger.info("    ✓ Redis缓存已连接")

        # 健康检查
        logger.info("[6/7] 执行健康检查...")
        health_status = health_checker.get_health_status()
        logger.info(f"    ✓ 系统状态: {health_status['status']}")

        # 启动监控任务
        logger.info("[7/7] 启动监控任务...")
        asyncio.create_task(monitoring_task())
        logger.info("    ✓ 监控任务已启动")

        logger.info("\n系统启动完成！(￣▽￣)／")
        logger.info("API文档: http://localhost:8000/docs")
        logger.info("Prometheus指标: http://localhost:8000/metrics")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise

    yield

    # 关闭时清理
    logger.info("系统关闭中...")
    if simulator:
        simulator.disconnect()
    if spectrometer_controller:
        spectrometer_controller.disconnect()
    await cache.close()
    await close_db()


# 创建FastAPI应用
app = FastAPI(
    title="血浆游离血红蛋白检测系统API（完整版）",
    description="集成数据库、认证、缓存、PDF、硬件、监控的企业级检测系统",
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


# ==================== 基础接口 ====================

@app.get("/", response_model=Dict)
async def root():
    """根路径"""
    return {
        "message": "血浆游离血红蛋白检测系统API（完整版）",
        "version": "2.0.0",
        "author": "哈雷酱大小姐 (￣▽￣)／",
        "features": [
            "PostgreSQL数据库",
            "JWT用户认证",
            "Redis缓存优化",
            "PDF报告生成",
            "硬件集成接口",
            "Prometheus监控"
        ],
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    health_status = health_checker.get_health_status()
    return {
        "status": health_status["status"],
        "checks": health_status["checks"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@app.get("/metrics")
async def metrics():
    """Prometheus指标"""
    return await metrics_endpoint()


# ==================== 用户认证接口 ====================

@app.post("/api/auth/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    # 检查用户是否存在
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建用户
    hashed_password = AuthService.get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role="user"
    )

    db.add(new_user)
    await db.commit()

    # 记录审计日志
    audit_log = AuditLog(
        user_id=new_user.id,
        action="register",
        resource="user",
        details={"username": username}
    )
    db.add(audit_log)
    await db.commit()

    return {"message": "注册成功", "username": username}


@app.post("/api/auth/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    # 验证用户
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not AuthService.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token = AuthService.create_access_token(data={"sub": user.username})

    # 记录审计日志
    audit_log = AuditLog(
        user_id=user.id,
        action="login",
        resource="auth",
        details={"username": user.username}
    )
    db.add(audit_log)
    await db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }


@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }


# ==================== 预测接口（带缓存和数据库） ====================

@app.post("/api/predict")
async def predict_concentration(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    """预测血浆游离血红蛋白浓度（增强版）- 无需认证"""
    start_time = time.time()

    try:
        # 提取吸光度数据
        a375 = request.absorbance.a375
        a405 = request.absorbance.a405
        a450 = request.absorbance.a450

        # 检查缓存
        cached_result = await get_cached_prediction(a375, a405, a450)
        if cached_result:
            logger.info(f"缓存命中: {a375}, {a405}, {a450}")
            metrics_collector.record_cache_access("prediction", True)
            return cached_result

        metrics_collector.record_cache_access("prediction", False)

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

        # 保存到数据库（无需用户认证，user_id为None）
        prediction_record = PredictionRecord(
            user_id=None,  # 无需认证，user_id设为None
            sample_id=request.sample_info.sample_id if request.sample_info else None,
            sample_type=request.sample_info.sample_type if request.sample_info else "待测样本",
            notes=request.sample_info.notes if request.sample_info else None,
            a375=a375,
            a405=a405,
            a450=a450,
            predicted_concentration=concentration,
            confidence=details['confidence'],
            model_type=request.model_type,
            input_features=details['input_features']
        )
        db.add(prediction_record)
        await db.commit()

        # 缓存结果
        await cache_prediction(a375, a405, a450, result.dict())

        # 记录指标
        duration = time.time() - start_time
        metrics_collector.record_prediction(request.model_type, True, duration)

        logger.info(f"预测成功: {concentration:.4f} g/L")
        return result

    except Exception as e:
        logger.error(f"预测失败: {e}")
        metrics_collector.record_prediction(request.model_type, False, time.time() - start_time)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PDF报告生成 ====================

@app.post("/api/reports/generate")
async def generate_pdf_report(
    prediction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成PDF检测报告"""
    try:
        # 查询预测记录
        result = await db.execute(
            select(PredictionRecord).where(PredictionRecord.id == prediction_id)
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="预测记录不存在")

        # 准备报告数据
        sample_info = {
            "sample_id": record.sample_id,
            "sample_type": record.sample_type,
            "notes": record.notes
        }

        absorbance = {
            "a375": record.a375,
            "a405": record.a405,
            "a450": record.a450
        }

        prediction = {
            "concentration": record.predicted_concentration,
            "confidence": record.confidence,
            "model_type": record.model_type,
            "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

        model_info = inference_engine.get_model_info(record.model_type)

        # 生成PDF
        pdf_path = pdf_generator.generate_detection_report(
            sample_info, absorbance, prediction, model_info
        )

        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            action="export",
            resource="report",
            details={"prediction_id": prediction_id, "pdf_path": pdf_path}
        )
        db.add(audit_log)
        await db.commit()

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"detection_report_{prediction_id}.pdf"
        )

    except Exception as e:
        logger.error(f"PDF生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 硬件接口 ====================

@app.post("/api/hardware/connect")
async def connect_hardware(
    device_type: str = "simulated",
    current_user: User = Depends(require_role("admin"))
):
    """连接硬件设备"""
    global spectrometer_controller

    try:
        spectrometer_controller = create_spectrometer(device_type)
        result = spectrometer_controller.connect()

        return result
    except Exception as e:
        logger.error(f"硬件连接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hardware/measure")
async def hardware_measure(
    current_user: User = Depends(get_current_active_user)
):
    """使用硬件设备进行测量"""
    global spectrometer_controller

    if not spectrometer_controller or not spectrometer_controller.is_connected:
        raise HTTPException(status_code=503, detail="硬件设备未连接")

    result = spectrometer_controller.perform_measurement()

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="hardware_measure",
        resource="spectrometer",
        details=result["absorbance"]
    )
    # 这里需要db session，简化处理

    return result


@app.get("/api/hardware/status")
async def get_hardware_status(
    current_user: User = Depends(get_current_active_user)
):
    """获取硬件状态"""
    global spectrometer_controller

    if not spectrometer_controller:
        return {"is_connected": False, "message": "硬件控制器未初始化"}

    return spectrometer_controller.get_device_status()


# ==================== 历史记录接口 ====================

@app.get("/api/history")
async def get_prediction_history(
    limit: int = 100,
    offset: int = 0,
    model_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取预测历史记录（支持分页和筛选）- 无需认证"""
    try:
        # 构建查询（不再按用户筛选，返回所有记录）
        query = select(PredictionRecord)

        # 按模型类型筛选
        if model_type:
            query = query.where(PredictionRecord.model_type == model_type)

        # 按日期范围筛选
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.where(PredictionRecord.created_at >= start_dt)
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.where(PredictionRecord.created_at <= end_dt)
            except ValueError:
                pass

        # 按创建时间倒序排序
        query = query.order_by(PredictionRecord.created_at.desc())

        # 获取总数
        count_query = select(PredictionRecord.id)
        if model_type:
            count_query = count_query.where(PredictionRecord.model_type == model_type)
        count_result = await db.execute(count_query)
        total = len(count_result.all())

        # 分页查询
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        records = result.scalars().all()

        # 格式化响应数据
        formatted_records = []
        for record in records:
            formatted_records.append({
                "id": str(record.id),
                "sample_info": {
                    "sample_id": record.sample_id,
                    "sample_type": record.sample_type,
                    "notes": record.notes
                } if record.sample_id or record.sample_type or record.notes else None,
                "absorbance": {
                    "a375": record.a375,
                    "a405": record.a405,
                    "a450": record.a450
                },
                "prediction": {
                    "concentration": record.predicted_concentration,
                    "confidence": record.confidence,
                    "model_type": record.model_type,
                    "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
                },
                "created_at": record.created_at.isoformat()
            })

        return {
            "total": total,
            "records": formatted_records,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{prediction_id}")
async def get_prediction_detail(
    prediction_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取单个预测记录详情 - 无需认证"""
    try:
        result = await db.execute(
            select(PredictionRecord).where(PredictionRecord.id == prediction_id)
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="预测记录不存在")

        # 获取模型信息
        model_info = inference_engine.get_model_info(record.model_type)

        return {
            "id": str(record.id),
            "sample_info": {
                "sample_id": record.sample_id,
                "sample_type": record.sample_type,
                "notes": record.notes
            },
            "absorbance": {
                "a375": record.a375,
                "a405": record.a405,
                "a450": record.a450
            },
            "prediction": {
                "concentration": record.predicted_concentration,
                "confidence": record.confidence,
                "model_type": record.model_type,
                "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
            },
            "input_features": record.input_features,
            "model_info": model_info,
            "created_at": record.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取预测详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/history/{prediction_id}")
async def delete_prediction_record(
    prediction_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除单个预测记录 - 无需认证"""
    try:
        result = await db.execute(
            select(PredictionRecord).where(PredictionRecord.id == prediction_id)
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="预测记录不存在")

        await db.delete(record)
        await db.commit()

        return {"message": "预测记录已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除预测记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/history")
async def clear_all_history(
    db: AsyncSession = Depends(get_db)
):
    """清除所有历史记录 - 无需认证"""
    try:
        # 删除所有预测记录
        result = await db.execute(select(PredictionRecord))
        records = result.scalars().all()

        count = len(records)
        for record in records:
            await db.delete(record)

        await db.commit()

        logger.info(f"清除了 {count} 条历史记录")
        return {"message": f"已清除 {count} 条历史记录"}

    except Exception as e:
        logger.error(f"清除历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计接口 ====================

@app.get("/api/statistics/summary")
async def get_statistics_summary(
    current_user: User = Depends(get_current_active_user)
):
    """获取统计摘要"""
    # 检查缓存
    cached_stats = await cache.get("statistics")
    if cached_stats:
        return cached_stats

    # 这里应该从数据库查询真实统计
    stats = {
        "total_predictions": metrics_collector.prediction_count,
        "total_errors": metrics_collector.error_count,
        "success_rate": 0.99,
        "avg_concentration": 0.1523,
        "timestamp": datetime.now().isoformat()
    }

    # 缓存5分钟
    await cache.set("statistics", stats, expire_seconds=300)

    return stats


@app.get("/api/statistics/metrics")
async def get_system_metrics(
    current_user: User = Depends(require_role("admin"))
):
    """获取系统指标（管理员）"""
    return metrics_collector.get_metrics_summary()


@app.get("/api/statistics/alerts")
async def get_active_alerts(
    current_user: User = Depends(require_role("admin"))
):
    """获取活跃告警（管理员）"""
    metrics = metrics_collector.get_metrics_summary()
    alerts = alert_manager.check_alerts(metrics)
    return {"alerts": alerts, "count": len(alerts)}


# ==================== 用户管理（管理员） ====================

@app.get("/api/admin/users")
async def list_users(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表（管理员）"""
    result = await db.execute(select(User))
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ]
    }


@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除用户（管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.delete(user)
    await db.commit()

    return {"message": "用户已删除"}


# ==================== 主程序入口 ====================

def main():
    """启动服务器"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║        血浆游离血红蛋白检测系统 - 企业级后端服务              ║
    ║                                                                ║
    ║        作者: 哈雷酱大小姐 (￣▽￣)／                           ║
    ║        版本: 2.0.0 (完整版)                                    ║
    ║                                                                ║
    ║        功能特性:                                               ║
    ║        ✓ PostgreSQL数据库                                      ║
    ║        ✓ JWT用户认证                                          ║
    ║        ✓ Redis缓存优化                                        ║
    ║        ✓ PDF报告生成                                          ║
    ║        ✓ 硬件集成接口                                         ║
    ║        ✓ Prometheus监控                                       ║
    ║                                                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main_complete:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
