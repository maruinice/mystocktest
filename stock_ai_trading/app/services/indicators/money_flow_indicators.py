"""
资金流向指标实现
包括主力资金、北向资金等资金流向相关指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from ..technical_indicators import BaseIndicator, IndicatorConfig, IndicatorType, performance_monitor
from ..technical_indicators import ensure_numeric, typical_price


class MainCapitalFlowIndicator(BaseIndicator):
    """主力资金流向指标"""
    
    def __init__(self, large_order_threshold: float = 1000000):
        config = IndicatorConfig(
            name="MAIN_CAPITAL_FLOW",
            type=IndicatorType.MONEY_FLOW,
            parameters={
                'large_order_threshold': {'type': float, 'min': 100000, 'max': 10000000, 'default': 1000000, 'required': False}
            },
            description="主力资金流向指标，基于大单交易分析资金流向"
        )
        super().__init__(config)
        self.large_order_threshold = large_order_threshold
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算主力资金流向"""
        self.validate_data(data, ['high', 'low', 'close', 'volume', 'amount'])
        
        large_order_threshold = kwargs.get('large_order_threshold', self.large_order_threshold)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        amount = ensure_numeric(data['amount'])
        
        # 计算平均成交价
        avg_price = amount / volume
        avg_price = avg_price.fillna(close)
        
        # 计算价格变化
        price_change = close.diff()
        
        # 估算主力资金流向（基于成交金额和价格变化）
        # 上涨时的成交金额视为流入，下跌时视为流出
        main_inflow = np.where(price_change > 0, amount, 0)
        main_outflow = np.where(price_change < 0, amount, 0)
        
        # 基于成交量大小判断主力行为
        avg_volume = volume.rolling(window=20, min_periods=1).mean()
        large_volume_mask = volume > avg_volume * 2
        
        # 调整主力资金流向
        main_inflow = np.where(large_volume_mask & (price_change > 0), main_inflow * 1.5, main_inflow)
        main_outflow = np.where(large_volume_mask & (price_change < 0), main_outflow * 1.5, main_outflow)
        
        # 计算净流入
        net_inflow = main_inflow - main_outflow
        
        # 计算累计净流入
        cumulative_net_inflow = pd.Series(net_inflow, index=data.index).cumsum()
        
        # 计算资金流向强度
        flow_strength = net_inflow / amount * 100
        flow_strength = flow_strength.fillna(0)
        
        return pd.DataFrame({
            'main_inflow': main_inflow,
            'main_outflow': main_outflow,
            'net_inflow': net_inflow,
            'cumulative_net_inflow': cumulative_net_inflow,
            'flow_strength': flow_strength
        }, index=data.index)


class NorthboundCapitalIndicator(BaseIndicator):
    """北向资金指标（需要外部数据源）"""
    
    def __init__(self):
        config = IndicatorConfig(
            name="NORTHBOUND_CAPITAL",
            type=IndicatorType.MONEY_FLOW,
            parameters={},
            description="北向资金流向指标，需要外部数据源提供北向资金数据"
        )
        super().__init__(config)
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, northbound_data: Optional[pd.DataFrame] = None, **kwargs) -> pd.DataFrame:
        """计算北向资金流向"""
        if northbound_data is None:
            # 如果没有外部数据，使用模拟数据进行演示
            return self._simulate_northbound_data(data)
        
        self.validate_data(northbound_data, ['net_inflow'])
        
        net_inflow = ensure_numeric(northbound_data['net_inflow'])
        
        # 计算累计净流入
        cumulative_inflow = net_inflow.cumsum()
        
        # 计算移动平均
        ma5 = net_inflow.rolling(window=5, min_periods=1).mean()
        ma20 = net_inflow.rolling(window=20, min_periods=1).mean()
        
        # 计算流向强度
        flow_strength = net_inflow / net_inflow.rolling(window=20, min_periods=1).std()
        flow_strength = flow_strength.fillna(0)
        
        return pd.DataFrame({
            'net_inflow': net_inflow,
            'cumulative_inflow': cumulative_inflow,
            'ma5': ma5,
            'ma20': ma20,
            'flow_strength': flow_strength
        }, index=northbound_data.index)
    
    def _simulate_northbound_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """模拟北向资金数据"""
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        
        # 基于价格和成交量变化模拟北向资金流向
        price_change = close.pct_change()
        volume_change = volume.pct_change()
        
        # 模拟净流入（简化模型）
        net_inflow = (price_change * 0.3 + volume_change * 0.2) * np.random.normal(1, 0.1, len(data))
        net_inflow = pd.Series(net_inflow * 1000000, index=data.index)  # 转换为金额单位
        
        cumulative_inflow = net_inflow.cumsum()
        ma5 = net_inflow.rolling(window=5, min_periods=1).mean()
        ma20 = net_inflow.rolling(window=20, min_periods=1).mean()
        
        return pd.DataFrame({
            'net_inflow': net_inflow,
            'cumulative_inflow': cumulative_inflow,
            'ma5': ma5,
            'ma20': ma20,
            'flow_strength': net_inflow / net_inflow.rolling(window=20, min_periods=1).std().fillna(1)
        }, index=data.index)


