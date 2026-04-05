"""
血浆游离血红蛋白检测系统 - Redis缓存层
作者: 哈雷酱大小姐 (￣▽￣)／
"""

import redis.asyncio as redis
import json
import os
from dotenv import load_dotenv
from typing import Optional, Any
import hashlib

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedisCache:
    """Redis缓存管理器"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """连接Redis"""
        try:
            self.redis = await redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            print("✓ Redis连接成功")
        except Exception as e:
            print(f"⚠ Redis连接失败: {e}")
            self.redis = None

    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """设置缓存"""
        if not self.redis:
            return False

        try:
            await self.redis.setex(
                key,
                expire_seconds,
                json.dumps(value, ensure_ascii=False)
            )
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis:
            return False

        try:
            return await self.redis.exists(key) > 0
        except Exception:
            return False

    def generate_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_str = ":".join(str(arg) for arg in args)
        return f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"


# 全局缓存实例
cache = RedisCache()


# 缓存装饰器
def cached(prefix: str, expire_seconds: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache.generate_key(prefix, *args, str(kwargs))

            # 尝试从缓存获取
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            await cache.set(cache_key, result, expire_seconds)

            return result
        return wrapper
    return decorator


# 预测结果缓存
async def cache_prediction(a375: float, a405: float, a450: float, result: dict):
    """缓存预测结果"""
    cache_key = cache.generate_key("prediction", a375, a405, a450)
    await cache.set(cache_key, result, expire_seconds=86400)  # 24小时


async def get_cached_prediction(a375: float, a405: float, a450: float) -> Optional[dict]:
    """获取缓存的预测结果"""
    cache_key = cache.generate_key("prediction", a375, a405, a450)
    return await cache.get(cache_key)


# 模型信息缓存
async def cache_model_info(model_type: str, info: dict):
    """缓存模型信息"""
    cache_key = f"model_info:{model_type}"
    await cache.set(cache_key, info, expire_seconds=3600)  # 1小时


async def get_cached_model_info(model_type: str) -> Optional[dict]:
    """获取缓存的模型信息"""
    cache_key = f"model_info:{model_type}"
    return await cache.get(cache_key)


# 统计数据缓存
async def cache_statistics(stats: dict):
    """缓存统计数据"""
    await cache.set("statistics", stats, expire_seconds=300)  # 5分钟


async def get_cached_statistics() -> Optional[dict]:
    """获取缓存的统计数据"""
    return await cache.get("statistics")


# 清除所有缓存
async def clear_all_cache():
    """清除所有缓存"""
    if cache.redis:
        await cache.redis.flushdb()
