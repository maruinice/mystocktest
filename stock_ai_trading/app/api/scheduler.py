# -*- coding: utf-8 -*-
"""
调度器API模块
提供任务调度和管理的REST API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
import asyncio
import json

router = APIRouter(prefix="/api/scheduler", tags=["任务调度"])

# 数据模型定义
class SchedulerResponse(BaseModel):
    """调度器响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应信息")

class TaskRequest(BaseModel):
    """任务请求模型"""
    name: str = Field(..., description="任务名称")
    function: str = Field(..., description="执行函数")
    schedule: str = Field(..., description="调度表达式")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="任务参数")
    enabled: bool = Field(default=True, description="是否启用")

class TaskStatus(BaseModel):
    """任务状态模型"""
    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务状态")
    last_run: Optional[datetime] = Field(None, description="上次执行时间")
    next_run: Optional[datetime] = Field(None, description="下次执行时间")
    success_count: int = Field(default=0, description="成功次数")
    error_count: int = Field(default=0, description="错误次数")

# 全局任务调度器
class TaskScheduler:
    def __init__(self):
        self.tasks = {}
        self.running_tasks = {}
        self.task_history = []
        self.is_running = False
        
    def add_task(self, task_id: str, task_config: Dict[str, Any]):
        """添加任务"""
        self.tasks[task_id] = {
            "id": task_id,
            "name": task_config.get("name", task_id),
            "function": task_config.get("function"),
            "schedule": task_config.get("schedule"),
            "parameters": task_config.get("parameters", {}),
            "enabled": task_config.get("enabled", True),
            "created_at": datetime.now(),
            "last_run": None,
            "next_run": None,
            "success_count": 0,
            "error_count": 0,
            "status": "pending"
        }
        
    def remove_task(self, task_id: str):
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
            
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        return self.tasks.get(task_id)
        
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return list(self.tasks.values())
        
    def start_scheduler(self):
        """启动调度器"""
        self.is_running = True
        
    def stop_scheduler(self):
        """停止调度器"""
        self.is_running = False
        
    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "enabled_tasks": len([t for t in self.tasks.values() if t["enabled"]]),
            "disabled_tasks": len([t for t in self.tasks.values() if not t["enabled"]])
        }
        
    async def execute_task(self, task_id: str):
        """执行任务"""
        if task_id not in self.tasks:
            raise ValueError(f"任务 {task_id} 不存在")
            
        task = self.tasks[task_id]
        if not task["enabled"]:
            raise ValueError(f"任务 {task_id} 已禁用")
            
        try:
            # 标记任务为运行中
            self.running_tasks[task_id] = datetime.now()
            task["status"] = "running"
            task["last_run"] = datetime.now()
            
            # 模拟任务执行
            await asyncio.sleep(1)
            
            # 任务执行成功
            task["success_count"] += 1
            task["status"] = "completed"
            
            # 记录历史
            self.task_history.append({
                "task_id": task_id,
                "task_name": task["name"],
                "status": "success",
                "start_time": self.running_tasks[task_id].isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": (datetime.now() - self.running_tasks[task_id]).total_seconds()
            })
            
        except Exception as e:
            # 任务执行失败
            task["error_count"] += 1
            task["status"] = "failed"
            
            # 记录历史
            self.task_history.append({
                "task_id": task_id,
                "task_name": task["name"],
                "status": "error",
                "start_time": self.running_tasks[task_id].isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": (datetime.now() - self.running_tasks[task_id]).total_seconds(),
                "error": str(e)
            })
            
            raise e
            
        finally:
            # 清理运行状态
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
                
        # 保持历史记录在合理范围内
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]

# 全局调度器实例
global_scheduler = TaskScheduler()

