"""
大模型统一网关
提供统一的LLM访问接口，支持多种模型提供商
"""
import asyncio
import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
from collections import deque
import random
import math

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"

class RequestPriority(Enum):
    """请求优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 8
    enabled: bool = True
    weight: float = 1.0  # 路由权重
    max_requests_per_minute: int = 60
    
@dataclass
class GatewayRequest:
    """网关请求"""
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False
    priority: RequestPriority = RequestPriority.NORMAL
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GatewayResponse:
    """网关响应"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int]
    response_time: float
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TokenBucket:
    """令牌桶限流算法"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = asyncio.Lock()  # 添加异步锁保证线程安全
    
    async def consume(self, tokens: int = 1) -> bool:
        """消费令牌（异步版本）"""
        async with self.lock:
            await self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def consume_sync(self, tokens: int = 1) -> bool:
        """消费令牌（同步版本）"""
        self._refill_sync()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    async def _refill(self):
        """补充令牌（异步版本）"""
        now = time.time()
        tokens_to_add = (now - self.last_refill) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def _refill_sync(self):
        """补充令牌（同步版本）"""
        now = time.time()
        tokens_to_add = (now - self.last_refill) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_available_tokens(self) -> int:
        """获取当前可用令牌数"""
        self._refill_sync()
        return int(self.tokens)

class ModelAdapter(ABC):
    """模型适配器基类"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'last_request_time': None,
            'error_rate': 0.0
        }
        self.rate_limiter = TokenBucket(
            capacity=config.max_requests_per_minute,
            refill_rate=config.max_requests_per_minute / 60.0
        )
    
    @abstractmethod
    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """生成响应"""
        pass
    
    @abstractmethod
    async def generate_stream(self, request: GatewayRequest) -> AsyncGenerator[str, None]:
        """流式生成响应"""
        pass
    
    def update_stats(self, success: bool, response_time: float):
        """更新统计信息"""
        self.stats['total_requests'] += 1
        self.stats['last_request_time'] = datetime.now()
        
        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        # 更新平均响应时间
        total_successful = self.stats['successful_requests']
        if total_successful > 0:
            current_avg = self.stats['avg_response_time']
            self.stats['avg_response_time'] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
        
        # 更新错误率
        total = self.stats['total_requests']
        self.stats['error_rate'] = self.stats['failed_requests'] / total if total > 0 else 0.0
    
    def get_health_score(self) -> float:
        """获取健康评分 (0-1)"""
        if self.stats['total_requests'] == 0:
            return 1.0
        
        # 基于错误率和响应时间计算健康评分
        error_penalty = self.stats['error_rate'] * 0.5
        
        # 响应时间惩罚 (超过2秒开始惩罚)
        avg_time = self.stats['avg_response_time']
        time_penalty = max(0, (avg_time - 2.0) / 10.0) * 0.3
        
        score = 1.0 - error_penalty - time_penalty
        return max(0.0, min(1.0, score))

