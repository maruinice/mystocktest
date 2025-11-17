"""
自然语言指令解析模块
负责将用户的自然语言指令转换为标准化的交易指令
"""
import re
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

from app.models.ai_decision_models import (
    InstructionParseResult, 
    InstructionType, 
    TradingAction
)
from app.services.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)

@dataclass
class ParsedInstruction:
    """解析后的指令结构"""
    action: TradingAction
    symbol: str
    quantity: Optional[int] = None
    price: Optional[float] = None
    instruction_type: InstructionType = InstructionType.MARKET_ORDER
    conditions: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}

class InstructionParser:
    """自然语言指令解析器"""
    
    def __init__(self, llm_gateway: LLMGateway):
        self.llm_gateway = llm_gateway
        
        # 预定义的关键词模式
        self.action_patterns = {
            TradingAction.BUY: [
                r'买入|购买|买|做多|开多|long',
                r'buy|purchase|long|go long'
            ],
            TradingAction.SELL: [
                r'卖出|出售|卖|做空|开空|short',
                r'sell|short|go short'
            ],
            TradingAction.HOLD: [
                r'持有|保持|不动|观望|等待',
                r'hold|keep|wait|maintain'
            ]
        }
        
        # 股票代码模式
        self.symbol_patterns = [
            r'([0-9]{6})',  # 6位数字股票代码
            r'([A-Z]{2,5})',  # 美股代码
            r'([0-9]{6}\.SH|[0-9]{6}\.SZ)',  # 带交易所后缀
            r'([\u4e00-\u9fa5]+)股票',  # 中文股票名称
            r'([\u4e00-\u9fa5]+)公司',  # 中文公司名称
            r'(平安银行|工商银行|建设银行|农业银行|中国银行|招商银行|浦发银行|民生银行|兴业银行|中信银行)',  # 常见银行名称
            r'(腾讯|阿里巴巴|百度|京东|美团|拼多多|字节跳动|小米|华为|比亚迪)',  # 常见公司名称
        ]
        
        # 数量模式
        self.quantity_patterns = [
            r'(\d+)股',
            r'(\d+)手',
            r'(\d+\.?\d*)万股',
            r'(\d+\.?\d*)万手',
            r'(\d+) shares?',
            r'(\d+) lots?'
        ]
        
        # 价格模式
        self.price_patterns = [
            r'(\d+\.?\d*)元',
            r'价格(\d+\.?\d*)',
            r'(\d+\.?\d*)块',
            r'\$(\d+\.?\d*)',
            r'at (\d+\.?\d*)',
            r'price (\d+\.?\d*)'
        ]
        
        # 指令类型模式
        self.instruction_type_patterns = {
            InstructionType.MARKET_ORDER: [
                r'市价|市场价|立即|马上',
                r'market|immediately|now'
            ],
            InstructionType.LIMIT_ORDER: [
                r'限价|指定价格|(\d+\.?\d*)元买入|(\d+\.?\d*)元卖出',
                r'limit|at price|specific price'
            ],
            InstructionType.STOP_ORDER: [
                r'止损|止盈|触发|达到.*时',
                r'stop|trigger|when.*reaches'
            ],
            InstructionType.CONDITIONAL_ORDER: [
                r'如果|当.*时|条件|满足.*条件',
                r'if|when|condition|conditional'
            ]
        }
        
        # 常见的模糊表达
        self.ambiguous_expressions = [
            r'一些|部分|适量|合适的数量',
            r'some|a bit|appropriate amount',
            r'差不多|大概|约|左右',
            r'about|around|approximately'
        ]
        
        # 冲突检测模式
        self.conflict_patterns = [
            (r'买入.*卖出|卖出.*买入', '同时包含买入和卖出指令'),
            (r'市价.*限价|限价.*市价', '同时指定市价和限价'),
            (r'立即.*等待|等待.*立即', '时间要求冲突'),
        ]

    async def parse_instruction(self, instruction: str, context: Dict[str, Any] = None) -> InstructionParseResult:
        """
        解析自然语言指令
        
        Args:
            instruction: 原始指令文本
            context: 上下文信息（如当前持仓、市场状态等）
            
        Returns:
            InstructionParseResult: 解析结果
        """
        try:
            logger.info(f"开始解析指令: {instruction}")
            
            # 1. 预处理指令
            cleaned_instruction = self._preprocess_instruction(instruction)
            
            # 2. 基于规则的初步解析
            rule_based_result = self._rule_based_parse(cleaned_instruction)
            
            # 3. 检测模糊性和冲突
            ambiguity_score = self._calculate_ambiguity_score(cleaned_instruction)
            conflicts = self._detect_conflicts(cleaned_instruction)
            
            # 4. 如果规则解析失败或置信度低，使用LLM增强解析
            if rule_based_result is None or ambiguity_score > 0.5:
                llm_result = await self._llm_enhanced_parse(cleaned_instruction, context)
                if llm_result:
                    rule_based_result = llm_result
            
            # 5. 生成标准化指令
            if rule_based_result:
                standardized_instruction = self._generate_standardized_instruction(rule_based_result)
                confidence = max(0.1, 1.0 - ambiguity_score - len(conflicts) * 0.2)
            else:
                standardized_instruction = "无法解析的指令"
                confidence = 0.0
            
            # 6. 生成建议
            suggestions = self._generate_suggestions(cleaned_instruction, conflicts, ambiguity_score)
            
            return InstructionParseResult(
                original_instruction=instruction,
                parsed_instruction=standardized_instruction,
                standardized_instructions=[standardized_instruction] if standardized_instruction != "无法解析的指令" else [],
                instruction_type=rule_based_result.instruction_type if rule_based_result else InstructionType.MARKET_ORDER,
                confidence=confidence,
                ambiguity_score=ambiguity_score,
                conflicts=conflicts,
                suggestions=suggestions,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"指令解析失败: {e}")
            return InstructionParseResult(
                original_instruction=instruction,
                parsed_instruction="解析失败",
                standardized_instructions=[],
                instruction_type=InstructionType.MARKET_ORDER,
                confidence=0.0,
                ambiguity_score=1.0,
                conflicts=[f"解析错误: {str(e)}"],
                suggestions=["请检查指令格式并重新输入"],
                timestamp=datetime.now()
            )

    def _preprocess_instruction(self, instruction: str) -> str:
        """预处理指令文本"""
        # 移除多余的空格和标点
        instruction = re.sub(r'\s+', ' ', instruction)
        instruction = re.sub(r'[，。！？；：]', ' ', instruction)
        
        # 标准化数字表达
        instruction = re.sub(r'一千', '1000', instruction)
        instruction = re.sub(r'一万', '10000', instruction)
        instruction = re.sub(r'十万', '100000', instruction)
        
        return instruction.strip()

    def _rule_based_parse(self, instruction: str) -> Optional[ParsedInstruction]:
        """基于规则的指令解析"""
        try:
            # 解析交易动作
            action = self._extract_action(instruction)
            if not action:
                return None
            
            # 解析股票代码
            symbol = self._extract_symbol(instruction)
            if not symbol:
                return None
            
            # 解析数量
            quantity = self._extract_quantity(instruction)
            
            # 解析价格
            price = self._extract_price(instruction)
            
            # 解析指令类型
            instruction_type = self._extract_instruction_type(instruction)
            
            # 解析条件
            conditions = self._extract_conditions(instruction)
            
            return ParsedInstruction(
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=price,
                instruction_type=instruction_type,
                conditions=conditions
            )
            
        except Exception as e:
            logger.error(f"规则解析失败: {e}")
            return None

    def _extract_action(self, instruction: str) -> Optional[TradingAction]:
        """提取交易动作"""
        for action, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, instruction, re.IGNORECASE):
                    return action
        return None

    def _extract_symbol(self, instruction: str) -> Optional[str]:
        """提取股票代码"""
        for pattern in self.symbol_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None

    def _extract_quantity(self, instruction: str) -> Optional[int]:
        """提取交易数量"""
        for pattern in self.quantity_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                quantity_str = match.group(1)
                try:
                    quantity = float(quantity_str)
                    # 处理万股、万手的情况
                    if '万' in match.group(0):
                        quantity *= 10000
                    # 手转换为股（1手=100股）
                    if '手' in match.group(0):
                        quantity *= 100
                    return int(quantity)
                except ValueError:
                    continue
        return None

    def _extract_price(self, instruction: str) -> Optional[float]:
        """提取价格"""
        for pattern in self.price_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_instruction_type(self, instruction: str) -> InstructionType:
        """提取指令类型"""
        for inst_type, patterns in self.instruction_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, instruction, re.IGNORECASE):
                    return inst_type
        return InstructionType.MARKET_ORDER

    def _extract_conditions(self, instruction: str) -> Dict[str, Any]:
        """提取条件信息"""
        conditions = {}
        
        # 提取止损条件
        stop_loss_match = re.search(r'止损.*?(\d+\.?\d*)', instruction, re.IGNORECASE)
        if stop_loss_match:
            conditions['stop_loss'] = float(stop_loss_match.group(1))
        
        # 提取止盈条件
        take_profit_match = re.search(r'止盈.*?(\d+\.?\d*)', instruction, re.IGNORECASE)
        if take_profit_match:
            conditions['take_profit'] = float(take_profit_match.group(1))
        
        # 提取时间条件
        time_match = re.search(r'(\d+)分钟|(\d+)小时|(\d+)天', instruction, re.IGNORECASE)
        if time_match:
            conditions['time_limit'] = time_match.group(0)
        
        return conditions

    def _calculate_ambiguity_score(self, instruction: str) -> float:
        """计算模糊度评分"""
        ambiguity_score = 0.0
        
        # 检查模糊表达
        for pattern in self.ambiguous_expressions:
            if re.search(pattern, instruction, re.IGNORECASE):
                ambiguity_score += 0.3
        
        # 检查缺失关键信息
        if not self._extract_symbol(instruction):
            ambiguity_score += 0.4
        
        if not self._extract_action(instruction):
            ambiguity_score += 0.4
        
        if not self._extract_quantity(instruction):
            ambiguity_score += 0.2
        
        return min(1.0, ambiguity_score)

    def _detect_conflicts(self, instruction: str) -> List[str]:
        """检测指令冲突"""
        conflicts = []
        
        for pattern, description in self.conflict_patterns:
            if re.search(pattern, instruction, re.IGNORECASE):
                conflicts.append(description)
        
        return conflicts

    async def _llm_enhanced_parse(self, instruction: str, context: Dict[str, Any] = None) -> Optional[ParsedInstruction]:
        """使用LLM增强解析"""
        try:
            from app.services.llm_gateway import GatewayRequest
            
            prompt = self._build_parse_prompt(instruction, context)
            
            request = GatewayRequest(
                messages=[{"role": "user", "content": prompt}],
                model="deepseek",
                temperature=0.1
            )
            
            response = await self.llm_gateway.generate(request)
            
            if response.success:
                return self._parse_llm_response(response.content)
            
        except Exception as e:
            logger.error(f"LLM增强解析失败: {e}")
        
        return None

    def _build_parse_prompt(self, instruction: str, context: Dict[str, Any] = None) -> str:
        """构建LLM解析提示词"""
        context_info = ""
        if context:
            context_info = f"上下文信息: {json.dumps(context, ensure_ascii=False)}\n"
        
        prompt = f"""
请解析以下交易指令，并以JSON格式返回结果：

{context_info}
用户指令: {instruction}

请返回以下格式的JSON：
{{
    "action": "BUY/SELL/HOLD",
    "symbol": "股票代码",
    "quantity": 数量(整数),
    "price": 价格(浮点数，可选),
    "instruction_type": "MARKET_ORDER/LIMIT_ORDER/STOP_ORDER/CONDITIONAL_ORDER",
    "conditions": {{
        "stop_loss": 止损价格(可选),
        "take_profit": 止盈价格(可选),
        "time_limit": "时间限制(可选)"
    }}
}}

如果无法解析，请返回null。
"""
        return prompt

    def _parse_llm_response(self, response: str) -> Optional[ParsedInstruction]:
        """解析LLM响应"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return None
            
            data = json.loads(json_match.group(0))
            
            if not data:
                return None
            
            return ParsedInstruction(
                action=TradingAction(data.get('action')),
                symbol=data.get('symbol'),
                quantity=data.get('quantity'),
                price=data.get('price'),
                instruction_type=InstructionType(data.get('instruction_type', 'MARKET_ORDER')),
                conditions=data.get('conditions', {})
            )
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            return None

    def _generate_standardized_instruction(self, parsed: ParsedInstruction) -> str:
        """生成标准化指令"""
        parts = []
        
        # 动作
        action_map = {
            TradingAction.BUY: "买入",
            TradingAction.SELL: "卖出",
            TradingAction.HOLD: "持有"
        }
        parts.append(action_map[parsed.action])
        
        # 股票代码
        parts.append(parsed.symbol)
        
        # 数量
        if parsed.quantity:
            parts.append(f"{parsed.quantity}股")
        
        # 价格和类型
        if parsed.instruction_type == InstructionType.MARKET_ORDER:
            parts.append("市价单")
        elif parsed.instruction_type == InstructionType.LIMIT_ORDER and parsed.price:
            parts.append(f"限价单 {parsed.price}元")
        elif parsed.instruction_type == InstructionType.STOP_ORDER:
            parts.append("止损单")
        elif parsed.instruction_type == InstructionType.CONDITIONAL_ORDER:
            parts.append("条件单")
        
        # 条件
        if parsed.conditions:
            if 'stop_loss' in parsed.conditions:
                parts.append(f"止损{parsed.conditions['stop_loss']}元")
            if 'take_profit' in parsed.conditions:
                parts.append(f"止盈{parsed.conditions['take_profit']}元")
        
        return " ".join(parts)

    def _generate_suggestions(self, instruction: str, conflicts: List[str], ambiguity_score: float) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if ambiguity_score > 0.5:
            suggestions.append("指令存在模糊表达，建议明确指定股票代码、数量和价格")
        
        if conflicts:
            suggestions.append("检测到指令冲突，请检查并修正矛盾的表达")
        
        if not self._extract_symbol(instruction):
            suggestions.append("请明确指定股票代码")
        
        if not self._extract_quantity(instruction):
            suggestions.append("建议指定具体的交易数量")
        
        if not self._extract_action(instruction):
            suggestions.append("请明确指定交易动作（买入/卖出/持有）")
        
        return suggestions

    async def resolve_conflicts(self, instruction: str, conflicts: List[str]) -> InstructionParseResult:
        """解决指令冲突"""
        try:
            prompt = f"""
