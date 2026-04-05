"""
血浆游离血红蛋白检测系统 - 数据库模型
作者: 哈雷酱大小姐 (￣▽￣)／
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="user")  # admin, user, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # 关系
    predictions = relationship("PredictionRecord", back_populates="user")


class PredictionRecord(Base):
    """预测记录表"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sample_id = Column(String(100))
    sample_type = Column(String(50), default="待测样本")
    notes = Column(Text)

    # 吸光度数据
    a375 = Column(Float, nullable=False)
    a405 = Column(Float, nullable=False)
    a450 = Column(Float, nullable=False)

    # 预测结果
    predicted_concentration = Column(Float, nullable=False)
    confidence = Column(Float)
    model_type = Column(String(20), default="rf")

    # 特征数据
    input_features = Column(JSON)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = relationship("User", back_populates="predictions")


class CalibrationRecord(Base):
    """校准记录表"""
    __tablename__ = "calibrations"

    id = Column(Integer, primary_key=True, index=True)
    calibration_name = Column(String(100), nullable=False)
    calibration_data = Column(JSON)
    performance_metrics = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20))  # INFO, WARNING, ERROR
    module = Column(String(50))
    message = Column(Text)
    extra_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100))  # login, predict, export, etc.
    resource = Column(String(100))
    details = Column(JSON)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
