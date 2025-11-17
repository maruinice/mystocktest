"""
AI策略生成器服务
基于大语言模型生成量化交易策略
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .llm_gateway import gateway, GatewayRequest, ModelProvider

logger = logging.getLogger(__name__)


class AIStrategyGenerator:
    """AI策略生成器"""
    
    def __init__(self):
        self._gateway = None  # 延迟初始化
        self.strategy_templates = {
            'kdj_rsrs': {
                'name': 'KDJ+RSRS择时策略',
                'description': '基于KDJ和RSRS指标的市场择时策略',
                'indicators': ['KDJ', 'RSRS', 'MA'],
                'template': '''def initialize(context):
    # KDJ+RSRS择时策略初始化
    context.kdj_n = {kdj_n}
    context.kdj_m1 = {kdj_m1}
    context.kdj_m2 = {kdj_m2}
    context.rsrs_n = {rsrs_n}
    context.rsrs_m = {rsrs_m}
    context.rsrs_threshold = {rsrs_threshold}
    context.position_size = {position_size}

def handle_data(context, data):
    # 获取指数数据用于择时
    index_code = '000300.XSHG'  # 沪深300
    index_data = data.history(index_code, ['high', 'low', 'close'], context.rsrs_m + context.kdj_n)
    
    # 计算KDJ指标
    kdj = calculate_kdj(index_data, context.kdj_n, context.kdj_m1, context.kdj_m2)
    last_j = kdj['J'].iloc[-1]
    last_k = kdj['K'].iloc[-1]
    
    # 计算RSRS指标
    rsrs = calculate_rsrs(index_data, context.rsrs_n, context.rsrs_m)
    rsrs_score = rsrs['rsrs_score'].iloc[-1]
    
    # 择时信号判断
    trading_signal = True
    if last_j < 0 or (last_k < 20 and rsrs_score > context.rsrs_threshold):
        trading_signal = True  # 买入信号
    elif last_j > 80 or rsrs_score < -context.rsrs_threshold:
        trading_signal = False  # 卖出信号
    
    # 根据信号执行交易
    for stock in context.stocks:
        position = context.portfolio.positions[stock].amount
        
        if trading_signal and position == 0:
            order_target_percent(stock, context.position_size)
        elif not trading_signal and position > 0:
            order_target_percent(stock, 0)'''
            },
            'trend_following': {
                'name': '趋势跟踪策略',
                'description': '基于技术指标识别趋势并跟踪的策略',
                'indicators': ['MA', 'EMA', 'MACD'],
                'template': '''def initialize(context):
    # 趋势跟踪策略初始化
    context.stocks = {stocks}
    context.short_period = {short_period}
    context.long_period = {long_period}
    context.position_size = {position_size}

def handle_data(context, data):
    for stock in context.stocks:
        # 获取历史价格数据
        hist = data.history(stock, 'close', context.long_period + 1)
        
        # 计算移动平均线
        short_ma = hist[-context.short_period:].mean()
        long_ma = hist.mean()
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：短期均线上穿长期均线
        if short_ma > long_ma and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：短期均线下穿长期均线
        elif short_ma < long_ma and current_position > 0:
            order_target_percent(stock, 0)'''
            },
            'mean_reversion': {
                'name': '均值回归策略',
                'description': '基于价格偏离均值时的回归特性进行交易',
                'indicators': ['RSI', 'BOLL', 'STDEV'],
                'template': '''def initialize(context):
    # 均值回归策略初始化
    context.stocks = {stocks}
    context.rsi_period = {rsi_period}
    context.rsi_overbought = {rsi_overbought}
    context.rsi_oversold = {rsi_oversold}
    context.position_size = {position_size}

def handle_data(context, data):
    for stock in context.stocks:
        # 计算RSI指标
        hist = data.history(stock, 'close', context.rsi_period + 1)
        rsi = calculate_rsi(hist, context.rsi_period)
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：RSI < 超卖线
        if rsi < context.rsi_oversold and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：RSI > 超买线
        elif rsi > context.rsi_overbought and current_position > 0:
            order_target_percent(stock, 0)

def calculate_rsi(prices, period):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]'''
            },
            'momentum': {
                'name': '动量策略',
                'description': '基于价格动量和成交量的策略',
                'indicators': ['MACD', 'Volume', 'ROC'],
                'template': '''def initialize(context):
    # 动量策略初始化
    context.stocks = {stocks}
    context.momentum_period = {momentum_period}
    context.volume_threshold = {volume_threshold}
    context.position_size = {position_size}

def handle_data(context, data):
    for stock in context.stocks:
        # 获取价格和成交量数据
        hist_price = data.history(stock, 'close', context.momentum_period + 1)
        hist_volume = data.history(stock, 'volume', context.momentum_period + 1)
        
        # 计算动量指标
        momentum = (hist_price.iloc[-1] / hist_price.iloc[0] - 1) * 100
        avg_volume = hist_volume.mean()
        current_volume = data.current(stock, 'volume')
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：正动量 + 成交量放大
        if momentum > 0 and current_volume > avg_volume * context.volume_threshold and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：负动量
        elif momentum < -5 and current_position > 0:
            order_target_percent(stock, 0)'''
            }
        }
    
    @property
    def gateway(self):
        """延迟获取gateway实例"""
        if self._gateway is None:
            self._gateway = gateway
        return self._gateway
    
    def generate_strategy_sync(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        基于用户提示生成策略（同步版本）
        
        Args:
            prompt: 用户的策略需求描述
            options: 生成选项
            
        Returns:
            生成的策略信息
        """
        try:
            import asyncio
            
            # 创建新的事件循环或使用现有的
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 调用异步方法
            return loop.run_until_complete(self.generate_strategy(prompt, options))
            
        except Exception as e:
            logger.error(f"同步AI策略生成失败: {e}")
            # 降级到模板生成
            return self._generate_from_template(prompt, options or {})

    async def generate_strategy(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        基于用户提示生成策略
        
        Args:
            prompt: 用户的策略需求描述
            options: 生成选项
            
        Returns:
            生成的策略信息
        """
        try:
            options = options or {}
            
            # 构建AI提示词
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(prompt, options)
            
            logger.info(f"[AI策略生成] 开始调用LLM，提示词长度: {len(user_prompt)}")
            
            import time
            import asyncio
            start_time = time.time()
            
            # 调用LLM生成策略，设置60秒超时
            request = GatewayRequest(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="deepseek-chat",
                max_tokens=2000,
                temperature=0.7
            )
            
            try:
                # 设置60秒超时
                response = await asyncio.wait_for(
                    self.gateway.generate(request),
                    timeout=60.0
                )
                
                elapsed_time = time.time() - start_time
                logger.info(f"[AI策略生成] LLM调用耗时: {elapsed_time:.2f}秒")
                
            except asyncio.TimeoutError:
                elapsed_time = time.time() - start_time
                logger.error(f"[AI策略生成] LLM调用超时: {elapsed_time:.2f}秒")
                # 超时后降级到模板生成
                return self._generate_from_template(prompt, options)
            
            logger.info(f"[AI策略生成] LLM响应状态: success={response.success}")
            
            if response.success:
                logger.info(f"[AI策略生成] LLM响应内容长度: {len(response.content)}")
                logger.info(f"[AI策略生成] LLM响应模型: {response.model}")
                logger.info(f"[AI策略生成] LLM响应提供商: {response.provider}")
                logger.info(f"[AI策略生成] LLM Token使用: {response.usage}")
                logger.info(f"[AI策略生成] LLM响应时间: {response.response_time:.2f}秒")
                logger.info(f"[AI策略生成] LLM完整响应内容:")
                logger.info("=" * 80)
                logger.info(response.content)
                logger.info("=" * 80)
                
                # 解析AI响应
                strategy_info = self._parse_ai_response(response.content, prompt, options)
                logger.info(f"[AI策略生成] 策略解析成功: {strategy_info.get('name')}")
                logger.info(f"[AI策略生成] 策略类型: {strategy_info.get('type')}")
                logger.info(f"[AI策略生成] 是否模板生成: {strategy_info.get('template_based', False)}")
                return strategy_info
            else:
                # AI调用失败，使用模板生成
                logger.warning(f"[AI策略生成] AI生成失败，使用模板: {response.error}")
                return self._generate_from_template(prompt, options)
                
        except Exception as e:
            logger.error(f"[AI策略生成] AI策略生成失败: {e}")
            import traceback
            traceback.print_exc()
            # 降级到模板生成
            logger.warning(f"[AI策略生成] 降级到模板生成")
            return self._generate_from_template(prompt, options)
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个专业的量化交易策略开发专家。你需要根据用户的需求生成完整的Python交易策略代码。

策略代码必须包含以下两个函数：
1. initialize(context): 策略初始化函数，设置context.stocks股票列表
2. handle_data(context, data): 数据处理函数，每个交易日调用

重要：代码必须严格遵循以下API规范：

**Context对象：**
- context.stocks: 股票代码列表（由用户在回测时指定，不要在代码中硬编码）
- context.portfolio.positions[stock_code]: 获取持仓对象
- context.portfolio.positions[stock_code].amount: 当前持仓数量
- context.portfolio.cash: 当前现金

**Data对象：**
- data.current(stock_code, 'close'): 获取当前收盘价
- data.current(stock_code, 'volume'): 获取当前成交量
- data.history(stock_code, 'close', bar_count): 获取历史收盘价序列(pandas Series)
- data.history(stock_code, ['close', 'volume'], bar_count): 获取多个字段(pandas DataFrame)

**交易函数：**
- order_target_percent(stock_code, target_percent): 按目标仓位百分比下单
  例如：order_target_percent('000001.XSHE', 0.1) 表示该股票占总资产10%

**重要说明：**
- **不要在initialize函数中设置context.stocks**，股票池由用户在回测时指定
- initialize函数只用于设置策略参数（如均线周期、阈值等）
- handle_data函数中直接使用context.stocks遍历股票

**代码示例：**
```python
def initialize(context):
    # 只设置策略参数，不要设置stocks
    context.ma_short = 5
    context.ma_long = 20
    context.position_size = 0.3

def handle_data(context, data):
    # 直接使用context.stocks，它由回测系统提供
    for stock in context.stocks:
        # 获取历史数据
        prices = data.history(stock, 'close', context.ma_long + 1)
        
        # 计算均线
        ma_short = prices[-context.ma_short:].mean()
        ma_long = prices.mean()
        
        # 获取当前持仓
        position = context.portfolio.positions[stock].amount
        
        # 交易逻辑
        if ma_short > ma_long and position == 0:
            order_target_percent(stock, 0.5)
        elif ma_short < ma_long and position > 0:
            order_target_percent(stock, 0)
```

请返回JSON格式的响应，包含以下字段：
{
    "name": "策略名称",
    "description": "策略描述",
    "category": "策略类型(trend_following/mean_reversion/momentum/arbitrage/multi_factor/custom)",
    "risk_level": "风险等级(low/medium/high)",
    "parameters": {
        "参数名": "参数值"
    },
    "indicators": ["使用的技术指标"],
    "buy_conditions": [
        {
            "type": "indicator/price/volume",
            "indicator": "指标名称(如MA/RSI/MACD)",
            "operator": "greater_than/less_than/cross_above/cross_below",
            "value": "比较值或阈值",
            "description": "条件描述"
        }
    ],
    "sell_conditions": [
        {
            "type": "indicator/price/volume",
            "indicator": "指标名称",
            "operator": "greater_than/less_than/cross_above/cross_below",
            "value": "比较值或阈值",
            "description": "条件描述"
        }
    ],
    "risk_controls": {
        "stop_loss": 5.0,
        "take_profit": 15.0,
        "max_position_size": 0.1
    },
    "code": "完整的Python策略代码"
}

确保代码语法正确，逻辑清晰，并包含适当的注释。买入卖出条件必须明确具体。"""
    
    def enhance_prompt(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """
        公共方法：增强用户提示词，自动补全缺失信息
        这个方法在API层调用，补全后的提示词会传递给AI
        
        Args:
            prompt: 原始用户提示词
            options: 可选的策略选项
            
        Returns:
            补全后的完整提示词
        """
        options = options or {}
        
        # 第一步：增强用户提示词，确保包含完整信息
        enhanced_prompt = f"{prompt}\n\n"
        
        enhancements = []
        
        # 检查是否提到了策略参数，如果没有则补充
        if not any(keyword in prompt.lower() for keyword in ['参数', 'parameter', '周期', 'period']):
            enhancement = "请为策略设计合理的参数配置。"
            enhanced_prompt += enhancement + "\n"
            enhancements.append("策略参数")
        
        # 检查是否提到了技术指标，如果没有则补充
        if not any(keyword in prompt.lower() for keyword in ['指标', 'indicator', 'ma', 'rsi', 'macd', 'kdj', 'cci', 'bollinger']):
            enhancement = "请选择合适的技术指标来实现策略逻辑。"
            enhanced_prompt += enhancement + "\n"
            enhancements.append("技术指标")
        
        # 检查是否提到了交易规则，如果没有则补充
        if not any(keyword in prompt.lower() for keyword in ['买入', 'buy', '卖出', 'sell', '条件', 'condition', '规则', 'rule']):
            enhancement = "请明确定义买入条件和卖出条件。"
            enhanced_prompt += enhancement + "\n"
            enhancements.append("交易规则")
        
        if enhancements:
            logger.info(f"[提示词增强] 补充了: {', '.join(enhancements)}")
        else:
            logger.info(f"[提示词增强] 提示词已完整，无需补充")
        
        return enhanced_prompt.strip()
    
    def _build_user_prompt(self, prompt: str, options: Dict[str, Any]) -> str:
        """构建用户提示词 - 内部方法，prompt已经过enhance_prompt增强"""
        
        # 注意：这里的prompt已经是增强后的提示词了
        enhanced_prompt = prompt
        
        # 第二步：构建完整的用户提示
        user_prompt = f"""请根据以下需求生成量化交易策略：

用户需求：
{enhanced_prompt}

要求：
1. **策略参数**：必须包含具体的、可调整的策略参数（如均线周期、阈值等）
2. **技术指标**：明确使用哪些技术指标（MA、RSI、MACD等）
3. **交易规则**：
   - 买入条件：明确的买入信号和条件
   - 卖出条件：明确的卖出信号和条件
4. **策略代码**：生成完整可运行的Python代码
5. **风险控制**：包含止损、止盈等风险管理措施
"""
        
        if options.get('strategy_type'):
            user_prompt += f"\n策略类型偏好: {options['strategy_type']}"
        
        if options.get('risk_level'):
            user_prompt += f"\n风险等级: {options['risk_level']}"
        
        if options.get('indicators'):
            user_prompt += f"\n希望使用的技术指标: {', '.join(options['indicators'])}"
        
        return user_prompt
    
    def _parse_ai_response(self, response_content: str, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            # 提取JSON内容（可能在代码块中）
            content = response_content.strip()
            
            # 如果包含```json代码块，提取其中的内容
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                if end > start:
                    content = content[start:end].strip()
            elif '```' in content:
                start = content.find('```') + 3
                end = content.find('```', start)
                if end > start:
                    content = content[start:end].strip()
            
            # 尝试解析JSON响应
            if content.startswith('{'):
                strategy_data = json.loads(content)
            else:
                # 如果不是JSON格式，尝试提取代码块
                strategy_data = self._extract_strategy_from_text(response_content, prompt, options)
            
            # 验证必需字段
            required_fields = ['name', 'description', 'category', 'risk_level', 'code']
            for field in required_fields:
                if field not in strategy_data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 添加元数据
            strategy_data.update({
                'strategy_id': f'AI_{int(datetime.now().timestamp())}',
                'author': 'AI助手',
                'status': 'draft',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'ai_generated': True,
                'original_prompt': prompt
            })
            
            return strategy_data
            
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            # 降级到模板生成
            return self._generate_from_template(prompt, options)
    
    def _extract_strategy_from_text(self, text: str, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """从文本中提取策略信息"""
        # 简单的文本解析逻辑
        lines = text.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if '```python' in line or '```' in line:
                in_code_block = not in_code_block
                continue
            if in_code_block:
                code_lines.append(line)
        
        code = '\n'.join(code_lines) if code_lines else self._get_default_code()
        
        # 根据提示词推断策略类型
        category = self._infer_strategy_type(prompt, options)
        
        return {
            'name': f'AI生成策略_{datetime.now().strftime("%m%d_%H%M")}',
            'description': f'基于提示词"{prompt[:50]}..."生成的策略',
            'category': category,
            'risk_level': options.get('risk_level', 'medium'),
            'parameters': {
                'position_size': 0.1,
                'stop_loss': 5.0,
                'take_profit': 15.0
            },
            'indicators': self._extract_indicators(text),
            'code': code
        }
    
    def _generate_from_template(self, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """基于模板生成策略"""
        # 根据提示词选择合适的模板
        strategy_type = self._infer_strategy_type(prompt, options)
        
        # 如果是custom类型，使用trend_following作为默认模板
        if strategy_type == 'custom':
            strategy_type = 'trend_following'
            
        template = self.strategy_templates.get(strategy_type, self.strategy_templates['trend_following'])

        # 生成参数
        parameters = self._generate_parameters(strategy_type, options)

        # 填充模板
        code = template['template'].format(**parameters)

        # 生成买入卖出条件
        buy_conditions, sell_conditions = self._generate_trading_conditions(strategy_type, parameters)

        return {
            'strategy_id': f'AI_{int(datetime.now().timestamp())}',
            'name': f'AI生成{template["name"]}',
            'description': f'基于提示词"{prompt}"生成的{template["description"]}',
            'category': strategy_type,
            'risk_level': options.get('risk_level', 'medium'),
            'author': 'AI助手',
            'parameters': parameters,
            'indicators': template['indicators'],
            'buy_conditions': buy_conditions,
            'sell_conditions': sell_conditions,
            'risk_controls': self._generate_risk_controls(options.get('risk_level', 'medium')),
            'code': code,
            'status': 'draft',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'ai_generated': True,
            'original_prompt': prompt,
            'template_based': True
        }
    
    def _infer_strategy_type(self, prompt: str, options: Dict[str, Any]) -> str:
        """推断策略类型"""
        prompt_lower = prompt.lower()
        
        if options.get('strategy_type'):
            return options['strategy_type']
        
        # 关键词匹配
        if any(word in prompt_lower for word in ['rsi', '超买', '超卖', '回归', '均值']):
            return 'mean_reversion'
        elif any(word in prompt_lower for word in ['动量', 'momentum', 'macd', '成交量']):
            return 'momentum'
        elif any(word in prompt_lower for word in ['均线', 'ma', 'ema', '趋势', 'trend']):
            return 'trend_following'
        else:
            return 'custom'
    
    def _generate_parameters(self, strategy_type: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """生成策略参数"""
        base_params = {
            'stocks': "['000001.XSHE', '000002.XSHE']",
            'position_size': 0.1
        }
        
        if strategy_type == 'kdj_rsrs':
            base_params.update({
                'kdj_n': 27,  # 长周期KDJ
                'kdj_m1': 9,
                'kdj_m2': 9,
                'rsrs_n': 18,
                'rsrs_m': 600,
                'rsrs_threshold': 0.7
            })
        elif strategy_type == 'trend_following':
            base_params.update({
                'short_period': 5,
                'long_period': 20
            })
        elif strategy_type == 'mean_reversion':
            base_params.update({
                'rsi_period': 14,
                'rsi_overbought': 70,
                'rsi_oversold': 30
            })
        elif strategy_type == 'momentum':
            base_params.update({
                'momentum_period': 10,
                'volume_threshold': 1.5
            })
        
        return base_params
    
    def _extract_indicators(self, text: str) -> List[str]:
        """从文本中提取技术指标"""
        indicators = []
        text_lower = text.lower()
        
        indicator_keywords = {
            'MA': ['ma', '移动平均', 'moving average'],
            'EMA': ['ema', '指数移动平均'],
            'RSI': ['rsi', '相对强弱'],
            'MACD': ['macd'],
            'BOLL': ['boll', '布林带', 'bollinger'],
            'KDJ': ['kdj', '随机指标'],
            'RSRS': ['rsrs', '阻力支撑', '相对强度'],
            'Volume': ['volume', '成交量'],
            'ATR': ['atr', '真实波幅'],
            'CCI': ['cci', '顺势指标']
        }
        
        for indicator, keywords in indicator_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                indicators.append(indicator)
        
        return indicators or ['MA']
    
    def _get_default_code(self) -> str:
        """获取默认策略代码"""
        return '''def initialize(context):
    # 默认策略初始化
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.position_size = 0.1

def handle_data(context, data):
    # 默认策略逻辑
    for stock in context.stocks:
        current_position = context.portfolio.positions[stock].amount

        # 简单的买入持有策略
        if current_position == 0:
            order_target_percent(stock, context.position_size)'''

    def _generate_trading_conditions(self, strategy_type: str, parameters: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """生成买入卖出条件"""
        buy_conditions = []
        sell_conditions = []

        if strategy_type == 'trend_following':
            buy_conditions = [
                {
                    'type': 'indicator',
                    'indicator': 'MA',
                    'operator': 'cross_above',
                    'params': {
                        'short_period': parameters.get('short_period', 5),
                        'long_period': parameters.get('long_period', 20)
                    },
                    'description': '短期均线上穿长期均线'
                }
            ]
            sell_conditions = [
                {
                    'type': 'indicator',
                    'indicator': 'MA',
                    'operator': 'cross_below',
                    'params': {
                        'short_period': parameters.get('short_period', 5),
                        'long_period': parameters.get('long_period', 20)
                    },
                    'description': '短期均线下穿长期均线'
                }
            ]

        elif strategy_type == 'mean_reversion':
            buy_conditions = [
                {
                    'type': 'indicator',
                    'indicator': 'RSI',
                    'operator': 'less_than',
                    'value': parameters.get('rsi_oversold', 30),
                    'params': {
                        'period': parameters.get('rsi_period', 14)
                    },
                    'description': f'RSI低于{parameters.get("rsi_oversold", 30)}（超卖）'
                }
            ]
            sell_conditions = [
                {
                    'type': 'indicator',
                    'indicator': 'RSI',
                    'operator': 'greater_than',
                    'value': parameters.get('rsi_overbought', 70),
                    'params': {
                        'period': parameters.get('rsi_period', 14)
                    },
                    'description': f'RSI高于{parameters.get("rsi_overbought", 70)}（超买）'
                }
            ]

        elif strategy_type == 'momentum':
            buy_conditions = [
                {
                    'type': 'indicator',
                    'indicator': 'MACD',
                    'operator': 'cross_above',
                    'params': {
                        'fast_period': 12,
                        'slow_period': 26,
                        'signal_period': 9
                    },
                    'description': 'MACD上穿信号线'
                },
                {
                    'type': 'volume',
                    'operator': 'greater_than',
                    'value': parameters.get('volume_threshold', 1.5),
                    'description': '成交量放大'
                }
            ]
            sell_conditions = [
                {
                    'type': 'indicator',
                    'indicator': 'MACD',
                    'operator': 'cross_below',
                    'params': {
                        'fast_period': 12,
                        'slow_period': 26,
                        'signal_period': 9
                    },
                    'description': 'MACD下穿信号线'
                }
            ]

        else:
            # 默认条件
            buy_conditions = [
                {
                    'type': 'price',
                    'operator': 'greater_than',
                    'value': 'MA20',
                    'description': '价格高于20日均线'
                }
            ]
            sell_conditions = [
                {
                    'type': 'price',
                    'operator': 'less_than',
                    'value': 'MA20',
                    'description': '价格低于20日均线'
                }
            ]

        return buy_conditions, sell_conditions

    def _generate_risk_controls(self, risk_level: str) -> Dict[str, Any]:
        """生成风险控制配置"""
        risk_configs = {
            'low': {
                'max_position_size': 0.05,  # 单只股票最大仓位5%
                'max_total_position': 0.3,   # 总仓位最大30%
                'stop_loss': 3.0,            # 止损3%
                'take_profit': 10.0,         # 止盈10%
                'max_drawdown': 5.0          # 最大回撤5%
            },
            'medium': {
                'max_position_size': 0.1,    # 单只股票最大仓位10%
                'max_total_position': 0.6,   # 总仓位最大60%
                'stop_loss': 5.0,            # 止损5%
                'take_profit': 15.0,         # 止盈15%
                'max_drawdown': 10.0         # 最大回撤10%
            },
            'high': {
                'max_position_size': 0.2,    # 单只股票最大仓位20%
                'max_total_position': 0.9,   # 总仓位最大90%
                'stop_loss': 8.0,            # 止损8%
                'take_profit': 25.0,         # 止盈25%
                'max_drawdown': 20.0         # 最大回撤20%
            }
        }

        return risk_configs.get(risk_level, risk_configs['medium'])


# 创建全局实例
ai_strategy_generator = AIStrategyGenerator()