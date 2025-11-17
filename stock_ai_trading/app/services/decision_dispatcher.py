"""
决策分发服务
负责并行LLM请求、响应格式校验、决策结果路由和异常决策处理
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp
import openai
from pydantic import BaseModel, ValidationError

from ..config.settings import settings
from .performance_monitor import monitor_performance

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """LLM提供商"""
    OPENAI = "openai"
    CLAUDE = "claude"
    QWEN = "qwen"
    BAIDU = "baidu"
    LOCAL = "local"

class DecisionStatus(Enum):
    """决策状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INVALID = "invalid"

@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout: int = 30
    retry_count: int = 3
    enabled: bool = True
    weight: float = 1.0  # 决策权重
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionRequest:
    """决策请求"""
    request_id: str
    symbol: str
    prompt: str
    timestamp: datetime
    priority: int = 1
    timeout: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionResponse:
    """决策响应"""
    request_id: str
    provider: LLMProvider
    model: str
    status: DecisionStatus
    response_time: float
    raw_response: str
    parsed_decision: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class DecisionValidator(BaseModel):
    """决策验证器"""
    action: str  # buy, sell, hold
    confidence: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    reasoning: Optional[Dict[str, Any]] = None
    risk_level: Optional[str] = None
    expected_return: Optional[float] = None
    holding_period: Optional[str] = None
    alternative_scenarios: Optional[Dict[str, str]] = None

class LLMClient:
    """LLM客户端基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.last_request_time = None
    
    async def generate_decision(self, prompt: str) -> str:
        """生成决策"""
        raise NotImplementedError
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            'provider': self.config.provider.value,
            'model': self.config.model,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'avg_response_time': avg_response_time,
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'enabled': self.config.enabled
        }

class OpenAIClient(LLMClient):
    """OpenAI客户端"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    @monitor_performance
    async def generate_decision(self, prompt: str) -> str:
        """使用OpenAI生成决策"""
        start_time = time.time()
        self.request_count += 1
        self.last_request_time = datetime.now()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的股票交易分析师，请根据提供的信息进行分析并给出交易决策建议。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"OpenAI请求失败: {str(e)}")
            raise

