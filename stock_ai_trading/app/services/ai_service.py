"""
AI服务调用模块
支持多种AI提供商的真实API调用
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """AI服务调用异常"""
    pass

class AIService:
    """AI服务调用类"""
    
    def __init__(self):
        self.timeout = 10  # 请求超时时间（秒）- 优化为10秒
    
    async def call_model(
        self, 
        model_config: Dict[str, Any], 
        input_text: str
    ) -> Dict[str, Any]:
        """
        调用AI模型
        
        Args:
            model_config: 模型配置信息
            input_text: 输入文本
            
        Returns:
            AI响应结果
        """
        model_type = model_config.get('model_type', '').lower()
        
        if model_type == 'deepseek':
            return await self._call_deepseek(model_config, input_text)
        elif model_type == 'chatgpt':
            return await self._call_openai(model_config, input_text)
        elif model_type == 'claude':
            return await self._call_claude(model_config, input_text)
        elif model_type == 'llama':
            return await self._call_llama(model_config, input_text)
        else:
            return await self._call_custom(model_config, input_text)
    
    async def _call_deepseek(
        self, 
        model_config: Dict[str, Any], 
        input_text: str
    ) -> Dict[str, Any]:
        """调用DeepSeek API"""
        try:
            url = f"{model_config['base_url']}/chat/completions"
            headers = {
                'Authorization': f"Bearer {model_config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            # 为空的model_version提供默认值
            model_version = model_config.get('model_version')
            if not model_version or model_version.strip() == '':
                model_version = 'deepseek-chat'
            
            payload = {
                'model': model_version,
                'messages': [
                    {'role': 'user', 'content': input_text}
                ],
                'max_tokens': model_config.get('max_tokens', 4096),
                'temperature': model_config.get('temperature', 0.7),
                'stream': False
            }
            
            start_time = datetime.now()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            usage = result.get('usage', {})
                            
                            return {
                                'success': True,
                                'output': content,
                                'response_time_ms': response_time_ms,
                                'token_count': usage.get('total_tokens', 0),
                                'input_tokens': usage.get('prompt_tokens', 0),
                                'output_tokens': usage.get('completion_tokens', 0)
                            }
                        else:
                            raise AIServiceError("API返回格式异常")
                    else:
                        error_text = await response.text()
                        raise AIServiceError(f"API调用失败: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error_code': 'TIMEOUT',
                'error_message': 'API调用超时',
                'response_time_ms': self.timeout * 1000
            }
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            return {
                'success': False,
                'error_code': 'API_ERROR',
                'error_message': str(e),
                'response_time_ms': 0
            }
    
    async def _call_openai(
        self, 
        model_config: Dict[str, Any], 
        input_text: str
    ) -> Dict[str, Any]:
        """调用OpenAI API"""
        try:
            url = f"{model_config['base_url']}/v1/chat/completions"
            headers = {
                'Authorization': f"Bearer {model_config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            # 为空的model_version提供默认值
            model_version = model_config.get('model_version')
            if not model_version or model_version.strip() == '':
                model_version = 'gpt-3.5-turbo'
            
            payload = {
                'model': model_version,
                'messages': [
                    {'role': 'user', 'content': input_text}
                ],
                'max_tokens': model_config.get('max_tokens', 4096),
                'temperature': model_config.get('temperature', 0.7)
            }
            
            start_time = datetime.now()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            usage = result.get('usage', {})
                            
                            return {
                                'success': True,
                                'output': content,
                                'response_time_ms': response_time_ms,
                                'token_count': usage.get('total_tokens', 0),
                                'input_tokens': usage.get('prompt_tokens', 0),
                                'output_tokens': usage.get('completion_tokens', 0)
                            }
                        else:
                            raise AIServiceError("API返回格式异常")
                    else:
                        error_text = await response.text()
                        raise AIServiceError(f"API调用失败: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error_code': 'TIMEOUT',
                'error_message': 'API调用超时',
                'response_time_ms': self.timeout * 1000
            }
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return {
                'success': False,
                'error_code': 'API_ERROR',
                'error_message': str(e),
                'response_time_ms': 0
            }
    
    async def _call_claude(
        self, 
        model_config: Dict[str, Any], 
        input_text: str
    ) -> Dict[str, Any]:
        """调用Claude API"""
        try:
            url = f"{model_config['base_url']}/v1/messages"
            headers = {
                'x-api-key': model_config['api_key'],
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            # 为空的model_version提供默认值
            model_version = model_config.get('model_version')
            if not model_version or model_version.strip() == '':
                model_version = 'claude-3-sonnet-20240229'
            
            payload = {
                'model': model_version,
                'max_tokens': model_config.get('max_tokens', 4096),
                'temperature': model_config.get('temperature', 0.7),
                'messages': [
                    {'role': 'user', 'content': input_text}
                ]
            }
            
            start_time = datetime.now()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'content' in result and len(result['content']) > 0:
                            content = result['content'][0]['text']
                            usage = result.get('usage', {})
                            
                            return {
                                'success': True,
                                'output': content,
                                'response_time_ms': response_time_ms,
                                'token_count': usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
                                'input_tokens': usage.get('input_tokens', 0),
                                'output_tokens': usage.get('output_tokens', 0)
                            }
                        else:
                            raise AIServiceError("API返回格式异常")
                    else:
                        error_text = await response.text()
                        raise AIServiceError(f"API调用失败: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error_code': 'TIMEOUT',
                'error_message': 'API调用超时',
                'response_time_ms': self.timeout * 1000
            }
        except Exception as e:
            logger.error(f"Claude API调用失败: {e}")
            return {
                'success': False,
                'error_code': 'API_ERROR',
                'error_message': str(e),
                'response_time_ms': 0
            }
    
    async def _call_llama(
        self, 
        model_config: Dict[str, Any], 
        input_text: str
    ) -> Dict[str, Any]:
        """调用Llama API（通过Ollama或其他服务）"""
        try:
            url = f"{model_config['base_url']}/api/generate"
            headers = {
                'Content-Type': 'application/json'
            }
            
            # 如果有API密钥，添加到头部
            if model_config.get('api_key'):
                headers['Authorization'] = f"Bearer {model_config['api_key']}"
            
            payload = {
                'model': model_config.get('model_version', 'llama2'),
                'prompt': input_text,
                'stream': False,
                'options': {
                    'temperature': model_config.get('temperature', 0.7),
                    'num_predict': model_config.get('max_tokens', 4096)
                }
            }
            
            start_time = datetime.now()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'response' in result:
                            content = result['response']
                            
                            return {
                                'success': True,
                                'output': content,
                                'response_time_ms': response_time_ms,
                                'token_count': len(content.split()),  # 简单估算
                                'input_tokens': len(input_text.split()),
                                'output_tokens': len(content.split())
                            }
                        else:
                            raise AIServiceError("API返回格式异常")
                    else:
                        error_text = await response.text()
                        raise AIServiceError(f"API调用失败: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error_code': 'TIMEOUT',
                'error_message': 'API调用超时',
                'response_time_ms': self.timeout * 1000
            }
        except Exception as e:
            logger.error(f"Llama API调用失败: {e}")
            return {
                'success': False,
                'error_code': 'API_ERROR',
                'error_message': str(e),
                'response_time_ms': 0
            }
    
    async def _call_custom(
        self, 
        model_config: Dict[str, Any], 
        input_text: str
    ) -> Dict[str, Any]:
        """调用自定义API"""
        try:
            url = model_config['base_url']
            headers = {
                'Content-Type': 'application/json'
            }
            
            # 如果有API密钥，添加到头部
            if model_config.get('api_key'):
                headers['Authorization'] = f"Bearer {model_config['api_key']}"
            
            # 尝试通用的请求格式
            payload = {
                'input': input_text,
                'max_tokens': model_config.get('max_tokens', 4096),
                'temperature': model_config.get('temperature', 0.7)
            }
            
            # 如果有自定义配置，合并到payload中
            if model_config.get('config_json'):
                payload.update(model_config['config_json'])
            
            start_time = datetime.now()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # 尝试从不同字段获取输出内容
                        content = None
                        for field in ['output', 'response', 'text', 'content', 'result']:
                            if field in result:
                                content = result[field]
                                break
                        
                        if content:
                            return {
                                'success': True,
                                'output': content,
                                'response_time_ms': response_time_ms,
                                'token_count': len(str(content).split()),  # 简单估算
                                'input_tokens': len(input_text.split()),
                                'output_tokens': len(str(content).split())
                            }
                        else:
                            raise AIServiceError("API返回格式异常，无法找到输出内容")
                    else:
                        error_text = await response.text()
                        raise AIServiceError(f"API调用失败: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error_code': 'TIMEOUT',
                'error_message': 'API调用超时',
                'response_time_ms': self.timeout * 1000
            }
        except Exception as e:
            logger.error(f"自定义API调用失败: {e}")
            return {
                'success': False,
                'error_code': 'API_ERROR',
                'error_message': str(e),
                'response_time_ms': 0
            }

# 全局AI服务实例
ai_service = AIService()