class InstitutionalFlowIndicator(BaseIndicator):
    """机构资金流向指标"""
    
    def __init__(self, period: int = 20):
        config = IndicatorConfig(
            name="INSTITUTIONAL_FLOW",
            type=IndicatorType.MONEY_FLOW,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 20, 'required': False}
            },
            description="机构资金流向指标，基于大额交易分析机构行为"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算机构资金流向"""
        self.validate_data(data, ['high', 'low', 'close', 'volume', 'amount'])
        
        period = kwargs.get('period', self.period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        amount = ensure_numeric(data['amount'])
        
        # 计算价格变化
        price_change = close.pct_change()
        
        # 识别机构行为特征
        # 1. 大额交易
        avg_amount = amount.rolling(window=period, min_periods=1).mean()
        large_trade_mask = amount > avg_amount * 1.5
        
        # 2. 逆市操作（可能的机构抄底或减仓）
        market_trend = price_change.rolling(window=5, min_periods=1).mean()
        contrarian_mask = (price_change * market_trend) < 0
        
        # 计算机构流入流出
        institutional_inflow = np.where(
            large_trade_mask & (price_change > 0), 
            amount, 
            np.where(contrarian_mask & (price_change > 0), amount * 0.7, 0)
        )
        
        institutional_outflow = np.where(
            large_trade_mask & (price_change < 0), 
            amount, 
            np.where(contrarian_mask & (price_change < 0), amount * 0.7, 0)
        )
        
        # 计算净流入
        net_flow = institutional_inflow - institutional_outflow
        
        # 计算累计净流入
        cumulative_flow = pd.Series(net_flow, index=data.index).cumsum()
        
        # 计算机构活跃度
        activity_score = (large_trade_mask.astype(int) + contrarian_mask.astype(int)).rolling(
            window=period, min_periods=1
        ).sum()
        
        return pd.DataFrame({
            'institutional_inflow': institutional_inflow,
            'institutional_outflow': institutional_outflow,
            'net_flow': net_flow,
            'cumulative_flow': cumulative_flow,
            'activity_score': activity_score
        }, index=data.index)


class SmartMoneyIndicator(BaseIndicator):
    """聪明钱指标"""
    
    def __init__(self, period: int = 14):
        config = IndicatorConfig(
            name="SMART_MONEY",
            type=IndicatorType.MONEY_FLOW,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False}
            },
            description="聪明钱指标，识别专业投资者的资金流向"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算聪明钱指标"""
        self.validate_data(data, ['high', 'low', 'close', 'volume'])
        
        period = kwargs.get('period', self.period)
        
        high = ensure_numeric(data['high'])
        low = ensure_numeric(data['low'])
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        
        # 计算真实波幅
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 计算价格位置
        price_position = (close - low) / (high - low)
        price_position = price_position.fillna(0.5)
        
        # 聪明钱流向 = 成交量 * 价格位置 * 真实波幅权重
        smart_money_flow = volume * price_position * (tr / tr.rolling(window=period, min_periods=1).mean())
        
        # 计算累计聪明钱流向
        cumulative_smart_money = smart_money_flow.cumsum()
        
        # 计算聪明钱强度
        smart_money_strength = smart_money_flow / smart_money_flow.rolling(window=period, min_periods=1).mean()
        smart_money_strength = smart_money_strength.fillna(1)
        
        # 计算聪明钱趋势
        smart_money_trend = smart_money_flow.rolling(window=period, min_periods=1).mean()
        
        return pd.DataFrame({
            'smart_money_flow': smart_money_flow,
            'cumulative_smart_money': cumulative_smart_money,
            'smart_money_strength': smart_money_strength,
            'smart_money_trend': smart_money_trend
        }, index=data.index)


