"""
模型管理占位接口（Stub）
当真实模型管理模块无法加载时，提供基本端点以保证前端可用
"""

from flask import Blueprint, jsonify, request
from datetime import datetime

# 与真实模块保持一致的蓝图名称与前缀
model_mgmt_bp = Blueprint('model_management', __name__, url_prefix='/api')


@model_mgmt_bp.route('/model-management/models', methods=['GET'])
def stub_get_models():
    """获取模型列表 - 从数据库读取真实数据"""
    from app.core.database import SessionLocal
    from sqlalchemy import text
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    db = SessionLocal()
    try:
        # 查询模型数据
        result = db.execute(text("SELECT * FROM ai_models WHERE enabled = 1"))
        rows = result.fetchall()
        columns = result.keys()
        
        # 转换为字典列表
        items = []
        for row in rows:
            model_dict = dict(zip(columns, row))
            items.append({
                'model_id': model_dict.get('model_id'),
                'name': model_dict.get('name'),
                'display_name': model_dict.get('display_name') or model_dict.get('name'),
                'description': model_dict.get('description'),
                'model_type': model_dict.get('model_type'),
                'provider': model_dict.get('provider'),
                'enabled': bool(model_dict.get('enabled')),
                'status': model_dict.get('status'),
                'created_at': str(model_dict.get('created_at')) if model_dict.get('created_at') else None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'items': items,
                'total': len(items),
                'page': page,
                'per_page': per_page,
                'pages': (len(items) + per_page - 1) // per_page
            }
        }), 200
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'查询失败: {str(e)}',
            'data': {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'pages': 0
            }
        }), 500
    finally:
        db.close()


@model_mgmt_bp.route('/models', methods=['POST'])
def stub_create_model():
    data = request.get_json(silent=True) or {}
    # 生成一个临时ID（不持久化）
    import uuid
    model_id = f"stub_{uuid.uuid4().hex[:8]}"
    model = {
        'model_id': model_id,
        'name': data.get('name', f'Model-{model_id}'),
        'display_name': data.get('display_name', data.get('name', f'Model-{model_id}')),
        'description': data.get('description', ''),
        'model_type': data.get('model_type', 'Custom'),
        'provider': data.get('provider', 'CustomProvider'),
        'model_version': data.get('model_version'),
        'base_url': data.get('base_url'),
        'api_key_encrypted': None,
        'max_tokens': data.get('max_tokens', 4096),
        'temperature': data.get('temperature', 0.7),
        'config_json': data.get('config_json', {}),
        'status': 'inactive',
        'enabled': False,
        'health_status': 'unknown',
        'created_at': datetime.now().isoformat()
    }
    return jsonify({
        'success': True,
        'message': 'stub: model created (not persisted)',
        'data': model
    }), 201


@model_mgmt_bp.route('/ensembles', methods=['GET'])
def stub_get_ensembles():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    return jsonify({
        'success': True,
        'message': 'stub: ensembles list',
        'data': {
            'items': [],
            'total': 0,
            'page': page,
            'per_page': per_page,
            'pages': 0
        }
    }), 200


@model_mgmt_bp.route('/dashboard/stats', methods=['GET'])
def stub_dashboard_stats():
    return jsonify({
        'success': True,
        'message': 'stub: dashboard stats',
        'data': {
            'total_models': 0,
            'active_models': 0,
            'avg_accuracy': 0.0,
            'avg_response_time': 0.0,
            'total_requests': 0,
            'success_rate': 0.0
        }
    }), 200


@model_mgmt_bp.route('/dashboard/performance', methods=['GET'])
def stub_dashboard_performance():
    days = int(request.args.get('days', 7))
    return jsonify({
        'success': True,
        'message': 'stub: performance metrics',
        'data': {
            'days': days,
            'metrics': []
        }
    }), 200


@model_mgmt_bp.route('/models/health', methods=['GET'])
def stub_models_health():
    return jsonify({
        'success': True,
        'message': 'stub: health ok',
        'data': {
            'service': 'model_management_stub',
            'status': 'ok',
            'timestamp': datetime.now().isoformat()
        }
    }), 200