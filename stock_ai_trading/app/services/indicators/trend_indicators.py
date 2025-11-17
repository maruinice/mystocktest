"""
趋势指标实现
包括移动平均线(MA)、指数移动平均线(EMA)、MACD、布林带(Bollinger Bands)等
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from ..technical_indicators import BaseIndicator, IndicatorConfig, IndicatorType, performance_monitor
from ..technical_indicators import ensure_numeric, rolling_window, exponential_smoothing


class MovingAverageIndicator(BaseIndicator):
    """移动平均线指标"""
    
    def __init__(self, period: int = 20, ma_type: str = 'sma'):
        config = IndicatorConfig(
            name="MA",
            type=IndicatorType.TREND,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 500, 'default': 20, 'required': True},
                'ma_type': {'type': str, 'options': ['sma', 'ema', 'wma'], 'default': 'sma', 'required': False}
            },
            description="移动平均线，支持简单移动平均(SMA)、指数移动平均(EMA)、加权移动平均(WMA)"
        )
        super().__init__(config)
        self.period = period
        self.ma_type = ma_type
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.Series:
        """计算移动平均线"""
        self.validate_data(data, [column])
        
        period = kwargs.get('period', self.period)
        ma_type = kwargs.get('ma_type', self.ma_type)
        
        price_series = ensure_numeric(data[column])
        
        if ma_type == 'sma':
            return price_series.rolling(window=period, min_periods=1).mean()
        elif ma_type == 'ema':
            return price_series.ewm(span=period, adjust=False).mean()
        elif ma_type == 'wma':
            return self._weighted_moving_average(price_series, period)
        else:
            raise ValueError(f"不支持的移动平均类型: {ma_type}")
    
    def _weighted_moving_average(self, series: pd.Series, period: int) -> pd.Series:
        """加权移动平均"""
        weights = np.arange(1, period + 1)
        weights = weights / weights.sum()
        
        def wma_calc(x):
            if len(x) < period:
                return np.nan
            return np.dot(x[-period:], weights)
        
        return series.rolling(window=period, min_periods=period).apply(wma_calc, raw=True)


class EMAIndicator(BaseIndicator):
    """指数移动平均线指标"""
    
    def __init__(self, period: int = 12):
        config = IndicatorConfig(
            name="EMA",
            type=IndicatorType.TREND,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 500, 'default': 12, 'required': True}
            },
            description="指数移动平均线，对近期价格给予更高权重"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.Series:
        """计算EMA"""
        self.validate_data(data, [column])
        
        period = kwargs.get('period', self.period)
        price_series = ensure_numeric(data[column])
        
        return price_series.ewm(span=period, adjust=False).mean()


class MACDIndicator(BaseIndicator):
    """MACD指标"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        config = IndicatorConfig(
            name="MACD",
            type=IndicatorType.TREND,
            parameters={
                'fast_period': {'type': int, 'min': 1, 'max': 100, 'default': 12, 'required': False},
                'slow_period': {'type': int, 'min': 1, 'max': 100, 'default': 26, 'required': False},
                'signal_period': {'type': int, 'min': 1, 'max': 50, 'default': 9, 'required': False}
            },
            description="MACD指标，包括MACD线、信号线和柱状图"
        )
        super().__init__(config)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.DataFrame:
        """计算MACD"""
        self.validate_data(data, [column])
        
        fast_period = kwargs.get('fast_period', self.fast_period)
        slow_period = kwargs.get('slow_period', self.slow_period)
        signal_period = kwargs.get('signal_period', self.signal_period)
        
        price_series = ensure_numeric(data[column])
        
        # 计算快速和慢速EMA
        ema_fast = price_series.ewm(span=fast_period, adjust=False).mean()
        ema_slow = price_series.ewm(span=slow_period, adjust=False).mean()
        
        # MACD线 = 快速EMA - 慢速EMA
        macd_line = ema_fast - ema_slow
        
        # 信号线 = MACD线的EMA
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # 柱状图 = MACD线 - 信号线
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }, index=data.index)


