"""
性能监控服务
提供模型性能跟踪、统计和异常监控功能
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """指标类型"""
    ACCURACY = "accuracy"
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    USAGE_COUNT = "usage_count"
    THROUGHPUT = "throughput"

@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    model_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelStats:
    """模型统计信息"""
    model_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    accuracy_sum: float = 0.0
    accuracy_count: int = 0
    last_request_time: Optional[datetime] = None
    first_request_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def error_rate(self) -> float:
        """错误率"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    @property
    def avg_response_time(self) -> float:
        """平均响应时间"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests
    
    @property
    def avg_accuracy(self) -> float:
        """平均准确率"""
        if self.accuracy_count == 0:
            return 0.0
        return self.accuracy_sum / self.accuracy_count

@dataclass
class Alert:
    """告警信息"""
    alert_id: str
    model_id: str
    level: AlertLevel
    message: str
    metric_type: MetricType
    threshold_value: float
    actual_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False

class PerformanceThreshold:
    """性能阈值配置"""
    
    def __init__(self):
        self.thresholds = {
            MetricType.ACCURACY: {"min": 0.7, "max": 1.0},
            MetricType.RESPONSE_TIME: {"min": 0.0, "max": 10.0},  # 秒
            MetricType.SUCCESS_RATE: {"min": 0.9, "max": 1.0},
            MetricType.ERROR_RATE: {"min": 0.0, "max": 0.1},
            MetricType.THROUGHPUT: {"min": 1.0, "max": 1000.0}  # 请求/秒
        }
    
    def set_threshold(self, metric_type: MetricType, min_value: float, max_value: float):
        """设置阈值"""
        self.thresholds[metric_type] = {"min": min_value, "max": max_value}
    
    def check_threshold(self, metric_type: MetricType, value: float) -> Optional[AlertLevel]:
        """检查是否超过阈值"""
        threshold = self.thresholds.get(metric_type)
        if not threshold:
            return None
        
        if value < threshold["min"]:
            if value < threshold["min"] * 0.5:
                return AlertLevel.CRITICAL
            elif value < threshold["min"] * 0.8:
                return AlertLevel.ERROR
            else:
                return AlertLevel.WARNING
        elif value > threshold["max"]:
            if value > threshold["max"] * 2.0:
                return AlertLevel.CRITICAL
            elif value > threshold["max"] * 1.5:
                return AlertLevel.ERROR
            else:
                return AlertLevel.WARNING
        
        return None

class TimeSeriesBuffer:
    """时间序列缓冲区"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.data: deque = deque(maxlen=max_size)
        self.lock = threading.Lock()
    
    def add(self, timestamp: datetime, value: float):
        """添加数据点"""
        with self.lock:
            self.data.append((timestamp, value))
    
    def get_recent(self, duration: timedelta) -> List[Tuple[datetime, float]]:
        """获取最近一段时间的数据"""
        cutoff_time = datetime.now() - duration
        with self.lock:
            return [(ts, val) for ts, val in self.data if ts >= cutoff_time]
    
    def get_statistics(self, duration: timedelta) -> Dict[str, float]:
        """获取统计信息"""
        recent_data = self.get_recent(duration)
        if not recent_data:
            return {}
        
        values = [val for _, val in recent_data]
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0
        }

