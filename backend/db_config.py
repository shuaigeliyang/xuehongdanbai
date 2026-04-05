"""
血浆游离血红蛋白检测系统 - 数据库配置
作者: 哈雷酱大小姐 (￣▽￣)／
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置 - 使用MySQL数据库
# MySQL连接格式：mysql+aiomysql://用户名:密码@主机:端口/数据库名
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:root@localhost:3306/fhb_detection"
)

# 同步引擎（用于Alembic迁移）
sync_engine = create_engine(
    DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://"),
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# 异步引擎
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# 会话工厂
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 数据库依赖
async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 初始化数据库
async def init_db():
    """初始化数据库表"""
    from database import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 清理数据库
async def close_db():
    """关闭数据库连接"""
    await async_engine.dispose()
