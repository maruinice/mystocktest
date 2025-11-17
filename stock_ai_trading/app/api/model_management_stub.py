"""
模型管理占位接口（Stub）
当真实模型管理模块无法加载时，提供基本端点以保证前端可用
"""

from flask import Blueprint, jsonify, request
from datetime import datetime

# 与真实模块保持一致的蓝图名称与前缀
model_mgmt_bp = Blueprint('model_management', __name__, url_prefix='/api')


@model_mgmt_bp.route('/models', methods=['GET'])
def stub_get_models():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    return jsonify({
        'success': True,
        'message': 'stub: models list',
        'data': {
            'items': [],
            'total': 0,
            'page': page,
            'per_page': per_page,
            'pages': 0
        }
    }), 200


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