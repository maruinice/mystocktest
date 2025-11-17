# -*- coding: utf-8 -*-
"""
性能监控API模块
提供系统性能监控和分析服务
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio
import time
import psutil
import logging

router = APIRouter(prefix="/api/performance", tags=["性能监控"])

# 数据模型定义
class PerformanceResponse(BaseModel):
    """性能监控响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应信息")

class SystemMetrics(BaseModel):
    """系统指标模型"""
    cpu_percent: float = Field(..., description="CPU使用率")
    memory_percent: float = Field(..., description="内存使用率")
    disk_usage: Dict[str, float] = Field(..., description="磁盘使用情况")
    network_io: Dict[str, int] = Field(..., description="网络IO统计")

class PerformanceAlert(BaseModel):
    """性能告警模型"""
    level: str = Field(..., description="告警级别")
    message: str = Field(..., description="告警信息")
    timestamp: datetime = Field(..., description="告警时间")
    metric: str = Field(..., description="相关指标")

# 全局性能监控器
class PerformanceMonitor:
    def __init__(self):
        self.metrics_history = []
        self.alerts = []
        self.slow_functions = []
        
    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage={
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            network_io={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        )
    
    def add_metric(self, metric_name: str, value: float, timestamp: datetime = None):
        """添加性能指标"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.metrics_history.append({
            "name": metric_name,
            "value": value,
            "timestamp": timestamp.isoformat()
        })
        
        # 保持历史记录在合理范围内
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def add_alert(self, level: str, message: str, metric: str):
        """添加性能告警"""
        alert = PerformanceAlert(
            level=level,
            message=message,
            timestamp=datetime.now(),
            metric=metric
        )
        self.alerts.append(alert)
        
        # 保持告警记录在合理范围内
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def record_slow_function(self, function_name: str, execution_time: float, threshold: float = 1.0):
        """记录慢函数"""
        if execution_time > threshold:
            self.slow_functions.append({
                "function_name": function_name,
                "execution_time": execution_time,
                "threshold": threshold,
                "timestamp": datetime.now().isoformat()
            })
            
            # 保持慢函数记录在合理范围内
            if len(self.slow_functions) > 100:
                self.slow_functions = self.slow_functions[-100:]

# 全局监控器实例
global_monitor = PerformanceMonitor()

@router.get("/health", summary="API健康检查")
async def get_health_status():
    """获取API健康状态"""
    try:
        system_metrics = global_monitor.get_system_metrics()
        
        # 判断系统健康状态
        health_status = "healthy"
        if system_metrics.cpu_percent > 80:
            health_status = "warning"
        if system_metrics.memory_percent > 90:
            health_status = "critical"
        
        return PerformanceResponse(
            success=True,
            message="健康检查完成",
            data={
                "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "system_metrics": system_metrics.dict()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

@router.get("/metrics", summary="获取性能指标")
async def get_performance_metrics(
    limit: int = Query(100, description="返回记录数量限制"),
    metric_name: Optional[str] = Query(None, description="指标名称过滤")
):
    """获取系统性能指标"""
    try:
        metrics = global_monitor.metrics_history
        
        # 按指标名称过滤
        if metric_name:
            metrics = [m for m in metrics if m["name"] == metric_name]
        
        # 限制返回数量
        metrics = metrics[-limit:] if limit > 0 else metrics
        
        return PerformanceResponse(
            success=True,
            message="获取性能指标成功",
            data={
                "metrics": metrics,
                "count": len(metrics),
                "total_count": len(global_monitor.metrics_history)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")

@router.get("/alerts", summary="获取性能告警")
async def get_performance_alerts(
    level: Optional[str] = Query(None, description="告警级别过滤"),
    limit: int = Query(50, description="返回记录数量限制")
):
    """获取性能告警信息"""
    try:
        alerts = global_monitor.alerts
        
        # 按告警级别过滤
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        # 限制返回数量
        alerts = alerts[-limit:] if limit > 0 else alerts
        
        # 转换为字典格式
        alert_data = [
            {
                "level": alert.level,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metric": alert.metric
            }
            for alert in alerts
        ]
        
        return PerformanceResponse(
            success=True,
            message="获取性能告警成功",
            data={
                "alerts": alert_data,
                "count": len(alert_data),
                "total_count": len(global_monitor.alerts)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能告警失败: {str(e)}")

@router.get("/slow-functions", summary="获取慢函数统计")
async def get_slow_functions(
    threshold: float = Query(1.0, description="执行时间阈值（秒）"),
    limit: int = Query(50, description="返回记录数量限制")
):
    """获取慢函数执行统计"""
    try:
        slow_functions = global_monitor.slow_functions
        
        # 按阈值过滤
        slow_functions = [f for f in slow_functions if f["execution_time"] >= threshold]
        
        # 限制返回数量
        slow_functions = slow_functions[-limit:] if limit > 0 else slow_functions
        
        return PerformanceResponse(
            success=True,
            message=f"获取慢函数统计成功，阈值: {threshold}秒",
            data={
                "slow_functions": slow_functions,
                "count": len(slow_functions),
                "threshold": threshold
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取慢函数统计失败: {str(e)}")

@router.post("/metrics", summary="添加性能指标")
async def add_performance_metric(
    metric_name: str,
    value: float,
    timestamp: Optional[datetime] = None
):
    """添加自定义性能指标"""
    try:
        global_monitor.add_metric(metric_name, value, timestamp)
        
        return PerformanceResponse(
            success=True,
            message=f"添加性能指标成功: {metric_name}",
            data={
                "metric_name": metric_name,
                "value": value,
                "timestamp": (timestamp or datetime.now()).isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加性能指标失败: {str(e)}")

@router.post("/alerts", summary="添加性能告警")
async def add_performance_alert(
    level: str,
    message: str,
    metric: str
):
    """添加性能告警"""
    try:
        global_monitor.add_alert(level, message, metric)
        
        return PerformanceResponse(
            success=True,
            message="添加性能告警成功",
            data={
                "level": level,
                "message": message,
                "metric": metric,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加性能告警失败: {str(e)}")

@router.get("/system", summary="获取系统资源使用情况")
async def get_system_resources():
    """获取当前系统资源使用情况"""
    try:
        system_metrics = global_monitor.get_system_metrics()
        
        return PerformanceResponse(
            success=True,
            message="获取系统资源使用情况成功",
            data=system_metrics.dict()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统资源使用情况失败: {str(e)}")

@router.delete("/metrics", summary="清空性能指标历史")
async def clear_performance_metrics():
    """清空性能指标历史记录"""
    try:
        count = len(global_monitor.metrics_history)
        global_monitor.metrics_history.clear()
        
        return PerformanceResponse(
            success=True,
            message=f"清空性能指标历史成功，共清空 {count} 条记录",
            data={"cleared_count": count}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空性能指标历史失败: {str(e)}")

@router.delete("/alerts", summary="清空性能告警历史")
async def clear_performance_alerts():
    """清空性能告警历史记录"""
    try:
        count = len(global_monitor.alerts)
        global_monitor.alerts.clear()
        
        return PerformanceResponse(
            success=True,
            message=f"清空性能告警历史成功，共清空 {count} 条记录",
            data={"cleared_count": count}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空性能告警历史失败: {str(e)}")








