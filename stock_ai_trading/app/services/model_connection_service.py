"""
模型连接管理服务
支持多种AI模型的连接配置和管理
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import json
import time

from .encryption_service import encryption_service

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """模型类型枚举"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CLAUDE = "claude"
    CUSTOM = "custom"

@dataclass
class ModelConfig:
    """模型配置数据类"""
    model_id: str
    model_type: ModelType
    name: str
    api_key: str
    base_url: str
    model_version: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30
    extra_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}

@dataclass
class ModelResponse:
    """模型响应数据类"""
    success: bool
    content: str = ""
    usage: Dict[str, int] = None
    response_time: float = 0.0
    error_message: str = ""
    error_code: str = ""
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

class BaseModelConnector(ABC):
    """模型连接器基类"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def send_message(self, message: str, **kwargs) -> ModelResponse:
        """发送消息到模型"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass
    
    async def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            response = await self.send_message("Hello", test_mode=True)
            return response.success
        except Exception as e:
            logger.error(f"Connection test failed for {self.config.model_id}: {e}")
            return False

class DeepSeekConnector(BaseModelConnector):
    """DeepSeek模型连接器"""
    
    def validate_config(self) -> bool:
        """验证DeepSeek配置"""
        required_fields = [self.config.api_key, self.config.base_url]
        return all(field for field in required_fields)
    
    async def send_message(self, message: str, **kwargs) -> ModelResponse:
        """发送消息到DeepSeek API"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.config.model_version or "deepseek-chat",
                "messages": [{"role": "user", "content": message}],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                **self.config.extra_params
            }
            
            async with self.session.post(
                f"{self.config.base_url}/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return ModelResponse(
                        success=True,
                        content=data["choices"][0]["message"]["content"],
                        usage=data.get("usage", {}),
                        response_time=response_time
                    )
                else:
                    error_text = await response.text()
                    return ModelResponse(
                        success=False,
                        error_message=error_text,
                        error_code=f"HTTP_{response.status}",
                        response_time=response_time
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"DeepSeek API error: {e}")
            return ModelResponse(
                success=False,
                error_message=str(e),
                error_code="CONNECTION_ERROR",
                response_time=response_time
            )

class OpenAIConnector(BaseModelConnector):
    """OpenAI ChatGPT模型连接器"""
    
    def validate_config(self) -> bool:
        """验证OpenAI配置"""
        required_fields = [self.config.api_key, self.config.base_url]
        return all(field for field in required_fields)
    
    async def send_message(self, message: str, **kwargs) -> ModelResponse:
        """发送消息到OpenAI API"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.config.model_version or "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": message}],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                **self.config.extra_params
            }
            
            async with self.session.post(
                f"{self.config.base_url}/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return ModelResponse(
                        success=True,
                        content=data["choices"][0]["message"]["content"],
                        usage=data.get("usage", {}),
                        response_time=response_time
                    )
                else:
                    error_text = await response.text()
                    return ModelResponse(
                        success=False,
                        error_message=error_text,
                        error_code=f"HTTP_{response.status}",
                        response_time=response_time
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"OpenAI API error: {e}")
            return ModelResponse(
                success=False,
                error_message=str(e),
                error_code="CONNECTION_ERROR",
                response_time=response_time
            )