以下交易指令存在冲突，请帮助解决：

原始指令: {instruction}
检测到的冲突: {', '.join(conflicts)}

请提供一个明确、无冲突的指令建议，并说明解决方案。
"""
            
            response = await self.llm_gateway.generate(
                GatewayRequest(
                    messages=[{"role": "user", "content": prompt}],
                    model="deepseek",
                    temperature=0.3
                )
            )
            
            if response.success:
                resolved_instruction = response.content
                return await self.parse_instruction(resolved_instruction)
            
        except Exception as e:
            logger.error(f"冲突解决失败: {e}")
        
        # 如果解决失败，返回原始解析结果
        return await self.parse_instruction(instruction)

    async def handle_ambiguous_instruction(self, instruction: str, ambiguity_score: float) -> InstructionParseResult:
        """处理模糊指令"""
        try:
            prompt = f"""
以下交易指令存在模糊表达（模糊度: {ambiguity_score:.2f}），请帮助澄清：

原始指令: {instruction}

请提供以下信息：
1. 明确的指令建议
2. 需要用户确认的关键信息
3. 可能的解释选项

请以结构化的方式回答。
"""
            
            response = await self.llm_gateway.generate(
                GatewayRequest(
                    messages=[{"role": "user", "content": prompt}],
                    model="deepseek",
                    temperature=0.2
                )
            )
            
            if response.success:
                # 基于LLM的建议重新解析
                clarified_instruction = response.content
                result = await self.parse_instruction(clarified_instruction)
                result.suggestions.append(f"LLM建议: {response.content}")
                return result
            
        except Exception as e:
            logger.error(f"模糊指令处理失败: {e}")
        
        # 如果处理失败，返回原始解析结果
        return await self.parse_instruction(instruction)