"""
动量指标实现
包括RSI、KDJ、CCI、Williams %R等动量指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from ..technical_indicators import BaseIndicator, IndicatorConfig, IndicatorType, performance_monitor
from ..technical_indicators import ensure_numeric, rolling_window, typical_price


class RSIIndicator(BaseIndicator):
    """相对强弱指数RSI"""
    
    def __init__(self, period: int = 14):
        config = IndicatorConfig(
            name="RSI",
            type=IndicatorType.MOMENTUM,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False}
            },
            description="相对强弱指数，衡量价格变动的速度和幅度"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.Series:
        """计算RSI"""
        self.validate_data(data, [column])
        
        period = kwargs.get('period', self.period)
        price_series = ensure_numeric(data[column])
        
        # 计算价格变化
        delta = price_series.diff()
        
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均收益和平均损失
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class KDJIndicator(BaseIndicator):
    """KDJ随机指标"""
    
    def __init__(self, k_period: int = 9, d_period: int = 3, j_period: int = 3):
        config = IndicatorConfig(
            name="KDJ",
            type=IndicatorType.MOMENTUM,
            parameters={
                'k_period': {'type': int, 'min': 1, 'max': 100, 'default': 9, 'required': False},
                'd_period': {'type': int, 'min': 1, 'max': 50, 'default': 3, 'required': False},
                'j_period': {'type': int, 'min': 1, 'max': 50, 'default': 3, 'required': False}
            },
            description="KDJ随机指标，包括K线、D线、J线"
        )
        super().__init__(config)
        self.k_period = k_period
        self.d_period = d_period
        self.j_period = j_period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算KDJ"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        k_period = kwargs.get('k_period', self.k_period)
        d_period = kwargs.get('d_period', self.d_period)
        j_period = kwargs.get('j_period', self.j_period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        # 计算最高价和最低价的滚动窗口
        lowest_low = low.rolling(window=k_period, min_periods=1).min()
        highest_high = high.rolling(window=k_period, min_periods=1).max()
        
        # 计算RSV (Raw Stochastic Value)
        rsv = 100 * (close - lowest_low) / (highest_high - lowest_low)
        rsv = rsv.fillna(50)  # 填充NaN值
        
        # 计算K值 (使用指数移动平均)
        k_values = rsv.ewm(span=d_period, adjust=False).mean()
        
        # 计算D值 (K值的指数移动平均)
        d_values = k_values.ewm(span=j_period, adjust=False).mean()
        
        # 计算J值
        j_values = 3 * k_values - 2 * d_values
        
        return pd.DataFrame({
            'k': k_values,
            'd': d_values,
            'j': j_values
        }, index=data.index)


class CCIIndicator(BaseIndicator):
    """商品通道指数CCI"""
    
    def __init__(self, period: int = 20, constant: float = 0.015):
        config = IndicatorConfig(
            name="CCI",
            type=IndicatorType.MOMENTUM,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 20, 'required': False},
                'constant': {'type': float, 'min': 0.001, 'max': 0.1, 'default': 0.015, 'required': False}
            },
            description="商品通道指数，衡量价格偏离统计平均值的程度"
        )
        super().__init__(config)
        self.period = period
        self.constant = constant
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算CCI"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        period = kwargs.get('period', self.period)
        constant = kwargs.get('constant', self.constant)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        # 计算典型价格
        tp = typical_price(high, low, close)
        
        # 计算典型价格的移动平均
        sma_tp = tp.rolling(window=period, min_periods=1).mean()
        
        # 计算平均绝对偏差
        mad = tp.rolling(window=period, min_periods=1).apply(
            lambda x: np.mean(np.abs(x - np.mean(x))), raw=True
        )
        
        # 计算CCI
        cci = (tp - sma_tp) / (constant * mad)
        
        return cci


class WilliamsRIndicator(BaseIndicator):
    """威廉指标Williams %R"""
    
    def __init__(self, period: int = 14):
        config = IndicatorConfig(
            name="WILLIAMS_R",
            type=IndicatorType.MOMENTUM,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False}
            },
            description="威廉指标，衡量超买超卖状态"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算Williams %R"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        period = kwargs.get('period', self.period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        # 计算最高价和最低价的滚动窗口
        highest_high = high.rolling(window=period, min_periods=1).max()
        lowest_low = low.rolling(window=period, min_periods=1).min()
        
        # 计算Williams %R
        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        
        return williams_r


class StochasticIndicator(BaseIndicator):
    """随机指标Stochastic"""
    
    def __init__(self, k_period: int = 14, d_period: int = 3, smooth_k: int = 3):
        config = IndicatorConfig(
            name="STOCHASTIC",
            type=IndicatorType.MOMENTUM,
            parameters={
                'k_period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False},
                'd_period': {'type': int, 'min': 1, 'max': 50, 'default': 3, 'required': False},
                'smooth_k': {'type': int, 'min': 1, 'max': 50, 'default': 3, 'required': False}
            },
            description="随机指标，包括%K和%D线"
        )
        super().__init__(config)
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算Stochastic"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        k_period = kwargs.get('k_period', self.k_period)
        d_period = kwargs.get('d_period', self.d_period)
        smooth_k = kwargs.get('smooth_k', self.smooth_k)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        # 计算最高价和最低价的滚动窗口
        lowest_low = low.rolling(window=k_period, min_periods=1).min()
        highest_high = high.rolling(window=k_period, min_periods=1).max()
        
        # 计算%K
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        
        # 平滑%K
        if smooth_k > 1:
            k_percent = k_percent.rolling(window=smooth_k, min_periods=1).mean()
        
        # 计算%D
        d_percent = k_percent.rolling(window=d_period, min_periods=1).mean()
        
        return pd.DataFrame({
            'k_percent': k_percent,
            'd_percent': d_percent
        }, index=data.index)


class ROCIndicator(BaseIndicator):
    """变动率指标ROC"""
    
    def __init__(self, period: int = 12):
        config = IndicatorConfig(
            name="ROC",
            type=IndicatorType.MOMENTUM,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 12, 'required': False}
            },
            description="变动率指标，衡量价格变动的百分比"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.Series:
        """计算ROC"""
        self.validate_data(data, [column])
        
        period = kwargs.get('period', self.period)
        price_series = ensure_numeric(data[column])
        
        # 计算ROC
        roc = ((price_series - price_series.shift(period)) / price_series.shift(period)) * 100
        
        return roc


class MomentumIndicator(BaseIndicator):
    """动量指标Momentum"""
    
    def __init__(self, period: int = 10):
        config = IndicatorConfig(
            name="MOMENTUM",
            type=IndicatorType.MOMENTUM,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 10, 'required': False}
            },
            description="动量指标，衡量价格变动的速度"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.Series:
        """计算Momentum"""
        self.validate_data(data, [column])
        
        period = kwargs.get('period', self.period)
        price_series = ensure_numeric(data[column])
        
        # 计算动量
        momentum = price_series - price_series.shift(period)
        
        return momentum


class UltimateOscillatorIndicator(BaseIndicator):
    """终极振荡器Ultimate Oscillator"""
    
    def __init__(self, period1: int = 7, period2: int = 14, period3: int = 28):
        config = IndicatorConfig(
            name="ULTIMATE_OSCILLATOR",
            type=IndicatorType.MOMENTUM,
            parameters={
                'period1': {'type': int, 'min': 1, 'max': 50, 'default': 7, 'required': False},
                'period2': {'type': int, 'min': 1, 'max': 50, 'default': 14, 'required': False},
                'period3': {'type': int, 'min': 1, 'max': 100, 'default': 28, 'required': False}
            },
            description="终极振荡器，结合三个不同周期的买卖压力"
        )
        super().__init__(config)
        self.period1 = period1
        self.period2 = period2
        self.period3 = period3
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算Ultimate Oscillator"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        period1 = kwargs.get('period1', self.period1)
        period2 = kwargs.get('period2', self.period2)
        period3 = kwargs.get('period3', self.period3)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        # 计算买卖压力
        prev_close = close.shift(1)
        bp = close - pd.concat([low, prev_close], axis=1).min(axis=1)  # 买压
        tr = pd.concat([
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        ], axis=1).max(axis=1)  # 真实波幅
        
        # 计算三个周期的平均值
        avg1 = bp.rolling(window=period1).sum() / tr.rolling(window=period1).sum()
        avg2 = bp.rolling(window=period2).sum() / tr.rolling(window=period2).sum()
        avg3 = bp.rolling(window=period3).sum() / tr.rolling(window=period3).sum()
        
        # 计算终极振荡器
        uo = 100 * (4 * avg1 + 2 * avg2 + avg3) / 7
        
        return uo