"""
成交量指标实现
包括OBV、VWAP、量比等成交量相关指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from ..technical_indicators import BaseIndicator, IndicatorConfig, IndicatorType, performance_monitor
from ..technical_indicators import ensure_numeric, typical_price


class OBVIndicator(BaseIndicator):
    """能量潮指标OBV (On Balance Volume)"""
    
    def __init__(self):
        config = IndicatorConfig(
            name="OBV",
            type=IndicatorType.VOLUME,
            parameters={},
            description="能量潮指标，通过累计成交量变化来预测价格趋势"
        )
        super().__init__(config)
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算OBV"""
        self.validate_data(data, ['close', 'volume'])
        
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        
        # 计算价格变化方向
        price_change = close.diff()
        
        # 根据价格变化方向调整成交量符号
        obv_volume = np.where(price_change > 0, volume,
                             np.where(price_change < 0, -volume, 0))
        
        # 累计成交量
        obv = pd.Series(obv_volume, index=data.index).cumsum()
        
        return obv


class VWAPIndicator(BaseIndicator):
    """成交量加权平均价格VWAP (Volume Weighted Average Price)"""
    
    def __init__(self, period: Optional[int] = None):
        config = IndicatorConfig(
            name="VWAP",
            type=IndicatorType.VOLUME,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 500, 'default': None, 'required': False}
            },
            description="成交量加权平均价格，如果不指定周期则计算累计VWAP"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算VWAP"""
        self.validate_data(data, ['high', 'low', 'close', 'volume'])
        
        period = kwargs.get('period', self.period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        
        # 计算典型价格
        tp = typical_price(high, low, close)
        
        # 计算价格*成交量
        pv = tp * volume
        
        if period is None:
            # 累计VWAP
            vwap = pv.cumsum() / volume.cumsum()
        else:
            # 滚动VWAP
            vwap = pv.rolling(window=period, min_periods=1).sum() / \
                   volume.rolling(window=period, min_periods=1).sum()
        
        return vwap


class VolumeRatioIndicator(BaseIndicator):
    """量比指标"""
    
    def __init__(self, period: int = 5):
        config = IndicatorConfig(
            name="VOLUME_RATIO",
            type=IndicatorType.VOLUME,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 5, 'required': False}
            },
            description="量比指标，当前成交量与历史平均成交量的比值"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算量比"""
        self.validate_data(data, ['volume'])
        
        period = kwargs.get('period', self.period)
        volume = ensure_numeric(data['volume'])
        
        # 计算平均成交量
        avg_volume = volume.rolling(window=period, min_periods=1).mean()
        
        # 计算量比
        volume_ratio = volume / avg_volume
        
        return volume_ratio


class AccumulationDistributionIndicator(BaseIndicator):
    """累积/派发线A/D Line"""
    
    def __init__(self):
        config = IndicatorConfig(
            name="AD_LINE",
            type=IndicatorType.VOLUME,
            parameters={},
            description="累积/派发线，衡量资金流入流出情况"
        )
        super().__init__(config)
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算A/D Line"""
        self.validate_data(data, ['high', 'low', 'close', 'volume'])
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        
        # 计算收盘价位置值CLV
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fillna(0)  # 处理高低价相等的情况
        
        # 计算资金流量乘数
        mfm = clv * volume
        
        # 累积资金流量
        ad_line = mfm.cumsum()
        
        return ad_line


class ChaikinOscillatorIndicator(BaseIndicator):
    """蔡金振荡器Chaikin Oscillator"""
    
    def __init__(self, fast_period: int = 3, slow_period: int = 10):
        config = IndicatorConfig(
            name="CHAIKIN_OSCILLATOR",
            type=IndicatorType.VOLUME,
            parameters={
                'fast_period': {'type': int, 'min': 1, 'max': 50, 'default': 3, 'required': False},
                'slow_period': {'type': int, 'min': 1, 'max': 100, 'default': 10, 'required': False}
            },
            description="蔡金振荡器，基于累积/派发线的动量指标"
        )
        super().__init__(config)
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算Chaikin Oscillator"""
        self.validate_data(data, ['high', 'low', 'close', 'volume'])
        
        fast_period = kwargs.get('fast_period', self.fast_period)
        slow_period = kwargs.get('slow_period', self.slow_period)
        
        # 先计算A/D Line
        ad_indicator = AccumulationDistributionIndicator()
        ad_line = ad_indicator.calculate(data)
        
        # 计算快速和慢速EMA
        fast_ema = ad_line.ewm(span=fast_period, adjust=False).mean()
        slow_ema = ad_line.ewm(span=slow_period, adjust=False).mean()
        
        # 蔡金振荡器 = 快速EMA - 慢速EMA
        chaikin_osc = fast_ema - slow_ema
        
        return chaikin_osc