class ClaudeConnector(BaseModelConnector):
    """Claude模型连接器"""
    
    def validate_config(self) -> bool:
        """验证Claude配置"""
        required_fields = [self.config.api_key, self.config.base_url]
        return all(field for field in required_fields)
    
    async def send_message(self, message: str, **kwargs) -> ModelResponse:
        """发送消息到Claude API"""
        start_time = time.time()
        
        try:
            headers = {
                "x-api-key": self.config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.config.model_version or "claude-3-sonnet-20240229",
                "max_tokens": self.config.max_tokens,
                "messages": [{"role": "user", "content": message}],
                **self.config.extra_params
            }
            
            async with self.session.post(
                f"{self.config.base_url}/v1/messages",
                headers=headers,
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return ModelResponse(
                        success=True,
                        content=data["content"][0]["text"],
                        usage=data.get("usage", {}),
                        response_time=response_time
                    )
                else:
                    error_text = await response.text()
                    return ModelResponse(
                        success=False,
                        error_message=error_text,
                        error_code=f"HTTP_{response.status}",
                        response_time=response_time
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Claude API error: {e}")
            return ModelResponse(
                success=False,
                error_message=str(e),
                error_code="CONNECTION_ERROR",
                response_time=response_time
            )

class CustomConnector(BaseModelConnector):
    """自定义模型连接器"""
    
    def validate_config(self) -> bool:
        """验证自定义模型配置"""
        return bool(self.config.base_url)
    
    async def send_message(self, message: str, **kwargs) -> ModelResponse:
        """发送消息到自定义模型API"""
        start_time = time.time()
        
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # 如果有API密钥，添加到请求头
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            # 构建通用的请求负载
            payload = {
                "message": message,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                **self.config.extra_params
            }
            
            # 如果有模型版本，添加到负载中
            if self.config.model_version:
                payload["model"] = self.config.model_version
            
            async with self.session.post(
                self.config.base_url,
                headers=headers,
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # 尝试从不同的字段中提取内容
                    content = ""
                    if "content" in data:
                        content = data["content"]
                    elif "response" in data:
                        content = data["response"]
                    elif "text" in data:
                        content = data["text"]
                    elif "message" in data:
                        content = data["message"]
                    
                    return ModelResponse(
                        success=True,
                        content=content,
                        usage=data.get("usage", {}),
                        response_time=response_time
                    )
                else:
                    error_text = await response.text()
                    return ModelResponse(
                        success=False,
                        error_message=error_text,
                        error_code=f"HTTP_{response.status}",
                        response_time=response_time
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Custom model API error: {e}")
            return ModelResponse(
                success=False,
                error_message=str(e),
                error_code="CONNECTION_ERROR",
                response_time=response_time
            )

class ModelConnectionService:
    """模型连接管理服务"""
    
    def __init__(self):
        self.connectors: Dict[str, BaseModelConnector] = {}
        self.connector_classes = {
            ModelType.DEEPSEEK: DeepSeekConnector,
            ModelType.OPENAI: OpenAIConnector,
            ModelType.CLAUDE: ClaudeConnector,
            ModelType.CUSTOM: CustomConnector
        }
    
    def register_model(self, config: ModelConfig) -> bool:
        """注册模型连接"""
        try:
            # 解密API密钥
            if config.api_key:
                try:
                    decrypted_key = encryption_service.decrypt(config.api_key)
                    config.api_key = decrypted_key
                except Exception as e:
                    logger.warning(f"Failed to decrypt API key for {config.model_id}, using as plain text: {e}")
            
            # 创建连接器
            connector_class = self.connector_classes.get(config.model_type)
            if not connector_class:
                logger.error(f"Unsupported model type: {config.model_type}")
                return False
            
            connector = connector_class(config)
            
            # 验证配置
            if not connector.validate_config():
                logger.error(f"Invalid configuration for model {config.model_id}")
                return False
            
            self.connectors[config.model_id] = connector
            logger.info(f"Model {config.model_id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register model {config.model_id}: {e}")
            return False
    
    def unregister_model(self, model_id: str) -> bool:
        """注销模型连接"""
        if model_id in self.connectors:
            del self.connectors[model_id]
            logger.info(f"Model {model_id} unregistered")
            return True
        return False
    
    def get_connector(self, model_id: str) -> Optional[BaseModelConnector]:
        """获取模型连接器"""
        return self.connectors.get(model_id)
    
    def list_models(self) -> List[str]:
        """列出所有已注册的模型"""
        return list(self.connectors.keys())
    
    async def send_message(self, model_id: str, message: str, **kwargs) -> ModelResponse:
        """发送消息到指定模型"""
        connector = self.get_connector(model_id)
        if not connector:
            return ModelResponse(
                success=False,
                error_message=f"Model {model_id} not found",
                error_code="MODEL_NOT_FOUND"
            )
        
        try:
            async with connector:
                return await connector.send_message(message, **kwargs)
        except Exception as e:
            logger.error(f"Error sending message to {model_id}: {e}")
            return ModelResponse(
                success=False,
                error_message=str(e),
                error_code="SEND_ERROR"
            )
    
    async def test_connection(self, model_id: str) -> bool:
        """测试模型连接"""
        connector = self.get_connector(model_id)
        if not connector:
            return False
        
        try:
            async with connector:
                return await connector.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed for {model_id}: {e}")
            return False
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """测试所有模型连接"""
        results = {}
        
        # 并发测试所有连接
        tasks = []
        model_ids = []
        
        for model_id in self.connectors.keys():
            tasks.append(self.test_connection(model_id))
            model_ids.append(model_id)
        
        if tasks:
            test_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for model_id, result in zip(model_ids, test_results):
                if isinstance(result, Exception):
                    results[model_id] = False
                    logger.error(f"Connection test error for {model_id}: {result}")
                else:
                    results[model_id] = result
        
        return results
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        connector = self.get_connector(model_id)
        if not connector:
            return None
        
        config = connector.config
        return {
            "model_id": config.model_id,
            "model_type": config.model_type.value,
            "name": config.name,
            "base_url": config.base_url,
            "model_version": config.model_version,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "timeout": config.timeout
        }
    
    def update_model_config(self, model_id: str, **updates) -> bool:
        """更新模型配置"""
        connector = self.get_connector(model_id)
        if not connector:
            return False
        
        try:
            config = connector.config
            
            # 更新允许的字段
            updatable_fields = [
                'name', 'model_version', 'max_tokens', 
                'temperature', 'timeout', 'extra_params'
            ]
            
            for field, value in updates.items():
                if field in updatable_fields:
                    setattr(config, field, value)
            
            # 重新验证配置
            if not connector.validate_config():
                logger.error(f"Invalid updated configuration for model {model_id}")
                return False
            
            logger.info(f"Model {model_id} configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update model {model_id} configuration: {e}")
            return False

# 全局模型连接服务实例
model_connection_service = ModelConnectionService()