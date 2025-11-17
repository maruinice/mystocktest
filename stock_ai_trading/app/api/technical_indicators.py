# -*- coding: utf-8 -*-
"""
技术指标API模块
提供各类技术指标的计算和分析服务
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime, date
import pandas as pd
import json

from app.services.technical_indicators import TechnicalIndicatorService, IndicatorType
from app.services.indicators.trend_indicators import (
    MovingAverageIndicator, EMAIndicator, MACDIndicator, BollingerBandsIndicator,
    ParabolicSARIndicator, ADXIndicator
)
from app.services.indicators.momentum_indicators import (
    RSIIndicator, KDJIndicator, CCIIndicator, WilliamsRIndicator,
    StochasticIndicator, ROCIndicator, MomentumIndicator, UltimateOscillatorIndicator
)
from app.services.indicators.volume_indicators import (
    OBVIndicator, VWAPIndicator, VolumeRatioIndicator, AccumulationDistributionIndicator,
    ChaikinOscillatorIndicator, MoneyFlowIndexIndicator
)
from app.services.indicators.volatility_indicators import (
    ATRIndicator, VolatilityChannelIndicator, HistoricalVolatilityIndicator,
    KeltnerChannelIndicator, DonchianChannelIndicator
)
from app.services.indicators.money_flow_indicators import (
    MainCapitalFlowIndicator, NorthboundCapitalIndicator, InstitutionalFlowIndicator,
    SmartMoneyIndicator, MoneyFlowIndexAdvancedIndicator, CapitalFlowAnalysisIndicator
)

router = APIRouter(prefix="/api/indicators", tags=["技术指标"])

# 初始化技术指标服务
indicator_service = TechnicalIndicatorService()

# 注册所有指标
def register_indicators():
    """注册所有技术指标"""
    # 趋势指标
    indicator_service.register_indicator("ma", MovingAverageIndicator())
    indicator_service.register_indicator("ema", EMAIndicator())
    indicator_service.register_indicator("macd", MACDIndicator())
    indicator_service.register_indicator("bollinger", BollingerBandsIndicator())
    indicator_service.register_indicator("sar", ParabolicSARIndicator())
    indicator_service.register_indicator("adx", ADXIndicator())
    
    # 动量指标
    indicator_service.register_indicator("rsi", RSIIndicator())
    indicator_service.register_indicator("kdj", KDJIndicator())
    indicator_service.register_indicator("cci", CCIIndicator())
    indicator_service.register_indicator("williams_r", WilliamsRIndicator())
    indicator_service.register_indicator("stochastic", StochasticIndicator())
    indicator_service.register_indicator("roc", ROCIndicator())
    indicator_service.register_indicator("momentum", MomentumIndicator())
    indicator_service.register_indicator("ultimate_oscillator", UltimateOscillatorIndicator())
    
    # 成交量指标
    indicator_service.register_indicator("obv", OBVIndicator())
    indicator_service.register_indicator("vwap", VWAPIndicator())
    indicator_service.register_indicator("volume_ratio", VolumeRatioIndicator())
    indicator_service.register_indicator("ad", AccumulationDistributionIndicator())
    indicator_service.register_indicator("chaikin_oscillator", ChaikinOscillatorIndicator())
    indicator_service.register_indicator("mfi", MoneyFlowIndexIndicator())
    
    # 波动率指标
    indicator_service.register_indicator("atr", ATRIndicator())
    indicator_service.register_indicator("volatility_channel", VolatilityChannelIndicator())
    indicator_service.register_indicator("historical_volatility", HistoricalVolatilityIndicator())
    indicator_service.register_indicator("keltner_channel", KeltnerChannelIndicator())
    indicator_service.register_indicator("donchian_channel", DonchianChannelIndicator())
    
    # 资金流向指标
    indicator_service.register_indicator("main_capital_flow", MainCapitalFlowIndicator())
    indicator_service.register_indicator("northbound_capital", NorthboundCapitalIndicator())
    indicator_service.register_indicator("institutional_flow", InstitutionalFlowIndicator())
    indicator_service.register_indicator("smart_money", SmartMoneyIndicator())
    indicator_service.register_indicator("mfi_advanced", MoneyFlowIndexAdvancedIndicator())
    indicator_service.register_indicator("capital_flow_analysis", CapitalFlowAnalysisIndicator())

# 注册指标
register_indicators()

# 数据模型定义
class IndicatorRequest(BaseModel):
    """技术指标计算请求"""
    symbol: str = Field(..., description="股票代码")
    data: List[Dict[str, Any]] = Field(..., description="价格数据")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="指标参数")

class BatchIndicatorRequest(BaseModel):
    """批量指标计算请求"""
    symbol: str = Field(..., description="股票代码")
    data: List[Dict[str, Any]] = Field(..., description="价格数据")
    indicators: List[str] = Field(..., description="指标名称列表")
    parameters: Optional[Dict[str, Dict[str, Any]]] = Field(default={}, description="各指标参数")

class IndicatorResponse(BaseModel):
    """指标计算响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

