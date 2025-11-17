"""
AI决策执行引擎
整合自然语言解析、置信度评估、多模型融合和指令生成等模块，提供统一的决策执行接口
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import uuid

from app.models.ai_decision_models import (
    TradingDecision, 
    InstructionParseResult,
    ConfidenceAssessment,
    ModelVote,
    ModelFusionResult,
    TradingAction
)
from app.services.instruction_parser import InstructionParser
from app.services.confidence_assessor import ConfidenceAssessor
from app.services.model_fusion import ModelFusion
from app.services.instruction_generator import InstructionGenerator, ExecutionPlan
from app.services.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)

class AIDecisionEngine:
    """AI决策执行引擎主控制器"""
    
    def __init__(self, llm_gateway: LLMGateway):
        self.llm_gateway = llm_gateway
        
        # 初始化各个模块
        self.instruction_parser = InstructionParser(llm_gateway)
        self.confidence_assessor = ConfidenceAssessor(llm_gateway)
        self.model_fusion = ModelFusion(llm_gateway)
        self.instruction_generator = InstructionGenerator(llm_gateway)
        
        # 决策历史记录
        self.decision_history: List[Dict[str, Any]] = []
        
        # 性能统计
        self.performance_stats = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'average_confidence': 0.0,
            'average_processing_time': 0.0
        }

    async def process_natural_language_instruction(
        self,
        instruction: str,
        context: Optional[Dict[str, Any]] = None
    ) -> InstructionParseResult:
        """
        处理自然语言指令
        
        Args:
            instruction: 自然语言指令
            context: 上下文信息
            
        Returns:
            InstructionParseResult: 解析结果
        """
        try:
            logger.info(f"处理自然语言指令: {instruction}")
            
            # 使用指令解析器处理
            parse_result = await self.instruction_parser.parse_instruction(instruction, context)
            
            logger.info(f"指令解析完成，置信度: {parse_result.confidence:.2f}")
            return parse_result
            
        except Exception as e:
            logger.error(f"自然语言指令处理失败: {e}")
            raise

    async def make_single_model_decision(
        self,
        instruction: str,
        model_id: str,
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> TradingDecision:
        """
        使用单个模型做出决策
        
        Args:
            instruction: 交易指令
            model_id: 模型ID
            market_data: 市场数据
            context: 上下文信息
            
        Returns:
            TradingDecision: 交易决策
        """
        try:
            logger.info(f"使用模型 {model_id} 做出决策")
            
            # 1. 解析指令
            parse_result = await self.process_natural_language_instruction(instruction, context)
            
            if not parse_result.standardized_instructions:
                raise ValueError("指令解析失败，无法生成标准化指令")
            
            # 2. 使用LLM生成决策
            decision = await self._generate_llm_decision(
                parse_result.standardized_instructions[0], 
                model_id, 
                market_data, 
                context
            )
            
            # 3. 评估置信度
            confidence_assessment = await self.confidence_assessor.assess_confidence(
                decision, market_data, context.get('historical_performance') if context else None
            )
            
            # 更新决策置信度
            decision.confidence = confidence_assessment.overall_confidence
            
            logger.info(f"单模型决策完成: {decision.action} {decision.symbol}, 置信度: {decision.confidence:.2f}")
            return decision
            
        except Exception as e:
            logger.error(f"单模型决策失败: {e}")
            raise

    async def make_multi_model_decision(
        self,
        instruction: str,
        model_ids: List[str],
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        fusion_strategy: str = 'weighted_voting'
    ) -> ModelFusionResult:
        """
        使用多个模型融合决策
        
        Args:
            instruction: 交易指令
            model_ids: 模型ID列表
            market_data: 市场数据
            context: 上下文信息
            fusion_strategy: 融合策略
            
        Returns:
            ModelFusionResult: 融合决策结果
        """
        try:
            logger.info(f"使用 {len(model_ids)} 个模型进行融合决策")
            
            # 1. 解析指令
            parse_result = await self.process_natural_language_instruction(instruction, context)
            
            if not parse_result.standardized_instructions:
                raise ValueError("指令解析失败，无法生成标准化指令")
            
            # 2. 并行获取各模型决策
            model_decisions = await self._get_multi_model_decisions(
                parse_result.standardized_instructions[0],
                model_ids,
                market_data,
                context
            )
            
            # 3. 创建模型投票
            model_votes = []
            for model_id, decision in model_decisions.items():
                # 评估每个决策的置信度
                confidence_assessment = await self.confidence_assessor.assess_confidence(
                    decision, market_data, context.get('historical_performance') if context else None
                )
                
                model_vote = ModelVote(
                    model_id=model_id,
                    decision=decision,
                    confidence=confidence_assessment.overall_confidence,
                    reasoning=decision.reasoning,
                    timestamp=datetime.now()
                )
                model_votes.append(model_vote)
            
            # 4. 融合决策
            fusion_result = await self.model_fusion.fuse_decisions(
                model_votes, fusion_strategy, market_data
            )
            
            logger.info(f"多模型融合决策完成: {fusion_result.fused_decision.action} "
                       f"{fusion_result.fused_decision.symbol}, "
                       f"融合置信度: {fusion_result.fusion_confidence:.2f}")
            
            return fusion_result
            
        except Exception as e:
            logger.error(f"多模型融合决策失败: {e}")
            raise

    async def generate_execution_plan(
        self,
        decision: Union[TradingDecision, ModelFusionResult],
        portfolio_context: Dict[str, Any],
        market_data: Dict[str, Any],
        risk_parameters: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        生成执行计划
        
        Args:
            decision: 交易决策或融合结果
            portfolio_context: 投资组合上下文
            market_data: 市场数据
            risk_parameters: 风险参数
            
        Returns:
            ExecutionPlan: 执行计划
        """
        try:
            # 提取决策对象
            if isinstance(decision, ModelFusionResult):
                trading_decision = decision.fused_decision
            else:
                trading_decision = decision
            
            logger.info(f"生成执行计划: {trading_decision.symbol} {trading_decision.action}")
            
            # 使用指令生成器创建执行计划
            execution_plan = await self.instruction_generator.generate_instruction(
                trading_decision, portfolio_context, market_data, risk_parameters
            )
            
            logger.info(f"执行计划生成完成，预期成本: {execution_plan.expected_cost:.2f}")
            return execution_plan
            
        except Exception as e:
            logger.error(f"执行计划生成失败: {e}")
            raise

    async def execute_complete_workflow(
        self,
        instruction: str,
        model_ids: List[str],
        market_data: Dict[str, Any],
        portfolio_context: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        fusion_strategy: str = 'weighted_voting',
        risk_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行完整的决策工作流
        
        Args:
            instruction: 自然语言指令
            model_ids: 模型ID列表
            market_data: 市场数据
            portfolio_context: 投资组合上下文
            context: 上下文信息
            fusion_strategy: 融合策略
            risk_parameters: 风险参数
            
        Returns:
            Dict: 完整的决策执行结果
        """
        start_time = datetime.now()
        workflow_id = str(uuid.uuid4())
        
        try:
            logger.info(f"开始执行完整决策工作流 {workflow_id}")
            
            # 1. 自然语言解析
            parse_result = await self.process_natural_language_instruction(instruction, context)
            
            # 2. 多模型决策融合
            if len(model_ids) > 1:
                fusion_result = await self.make_multi_model_decision(
                    instruction, model_ids, market_data, context, fusion_strategy
                )
                decision = fusion_result
            else:
                single_decision = await self.make_single_model_decision(
                    instruction, model_ids[0], market_data, context
                )
                decision = single_decision
            
            # 3. 生成执行计划
            execution_plan = await self.generate_execution_plan(
                decision, portfolio_context, market_data, risk_parameters
            )
            
            # 4. 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 5. 构建完整结果
            result = {
                'workflow_id': workflow_id,
                'instruction': instruction,
                'parse_result': parse_result.__dict__,
                'decision': decision.fused_decision.__dict__ if isinstance(decision, ModelFusionResult) else decision.__dict__,
                'fusion_result': decision.__dict__ if isinstance(decision, ModelFusionResult) else None,
                'execution_plan': {
                    'primary_order': execution_plan.primary_order.__dict__,
                    'contingent_orders': [order.__dict__ for order in execution_plan.contingent_orders],
                    'execution_timeline': [(dt.isoformat(), desc) for dt, desc in execution_plan.execution_timeline],
                    'expected_cost': execution_plan.expected_cost,
                    'expected_slippage': execution_plan.expected_slippage
                },
                'processing_time': processing_time,
                'timestamp': start_time.isoformat(),
                'success': True
            }
            
            # 6. 更新统计信息
            self._update_performance_stats(True, processing_time, 
                                         decision.fusion_confidence if isinstance(decision, ModelFusionResult) else decision.confidence)
            
            # 7. 记录决策历史
            self.decision_history.append(result)
            
            logger.info(f"完整决策工作流执行成功 {workflow_id}, 耗时: {processing_time:.2f}秒")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"完整决策工作流执行失败 {workflow_id}: {e}")
            
            # 更新失败统计
            self._update_performance_stats(False, processing_time, 0.0)
            
            # 返回错误结果
            return {
                'workflow_id': workflow_id,
                'instruction': instruction,
                'error': str(e),
                'processing_time': processing_time,
                'timestamp': start_time.isoformat(),
                'success': False
            }

    async def _generate_llm_decision(
        self,
        standardized_instruction: str,
        model_id: str,
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> TradingDecision:
        """使用LLM生成交易决策"""
        from app.services.llm_gateway import GatewayRequest
        
        # 构建决策提示词
        prompt = self._build_decision_prompt(standardized_instruction, market_data, context)
        
        # 创建请求对象
        request = GatewayRequest(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            temperature=0.1
        )
        
        # 调用LLM
        response = await self.llm_gateway.generate(request)
        
        if not response.success:
            raise Exception(f"LLM调用失败: {response.error}")
        
        # 解析LLM响应为决策对象
        decision = self._parse_llm_decision_response(response.content, model_id)
        
        return decision

    def _build_decision_prompt(
        self,
        instruction: str,
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建决策提示词"""
        
        market_info = json.dumps(market_data, ensure_ascii=False, indent=2)
        context_info = json.dumps(context, ensure_ascii=False, indent=2) if context else "无"
        
        prompt = f"""
你是一个专业的股票交易AI助手。请根据以下信息做出交易决策：

交易指令：{instruction}

市场数据：
{market_info}

上下文信息：
{context_info}

请分析市场情况并做出交易决策，返回JSON格式：
{{
    "action": "BUY/SELL/HOLD",
    "symbol": "股票代码",
    "quantity": 数量,
    "price": 价格,
    "confidence": 置信度(0-1),
    "reasoning": "决策理由",
    "stop_loss": 止损价格(可选),
    "take_profit": 止盈价格(可选)
}}

请确保：
1. 决策基于充分的市场分析
2. 考虑风险控制
3. 提供清晰的决策理由
4. 置信度反映决策的确定性
"""
        return prompt

    def _parse_llm_decision_response(self, response: str, model_id: str) -> TradingDecision:
        """解析LLM决策响应"""
        
        try:
            # 尝试解析JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision_data = json.loads(json_match.group())
            else:
                raise ValueError("无法找到JSON格式的决策数据")
            
            # 创建决策对象
            decision = TradingDecision(
                action=TradingAction(decision_data.get('action', 'HOLD')),
                symbol=decision_data.get('symbol', 'UNKNOWN'),
                quantity=decision_data.get('quantity'),
                price=decision_data.get('price'),
                confidence=decision_data.get('confidence', 0.5),
                reasoning=decision_data.get('reasoning', ''),
                model_id=model_id,
                timestamp=datetime.now(),
                stop_loss=decision_data.get('stop_loss'),
                take_profit=decision_data.get('take_profit')
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"解析LLM决策响应失败: {e}")
            # 返回默认决策
            return TradingDecision(
                action=TradingAction.HOLD,
                symbol='UNKNOWN',
                quantity=None,
                price=None,
                confidence=0.0,
                reasoning=f"决策解析失败: {str(e)}",
                model_id=model_id,
                timestamp=datetime.now()
            )

    async def _get_multi_model_decisions(
        self,
        instruction: str,
        model_ids: List[str],
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, TradingDecision]:
        """并行获取多个模型的决策"""
        
        tasks = []
        for model_id in model_ids:
            task = self._generate_llm_decision(instruction, model_id, market_data, context)
            tasks.append((model_id, task))
        
        results = {}
        for model_id, task in tasks:
            try:
                decision = await task
                results[model_id] = decision
            except Exception as e:
                logger.error(f"模型 {model_id} 决策失败: {e}")
                # 创建默认决策
                results[model_id] = TradingDecision(
                    action=TradingAction.HOLD,
                    symbol='UNKNOWN',
                    quantity=None,
                    price=None,
                    confidence=0.0,
                    reasoning=f"模型决策失败: {str(e)}",
                    model_id=model_id,
                    timestamp=datetime.now()
                )
        
        return results

    def _update_performance_stats(self, success: bool, processing_time: float, confidence: float):
        """更新性能统计"""
        
        self.performance_stats['total_decisions'] += 1
        
        if success:
            self.performance_stats['successful_decisions'] += 1
        else:
            self.performance_stats['failed_decisions'] += 1
        
        # 更新平均置信度
        total_decisions = self.performance_stats['total_decisions']
        current_avg_confidence = self.performance_stats['average_confidence']
        self.performance_stats['average_confidence'] = (
            (current_avg_confidence * (total_decisions - 1) + confidence) / total_decisions
        )
        
        # 更新平均处理时间
        current_avg_time = self.performance_stats['average_processing_time']
        self.performance_stats['average_processing_time'] = (
            (current_avg_time * (total_decisions - 1) + processing_time) / total_decisions
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.performance_stats.copy()

    def get_decision_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取决策历史"""
        if limit:
            return self.decision_history[-limit:]
        return self.decision_history.copy()

    def clear_decision_history(self):
        """清空决策历史"""
        self.decision_history.clear()

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查各个模块
            modules_status = {
                'instruction_parser': 'healthy',
                'confidence_assessor': 'healthy', 
                'model_fusion': 'healthy',
                'instruction_generator': 'healthy',
                'llm_gateway': 'healthy'
            }
            
            # 检查LLM网关
            gateway_stats = self.llm_gateway.get_stats()
            if gateway_stats.get('enabled_adapters', 0) == 0:
                modules_status['llm_gateway'] = 'no_adapters'
            
            return {
                'status': 'healthy',
                'modules': modules_status,
                'performance_stats': self.performance_stats,
                'decision_history_count': len(self.decision_history),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }