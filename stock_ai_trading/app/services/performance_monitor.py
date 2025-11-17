"""
技术指标计算性能监控模块
提供性能统计、监控和优化建议
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import pandas as pd
import numpy as np
from functools import wraps
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    data_size: int
    timestamp: datetime
    parameters: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

@dataclass
class AggregatedMetrics:
    """聚合性能指标"""
    function_name: str
    call_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    avg_memory: float
    avg_cpu: float
    error_count: int
    last_called: datetime
    throughput: float  # 每秒处理的数据量

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_records: int = 10000, cleanup_interval: int = 3600):
        self.max_records = max_records
        self.cleanup_interval = cleanup_interval
        self.metrics: deque = deque(maxlen=max_records)
        self.aggregated_metrics: Dict[str, AggregatedMetrics] = {}
        self.lock = threading.Lock()
        self.start_time = datetime.now()
        
        # 启动清理线程
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """启动定期清理线程"""
        def cleanup():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_old_metrics()
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_metrics(self):
        """清理过期的性能指标"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        with self.lock:
            # 清理详细指标
            while self.metrics and self.metrics[0].timestamp < cutoff_time:
                self.metrics.popleft()
    
    def record_metric(self, metric: PerformanceMetric):
        """记录性能指标"""
        with self.lock:
            self.metrics.append(metric)
            self._update_aggregated_metrics(metric)
    
    def _update_aggregated_metrics(self, metric: PerformanceMetric):
        """更新聚合指标"""
        func_name = metric.function_name
        
        if func_name not in self.aggregated_metrics:
            self.aggregated_metrics[func_name] = AggregatedMetrics(
                function_name=func_name,
                call_count=0,
                total_time=0.0,
                avg_time=0.0,
                min_time=float('inf'),
                max_time=0.0,
                avg_memory=0.0,
                avg_cpu=0.0,
                error_count=0,
                last_called=metric.timestamp,
                throughput=0.0
            )
        
        agg = self.aggregated_metrics[func_name]
        
        # 更新计数和时间统计
        agg.call_count += 1
        agg.total_time += metric.execution_time
        agg.avg_time = agg.total_time / agg.call_count
        agg.min_time = min(agg.min_time, metric.execution_time)
        agg.max_time = max(agg.max_time, metric.execution_time)
        agg.last_called = metric.timestamp
        
        # 更新资源使用统计
        agg.avg_memory = (agg.avg_memory * (agg.call_count - 1) + metric.memory_usage) / agg.call_count
        agg.avg_cpu = (agg.avg_cpu * (agg.call_count - 1) + metric.cpu_usage) / agg.call_count
        
        # 更新错误计数
        if metric.error:
            agg.error_count += 1
        
        # 计算吞吐量（每秒处理的数据量）
        if agg.avg_time > 0:
            agg.throughput = metric.data_size / agg.avg_time
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取性能指标摘要"""
        with self.lock:
            summary = {
                'total_calls': len(self.metrics),
                'monitoring_duration': (datetime.now() - self.start_time).total_seconds(),
                'functions': {}
            }
            
            for func_name, agg in self.aggregated_metrics.items():
                summary['functions'][func_name] = {
                    'call_count': agg.call_count,
                    'avg_execution_time': round(agg.avg_time, 4),
                    'min_execution_time': round(agg.min_time, 4),
                    'max_execution_time': round(agg.max_time, 4),
                    'total_execution_time': round(agg.total_time, 4),
                    'avg_memory_usage': round(agg.avg_memory, 2),
                    'avg_cpu_usage': round(agg.avg_cpu, 2),
                    'error_count': agg.error_count,
                    'error_rate': round(agg.error_count / agg.call_count * 100, 2),
                    'throughput': round(agg.throughput, 2),
                    'last_called': agg.last_called.isoformat()
                }
            
            return summary
    
    def get_performance_trends(self, function_name: Optional[str] = None, 
                             hours: int = 24) -> Dict[str, Any]:
        """获取性能趋势数据"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            filtered_metrics = [
                m for m in self.metrics 
                if m.timestamp >= cutoff_time and 
                (function_name is None or m.function_name == function_name)
            ]
        
        if not filtered_metrics:
            return {'message': 'No data available for the specified period'}
        
        # 按小时分组统计
        hourly_stats = defaultdict(list)
        for metric in filtered_metrics:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_stats[hour_key].append(metric)
        
        trends = {
            'period_hours': hours,
            'data_points': len(hourly_stats),
            'hourly_trends': []
        }
        
        for hour, metrics in sorted(hourly_stats.items()):
            hour_data = {
                'timestamp': hour.isoformat(),
                'call_count': len(metrics),
                'avg_execution_time': np.mean([m.execution_time for m in metrics]),
                'avg_memory_usage': np.mean([m.memory_usage for m in metrics]),
                'avg_cpu_usage': np.mean([m.cpu_usage for m in metrics]),
                'error_count': sum(1 for m in metrics if m.error)
            }
            trends['hourly_trends'].append(hour_data)
        
        return trends
    
    def get_slow_functions(self, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """获取执行缓慢的函数"""
        with self.lock:
            slow_functions = []
            
            for func_name, agg in self.aggregated_metrics.items():
                if agg.avg_time >= threshold_seconds:
                    slow_functions.append({
                        'function_name': func_name,
                        'avg_execution_time': round(agg.avg_time, 4),
                        'max_execution_time': round(agg.max_time, 4),
                        'call_count': agg.call_count,
                        'total_time': round(agg.total_time, 4)
                    })
            
            # 按平均执行时间排序
            slow_functions.sort(key=lambda x: x['avg_execution_time'], reverse=True)
            
            return slow_functions
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        suggestions = []
        
        with self.lock:
            for func_name, agg in self.aggregated_metrics.items():
                # 执行时间过长
                if agg.avg_time > 1.0:
                    suggestions.append({
                        'type': 'performance',
                        'function': func_name,
                        'issue': 'High execution time',
                        'value': f'{agg.avg_time:.4f}s',
                        'suggestion': 'Consider optimizing algorithm or using vectorized operations'
                    })
                
                # 内存使用过高
                if agg.avg_memory > 500:  # MB
                    suggestions.append({
                        'type': 'memory',
                        'function': func_name,
                        'issue': 'High memory usage',
                        'value': f'{agg.avg_memory:.2f}MB',
                        'suggestion': 'Consider processing data in chunks or optimizing data structures'
                    })
                
                # 错误率过高
                error_rate = agg.error_count / agg.call_count * 100
                if error_rate > 5:
                    suggestions.append({
                        'type': 'reliability',
                        'function': func_name,
                        'issue': 'High error rate',
                        'value': f'{error_rate:.2f}%',
                        'suggestion': 'Review error handling and input validation'
                    })
                
                # 吞吐量过低
                if agg.throughput < 1000 and agg.call_count > 10:
                    suggestions.append({
                        'type': 'throughput',
                        'function': func_name,
                        'issue': 'Low throughput',
                        'value': f'{agg.throughput:.2f} records/s',
                        'suggestion': 'Consider batch processing or parallel computation'
                    })
        
        return suggestions
    
    def export_metrics(self, format: str = 'json') -> str:
        """导出性能指标数据"""
        summary = self.get_metrics_summary()
        
        if format.lower() == 'json':
            import json
            return json.dumps(summary, indent=2, default=str)
        elif format.lower() == 'csv':
            # 转换为CSV格式
            rows = []
            for func_name, data in summary['functions'].items():
                row = {'function_name': func_name}
                row.update(data)
                rows.append(row)
            
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

# 全局性能监控器实例
global_monitor = PerformanceMonitor()

def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        error = None
        result = None
        data_size = 0
        
        try:
            result = func(*args, **kwargs)
            
            # 尝试估算数据大小
            if hasattr(result, '__len__'):
                data_size = len(result)
            elif isinstance(result, pd.DataFrame):
                data_size = len(result)
            elif args and hasattr(args[0], '__len__'):
                data_size = len(args[0])
            
        except Exception as e:
            error = str(e)
            logger.error(f"Error in {func.__name__}: {error}")
            raise
        
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent()
            
            # 记录性能指标
            metric = PerformanceMetric(
                function_name=f"{func.__module__}.{func.__name__}",
                execution_time=end_time - start_time,
                memory_usage=end_memory - start_memory,
                cpu_usage=(start_cpu + end_cpu) / 2,
                data_size=data_size,
                timestamp=datetime.now(),
                parameters={k: str(v)[:100] for k, v in kwargs.items()},  # 限制参数长度
                error=error
            )
            
            global_monitor.record_metric(metric)
        
        return result
    
    return wrapper

class PerformanceAnalyzer:
    """性能分析器"""
    
    @staticmethod
    def analyze_function_performance(function_name: str, 
                                   monitor: PerformanceMonitor = None) -> Dict[str, Any]:
        """分析特定函数的性能"""
        if monitor is None:
            monitor = global_monitor
        
        with monitor.lock:
            function_metrics = [
                m for m in monitor.metrics 
                if m.function_name == function_name
            ]
        
        if not function_metrics:
            return {'error': f'No metrics found for function {function_name}'}
        
        execution_times = [m.execution_time for m in function_metrics]
        memory_usage = [m.memory_usage for m in function_metrics]
        data_sizes = [m.data_size for m in function_metrics]
        
        analysis = {
            'function_name': function_name,
            'sample_size': len(function_metrics),
            'execution_time': {
                'mean': np.mean(execution_times),
                'median': np.median(execution_times),
                'std': np.std(execution_times),
                'min': np.min(execution_times),
                'max': np.max(execution_times),
                'percentiles': {
                    '95th': np.percentile(execution_times, 95),
                    '99th': np.percentile(execution_times, 99)
                }
            },
            'memory_usage': {
                'mean': np.mean(memory_usage),
                'median': np.median(memory_usage),
                'std': np.std(memory_usage),
                'min': np.min(memory_usage),
                'max': np.max(memory_usage)
            },
            'data_size': {
                'mean': np.mean(data_sizes),
                'median': np.median(data_sizes),
                'min': np.min(data_sizes),
                'max': np.max(data_sizes)
            }
        }
        
        # 性能评级
        avg_time = analysis['execution_time']['mean']
        if avg_time < 0.1:
            performance_grade = 'A'
        elif avg_time < 0.5:
            performance_grade = 'B'
        elif avg_time < 1.0:
            performance_grade = 'C'
        elif avg_time < 2.0:
            performance_grade = 'D'
        else:
            performance_grade = 'F'
        
        analysis['performance_grade'] = performance_grade
        
        return analysis
    
    @staticmethod
    def compare_functions(function_names: List[str], 
                         monitor: PerformanceMonitor = None) -> Dict[str, Any]:
        """比较多个函数的性能"""
        if monitor is None:
            monitor = global_monitor
        
        comparison = {
            'functions': function_names,
            'comparison_data': {},
            'ranking': {}
        }
        
        for func_name in function_names:
            analysis = PerformanceAnalyzer.analyze_function_performance(func_name, monitor)
            if 'error' not in analysis:
                comparison['comparison_data'][func_name] = analysis
        
        # 性能排名
        if comparison['comparison_data']:
            # 按平均执行时间排名
            time_ranking = sorted(
                comparison['comparison_data'].items(),
                key=lambda x: x[1]['execution_time']['mean']
            )
            comparison['ranking']['by_speed'] = [func for func, _ in time_ranking]
            
            # 按内存使用排名
            memory_ranking = sorted(
                comparison['comparison_data'].items(),
                key=lambda x: x[1]['memory_usage']['mean']
            )
            comparison['ranking']['by_memory'] = [func for func, _ in memory_ranking]
        
        return comparison

# 导出主要接口
__all__ = [
    'PerformanceMonitor',
    'PerformanceMetric',
    'AggregatedMetrics',
    'PerformanceAnalyzer',
    'monitor_performance',
    'global_monitor'
]