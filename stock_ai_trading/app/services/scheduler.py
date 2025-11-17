"""
核心调度服务
负责定时调度、数据聚合、决策生成和分发
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from ..config.settings import settings
from .performance_monitor import monitor_performance

logger = logging.getLogger(__name__)

class SchedulerStatus(Enum):
    """调度器状态"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class ScheduledTask:
    """调度任务"""
    task_id: str
    name: str
    func: Callable
    interval_minutes: int
    next_run: datetime
    last_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    error_count: int = 0
    max_retries: int = 3
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    start_time: datetime
    end_time: datetime
    duration: float
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TradingTimeManager:
    """交易时间管理器"""
    
    def __init__(self):
        # A股交易时间
        self.morning_start = time(9, 30)
        self.morning_end = time(11, 30)
        self.afternoon_start = time(13, 0)
        self.afternoon_end = time(15, 0)
        
        # 节假日列表（需要定期更新）
        self.holidays = set([
            # 2024年节假日
            "2024-01-01",  # 元旦
            "2024-02-10", "2024-02-11", "2024-02-12", "2024-02-13", 
            "2024-02-14", "2024-02-15", "2024-02-16", "2024-02-17",  # 春节
            "2024-04-04", "2024-04-05", "2024-04-06",  # 清明节
            "2024-05-01", "2024-05-02", "2024-05-03",  # 劳动节
            "2024-06-10",  # 端午节
            "2024-09-15", "2024-09-16", "2024-09-17",  # 中秋节
            "2024-10-01", "2024-10-02", "2024-10-03", "2024-10-04",
            "2024-10-05", "2024-10-06", "2024-10-07",  # 国庆节
            # 2025年节假日
            "2025-01-01",  # 元旦
            "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",
            "2025-02-01", "2025-02-02", "2025-02-03", "2025-02-04",  # 春节
        ])
    
    def is_trading_day(self, date: datetime) -> bool:
        """判断是否为交易日"""
        # 周末不交易
        if date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False
        
        # 节假日不交易
        date_str = date.strftime("%Y-%m-%d")
        if date_str in self.holidays:
            return False
        
        return True
    
    def is_trading_time(self, dt: datetime) -> bool:
        """判断是否为交易时间"""
        if not self.is_trading_day(dt):
            return False
        
        current_time = dt.time()
        
        # 上午交易时间
        if self.morning_start <= current_time <= self.morning_end:
            return True
        
        # 下午交易时间
        if self.afternoon_start <= current_time <= self.afternoon_end:
            return True
        
        return False
    
    def get_next_trading_time(self, from_time: datetime) -> datetime:
        """获取下一个交易时间"""
        current = from_time
        
        while True:
            if self.is_trading_day(current):
                current_time = current.time()
                
                # 如果在上午交易时间之前
                if current_time < self.morning_start:
                    return current.replace(
                        hour=self.morning_start.hour,
                        minute=self.morning_start.minute,
                        second=0,
                        microsecond=0
                    )
                
                # 如果在上午交易时间内
                elif self.morning_start <= current_time <= self.morning_end:
                    return current
                
                # 如果在午休时间
                elif self.morning_end < current_time < self.afternoon_start:
                    return current.replace(
                        hour=self.afternoon_start.hour,
                        minute=self.afternoon_start.minute,
                        second=0,
                        microsecond=0
                    )
                
                # 如果在下午交易时间内
                elif self.afternoon_start <= current_time <= self.afternoon_end:
                    return current
                
                # 如果在下午交易时间之后，跳到下一个交易日
                else:
                    current = current + timedelta(days=1)
                    current = current.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                # 非交易日，跳到下一天
                current = current + timedelta(days=1)
                current = current.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def get_trading_sessions_today(self, date: datetime) -> List[tuple]:
        """获取今日交易时段"""
        if not self.is_trading_day(date):
            return []
        
        morning_start = date.replace(
            hour=self.morning_start.hour,
            minute=self.morning_start.minute,
            second=0,
            microsecond=0
        )
        morning_end = date.replace(
            hour=self.morning_end.hour,
            minute=self.morning_end.minute,
            second=0,
            microsecond=0
        )
        afternoon_start = date.replace(
            hour=self.afternoon_start.hour,
            minute=self.afternoon_start.minute,
            second=0,
            microsecond=0
        )
        afternoon_end = date.replace(
            hour=self.afternoon_end.hour,
            minute=self.afternoon_end.minute,
            second=0,
            microsecond=0
        )
        
        return [
            (morning_start, morning_end),
            (afternoon_start, afternoon_end)
        ]

