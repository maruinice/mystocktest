# -*- coding: utf-8 -*-
"""
Tushare数据API
提供股票基础数据、行情数据、财务数据等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import pandas as pd
from pydantic import BaseModel

from app.core.database import get_db
from app.services.tushare_service import tushare_service
from app.services.data_storage_service import data_storage_service
from app.tasks.data_sync_tasks import (
    sync_stock_basic_data, 
    sync_daily_quotes, 
    sync_financial_data,
    sync_incremental_data
)
from app.core.redis_client import redis_client

router = APIRouter(prefix="/api/tushare", tags=["Tushare数据"])

# 数据模型定义
class DataSyncRequest(BaseModel):
    """数据同步请求模型"""
    data_type: str
    parameters: Optional[Dict[str, Any]] = {}
    force_refresh: Optional[bool] = False

class DataQualityResponse(BaseModel):
    """数据质量响应模型"""
    is_valid: bool
    quality_report: Dict[str, Any]

class APIResponse(BaseModel):
    """API响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None
    count: Optional[int] = None

@router.get("/stock/basic", summary="获取股票基础信息")
async def get_stock_basic_info(
    ts_code: Optional[str] = Query(None, description="股票代码"),
    name: Optional[str] = Query(None, description="股票名称"),
    exchange: Optional[str] = Query(None, description="交易所"),
    market: Optional[str] = Query(None, description="市场类型"),
    is_hs: Optional[str] = Query(None, description="是否沪深港通标的"),
    list_status: Optional[str] = Query("L", description="上市状态"),
    limit: int = Query(100, description="单次返回数据量"),
    offset: int = Query(0, description="数据偏移量"),
    db: Session = Depends(get_db)
):
    """获取股票基础信息"""
    try:
        # 构建查询参数
        params = {
            "ts_code": ts_code,
            "name": name,
            "exchange": exchange,
            "market": market,
            "is_hs": is_hs,
            "list_status": list_status,
            "limit": limit,
            "offset": offset
        }
        
        # 过滤空值参数
        params = {k: v for k, v in params.items() if v is not None}
        
        # 调用tushare服务
        result = await tushare_service.get_stock_basic(**params)
        
        if result is None:
            raise HTTPException(status_code=404, detail="未找到相关数据")
        
        return APIResponse(
            success=True,
            message="获取股票基础信息成功",
            data=result.to_dict('records') if hasattr(result, 'to_dict') else result,
            count=len(result) if hasattr(result, '__len__') else 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票基础信息失败: {str(e)}")

@router.get("/index/basic", summary="获取指数基础信息")
async def get_index_basic_info(
    market: Optional[str] = Query(None, description="交易所或服务商"),
    publisher: Optional[str] = Query(None, description="发布商"),
    category: Optional[str] = Query(None, description="指数类别"),
    db: Session = Depends(get_db)
):
    """获取指数基础信息"""
    try:
        params = {
            "market": market,
            "publisher": publisher,
            "category": category
        }
        
        # 过滤空值参数
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await tushare_service.get_index_basic(**params)
        
        return APIResponse(
            success=True,
            message="获取指数基础信息成功",
            data=result.to_dict('records') if hasattr(result, 'to_dict') else result,
            count=len(result) if hasattr(result, '__len__') else 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指数基础信息失败: {str(e)}")

@router.get("/daily", summary="获取日线行情")
async def get_daily_quotes(
    ts_code: Optional[str] = Query(None, description="股票代码"),
    trade_date: Optional[str] = Query(None, description="交易日期"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取日线行情数据"""
    try:
        params = {
            "ts_code": ts_code,
            "trade_date": trade_date,
            "start_date": start_date,
            "end_date": end_date
        }
        
        # 过滤空值参数
        params = {k: v for k, v in params.items() if v is not None}
        
        if not any(params.values()):
            raise HTTPException(status_code=400, detail="请至少提供一个查询参数")
        
        result = await tushare_service.get_daily_quotes(**params)
        
        return APIResponse(
            success=True,
            message="获取日线行情成功",
            data=result.to_dict('records') if hasattr(result, 'to_dict') else result,
            count=len(result) if hasattr(result, '__len__') else 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日线行情失败: {str(e)}")

@router.get("/minute", summary="获取分钟级行情")
async def get_minute_quotes(
    ts_code: str = Query(..., description="股票代码"),
    freq: str = Query("1min", description="数据频度"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取分钟级行情数据"""
    try:
        params = {
            "ts_code": ts_code,
            "freq": freq,
            "start_date": start_date,
            "end_date": end_date
        }
        
        # 过滤空值参数
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await tushare_service.get_minute_quotes(**params)
        
        return APIResponse(
            success=True,
            message="获取分钟级行情成功",
            data=result.to_dict('records') if hasattr(result, 'to_dict') else result,
            count=len(result) if hasattr(result, '__len__') else 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分钟级行情失败: {str(e)}")

@router.get("/income", summary="获取利润表数据")
async def get_income_statement(
    ts_code: Optional[str] = Query(None, description="股票代码"),
    ann_date: Optional[str] = Query(None, description="公告日期"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    period: Optional[str] = Query(None, description="报告期"),
    report_type: Optional[str] = Query(None, description="报告类型"),
    comp_type: Optional[str] = Query(None, description="公司类型"),
    db: Session = Depends(get_db)
):
    """获取利润表数据"""
    try:
        params = {
            "ts_code": ts_code,
            "ann_date": ann_date,
            "start_date": start_date,
            "end_date": end_date,
            "period": period,
            "report_type": report_type,
            "comp_type": comp_type
        }
        
        # 过滤空值参数
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await tushare_service.get_income_statement(**params)
        
        return APIResponse(
            success=True,
            message="获取利润表数据成功",
            data=result.to_dict('records') if hasattr(result, 'to_dict') else result,
            count=len(result) if hasattr(result, '__len__') else 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取利润表数据失败: {str(e)}")

@router.post("/sync/stock-basic", summary="同步股票基础数据")
async def sync_stock_basic(
    background_tasks: BackgroundTasks,
    request: DataSyncRequest,
    db: Session = Depends(get_db)
):
    """同步股票基础数据"""
    try:
        # 添加后台任务
        background_tasks.add_task(
            sync_stock_basic_data,
            **request.parameters,
            force_refresh=request.force_refresh
        )
        
        return APIResponse(
            success=True,
            message="股票基础数据同步任务已启动"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动同步任务失败: {str(e)}")

@router.post("/sync/daily-quotes", summary="同步日线行情数据")
async def sync_daily_quotes_data(
    background_tasks: BackgroundTasks,
    request: DataSyncRequest,
    db: Session = Depends(get_db)
):
    """同步日线行情数据"""
    try:
        background_tasks.add_task(
            sync_daily_quotes,
            **request.parameters,
            force_refresh=request.force_refresh
        )
        
        return APIResponse(
            success=True,
            message="日线行情数据同步任务已启动"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动同步任务失败: {str(e)}")

@router.post("/sync/financial", summary="同步财务数据")
async def sync_financial_data_task(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    request: DataSyncRequest = None
):
    """同步财务数据"""
    try:
        params = request.parameters if request else {}
        force_refresh = request.force_refresh if request else False
        
        background_tasks.add_task(
            sync_financial_data,
            **params,
            force_refresh=force_refresh
        )
        
        return APIResponse(
            success=True,
            message="财务数据同步任务已启动"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动同步任务失败: {str(e)}")

@router.post("/sync/incremental", summary="增量数据同步")
async def sync_incremental_data_task(
    background_tasks: BackgroundTasks,
    request: DataSyncRequest,
    db: Session = Depends(get_db)
):
    """增量数据同步"""
    try:
        background_tasks.add_task(
            sync_incremental_data,
            **request.parameters,
            force_refresh=request.force_refresh
        )
        
        return APIResponse(
            success=True,
            message="增量数据同步任务已启动"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动同步任务失败: {str(e)}")

@router.get("/data-quality/check", summary="数据质量检查")
async def check_data_quality(
    table_name: str = Query(..., description="表名"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """检查数据质量"""
    try:
        # 调用数据质量检查服务
        quality_report = await data_storage_service.check_data_quality(
            table_name=table_name,
            start_date=start_date,
            end_date=end_date
        )
        
        # 判断数据质量是否合格
        is_valid = (
            quality_report.get('completeness', 0) >= 0.95 and
            quality_report.get('accuracy', 0) >= 0.98 and
            quality_report.get('consistency', 0) >= 0.99
        )
        
        return DataQualityResponse(
            is_valid=is_valid,
            quality_report=quality_report
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据质量检查失败: {str(e)}")

@router.delete("/data/cleanup", summary="数据清理")
async def cleanup_data(
    table_name: str = Query(..., description="表名"),
    cleanup_type: str = Query("duplicates", description="清理类型"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    dry_run: bool = Query(True, description="是否为试运行"),
    db: Session = Depends(get_db)
):
    """数据清理"""
    try:
        result = await data_storage_service.cleanup_data(
            table_name=table_name,
            cleanup_type=cleanup_type,
            start_date=start_date,
            end_date=end_date,
            dry_run=dry_run
        )
        
        return APIResponse(
            success=True,
            message=f"数据清理{'预览' if dry_run else '执行'}完成",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据清理失败: {str(e)}")

@router.delete("/cache/clear", summary="清理缓存")
async def clear_cache(
    cache_type: str = Query("all", description="缓存类型"),
    pattern: Optional[str] = Query(None, description="缓存键模式")
):
    """清理Redis缓存"""
    try:
        if cache_type == "all":
            # 清理所有tushare相关缓存
            pattern = "tushare:*"
        elif pattern is None:
            pattern = f"tushare:{cache_type}:*"
        
        # 获取匹配的键
        keys = redis_client.keys(pattern)
        
        if keys:
            # 删除匹配的键
            deleted_count = redis_client.delete(*keys)
        else:
            deleted_count = 0
        
        return APIResponse(
            success=True,
            message=f"成功清理 {deleted_count} 个缓存项",
            data={
                "deleted_count": deleted_count,
                "pattern": pattern
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")








