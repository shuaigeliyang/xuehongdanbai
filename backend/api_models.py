"""
血浆游离血红蛋白检测系统 - API数据模型
作者: 哈雷酱大小姐 (￣▽￣)／
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# ==================== 请求模型 ====================

class AbsorbanceData(BaseModel):
    """吸光度数据"""
    a375: float = Field(..., description="375nm吸光度", ge=0)
    a405: float = Field(..., description="405nm吸光度", ge=0)
    a450: float = Field(..., description="450nm吸光度", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "a375": 0.1275,
                "a405": 0.1875,
                "a450": 0.0975
            }
        }


class SampleInfo(BaseModel):
    """样本信息"""
    sample_id: Optional[str] = Field(None, description="样本编号")
    sample_type: Optional[str] = Field("待测样本", description="样本类型")
    notes: Optional[str] = Field(None, description="备注")


class PredictionRequest(BaseModel):
    """预测请求"""
    absorbance: AbsorbanceData
    sample_info: Optional[SampleInfo] = None
    model_type: str = Field("rf", description="模型类型: rf/svr")

    class Config:
        json_schema_extra = {
            "example": {
                "absorbance": {
                    "a375": 0.1275,
                    "a405": 0.1875,
                    "a450": 0.0975
                },
                "sample_info": {
                    "sample_id": "SAMPLE-001",
                    "sample_type": "待测样本",
                    "notes": "常规检测"
                },
                "model_type": "rf"
            }
        }


class BatchPredictionRequest(BaseModel):
    """批量预测请求"""
    samples: List[PredictionRequest]
    model_type: str = Field("rf", description="模型类型: rf/svr")


class CalibrationRequest(BaseModel):
    """校准请求"""
    calibration_data: List[Dict[str, float]]
    notes: Optional[str] = None


# ==================== 响应模型 ====================

class PredictionResult(BaseModel):
    """预测结果"""
    concentration: float = Field(..., description="预测浓度 (g/L)")
    confidence: Optional[float] = Field(None, description="置信度 (0-1)")
    model_type: str = Field(..., description="使用的模型类型")
    timestamp: str = Field(..., description="预测时间")

    class Config:
        json_schema_extra = {
            "example": {
                "concentration": 0.1523,
                "confidence": 0.95,
                "model_type": "rf",
                "timestamp": "2026-03-16 14:30:00"
            }
        }


class DetailedPrediction(BaseModel):
    """详细预测结果"""
    sample_info: Optional[SampleInfo]
    prediction: PredictionResult
    input_features: Dict[str, float] = Field(..., description="输入特征")
    model_info: Dict[str, float] = Field(..., description="模型信息")


class BatchPredictionResponse(BaseModel):
    """批量预测响应"""
    results: List[PredictionResult]
    total_samples: int
    success_count: int
    timestamp: str


class ModelInfo(BaseModel):
    """模型信息"""
    model_type: str
    version: str
    performance_metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]] = None
    last_trained: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    message: str
    models_loaded: bool
    simulator_connected: bool
    timestamp: str


# ==================== 模拟器相关模型 ====================

class SimulatorRequest(BaseModel):
    """模拟器请求"""
    concentration: float = Field(..., description="样本浓度 (g/L)", ge=0, le=6)
    noise_level: float = Field(0.01, description="噪声水平", ge=0, le=0.1)


class SimulatorResponse(BaseModel):
    """模拟器响应"""
    absorbance: AbsorbanceData
    concentration: float
    measurement_time: str


class BatchSimulatorRequest(BaseModel):
    """批量模拟请求"""
    concentrations: List[float]
    noise_level: float = Field(0.01, description="噪声水平", ge=0, le=0.1)


# ==================== 历史记录相关 ====================

class HistoryRecord(BaseModel):
    """历史记录"""
    id: str
    sample_info: Optional[SampleInfo] = None
    absorbance: AbsorbanceData
    prediction: PredictionResult
    created_at: str


class HistoryList(BaseModel):
    """历史记录列表"""
    total: int
    records: List[HistoryRecord]


# ==================== 统计分析 ====================

class StatisticsSummary(BaseModel):
    """统计摘要"""
    total_predictions: int
    avg_concentration: float
    min_concentration: float
    max_concentration: float
    std_concentration: float
    prediction_distribution: Dict[str, int]


class QualityMetrics(BaseModel):
    """质量指标"""
    accuracy_score: float
    precision_score: float
    recall_score: float
    last_calibration: Optional[str]
    system_status: str
