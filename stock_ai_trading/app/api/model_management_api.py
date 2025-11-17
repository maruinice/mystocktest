"""
模型管理系统 Flask API
提供完整的AI模型管理、组合管理、测试和监控功能
"""

import os
import logging
import asyncio
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from functools import wraps

from flask import Flask, Blueprint, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger, swag_from
from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import BadRequest, NotFound, Conflict, InternalServerError

# 导入数据模型
from ..models.model_management import (
    Base, AIModel, ModelEnsemble, EnsembleModelMapping, 
    ModelTestRecord, ModelMetric, ModelAPIKey, ModelUsageLog,
    ModelType, ModelStatus, HealthStatus, WeightStrategy, VotingMethod, TestType
)
from ..middleware.auth import require_auth
from ..services.encryption_service import EncryptionService
from ..services.model_test_service import ModelTestService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
model_mgmt_bp = Blueprint('model_management', __name__, url_prefix='/api')

# 配置CORS和限流
limiter = Limiter(
    app=None,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:password@localhost:3306/stock_ai_trading?charset=utf8mb4')

# 创建数据库引擎和会话
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
SessionLocal = scoped_session(sessionmaker(bind=engine))

# 初始化服务
encryption_service = EncryptionService()
model_test_service = ModelTestService()

# =====================================================
# 数据库会话管理
# =====================================================

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def with_db_session(f):
    """数据库会话装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
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

# =====================================================
# 工具函数
# =====================================================

def validate_json_request(required_fields: List[str] = None):
    """验证JSON请求"""
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

def paginate_query(query, page: int = 1, per_page: int = 20):
    """分页查询"""
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }

def model_to_dict(model_instance):
    """将模型实例转换为字典"""
    if not model_instance:
        return None
    
    result = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        if isinstance(value, (datetime, date)):
            result[column.name] = value.isoformat() if value else None
        elif isinstance(value, Decimal):
            result[column.name] = float(value)
        elif hasattr(value, 'value'):  # 枚举类型
            result[column.name] = value.value
        else:
            result[column.name] = value
    
    return result

# =====================================================
# 1. 模型管理 CRUD API
# =====================================================

@model_mgmt_bp.route('/models', methods=['POST'])
@require_auth
@validate_json_request(['name', 'model_type', 'provider'])
@with_db_session
@swag_from({
    'tags': ['模型管理'],
    'summary': '创建AI模型',
    'description': '创建新的AI模型，支持DeepSeek、ChatGPT、Claude等类型',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['name', 'model_type', 'provider'],
            'properties': {
                'name': {'type': 'string', 'description': '模型名称'},
                'model_type': {'type': 'string', 'enum': ['DeepSeek', 'ChatGPT', 'Claude', 'Llama', 'Custom']},
                'provider': {'type': 'string', 'description': '提供商'},
                'display_name': {'type': 'string', 'description': '显示名称'},
                'description': {'type': 'string', 'description': '模型描述'},
                'model_version': {'type': 'string', 'description': '模型版本'},
                'base_url': {'type': 'string', 'description': 'API基础URL'},
                'api_key': {'type': 'string', 'description': 'API密钥'},
                'max_tokens': {'type': 'integer', 'description': '最大token数'},
                'temperature': {'type': 'number', 'description': '温度参数'},
                'config_json': {'type': 'object', 'description': '扩展配置'}
            }
        }
    }],
    'responses': {
        201: {'description': '创建成功'},
        400: {'description': '请求参数错误'},
        409: {'description': '模型名称已存在'}
    }
})
def create_model():
    """创建AI模型"""
    try:
        data = request.get_json()
        db = g.db
        
        # 检查模型名称是否已存在
        existing_model = db.query(AIModel).filter(AIModel.name == data['name']).first()
        if existing_model:
            return jsonify({
                'success': False,
                'message': f'模型名称 "{data["name"]}" 已存在'
            }), 409
        
        # 生成模型ID
        model_id = f"{data['model_type'].lower()}_{data['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 加密API密钥
        encrypted_api_key = None
        if data.get('api_key'):
            encrypted_api_key = encryption_service.encrypt(data['api_key'])
        
        # 创建模型实例
        model = AIModel(
            model_id=model_id,
            name=data['name'],
            display_name=data.get('display_name', data['name']),
            description=data.get('description', ''),
            model_type=ModelType(data['model_type']),
            provider=data['provider'],
            model_version=data.get('model_version'),
            base_url=data.get('base_url'),
            api_key_encrypted=encrypted_api_key,
            max_tokens=data.get('max_tokens', 4096),
            temperature=Decimal(str(data.get('temperature', 0.7))),
            config_json=data.get('config_json', {}),
            status=ModelStatus.INACTIVE,
            enabled=False,
            health_status=HealthStatus.UNKNOWN,
            created_by=g.current_user.get('user_id', 'system')
        )
        
        db.add(model)
        db.flush()  # 获取生成的ID
        
        # 如果提供了API密钥，创建密钥记录
        if data.get('api_key'):
            api_key_record = ModelAPIKey(
                key_id=f"key_{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_id=model_id,
                key_name=f"{data['name']} Primary Key",
                encrypted_key=encrypted_api_key,
                key_hash=encryption_service.hash_key(data['api_key']),
                status='active',
                created_by=g.current_user.get('user_id', 'system')
            )
            db.add(api_key_record)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '模型创建成功',
            'data': model_to_dict(model)
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'参数错误: {str(e)}'
        }), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error creating model: {e}")
        return jsonify({
            'success': False,
            'message': '数据库错误，创建模型失败'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error creating model: {e}")
        return jsonify({
            'success': False,
            'message': '创建模型时发生未知错误'
        }), 500

@model_mgmt_bp.route('/models', methods=['GET'])
@require_auth
@with_db_session
@swag_from({
    'tags': ['模型管理'],
    'summary': '获取模型列表',
    'description': '获取AI模型列表，支持搜索和分页',
    'parameters': [
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1, 'description': '页码'},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 20, 'description': '每页数量'},
        {'name': 'search', 'in': 'query', 'type': 'string', 'description': '搜索关键词'},
        {'name': 'model_type', 'in': 'query', 'type': 'string', 'description': '模型类型过滤'},
        {'name': 'status', 'in': 'query', 'type': 'string', 'description': '状态过滤'},
        {'name': 'enabled', 'in': 'query', 'type': 'boolean', 'description': '启用状态过滤'}
    ],
    'responses': {
        200: {'description': '获取成功'},
        400: {'description': '请求参数错误'}
    }
})
def get_models():
    """获取模型列表"""
    try:
        db = g.db
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # 限制最大每页数量
        search = request.args.get('search', '').strip()
        model_type = request.args.get('model_type')
        status = request.args.get('status')
        enabled = request.args.get('enabled')
        
        # 构建查询
        query = db.query(AIModel)
        
        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    AIModel.name.contains(search),
                    AIModel.display_name.contains(search),
                    AIModel.description.contains(search),
                    AIModel.provider.contains(search)
                )
            )
        
        # 类型过滤
        if model_type:
            try:
                query = query.filter(AIModel.model_type == ModelType(model_type))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': f'无效的模型类型: {model_type}'
                }), 400
        
        # 状态过滤
        if status:
            try:
                query = query.filter(AIModel.status == ModelStatus(status))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': f'无效的状态: {status}'
                }), 400
        
        # 启用状态过滤
        if enabled is not None:
            enabled_bool = enabled.lower() in ('true', '1', 'yes')
            query = query.filter(AIModel.enabled == enabled_bool)
        
        # 排序
        query = query.order_by(desc(AIModel.created_at))
        
        # 分页
        result = paginate_query(query, page, per_page)
        
        # 转换为字典格式
        models_data = [model_to_dict(model) for model in result['items']]
        
        return jsonify({
            'success': True,
            'message': '获取模型列表成功',
            'data': {
                'models': models_data,
                'pagination': {
                    'total': result['total'],
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'pages': result['pages']
                }
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'参数错误: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return jsonify({
            'success': False,
            'message': '获取模型列表时发生错误'
        }), 500

@model_mgmt_bp.route('/models/<model_id>', methods=['GET'])
@require_auth
@with_db_session
@swag_from({
    'tags': ['模型管理'],
    'summary': '获取模型详情',
    'description': '根据模型ID获取详细信息',
    'parameters': [
        {'name': 'model_id', 'in': 'path', 'type': 'string', 'required': True, 'description': '模型ID'}
    ],
    'responses': {
        200: {'description': '获取成功'},
        404: {'description': '模型不存在'}
    }
})
def get_model_detail(model_id):
    """获取模型详情"""
    try:
        db = g.db
        
        model = db.query(AIModel).filter(AIModel.model_id == model_id).first()
        if not model:
            return jsonify({
                'success': False,
                'message': f'模型 {model_id} 不存在'
            }), 404
        
        # 获取相关的API密钥信息（不包含实际密钥）
        api_keys = db.query(ModelAPIKey).filter(ModelAPIKey.model_id == model_id).all()
        api_keys_data = []
        for key in api_keys:
            key_data = model_to_dict(key)
            # 移除敏感信息
            key_data.pop('encrypted_key', None)
            key_data.pop('key_hash', None)
            api_keys_data.append(key_data)
        
        # 获取最近的性能指标
        latest_metric = db.query(ModelMetric).filter(
            ModelMetric.model_id == model_id
        ).order_by(desc(ModelMetric.metric_date)).first()
        
        model_data = model_to_dict(model)
        model_data['api_keys'] = api_keys_data
        model_data['latest_metric'] = model_to_dict(latest_metric) if latest_metric else None
        
        # 移除加密的API密钥
        model_data.pop('api_key_encrypted', None)
        
        return jsonify({
            'success': True,
            'message': '获取模型详情成功',
            'data': model_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting model detail: {e}")
        return jsonify({
            'success': False,
            'message': '获取模型详情时发生错误'
        }), 500

@model_mgmt_bp.route('/models/<model_id>', methods=['PUT'])
@require_auth
@validate_json_request()
@with_db_session
@swag_from({
    'tags': ['模型管理'],
    'summary': '更新模型信息',
    'description': '更新指定模型的配置信息',
    'parameters': [
        {'name': 'model_id', 'in': 'path', 'type': 'string', 'required': True, 'description': '模型ID'},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'display_name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'model_version': {'type': 'string'},
                    'base_url': {'type': 'string'},
                    'max_tokens': {'type': 'integer'},
                    'temperature': {'type': 'number'},
                    'weight': {'type': 'number'},
                    'config_json': {'type': 'object'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': '更新成功'},
        404: {'description': '模型不存在'},
        400: {'description': '请求参数错误'}
    }
})
def update_model(model_id):
    """更新模型信息"""
    try:
        db = g.db
        data = request.get_json()
        
        model = db.query(AIModel).filter(AIModel.model_id == model_id).first()
        if not model:
            return jsonify({
                'success': False,
                'message': f'模型 {model_id} 不存在'
            }), 404
        
        # 更新允许的字段
        updatable_fields = [
            'display_name', 'description', 'model_version', 'base_url',
            'max_tokens', 'temperature', 'weight', 'config_json'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'temperature' or field == 'weight':
                    setattr(model, field, Decimal(str(data[field])))
                else:
                    setattr(model, field, data[field])
        
        model.updated_by = g.current_user.get('user_id', 'system')
        model.updated_at = datetime.now()
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '模型更新成功',
            'data': model_to_dict(model)
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'参数错误: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error updating model: {e}")
        return jsonify({
            'success': False,
            'message': '更新模型时发生错误'
        }), 500

@model_mgmt_bp.route('/models/<model_id>', methods=['DELETE'])
@require_auth
@with_db_session
@swag_from({
    'tags': ['模型管理'],
    'summary': '删除模型',
    'description': '删除指定的AI模型',
    'parameters': [
        {'name': 'model_id', 'in': 'path', 'type': 'string', 'required': True, 'description': '模型ID'}
    ],
    'responses': {
        200: {'description': '删除成功'},
        404: {'description': '模型不存在'},
        409: {'description': '模型正在使用中，无法删除'}
    }
})
def delete_model(model_id):
    """删除模型"""
    try:
        db = g.db
        
        model = db.query(AIModel).filter(AIModel.model_id == model_id).first()
        if not model:
            return jsonify({
                'success': False,
                'message': f'模型 {model_id} 不存在'
            }), 404
        
        # 检查模型是否在组合中使用
        ensemble_mappings = db.query(EnsembleModelMapping).filter(
            EnsembleModelMapping.model_id == model_id
        ).count()
        
        if ensemble_mappings > 0:
            return jsonify({
                'success': False,
                'message': '模型正在组合中使用，请先从组合中移除后再删除'
            }), 409
        
        # 删除模型（级联删除相关记录）
        db.delete(model)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '模型删除成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        return jsonify({
            'success': False,
            'message': '删除模型时发生错误'
        }), 500

@model_mgmt_bp.route('/models/<model_id>/status', methods=['PATCH'])
@require_auth
@validate_json_request(['enabled'])
@with_db_session
@swag_from({
    'tags': ['模型管理'],
    'summary': '启用/停用模型',
    'description': '切换模型的启用状态',
    'parameters': [
        {'name': 'model_id', 'in': 'path', 'type': 'string', 'required': True, 'description': '模型ID'},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['enabled'],
                'properties': {
                    'enabled': {'type': 'boolean', 'description': '是否启用'},
                    'status': {'type': 'string', 'enum': ['active', 'inactive', 'maintenance'], 'description': '运行状态'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': '状态更新成功'},
        404: {'description': '模型不存在'}
    }
})
def update_model_status(model_id):
    """启用/停用模型"""
    try:
        db = g.db
        data = request.get_json()
        
        model = db.query(AIModel).filter(AIModel.model_id == model_id).first()
        if not model:
            return jsonify({
                'success': False,
                'message': f'模型 {model_id} 不存在'
            }), 404
        
        # 更新启用状态
        model.enabled = data['enabled']
        
        # 更新运行状态
        if 'status' in data:
            try:
                model.status = ModelStatus(data['status'])
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': f'无效的状态: {data["status"]}'
                }), 400
        else:
            # 根据启用状态自动设置运行状态
            model.status = ModelStatus.ACTIVE if data['enabled'] else ModelStatus.INACTIVE
        
        model.updated_by = g.current_user.get('user_id', 'system')
        model.updated_at = datetime.now()
        
        db.commit()
        
        action = "启用" if data['enabled'] else "停用"
        return jsonify({
            'success': True,
            'message': f'模型{action}成功',
            'data': {
                'model_id': model_id,
                'enabled': model.enabled,
                'status': model.status.value
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating model status: {e}")
        return jsonify({
            'success': False,
            'message': '更新模型状态时发生错误'
        }), 500

# =====================================================
# 健康检查接口
# =====================================================

@model_mgmt_bp.route('/models/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        db = get_db()
        # 简单的数据库连接测试
        db.execute('SELECT 1')
        db.close()
        
        return jsonify({
            'success': True,
            'message': '模型管理API服务正常',
            'service': 'model_management_api',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'message': '服务异常',
            'service': 'model_management_api',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500