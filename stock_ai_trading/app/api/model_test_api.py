"""
模型测试API
提供单模型和组合模型的测试功能
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any

from flask import Blueprint, request, jsonify, g
from flasgger import swag_from
from sqlalchemy import and_, desc

from ..models.model_management import (
    AIModel, ModelEnsemble, EnsembleModelMapping, 
    ModelTestRecord, ModelUsageLog, TestType
)
from ..middleware.auth import require_auth
from ..services.encryption_service import encryption_service

logger = logging.getLogger(__name__)

# 创建蓝图
model_test_bp = Blueprint('model_test', __name__, url_prefix='/api')

# =====================================================
# 模型测试服务类
# =====================================================

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
        import time
        from ..services.ai_service import ai_service
        
        start_time = time.time()
        
        try:
            # 调用真实的AI服务
            result = await ai_service.call_model(model_config, test_input)
            
            if result.get('success'):
                # 计算准确率（如果有期望输出）
                accuracy_score = None
                if expected_output:
                    accuracy_score = self._calculate_accuracy(result['output'], expected_output)
                
                return {
                    'success': True,
                    'output': result['output'],
                    'response_time_ms': result.get('response_time_ms', int((time.time() - start_time) * 1000)),
                    'token_count': result.get('token_count', 0),
                    'input_tokens': result.get('input_tokens', 0),
                    'output_tokens': result.get('output_tokens', 0),
                    'accuracy_score': accuracy_score,
                    'model_id': model_config['model_id'],
                    'test_timestamp': datetime.now().isoformat()
                }
            else:
                # AI服务调用失败
                response_time = result.get('response_time_ms', int((time.time() - start_time) * 1000))
                return {
                    'success': False,
                    'output': None,
                    'response_time_ms': response_time,
                    'token_count': 0,
                    'accuracy_score': None,
                    'error_code': result.get('error_code', 'API_ERROR'),
                    'error_message': result.get('error_message', '未知错误'),
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
        import time
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

# =====================================================
# 工具函数
# =====================================================

def validate_json_request(required_fields: List[str] = None):
    """验证JSON请求"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': '请求必须是JSON格式'
                }), 400
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': '请求体不能为空'
                }), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'message': f'缺少必需字段: {", ".join(missing_fields)}'
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def with_db_session(f):
    """数据库会话装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from ..api.model_management_flask import get_db
        db = get_db()
        try:
            g.db = db
            result = f(*args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Database error in {f.__name__}: {e}")
            raise e
        finally:
            db.close()
    return decorated_function

def model_to_dict(model_instance):
    """将模型实例转换为字典"""
    if not model_instance:
        return None
    
    result = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        if isinstance(value, (datetime,)):
            result[column.name] = value.isoformat() if value else None
        elif isinstance(value, Decimal):
            result[column.name] = float(value)
        elif hasattr(value, 'value'):  # 枚举类型
            result[column.name] = value.value
        else:
            result[column.name] = value
    
    return result

# =====================================================
# 3. 模型测试API
# =====================================================

@model_test_bp.route('/models/test', methods=['POST'])
@require_auth
@validate_json_request(['model_id', 'input'])
@with_db_session
@swag_from({
    'tags': ['模型测试'],
    'summary': '单模型对话测试',
    'description': '测试单个AI模型的对话能力',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['model_id', 'input'],
            'properties': {
                'model_id': {'type': 'string', 'description': '模型ID'},
                'input': {'type': 'string', 'description': '测试输入'},
                'expected_output': {'type': 'string', 'description': '期望输出（可选）'},
                'test_name': {'type': 'string', 'description': '测试名称'},
                'test_description': {'type': 'string', 'description': '测试描述'}
            }
        }
    }],
    'responses': {
        200: {'description': '测试成功'},
        404: {'description': '模型不存在'},
        400: {'description': '请求参数错误'}
    }
})
def test_single_model():
    """单模型对话测试"""
    try:
        data = request.get_json()
        db = g.db
        
        # 检查模型是否存在
        model = db.query(AIModel).filter(AIModel.model_id == data['model_id']).first()
        if not model:
            return jsonify({
                'success': False,
                'message': f'模型 {data["model_id"]} 不存在'
            }), 404
        
        # 检查模型是否启用
        if not model.enabled:
            return jsonify({
                'success': False,
                'message': '模型未启用，无法进行测试'
            }), 400
        
        # 准备模型配置
        model_config = {
            'model_id': model.model_id,
            'model_type': model.model_type.value,
            'provider': model.provider,
            'base_url': model.base_url,
            'model_version': model.model_version,
            'max_tokens': model.max_tokens,
            'temperature': float(model.temperature) if model.temperature else 0.7
        }
        
        # 解密API密钥
        if model.api_key_encrypted:
            try:
                model_config['api_key'] = encryption_service.decrypt(model.api_key_encrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt API key: {e}")
                return jsonify({
                    'success': False,
                    'message': 'API密钥解密失败'
                }), 500
        
        # 执行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            test_result = loop.run_until_complete(
                model_test_service.test_single_model(
                    model_config,
                    data['input'],
                    data.get('expected_output')
                )
            )
        finally:
            loop.close()
        
        # 保存测试记录
        test_record = ModelTestRecord(
            test_id=f"test_{model.model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model_id=model.model_id,
            test_type=TestType.UNIT,
            test_name=data.get('test_name', '单模型对话测试'),
            test_description=data.get('test_description', ''),
            input_data={'input': data['input']},
            expected_output={'output': data.get('expected_output')} if data.get('expected_output') else None,
            actual_output={'output': test_result.get('output')},
            response_time_ms=test_result.get('response_time_ms'),
            token_count=test_result.get('token_count'),
            success=test_result.get('success', False),
            accuracy_score=Decimal(str(test_result.get('accuracy_score'))) if test_result.get('accuracy_score') else None,
            error_code=test_result.get('error_code'),
            error_message=test_result.get('error_message'),
            tested_by=g.current_user.get('user_id', 'system')
        )
        
        db.add(test_record)
        
        # 记录使用日志
        usage_log = ModelUsageLog(
            log_id=f"log_{model.model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model_id=model.model_id,
            user_id=g.current_user.get('user_id', 'system'),
            input_tokens=len(data['input'].split()),
            output_tokens=test_result.get('token_count', 0) - len(data['input'].split()),
            total_tokens=test_result.get('token_count', 0),
            response_time_ms=test_result.get('response_time_ms'),
            success=test_result.get('success', False),
            error_code=test_result.get('error_code'),
            error_message=test_result.get('error_message')
        )
        
        db.add(usage_log)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '模型测试完成',
            'data': {
                'test_result': test_result,
                'test_record_id': test_record.test_id
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing single model: {e}")
        return jsonify({
            'success': False,
            'message': '模型测试时发生错误'
        }), 500

@model_test_bp.route('/ensembles/test', methods=['POST'])
@require_auth
@validate_json_request(['ensemble_id', 'input'])
@with_db_session
@swag_from({
    'tags': ['模型测试'],
    'summary': '组合模型测试',
    'description': '测试模型组合的对话能力',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['ensemble_id', 'input'],
            'properties': {
                'ensemble_id': {'type': 'string', 'description': '组合ID'},
                'input': {'type': 'string', 'description': '测试输入'},
                'expected_output': {'type': 'string', 'description': '期望输出（可选）'},
                'test_name': {'type': 'string', 'description': '测试名称'},
                'test_description': {'type': 'string', 'description': '测试描述'}
            }
        }
    }],
    'responses': {
        200: {'description': '测试成功'},
        404: {'description': '组合不存在'},
        400: {'description': '请求参数错误'}
    }
})
def test_ensemble_models():
    """组合模型测试"""
    try:
        data = request.get_json()
        db = g.db
        
        # 检查组合是否存在
        ensemble = db.query(ModelEnsemble).filter(ModelEnsemble.ensemble_id == data['ensemble_id']).first()
        if not ensemble:
            return jsonify({
                'success': False,
                'message': f'组合 {data["ensemble_id"]} 不存在'
            }), 404
        
        # 检查组合是否启用
        if not ensemble.enabled:
            return jsonify({
                'success': False,
                'message': '组合未启用，无法进行测试'
            }), 400
        
        # 获取组合中的模型
        mappings = db.query(EnsembleModelMapping).filter(
            and_(
                EnsembleModelMapping.ensemble_id == data['ensemble_id'],
                EnsembleModelMapping.enabled == True
            )
        ).all()
        
        if not mappings:
            return jsonify({
                'success': False,
                'message': '组合中没有启用的模型'
            }), 400
        
        # 准备模型配置列表
        models_config = []
        for mapping in mappings:
            model = db.query(AIModel).filter(AIModel.model_id == mapping.model_id).first()
            if model and model.enabled:
                model_config = {
                    'model_id': model.model_id,
                    'model_type': model.model_type.value,
                    'provider': model.provider,
                    'base_url': model.base_url,
                    'model_version': model.model_version,
                    'max_tokens': model.max_tokens,
                    'temperature': float(model.temperature) if model.temperature else 0.7,
                    'weight': float(mapping.weight)
                }
                
                # 解密API密钥
                if model.api_key_encrypted:
                    try:
                        model_config['api_key'] = encryption_service.decrypt(model.api_key_encrypted)
                    except Exception as e:
                        logger.error(f"Failed to decrypt API key for model {model.model_id}: {e}")
                        continue
                
                models_config.append(model_config)
        
        if not models_config:
            return jsonify({
                'success': False,
                'message': '组合中没有可用的模型'
            }), 400
        
        # 准备组合配置
        ensemble_config = {
            'ensemble_id': ensemble.ensemble_id,
            'weight_strategy': ensemble.weight_strategy.value,
            'voting_method': ensemble.voting_method.value,
            'confidence_threshold': float(ensemble.confidence_threshold)
        }
        
        # 执行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            test_result = loop.run_until_complete(
                model_test_service.test_ensemble_models(
                    ensemble_config,
                    models_config,
                    data['input'],
                    data.get('expected_output')
                )
            )
        finally:
            loop.close()
        
        # 保存测试记录
        test_record = ModelTestRecord(
            test_id=f"test_{ensemble.ensemble_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model_id=models_config[0]['model_id'],  # 使用第一个模型的ID
            ensemble_id=ensemble.ensemble_id,
            test_type=TestType.INTEGRATION,
            test_name=data.get('test_name', '组合模型测试'),
            test_description=data.get('test_description', ''),
            input_data={'input': data['input']},
            expected_output={'output': data.get('expected_output')} if data.get('expected_output') else None,
            actual_output={'output': test_result.get('ensemble_output')},
            response_time_ms=test_result.get('response_time_ms'),
            success=test_result.get('success', False),
            accuracy_score=Decimal(str(test_result.get('accuracy_score'))) if test_result.get('accuracy_score') else None,
            error_message=test_result.get('error_message'),
            tested_by=g.current_user.get('user_id', 'system')
        )
        
        db.add(test_record)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '组合模型测试完成',
            'data': {
                'test_result': test_result,
                'test_record_id': test_record.test_id
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing ensemble models: {e}")
        return jsonify({
            'success': False,
            'message': '组合模型测试时发生错误'
        }), 500

@model_test_bp.route('/models/<model_id>/test-records', methods=['GET'])
@require_auth
@with_db_session
@swag_from({
    'tags': ['模型测试'],
    'summary': '获取测试记录',
    'description': '获取指定模型的测试记录',
    'parameters': [
        {'name': 'model_id', 'in': 'path', 'type': 'string', 'required': True, 'description': '模型ID'},
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1, 'description': '页码'},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 20, 'description': '每页数量'},
        {'name': 'test_type', 'in': 'query', 'type': 'string', 'description': '测试类型过滤'},
        {'name': 'success', 'in': 'query', 'type': 'boolean', 'description': '成功状态过滤'}
    ],
    'responses': {
        200: {'description': '获取成功'},
        404: {'description': '模型不存在'}
    }
})
def get_model_test_records(model_id):
    """获取测试记录"""
    try:
        db = g.db
        
        # 检查模型是否存在
        model = db.query(AIModel).filter(AIModel.model_id == model_id).first()
        if not model:
            return jsonify({
                'success': False,
                'message': f'模型 {model_id} 不存在'
            }), 404
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        test_type = request.args.get('test_type')
        success = request.args.get('success')
        
        # 构建查询
        query = db.query(ModelTestRecord).filter(ModelTestRecord.model_id == model_id)
        
        # 测试类型过滤
        if test_type:
            try:
                query = query.filter(ModelTestRecord.test_type == TestType(test_type))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': f'无效的测试类型: {test_type}'
                }), 400
        
        # 成功状态过滤
        if success is not None:
            success_bool = success.lower() in ('true', '1', 'yes')
            query = query.filter(ModelTestRecord.success == success_bool)
        
        # 排序
        query = query.order_by(desc(ModelTestRecord.created_at))
        
        # 分页
        from ..api.model_management_flask import paginate_query
        result = paginate_query(query, page, per_page)
        
        # 转换为字典格式
        records_data = [model_to_dict(record) for record in result['items']]
        
        return jsonify({
            'success': True,
            'message': '获取测试记录成功',
            'data': {
                'items': records_data,
                'total': result['total'],
                'page': result['page'],
                'per_page': result['per_page'],
                'pages': result['pages']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting test records: {e}")
        return jsonify({
            'success': False,
            'message': '获取测试记录时发生错误'
        }), 500

# =====================================================
# 健康检查接口
# =====================================================

@model_test_bp.route('/test/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        return jsonify({
            'success': True,
            'message': '模型测试API服务正常',
            'service': 'model_test_api',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'message': '服务异常',
            'service': 'model_test_api',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500