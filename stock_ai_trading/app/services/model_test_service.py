"""
模型测试服务
提供AI模型和模型组合的测试功能
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class ModelTestService:
    """模型测试服务"""
    
    def __init__(self):
        self.timeout = 30  # 请求超时时间（秒）
    
    async def test_single_model(
        self, 
        model_config: Dict[str, Any], 
        test_input: str,
        expected_output: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        测试单个模型
        
        Args:
            model_config: 模型配置信息
            test_input: 测试输入
            expected_output: 期望输出（可选）
            
        Returns:
            测试结果
        """
        start_time = time.time()
        
        try:
            # 根据模型类型构建请求
            if model_config['model_type'] == 'ChatGPT':
                result = await self._test_openai_model(model_config, test_input)
            elif model_config['model_type'] == 'Claude':
                result = await self._test_claude_model(model_config, test_input)
            elif model_config['model_type'] == 'DeepSeek':
                result = await self._test_deepseek_model(model_config, test_input)
            else:
                result = await self._test_generic_model(model_config, test_input)
            
            response_time = int((time.time() - start_time) * 1000)  # 毫秒
            
            # 计算准确率（如果有期望输出）
            accuracy_score = None
            if expected_output and result.get('success'):
                accuracy_score = self._calculate_accuracy(
                    result.get('output', ''), 
                    expected_output
                )
            
            return {
                'success': result.get('success', False),
                'output': result.get('output'),
                'response_time_ms': response_time,
                'token_count': result.get('token_count', 0),
                'accuracy_score': accuracy_score,
                'error_code': result.get('error_code'),
                'error_message': result.get('error_message'),
                'model_id': model_config['model_id'],
                'test_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            logger.error(f"Model test failed: {e}")
            
            return {
                'success': False,
                'output': None,
                'response_time_ms': response_time,
                'token_count': 0,
                'accuracy_score': None,
                'error_code': 'TEST_ERROR',
                'error_message': str(e),
                'model_id': model_config['model_id'],
                'test_timestamp': datetime.now().isoformat()
            }
    
    async def test_ensemble_models(
        self,
        ensemble_config: Dict[str, Any],
        models_config: List[Dict[str, Any]],
        test_input: str,
        expected_output: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        测试模型组合
        
        Args:
            ensemble_config: 组合配置
            models_config: 模型配置列表
            test_input: 测试输入
            expected_output: 期望输出（可选）
            
        Returns:
            组合测试结果
        """
        start_time = time.time()
        
        try:
            # 并行测试所有模型
            tasks = []
            for model_config in models_config:
                task = self.test_single_model(model_config, test_input, expected_output)
                tasks.append(task)
            
            model_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            valid_results = []
            for i, result in enumerate(model_results):
                if isinstance(result, Exception):
                    logger.error(f"Model {models_config[i]['model_id']} test failed: {result}")
                    continue
                if result.get('success'):
                    valid_results.append(result)
            
            if not valid_results:
                return {
                    'success': False,
                    'ensemble_output': None,
                    'individual_results': model_results,
                    'response_time_ms': int((time.time() - start_time) * 1000),
                    'error_message': '所有模型测试都失败了'
                }
            
            # 根据组合策略合并结果
            ensemble_output = self._combine_model_outputs(
                valid_results, 
                ensemble_config
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            # 计算组合准确率
            ensemble_accuracy = None
            if expected_output:
                ensemble_accuracy = self._calculate_accuracy(
                    ensemble_output, 
                    expected_output
                )
            
            return {
                'success': True,
                'ensemble_output': ensemble_output,
                'individual_results': model_results,
                'response_time_ms': response_time,
                'accuracy_score': ensemble_accuracy,
                'ensemble_id': ensemble_config['ensemble_id'],
                'test_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            logger.error(f"Ensemble test failed: {e}")
            
            return {
                'success': False,
                'ensemble_output': None,
                'individual_results': [],
                'response_time_ms': response_time,
                'error_message': str(e),
                'ensemble_id': ensemble_config['ensemble_id'],
                'test_timestamp': datetime.now().isoformat()
            }
    
    async def _test_openai_model(self, model_config: Dict[str, Any], test_input: str) -> Dict[str, Any]:
        """测试OpenAI模型"""
        try:
            headers = {
                'Authorization': f'Bearer {model_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model_config.get('model_version', 'gpt-3.5-turbo'),
                'messages': [
                    {'role': 'user', 'content': test_input}
                ],
                'max_tokens': model_config.get('max_tokens', 1000),
                'temperature': float(model_config.get('temperature', 0.7))
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{model_config['base_url']}/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'output': result['choices'][0]['message']['content'],
                            'token_count': result.get('usage', {}).get('total_tokens', 0)
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error_code': f'HTTP_{response.status}',
                            'error_message': error_text
                        }
        except Exception as e:
            return {
                'success': False,
                'error_code': 'REQUEST_ERROR',
                'error_message': str(e)
            }
    
    async def _test_claude_model(self, model_config: Dict[str, Any], test_input: str) -> Dict[str, Any]:
        """测试Claude模型"""
        try:
            headers = {
                'x-api-key': model_config["api_key"],
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            data = {
                'model': model_config.get('model_version', 'claude-3-sonnet-20240229'),
                'max_tokens': model_config.get('max_tokens', 1000),
                'messages': [
                    {'role': 'user', 'content': test_input}
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{model_config['base_url']}/v1/messages",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'output': result['content'][0]['text'],
                            'token_count': result.get('usage', {}).get('output_tokens', 0)
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error_code': f'HTTP_{response.status}',
                            'error_message': error_text
                        }
        except Exception as e:
            return {
                'success': False,
                'error_code': 'REQUEST_ERROR',
                'error_message': str(e)
            }
    
    async def _test_deepseek_model(self, model_config: Dict[str, Any], test_input: str) -> Dict[str, Any]:
        """测试DeepSeek模型"""
        try:
            headers = {
                'Authorization': f'Bearer {model_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model_config.get('model_version', 'deepseek-chat'),
                'messages': [
                    {'role': 'user', 'content': test_input}
                ],
                'max_tokens': model_config.get('max_tokens', 1000),
                'temperature': float(model_config.get('temperature', 0.7))
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{model_config['base_url']}/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'output': result['choices'][0]['message']['content'],
                            'token_count': result.get('usage', {}).get('total_tokens', 0)
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error_code': f'HTTP_{response.status}',
                            'error_message': error_text
                        }
        except Exception as e:
            return {
                'success': False,
                'error_code': 'REQUEST_ERROR',
                'error_message': str(e)
            }
    
    async def _test_generic_model(self, model_config: Dict[str, Any], test_input: str) -> Dict[str, Any]:
        """测试通用模型（自定义或其他类型）"""
        try:
            # 模拟测试结果（实际实现中应该根据具体的API格式调用）
            await asyncio.sleep(0.5)  # 模拟网络延迟
            
            return {
                'success': True,
                'output': f"模拟回复: 收到输入 '{test_input[:50]}...'",
                'token_count': len(test_input.split()) + 10
            }
        except Exception as e:
            return {
                'success': False,
                'error_code': 'GENERIC_ERROR',
                'error_message': str(e)
            }
    
    def _combine_model_outputs(
        self, 
        results: List[Dict[str, Any]], 
        ensemble_config: Dict[str, Any]
    ) -> str:
        """
        根据组合策略合并模型输出
        
        Args:
            results: 模型测试结果列表
            ensemble_config: 组合配置
            
        Returns:
            合并后的输出
        """
        if not results:
            return ""
        
        strategy = ensemble_config.get('weight_strategy', 'equal_weight')
        
        if strategy == 'equal_weight':
            # 等权重：简单选择第一个成功的结果
            return results[0]['output']
        
        elif strategy == 'accuracy_weight':
            # 准确率权重：选择准确率最高的结果
            best_result = max(results, key=lambda x: x.get('accuracy_score', 0) or 0)
            return best_result['output']
        
        elif strategy == 'confidence':
            # 置信度：选择响应时间最短的（假设更快=更有信心）
            best_result = min(results, key=lambda x: x.get('response_time_ms', float('inf')))
            return best_result['output']
        
        else:
            # 默认返回第一个结果
            return results[0]['output']
    
    def _calculate_accuracy(self, actual_output: str, expected_output: str) -> float:
        """
        计算输出准确率（简单的字符串相似度）
        
        Args:
            actual_output: 实际输出
            expected_output: 期望输出
            
        Returns:
            准确率分数 (0.0-1.0)
        """
        if not actual_output or not expected_output:
            return 0.0
        
        # 简单的字符串相似度计算
        actual_words = set(actual_output.lower().split())
        expected_words = set(expected_output.lower().split())
        
        if not expected_words:
            return 0.0
        
        intersection = actual_words.intersection(expected_words)
        union = actual_words.union(expected_words)
        
        # Jaccard相似度
        similarity = len(intersection) / len(union) if union else 0.0
        
        return min(similarity, 1.0)

# 全局测试服务实例
model_test_service = ModelTestService()