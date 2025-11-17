"""
置信度评估模块
负责评估交易决策的置信度，包括逻辑合理性、市场环境匹配度和风险收益评估
"""
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json

from app.models.ai_decision_models import (
    TradingDecision, 
    ConfidenceAssessment,
    TradingAction
)
from app.services.llm_gateway import LLMGateway, GatewayRequest

logger = logging.getLogger(__name__)

@dataclass
class MarketCondition:
    """市场条件数据结构"""
    volatility: float  # 波动率
    trend: str  # 趋势方向: "up", "down", "sideways"
    volume: float  # 成交量
    sentiment: str  # 市场情绪: "bullish", "bearish", "neutral"
    support_level: Optional[float] = None  # 支撑位
    resistance_level: Optional[float] = None  # 阻力位

@dataclass
class RiskMetrics:
    """风险指标数据结构"""
    var_95: float  # 95% VaR
    max_drawdown: float  # 最大回撤
    sharpe_ratio: float  # 夏普比率
    beta: float  # 贝塔系数
    correlation: float  # 与市场相关性

class ConfidenceAssessor:
    """置信度评估器"""
    
    def __init__(self, llm_gateway: LLMGateway):
        self.llm_gateway = llm_gateway
        
        # 评估权重配置
        self.weights = {
            'logic_score': 0.3,
            'market_match_score': 0.3,
            'risk_reward_score': 0.25,
            'historical_accuracy': 0.15
        }
        
        # 风险阈值配置
        self.risk_thresholds = {
            'high_volatility': 0.3,
            'max_position_size': 0.1,  # 最大仓位比例
            'max_drawdown': 0.15,
            'min_sharpe_ratio': 0.5
        }
        
        # 市场条件评分标准
        self.market_scoring = {
            'volatility': {
                'low': (0, 0.15, 0.8),      # (min, max, score)
                'medium': (0.15, 0.3, 0.6),
                'high': (0.3, 1.0, 0.3)
            },
            'trend_alignment': {
                'aligned': 0.9,
                'neutral': 0.5,
                'opposite': 0.2
            }
        }

    async def assess_confidence(
        self, 
        decision: TradingDecision, 
        market_data: Dict[str, Any],
        historical_performance: Optional[Dict[str, float]] = None,
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> ConfidenceAssessment:
        """
        评估交易决策的置信度
        
        Args:
            decision: 交易决策
            market_data: 市场数据
            historical_performance: 历史表现数据
            portfolio_context: 投资组合上下文
            
        Returns:
            ConfidenceAssessment: 置信度评估结果
        """
        try:
            logger.info(f"开始评估决策置信度: {decision.symbol} {decision.action}")
            
            # 1. 决策逻辑合理性分析
            logic_score = await self._assess_logic_rationality(decision, market_data)
            
            # 2. 市场环境匹配度评估
            market_match_score = self._assess_market_match(decision, market_data)
            
            # 3. 风险收益评估
            risk_reward_score = self._assess_risk_reward(decision, market_data, portfolio_context)
            
            # 4. 历史准确率
            historical_accuracy = self._get_historical_accuracy(
                decision.model_id, historical_performance
            )
            
            # 5. 计算总体置信度
            overall_confidence = self._calculate_overall_confidence(
                logic_score, market_match_score, risk_reward_score, historical_accuracy
            )
            
            # 6. 提取市场条件和风险因素
            market_conditions = self._extract_market_conditions(market_data)
            risk_factors = self._identify_risk_factors(decision, market_data, portfolio_context)
            
            return ConfidenceAssessment(
                overall_confidence=overall_confidence,
                logic_score=logic_score,
                market_match_score=market_match_score,
                risk_reward_score=risk_reward_score,
                historical_accuracy=historical_accuracy,
                market_conditions=market_conditions,
                risk_factors=risk_factors,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"置信度评估失败: {e}")
            return ConfidenceAssessment(
                overall_confidence=0.0,
                logic_score=0.0,
                market_match_score=0.0,
                risk_reward_score=0.0,
                historical_accuracy=0.0,
                market_conditions={},
                risk_factors=[f"评估错误: {str(e)}"],
                timestamp=datetime.now()
            )

    async def _assess_logic_rationality(self, decision: TradingDecision, market_data: Dict[str, Any]) -> float:
        """评估决策逻辑合理性"""
        try:
            # 构建逻辑评估提示词
            prompt = self._build_logic_assessment_prompt(decision, market_data)
            
            response = await self.llm_gateway.generate(
                GatewayRequest(
                    messages=[{"role": "user", "content": prompt}],
                    model="deepseek",
                    temperature=0.1
                )
            )
            
            if response.success:
                # 解析LLM评估结果
                logic_score = self._parse_logic_score(response.content)
                
                # 结合规则检查
                rule_score = self._rule_based_logic_check(decision, market_data)
                
                # 加权平均
                return 0.7 * logic_score + 0.3 * rule_score
            
            # 如果LLM失败，仅使用规则检查
            return self._rule_based_logic_check(decision, market_data)
            
        except Exception as e:
            logger.error(f"逻辑合理性评估失败: {e}")
            return 0.5  # 默认中等评分

    def _build_logic_assessment_prompt(self, decision: TradingDecision, market_data: Dict[str, Any]) -> str:
        """构建逻辑评估提示词"""
        market_info = json.dumps(market_data, ensure_ascii=False, indent=2)
        
        prompt = f"""
请评估以下交易决策的逻辑合理性（0-1分）：

交易决策：
- 动作: {decision.action.value}
- 股票: {decision.symbol}
- 数量: {decision.quantity}
- 价格: {decision.price}
- 理由: {decision.reasoning}

市场数据：
{market_info}

请从以下角度评估：
1. 决策理由是否充分
2. 是否符合技术分析原理
3. 是否考虑了基本面因素
4. 时机选择是否合适
5. 风险控制是否到位

请返回0-1之间的评分，并简要说明理由。
格式：评分: 0.XX 理由: ...
"""
        return prompt

    def _parse_logic_score(self, response: str) -> float:
        """解析LLM逻辑评分"""
        try:
            import re
            # 查找评分模式
            score_match = re.search(r'评分[:：]\s*([0-1]\.?\d*)', response)
            if score_match:
                return float(score_match.group(1))
            
            # 查找数字模式
            number_match = re.search(r'([0-1]\.?\d*)', response)
            if number_match:
                score = float(number_match.group(1))
                return min(1.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"解析逻辑评分失败: {e}")
        
        return 0.5  # 默认评分

    def _rule_based_logic_check(self, decision: TradingDecision, market_data: Dict[str, Any]) -> float:
        """基于规则的逻辑检查"""
        score = 0.5  # 基础分
        
        try:
            current_price = market_data.get('current_price', 0)
            
            # 检查价格合理性
            if decision.price and current_price:
                price_diff = abs(decision.price - current_price) / current_price
                if price_diff < 0.05:  # 价格差异小于5%
                    score += 0.2
                elif price_diff > 0.2:  # 价格差异大于20%
                    score -= 0.2
            
            # 检查数量合理性
            if decision.quantity:
                daily_volume = market_data.get('volume', 0)
                if daily_volume > 0:
                    volume_ratio = decision.quantity / daily_volume
                    if volume_ratio < 0.01:  # 小于日成交量1%
                        score += 0.1
                    elif volume_ratio > 0.1:  # 大于日成交量10%
                        score -= 0.2
            
            # 检查趋势一致性
            trend = market_data.get('trend', 'neutral')
            if (decision.action == TradingAction.BUY and trend == 'up') or \
               (decision.action == TradingAction.SELL and trend == 'down'):
                score += 0.2
            elif (decision.action == TradingAction.BUY and trend == 'down') or \
                 (decision.action == TradingAction.SELL and trend == 'up'):
                score -= 0.2
            
            # 检查波动率
            volatility = market_data.get('volatility', 0)
            if volatility > self.risk_thresholds['high_volatility']:
                if decision.action == TradingAction.HOLD:
                    score += 0.1  # 高波动时持有是谨慎的
                else:
                    score -= 0.1  # 高波动时交易风险较大
            
        except Exception as e:
            logger.error(f"规则逻辑检查失败: {e}")
        
        return max(0.0, min(1.0, score))

    def _assess_market_match(self, decision: TradingDecision, market_data: Dict[str, Any]) -> float:
        """评估市场环境匹配度"""
        try:
            score = 0.0
            
            # 1. 波动率匹配度
            volatility = market_data.get('volatility', 0)
            volatility_score = self._score_volatility_match(decision, volatility)
            score += volatility_score * 0.3
            
            # 2. 趋势匹配度
            trend = market_data.get('trend', 'neutral')
            trend_score = self._score_trend_match(decision, trend)
            score += trend_score * 0.4
            
            # 3. 成交量匹配度
            volume = market_data.get('volume', 0)
            avg_volume = market_data.get('avg_volume', volume)
            volume_score = self._score_volume_match(decision, volume, avg_volume)
            score += volume_score * 0.2
            
            # 4. 技术指标匹配度
            technical_score = self._score_technical_match(decision, market_data)
            score += technical_score * 0.1
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"市场匹配度评估失败: {e}")
            return 0.5

    def _score_volatility_match(self, decision: TradingDecision, volatility: float) -> float:
        """评估波动率匹配度"""
        if volatility <= 0.15:  # 低波动
            if decision.action == TradingAction.HOLD:
                return 0.6  # 低波动时持有较合适
            else:
                return 0.8  # 低波动时交易风险较小
        elif volatility <= 0.3:  # 中等波动
            return 0.7  # 中等波动适合各种操作
        else:  # 高波动
            if decision.action == TradingAction.HOLD:
                return 0.8  # 高波动时持有较安全
            else:
                return 0.4  # 高波动时交易风险较大

    def _score_trend_match(self, decision: TradingDecision, trend: str) -> float:
        """评估趋势匹配度"""
        if trend == 'up':
            if decision.action == TradingAction.BUY:
                return 0.9  # 上涨趋势买入
            elif decision.action == TradingAction.SELL:
                return 0.3  # 上涨趋势卖出
            else:
                return 0.6  # 上涨趋势持有
        elif trend == 'down':
            if decision.action == TradingAction.SELL:
                return 0.9  # 下跌趋势卖出
            elif decision.action == TradingAction.BUY:
                return 0.3  # 下跌趋势买入
            else:
                return 0.7  # 下跌趋势持有
        else:  # sideways
            if decision.action == TradingAction.HOLD:
                return 0.8  # 横盘时持有
            else:
                return 0.5  # 横盘时交易

    def _score_volume_match(self, decision: TradingDecision, volume: float, avg_volume: float) -> float:
        """评估成交量匹配度"""
        if avg_volume <= 0:
            return 0.5
        
        volume_ratio = volume / avg_volume
        
        if volume_ratio > 1.5:  # 放量
            if decision.action != TradingAction.HOLD:
                return 0.8  # 放量时交易较好
            else:
                return 0.4  # 放量时持有可能错失机会
        elif volume_ratio < 0.5:  # 缩量
            if decision.action == TradingAction.HOLD:
                return 0.7  # 缩量时持有较好
            else:
                return 0.4  # 缩量时交易流动性差
        else:  # 正常量
            return 0.6

    def _score_technical_match(self, decision: TradingDecision, market_data: Dict[str, Any]) -> float:
        """评估技术指标匹配度"""
        score = 0.5
        
        try:
            # RSI指标
            rsi = market_data.get('rsi', 50)
            if rsi > 70:  # 超买
                if decision.action == TradingAction.SELL:
                    score += 0.3
                elif decision.action == TradingAction.BUY:
                    score -= 0.2
            elif rsi < 30:  # 超卖
                if decision.action == TradingAction.BUY:
                    score += 0.3
                elif decision.action == TradingAction.SELL:
                    score -= 0.2
            
            # MACD指标
            macd = market_data.get('macd', 0)
            if macd > 0:  # 金叉
                if decision.action == TradingAction.BUY:
                    score += 0.2
            elif macd < 0:  # 死叉
                if decision.action == TradingAction.SELL:
                    score += 0.2
            
        except Exception as e:
            logger.error(f"技术指标匹配度评估失败: {e}")
        
        return max(0.0, min(1.0, score))

    def _assess_risk_reward(
        self, 
        decision: TradingDecision, 
        market_data: Dict[str, Any],
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """评估风险收益比"""
        try:
            # 1. 计算预期收益
            expected_return = self._calculate_expected_return(decision, market_data)
            
            # 2. 计算风险指标
            risk_metrics = self._calculate_risk_metrics(decision, market_data, portfolio_context)
            
            # 3. 计算风险收益比
            if risk_metrics.var_95 > 0:
                risk_reward_ratio = expected_return / risk_metrics.var_95
            else:
                risk_reward_ratio = 0
            
            # 4. 评分标准
            if risk_reward_ratio > 2.0:
                return 0.9
            elif risk_reward_ratio > 1.5:
                return 0.8
            elif risk_reward_ratio > 1.0:
                return 0.7
            elif risk_reward_ratio > 0.5:
                return 0.5
            else:
                return 0.3
                
        except Exception as e:
            logger.error(f"风险收益评估失败: {e}")
            return 0.5

    def _calculate_expected_return(self, decision: TradingDecision, market_data: Dict[str, Any]) -> float:
        """计算预期收益"""
        try:
            current_price = market_data.get('current_price', 0)
            if not current_price or not decision.price:
                return 0.0
            
            if decision.action == TradingAction.BUY:
                # 买入的预期收益基于目标价格
                target_price = decision.take_profit or current_price * 1.1
                return (target_price - decision.price) / decision.price
            elif decision.action == TradingAction.SELL:
                # 卖出的预期收益基于避免损失
                stop_loss = decision.stop_loss or current_price * 0.9
                return (decision.price - stop_loss) / decision.price
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"预期收益计算失败: {e}")
            return 0.0

    def _calculate_risk_metrics(
        self, 
        decision: TradingDecision, 
        market_data: Dict[str, Any],
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> RiskMetrics:
        """计算风险指标"""
        try:
            volatility = market_data.get('volatility', 0.2)
            current_price = market_data.get('current_price', 0)
            
            # VaR计算（简化版）
            if decision.price and decision.quantity:
                position_value = decision.price * decision.quantity
                var_95 = position_value * volatility * 1.645  # 95% VaR
            else:
                var_95 = 0
            
            # 最大回撤估算
            max_drawdown = volatility * 2  # 简化估算
            
            # 夏普比率估算
            risk_free_rate = 0.03  # 假设无风险利率3%
            expected_return = self._calculate_expected_return(decision, market_data)
            if volatility > 0:
                sharpe_ratio = (expected_return - risk_free_rate) / volatility
            else:
                sharpe_ratio = 0
            
            # 贝塔系数（简化）
            beta = market_data.get('beta', 1.0)
            
            # 相关性
            correlation = market_data.get('correlation', 0.7)
            
            return RiskMetrics(
                var_95=var_95,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                beta=beta,
                correlation=correlation
            )
            
        except Exception as e:
            logger.error(f"风险指标计算失败: {e}")
            return RiskMetrics(0, 0, 0, 1.0, 0.5)

    def _get_historical_accuracy(
        self, 
        model_id: str, 
        historical_performance: Optional[Dict[str, float]] = None
    ) -> Optional[float]:
        """获取历史准确率"""
        if not historical_performance:
            return None
        
        return historical_performance.get(model_id, 0.5)

    def _calculate_overall_confidence(
        self, 
        logic_score: float, 
        market_match_score: float, 
        risk_reward_score: float, 
        historical_accuracy: Optional[float]
    ) -> float:
        """计算总体置信度"""
        # 如果没有历史准确率，调整权重
        if historical_accuracy is None:
            weights = {
                'logic_score': 0.35,
                'market_match_score': 0.35,
                'risk_reward_score': 0.3
            }
            confidence = (
                logic_score * weights['logic_score'] +
                market_match_score * weights['market_match_score'] +
                risk_reward_score * weights['risk_reward_score']
            )
        else:
            confidence = (
                logic_score * self.weights['logic_score'] +
                market_match_score * self.weights['market_match_score'] +
                risk_reward_score * self.weights['risk_reward_score'] +
                historical_accuracy * self.weights['historical_accuracy']
            )
        
        return max(0.0, min(1.0, confidence))

    def _extract_market_conditions(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取市场条件"""
        return {
            'volatility': market_data.get('volatility', 0),
            'trend': market_data.get('trend', 'neutral'),
            'volume': market_data.get('volume', 0),
            'rsi': market_data.get('rsi', 50),
            'macd': market_data.get('macd', 0),
            'current_price': market_data.get('current_price', 0),
            'support_level': market_data.get('support_level'),
            'resistance_level': market_data.get('resistance_level')
        }

    def _identify_risk_factors(
        self, 
        decision: TradingDecision, 
        market_data: Dict[str, Any],
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """识别风险因素"""
        risk_factors = []
        
        try:
            # 高波动率风险
            volatility = market_data.get('volatility', 0)
            if volatility > self.risk_thresholds['high_volatility']:
                risk_factors.append(f"高波动率风险: {volatility:.2%}")
            
            # 流动性风险
            volume = market_data.get('volume', 0)
            avg_volume = market_data.get('avg_volume', volume)
            if volume < avg_volume * 0.5:
                risk_factors.append("流动性不足风险")
            
            # 趋势逆转风险
            trend = market_data.get('trend', 'neutral')
            if (decision.action == TradingAction.BUY and trend == 'down') or \
               (decision.action == TradingAction.SELL and trend == 'up'):
                risk_factors.append("趋势逆转风险")
            
            # 技术指标风险
            rsi = market_data.get('rsi', 50)
            if rsi > 80:
                risk_factors.append("技术指标超买风险")
            elif rsi < 20:
                risk_factors.append("技术指标超卖风险")
            
            # 仓位集中度风险
            if portfolio_context:
                total_value = portfolio_context.get('total_value', 0)
                if decision.price and decision.quantity and total_value > 0:
                    position_ratio = (decision.price * decision.quantity) / total_value
                    if position_ratio > self.risk_thresholds['max_position_size']:
                        risk_factors.append(f"仓位过度集中风险: {position_ratio:.1%}")
            
            # 价格偏离风险
            current_price = market_data.get('current_price', 0)
            if decision.price and current_price:
                price_deviation = abs(decision.price - current_price) / current_price
                if price_deviation > 0.1:
                    risk_factors.append(f"价格偏离风险: {price_deviation:.1%}")
            
        except Exception as e:
            logger.error(f"风险因素识别失败: {e}")
            risk_factors.append(f"风险评估错误: {str(e)}")
        
        return risk_factors

    async def batch_assess_confidence(
        self, 
        decisions: List[TradingDecision],
        market_data_batch: List[Dict[str, Any]],
        historical_performance: Optional[Dict[str, float]] = None,
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> List[ConfidenceAssessment]:
        """批量评估置信度"""
        tasks = []
        for decision, market_data in zip(decisions, market_data_batch):
            task = self.assess_confidence(
                decision, market_data, historical_performance, portfolio_context
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)