class PerformanceMonitoringService:
    """性能监控服务"""
    
    def __init__(self):
        self.model_stats: Dict[str, ModelStats] = {}
        self.metrics_buffer: Dict[str, Dict[MetricType, TimeSeriesBuffer]] = defaultdict(
            lambda: defaultdict(lambda: TimeSeriesBuffer())
        )
        self.alerts: List[Alert] = []
        self.thresholds = PerformanceThreshold()
        self.lock = threading.Lock()
        
        # 监控配置
        self.monitoring_enabled = True
        self.alert_cooldown = timedelta(minutes=5)  # 告警冷却时间
        self.last_alert_time: Dict[str, datetime] = {}
    
    def record_request(
        self, 
        model_id: str, 
        success: bool, 
        response_time: float,
        accuracy: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录请求信息"""
        if not self.monitoring_enabled:
            return
        
        with self.lock:
            # 更新模型统计
            if model_id not in self.model_stats:
                self.model_stats[model_id] = ModelStats(model_id=model_id)
            
            stats = self.model_stats[model_id]
            stats.total_requests += 1
            stats.last_request_time = datetime.now()
            
            if stats.first_request_time is None:
                stats.first_request_time = datetime.now()
            
            if success:
                stats.successful_requests += 1
                stats.total_response_time += response_time
                
                # 记录响应时间指标
                self._record_metric(model_id, MetricType.RESPONSE_TIME, response_time)
            else:
                stats.failed_requests += 1
            
            # 记录准确率
            if accuracy is not None:
                stats.accuracy_sum += accuracy
                stats.accuracy_count += 1
                self._record_metric(model_id, MetricType.ACCURACY, accuracy)
            
            # 记录成功率和错误率
            self._record_metric(model_id, MetricType.SUCCESS_RATE, stats.success_rate)
            self._record_metric(model_id, MetricType.ERROR_RATE, stats.error_rate)
            
            # 记录使用次数
            self._record_metric(model_id, MetricType.USAGE_COUNT, stats.total_requests)
        
        # 检查告警
        self._check_alerts(model_id)
    
    def _record_metric(self, model_id: str, metric_type: MetricType, value: float):
        """记录指标数据"""
        timestamp = datetime.now()
        
        # 添加到时间序列缓冲区
        self.metrics_buffer[model_id][metric_type].add(timestamp, value)
        
        # 创建指标对象
        metric = PerformanceMetric(
            model_id=model_id,
            metric_type=metric_type,
            value=value,
            timestamp=timestamp
        )
    
    def _check_alerts(self, model_id: str):
        """检查告警条件"""
        if not self.monitoring_enabled:
            return
        
        stats = self.model_stats.get(model_id)
        if not stats:
            return
        
        # 检查各项指标
        metrics_to_check = [
            (MetricType.ACCURACY, stats.avg_accuracy),
            (MetricType.RESPONSE_TIME, stats.avg_response_time),
            (MetricType.SUCCESS_RATE, stats.success_rate),
            (MetricType.ERROR_RATE, stats.error_rate)
        ]
        
        for metric_type, value in metrics_to_check:
            alert_level = self.thresholds.check_threshold(metric_type, value)
            if alert_level:
                self._create_alert(model_id, metric_type, alert_level, value)
    
    def _create_alert(
        self, 
        model_id: str, 
        metric_type: MetricType, 
        level: AlertLevel, 
        value: float
    ):
        """创建告警"""
        # 检查告警冷却时间
        alert_key = f"{model_id}_{metric_type.value}_{level.value}"
        now = datetime.now()
        
        if alert_key in self.last_alert_time:
            if now - self.last_alert_time[alert_key] < self.alert_cooldown:
                return  # 在冷却时间内，不重复告警
        
        # 创建告警
        threshold = self.thresholds.thresholds.get(metric_type, {})
        alert_id = f"alert_{model_id}_{int(now.timestamp())}"
        
        message = self._generate_alert_message(model_id, metric_type, level, value, threshold)
        
        alert = Alert(
            alert_id=alert_id,
            model_id=model_id,
            level=level,
            message=message,
            metric_type=metric_type,
            threshold_value=threshold.get("min", 0.0) if value < threshold.get("min", 0.0) else threshold.get("max", 1.0),
            actual_value=value
        )
        
        self.alerts.append(alert)
        self.last_alert_time[alert_key] = now
        
        logger.warning(f"Alert created: {message}")
    
    def _generate_alert_message(
        self, 
        model_id: str, 
        metric_type: MetricType, 
        level: AlertLevel, 
        value: float,
        threshold: Dict[str, float]
    ) -> str:
        """生成告警消息"""
        metric_name = {
            MetricType.ACCURACY: "准确率",
            MetricType.RESPONSE_TIME: "响应时间",
            MetricType.SUCCESS_RATE: "成功率",
            MetricType.ERROR_RATE: "错误率",
            MetricType.THROUGHPUT: "吞吐量"
        }.get(metric_type, metric_type.value)
        
        level_name = {
            AlertLevel.WARNING: "警告",
            AlertLevel.ERROR: "错误",
            AlertLevel.CRITICAL: "严重"
        }.get(level, level.value)
        
        if value < threshold.get("min", 0.0):
            return f"模型 {model_id} {metric_name}过低 ({level_name}): {value:.3f} < {threshold['min']:.3f}"
        else:
            return f"模型 {model_id} {metric_name}过高 ({level_name}): {value:.3f} > {threshold['max']:.3f}"
    
    def get_model_performance(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取模型性能信息"""
        stats = self.model_stats.get(model_id)
        if not stats:
            return None
        
        # 获取最近1小时的统计信息
        recent_stats = {}
        for metric_type in MetricType:
            buffer = self.metrics_buffer[model_id].get(metric_type)
            if buffer:
                recent_stats[metric_type.value] = buffer.get_statistics(timedelta(hours=1))
        
        return {
            "model_id": model_id,
            "total_requests": stats.total_requests,
            "successful_requests": stats.successful_requests,
            "failed_requests": stats.failed_requests,
            "success_rate": stats.success_rate,
            "error_rate": stats.error_rate,
            "avg_response_time": stats.avg_response_time,
            "avg_accuracy": stats.avg_accuracy,
            "first_request_time": stats.first_request_time.isoformat() if stats.first_request_time else None,
            "last_request_time": stats.last_request_time.isoformat() if stats.last_request_time else None,
            "recent_stats": recent_stats
        }
    
    def get_all_models_performance(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型的性能信息"""
        return {
            model_id: self.get_model_performance(model_id)
            for model_id in self.model_stats.keys()
        }
    
    def get_alerts(
        self, 
        model_id: Optional[str] = None, 
        level: Optional[AlertLevel] = None,
        acknowledged: Optional[bool] = None
    ) -> List[Alert]:
        """获取告警信息"""
        alerts = self.alerts
        
        if model_id:
            alerts = [a for a in alerts if a.model_id == model_id]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False
    
    def clear_old_alerts(self, days: int = 7):
        """清理旧告警"""
        cutoff_time = datetime.now() - timedelta(days=days)
        original_count = len(self.alerts)
        
        self.alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
        
        cleared_count = original_count - len(self.alerts)
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} old alerts")
    
    def calculate_throughput(self, model_id: str, duration: timedelta = timedelta(minutes=1)) -> float:
        """计算吞吐量（请求/秒）"""
        usage_buffer = self.metrics_buffer[model_id].get(MetricType.USAGE_COUNT)
        if not usage_buffer:
            return 0.0
        
        recent_data = usage_buffer.get_recent(duration)
        if len(recent_data) < 2:
            return 0.0
        
        # 计算时间段内的请求增长
        start_requests = recent_data[0][1]
        end_requests = recent_data[-1][1]
        time_diff = (recent_data[-1][0] - recent_data[0][0]).total_seconds()
        
        if time_diff <= 0:
            return 0.0
        
        return (end_requests - start_requests) / time_diff
    
    def get_performance_trends(
        self, 
        model_id: str, 
        metric_type: MetricType,
        duration: timedelta = timedelta(hours=24)
    ) -> List[Tuple[datetime, float]]:
        """获取性能趋势数据"""
        buffer = self.metrics_buffer[model_id].get(metric_type)
        if not buffer:
            return []
        
        return buffer.get_recent(duration)
    
    def generate_performance_report(self, model_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """生成性能报告"""
        if model_ids is None:
            model_ids = list(self.model_stats.keys())
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "models": {},
            "summary": {
                "total_models": len(model_ids),
                "total_requests": 0,
                "avg_success_rate": 0.0,
                "avg_response_time": 0.0,
                "active_alerts": len([a for a in self.alerts if not a.acknowledged])
            }
        }
        
        total_requests = 0
        success_rates = []
        response_times = []
        
        for model_id in model_ids:
            perf = self.get_model_performance(model_id)
            if perf:
                report["models"][model_id] = perf
                total_requests += perf["total_requests"]
                
                if perf["total_requests"] > 0:
                    success_rates.append(perf["success_rate"])
                    if perf["avg_response_time"] > 0:
                        response_times.append(perf["avg_response_time"])
        
        # 更新汇总信息
        report["summary"]["total_requests"] = total_requests
        if success_rates:
            report["summary"]["avg_success_rate"] = statistics.mean(success_rates)
        if response_times:
            report["summary"]["avg_response_time"] = statistics.mean(response_times)
        
        return report
    
    def set_monitoring_enabled(self, enabled: bool):
        """启用/禁用监控"""
        self.monitoring_enabled = enabled
        logger.info(f"Performance monitoring {'enabled' if enabled else 'disabled'}")
    
    def reset_model_stats(self, model_id: str):
        """重置模型统计信息"""
        with self.lock:
            if model_id in self.model_stats:
                del self.model_stats[model_id]
            
            if model_id in self.metrics_buffer:
                del self.metrics_buffer[model_id]
            
            # 清理相关告警
            self.alerts = [a for a in self.alerts if a.model_id != model_id]
            
            logger.info(f"Reset stats for model {model_id}")

# 全局性能监控服务实例
performance_monitoring_service = PerformanceMonitoringService()