class MoneyFlowIndexIndicator(BaseIndicator):
    """资金流量指数MFI (Money Flow Index)"""
    
    def __init__(self, period: int = 14):
        config = IndicatorConfig(
            name="MFI",
            type=IndicatorType.VOLUME,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False}
            },
            description="资金流量指数，结合价格和成交量的动量指标"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算MFI"""
        self.validate_data(data, ['high', 'low', 'close', 'volume'])
        
        period = kwargs.get('period', self.period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        
        # 计算典型价格
        tp = typical_price(high, low, close)
        
        # 计算资金流量
        money_flow = tp * volume
        
        # 计算典型价格变化
        tp_change = tp.diff()
        
        # 分离正向和负向资金流量
        positive_mf = money_flow.where(tp_change > 0, 0)
        negative_mf = money_flow.where(tp_change < 0, 0)
        
        # 计算资金流量比率
        positive_mf_sum = positive_mf.rolling(window=period, min_periods=1).sum()
        negative_mf_sum = negative_mf.rolling(window=period, min_periods=1).sum()
        
        money_flow_ratio = positive_mf_sum / negative_mf_sum
        
        # 计算MFI
        mfi = 100 - (100 / (1 + money_flow_ratio))
        
        return mfi


class VolumeOscillatorIndicator(BaseIndicator):
    """成交量振荡器Volume Oscillator"""
    
    def __init__(self, short_period: int = 5, long_period: int = 10):
        config = IndicatorConfig(
            name="VOLUME_OSCILLATOR",
            type=IndicatorType.VOLUME,
            parameters={
                'short_period': {'type': int, 'min': 1, 'max': 50, 'default': 5, 'required': False},
                'long_period': {'type': int, 'min': 1, 'max': 100, 'default': 10, 'required': False}
            },
            description="成交量振荡器，比较短期和长期成交量移动平均"
        )
        super().__init__(config)
        self.short_period = short_period
        self.long_period = long_period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算Volume Oscillator"""
        self.validate_data(data, ['volume'])
        
        short_period = kwargs.get('short_period', self.short_period)
        long_period = kwargs.get('long_period', self.long_period)
        
        volume = ensure_numeric(data['volume'])
        
        # 计算短期和长期移动平均
        short_ma = volume.rolling(window=short_period, min_periods=1).mean()
        long_ma = volume.rolling(window=long_period, min_periods=1).mean()
        
        # 计算成交量振荡器
        volume_osc = ((short_ma - long_ma) / long_ma) * 100
        
        return volume_osc


class PriceVolumeIndicator(BaseIndicator):
    """价量指标PVI (Price Volume Indicator)"""
    
    def __init__(self):
        config = IndicatorConfig(
            name="PVI",
            type=IndicatorType.VOLUME,
            parameters={},
            description="价量指标，在成交量增加时跟踪价格变化"
        )
        super().__init__(config)
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算PVI"""
        self.validate_data(data, ['close', 'volume'])
        
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        
        # 计算价格变化率
        price_change = close.pct_change()
        
        # 计算成交量变化
        volume_change = volume.diff()
        
        # 初始化PVI
        pvi = pd.Series(index=data.index, dtype=float)
        pvi.iloc[0] = 1000  # 起始值
        
        for i in range(1, len(data)):
            if volume_change.iloc[i] > 0:
                # 成交量增加时更新PVI
                pvi.iloc[i] = pvi.iloc[i-1] * (1 + price_change.iloc[i])
            else:
                # 成交量未增加时保持不变
                pvi.iloc[i] = pvi.iloc[i-1]
        
        return pvi


class NegativeVolumeIndexIndicator(BaseIndicator):
    """负成交量指数NVI (Negative Volume Index)"""
    
    def __init__(self):
        config = IndicatorConfig(
            name="NVI",
            type=IndicatorType.VOLUME,
            parameters={},
            description="负成交量指数，在成交量减少时跟踪价格变化"
        )
        super().__init__(config)
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算NVI"""
        self.validate_data(data, ['close', 'volume'])
        
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        
        # 计算价格变化率
        price_change = close.pct_change()
        
        # 计算成交量变化
        volume_change = volume.diff()
        
        # 初始化NVI
        nvi = pd.Series(index=data.index, dtype=float)
        nvi.iloc[0] = 1000  # 起始值
        
        for i in range(1, len(data)):
            if volume_change.iloc[i] < 0:
                # 成交量减少时更新NVI
                nvi.iloc[i] = nvi.iloc[i-1] * (1 + price_change.iloc[i])
            else:
                # 成交量未减少时保持不变
                nvi.iloc[i] = nvi.iloc[i-1]
        
        return nvi


class VolumeWeightedMomentumIndicator(BaseIndicator):
    """成交量加权动量指标"""
    
    def __init__(self, period: int = 14):
        config = IndicatorConfig(
            name="VOLUME_WEIGHTED_MOMENTUM",
            type=IndicatorType.VOLUME,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False}
            },
            description="成交量加权动量指标，结合价格动量和成交量"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算成交量加权动量"""
        self.validate_data(data, ['close', 'volume'])
        
        period = kwargs.get('period', self.period)
        
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        
        # 计算价格动量
        momentum = close - close.shift(period)
        
        # 计算成交量权重
        volume_weight = volume / volume.rolling(window=period, min_periods=1).mean()
        
        # 成交量加权动量
        vwm = momentum * volume_weight
        
        return vwm