"""
技术指标计算服务
提供各种技术指标的计算功能，包括趋势、动量、成交量、波动率和资金流向指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from abc import ABC, abstractmethod
import time
import logging
from .performance_monitor import monitor_performance
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IndicatorType(Enum):
    """指标类型枚举"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    MONEY_FLOW = "money_flow"


@dataclass
class IndicatorConfig:
    """指标配置类"""
    name: str
    type: IndicatorType
    parameters: Dict[str, Any]
    description: str = ""


@dataclass
class PerformanceMetrics:
    """性能监控指标"""
    indicator_name: str
    calculation_time: float
    data_points: int
    memory_usage: float
    timestamp: float


performance_monitor = monitor_performance


class BaseIndicator(ABC):
    """技术指标基础类"""
    
    def __init__(self, config: IndicatorConfig):
        self.config = config
        self.performance_history: List[PerformanceMetrics] = []
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame, **kwargs) -> Union[pd.Series, pd.DataFrame]:
        """计算指标值"""
        pass
    
    def validate_data(self, data: pd.DataFrame, required_columns: List[str]) -> bool:
        """验证输入数据"""
        if data.empty:
            raise ValueError("输入数据为空")
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        return True
    
    def _record_performance(self, metrics: PerformanceMetrics):
        """记录性能指标"""
        self.performance_history.append(metrics)
        
        # 保持最近100条记录
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    def _get_memory_usage(self) -> float:
        """获取内存使用量（MB）"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def get_performance_stats(self) -> Dict[str, float]:
        """获取性能统计信息"""
        if not self.performance_history:
            return {}
        
        times = [m.calculation_time for m in self.performance_history]
        return {
            "avg_calculation_time": np.mean(times),
            "max_calculation_time": np.max(times),
            "min_calculation_time": np.min(times),
            "total_calculations": len(self.performance_history)
        }


class TechnicalIndicatorService:
    """技术指标计算服务"""
    
    def __init__(self):
        self.indicators: Dict[str, BaseIndicator] = {}
        self.performance_history: List[PerformanceMetrics] = []
        self._register_indicators()
    
    def _register_indicators(self):
        """注册所有指标"""
        # 这里将在后续实现中注册具体的指标类
        pass
    
    def register_indicator(self, name: str, indicator: BaseIndicator):
        """注册指标"""
        self.indicators[name] = indicator
        logger.info(f"注册指标: {name}")
    
    def calculate_indicator(self, name: str, data: pd.DataFrame, **kwargs) -> Union[pd.Series, pd.DataFrame]:
        """计算指定指标"""
        if name not in self.indicators:
            raise ValueError(f"未知指标: {name}")
        
        return self.indicators[name].calculate(data, **kwargs)
    
    def calculate_multiple_indicators(self, 
                                    indicator_names: List[str], 
                                    data: pd.DataFrame, 
                                    **kwargs) -> Dict[str, Union[pd.Series, pd.DataFrame]]:
        """批量计算多个指标"""
        results = {}
        
        for name in indicator_names:
            try:
                results[name] = self.calculate_indicator(name, data, **kwargs)
            except Exception as e:
                logger.error(f"计算指标 {name} 失败: {str(e)}")
                results[name] = None
        
        return results
    
    def get_available_indicators(self) -> Dict[str, Dict[str, Any]]:
        """获取可用指标列表"""
        return {
            name: {
                "type": indicator.config.type.value,
                "parameters": indicator.config.parameters,
                "description": indicator.config.description
            }
            for name, indicator in self.indicators.items()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {}
        
        for name, indicator in self.indicators.items():
            stats = indicator.get_performance_stats()
            if stats:
                summary[name] = stats
        
        return summary
    
    def validate_parameters(self, indicator_name: str, parameters: Dict[str, Any]) -> bool:
        """验证指标参数"""
        if indicator_name not in self.indicators:
            return False
        
        indicator = self.indicators[indicator_name]
        required_params = indicator.config.parameters
        
        for param, config in required_params.items():
            if param not in parameters:
                if config.get('required', False):
                    return False
            else:
                value = parameters[param]
                param_type = config.get('type')
                if param_type and not isinstance(value, param_type):
                    return False
                
                min_val = config.get('min')
                max_val = config.get('max')
                if min_val is not None and value < min_val:
                    return False
                if max_val is not None and value > max_val:
                    return False
        
        return True


# 全局技术指标服务实例
technical_indicator_service = TechnicalIndicatorService()


# 工具函数
def ensure_numeric(series: pd.Series) -> pd.Series:
    """确保序列为数值类型"""
    return pd.to_numeric(series, errors='coerce')


def rolling_window(data: pd.Series, window: int, min_periods: int = None) -> pd.Series:
    """滚动窗口计算"""
    if min_periods is None:
        min_periods = window
    return data.rolling(window=window, min_periods=min_periods)


def exponential_smoothing(data: pd.Series, alpha: float) -> pd.Series:
    """指数平滑"""
    return data.ewm(alpha=alpha, adjust=False)


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """真实波幅计算"""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def typical_price(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """典型价格 (HLC/3)"""
    return (high + low + close) / 3


def weighted_close(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """加权收盘价 (HLCC/4)"""
    return (high + low + close + close) / 4


def calculate_kdj(data: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """计算KDJ指标"""
    if not all(col in data.columns for col in ['high', 'low', 'close']):
        raise ValueError("数据必须包含high, low, close列")
    
    # 计算RSV
    low_n = data['low'].rolling(window=n).min()
    high_n = data['high'].rolling(window=n).max()
    rsv = (data['close'] - low_n) / (high_n - low_n) * 100
    
    # 计算K值
    k = rsv.ewm(alpha=1/m1, adjust=False).mean()
    # 计算D值
    d = k.ewm(alpha=1/m2, adjust=False).mean()
    # 计算J值
    j = 3 * k - 2 * d
    
    return pd.DataFrame({'K': k, 'D': d, 'J': j, 'RSV': rsv}, index=data.index)


def calculate_rsrs(data: pd.DataFrame, n: int = 18, m: int = 600) -> pd.DataFrame:
    """计算RSRS指标（阻力支撑相对强度）"""
    if not all(col in data.columns for col in ['high', 'low']):
        raise ValueError("数据必须包含high, low列")
    
    slopes = []
    r2_values = []
    
    # 滚动计算斜率和R²
    for i in range(n-1, len(data)):
        window = data.iloc[i-n+1:i+1]
        x = window['low'].values
        y = window['high'].values
        
        if len(x) >= 2:
            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            slopes.append(slope)
            r2_values.append(r2)
        else:
            slopes.append(np.nan)
            r2_values.append(np.nan)
    
    result = pd.DataFrame({
        'slope': slopes,
        'r2': r2_values
    }, index=data.index[n-1:])
    
    # 计算Z-Score
    result['zscore'] = result['slope'].rolling(window=min(m, len(result))).apply(
        lambda x: (x.iloc[-1] - x.mean()) / x.std() if len(x) > 1 and x.std() > 0 else 0
    )
    
    # RSRS分数 = Z-Score * R²
    result['rsrs_score'] = result['zscore'] * result['r2']
    
    return result