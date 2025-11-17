"""
Prompt生成服务
负责生成统一的决策Prompt模板和动态上下文构建
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import pandas as pd
from jinja2 import Template, Environment, BaseLoader

from ..config.settings import settings
from .performance_monitor import monitor_performance
from .data_aggregator import AggregatedData, MarketEnvironment, RealtimeQuote

logger = logging.getLogger(__name__)

class RiskPreference(Enum):
    """风险偏好"""
    CONSERVATIVE = "conservative"  # 保守型
    MODERATE = "moderate"         # 稳健型
    AGGRESSIVE = "aggressive"     # 激进型

class TradingAction(Enum):
    """交易动作"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class TradingRules:
    """交易规则"""
    max_position_size: float = 0.3  # 最大仓位比例
    max_single_loss: float = 0.05   # 单笔最大亏损
    stop_loss_ratio: float = 0.08   # 止损比例
    take_profit_ratio: float = 0.15 # 止盈比例
    max_daily_trades: int = 5       # 每日最大交易次数
    min_holding_period: int = 60    # 最小持仓时间（分钟）
    risk_control_enabled: bool = True
    allow_short_selling: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MarketContext:
    """市场上下文"""
    current_time: datetime
    trading_session: str  # 'morning', 'afternoon', 'closed'
    market_phase: str     # 'opening', 'continuous', 'closing'
    volatility_level: str # 'low', 'medium', 'high'
    liquidity_level: str  # 'low', 'medium', 'high'
    news_sentiment: Optional[str] = None
    major_events: List[str] = field(default_factory=list)

