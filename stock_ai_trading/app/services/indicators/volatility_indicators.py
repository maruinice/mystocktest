"""
波动率指标实现
包括ATR、波动率通道、历史波动率等指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from ..technical_indicators import BaseIndicator, IndicatorConfig, IndicatorType, performance_monitor
from ..technical_indicators import ensure_numeric, true_range


class ATRIndicator(BaseIndicator):
    """平均真实波幅ATR (Average True Range)"""
    
    def __init__(self, period: int = 14):
        config = IndicatorConfig(
            name="ATR",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False}
            },
            description="平均真实波幅，衡量价格波动性"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算ATR"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        period = kwargs.get('period', self.period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        # 计算真实波幅
        tr = true_range(high, low, close)
        
        # 计算ATR (使用指数移动平均)
        atr = tr.ewm(span=period, adjust=False).mean()
        
        return atr


class VolatilityChannelIndicator(BaseIndicator):
    """波动率通道指标"""
    
    def __init__(self, period: int = 20, multiplier: float = 2.0):
        config = IndicatorConfig(
            name="VOLATILITY_CHANNEL",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 20, 'required': False},
                'multiplier': {'type': float, 'min': 0.1, 'max': 5.0, 'default': 2.0, 'required': False}
            },
            description="波动率通道，基于ATR构建的价格通道"
        )
        super().__init__(config)
        self.period = period
        self.multiplier = multiplier
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算波动率通道"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        period = kwargs.get('period', self.period)
        multiplier = kwargs.get('multiplier', self.multiplier)
        
        close = ensure_numeric(data['close'])
        
        # 计算ATR
        atr_indicator = ATRIndicator(period)
        atr = atr_indicator.calculate(data)
        
        # 计算中轨（移动平均）
        middle_line = close.rolling(window=period, min_periods=1).mean()
        
        # 计算上轨和下轨
        upper_channel = middle_line + (atr * multiplier)
        lower_channel = middle_line - (atr * multiplier)
        
        return pd.DataFrame({
            'upper_channel': upper_channel,
            'middle_line': middle_line,
            'lower_channel': lower_channel,
            'channel_width': upper_channel - lower_channel
        }, index=data.index)


class HistoricalVolatilityIndicator(BaseIndicator):
    """历史波动率指标"""
    
    def __init__(self, period: int = 20, annualize: bool = True):
        config = IndicatorConfig(
            name="HISTORICAL_VOLATILITY",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 252, 'default': 20, 'required': False},
                'annualize': {'type': bool, 'default': True, 'required': False}
            },
            description="历史波动率，基于价格收益率的标准差"
        )
        super().__init__(config)
        self.period = period
        self.annualize = annualize
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.Series:
        """计算历史波动率"""
        self.validate_data(data, [column])
        
        period = kwargs.get('period', self.period)
        annualize = kwargs.get('annualize', self.annualize)
        
        price_series = ensure_numeric(data[column])
        
        # 计算对数收益率
        log_returns = np.log(price_series / price_series.shift(1))
        
        # 计算滚动标准差
        volatility = log_returns.rolling(window=period, min_periods=1).std()
        
        # 年化波动率
        if annualize:
            volatility = volatility * np.sqrt(252)  # 假设一年252个交易日
        
        return volatility


class KeltnerChannelIndicator(BaseIndicator):
    """肯特纳通道Keltner Channel"""
    
    def __init__(self, period: int = 20, multiplier: float = 2.0):
        config = IndicatorConfig(
            name="KELTNER_CHANNEL",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 20, 'required': False},
                'multiplier': {'type': float, 'min': 0.1, 'max': 5.0, 'default': 2.0, 'required': False}
            },
            description="肯特纳通道，基于EMA和ATR的价格通道"
        )
        super().__init__(config)
        self.period = period
        self.multiplier = multiplier
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算Keltner Channel"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        period = kwargs.get('period', self.period)
        multiplier = kwargs.get('multiplier', self.multiplier)
        
        close = ensure_numeric(data['close'])
        
        # 计算中轨（EMA）
        middle_line = close.ewm(span=period, adjust=False).mean()
        
        # 计算ATR
        atr_indicator = ATRIndicator(period)
        atr = atr_indicator.calculate(data)
        
        # 计算上轨和下轨
        upper_channel = middle_line + (atr * multiplier)
        lower_channel = middle_line - (atr * multiplier)
        
        return pd.DataFrame({
            'upper_channel': upper_channel,
            'middle_line': middle_line,
            'lower_channel': lower_channel,
            'channel_width': upper_channel - lower_channel
        }, index=data.index)


class DonchianChannelIndicator(BaseIndicator):
    """唐奇安通道Donchian Channel"""
    
    def __init__(self, period: int = 20):
        config = IndicatorConfig(
            name="DONCHIAN_CHANNEL",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 20, 'required': False}
            },
            description="唐奇安通道，基于最高价和最低价的价格通道"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算Donchian Channel"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        period = kwargs.get('period', self.period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        # 计算上轨（最高价）
        upper_channel = high.rolling(window=period, min_periods=1).max()
        
        # 计算下轨（最低价）
        lower_channel = low.rolling(window=period, min_periods=1).min()
        
        # 计算中轨（上轨和下轨的平均）
        middle_line = (upper_channel + lower_channel) / 2
        
        return pd.DataFrame({
            'upper_channel': upper_channel,
            'middle_line': middle_line,
            'lower_channel': lower_channel,
            'channel_width': upper_channel - lower_channel
        }, index=data.index)


class StandardDeviationIndicator(BaseIndicator):
    """标准差指标"""
    
    def __init__(self, period: int = 20):
        config = IndicatorConfig(
            name="STANDARD_DEVIATION",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 20, 'required': False}
            },
            description="标准差指标，衡量价格偏离平均值的程度"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.Series:
        """计算标准差"""
        self.validate_data(data, [column])
        
        period = kwargs.get('period', self.period)
        price_series = ensure_numeric(data[column])
        
        # 计算滚动标准差
        std_dev = price_series.rolling(window=period, min_periods=1).std()
        
        return std_dev


class VarianceIndicator(BaseIndicator):
    """方差指标"""
    
    def __init__(self, period: int = 20):
        config = IndicatorConfig(
            name="VARIANCE",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 20, 'required': False}
            },
            description="方差指标，衡量价格变动的离散程度"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.Series:
        """计算方差"""
        self.validate_data(data, [column])
        
        period = kwargs.get('period', self.period)
        price_series = ensure_numeric(data[column])
        
        # 计算滚动方差
        variance = price_series.rolling(window=period, min_periods=1).var()
        
        return variance


class RangeIndicator(BaseIndicator):
    """价格区间指标"""
    
    def __init__(self, period: int = 14):
        config = IndicatorConfig(
            name="RANGE",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False}
            },
            description="价格区间指标，衡量高低价差"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算价格区间"""
        self.validate_data(data, ['high', 'low'])
        
        period = kwargs.get('period', self.period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        
        # 计算日内区间
        daily_range = high - low
        
        # 计算平均区间
        avg_range = daily_range.rolling(window=period, min_periods=1).mean()
        
        # 计算区间百分比
        range_pct = (daily_range / low) * 100
        avg_range_pct = range_pct.rolling(window=period, min_periods=1).mean()
        
        return pd.DataFrame({
            'daily_range': daily_range,
            'avg_range': avg_range,
            'range_pct': range_pct,
            'avg_range_pct': avg_range_pct
        }, index=data.index)


class GarmanKlassVolatilityIndicator(BaseIndicator):
    """Garman-Klass波动率估计器"""
    
    def __init__(self, period: int = 20, annualize: bool = True):
        config = IndicatorConfig(
            name="GARMAN_KLASS_VOLATILITY",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 252, 'default': 20, 'required': False},
                'annualize': {'type': bool, 'default': True, 'required': False}
            },
            description="Garman-Klass波动率估计器，使用OHLC数据的高效波动率估计"
        )
        super().__init__(config)
        self.period = period
        self.annualize = annualize
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算Garman-Klass波动率"""
        self.validate_data(data, ['open', 'high', 'low', 'close'])
        
        period = kwargs.get('period', self.period)
        annualize = kwargs.get('annualize', self.annualize)
        
        open_price = ensure_numeric(data['open'])
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        # Garman-Klass估计器公式
        ln_hl = np.log(high / low)
        ln_co = np.log(close / open_price)
        
        gk_vol = ln_hl ** 2 - (2 * np.log(2) - 1) * ln_co ** 2
        
        # 计算滚动平均
        volatility = gk_vol.rolling(window=period, min_periods=1).mean()
        volatility = np.sqrt(volatility)
        
        # 年化波动率
        if annualize:
            volatility = volatility * np.sqrt(252)
        
        return volatility


class ParkinsonVolatilityIndicator(BaseIndicator):
    """Parkinson波动率估计器"""
    
    def __init__(self, period: int = 20, annualize: bool = True):
        config = IndicatorConfig(
            name="PARKINSON_VOLATILITY",
            type=IndicatorType.VOLATILITY,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 252, 'default': 20, 'required': False},
                'annualize': {'type': bool, 'default': True, 'required': False}
            },
            description="Parkinson波动率估计器，基于高低价的波动率估计"
        )
        super().__init__(config)
        self.period = period
        self.annualize = annualize
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算Parkinson波动率"""
        self.validate_data(data, ['high', 'low'])
        
        period = kwargs.get('period', self.period)
        annualize = kwargs.get('annualize', self.annualize)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        
        # Parkinson估计器公式
        ln_hl = np.log(high / low)
        parkinson_vol = ln_hl ** 2 / (4 * np.log(2))
        
        # 计算滚动平均
        volatility = parkinson_vol.rolling(window=period, min_periods=1).mean()
        volatility = np.sqrt(volatility)
        
        # 年化波动率
        if annualize:
            volatility = volatility * np.sqrt(252)
        
        return volatility