class OpenAIAdapter(ModelAdapter):
    """OpenAI适配器"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
    
    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """生成响应"""
        if not await self.rate_limiter.consume():
            raise Exception("Rate limit exceeded")
        
        start_time = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=request.model or self.config.model_name,
                messages=request.messages,
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature,
                timeout=request.timeout or self.config.timeout
            )
            
            response_time = time.time() - start_time
            self.update_stats(True, response_time)
            
            return GatewayResponse(
                content=response.choices[0].message.content,
                model=response.model,
                provider=self.config.provider.value,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                response_time=response_time
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            self.update_stats(False, response_time)
            raise e
    
    async def generate_stream(self, request: GatewayRequest) -> AsyncGenerator[str, None]:
        """流式生成响应"""
        if not await self.rate_limiter.consume():
            raise Exception("Rate limit exceeded")
        
        try:
            stream = await self.client.chat.completions.create(
                model=request.model or self.config.model_name,
                messages=request.messages,
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature,
                stream=True,
                timeout=request.timeout or self.config.timeout
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise e

class DeepSeekAdapter(ModelAdapter):
    """DeepSeek适配器 - 使用aiohttp直接调用API"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.deepseek.com/v1"
        self.model_name = config.model_name or "deepseek-chat"
        self.session = None
    
    async def _get_session(self):
        """获取或创建aiohttp会话"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=90, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """生成响应"""
        if not await self.rate_limiter.consume():
            raise Exception("Rate limit exceeded")
        
        start_time = time.time()
        try:
            # 确定模型名称
            if request.model == "deepseek":
                model_name = "deepseek-chat"
            else:
                model_name = request.model or self.model_name
            
            # 构建请求数据
            data = {
                "model": model_name,
                "messages": request.messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature
            }
            
            # 详细日志：请求信息
            logger.info("=" * 80)
            logger.info("[DeepSeek API] 开始调用")
            logger.info(f"[DeepSeek API] URL: {self.base_url}/chat/completions")
            logger.info(f"[DeepSeek API] Model: {model_name}")
            logger.info(f"[DeepSeek API] API Key: {self.api_key[:10]}...{self.api_key[-4:]}")
            logger.info(f"[DeepSeek API] Messages count: {len(request.messages)}")
            for i, msg in enumerate(request.messages):
                logger.info(f"[DeepSeek API] Message {i+1} ({msg['role']}): {msg['content'][:100]}...")
            logger.info(f"[DeepSeek API] Max tokens: {data['max_tokens']}")
            logger.info(f"[DeepSeek API] Temperature: {data['temperature']}")
            
            # 发送请求
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            ) as resp:
                logger.info(f"[DeepSeek API] Response status: {resp.status}")
                
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"[DeepSeek API] Error response: {error_text}")
                    raise Exception(f"DeepSeek API error: {resp.status} - {error_text}")
                
                response_data = await resp.json()
            
            response_time = time.time() - start_time
            self.update_stats(True, response_time)
            
            # 详细日志：响应信息
            logger.info(f"[DeepSeek API] Response time: {response_time:.2f}秒")
            logger.info(f"[DeepSeek API] Response model: {response_data.get('model')}")
            
            usage = response_data.get('usage', {})
            logger.info(f"[DeepSeek API] Token usage:")
            logger.info(f"  - Prompt tokens: {usage.get('prompt_tokens', 0)}")
            logger.info(f"  - Completion tokens: {usage.get('completion_tokens', 0)}")
            logger.info(f"  - Total tokens: {usage.get('total_tokens', 0)}")
            
            content = response_data['choices'][0]['message']['content']
            logger.info(f"[DeepSeek API] Response content length: {len(content)}")
            logger.info(f"[DeepSeek API] Response content preview:")
            logger.info(f"{content[:500]}")
            logger.info("=" * 80)
            
            return GatewayResponse(
                content=content,
                model=response_data['model'],
                provider=self.config.provider.value,
                usage=usage,
                response_time=response_time
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            self.update_stats(False, response_time)
            logger.error(f"[DeepSeek API] Exception: {e}")
            logger.error("=" * 80)
            raise e
    
    async def generate_stream(self, request: GatewayRequest) -> AsyncGenerator[str, None]:
        """流式生成响应"""
        if not await self.rate_limiter.consume():
            raise Exception("Rate limit exceeded")
        
        try:
            model_name = request.model or self.model_name
            
            data = {
                "model": model_name,
                "messages": request.messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                "stream": True
            }
            
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            ) as resp:
                async for line in resp.content:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str != '[DONE]':
                                try:
                                    chunk_data = json.loads(data_str)
                                    if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                        delta = chunk_data['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            yield delta['content']
                                except json.JSONDecodeError:
                                    continue
        
        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            raise e

class QwenAdapter(ModelAdapter):
    """通义千问适配器"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://dashscope.aliyuncs.com/api/v1"
        self.session = None
    
    async def _get_session(self):
        """获取HTTP会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """生成响应"""
        if not await self.rate_limiter.consume():
            raise Exception("Rate limit exceeded")
        
        start_time = time.time()
        session = await self._get_session()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": request.model or self.config.model_name or "qwen-turbo",
                "input": {
                    "messages": request.messages
                },
                "parameters": {
                    "max_tokens": request.max_tokens or self.config.max_tokens,
                    "temperature": request.temperature or self.config.temperature
                }
            }
            
            timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
            
            async with session.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=payload,
                headers=headers,
                timeout=timeout
            ) as response:
                result = await response.json()
                
                if response.status != 200:
                    raise Exception(f"Qwen API error: {result}")
                
                response_time = time.time() - start_time
                self.update_stats(True, response_time)
                
                return GatewayResponse(
                    content=result["output"]["text"],
                    model=payload["model"],
                    provider=self.config.provider.value,
                    usage=result.get("usage", {}),
                    response_time=response_time
                )
        
        except Exception as e:
            response_time = time.time() - start_time
            self.update_stats(False, response_time)
            raise e
    
    async def generate_stream(self, request: GatewayRequest) -> AsyncGenerator[str, None]:
        """流式生成响应"""
        if not await self.rate_limiter.consume():
            raise Exception("Rate limit exceeded")
        
        session = await self._get_session()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": request.model or self.config.model_name or "qwen-turbo",
                "input": {
                    "messages": request.messages
                },
                "parameters": {
                    "max_tokens": request.max_tokens or self.config.max_tokens,
                    "temperature": request.temperature or self.config.temperature,
                    "incremental_output": True
                }
            }
            
            timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
            
            async with session.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=payload,
                headers=headers,
                timeout=timeout
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'output' in data and 'text' in data['output']:
                                yield data['output']['text']
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"Qwen streaming error: {e}")
            raise e

class RequestQueue:
    """请求优先级队列"""
    
    def __init__(self, max_size: int = 1000):
        self.queues = {
            RequestPriority.URGENT: deque(),
            RequestPriority.HIGH: deque(),
            RequestPriority.NORMAL: deque(),
            RequestPriority.LOW: deque()
        }
        self.max_size = max_size
        self.lock = asyncio.Lock()
        self.request_timestamps = {}  # 记录请求时间戳用于超时检查
    
    async def put(self, request: GatewayRequest, callback) -> bool:
        """添加请求到队列"""
        async with self.lock:
            # 检查队列是否已满
            if self.size() >= self.max_size:
                # 如果是低优先级请求且队列满了，直接拒绝
                if request.priority == RequestPriority.LOW:
                    return False
                # 否则移除一个低优先级请求
                if self.queues[RequestPriority.LOW]:
                    removed_item = self.queues[RequestPriority.LOW].popleft()
                    if removed_item:
                        removed_request, removed_callback = removed_item
                        # 通知被移除的请求
                        try:
                            await removed_callback(GatewayResponse(
                                content="",
                                model="",
                                provider="",
                                usage={},
                                response_time=0.0,
                                success=False,
                                error="Request dropped due to queue overflow"
                            ))
                        except Exception as e:
                            logger.warning(f"Failed to notify dropped request: {e}")
            
            # 添加请求到对应优先级队列
            request_id = id(request)
            self.request_timestamps[request_id] = time.time()
            self.queues[request.priority].append((request, callback, request_id))
            return True
    
    async def get(self) -> Optional[tuple]:
        """从队列中获取请求（按优先级）"""
        async with self.lock:
            # 清理超时请求
            await self._cleanup_expired_requests()
            
            # 按优先级获取请求
            for priority in [RequestPriority.URGENT, RequestPriority.HIGH, 
                            RequestPriority.NORMAL, RequestPriority.LOW]:
                if self.queues[priority]:
                    item = self.queues[priority].popleft()
                    if len(item) == 3:  # 包含request_id
                        request, callback, request_id = item
                        # 清理时间戳记录
                        self.request_timestamps.pop(request_id, None)
                        return (request, callback)
                    else:  # 兼容旧格式
                        return item
            return None
    
    async def _cleanup_expired_requests(self):
        """清理超时请求"""
        current_time = time.time()
        timeout = 8.0  # 8秒超时
        
        for priority_queue in self.queues.values():
            expired_items = []
            remaining_items = deque()
            
            while priority_queue:
                item = priority_queue.popleft()
                if len(item) == 3:
                    request, callback, request_id = item
                    request_time = self.request_timestamps.get(request_id, current_time)
                    
                    if current_time - request_time > timeout:
                        expired_items.append((request, callback))
                        self.request_timestamps.pop(request_id, None)
                    else:
                        remaining_items.append(item)
                else:
                    # 兼容旧格式，假设没有超时
                    remaining_items.append(item)
            
            # 恢复未超时的请求
            priority_queue.extend(remaining_items)
            
            # 通知超时的请求
            for request, callback in expired_items:
                try:
                    await callback(GatewayResponse(
                        content="",
                        model="",
                        provider="",
                        usage={},
                        response_time=0.0,
                        success=False,
                        error="Request timeout in queue"
                    ))
                except Exception as e:
                    logger.warning(f"Failed to notify timeout request: {e}")
    
    def size(self) -> int:
        """获取队列总大小"""
        return sum(len(queue) for queue in self.queues.values())
    
    def get_priority_sizes(self) -> Dict[str, int]:
        """获取各优先级队列大小"""
        return {
            priority.name: len(queue) 
            for priority, queue in self.queues.items()
        }

class LLMGateway:
    """大模型统一网关"""
    
    def __init__(self):
        self.adapters: Dict[str, ModelAdapter] = {}
        self.request_queue = RequestQueue()
        self.is_processing = False
        self.retry_delays = [1, 2, 4, 8]  # 指数退避重试延迟
        self.circuit_breakers: Dict[str, Dict] = {}  # 熔断器状态
        self.load_balancer_state = {}  # 负载均衡状态
        self.performance_history = {}  # 性能历史记录
        
    def register_adapter(self, name: str, adapter: ModelAdapter):
        """注册适配器"""
        self.adapters[name] = adapter
        # 初始化熔断器状态
        self.circuit_breakers[name] = {
            'state': 'closed',  # closed, open, half_open
            'failure_count': 0,
            'last_failure_time': None,
            'failure_threshold': 5,  # 失败阈值
            'recovery_timeout': 60,  # 恢复超时时间（秒）
        }
        # 初始化负载均衡状态
        self.load_balancer_state[name] = {
            'request_count': 0,
            'last_request_time': None,
            'avg_response_time': 0.0,
        }
        # 初始化性能历史
        self.performance_history[name] = deque(maxlen=100)
        logger.info(f"Registered adapter: {name}")
    
    def _check_circuit_breaker(self, adapter_name: str) -> bool:
        """检查熔断器状态"""
        breaker = self.circuit_breakers.get(adapter_name)
        if not breaker:
            return True
        
        current_time = time.time()
        
        # 如果熔断器开启，检查是否可以进入半开状态
        if breaker['state'] == 'open':
            if (breaker['last_failure_time'] and 
                current_time - breaker['last_failure_time'] > breaker['recovery_timeout']):
                breaker['state'] = 'half_open'
                logger.info(f"Circuit breaker for {adapter_name} entering half-open state")
                return True
            return False
        
        return True
    
    def _update_circuit_breaker(self, adapter_name: str, success: bool):
        """更新熔断器状态"""
        breaker = self.circuit_breakers.get(adapter_name)
        if not breaker:
            return
        
        if success:
            if breaker['state'] == 'half_open':
                breaker['state'] = 'closed'
                breaker['failure_count'] = 0
                logger.info(f"Circuit breaker for {adapter_name} closed")
            elif breaker['state'] == 'closed':
                breaker['failure_count'] = max(0, breaker['failure_count'] - 1)
        else:
            breaker['failure_count'] += 1
            breaker['last_failure_time'] = time.time()
            
            if breaker['failure_count'] >= breaker['failure_threshold']:
                breaker['state'] = 'open'
                logger.warning(f"Circuit breaker for {adapter_name} opened due to failures")
    
    def _update_performance_metrics(self, adapter_name: str, response_time: float, success: bool):
        """更新性能指标"""
        # 更新负载均衡状态
        lb_state = self.load_balancer_state.get(adapter_name)
        if lb_state:
            lb_state['request_count'] += 1
            lb_state['last_request_time'] = time.time()
            
            # 计算平均响应时间（指数移动平均）
            alpha = 0.1  # 平滑因子
            if lb_state['avg_response_time'] == 0:
                lb_state['avg_response_time'] = response_time
            else:
                lb_state['avg_response_time'] = (
                    alpha * response_time + (1 - alpha) * lb_state['avg_response_time']
                )
        
        # 更新性能历史
        history = self.performance_history.get(adapter_name)
        if history is not None:
            history.append({
                'timestamp': time.time(),
                'response_time': response_time,
                'success': success
            })
    
    def _calculate_adapter_score(self, adapter_name: str, adapter: ModelAdapter) -> float:
        """计算适配器综合评分"""
        if not self._check_circuit_breaker(adapter_name):
            return 0.0  # 熔断器开启时评分为0
        
        # 基础健康评分
        health_score = adapter.get_health_score()
        
        # 负载均衡评分（请求数越少评分越高）
        lb_state = self.load_balancer_state.get(adapter_name, {})
        request_count = lb_state.get('request_count', 0)
        avg_response_time = lb_state.get('avg_response_time', 1.0)
        
        # 计算负载评分（反比例）
        max_requests = max([s.get('request_count', 1) for s in self.load_balancer_state.values()] + [1])
        load_score = 1.0 - (request_count / max_requests) if max_requests > 0 else 1.0
        
        # 计算响应时间评分（反比例）
        time_score = 1.0 / (1.0 + avg_response_time)
        
        # 综合评分
        final_score = (
            health_score * 0.4 +      # 健康状态权重40%
            load_score * 0.3 +        # 负载均衡权重30%
            time_score * 0.2 +        # 响应时间权重20%
            adapter.config.weight * 0.1  # 配置权重10%
        )
        
        return final_score
        
    def _select_adapter(self, request: GatewayRequest) -> ModelAdapter:
        """智能选择适配器"""
        available_adapters = [
            (name, adapter) for name, adapter in self.adapters.items()
            if adapter.config.enabled and self._check_circuit_breaker(name)
        ]
        
        if not available_adapters:
            raise Exception("No available adapters")
        
        # 如果请求中指定了模型，优先选择对应的适配器
        if request.model:
            # 直接匹配适配器名称
            for name, adapter in available_adapters:
                if name == request.model:
                    logger.debug(f"Selected specific adapter: {name}")
                    return adapter
            
            # 如果没有直接匹配，尝试匹配模型名称
            for name, adapter in available_adapters:
                if adapter.config.model_name == request.model:
                    logger.debug(f"Selected adapter by model name: {name} (model: {adapter.config.model_name})")
                    return adapter
            
            logger.warning(f"Requested model '{request.model}' not found, falling back to automatic selection")
        
        # 计算每个适配器的综合评分
        scored_adapters = []
        for name, adapter in available_adapters:
            score = self._calculate_adapter_score(name, adapter)
            scored_adapters.append((score, name, adapter))
        
        # 按评分排序
        scored_adapters.sort(key=lambda x: x[0], reverse=True)
        
        # 使用加权随机选择，给高评分适配器更高概率
        total_score = sum(s[0] for s in scored_adapters)
        if total_score == 0:
            return scored_adapters[0][2]  # 如果所有评分为0，选择第一个
        
        rand = random.uniform(0, total_score)
        current_score = 0
        
        for score, name, adapter in scored_adapters:
            current_score += score
            if rand <= current_score:
                logger.debug(f"Selected adapter: {name} (score: {score:.3f})")
                return adapter
        
        return scored_adapters[0][2]  # 默认返回第一个
    
    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """生成响应"""
        selected_adapter = None
        adapter_name = None
        
        for attempt in range(len(self.retry_delays) + 1):
            try:
                selected_adapter = self._select_adapter(request)
                # 找到适配器名称
                adapter_name = next(
                    name for name, adapter in self.adapters.items() 
                    if adapter is selected_adapter
                )
                
                start_time = time.time()
                response = await selected_adapter.generate(request)
                response_time = time.time() - start_time
                
                # 更新性能指标和熔断器状态
                self._update_performance_metrics(adapter_name, response_time, True)
                self._update_circuit_breaker(adapter_name, True)
                
                return response
            
            except Exception as e:
                response_time = time.time() - start_time if 'start_time' in locals() else 0
                
                # 更新性能指标和熔断器状态
                if adapter_name:
                    self._update_performance_metrics(adapter_name, response_time, False)
                    self._update_circuit_breaker(adapter_name, False)
                
                if attempt < len(self.retry_delays):
                    delay = self.retry_delays[attempt]
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after all retries: {e}")
                    return GatewayResponse(
                        content="",
                        model="",
                        provider="",
                        usage={},
                        response_time=0.0,
                        success=False,
                        error=str(e)
                    )
    
    async def generate_stream(self, request: GatewayRequest) -> AsyncGenerator[str, None]:
        """流式生成响应"""
        for attempt in range(len(self.retry_delays) + 1):
            try:
                adapter = self._select_adapter(request)
                async for chunk in adapter.generate_stream(request):
                    yield chunk
                return
            
            except Exception as e:
                if attempt < len(self.retry_delays):
                    delay = self.retry_delays[attempt]
                    logger.warning(f"Stream request failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Stream request failed after all retries: {e}")
                    yield f"Error: {str(e)}"
                    return
    
    def get_stats(self) -> Dict[str, Any]:
        """获取网关统计信息"""
        adapter_stats = {}
        for name, adapter in self.adapters.items():
            breaker = self.circuit_breakers.get(name, {})
            lb_state = self.load_balancer_state.get(name, {})
            history = self.performance_history.get(name, deque())
            
            # 计算最近成功率
            recent_requests = list(history)[-20:]  # 最近20个请求
            success_rate = (
                sum(1 for r in recent_requests if r['success']) / len(recent_requests)
                if recent_requests else 0.0
            )
            
            adapter_stats[name] = {
                'config': {
                    'provider': adapter.config.provider.value,
                    'model': adapter.config.model_name,
                    'enabled': adapter.config.enabled,
                    'weight': adapter.config.weight
                },
                'circuit_breaker_state': breaker.get('state', 'unknown'),
                'failure_count': breaker.get('failure_count', 0),
                'request_count': lb_state.get('request_count', 0),
                'avg_response_time': lb_state.get('avg_response_time', 0.0),
                'success_rate': success_rate,
                'health_score': adapter.get_health_score(),
                'overall_score': self._calculate_adapter_score(name, adapter),
                'stats': adapter.stats
            }
        
        return {
            'total_adapters': len(self.adapters),
            'enabled_adapters': len([
                a for name, a in self.adapters.items() 
                if a.config.enabled and self._check_circuit_breaker(name)
            ]),
            'queue_size': self.request_queue.size(),
            'adapters': adapter_stats
        }

# 全局网关实例
gateway = LLMGateway()

def initialize_gateway():
    """初始化网关"""
    from ..config.settings import settings
    
    # 优先注册DeepSeek适配器作为主要LLM
    if hasattr(settings, 'DEEPSEEK_API_KEY') and settings.DEEPSEEK_API_KEY:
        deepseek_config = ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_name=getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat'),
            api_key=settings.DEEPSEEK_API_KEY,
            base_url='https://api.deepseek.com/v1',
            timeout=60,  # 增加DeepSeek的超时时间到60秒
            weight=10.0  # 给DeepSeek最高权重，作为默认选择
        )
        gateway.register_adapter('deepseek', DeepSeekAdapter(deepseek_config))
        logger.info("DeepSeek adapter registered as primary LLM")
    
    # 注册OpenAI适配器（备用，可选）
    if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        try:
            openai_config = ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                api_key=settings.OPENAI_API_KEY,
                base_url=getattr(settings, 'OPENAI_BASE_URL', None),
                weight=1.0  # 较低权重
            )
            gateway.register_adapter('openai', OpenAIAdapter(openai_config))
            logger.info("OpenAI adapter registered as backup LLM")
        except ImportError:
            logger.warning("OpenAI library not installed, skipping OpenAI adapter")
    
    # 注册通义千问适配器
    if hasattr(settings, 'QWEN_API_KEY'):
        qwen_config = ModelConfig(
            provider=ModelProvider.QWEN,
            model_name='qwen-turbo',
            api_key=settings.QWEN_API_KEY
        )
        gateway.register_adapter('qwen', QwenAdapter(qwen_config))
    
    logger.info("LLM Gateway initialized successfully")

__all__ = [
    'LLMGateway',
    'GatewayRequest', 
    'GatewayResponse',
    'ModelProvider',
    'RequestPriority',
    'gateway',
    'initialize_gateway'
]