@dataclass
class PromptContext:
    """Prompt上下文"""
    symbol: str
    aggregated_data: AggregatedData
    market_context: MarketContext
    risk_preference: RiskPreference
    trading_rules: TradingRules
    historical_decisions: List[Dict[str, Any]] = field(default_factory=list)
    portfolio_status: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class PromptTemplate:
    """Prompt模板"""
    
    def __init__(self):
        self.env = Environment(loader=BaseLoader())
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Template]:
        """加载Prompt模板"""
        templates = {}
        
        # 主决策模板
        templates['main_decision'] = self.env.from_string("""
# 股票交易决策分析

## 基本信息
- 股票代码: {{ symbol }}
- 分析时间: {{ current_time }}
- 交易时段: {{ trading_session }}
- 市场阶段: {{ market_phase }}

## 市场数据分析

### 实时行情
{% if realtime_quote %}
- 当前价格: {{ realtime_quote.current_price }}
- 涨跌幅: {{ realtime_quote.change_percent }}%
- 成交量: {{ realtime_quote.volume }}
- 买一价: {{ realtime_quote.bid_prices[0] if realtime_quote.bid_prices else 'N/A' }}
- 卖一价: {{ realtime_quote.ask_prices[0] if realtime_quote.ask_prices else 'N/A' }}
{% else %}
- 实时行情数据不可用
{% endif %}

### 技术指标分析
{% if technical_indicators %}
#### 趋势指标
- SMA20: {{ technical_indicators.trend.sma_20 if technical_indicators.trend else 'N/A' }}
- SMA60: {{ technical_indicators.trend.sma_60 if technical_indicators.trend else 'N/A' }}
- EMA12: {{ technical_indicators.trend.ema_12 if technical_indicators.trend else 'N/A' }}
- EMA26: {{ technical_indicators.trend.ema_26 if technical_indicators.trend else 'N/A' }}

#### MACD指标
- MACD线: {{ technical_indicators.macd.macd_line if technical_indicators.macd else 'N/A' }}
- 信号线: {{ technical_indicators.macd.signal_line if technical_indicators.macd else 'N/A' }}
- 柱状图: {{ technical_indicators.macd.histogram if technical_indicators.macd else 'N/A' }}

#### 布林带
- 上轨: {{ technical_indicators.bollinger.upper if technical_indicators.bollinger else 'N/A' }}
- 中轨: {{ technical_indicators.bollinger.middle if technical_indicators.bollinger else 'N/A' }}
- 下轨: {{ technical_indicators.bollinger.lower if technical_indicators.bollinger else 'N/A' }}
- 位置: {{ (technical_indicators.bollinger.position * 100) | round(2) if technical_indicators.bollinger else 'N/A' }}%

#### 动量指标
- RSI: {{ technical_indicators.momentum.rsi if technical_indicators.momentum else 'N/A' }}
- 随机指标K: {{ technical_indicators.momentum.stoch_k if technical_indicators.momentum else 'N/A' }}
- 随机指标D: {{ technical_indicators.momentum.stoch_d if technical_indicators.momentum else 'N/A' }}

#### 成交量指标
{% if technical_indicators.volume %}
- 成交量均线: {{ technical_indicators.volume.volume_sma }}
- 量比: {{ technical_indicators.volume.volume_ratio | round(2) }}
{% endif %}

#### 波动率指标
- ATR: {{ technical_indicators.volatility.atr if technical_indicators.volatility else 'N/A' }}
{% endif %}

### 市场环境
{% if market_environment %}
- 市场趋势: {{ market_environment.market_trend }}
- 市场波动率: {{ market_environment.market_volatility }}
- 市场情绪: {{ market_environment.market_sentiment }}
- 风险水平: {{ market_environment.risk_level }}
- 流动性指数: {{ market_environment.liquidity_index }}

#### 主要指数表现
{% for index_name, index_data in market_environment.major_indices.items() %}
- {{ index_name }}: {{ index_data.current }} ({{ index_data.change_percent }}%)
{% endfor %}

#### 板块表现
{% for sector, performance in market_environment.sector_performance.items() %}
- {{ sector }}: {{ performance }}%
{% endfor %}
{% endif %}

## 交易规则约束
- 风险偏好: {{ risk_preference }}
- 最大仓位: {{ (trading_rules.max_position_size * 100) | round(1) }}%
- 止损比例: {{ (trading_rules.stop_loss_ratio * 100) | round(1) }}%
- 止盈比例: {{ (trading_rules.take_profit_ratio * 100) | round(1) }}%
- 单笔最大亏损: {{ (trading_rules.max_single_loss * 100) | round(1) }}%
- 每日最大交易次数: {{ trading_rules.max_daily_trades }}

## 历史决策回顾
{% if historical_decisions %}
最近{{ historical_decisions | length }}次决策:
{% for decision in historical_decisions[-5:] %}
- {{ decision.timestamp }}: {{ decision.action }} ({{ decision.reason }})
{% endfor %}
{% else %}
暂无历史决策记录
{% endif %}

## 投资组合状态
{% if portfolio_status %}
- 总资产: {{ portfolio_status.total_assets }}
- 可用资金: {{ portfolio_status.available_cash }}
- 持仓市值: {{ portfolio_status.position_value }}
- 当前仓位: {{ (portfolio_status.position_ratio * 100) | round(1) }}%
- 今日盈亏: {{ portfolio_status.daily_pnl }}
{% else %}
投资组合状态不可用
{% endif %}

## 决策要求

请基于以上信息，进行综合分析并给出交易决策建议。

### 分析要点：
1. 技术面分析：基于技术指标判断趋势和买卖点
2. 市场环境：考虑整体市场情况和板块轮动
3. 风险控制：严格遵守交易规则和风险偏好
4. 资金管理：合理配置仓位和资金使用

### 输出格式：
请严格按照以下JSON格式输出决策结果：

```json
{
    "action": "buy/sell/hold",
    "confidence": 0.85,
    "target_price": 100.50,
    "stop_loss": 95.00,
    "take_profit": 110.00,
    "position_size": 0.20,
    "reasoning": {
        "technical_analysis": "技术面分析要点",
        "market_environment": "市场环境分析",
        "risk_assessment": "风险评估",
        "key_factors": ["关键因素1", "关键因素2"]
    },
    "risk_level": "medium",
    "expected_return": 0.08,
    "holding_period": "1-3天",
    "alternative_scenarios": {
        "bullish": "看涨情况下的策略",
        "bearish": "看跌情况下的策略"
    }
}
```

请确保决策符合风险控制要求，并提供详细的分析理由。
""")
        
        # 风险评估模板
        templates['risk_assessment'] = self.env.from_string("""
# 风险评估报告

## 股票: {{ symbol }}
## 评估时间: {{ current_time }}

### 市场风险
- 整体市场风险水平: {{ market_environment.risk_level if market_environment else 'N/A' }}
- 市场波动率: {{ market_environment.market_volatility if market_environment else 'N/A' }}
- 流动性风险: {{ 'low' if market_environment and market_environment.liquidity_index > 0.8 else 'medium' if market_environment and market_environment.liquidity_index > 0.5 else 'high' }}

### 技术风险
{% if technical_indicators %}
- RSI超买超卖: {{ 'overbought' if technical_indicators.momentum and technical_indicators.momentum.rsi > 70 else 'oversold' if technical_indicators.momentum and technical_indicators.momentum.rsi < 30 else 'normal' }}
- 布林带位置: {{ 'upper' if technical_indicators.bollinger and technical_indicators.bollinger.position > 0.8 else 'lower' if technical_indicators.bollinger and technical_indicators.bollinger.position < 0.2 else 'middle' }}
- 波动率水平: {{ 'high' if technical_indicators.volatility and technical_indicators.volatility.atr > 5 else 'medium' if technical_indicators.volatility and technical_indicators.volatility.atr > 2 else 'low' }}
{% endif %}

### 资金风险
{% if portfolio_status %}
- 当前仓位风险: {{ 'high' if portfolio_status.position_ratio > 0.8 else 'medium' if portfolio_status.position_ratio > 0.5 else 'low' }}
- 资金利用率: {{ (portfolio_status.position_ratio * 100) | round(1) }}%
{% endif %}

### 风险建议
基于{{ risk_preference }}风险偏好，建议采取相应的风险控制措施。
""")
        
        return templates
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """渲染模板"""
        if template_name not in self.templates:
            raise ValueError(f"模板 {template_name} 不存在")
        
        template = self.templates[template_name]
        return template.render(**context)

