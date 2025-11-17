"""
数据聚合服务
负责整合K线数据、实时盘口、技术指标和市场环境分析
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from ..config.settings import settings
from .performance_monitor import monitor_performance
from .technical_indicators import TechnicalIndicatorService

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RealtimeQuote:
    """实时盘口数据"""
    symbol: str
    timestamp: datetime
    current_price: float
    change: float
    change_percent: float
    volume: int
    amount: float
    bid_prices: List[float] = field(default_factory=list)  # 买盘价格
    bid_volumes: List[int] = field(default_factory=list)   # 买盘量
    ask_prices: List[float] = field(default_factory=list)  # 卖盘价格
    ask_volumes: List[int] = field(default_factory=list)   # 卖盘量
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    prev_close: float = 0.0

@dataclass
class MarketEnvironment:
    """市场环境分析"""
    timestamp: datetime
    market_trend: str  # 'bullish', 'bearish', 'sideways'
    market_volatility: float  # 市场波动率
    sector_performance: Dict[str, float]  # 板块表现
    market_sentiment: float  # 市场情绪 (-1 to 1)
    risk_level: str  # 'low', 'medium', 'high'
    major_indices: Dict[str, Dict[str, float]]  # 主要指数数据
    market_breadth: Dict[str, float]  # 市场广度指标
    liquidity_index: float  # 流动性指数
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AggregatedData:
    """聚合数据"""
    symbol: str
    timestamp: datetime
    kline_data: List[MarketData]  # K线数据
    realtime_quote: Optional[RealtimeQuote]  # 实时盘口
    technical_indicators: Dict[str, Any]  # 技术指标
    market_environment: Optional[MarketEnvironment]  # 市场环境
    metadata: Dict[str, Any] = field(default_factory=dict)

class DataSource:
    """数据源基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.last_update = None
        self.error_count = 0
        self.max_errors = 5
    
    async def fetch_data(self, symbol: str, **kwargs) -> Any:
        """获取数据"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return self.enabled and self.error_count < self.max_errors

class MockDataSource(DataSource):
    """模拟数据源"""
    
    def __init__(self):
        super().__init__("mock_data_source")
    
    @monitor_performance
    async def fetch_kline_data(self, symbol: str, period: str = "60min", count: int = 100) -> List[MarketData]:
        """获取K线数据"""
        try:
            # 模拟K线数据生成
            end_time = datetime.now()
            data = []
            
            base_price = 100.0  # 基础价格
            
            for i in range(count):
                timestamp = end_time - timedelta(hours=count-i)
                
                # 模拟价格波动
                price_change = np.random.normal(0, 2)  # 正态分布价格变化
                open_price = base_price + price_change
                
                high_price = open_price + abs(np.random.normal(0, 1))
                low_price = open_price - abs(np.random.normal(0, 1))
                close_price = open_price + np.random.normal(0, 1)
                
                volume = int(np.random.uniform(10000, 100000))
                amount = volume * close_price
                
                data.append(MarketData(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=volume,
                    amount=round(amount, 2)
                ))
                
                base_price = close_price  # 下一根K线的基础价格
            
            self.last_update = datetime.now()
            return data
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"获取K线数据失败: {str(e)}")
            raise
    
    @monitor_performance
    async def fetch_realtime_quote(self, symbol: str) -> RealtimeQuote:
        """获取实时盘口数据"""
        try:
            current_time = datetime.now()
            base_price = 100.0
            
            # 模拟实时价格
            current_price = base_price + np.random.normal(0, 2)
            prev_close = base_price
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
            
            # 模拟买卖盘
            bid_prices = [current_price - i * 0.01 for i in range(1, 6)]
            ask_prices = [current_price + i * 0.01 for i in range(1, 6)]
            bid_volumes = [int(np.random.uniform(100, 1000)) for _ in range(5)]
            ask_volumes = [int(np.random.uniform(100, 1000)) for _ in range(5)]
            
            quote = RealtimeQuote(
                symbol=symbol,
                timestamp=current_time,
                current_price=round(current_price, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                volume=int(np.random.uniform(10000, 50000)),
                amount=round(current_price * np.random.uniform(10000, 50000), 2),
                bid_prices=[round(p, 2) for p in bid_prices],
                bid_volumes=bid_volumes,
                ask_prices=[round(p, 2) for p in ask_prices],
                ask_volumes=ask_volumes,
                high=round(current_price + abs(np.random.normal(0, 1)), 2),
                low=round(current_price - abs(np.random.normal(0, 1)), 2),
                open=round(base_price, 2),
                prev_close=round(prev_close, 2)
            )
            
            self.last_update = datetime.now()
            return quote
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"获取实时盘口数据失败: {str(e)}")
            raise
    
    @monitor_performance
    async def fetch_market_environment(self) -> MarketEnvironment:
        """获取市场环境数据"""
        try:
            current_time = datetime.now()
            
            # 模拟市场环境数据
            trends = ['bullish', 'bearish', 'sideways']
            risk_levels = ['low', 'medium', 'high']
            
            # 模拟板块表现
            sectors = ['科技', '金融', '医药', '消费', '地产', '能源', '材料', '工业']
            sector_performance = {
                sector: round(np.random.normal(0, 3), 2) 
                for sector in sectors
            }
            
            # 模拟主要指数
            indices = {
                '上证指数': {
                    'current': round(3000 + np.random.normal(0, 100), 2),
                    'change': round(np.random.normal(0, 30), 2),
                    'change_percent': round(np.random.normal(0, 1), 2)
                },
                '深证成指': {
                    'current': round(10000 + np.random.normal(0, 300), 2),
                    'change': round(np.random.normal(0, 100), 2),
                    'change_percent': round(np.random.normal(0, 1.5), 2)
                },
                '创业板指': {
                    'current': round(2000 + np.random.normal(0, 100), 2),
                    'change': round(np.random.normal(0, 50), 2),
                    'change_percent': round(np.random.normal(0, 2), 2)
                }
            }
            
            # 模拟市场广度指标
            market_breadth = {
                'advance_decline_ratio': round(np.random.uniform(0.3, 1.7), 2),
                'new_high_low_ratio': round(np.random.uniform(0.1, 2.0), 2),
                'volume_ratio': round(np.random.uniform(0.5, 1.5), 2)
            }
            
            environment = MarketEnvironment(
                timestamp=current_time,
                market_trend=np.random.choice(trends),
                market_volatility=round(np.random.uniform(0.1, 0.5), 3),
                sector_performance=sector_performance,
                market_sentiment=round(np.random.uniform(-1, 1), 2),
                risk_level=np.random.choice(risk_levels),
                major_indices=indices,
                market_breadth=market_breadth,
                liquidity_index=round(np.random.uniform(0.3, 1.2), 2)
            )
            
            self.last_update = datetime.now()
            return environment
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"获取市场环境数据失败: {str(e)}")
            raise

class DataAggregator:
    """数据聚合器"""
    
    def __init__(self):
        self.data_sources = {
            'mock': MockDataSource()
        }
        self.technical_indicator_service = TechnicalIndicatorService()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.cache = {}
        self.cache_ttl = 60  # 缓存60秒
    
    def add_data_source(self, name: str, source: DataSource):
        """添加数据源"""
        self.data_sources[name] = source
        logger.info(f"添加数据源: {name}")
    
    def remove_data_source(self, name: str):
        """移除数据源"""
        if name in self.data_sources:
            del self.data_sources[name]
            logger.info(f"移除数据源: {name}")
    
    def _get_cache_key(self, symbol: str, data_type: str) -> str:
        """生成缓存键"""
        return f"{symbol}_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    def _is_cache_valid(self, cache_time: datetime) -> bool:
        """检查缓存是否有效"""
        return (datetime.now() - cache_time).total_seconds() < self.cache_ttl
    
    @monitor_performance
    async def aggregate_data(self, symbol: str, include_indicators: bool = True) -> AggregatedData:
        """聚合指定股票的所有数据"""
        try:
            logger.info(f"开始聚合数据: {symbol}")
            
            # 并行获取各类数据
            tasks = []
            
            # 获取K线数据
            for source_name, source in self.data_sources.items():
                if source.is_available():
                    tasks.append(('kline', source.fetch_kline_data(symbol)))
                    break
            
            # 获取实时盘口数据
            for source_name, source in self.data_sources.items():
                if source.is_available():
                    tasks.append(('quote', source.fetch_realtime_quote(symbol)))
                    break
            
            # 获取市场环境数据
            for source_name, source in self.data_sources.items():
                if source.is_available():
                    tasks.append(('environment', source.fetch_market_environment()))
                    break
            
            # 执行并行任务
            results = {}
            for task_type, task in tasks:
                try:
                    result = await task
                    results[task_type] = result
                except Exception as e:
                    logger.error(f"获取{task_type}数据失败: {str(e)}")
                    results[task_type] = None
            
            # 计算技术指标
            technical_indicators = {}
            if include_indicators and 'kline' in results and results['kline']:
                try:
                    kline_data = results['kline']
                    df = pd.DataFrame([
                        {
                            'timestamp': d.timestamp,
                            'open': d.open,
                            'high': d.high,
                            'low': d.low,
                            'close': d.close,
                            'volume': d.volume
                        }
                        for d in kline_data
                    ])
                    
                    # 计算各类技术指标
                    technical_indicators = await self._calculate_technical_indicators(df)
                    
                except Exception as e:
                    logger.error(f"计算技术指标失败: {str(e)}")
            
            # 构建聚合数据
            aggregated_data = AggregatedData(
                symbol=symbol,
                timestamp=datetime.now(),
                kline_data=results.get('kline', []),
                realtime_quote=results.get('quote'),
                technical_indicators=technical_indicators,
                market_environment=results.get('environment'),
                metadata={
                    'data_sources_used': list(self.data_sources.keys()),
                    'aggregation_time': datetime.now().isoformat(),
                    'data_quality': self._assess_data_quality(results)
                }
            )
            
            logger.info(f"数据聚合完成: {symbol}")
            return aggregated_data
            
        except Exception as e:
            logger.error(f"数据聚合失败: {symbol}, 错误: {str(e)}")
            raise
    
    @monitor_performance
    async def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算技术指标"""
        indicators = {}
        
        try:
            # 趋势指标
            indicators['trend'] = {
                'sma_20': self.technical_indicator_service.calculate_sma(df['close'], 20).iloc[-1],
                'sma_60': self.technical_indicator_service.calculate_sma(df['close'], 60).iloc[-1],
                'ema_12': self.technical_indicator_service.calculate_ema(df['close'], 12).iloc[-1],
                'ema_26': self.technical_indicator_service.calculate_ema(df['close'], 26).iloc[-1],
            }
            
            # MACD
            macd_line, signal_line, histogram = self.technical_indicator_service.calculate_macd(df['close'])
            indicators['macd'] = {
                'macd_line': macd_line.iloc[-1],
                'signal_line': signal_line.iloc[-1],
                'histogram': histogram.iloc[-1]
            }
            
            # 布林带
            upper, middle, lower = self.technical_indicator_service.calculate_bollinger_bands(df['close'])
            indicators['bollinger'] = {
                'upper': upper.iloc[-1],
                'middle': middle.iloc[-1],
                'lower': lower.iloc[-1],
                'position': (df['close'].iloc[-1] - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])
            }
            
            # 动量指标
            indicators['momentum'] = {
                'rsi': self.technical_indicator_service.calculate_rsi(df['close']).iloc[-1],
                'stoch_k': self.technical_indicator_service.calculate_stochastic(df['high'], df['low'], df['close'])[0].iloc[-1],
                'stoch_d': self.technical_indicator_service.calculate_stochastic(df['high'], df['low'], df['close'])[1].iloc[-1],
            }
            
            # 成交量指标
            if 'volume' in df.columns:
                indicators['volume'] = {
                    'volume_sma': self.technical_indicator_service.calculate_sma(df['volume'], 20).iloc[-1],
                    'volume_ratio': df['volume'].iloc[-1] / self.technical_indicator_service.calculate_sma(df['volume'], 20).iloc[-1],
                }
            
            # 波动率指标
            indicators['volatility'] = {
                'atr': self.technical_indicator_service.calculate_atr(df['high'], df['low'], df['close']).iloc[-1],
            }
            
        except Exception as e:
            logger.error(f"计算技术指标时出错: {str(e)}")
        
        return indicators
    
    def _assess_data_quality(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量"""
        quality = {
            'completeness': 0.0,
            'freshness': 0.0,
            'accuracy': 0.0,
            'overall': 0.0
        }
        
        try:
            # 完整性评估
            expected_data_types = ['kline', 'quote', 'environment']
            available_data = sum(1 for dt in expected_data_types if results.get(dt) is not None)
            quality['completeness'] = available_data / len(expected_data_types)
            
            # 新鲜度评估（基于数据时间戳）
            current_time = datetime.now()
            freshness_scores = []
            
            for data_type, data in results.items():
                if data is not None:
                    if hasattr(data, 'timestamp'):
                        age = (current_time - data.timestamp).total_seconds()
                        freshness_score = max(0, 1 - age / 3600)  # 1小时内为满分
                        freshness_scores.append(freshness_score)
                    elif isinstance(data, list) and data and hasattr(data[0], 'timestamp'):
                        age = (current_time - data[-1].timestamp).total_seconds()
                        freshness_score = max(0, 1 - age / 3600)
                        freshness_scores.append(freshness_score)
            
            quality['freshness'] = np.mean(freshness_scores) if freshness_scores else 0.0
            
            # 准确性评估（基于数据源可用性）
            available_sources = sum(1 for source in self.data_sources.values() if source.is_available())
            total_sources = len(self.data_sources)
            quality['accuracy'] = available_sources / total_sources if total_sources > 0 else 0.0
            
            # 综合评分
            quality['overall'] = (quality['completeness'] + quality['freshness'] + quality['accuracy']) / 3
            
        except Exception as e:
            logger.error(f"评估数据质量时出错: {str(e)}")
        
        return quality
    
    async def get_batch_data(self, symbols: List[str], include_indicators: bool = True) -> Dict[str, AggregatedData]:
        """批量获取多个股票的聚合数据"""
        results = {}
        
        # 并行处理多个股票
        tasks = [self.aggregate_data(symbol, include_indicators) for symbol in symbols]
        
        try:
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(symbols, completed_tasks):
                if isinstance(result, Exception):
                    logger.error(f"获取{symbol}数据失败: {str(result)}")
                    results[symbol] = None
                else:
                    results[symbol] = result
                    
        except Exception as e:
            logger.error(f"批量获取数据失败: {str(e)}")
        
        return results
    
    def get_data_source_status(self) -> Dict[str, Dict[str, Any]]:
        """获取数据源状态"""
        status = {}
        
        for name, source in self.data_sources.items():
            status[name] = {
                'name': source.name,
                'enabled': source.enabled,
                'available': source.is_available(),
                'last_update': source.last_update.isoformat() if source.last_update else None,
                'error_count': source.error_count,
                'max_errors': source.max_errors
            }
        
        return status

# 全局数据聚合器实例
global_data_aggregator = DataAggregator()

# 导出主要接口
__all__ = [
    'DataAggregator',
    'MarketData',
    'RealtimeQuote',
    'MarketEnvironment',
    'AggregatedData',
    'DataSource',
    'MockDataSource',
    'global_data_aggregator'
]