class BollingerBandsIndicator(BaseIndicator):
    """布林带指标"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        config = IndicatorConfig(
            name="BOLLINGER_BANDS",
            type=IndicatorType.TREND,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 20, 'required': False},
                'std_dev': {'type': float, 'min': 0.1, 'max': 5.0, 'default': 2.0, 'required': False}
            },
            description="布林带指标，包括上轨、中轨(移动平均)、下轨"
        )
        super().__init__(config)
        self.period = period
        self.std_dev = std_dev
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, column: str = 'close', **kwargs) -> pd.DataFrame:
        """计算布林带"""
        self.validate_data(data, [column])
        
        period = kwargs.get('period', self.period)
        std_dev = kwargs.get('std_dev', self.std_dev)
        
        price_series = ensure_numeric(data[column])
        
        # 中轨：移动平均线
        middle_band = price_series.rolling(window=period, min_periods=1).mean()
        
        # 标准差
        std = price_series.rolling(window=period, min_periods=1).std()
        
        # 上轨和下轨
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        # 计算布林带宽度和位置
        bb_width = (upper_band - lower_band) / middle_band * 100
        bb_position = (price_series - lower_band) / (upper_band - lower_band) * 100
        
        return pd.DataFrame({
            'upper_band': upper_band,
            'middle_band': middle_band,
            'lower_band': lower_band,
            'bb_width': bb_width,
            'bb_position': bb_position
        }, index=data.index)


class ParabolicSARIndicator(BaseIndicator):
    """抛物线SAR指标"""
    
    def __init__(self, af_start: float = 0.02, af_increment: float = 0.02, af_max: float = 0.2):
        config = IndicatorConfig(
            name="PARABOLIC_SAR",
            type=IndicatorType.TREND,
            parameters={
                'af_start': {'type': float, 'min': 0.001, 'max': 0.1, 'default': 0.02, 'required': False},
                'af_increment': {'type': float, 'min': 0.001, 'max': 0.1, 'default': 0.02, 'required': False},
                'af_max': {'type': float, 'min': 0.1, 'max': 1.0, 'default': 0.2, 'required': False}
            },
            description="抛物线SAR指标，用于判断趋势转换点"
        )
        super().__init__(config)
        self.af_start = af_start
        self.af_increment = af_increment
        self.af_max = af_max
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """计算抛物线SAR"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        af_start = kwargs.get('af_start', self.af_start)
        af_increment = kwargs.get('af_increment', self.af_increment)
        af_max = kwargs.get('af_max', self.af_max)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        length = len(data)
        sar = np.zeros(length)
        trend = np.zeros(length)  # 1 for uptrend, -1 for downtrend
        af = np.zeros(length)
        ep = np.zeros(length)  # extreme point
        
        # 初始化
        sar[0] = low.iloc[0]
        trend[0] = 1
        af[0] = af_start
        ep[0] = high.iloc[0]
        
        for i in range(1, length):
            if trend[i-1] == 1:  # 上升趋势
                sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
                
                # 确保SAR不超过前两个周期的最低价
                if i >= 2:
                    sar[i] = min(sar[i], low.iloc[i-1], low.iloc[i-2])
                else:
                    sar[i] = min(sar[i], low.iloc[i-1])
                
                # 检查趋势是否反转
                if low.iloc[i] <= sar[i]:
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    af[i] = af_start
                    ep[i] = low.iloc[i]
                else:
                    trend[i] = 1
                    if high.iloc[i] > ep[i-1]:
                        ep[i] = high.iloc[i]
                        af[i] = min(af[i-1] + af_increment, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
            
            else:  # 下降趋势
                sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
                
                # 确保SAR不超过前两个周期的最高价
                if i >= 2:
                    sar[i] = max(sar[i], high.iloc[i-1], high.iloc[i-2])
                else:
                    sar[i] = max(sar[i], high.iloc[i-1])
                
                # 检查趋势是否反转
                if high.iloc[i] >= sar[i]:
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    af[i] = af_start
                    ep[i] = high.iloc[i]
                else:
                    trend[i] = -1
                    if low.iloc[i] < ep[i-1]:
                        ep[i] = low.iloc[i]
                        af[i] = min(af[i-1] + af_increment, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
        
        return pd.Series(sar, index=data.index, name='sar')


class ADXIndicator(BaseIndicator):
    """平均趋向指数ADX"""
    
    def __init__(self, period: int = 14):
        config = IndicatorConfig(
            name="ADX",
            type=IndicatorType.TREND,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False}
            },
            description="平均趋向指数，衡量趋势强度"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算ADX"""
        self.validate_data(data, ['high', 'low', 'close'])
        
        period = kwargs.get('period', self.period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        
        # 计算真实波幅TR
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 计算方向移动DM
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        plus_dm = pd.Series(plus_dm, index=data.index)
        minus_dm = pd.Series(minus_dm, index=data.index)
        
        # 计算平滑的TR和DM
        atr = tr.ewm(span=period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)
        
        # 计算ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period, adjust=False).mean()
        
        return pd.DataFrame({
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }, index=data.index)