class PromptGenerator:
    """Prompt生成器"""
    
    def __init__(self):
        self.template = PromptTemplate()
        self.context_builders = {
            'market': self._build_market_context,
            'technical': self._build_technical_context,
            'risk': self._build_risk_context,
            'portfolio': self._build_portfolio_context
        }
    
    @monitor_performance
    def generate_decision_prompt(self, context: PromptContext) -> str:
        """生成决策Prompt"""
        try:
            # 构建模板上下文
            template_context = {
                'symbol': context.symbol,
                'current_time': context.market_context.current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'trading_session': context.market_context.trading_session,
                'market_phase': context.market_context.market_phase,
                'realtime_quote': context.aggregated_data.realtime_quote,
                'technical_indicators': context.aggregated_data.technical_indicators,
                'market_environment': context.aggregated_data.market_environment,
                'risk_preference': context.risk_preference.value,
                'trading_rules': context.trading_rules,
                'historical_decisions': context.historical_decisions,
                'portfolio_status': context.portfolio_status
            }
            
            # 渲染主决策模板
            prompt = self.template.render('main_decision', template_context)
            
            logger.info(f"生成决策Prompt成功: {context.symbol}")
            return prompt
            
        except Exception as e:
            logger.error(f"生成决策Prompt失败: {str(e)}")
            raise
    
    @monitor_performance
    def generate_risk_assessment_prompt(self, context: PromptContext) -> str:
        """生成风险评估Prompt"""
        try:
            template_context = {
                'symbol': context.symbol,
                'current_time': context.market_context.current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'technical_indicators': context.aggregated_data.technical_indicators,
                'market_environment': context.aggregated_data.market_environment,
                'risk_preference': context.risk_preference.value,
                'portfolio_status': context.portfolio_status
            }
            
            prompt = self.template.render('risk_assessment', template_context)
            
            logger.info(f"生成风险评估Prompt成功: {context.symbol}")
            return prompt
            
        except Exception as e:
            logger.error(f"生成风险评估Prompt失败: {str(e)}")
            raise
    
    def _build_market_context(self, aggregated_data: AggregatedData) -> MarketContext:
        """构建市场上下文"""
        current_time = datetime.now()
        
        # 判断交易时段
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        if 9 <= current_hour < 11 or (current_hour == 11 and current_minute <= 30):
            trading_session = 'morning'
        elif 13 <= current_hour < 15:
            trading_session = 'afternoon'
        else:
            trading_session = 'closed'
        
        # 判断市场阶段
        if trading_session != 'closed':
            if (current_hour == 9 and current_minute < 45) or (current_hour == 13 and current_minute < 15):
                market_phase = 'opening'
            elif (current_hour == 11 and current_minute > 15) or (current_hour == 14 and current_minute > 45):
                market_phase = 'closing'
            else:
                market_phase = 'continuous'
        else:
            market_phase = 'closed'
        
        # 判断波动率水平
        volatility_level = 'medium'
        if aggregated_data.market_environment:
            vol = aggregated_data.market_environment.market_volatility
            if vol > 0.3:
                volatility_level = 'high'
            elif vol < 0.15:
                volatility_level = 'low'
        
        # 判断流动性水平
        liquidity_level = 'medium'
        if aggregated_data.market_environment:
            liq = aggregated_data.market_environment.liquidity_index
            if liq > 0.8:
                liquidity_level = 'high'
            elif liq < 0.5:
                liquidity_level = 'low'
        
        return MarketContext(
            current_time=current_time,
            trading_session=trading_session,
            market_phase=market_phase,
            volatility_level=volatility_level,
            liquidity_level=liquidity_level
        )
    
    def _build_technical_context(self, aggregated_data: AggregatedData) -> Dict[str, Any]:
        """构建技术分析上下文"""
        context = {}
        
        if aggregated_data.technical_indicators:
            indicators = aggregated_data.technical_indicators
            
            # 趋势判断
            trend_signals = []
            if 'trend' in indicators:
                trend = indicators['trend']
                if 'sma_20' in trend and 'sma_60' in trend:
                    if trend['sma_20'] > trend['sma_60']:
                        trend_signals.append('short_term_bullish')
                    else:
                        trend_signals.append('short_term_bearish')
            
            # MACD信号
            macd_signals = []
            if 'macd' in indicators:
                macd = indicators['macd']
                if 'macd_line' in macd and 'signal_line' in macd:
                    if macd['macd_line'] > macd['signal_line']:
                        macd_signals.append('bullish_crossover')
                    else:
                        macd_signals.append('bearish_crossover')
            
            # RSI信号
            rsi_signals = []
            if 'momentum' in indicators and 'rsi' in indicators['momentum']:
                rsi = indicators['momentum']['rsi']
                if rsi > 70:
                    rsi_signals.append('overbought')
                elif rsi < 30:
                    rsi_signals.append('oversold')
                else:
                    rsi_signals.append('neutral')
            
            context = {
                'trend_signals': trend_signals,
                'macd_signals': macd_signals,
                'rsi_signals': rsi_signals
            }
        
        return context
    
    def _build_risk_context(self, market_environment: MarketEnvironment, risk_preference: RiskPreference) -> Dict[str, Any]:
        """构建风险上下文"""
        context = {
            'risk_preference': risk_preference.value,
            'market_risk_level': 'medium'
        }
        
        if market_environment:
            context['market_risk_level'] = market_environment.risk_level
            context['market_volatility'] = market_environment.market_volatility
            context['market_sentiment'] = market_environment.market_sentiment
        
        return context
    
    def _build_portfolio_context(self, portfolio_status: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """构建投资组合上下文"""
        if not portfolio_status:
            return {'has_portfolio_data': False}
        
        return {
            'has_portfolio_data': True,
            'position_ratio': portfolio_status.get('position_ratio', 0),
            'available_cash_ratio': portfolio_status.get('available_cash_ratio', 1),
            'daily_pnl': portfolio_status.get('daily_pnl', 0)
        }
    
    def create_context(self, 
                      symbol: str,
                      aggregated_data: AggregatedData,
                      risk_preference: RiskPreference = RiskPreference.MODERATE,
                      trading_rules: Optional[TradingRules] = None,
                      historical_decisions: Optional[List[Dict[str, Any]]] = None,
                      portfolio_status: Optional[Dict[str, Any]] = None) -> PromptContext:
        """创建Prompt上下文"""
        
        if trading_rules is None:
            trading_rules = TradingRules()
        
        if historical_decisions is None:
            historical_decisions = []
        
        market_context = self._build_market_context(aggregated_data)
        
        return PromptContext(
            symbol=symbol,
            aggregated_data=aggregated_data,
            market_context=market_context,
            risk_preference=risk_preference,
            trading_rules=trading_rules,
            historical_decisions=historical_decisions,
            portfolio_status=portfolio_status
        )
    
    def get_prompt_templates(self) -> List[str]:
        """获取可用的Prompt模板列表"""
        return list(self.template.templates.keys())
    
    def validate_prompt_context(self, context: PromptContext) -> Dict[str, Any]:
        """验证Prompt上下文的完整性"""
        validation_result = {
            'is_valid': True,
            'missing_fields': [],
            'warnings': []
        }
        
        # 检查必需字段
        if not context.symbol:
            validation_result['missing_fields'].append('symbol')
        
        if not context.aggregated_data:
            validation_result['missing_fields'].append('aggregated_data')
        
        if not context.market_context:
            validation_result['missing_fields'].append('market_context')
        
        # 检查数据质量
        if context.aggregated_data:
            if not context.aggregated_data.realtime_quote:
                validation_result['warnings'].append('missing_realtime_quote')
            
            if not context.aggregated_data.technical_indicators:
                validation_result['warnings'].append('missing_technical_indicators')
            
            if not context.aggregated_data.market_environment:
                validation_result['warnings'].append('missing_market_environment')
        
        validation_result['is_valid'] = len(validation_result['missing_fields']) == 0
        
        return validation_result

# 全局Prompt生成器实例
global_prompt_generator = PromptGenerator()

# 导出主要接口
__all__ = [
    'PromptGenerator',
    'PromptContext',
    'PromptTemplate',
    'MarketContext',
    'TradingRules',
    'RiskPreference',
    'TradingAction',
    'global_prompt_generator'
]