class MoneyFlowIndexAdvancedIndicator(BaseIndicator):
    """高级资金流量指数"""
    
    def __init__(self, period: int = 14):
        config = IndicatorConfig(
            name="MFI_ADVANCED",
            type=IndicatorType.MONEY_FLOW,
            parameters={
                'period': {'type': int, 'min': 1, 'max': 100, 'default': 14, 'required': False}
            },
            description="高级资金流量指数，增强版MFI指标"
        )
        super().__init__(config)
        self.period = period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算高级MFI"""
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
        
        # 计算滚动和
        positive_mf_sum = positive_mf.rolling(window=period, min_periods=1).sum()
        negative_mf_sum = negative_mf.rolling(window=period, min_periods=1).sum()
        
        # 计算MFI
        money_flow_ratio = positive_mf_sum / negative_mf_sum
        mfi = 100 - (100 / (1 + money_flow_ratio))
        
        # 计算MFI变化率
        mfi_change = mfi.diff()
        
        # 计算MFI背离信号
        price_trend = close.rolling(window=period, min_periods=1).apply(
            lambda x: 1 if x.iloc[-1] > x.iloc[0] else -1, raw=False
        )
        mfi_trend = mfi.rolling(window=period, min_periods=1).apply(
            lambda x: 1 if x.iloc[-1] > x.iloc[0] else -1, raw=False
        )
        
        divergence_signal = np.where(price_trend != mfi_trend, 1, 0)
        
        return pd.DataFrame({
            'mfi': mfi,
            'mfi_change': mfi_change,
            'positive_mf_ratio': positive_mf_sum / (positive_mf_sum + negative_mf_sum) * 100,
            'negative_mf_ratio': negative_mf_sum / (positive_mf_sum + negative_mf_sum) * 100,
            'divergence_signal': divergence_signal
        }, index=data.index)


class CapitalFlowAnalysisIndicator(BaseIndicator):
    """综合资金流向分析指标"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20):
        config = IndicatorConfig(
            name="CAPITAL_FLOW_ANALYSIS",
            type=IndicatorType.MONEY_FLOW,
            parameters={
                'short_period': {'type': int, 'min': 1, 'max': 50, 'default': 5, 'required': False},
                'long_period': {'type': int, 'min': 1, 'max': 100, 'default': 20, 'required': False}
            },
            description="综合资金流向分析，结合多个维度分析资金流向"
        )
        super().__init__(config)
        self.short_period = short_period
        self.long_period = long_period
    
    @performance_monitor
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算综合资金流向分析"""
        self.validate_data(data, ['high', 'low', 'close', 'volume', 'amount'])
        
        short_period = kwargs.get('short_period', self.short_period)
        long_period = kwargs.get('long_period', self.long_period)
        
        close = ensure_numeric(data['close'])
        volume = ensure_numeric(data['volume'])
        amount = ensure_numeric(data['amount'])
        
        # 1. 价格动量
        price_momentum = close.pct_change(short_period)
        
        # 2. 成交量动量
        volume_momentum = volume.pct_change(short_period)
        
        # 3. 资金流向强度
        price_change = close.diff()
        flow_direction = np.where(price_change > 0, 1, np.where(price_change < 0, -1, 0))
        flow_strength = amount * flow_direction
        
        # 4. 短期和长期资金流向
        short_flow = flow_strength.rolling(window=short_period, min_periods=1).sum()
        long_flow = flow_strength.rolling(window=long_period, min_periods=1).sum()
        
        # 5. 资金流向比率
        flow_ratio = short_flow / long_flow
        flow_ratio = flow_ratio.fillna(0)
        
        # 6. 综合评分
        momentum_score = (price_momentum + volume_momentum) / 2
        flow_score = flow_ratio
        
        comprehensive_score = (momentum_score * 0.4 + flow_score * 0.6)
        
        # 7. 信号强度
        signal_strength = abs(comprehensive_score)
        
        return pd.DataFrame({
            'price_momentum': price_momentum,
            'volume_momentum': volume_momentum,
            'short_flow': short_flow,
            'long_flow': long_flow,
            'flow_ratio': flow_ratio,
            'comprehensive_score': comprehensive_score,
            'signal_strength': signal_strength
        }, index=data.index)