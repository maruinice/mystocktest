"""
模型管理系统 Flask API
提供完整的AI模型管理、组合管理、测试和监控功能
"""

import os
import logging
import asyncio
import json
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from functools import wraps

from flask import Flask, Blueprint, request, jsonify, g
from flask_cors import CORS
from flasgger import Swagger, swag_from
from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# 导入数据模型
from ..models.model_management import (
    Base, AIModel, ModelEnsemble, EnsembleModelMapping, 
    ModelTestRecord, ModelMetric, ModelAPIKey, ModelUsageLog,
    ModelType, ModelStatus, HealthStatus, WeightStrategy, VotingMethod, TestType
)
from ..middleware.auth import require_auth
from ..services.encryption_service import encryption_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
model_mgmt_bp = Blueprint('model_management', __name__, url_prefix='/api')

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

# 在启动时确保模型管理相关表结构存在（避免首次运行由于缺表导致500）
try:
    Base.metadata.create_all(bind=engine)
    logger.info("模型管理数据库表已确保存在")
except Exception as e:
    logger.warning(f"初始化模型管理数据库表失败: {e}")

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
            status='inactive',
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
        }), 200
        
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
        models_data = []
        for model in result['items']:
            model_dict = model_to_dict(model)
            # 移除敏感信息
            model_dict.pop('api_key_encrypted', None)
            models_data.append(model_dict)
        
        return jsonify({
            'success': True,
            'message': '获取模型列表成功',
            'data': {
                'items': models_data,
                'total': result['total'],
                'page': result['page'],
                'per_page': result['per_page'],
                'pages': result['pages']
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
        
        model_data = model_to_dict(model)
        model_data.pop('api_key_encrypted', None)
        
        return jsonify({
            'success': True,
            'message': '模型更新成功',
            'data': model_data
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
            valid_statuses = ['active', 'inactive', 'training', 'error', 'maintenance']
            if data['status'] not in valid_statuses:
                return jsonify({
                    'success': False,
                    'message': f'无效的状态: {data["status"]}'
                }), 400
            model.status = data['status']
        else:
            # 根据启用状态自动设置运行状态
            model.status = 'active' if data['enabled'] else 'inactive'
        
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
                'status': model.status
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating model status: {e}")
        return jsonify({
            'success': False,
            'message': '更新模型状态时发生错误'
        }), 500

# =====================================================
# 2. 模型组合管理API
# =====================================================

@model_mgmt_bp.route('/ensembles', methods=['POST'])
@require_auth
@validate_json_request(['name', 'weight_strategy'])
@with_db_session
@swag_from({
    'tags': ['模型组合'],
    'summary': '创建模型组合',
    'description': '创建新的模型组合',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['name', 'weight_strategy'],
            'properties': {
                'name': {'type': 'string', 'description': '组合名称'},
                'weight_strategy': {'type': 'string', 'enum': ['equal_weight', 'accuracy_weight', 'manual_weight', 'dynamic_weight']},
                'display_name': {'type': 'string', 'description': '显示名称'},
                'description': {'type': 'string', 'description': '组合描述'},
                'voting_method': {'type': 'string', 'enum': ['majority', 'weighted', 'confidence', 'threshold']},
                'confidence_threshold': {'type': 'number', 'description': '置信度阈值'},
                'config_json': {'type': 'object', 'description': '扩展配置'}
            }
        }
    }],
    'responses': {
        201: {'description': '创建成功'},
        400: {'description': '请求参数错误'},
        409: {'description': '组合名称已存在'}
    }
})
def create_ensemble():
    """创建模型组合"""
    try:
        data = request.get_json()
        db = g.db
        
        # 检查组合名称是否已存在
        existing_ensemble = db.query(ModelEnsemble).filter(ModelEnsemble.name == data['name']).first()
        if existing_ensemble:
            return jsonify({
                'success': False,
                'message': f'组合名称 "{data["name"]}" 已存在'
            }), 409
        
        # 生成组合ID
        ensemble_id = f"ensemble_{data['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建组合实例
        ensemble = ModelEnsemble(
            ensemble_id=ensemble_id,
            name=data['name'],
            display_name=data.get('display_name', data['name']),
            description=data.get('description', ''),
            weight_strategy=WeightStrategy(data['weight_strategy']),
            voting_method=VotingMethod(data.get('voting_method', 'weighted')),
            confidence_threshold=Decimal(str(data.get('confidence_threshold', 0.5))),
            config_json=data.get('config_json', {}),
            status='inactive',
            enabled=False,
            health_status=HealthStatus.UNKNOWN,
            created_by=g.current_user.get('user_id', 'system')
        )
        
        db.add(ensemble)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '模型组合创建成功',
            'data': model_to_dict(ensemble)
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'参数错误: {str(e)}'
        }), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error creating ensemble: {e}")
        return jsonify({
            'success': False,
            'message': '数据库错误，创建组合失败'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error creating ensemble: {e}")
        return jsonify({
            'success': False,
            'message': '创建组合时发生未知错误'
        }), 500

@model_mgmt_bp.route('/ensembles', methods=['GET'])
@require_auth
@with_db_session
@swag_from({
    'tags': ['模型组合'],
    'summary': '获取组合列表',
    'description': '获取模型组合列表，支持搜索和分页',
    'parameters': [
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1, 'description': '页码'},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 20, 'description': '每页数量'},
        {'name': 'search', 'in': 'query', 'type': 'string', 'description': '搜索关键词'},
        {'name': 'status', 'in': 'query', 'type': 'string', 'description': '状态过滤'},
        {'name': 'enabled', 'in': 'query', 'type': 'boolean', 'description': '启用状态过滤'}
    ],
    'responses': {
        200: {'description': '获取成功'}
    }
})
def get_ensembles():
    """获取组合列表"""
    try:
        db = g.db
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        search = request.args.get('search', '').strip()
        status = request.args.get('status')
        enabled = request.args.get('enabled')
        
        # 构建查询
        query = db.query(ModelEnsemble)
        
        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    ModelEnsemble.name.contains(search),
                    ModelEnsemble.display_name.contains(search),
                    ModelEnsemble.description.contains(search)
                )
            )
        
        # 状态过滤
        if status:
            query = query.filter(ModelEnsemble.status == status)
        
        # 启用状态过滤
        if enabled is not None:
            enabled_bool = enabled.lower() in ('true', '1', 'yes')
            query = query.filter(ModelEnsemble.enabled == enabled_bool)
        
        # 排序
        query = query.order_by(desc(ModelEnsemble.created_at))
        
        # 分页
        result = paginate_query(query, page, per_page)
        
        # 转换为字典格式并添加模型信息
        ensembles_data = []
        for ensemble in result['items']:
            ensemble_dict = model_to_dict(ensemble)
            
            # 获取组合中的模型信息
            mappings = db.query(EnsembleModelMapping).filter(
                EnsembleModelMapping.ensemble_id == ensemble.ensemble_id
            ).all()
            
            models_info = []
            for mapping in mappings:
                model = db.query(AIModel).filter(AIModel.model_id == mapping.model_id).first()
                if model:
                    models_info.append({
                        'model_id': model.model_id,
                        'name': model.name,
                        'weight': float(mapping.weight),
                        'priority': mapping.priority,
                        'enabled': mapping.enabled
                    })
            
            ensemble_dict['models'] = models_info
            ensembles_data.append(ensemble_dict)
        
        return jsonify({
            'success': True,
            'message': '获取组合列表成功',
            'data': {
                'items': ensembles_data,
                'total': result['total'],
                'page': result['page'],
                'per_page': result['per_page'],
                'pages': result['pages']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting ensembles: {e}")
        return jsonify({
            'success': False,
            'message': '获取组合列表时发生错误'
        }), 500

@model_mgmt_bp.route('/ensembles/<ensemble_id>/models', methods=['POST'])
@require_auth
@validate_json_request(['model_id'])
@with_db_session
@swag_from({
    'tags': ['模型组合'],
    'summary': '添加模型到组合',
    'description': '将模型添加到指定的组合中',
    'parameters': [
        {'name': 'ensemble_id', 'in': 'path', 'type': 'string', 'required': True, 'description': '组合ID'},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['model_id'],
                'properties': {
                    'model_id': {'type': 'string', 'description': '模型ID'},
                    'weight': {'type': 'number', 'description': '权重', 'default': 1.0},
                    'priority': {'type': 'integer', 'description': '优先级', 'default': 1}
                }
            }
        }
    ],
    'responses': {
        201: {'description': '添加成功'},
        404: {'description': '组合或模型不存在'},
        409: {'description': '模型已在组合中'}
    }
})
def add_model_to_ensemble(ensemble_id):
    """添加模型到组合"""
    try:
        data = request.get_json()
        db = g.db
        
        # 检查组合是否存在
        ensemble = db.query(ModelEnsemble).filter(ModelEnsemble.ensemble_id == ensemble_id).first()
        if not ensemble:
            return jsonify({
                'success': False,
                'message': f'组合 {ensemble_id} 不存在'
            }), 404
        
        # 检查模型是否存在
        model = db.query(AIModel).filter(AIModel.model_id == data['model_id']).first()
        if not model:
            return jsonify({
                'success': False,
                'message': f'模型 {data["model_id"]} 不存在'
            }), 404
        
        # 检查模型是否已在组合中
        existing_mapping = db.query(EnsembleModelMapping).filter(
            and_(
                EnsembleModelMapping.ensemble_id == ensemble_id,
                EnsembleModelMapping.model_id == data['model_id']
            )
        ).first()
        
        if existing_mapping:
            return jsonify({
                'success': False,
                'message': '模型已在组合中'
            }), 409
        
        # 创建关联记录
        mapping_id = f"mapping_{ensemble_id}_{data['model_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        mapping = EnsembleModelMapping(
            mapping_id=mapping_id,
            ensemble_id=ensemble_id,
            model_id=data['model_id'],
            weight=Decimal(str(data.get('weight', 1.0))),
            priority=data.get('priority', 1),
            enabled=True,
            status='active',
            created_by=g.current_user.get('user_id', 'system')
        )
        
        db.add(mapping)
        
        # 更新组合的模型数量
        ensemble.model_count = db.query(EnsembleModelMapping).filter(
            EnsembleModelMapping.ensemble_id == ensemble_id
        ).count() + 1
        
        ensemble.active_model_count = db.query(EnsembleModelMapping).filter(
            and_(
                EnsembleModelMapping.ensemble_id == ensemble_id,
                EnsembleModelMapping.enabled == True
            )
        ).count() + 1
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '模型添加到组合成功',
            'data': model_to_dict(mapping)
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding model to ensemble: {e}")
        return jsonify({
            'success': False,
            'message': '添加模型到组合时发生错误'
        }), 500