class MockLLMClient(LLMClient):
    """模拟LLM客户端"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
    
    @monitor_performance
    async def generate_decision(self, prompt: str) -> str:
        """模拟生成决策"""
        start_time = time.time()
        self.request_count += 1
        self.last_request_time = datetime.now()
        
        try:
            # 模拟网络延迟
            await asyncio.sleep(0.5 + (self.request_count % 3) * 0.2)
            
            # 模拟决策生成
            import random
            actions = ['buy', 'sell', 'hold']
            action = random.choice(actions)
            confidence = round(random.uniform(0.6, 0.95), 2)
            
            mock_decision = {
                "action": action,
                "confidence": confidence,
                "target_price": round(100 + random.uniform(-10, 10), 2),
                "stop_loss": round(95 + random.uniform(-5, 5), 2),
                "take_profit": round(110 + random.uniform(-5, 10), 2),
                "position_size": round(random.uniform(0.1, 0.3), 2),
                "reasoning": {
                    "technical_analysis": f"基于技术指标分析，建议{action}",
                    "market_environment": "市场环境分析结果",
                    "risk_assessment": "风险评估结果",
                    "key_factors": ["因素1", "因素2", "因素3"]
                },
                "risk_level": random.choice(["low", "medium", "high"]),
                "expected_return": round(random.uniform(-0.1, 0.2), 3),
                "holding_period": random.choice(["1-2天", "3-5天", "1-2周"]),
                "alternative_scenarios": {
                    "bullish": "看涨情况下的策略",
                    "bearish": "看跌情况下的策略"
                }
            }
            
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            return f"```json\n{json.dumps(mock_decision, ensure_ascii=False, indent=2)}\n```"
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Mock LLM请求失败: {str(e)}")
            raise

class DecisionDispatcher:
    """决策分发器"""
    
    def __init__(self):
        self.llm_clients: Dict[str, LLMClient] = {}
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.response_cache: Dict[str, DecisionResponse] = {}
        self.cache_ttl = 300  # 缓存5分钟
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.running = False
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'start_time': None
        }
        
        # 初始化默认LLM客户端
        self._initialize_default_clients()
    
    def _initialize_default_clients(self):
        """初始化默认LLM客户端"""
        # Mock客户端用于测试
        mock_config = LLMConfig(
            provider=LLMProvider.LOCAL,
            model="mock-model",
            weight=1.0
        )
        self.add_llm_client("mock", MockLLMClient(mock_config))
        
        # 如果有OpenAI配置，添加OpenAI客户端
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            openai_config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-3.5-turbo",
                api_key=settings.OPENAI_API_KEY,
                weight=2.0
            )
            self.add_llm_client("openai", OpenAIClient(openai_config))
    
    def add_llm_client(self, name: str, client: LLMClient):
        """添加LLM客户端"""
        self.llm_clients[name] = client
        logger.info(f"添加LLM客户端: {name} ({client.config.provider.value})")
    
    def remove_llm_client(self, name: str):
        """移除LLM客户端"""
        if name in self.llm_clients:
            del self.llm_clients[name]
            logger.info(f"移除LLM客户端: {name}")
    
    def enable_client(self, name: str):
        """启用客户端"""
        if name in self.llm_clients:
            self.llm_clients[name].config.enabled = True
            logger.info(f"启用LLM客户端: {name}")
    
    def disable_client(self, name: str):
        """禁用客户端"""
        if name in self.llm_clients:
            self.llm_clients[name].config.enabled = False
            logger.info(f"禁用LLM客户端: {name}")
    
    @monitor_performance
    async def dispatch_decision_request(self, request: DecisionRequest) -> List[DecisionResponse]:
        """分发决策请求"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            logger.info(f"分发决策请求: {request.request_id} ({request.symbol})")
            
            # 获取可用的LLM客户端
            available_clients = [
                (name, client) for name, client in self.llm_clients.items()
                if client.config.enabled
            ]
            
            if not available_clients:
                raise ValueError("没有可用的LLM客户端")
            
            # 并行请求所有可用客户端
            tasks = []
            for name, client in available_clients:
                task = self._request_single_llm(request, name, client)
                tasks.append(task)
            
            # 等待所有请求完成
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理响应结果
            valid_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"LLM请求异常: {available_clients[i][0]}, {str(response)}")
                    # 创建失败响应
                    failed_response = DecisionResponse(
                        request_id=request.request_id,
                        provider=available_clients[i][1].config.provider,
                        model=available_clients[i][1].config.model,
                        status=DecisionStatus.FAILED,
                        response_time=0,
                        raw_response="",
                        error=str(response)
                    )
                    valid_responses.append(failed_response)
                else:
                    valid_responses.append(response)
            
            # 更新统计信息
            successful_count = sum(1 for r in valid_responses if r.status == DecisionStatus.COMPLETED)
            if successful_count > 0:
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1
            
            response_time = time.time() - start_time
            self.stats['avg_response_time'] = (
                (self.stats['avg_response_time'] * (self.stats['total_requests'] - 1) + response_time) /
                self.stats['total_requests']
            )
            
            logger.info(f"决策请求完成: {request.request_id}, 成功: {successful_count}/{len(valid_responses)}")
            return valid_responses
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"分发决策请求失败: {request.request_id}, 错误: {str(e)}")
            raise
    
    async def _request_single_llm(self, request: DecisionRequest, client_name: str, client: LLMClient) -> DecisionResponse:
        """请求单个LLM"""
        start_time = time.time()
        
        try:
            # 生成决策
            raw_response = await client.generate_decision(request.prompt)
            response_time = time.time() - start_time
            
            # 解析和验证响应
            parsed_decision, confidence = self._parse_and_validate_response(raw_response)
            
            status = DecisionStatus.COMPLETED if parsed_decision else DecisionStatus.INVALID
            
            response = DecisionResponse(
                request_id=request.request_id,
                provider=client.config.provider,
                model=client.config.model,
                status=status,
                response_time=response_time,
                raw_response=raw_response,
                parsed_decision=parsed_decision,
                confidence=confidence,
                metadata={'client_name': client_name}
            )
            
            logger.info(f"LLM请求成功: {client_name}, 耗时: {response_time:.2f}s")
            return response
            
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            logger.error(f"LLM请求超时: {client_name}")
            
            return DecisionResponse(
                request_id=request.request_id,
                provider=client.config.provider,
                model=client.config.model,
                status=DecisionStatus.TIMEOUT,
                response_time=response_time,
                raw_response="",
                error="Request timeout",
                metadata={'client_name': client_name}
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"LLM请求失败: {client_name}, 错误: {str(e)}")
            
            return DecisionResponse(
                request_id=request.request_id,
                provider=client.config.provider,
                model=client.config.model,
                status=DecisionStatus.FAILED,
                response_time=response_time,
                raw_response="",
                error=str(e),
                metadata={'client_name': client_name}
            )
    
    def _parse_and_validate_response(self, raw_response: str) -> tuple[Optional[Dict[str, Any]], float]:
        """解析和验证响应"""
        try:
            # 提取JSON内容
            json_content = self._extract_json_from_response(raw_response)
            if not json_content:
                return None, 0.0
            
            # 解析JSON
            decision_data = json.loads(json_content)
            
            # 验证决策格式
            validator = DecisionValidator(**decision_data)
            
            # 验证动作
            if validator.action not in ['buy', 'sell', 'hold']:
                logger.warning(f"无效的交易动作: {validator.action}")
                return None, 0.0
            
            # 验证置信度
            if not (0 <= validator.confidence <= 1):
                logger.warning(f"无效的置信度: {validator.confidence}")
                return None, 0.0
            
            return decision_data, validator.confidence
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            return None, 0.0
        except ValidationError as e:
            logger.error(f"决策验证失败: {str(e)}")
            return None, 0.0
        except Exception as e:
            logger.error(f"响应解析失败: {str(e)}")
            return None, 0.0
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """从响应中提取JSON内容"""
        try:
            # 查找JSON代码块
            import re
            
            # 匹配 ```json ... ``` 格式
            json_pattern = r'```json\s*(.*?)\s*```'
            match = re.search(json_pattern, response, re.DOTALL | re.IGNORECASE)
            
            if match:
                return match.group(1).strip()
            
            # 匹配 ``` ... ``` 格式
            code_pattern = r'```\s*(.*?)\s*```'
            match = re.search(code_pattern, response, re.DOTALL)
            
            if match:
                content = match.group(1).strip()
                # 检查是否为JSON格式
                if content.startswith('{') and content.endswith('}'):
                    return content
            
            # 直接查找JSON对象
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            
            if match:
                return match.group(0)
            
            return None
            
        except Exception as e:
            logger.error(f"提取JSON失败: {str(e)}")
            return None
    
    @monitor_performance
    def aggregate_decisions(self, responses: List[DecisionResponse]) -> Dict[str, Any]:
        """聚合多个决策结果"""
        try:
            # 过滤有效响应
            valid_responses = [
                r for r in responses 
                if r.status == DecisionStatus.COMPLETED and r.parsed_decision
            ]
            
            if not valid_responses:
                return {
                    'status': 'failed',
                    'error': 'No valid decisions available',
                    'responses_count': len(responses)
                }
            
            # 收集所有决策
            decisions = [r.parsed_decision for r in valid_responses]
            weights = [self.llm_clients.get(r.metadata.get('client_name', ''), type('obj', (object,), {'config': type('obj', (object,), {'weight': 1.0})()})).config.weight for r in valid_responses]
            
            # 聚合决策动作（加权投票）
            action_votes = {}
            for decision, weight in zip(decisions, weights):
                action = decision.get('action', 'hold')
                action_votes[action] = action_votes.get(action, 0) + weight
            
            # 选择得票最多的动作
            final_action = max(action_votes, key=action_votes.get)
            
            # 计算加权平均置信度
            total_weight = sum(weights)
            weighted_confidence = sum(
                decision.get('confidence', 0) * weight 
                for decision, weight in zip(decisions, weights)
            ) / total_weight
            
            # 聚合其他字段
            target_prices = [d.get('target_price') for d in decisions if d.get('target_price')]
            stop_losses = [d.get('stop_loss') for d in decisions if d.get('stop_loss')]
            take_profits = [d.get('take_profit') for d in decisions if d.get('take_profit')]
            position_sizes = [d.get('position_size') for d in decisions if d.get('position_size')]
            
            aggregated_decision = {
                'action': final_action,
                'confidence': round(weighted_confidence, 3),
                'target_price': round(sum(target_prices) / len(target_prices), 2) if target_prices else None,
                'stop_loss': round(sum(stop_losses) / len(stop_losses), 2) if stop_losses else None,
                'take_profit': round(sum(take_profits) / len(take_profits), 2) if take_profits else None,
                'position_size': round(sum(position_sizes) / len(position_sizes), 3) if position_sizes else None,
                'consensus_level': len(valid_responses),
                'total_responses': len(responses),
                'action_distribution': action_votes,
                'aggregation_method': 'weighted_voting',
                'timestamp': datetime.now().isoformat()
            }
            
            # 收集推理信息
            reasoning_summary = {
                'technical_analysis': [],
                'market_environment': [],
                'risk_assessment': [],
                'key_factors': []
            }
            
            for decision in decisions:
                reasoning = decision.get('reasoning', {})
                if isinstance(reasoning, dict):
                    for key in reasoning_summary:
                        if key in reasoning:
                            value = reasoning[key]
                            if isinstance(value, list):
                                reasoning_summary[key].extend(value)
                            elif isinstance(value, str):
                                reasoning_summary[key].append(value)
            
            # 去重并限制数量
            for key in reasoning_summary:
                reasoning_summary[key] = list(set(reasoning_summary[key]))[:5]
            
            aggregated_decision['reasoning_summary'] = reasoning_summary
            
            logger.info(f"决策聚合完成: {final_action}, 置信度: {weighted_confidence:.3f}, 共识度: {len(valid_responses)}/{len(responses)}")
            
            return {
                'status': 'success',
                'decision': aggregated_decision,
                'individual_responses': [
                    {
                        'provider': r.provider.value,
                        'model': r.model,
                        'confidence': r.confidence,
                        'response_time': r.response_time,
                        'decision': r.parsed_decision
                    }
                    for r in valid_responses
                ]
            }
            
        except Exception as e:
            logger.error(f"决策聚合失败: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'responses_count': len(responses)
            }
    
    def get_client_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        stats = {}
        for name, client in self.llm_clients.items():
            stats[name] = client.get_stats()
        return stats
    
    def get_dispatcher_stats(self) -> Dict[str, Any]:
        """获取分发器统计信息"""
        return {
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': (
                self.stats['successful_requests'] / max(self.stats['total_requests'], 1)
            ),
            'avg_response_time': self.stats['avg_response_time'],
            'active_clients': len([c for c in self.llm_clients.values() if c.config.enabled]),
            'total_clients': len(self.llm_clients)
        }

# 全局决策分发器实例
global_decision_dispatcher = DecisionDispatcher()

# 导出主要接口
__all__ = [
    'DecisionDispatcher',
    'DecisionRequest',
    'DecisionResponse',
    'LLMConfig',
    'LLMProvider',
    'DecisionStatus',
    'DecisionValidator',
    'global_decision_dispatcher'
]