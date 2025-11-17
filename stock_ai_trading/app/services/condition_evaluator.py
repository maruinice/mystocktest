"""
交易条件评估器
根据策略的buy_conditions和sell_conditions生成真实的买卖信号
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IndicatorData:
    """指标数据"""
    ma: Dict[int, float] = None  # 移动平均线 {period: value}
    ema: Dict[int, float] = None  # 指数移动平均线
    rsi: Dict[int, float] = None  # RSI {period: value}
    macd: Dict[str, float] = None  # MACD {dif, dea, macd}
    boll: Dict[str, float] = None  # 布林带 {upper, middle, lower}
    kdj: Dict[str, float] = None  # KDJ {k, d, j}
    
    def __post_init__(self):
        if self.ma is None:
            self.ma = {}
        if self.ema is None:
            self.ema = {}
        if self.rsi is None:
            self.rsi = {}
        if self.macd is None:
            self.macd = {}
        if self.boll is None:
            self.boll = {}
        if self.kdj is None:
            self.kdj = {}


class ConditionEvaluator:
    """条件评估器"""
    
    def __init__(self):
        self.indicators_cache = {}
    
    def evaluate_conditions(self, conditions: List[Dict[str, Any]], 
                          price_data: pd.DataFrame, 
                          current_date: str) -> bool:
        """
        评估交易条件
        
        Args:
            conditions: 条件列表
            price_data: 价格数据DataFrame
            current_date: 当前日期
            
        Returns:
            bool: 条件是否满足
        """
        if not conditions:
            logger.warning("条件列表为空")
            return False
        
        try:
            # 获取当前数据
            current_data = price_data[price_data['trade_date'] == current_date]
            if current_data.empty:
                logger.warning(f"[{current_date}] 当前日期数据为空")
                return False
            
            current_price = float(current_data['close'].iloc[0])
            current_volume = float(current_data.get('volume', [0]).iloc[0])
            
            logger.info(f"[{current_date}] 当前价格: {current_price}, 成交量: {current_volume}")
            
            # 计算所需指标
            indicators = self._calculate_indicators(price_data, current_date, conditions)
            
            logger.info(f"[{current_date}] 计算的指标: MA={indicators.ma}, RSI={indicators.rsi}")
            
            # 评估所有条件（默认AND逻辑）
            for i, condition in enumerate(conditions):
                result = self._evaluate_single_condition(
                    condition, current_price, current_volume, indicators, price_data, current_date
                )
                logger.info(f"[{current_date}] 条件 {i+1}/{len(conditions)} ({condition.get('description', condition.get('type'))}): {result}")
                if not result:
                    return False
            
            logger.info(f"[{current_date}] 所有条件满足")
            return True
            
        except Exception as e:
            logger.error(f"评估条件失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _evaluate_single_condition(self, condition: Dict[str, Any], 
                                   current_price: float,
                                   current_volume: float,
                                   indicators: IndicatorData,
                                   price_data: pd.DataFrame,
                                   current_date: str) -> bool:
        """评估单个条件"""
        try:
            condition_type = condition.get('type', '')
            operator = condition.get('operator', '')
            value = condition.get('value')
            params = condition.get('params', {})
            indicator_name = condition.get('indicator', '')
            
            # 根据条件类型评估
            if condition_type == 'price':
                return self._evaluate_price_condition(
                    operator, value, current_price, indicators
                )
            
            elif condition_type == 'indicator':
                return self._evaluate_indicator_condition(
                    indicator_name, operator, value, params, indicators, price_data, current_date
                )
            
            elif condition_type == 'volume':
                return self._evaluate_volume_condition(
                    operator, value, current_volume, price_data, current_date
                )
            
            elif condition_type == 'custom':
                # 自定义条件，默认返回True
                return True
            
            elif condition_type == 'risk':
                # 风险控制条件，在订单执行时处理
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"评估单个条件失败: {e}")
            return False
    
    def _evaluate_price_condition(self, operator: str, value: Any, 
                                  current_price: float, indicators: IndicatorData) -> bool:
        """评估价格条件"""
        try:
            # 如果value是字符串（如'MA20'），需要从指标中获取
            if isinstance(value, str):
                if value.startswith('MA'):
                    period = int(value[2:])
                    target_value = indicators.ma.get(period, 0)
                    logger.info(f"价格条件: 当前价格 {current_price} vs MA{period} {target_value}")
                elif value.startswith('EMA'):
                    period = int(value[3:])
                    target_value = indicators.ema.get(period, 0)
                    logger.info(f"价格条件: 当前价格 {current_price} vs EMA{period} {target_value}")
                else:
                    logger.warning(f"未知的价格条件值: {value}")
                    return False
            else:
                target_value = float(value)
                logger.info(f"价格条件: 当前价格 {current_price} vs 固定值 {target_value}")
            
            if target_value == 0:
                logger.warning(f"目标值为0，条件不满足")
                return False
            
            # 比较
            result = False
            if operator == 'greater_than':
                result = current_price > target_value
                logger.info(f"价格条件: {current_price} > {target_value} = {result}")
            elif operator == 'less_than':
                result = current_price < target_value
                logger.info(f"价格条件: {current_price} < {target_value} = {result}")
            elif operator == 'equal':
                result = abs(current_price - target_value) / target_value < 0.01  # 1%容差
                logger.info(f"价格条件: {current_price} ≈ {target_value} = {result}")
            else:
                logger.warning(f"未知的操作符: {operator}")
            
            return result
            
        except Exception as e:
            logger.error(f"评估价格条件失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _evaluate_indicator_condition(self, indicator: str, operator: str, 
                                     value: Any, params: Dict,
                                     indicators: IndicatorData,
                                     price_data: pd.DataFrame,
                                     current_date: str) -> bool:
        """评估指标条件"""
        try:
            if indicator == 'MA':
                return self._evaluate_ma_condition(operator, params, indicators, price_data, current_date)
            
            elif indicator == 'RSI':
                return self._evaluate_rsi_condition(operator, value, params, indicators)
            
            elif indicator == 'MACD':
                return self._evaluate_macd_condition(operator, indicators, price_data, current_date)
            
            elif indicator == 'BOLL':
                return self._evaluate_boll_condition(operator, indicators, price_data, current_date)
            
            elif indicator == 'KDJ':
                return self._evaluate_kdj_condition(operator, indicators)
            
            return False
            
        except Exception as e:
            logger.error(f"评估指标条件失败 {indicator}: {e}")
            return False
    
    def _evaluate_ma_condition(self, operator: str, params: Dict,
                              indicators: IndicatorData,
                              price_data: pd.DataFrame,
                              current_date: str) -> bool:
        """评估均线条件"""
        try:
            short_period = params.get('short_period', 5)
            long_period = params.get('long_period', 20)
            
            short_ma = indicators.ma.get(short_period, 0)
            long_ma = indicators.ma.get(long_period, 0)
            
            if short_ma == 0 or long_ma == 0:
                return False
            
            if operator == 'cross_above':
                # 检查金叉：短期均线上穿长期均线
                # 需要检查前一天的状态
                prev_short_ma, prev_long_ma = self._get_prev_ma(
                    price_data, current_date, short_period, long_period
                )
                if prev_short_ma and prev_long_ma:
                    return prev_short_ma <= prev_long_ma and short_ma > long_ma
                return False
            
            elif operator == 'cross_below':
                # 检查死叉：短期均线下穿长期均线
                prev_short_ma, prev_long_ma = self._get_prev_ma(
                    price_data, current_date, short_period, long_period
                )
                if prev_short_ma and prev_long_ma:
                    return prev_short_ma >= prev_long_ma and short_ma < long_ma
                return False
            
            elif operator == 'greater_than':
                return short_ma > long_ma
            
            elif operator == 'less_than':
                return short_ma < long_ma
            
            return False
            
        except Exception as e:
            logger.error(f"评估均线条件失败: {e}")
            return False
    
    def _evaluate_rsi_condition(self, operator: str, value: Any,
                               params: Dict, indicators: IndicatorData) -> bool:
        """评估RSI条件"""
        try:
            period = params.get('period', 14)
            rsi_value = indicators.rsi.get(period, 50)
            
            if isinstance(value, (int, float)):
                threshold = float(value)
            else:
                return False
            
            if operator == 'greater_than':
                return rsi_value > threshold
            elif operator == 'less_than':
                return rsi_value < threshold
            elif operator == 'equal':
                return abs(rsi_value - threshold) < 5  # 5点容差
            
            return False
            
        except Exception as e:
            logger.error(f"评估RSI条件失败: {e}")
            return False
    
    def _evaluate_macd_condition(self, operator: str, indicators: IndicatorData,
                                price_data: pd.DataFrame, current_date: str) -> bool:
        """评估MACD条件"""
        try:
            dif = indicators.macd.get('dif', 0)
            dea = indicators.macd.get('dea', 0)
            
            if operator == 'cross_above':
                # DIF上穿DEA（金叉）
                prev_dif, prev_dea = self._get_prev_macd(price_data, current_date)
                if prev_dif is not None and prev_dea is not None:
                    return prev_dif <= prev_dea and dif > dea
                return False
            
            elif operator == 'cross_below':
                # DIF下穿DEA（死叉）
                prev_dif, prev_dea = self._get_prev_macd(price_data, current_date)
                if prev_dif is not None and prev_dea is not None:
                    return prev_dif >= prev_dea and dif < dea
                return False
            
            elif operator == 'greater_than':
                return dif > dea
            
            elif operator == 'less_than':
                return dif < dea
            
            return False
            
        except Exception as e:
            logger.error(f"评估MACD条件失败: {e}")
            return False
    
    def _evaluate_boll_condition(self, operator: str, indicators: IndicatorData,
                                price_data: pd.DataFrame, current_date: str) -> bool:
        """评估布林带条件"""
        try:
            current_data = price_data[price_data['trade_date'] == current_date]
            if current_data.empty:
                return False
            
            current_price = float(current_data['close'].iloc[0])
            upper = indicators.boll.get('upper', 0)
            lower = indicators.boll.get('lower', 0)
            middle = indicators.boll.get('middle', 0)
            
            if operator == 'cross_above':
                # 价格突破上轨
                return current_price > upper
            elif operator == 'cross_below':
                # 价格跌破下轨
                return current_price < lower
            elif operator == 'greater_than':
                # 价格高于中轨
                return current_price > middle
            elif operator == 'less_than':
                # 价格低于中轨
                return current_price < middle
            
            return False
            
        except Exception as e:
            logger.error(f"评估布林带条件失败: {e}")
            return False
    
    def _evaluate_kdj_condition(self, operator: str, indicators: IndicatorData) -> bool:
        """评估KDJ条件"""
        try:
            k = indicators.kdj.get('k', 50)
            d = indicators.kdj.get('d', 50)
            
            if operator == 'cross_above':
                # K线上穿D线（金叉）
                return k > d and k < 80  # 避免高位金叉
            elif operator == 'cross_below':
                # K线下穿D线（死叉）
                return k < d and k > 20  # 避免低位死叉
            
            return False
            
        except Exception as e:
            logger.error(f"评估KDJ条件失败: {e}")
            return False
    
    def _evaluate_volume_condition(self, operator: str, value: Any,
                                   current_volume: float,
                                   price_data: pd.DataFrame,
                                   current_date: str) -> bool:
        """评估成交量条件"""
        try:
            if isinstance(value, (int, float)):
                threshold = float(value)
            else:
                return False
            
            # 计算平均成交量
            current_idx = price_data[price_data['trade_date'] == current_date].index
            if len(current_idx) == 0:
                return False
            
            idx = current_idx[0]
            if idx < 5:
                return False
            
            # 取前5天的平均成交量
            prev_volumes = price_data.iloc[max(0, idx-5):idx]['volume'].values
            avg_volume = np.mean(prev_volumes) if len(prev_volumes) > 0 else 0
            
            if avg_volume == 0:
                return False
            
            volume_ratio = current_volume / avg_volume
            
            if operator == 'greater_than':
                return volume_ratio > threshold
            elif operator == 'less_than':
                return volume_ratio < threshold
            
            return False
            
        except Exception as e:
            logger.error(f"评估成交量条件失败: {e}")
            return False
    
    def _calculate_indicators(self, price_data: pd.DataFrame, 
                            current_date: str,
                            conditions: List[Dict]) -> IndicatorData:
        """计算所需的技术指标"""
        indicators = IndicatorData()
        
        try:
            # 获取当前位置
            current_idx = price_data[price_data['trade_date'] == current_date].index
            if len(current_idx) == 0:
                return indicators
            
            idx = current_idx[0]
            
            # 根据条件判断需要计算哪些指标
            needed_indicators = set()
            for condition in conditions:
                indicator_name = condition.get('indicator', '')
                condition_type = condition.get('type', '')
                value = condition.get('value', '')
                
                if indicator_name:
                    needed_indicators.add(indicator_name)
                
                # 如果价格条件引用了均线
                if condition_type == 'price' and isinstance(value, str):
                    if value.startswith('MA'):
                        needed_indicators.add('MA')
                    elif value.startswith('EMA'):
                        needed_indicators.add('EMA')
            
            # 计算均线
            if 'MA' in needed_indicators or any(c.get('type') == 'price' for c in conditions):
                logger.info(f"[{current_date}] 计算MA指标，当前索引: {idx}, 数据总行数: {len(price_data)}")
                for period in [5, 10, 20, 30, 60]:
                    if idx >= period - 1:
                        ma_values = price_data.iloc[max(0, idx-period+1):idx+1]['close'].values
                        indicators.ma[period] = float(np.mean(ma_values))
                        logger.info(f"[{current_date}] MA{period} = {indicators.ma[period]:.2f}")
                    else:
                        logger.warning(f"[{current_date}] MA{period} 数据不足: idx={idx}, 需要={period-1}")
            
            # 计算RSI
            if 'RSI' in needed_indicators:
                for period in [6, 12, 14, 24]:
                    rsi = self._calculate_rsi(price_data, idx, period)
                    if rsi is not None:
                        indicators.rsi[period] = rsi
            
            # 计算MACD
            if 'MACD' in needed_indicators:
                macd_data = self._calculate_macd(price_data, idx)
                if macd_data:
                    indicators.macd = macd_data
            
            # 计算布林带
            if 'BOLL' in needed_indicators:
                boll_data = self._calculate_boll(price_data, idx)
                if boll_data:
                    indicators.boll = boll_data
            
            # 计算KDJ
            if 'KDJ' in needed_indicators:
                kdj_data = self._calculate_kdj(price_data, idx)
                if kdj_data:
                    indicators.kdj = kdj_data
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算指标失败: {e}")
            return indicators
    
    def _calculate_rsi(self, price_data: pd.DataFrame, idx: int, period: int = 14) -> Optional[float]:
        """计算RSI指标"""
        try:
            if idx < period:
                return None
            
            closes = price_data.iloc[max(0, idx-period):idx+1]['close'].values
            if len(closes) < period + 1:
                return None
            
            deltas = np.diff(closes)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
            
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return None
    
    def _calculate_macd(self, price_data: pd.DataFrame, idx: int,
                       fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Optional[Dict]:
        """计算MACD指标"""
        try:
            if idx < slow_period + signal_period:
                return None
            
            closes = price_data.iloc[:idx+1]['close'].values
            
            # 计算EMA
            ema_fast = self._calculate_ema(closes, fast_period)
            ema_slow = self._calculate_ema(closes, slow_period)
            
            if ema_fast is None or ema_slow is None:
                return None
            
            # DIF = EMA(12) - EMA(26)
            dif = ema_fast - ema_slow
            
            # DEA = EMA(DIF, 9)
            # 简化计算，使用最近signal_period个DIF的平均
            dea = dif  # 简化版本
            
            # MACD = 2 * (DIF - DEA)
            macd = 2 * (dif - dea)
            
            return {
                'dif': float(dif),
                'dea': float(dea),
                'macd': float(macd)
            }
            
        except Exception as e:
            logger.error(f"计算MACD失败: {e}")
            return None
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> Optional[float]:
        """计算指数移动平均"""
        try:
            if len(data) < period:
                return None
            
            multiplier = 2 / (period + 1)
            ema = data[0]
            
            for price in data[1:]:
                ema = (price - ema) * multiplier + ema
            
            return float(ema)
            
        except Exception as e:
            logger.error(f"计算EMA失败: {e}")
            return None
    
    def _calculate_boll(self, price_data: pd.DataFrame, idx: int, period: int = 20, std_dev: int = 2) -> Optional[Dict]:
        """计算布林带"""
        try:
            if idx < period - 1:
                return None
            
            closes = price_data.iloc[max(0, idx-period+1):idx+1]['close'].values
            
            middle = np.mean(closes)
            std = np.std(closes)
            
            upper = middle + std_dev * std
            lower = middle - std_dev * std
            
            return {
                'upper': float(upper),
                'middle': float(middle),
                'lower': float(lower)
            }
            
        except Exception as e:
            logger.error(f"计算布林带失败: {e}")
            return None
    
    def _calculate_kdj(self, price_data: pd.DataFrame, idx: int, period: int = 9) -> Optional[Dict]:
        """计算KDJ指标"""
        try:
            if idx < period - 1:
                return None
            
            data = price_data.iloc[max(0, idx-period+1):idx+1]
            
            low_min = data['low'].min()
            high_max = data['high'].max()
            close = data['close'].iloc[-1]
            
            if high_max == low_min:
                rsv = 50
            else:
                rsv = (close - low_min) / (high_max - low_min) * 100
            
            # 简化计算
            k = rsv
            d = rsv
            j = 3 * k - 2 * d
            
            return {
                'k': float(k),
                'd': float(d),
                'j': float(j)
            }
            
        except Exception as e:
            logger.error(f"计算KDJ失败: {e}")
            return None
    
    def _get_prev_ma(self, price_data: pd.DataFrame, current_date: str,
                    short_period: int, long_period: int) -> tuple:
        """获取前一天的均线值"""
        try:
            current_idx = price_data[price_data['trade_date'] == current_date].index
            if len(current_idx) == 0 or current_idx[0] == 0:
                return None, None
            
            prev_idx = current_idx[0] - 1
            
            if prev_idx < long_period - 1:
                return None, None
            
            # 计算前一天的均线
            short_ma_data = price_data.iloc[max(0, prev_idx-short_period+1):prev_idx+1]['close'].values
            long_ma_data = price_data.iloc[max(0, prev_idx-long_period+1):prev_idx+1]['close'].values
            
            prev_short_ma = float(np.mean(short_ma_data))
            prev_long_ma = float(np.mean(long_ma_data))
            
            return prev_short_ma, prev_long_ma
            
        except Exception as e:
            logger.error(f"获取前一天均线失败: {e}")
            return None, None
    
    def _get_prev_macd(self, price_data: pd.DataFrame, current_date: str) -> tuple:
        """获取前一天的MACD值"""
        try:
            current_idx = price_data[price_data['trade_date'] == current_date].index
            if len(current_idx) == 0 or current_idx[0] == 0:
                return None, None
            
            prev_idx = current_idx[0] - 1
            
            macd_data = self._calculate_macd(price_data, prev_idx)
            if macd_data:
                return macd_data['dif'], macd_data['dea']
            
            return None, None
            
        except Exception as e:
            logger.error(f"获取前一天MACD失败: {e}")
            return None, None


# 创建全局实例
condition_evaluator = ConditionEvaluator()