@model_mgmt_bp.route('/ensembles/<ensemble_id>/models/<model_id>', methods=['DELETE'])
@require_auth
@with_db_session
@swag_from({
    'tags': ['模型组合'],
    'summary': '从组合移除模型',
    'description': '从指定组合中移除模型',
    'parameters': [
        {'name': 'ensemble_id', 'in': 'path', 'type': 'string', 'required': True, 'description': '组合ID'},
        {'name': 'model_id', 'in': 'path', 'type': 'string', 'required': True, 'description': '模型ID'}
    ],
    'responses': {
        200: {'description': '移除成功'},
        404: {'description': '组合、模型或关联不存在'}
    }
})
def remove_model_from_ensemble(ensemble_id, model_id):
    """从组合移除模型"""
    try:
        db = g.db
        
        # 查找关联记录
        mapping = db.query(EnsembleModelMapping).filter(
            and_(
                EnsembleModelMapping.ensemble_id == ensemble_id,
                EnsembleModelMapping.model_id == model_id
            )
        ).first()
        
        if not mapping:
            return jsonify({
                'success': False,
                'message': '模型不在指定组合中'
            }), 404
        
        # 删除关联记录
        db.delete(mapping)
        
        # 更新组合的模型数量
        ensemble = db.query(ModelEnsemble).filter(ModelEnsemble.ensemble_id == ensemble_id).first()
        if ensemble:
            ensemble.model_count = db.query(EnsembleModelMapping).filter(
                EnsembleModelMapping.ensemble_id == ensemble_id
            ).count() - 1
            
            ensemble.active_model_count = db.query(EnsembleModelMapping).filter(
                and_(
                    EnsembleModelMapping.ensemble_id == ensemble_id,
                    EnsembleModelMapping.enabled == True
                )
            ).count() - (1 if mapping.enabled else 0)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '模型从组合中移除成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Error removing model from ensemble: {e}")
        return jsonify({
            'success': False,
            'message': '从组合移除模型时发生错误'
        }), 500

