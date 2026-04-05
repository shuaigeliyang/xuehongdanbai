"""
血浆游离血红蛋白检测系统 - 监控告警系统
作者: 哈雷酱大小姐 (￣▽￣)／
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio


# Prometheus指标
prediction_requests = Counter(
    'fhb_prediction_requests_total',
    'Total prediction requests',
    ['model_type', 'status']
)

prediction_duration = Histogram(
    'fhb_prediction_duration_seconds',
    'Prediction request duration',
    ['model_type']
)

active_users = Gauge(
    'fhb_active_users',
    'Number of active users'
)

system_errors = Counter(
    'fhb_system_errors_total',
    'Total system errors',
    ['error_type', 'severity']
)

database_queries = Counter(
    'fhb_database_queries_total',
    'Total database queries',
    ['operation', 'status']
)

cache_hits = Counter(
    'fhb_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'fhb_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.prediction_count = 0
        self.error_count = 0
        self.start_time = datetime.now()

    def record_prediction(self, model_type: str, success: bool, duration: float):
        """记录预测指标"""
        status = "success" if success else "error"
        prediction_requests.labels(model_type=model_type, status=status).inc()
        prediction_duration.labels(model_type=model_type).observe(duration)

        if success:
            self.prediction_count += 1
        else:
            self.error_count += 1
            system_errors.labels(
                error_type="prediction",
                severity="high"
            ).inc()

    def record_database_query(self, operation: str, success: bool):
        """记录数据库查询"""
        status = "success" if success else "error"
        database_queries.labels(operation=operation, status=status).inc()

    def record_cache_access(self, cache_type: str, hit: bool):
        """记录缓存访问"""
        if hit:
            cache_hits.labels(cache_type=cache_type).inc()
        else:
            cache_misses.labels(cache_type=cache_type).inc()

    def update_active_users(self, count: int):
        """更新活跃用户数"""
        active_users.set(count)

    def get_metrics_summary(self) -> Dict:
        """获取指标摘要"""
        uptime = datetime.now() - self.start_time

        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_predictions": self.prediction_count,
            "total_errors": self.error_count,
            "success_rate": self.prediction_count / max(1, self.prediction_count + self.error_count),
            "last_updated": datetime.now().isoformat()
        }


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alerts = []
        self.alert_rules = {
            "high_error_rate": {
                "threshold": 0.1,  # 10%错误率
                "severity": "high",
                "message": "系统错误率过高"
            },
            "slow_prediction": {
                "threshold": 5.0,  # 5秒
                "severity": "medium",
                "message": "预测响应时间过长"
            },
            "database_connection": {
                "threshold": 0,  # 0表示连接失败
                "severity": "critical",
                "message": "数据库连接失败"
            }
        }

    def check_alerts(self, metrics: Dict) -> List[Dict]:
        """检查告警条件"""
        active_alerts = []

        # 检查错误率
        error_rate = metrics.get("error_rate", 0)
        if error_rate > self.alert_rules["high_error_rate"]["threshold"]:
            active_alerts.append({
                "type": "high_error_rate",
                "severity": "high",
                "message": f"错误率过高: {error_rate:.2%}",
                "timestamp": datetime.now().isoformat()
            })

        # 检查响应时间
        avg_duration = metrics.get("avg_prediction_duration", 0)
        if avg_duration > self.alert_rules["slow_prediction"]["threshold"]:
            active_alerts.append({
                "type": "slow_prediction",
                "severity": "medium",
                "message": f"平均预测时间过长: {avg_duration:.2f}秒",
                "timestamp": datetime.now().isoformat()
            })

        # 检查数据库连接
        db_connected = metrics.get("database_connected", True)
        if not db_connected:
            active_alerts.append({
                "type": "database_connection",
                "severity": "critical",
                "message": "数据库连接失败",
                "timestamp": datetime.now().isoformat()
            })

        return active_alerts

    def send_alert(self, alert: Dict):
        """发送告警（示例）"""
        # 这里可以集成邮件、短信、钉钉等通知方式
        print(f"[ALERT] {alert['severity'].upper()}: {alert['message']}")
        self.alerts.append(alert)


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.checks = {
            "database": False,
            "redis": False,
            "ml_models": False,
            "hardware": False
        }

    async def check_database(self) -> bool:
        """检查数据库连接"""
        try:
            from db_config import async_engine
            async with async_engine.connect() as conn:
                await conn.execute("SELECT 1")
            self.checks["database"] = True
            return True
        except Exception as e:
            print(f"数据库检查失败: {e}")
            self.checks["database"] = False
            return False

    async def check_redis(self) -> bool:
        """检查Redis连接"""
        try:
            from cache import cache
            await cache.connect()
            self.checks["redis"] = cache.redis is not None
            return self.checks["redis"]
        except Exception as e:
            print(f"Redis检查失败: {e}")
            self.checks["redis"] = False
            return False

    def check_ml_models(self) -> bool:
        """检查ML模型"""
        try:
            from model_inference import get_inference_engine
            engine = get_inference_engine()
            self.checks["ml_models"] = (
                engine.rf_model is not None or
                engine.svr_model is not None
            )
            return self.checks["ml_models"]
        except Exception as e:
            print(f"ML模型检查失败: {e}")
            self.checks["ml_models"] = False
            return False

    def get_health_status(self) -> Dict:
        """获取健康状态"""
        all_healthy = all(self.checks.values())

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": self.checks,
            "timestamp": datetime.now().isoformat()
        }


# 全局实例
metrics_collector = MetricsCollector()
alert_manager = AlertManager()
health_checker = HealthChecker()


# Prometheus指标导出端点
async def metrics_endpoint():
    """Prometheus指标导出"""
    metrics = generate_latest()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)


# 定期监控任务
async def monitoring_task():
    """定期监控任务"""
    while True:
        try:
            # 更新指标
            summary = metrics_collector.get_metrics_summary()

            # 检查告警
            alerts = alert_manager.check_alerts(summary)
            for alert in alerts:
                alert_manager.send_alert(alert)

            # 健康检查
            await health_checker.check_database()
            await health_checker.check_redis()
            health_checker.check_ml_models()

            # 等待60秒
            await asyncio.sleep(60)

        except Exception as e:
            print(f"监控任务错误: {e}")
            await asyncio.sleep(60)
