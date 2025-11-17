# -*- coding: utf-8 -*-
"""
LLM网关API模块
提供大语言模型网关服务的REST API接口
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
import json
import logging
import asyncio
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/llm", tags=["LLM网关"])

# 数据模型定义
class LLMResponse(BaseModel):
    """LLM响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应信息")

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="角色: system, user, assistant")
    content: str = Field(..., description="消息内容")

class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage] = Field(..., description="消息列表")
    model: Optional[str] = Field(None, description="模型名称")
    max_tokens: Optional[int] = Field(None, description="最大令牌数")
    temperature: Optional[float] = Field(None, description="温度参数")
    stream: bool = Field(False, description="是否流式响应")
    provider: Optional[str] = Field(None, description="LLM提供商")

class CompletionRequest(BaseModel):
    """文本补全请求模型"""
    prompt: str = Field(..., description="提示文本")
    model: Optional[str] = Field(None, description="模型名称")
    max_tokens: Optional[int] = Field(None, description="最大令牌数")
    temperature: Optional[float] = Field(None, description="温度参数")
    provider: Optional[str] = Field(None, description="LLM提供商")

class ModelInfo(BaseModel):
    """模型信息模型"""
    id: str = Field(..., description="模型ID")
    name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="提供商")
    description: Optional[str] = Field(None, description="模型描述")
    max_tokens: int = Field(..., description="最大令牌数")
    pricing: Optional[Dict[str, float]] = Field(None, description="定价信息")
    available: bool = Field(..., description="是否可用")

class ProviderConfig(BaseModel):
    """提供商配置模型"""
    name: str = Field(..., description="提供商名称")
    api_key: str = Field(..., description="API密钥")
    base_url: Optional[str] = Field(None, description="基础URL")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=1, description="优先级")
    rate_limit: Optional[int] = Field(None, description="速率限制")