# =====================================================
# 3. 仪表盘数据API
# =====================================================

@model_mgmt_bp.route('/dashboard/stats', methods=['GET'])
@require_auth
@with_db_session
@swag_from({
    'tags': ['仪表盘'],
    'summary': '获取统计信息',
    'description': '获取模型管理系统的统计信息',
    'responses': {
        200: {'description': '获取成功'}
    }
})
def get_dashboard_stats():
    """获取统计信息"""
    try:
        db = g.db
        
        # 模型统计
        total_models = db.query(AIModel).count()
        active_models = db.query(AIModel).filter(AIModel.enabled == True).count()
        inactive_models = total_models - active_models
        
        # 组合统计
        total_ensembles = db.query(ModelEnsemble).count()
        active_ensembles = db.query(ModelEnsemble).filter(ModelEnsemble.enabled == True).count()
        
        # 平均准确率
        avg_accuracy = db.query(func.avg(AIModel.accuracy_rate)).filter(
            AIModel.enabled == True
        ).scalar() or 0
        
        # 今日测试次数
        today = date.today()
        today_tests = db.query(ModelTestRecord).filter(
            func.date(ModelTestRecord.created_at) == today
        ).count()
        
        # 模型类型分布
        model_types = db.query(
            AIModel.model_type,
            func.count(AIModel.model_id).label('count')
        ).group_by(AIModel.model_type).all()
        
        type_distribution = {}
        for model_type, count in model_types:
            type_distribution[model_type.value] = count
        
        # 健康状态分布
        health_stats = db.query(
            AIModel.health_status,
            func.count(AIModel.model_id).label('count')
        ).group_by(AIModel.health_status).all()
        
        health_distribution = {}
        for health_status, count in health_stats:
            health_distribution[health_status.value] = count
        
        return jsonify({
            'success': True,
            'message': '获取统计信息成功',
            'data': {
                'models': {
                    'total': total_models,
                    'active': active_models,
                    'inactive': inactive_models,
                    'avg_accuracy': float(avg_accuracy) if avg_accuracy else 0.0
                },
                'ensembles': {
                    'total': total_ensembles,
                    'active': active_ensembles
                },
                'tests': {
                    'today': today_tests
                },
                'distributions': {
                    'model_types': type_distribution,
                    'health_status': health_distribution
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'success': False,
            'message': '获取统计信息时发生错误'
        }), 500

@model_mgmt_bp.route('/dashboard/performance', methods=['GET'])
@require_auth
@with_db_session
@swag_from({
    'tags': ['仪表盘'],
    'summary': '获取性能指标',
    'description': '获取模型性能指标数据',
    'parameters': [
        {'name': 'days', 'in': 'query', 'type': 'integer', 'default': 7, 'description': '查询天数'},
        {'name': 'model_id', 'in': 'query', 'type': 'string', 'description': '特定模型ID'}
    ],
    'responses': {
        200: {'description': '获取成功'}
    }
})
def get_dashboard_performance():
    """获取性能指标"""
    try:
        db = g.db
        
        days = int(request.args.get('days', 7))
        model_id = request.args.get('model_id')
        
        # 计算日期范围
        end_date = date.today()
        start_date = date.fromordinal(end_date.toordinal() - days + 1)
        
        # 构建查询
        query = db.query(ModelMetric).filter(
            and_(
                ModelMetric.metric_date >= start_date,
                ModelMetric.metric_date <= end_date,
                ModelMetric.time_period == 'daily'
            )
        )
        
        if model_id:
            query = query.filter(ModelMetric.model_id == model_id)
        
        metrics = query.order_by(ModelMetric.metric_date).all()
        
        # 按日期组织数据
        performance_data = {}
        for metric in metrics:
            date_str = metric.metric_date.isoformat()
            if date_str not in performance_data:
                performance_data[date_str] = {
                    'date': date_str,
                    'accuracy_rate': [],
                    'avg_response_time': [],
                    'success_rate': [],
                    'total_requests': 0
                }
            
            performance_data[date_str]['accuracy_rate'].append(float(metric.accuracy_rate) if metric.accuracy_rate else 0)
            performance_data[date_str]['avg_response_time'].append(metric.avg_response_time_ms or 0)
            performance_data[date_str]['success_rate'].append(float(metric.success_rate) if metric.success_rate else 0)
            performance_data[date_str]['total_requests'] += metric.total_requests or 0
        
        # 计算每日平均值
        daily_performance = []
        for date_str, data in performance_data.items():
            daily_performance.append({
                'date': date_str,
                'avg_accuracy': sum(data['accuracy_rate']) / len(data['accuracy_rate']) if data['accuracy_rate'] else 0,
                'avg_response_time': sum(data['avg_response_time']) / len(data['avg_response_time']) if data['avg_response_time'] else 0,
                'avg_success_rate': sum(data['success_rate']) / len(data['success_rate']) if data['success_rate'] else 0,
                'total_requests': data['total_requests']
            })
        
        # 按日期排序
        daily_performance.sort(key=lambda x: x['date'])
        
        return jsonify({
            'success': True,
            'message': '获取性能指标成功',
            'data': {
                'daily_performance': daily_performance,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard performance: {e}")
        return jsonify({
            'success': False,
            'message': '获取性能指标时发生错误'
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