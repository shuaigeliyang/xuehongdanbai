"""
血浆游离血红蛋白检测系统 - 数据库配置（简化版）
作者: 哈雷酱大小姐 (￣▽￣)／
使用同步MySQL驱动，避免编译问题
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置 - 使用MySQL数据库（同步版本）
# MySQL连接格式：mysql+pymysql://用户名:密码@主机:端口/数据库名
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/fhb_detection"
)

# 创建引擎（同步版本，禁用连接池）
engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=None,  # 禁用连接池
    pool_pre_ping=False
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 数据库依赖
@contextmanager
def get_db():
    """获取数据库会话（同步版本）"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# 初始化数据库
def init_db():
    """初始化数据库表（同步版本）"""
    from database import Base
    Base.metadata.create_all(bind=engine)

# 清理数据库
def close_db():
    """关闭数据库连接"""
    engine.dispose()