def convert_data_types(data: Dict[str, Any]) -> Dict[str, Any]:
    """转换数据类型，确保JSON序列化兼容"""
    converted = {}
    for key, value in data.items():
        if isinstance(value, pd.Series):
            converted[key] = value.tolist()
        elif isinstance(value, pd.DataFrame):
            converted[key] = value.to_dict('records')
        elif isinstance(value, (pd.Timestamp, datetime)):
            converted[key] = value.isoformat()
        elif isinstance(value, dict):
            converted[key] = convert_data_types(value)
        elif isinstance(value, list):
            converted[key] = [convert_data_types(item) if isinstance(item, dict) else item for item in value]
        else:
            converted[key] = value
    return converted

@router.get("/list", summary="获取所有可用指标")
async def get_available_indicators():
    """获取所有可用的技术指标列表"""
    try:
        indicators = indicator_service.get_available_indicators()
        
        return IndicatorResponse(
            success=True,
            message="获取指标列表成功",
            data={
                "indicators": indicators,
                "count": len(indicators)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标列表失败: {str(e)}")

@router.post("/calculate/{indicator_name}", summary="计算单个技术指标")
async def calculate_indicator(
    indicator_name: str,
    request: IndicatorRequest
):
    """计算指定的技术指标"""
    try:
        # 验证指标是否存在
        if not indicator_service.has_indicator(indicator_name):
            raise HTTPException(status_code=404, detail=f"指标 '{indicator_name}' 不存在")
        
        # 计算指标
        result = await indicator_service.calculate_indicator(
            indicator_name=indicator_name,
            symbol=request.symbol,
            data=request.data,
            parameters=request.parameters
        )
        
        # 转换数据类型
        converted_result = convert_data_types(result)
        
        return IndicatorResponse(
            success=True,
            message=f"计算指标 {indicator_name} 成功",
            data=converted_result,
            metadata={
                "indicator": indicator_name,
                "symbol": request.symbol,
                "data_points": len(request.data),
                "parameters": request.parameters
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算指标失败: {str(e)}")

@router.post("/batch-calculate", summary="批量计算技术指标")
async def batch_calculate_indicators(
    request: BatchIndicatorRequest
):
    """批量计算多个技术指标"""
    try:
        results = {}
        errors = {}
        
        for indicator_name in request.indicators:
            try:
                if not indicator_service.has_indicator(indicator_name):
                    errors[indicator_name] = f"指标 '{indicator_name}' 不存在"
                    continue
                
                # 获取该指标的参数
                params = request.parameters.get(indicator_name, {})
                
                # 计算指标
                result = await indicator_service.calculate_indicator(
                    indicator_name=indicator_name,
                    symbol=request.symbol,
                    data=request.data,
                    parameters=params
                )
                
                # 转换数据类型
                results[indicator_name] = convert_data_types(result)
                
            except Exception as e:
                errors[indicator_name] = str(e)
        
        return IndicatorResponse(
            success=len(results) > 0,
            message=f"批量计算完成，成功: {len(results)}, 失败: {len(errors)}",
            data={
                "results": results,
                "errors": errors if errors else None
            },
            metadata={
                "symbol": request.symbol,
                "requested_indicators": request.indicators,
                "successful_count": len(results),
                "error_count": len(errors)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量计算指标失败: {str(e)}")

@router.get("/info/{indicator_name}", summary="获取指标信息")
async def get_indicator_info(indicator_name: str):
    """获取指定指标的详细信息"""
    try:
        if not indicator_service.has_indicator(indicator_name):
            raise HTTPException(status_code=404, detail=f"指标 '{indicator_name}' 不存在")
        
        info = indicator_service.get_indicator_info(indicator_name)
        
        return IndicatorResponse(
            success=True,
            message=f"获取指标 {indicator_name} 信息成功",
            data=info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标信息失败: {str(e)}")

@router.get("/categories", summary="获取指标分类")
async def get_indicator_categories():
    """获取技术指标分类信息"""
    try:
        categories = {
            "trend": {
                "name": "趋势指标",
                "description": "用于识别价格趋势方向和强度的指标",
                "indicators": ["ma", "ema", "macd", "bollinger", "sar", "adx"]
            },
            "momentum": {
                "name": "动量指标",
                "description": "用于衡量价格变化速度和力度的指标",
                "indicators": ["rsi", "kdj", "cci", "williams_r", "stochastic", "roc", "momentum", "ultimate_oscillator"]
            },
            "volume": {
                "name": "成交量指标",
                "description": "基于成交量分析的技术指标",
                "indicators": ["obv", "vwap", "volume_ratio", "ad", "chaikin_oscillator", "mfi"]
            },
            "volatility": {
                "name": "波动率指标",
                "description": "用于衡量价格波动程度的指标",
                "indicators": ["atr", "volatility_channel", "historical_volatility", "keltner_channel", "donchian_channel"]
            },
            "money_flow": {
                "name": "资金流向指标",
                "description": "用于分析资金流入流出情况的指标",
                "indicators": ["main_capital_flow", "northbound_capital", "institutional_flow", "smart_money", "mfi_advanced", "capital_flow_analysis"]
            }
        }
        
        return IndicatorResponse(
            success=True,
            message="获取指标分类成功",
            data=categories
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标分类失败: {str(e)}")