# 全局LLM网关管理器
class LLMGateway:
    def __init__(self):
        self.providers = {}
        self.models = {}
        self.request_history = []
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0
        }
        
    def add_provider(self, provider_name: str, config: Dict[str, Any]):
        """添加LLM提供商"""
        self.providers[provider_name] = {
            "name": provider_name,
            "config": config,
            "enabled": config.get("enabled", True),
            "priority": config.get("priority", 1),
            "rate_limit": config.get("rate_limit"),
            "request_count": 0,
            "error_count": 0,
            "last_request": None
        }
        
    def remove_provider(self, provider_name: str):
        """移除LLM提供商"""
        if provider_name in self.providers:
            del self.providers[provider_name]
            
    def get_provider_status(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """获取提供商状态"""
        return self.providers.get(provider_name)
        
    def get_all_providers(self) -> List[Dict[str, Any]]:
        """获取所有提供商"""
        return list(self.providers.values())
        
    def add_model(self, model_id: str, model_info: Dict[str, Any]):
        """添加模型"""
        self.models[model_id] = {
            "id": model_id,
            "name": model_info.get("name", model_id),
            "provider": model_info.get("provider"),
            "description": model_info.get("description"),
            "max_tokens": model_info.get("max_tokens", 4096),
            "pricing": model_info.get("pricing"),
            "available": model_info.get("available", True),
            "request_count": 0,
            "success_count": 0,
            "error_count": 0
        }
        
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用模型列表"""
        return [model for model in self.models.values() if model["available"]]
        
    async def chat_completion(self, request: ChatRequest) -> Dict[str, Any]:
        """聊天补全"""
        try:
            # 记录请求
            request_id = str(uuid.uuid4())
            self.stats["total_requests"] += 1
            
            # 模拟聊天补全
            response_content = f"这是对消息的回复: {request.messages[-1].content if request.messages else '无消息'}"
            
            # 模拟处理延迟
            await asyncio.sleep(0.5)
            
            # 记录成功
            self.stats["successful_requests"] += 1
            self.stats["total_tokens"] += len(response_content)
            
            # 记录历史
            self.request_history.append({
                "request_id": request_id,
                "type": "chat_completion",
                "model": request.model or "default",
                "provider": request.provider or "default",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "input_tokens": sum(len(msg.content) for msg in request.messages),
                "output_tokens": len(response_content)
            })
            
            return {
                "id": request_id,
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": request.model or "default",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": sum(len(msg.content) for msg in request.messages),
                    "completion_tokens": len(response_content),
                    "total_tokens": sum(len(msg.content) for msg in request.messages) + len(response_content)
                }
            }
            
        except Exception as e:
            # 记录失败
            self.stats["failed_requests"] += 1
            
            # 记录历史
            self.request_history.append({
                "request_id": request_id,
                "type": "chat_completion",
                "model": request.model or "default",
                "provider": request.provider or "default",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            })
            
            raise e
            
    async def text_completion(self, request: CompletionRequest) -> Dict[str, Any]:
        """文本补全"""
        try:
            # 记录请求
            request_id = str(uuid.uuid4())
            self.stats["total_requests"] += 1
            
            # 模拟文本补全
            response_content = f"基于提示 '{request.prompt}' 的补全内容"
            
            # 模拟处理延迟
            await asyncio.sleep(0.3)
            
            # 记录成功
            self.stats["successful_requests"] += 1
            self.stats["total_tokens"] += len(response_content)
            
            # 记录历史
            self.request_history.append({
                "request_id": request_id,
                "type": "text_completion",
                "model": request.model or "default",
                "provider": request.provider or "default",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "input_tokens": len(request.prompt),
                "output_tokens": len(response_content)
            })
            
            return {
                "id": request_id,
                "object": "text_completion",
                "created": int(datetime.now().timestamp()),
                "model": request.model or "default",
                "choices": [{
                    "text": response_content,
                    "index": 0,
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(request.prompt),
                    "completion_tokens": len(response_content),
                    "total_tokens": len(request.prompt) + len(response_content)
                }
            }
            
        except Exception as e:
            # 记录失败
            self.stats["failed_requests"] += 1
            
            # 记录历史
            self.request_history.append({
                "request_id": request_id,
                "type": "text_completion",
                "model": request.model or "default",
                "provider": request.provider or "default",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            })
            
            raise e
            
    def get_gateway_stats(self) -> Dict[str, Any]:
        """获取网关统计信息"""
        return {
            "stats": self.stats,
            "providers_count": len(self.providers),
            "models_count": len(self.models),
            "active_providers": len([p for p in self.providers.values() if p["enabled"]]),
            "available_models": len([m for m in self.models.values() if m["available"]])
        }

# 全局网关实例
global_gateway = LLMGateway()

@router.get("/status", summary="获取网关状态")
async def get_gateway_status():
    """获取LLM网关运行状态"""
    try:
        stats = global_gateway.get_gateway_stats()
        
        return LLMResponse(
            success=True,
            message="获取网关状态成功",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取网关状态失败: {str(e)}")

@router.get("/models", summary="获取可用模型")
async def get_available_models():
    """获取所有可用的LLM模型"""
    try:
        models = global_gateway.get_available_models()
        
        return LLMResponse(
            success=True,
            message="获取模型列表成功",
            data={
                "models": models,
                "count": len(models)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.get("/providers", summary="获取提供商列表")
async def get_providers():
    """获取所有LLM提供商"""
    try:
        providers = global_gateway.get_all_providers()
        
        return LLMResponse(
            success=True,
            message="获取提供商列表成功",
            data={
                "providers": providers,
                "count": len(providers)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {str(e)}")

@router.post("/chat/completions", summary="聊天补全")
async def chat_completions(request: ChatRequest):
    """执行聊天补全请求"""
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="消息列表不能为空")
        
        result = await global_gateway.chat_completion(request)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天补全失败: {str(e)}")

@router.post("/completions", summary="文本补全")
async def text_completions(request: CompletionRequest):
    """执行文本补全请求"""
    try:
        if not request.prompt:
            raise HTTPException(status_code=400, detail="提示文本不能为空")
        
        result = await global_gateway.text_completion(request)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本补全失败: {str(e)}")

@router.post("/providers", summary="添加提供商")
async def add_provider(config: ProviderConfig):
    """添加新的LLM提供商"""
    try:
        provider_config = {
            "api_key": config.api_key,
            "base_url": config.base_url,
            "enabled": config.enabled,
            "priority": config.priority,
            "rate_limit": config.rate_limit
        }
        
        global_gateway.add_provider(config.name, provider_config)
        
        return LLMResponse(
            success=True,
            message=f"添加提供商成功: {config.name}",
            data={
                "provider_name": config.name,
                "config": provider_config
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加提供商失败: {str(e)}")

@router.delete("/providers/{provider_name}", summary="删除提供商")
async def remove_provider(provider_name: str):
    """删除指定的LLM提供商"""
    try:
        if not global_gateway.get_provider_status(provider_name):
            raise HTTPException(status_code=404, detail=f"提供商 {provider_name} 不存在")
        
        global_gateway.remove_provider(provider_name)
        
        return LLMResponse(
            success=True,
            message=f"删除提供商成功: {provider_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除提供商失败: {str(e)}")

@router.get("/history", summary="获取请求历史")
async def get_request_history(
    limit: int = 100,
    request_type: Optional[str] = None
):
    """获取LLM请求历史记录"""
    try:
        history = global_gateway.request_history
        
        # 按请求类型过滤
        if request_type:
            history = [h for h in history if h["type"] == request_type]
        
        # 限制返回数量
        history = history[-limit:] if limit > 0 else history
        
        return LLMResponse(
            success=True,
            message="获取请求历史成功",
            data={
                "history": history,
                "count": len(history),
                "total_count": len(global_gateway.request_history)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取请求历史失败: {str(e)}")

@router.delete("/history", summary="清空请求历史")
async def clear_request_history():
    """清空LLM请求历史记录"""
    try:
        count = len(global_gateway.request_history)
        global_gateway.request_history.clear()
        
        return LLMResponse(
            success=True,
            message=f"清空请求历史成功，共清空 {count} 条记录",
            data={"cleared_count": count}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空请求历史失败: {str(e)}")

@router.get("/health", summary="网关健康检查")
async def gateway_health_check():
    """检查LLM网关健康状态"""
    try:
        stats = global_gateway.get_gateway_stats()
        
        # 判断健康状态
        health_status = "healthy"
        if stats["providers_count"] == 0:
            health_status = "no_providers"
        elif stats["active_providers"] == 0:
            health_status = "no_active_providers"
        elif stats["available_models"] == 0:
            health_status = "no_available_models"
        
        return LLMResponse(
            success=True,
            message="网关健康检查完成",
            data={
                "health_status": health_status,
                "gateway_stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"网关健康检查失败: {str(e)}")

# 初始化默认配置
async def initialize_default_gateway():
    """初始化默认网关配置"""
    try:
        # 添加默认提供商
        default_providers = [
            {
                "name": "openai",
                "config": {
                    "api_key": "sk-default",
                    "base_url": "https://api.openai.com/v1",
                    "enabled": True,
                    "priority": 1
                }
            },
            {
                "name": "anthropic",
                "config": {
                    "api_key": "sk-default",
                    "base_url": "https://api.anthropic.com",
                    "enabled": True,
                    "priority": 2
                }
            }
        ]
        
        for provider in default_providers:
            global_gateway.add_provider(provider["name"], provider["config"])
        
        # 添加默认模型
        default_models = [
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "openai",
                "description": "OpenAI GPT-3.5 Turbo模型",
                "max_tokens": 4096,
                "available": True
            },
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "openai",
                "description": "OpenAI GPT-4模型",
                "max_tokens": 8192,
                "available": True
            },
            {
                "id": "claude-3-sonnet",
                "name": "Claude 3 Sonnet",
                "provider": "anthropic",
                "description": "Anthropic Claude 3 Sonnet模型",
                "max_tokens": 200000,
                "available": True
            }
        ]
        
        for model in default_models:
            global_gateway.add_model(model["id"], model)
            
    except Exception as e:
        logging.error(f"初始化默认网关配置失败: {str(e)}")

# 启动时初始化
@router.on_event("startup")
async def startup_event():
    """启动事件处理"""
    await initialize_default_gateway()