@router.get("/status", summary="获取调度器状态")
async def get_scheduler_status():
    """获取调度器运行状态"""
    try:
        status = global_scheduler.get_scheduler_status()
        
        return SchedulerResponse(
            success=True,
            message="获取调度器状态成功",
            data=status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取调度器状态失败: {str(e)}")

@router.post("/start", summary="启动调度器")
async def start_scheduler():
    """启动任务调度器"""
    try:
        global_scheduler.start_scheduler()
        
        return SchedulerResponse(
            success=True,
            message="调度器启动成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动调度器失败: {str(e)}")

@router.post("/stop", summary="停止调度器")
async def stop_scheduler():
    """停止任务调度器"""
    try:
        global_scheduler.stop_scheduler()
        
        return SchedulerResponse(
            success=True,
            message="调度器停止成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止调度器失败: {str(e)}")

@router.get("/tasks", summary="获取所有任务")
async def get_all_tasks():
    """获取所有调度任务"""
    try:
        tasks = global_scheduler.get_all_tasks()
        
        return SchedulerResponse(
            success=True,
            message="获取任务列表成功",
            data={
                "tasks": tasks,
                "count": len(tasks)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.get("/tasks/{task_id}", summary="获取任务详情")
async def get_task_detail(task_id: str):
    """获取指定任务的详细信息"""
    try:
        task = global_scheduler.get_task_status(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        return SchedulerResponse(
            success=True,
            message=f"获取任务 {task_id} 详情成功",
            data=task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")

@router.post("/tasks", summary="创建新任务")
async def create_task(task_request: TaskRequest):
    """创建新的调度任务"""
    try:
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task_config = {
            "name": task_request.name,
            "function": task_request.function,
            "schedule": task_request.schedule,
            "parameters": task_request.parameters,
            "enabled": task_request.enabled
        }
        
        global_scheduler.add_task(task_id, task_config)
        
        return SchedulerResponse(
            success=True,
            message=f"创建任务成功: {task_request.name}",
            data={
                "task_id": task_id,
                "task_config": task_config
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@router.put("/tasks/{task_id}", summary="更新任务")
async def update_task(task_id: str, task_request: TaskRequest):
    """更新指定任务的配置"""
    try:
        if not global_scheduler.get_task_status(task_id):
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        task_config = {
            "name": task_request.name,
            "function": task_request.function,
            "schedule": task_request.schedule,
            "parameters": task_request.parameters,
            "enabled": task_request.enabled
        }
        
        global_scheduler.add_task(task_id, task_config)
        
        return SchedulerResponse(
            success=True,
            message=f"更新任务成功: {task_id}",
            data={
                "task_id": task_id,
                "task_config": task_config
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新任务失败: {str(e)}")

@router.delete("/tasks/{task_id}", summary="删除任务")
async def delete_task(task_id: str):
    """删除指定的调度任务"""
    try:
        if not global_scheduler.get_task_status(task_id):
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        global_scheduler.remove_task(task_id)
        
        return SchedulerResponse(
            success=True,
            message=f"删除任务成功: {task_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@router.post("/tasks/{task_id}/execute", summary="执行任务")
async def execute_task(task_id: str, background_tasks: BackgroundTasks):
    """立即执行指定任务"""
    try:
        if not global_scheduler.get_task_status(task_id):
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        # 在后台执行任务
        background_tasks.add_task(global_scheduler.execute_task, task_id)
        
        return SchedulerResponse(
            success=True,
            message=f"任务 {task_id} 已开始执行"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行任务失败: {str(e)}")

@router.get("/history", summary="获取任务执行历史")
async def get_task_history(
    limit: int = Query(100, description="返回记录数量限制"),
    task_id: Optional[str] = Query(None, description="任务ID过滤")
):
    """获取任务执行历史记录"""
    try:
        history = global_scheduler.task_history
        
        # 按任务ID过滤
        if task_id:
            history = [h for h in history if h["task_id"] == task_id]
        
        # 限制返回数量
        history = history[-limit:] if limit > 0 else history
        
        return SchedulerResponse(
            success=True,
            message="获取任务执行历史成功",
            data={
                "history": history,
                "count": len(history),
                "total_count": len(global_scheduler.task_history)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务执行历史失败: {str(e)}")

@router.delete("/history", summary="清空执行历史")
async def clear_task_history():
    """清空任务执行历史记录"""
    try:
        count = len(global_scheduler.task_history)
        global_scheduler.task_history.clear()
        
        return SchedulerResponse(
            success=True,
            message=f"清空任务执行历史成功，共清空 {count} 条记录",
            data={"cleared_count": count}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空任务执行历史失败: {str(e)}")

@router.get("/health", summary="调度器健康检查")
async def scheduler_health_check():
    """检查调度器健康状态"""
    try:
        status = global_scheduler.get_scheduler_status()
        
        # 判断健康状态
        health_status = "healthy"
        if not status["is_running"]:
            health_status = "stopped"
        elif len(global_scheduler.running_tasks) > 10:
            health_status = "overloaded"
        
        return SchedulerResponse(
            success=True,
            message="调度器健康检查完成",
            data={
                "health_status": health_status,
                "scheduler_status": status,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调度器健康检查失败: {str(e)}")