class CoreScheduler:
    """核心调度器"""
    
    def __init__(self):
        self.status = SchedulerStatus.STOPPED
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_results: List[TaskResult] = []
        self.trading_time_manager = TradingTimeManager()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'total_tasks_executed': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'skipped_tasks': 0,
            'start_time': None,
            'last_execution': None
        }
    
    def add_task(self, task: ScheduledTask):
        """添加调度任务"""
        with self.lock:
            self.tasks[task.task_id] = task
            logger.info(f"添加调度任务: {task.name} (ID: {task.task_id})")
    
    def remove_task(self, task_id: str):
        """移除调度任务"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.info(f"移除调度任务: {task_id}")
    
    def enable_task(self, task_id: str):
        """启用任务"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = True
                logger.info(f"启用任务: {task_id}")
    
    def disable_task(self, task_id: str):
        """禁用任务"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = False
                logger.info(f"禁用任务: {task_id}")
    
    @monitor_performance
    def execute_task(self, task: ScheduledTask) -> TaskResult:
        """执行单个任务"""
        start_time = datetime.now()
        task.status = TaskStatus.RUNNING
        
        try:
            logger.info(f"开始执行任务: {task.name}")
            
            # 检查是否为交易时间
            if not self.trading_time_manager.is_trading_time(start_time):
                logger.info(f"非交易时间，跳过任务: {task.name}")
                task.status = TaskStatus.SKIPPED
                self.stats['skipped_tasks'] += 1
                
                return TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.SKIPPED,
                    start_time=start_time,
                    end_time=datetime.now(),
                    duration=0,
                    metadata={'reason': 'non_trading_time'}
                )
            
            # 执行任务
            result = task.func()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            task.status = TaskStatus.COMPLETED
            task.last_run = start_time
            task.error_count = 0
            task.next_run = start_time + timedelta(minutes=task.interval_minutes)
            
            self.stats['successful_tasks'] += 1
            
            logger.info(f"任务执行成功: {task.name}, 耗时: {duration:.2f}s")
            
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                result=result
            )
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            task.status = TaskStatus.FAILED
            task.error_count += 1
            
            # 如果错误次数超过最大重试次数，禁用任务
            if task.error_count >= task.max_retries:
                task.enabled = False
                logger.error(f"任务 {task.name} 错误次数过多，已禁用")
            
            self.stats['failed_tasks'] += 1
            
            logger.error(f"任务执行失败: {task.name}, 错误: {str(e)}")
            
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                error=str(e)
            )
    
    def _scheduler_loop(self):
        """调度器主循环"""
        logger.info("调度器主循环启动")
        
        while not self.stop_event.is_set():
            try:
                current_time = datetime.now()
                tasks_to_run = []
                
                # 检查需要执行的任务
                with self.lock:
                    for task in self.tasks.values():
                        if (task.enabled and 
                            task.status != TaskStatus.RUNNING and
                            current_time >= task.next_run):
                            tasks_to_run.append(task)
                
                # 执行任务
                if tasks_to_run:
                    futures = []
                    for task in tasks_to_run:
                        future = self.executor.submit(self.execute_task, task)
                        futures.append(future)
                    
                    # 等待任务完成
                    for future in as_completed(futures, timeout=300):  # 5分钟超时
                        try:
                            result = future.result()
                            self.task_results.append(result)
                            self.stats['total_tasks_executed'] += 1
                            self.stats['last_execution'] = datetime.now()
                            
                            # 保持结果列表大小
                            if len(self.task_results) > 1000:
                                self.task_results = self.task_results[-500:]
                                
                        except Exception as e:
                            logger.error(f"任务执行异常: {str(e)}")
                
                # 休眠30秒后继续检查
                self.stop_event.wait(30)
                
            except Exception as e:
                logger.error(f"调度器循环异常: {str(e)}")
                self.stop_event.wait(60)  # 出错后等待1分钟
    
    def start(self):
        """启动调度器"""
        if self.status == SchedulerStatus.RUNNING:
            logger.warning("调度器已在运行中")
            return
        
        self.status = SchedulerStatus.RUNNING
        self.stop_event.clear()
        self.stats['start_time'] = datetime.now()
        
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("核心调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if self.status != SchedulerStatus.RUNNING:
            logger.warning("调度器未在运行")
            return
        
        self.status = SchedulerStatus.STOPPED
        self.stop_event.set()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        self.executor.shutdown(wait=True)
        
        logger.info("核心调度器已停止")
    
    def pause(self):
        """暂停调度器"""
        if self.status == SchedulerStatus.RUNNING:
            self.status = SchedulerStatus.PAUSED
            logger.info("调度器已暂停")
    
    def resume(self):
        """恢复调度器"""
        if self.status == SchedulerStatus.PAUSED:
            self.status = SchedulerStatus.RUNNING
            logger.info("调度器已恢复")
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        with self.lock:
            task_summary = {}
            for status in TaskStatus:
                task_summary[status.value] = sum(
                    1 for task in self.tasks.values() 
                    if task.status == status
                )
            
            # 处理stats中的datetime对象
            stats_copy = self.stats.copy()
            for key, value in stats_copy.items():
                if isinstance(value, datetime):
                    stats_copy[key] = value.isoformat()
            
            return {
                'scheduler_status': self.status.value,
                'total_tasks': len(self.tasks),
                'task_summary': task_summary,
                'stats': stats_copy,
                'trading_time': {
                    'is_trading_day': self.trading_time_manager.is_trading_day(datetime.now()),
                    'is_trading_time': self.trading_time_manager.is_trading_time(datetime.now()),
                    'next_trading_time': self.trading_time_manager.get_next_trading_time(datetime.now()).isoformat()
                }
            }
    
    def get_task_history(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务执行历史"""
        results = self.task_results[-limit:]
        
        if task_id:
            results = [r for r in results if r.task_id == task_id]
        
        return [
            {
                'task_id': r.task_id,
                'status': r.status.value,
                'start_time': r.start_time.isoformat(),
                'end_time': r.end_time.isoformat(),
                'duration': r.duration,
                'error': r.error,
                'metadata': r.metadata
            }
            for r in results
        ]

# 全局调度器实例
global_scheduler = CoreScheduler()

# 导出主要接口
__all__ = [
    'CoreScheduler',
    'ScheduledTask',
    'TaskResult',
    'TradingTimeManager',
    'SchedulerStatus',
    'TaskStatus',
    'global_scheduler'
]