"""
Agent API - Flask版本
提供Agent管理和多Agent分析的REST API
"""
import asyncio
import logging
from flask import Blueprint, request, jsonify, g
from typing import Dict, Any
from datetime import datetime

from app.middleware.auth import require_auth
from app.core.database import SessionLocal
from app.services.agent_service import AgentService
from app.services.multi_agent_engine import MultiAgentEngine
from app.models.agent_models import SessionType

logger = logging.getLogger(__name__)

# 创建Agent蓝图
agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')


def get_db():
    """获取数据库会话"""
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db


@agent_bp.teardown_app_request
def close_db(error):
    """关闭数据库会话"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ==================== Agent管理 ====================

@agent_bp.route('/agents', methods=['GET'])
@require_auth
def list_agents():
    """获取Agent列表"""
    try:
        db = get_db()
        service = AgentService(db)
        
        agent_type = request.args.get('agent_type')
        enabled = request.args.get('enabled')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        if enabled is not None:
            enabled = enabled.lower() == 'true'
        
        result = service.list_agents(
            agent_type=agent_type,
            enabled=enabled,
            page=page,
            page_size=page_size
        )
        
        # 转换为字典
        items = []
        for agent in result['items']:
            items.append({
                'agent_id': agent.agent_id,
                'name': agent.name,
                'display_name': agent.display_name,
                'description': agent.description,
                'agent_type': agent.agent_type,
                'model_id': agent.model_id,
                'enabled': agent.enabled,
                'priority': agent.priority,
                'weight': agent.weight,
                'total_analyses': agent.total_analyses,
                'success_analyses': agent.success_analyses,
                'avg_score': agent.avg_score,
                'created_at': agent.created_at.isoformat() if agent.created_at else None,
                'updated_at': agent.updated_at.isoformat() if agent.updated_at else None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total': result['total'],
                'page': result['page'],
                'page_size': result['page_size'],
                'items': items
            }
        })
        
    except Exception as e:
        logger.error(f"获取Agent列表失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


@agent_bp.route('/agents/<agent_id>', methods=['GET'])
@require_auth
def get_agent(agent_id):
    """获取Agent详情"""
    try:
        db = get_db()
        service = AgentService(db)
        
        agent = service.get_agent(agent_id)
        if not agent:
            return jsonify({'code': 404, 'message': 'Agent不存在'}), 404
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'agent_id': agent.agent_id,
                'name': agent.name,
                'display_name': agent.display_name,
                'description': agent.description,
                'agent_type': agent.agent_type,
                'model_id': agent.model_id,
                'system_prompt': agent.system_prompt,
                'enabled': agent.enabled,
                'priority': agent.priority,
                'weight': agent.weight,
                'config_json': agent.config_json,
                'total_analyses': agent.total_analyses,
                'success_analyses': agent.success_analyses,
                'avg_score': agent.avg_score,
                'created_at': agent.created_at.isoformat() if agent.created_at else None,
                'updated_at': agent.updated_at.isoformat() if agent.updated_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"获取Agent详情失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


@agent_bp.route('/agents', methods=['POST'])
@require_auth
def create_agent():
    """创建Agent"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'agent_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'code': 400, 'message': f'缺少必填字段: {field}'}), 400
        
        db = get_db()
        service = AgentService(db)
        
        # 添加创建者信息
        data['created_by'] = g.user.get('user_id') if hasattr(g, 'user') else None
        
        agent = service.create_agent(data)
        
        return jsonify({
            'code': 200,
            'message': 'Agent创建成功',
            'data': {
                'agent_id': agent.agent_id,
                'name': agent.name
            }
        })
        
    except Exception as e:
        logger.error(f"创建Agent失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


@agent_bp.route('/agents/<agent_id>', methods=['PUT'])
@require_auth
def update_agent(agent_id):
    """更新Agent"""
    try:
        data = request.get_json()
        
        db = get_db()
        service = AgentService(db)
        
        # 添加更新者信息
        data['updated_by'] = g.user.get('user_id') if hasattr(g, 'user') else None
        
        agent = service.update_agent(agent_id, data)
        if not agent:
            return jsonify({'code': 404, 'message': 'Agent不存在'}), 404
        
        return jsonify({
            'code': 200,
            'message': 'Agent更新成功',
            'data': {
                'agent_id': agent.agent_id,
                'name': agent.name
            }
        })
        
    except Exception as e:
        logger.error(f"更新Agent失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


@agent_bp.route('/agents/<agent_id>', methods=['DELETE'])
@require_auth
def delete_agent(agent_id):
    """删除Agent"""
    try:
        db = get_db()
        service = AgentService(db)
        
        success = service.delete_agent(agent_id)
        if not success:
            return jsonify({'code': 404, 'message': 'Agent不存在'}), 404
        
        return jsonify({
            'code': 200,
            'message': 'Agent删除成功'
        })
        
    except Exception as e:
        logger.error(f"删除Agent失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


@agent_bp.route('/agents/<agent_id>/toggle', methods=['POST'])
@require_auth
def toggle_agent_status(agent_id):
    """切换Agent启用状态"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        
        db = get_db()
        service = AgentService(db)
        
        agent = service.toggle_agent_status(agent_id, enabled)
        if not agent:
            return jsonify({'code': 404, 'message': 'Agent不存在'}), 404
        
        return jsonify({
            'code': 200,
            'message': f"Agent已{'启用' if enabled else '禁用'}",
            'data': {
                'agent_id': agent.agent_id,
                'enabled': agent.enabled
            }
        })
        
    except Exception as e:
        logger.error(f"切换Agent状态失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


# ==================== 分析功能 ====================

@agent_bp.route('/analyze/single', methods=['POST'])
@require_auth
def analyze_single_stock():
    """单股分析"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        stock_code = data.get('stock_code')
        agent_ids = data.get('agent_ids', [])
        
        if not stock_code:
            return jsonify({'code': 400, 'message': '缺少股票代码'}), 400
        if not agent_ids:
            return jsonify({'code': 400, 'message': '缺少Agent配置'}), 400
        
        db = get_db()
        service = AgentService(db)
        engine = MultiAgentEngine(db)
        
        # 创建分析会话
        session = service.create_session({
            'session_type': SessionType.SINGLE_STOCK.value,
            'stock_codes': [stock_code],
            'agent_ids': agent_ids,
            'created_by': g.user.get('user_id') if hasattr(g, 'user') else None
        })
        
        # 执行分析（同步转异步）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            engine.analyze_stock(session.session_id, stock_code, agent_ids)
        )
        loop.close()
        
        # 更新会话状态
        service.update_session_status(session.session_id, 'completed', 100)
        
        # 保存选股结果
        service.create_selection_result({
            'session_id': session.session_id,
            'scheme_id': data.get('scheme_id'),
            'stock_code': stock_code,
            **result
        })
        
        return jsonify({
            'code': 200,
            'message': '分析完成',
            'data': {
                'session_id': session.session_id,
                **result
            }
        })
        
    except Exception as e:
        logger.error(f"单股分析失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


@agent_bp.route('/analyze/batch', methods=['POST'])
@require_auth
def analyze_batch_stocks():
    """批量分析"""
    try:
        data = request.get_json()
        
        stock_codes = data.get('stock_codes', [])
        agent_ids = data.get('agent_ids', [])
        
        if not stock_codes:
            return jsonify({'code': 400, 'message': '缺少股票代码列表'}), 400
        if not agent_ids:
            return jsonify({'code': 400, 'message': '缺少Agent配置'}), 400
        
        db = get_db()
        service = AgentService(db)
        engine = MultiAgentEngine(db)
        
        # 创建分析会话
        session = service.create_session({
            'session_type': SessionType.BATCH_ANALYSIS.value,
            'stock_codes': stock_codes,
            'agent_ids': agent_ids,
            'created_by': g.user.get('user_id') if hasattr(g, 'user') else None
        })
        
        # 更新会话状态为运行中
        service.update_session_status(session.session_id, 'running', 0)
        
        # 执行批量分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(
            engine.batch_analyze(session.session_id, stock_codes, agent_ids)
        )
        loop.close()
        
        # 保存所有结果
        for result in results:
            service.create_selection_result({
                'session_id': session.session_id,
                'scheme_id': data.get('scheme_id'),
                'stock_code': result.get('market_data_snapshot', {}).get('stock_code'),
                **result
            })
        
        # 更新会话状态
        service.update_session_status(session.session_id, 'completed', 100)
        
        return jsonify({
            'code': 200,
            'message': '批量分析完成',
            'data': {
                'session_id': session.session_id,
                'total': len(results),
                'results': results[:10]  # 只返回前10个
            }
        })
        
    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


# ==================== 选股方案 ====================

@agent_bp.route('/schemes', methods=['GET'])
@require_auth
def list_schemes():
    """获取选股方案列表"""
    try:
        db = get_db()
        service = AgentService(db)
        
        enabled = request.args.get('enabled')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        if enabled is not None:
            enabled = enabled.lower() == 'true'
        
        result = service.list_schemes(enabled=enabled, page=page, page_size=page_size)
        
        items = []
        for scheme in result['items']:
            items.append({
                'scheme_id': scheme.scheme_id,
                'name': scheme.name,
                'description': scheme.description,
                'enabled': scheme.enabled,
                'total_runs': scheme.total_runs,
                'last_run_at': scheme.last_run_at.isoformat() if scheme.last_run_at else None,
                'created_at': scheme.created_at.isoformat() if scheme.created_at else None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total': result['total'],
                'page': result['page'],
                'page_size': result['page_size'],
                'items': items
            }
        })
        
    except Exception as e:
        logger.error(f"获取选股方案列表失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


@agent_bp.route('/schemes', methods=['POST'])
@require_auth
def create_scheme():
    """创建选股方案"""
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'code': 400, 'message': '缺少方案名称'}), 400
        
        db = get_db()
        service = AgentService(db)
        
        data['created_by'] = g.user.get('user_id') if hasattr(g, 'user') else None
        
        scheme = service.create_scheme(data)
        
        return jsonify({
            'code': 200,
            'message': '选股方案创建成功',
            'data': {
                'scheme_id': scheme.scheme_id,
                'name': scheme.name
            }
        })
        
    except Exception as e:
        logger.error(f"创建选股方案失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


# ==================== 分析会话和结果 ====================

@agent_bp.route('/sessions', methods=['GET'])
@require_auth
def list_sessions():
    """获取分析会话列表"""
    try:
        db = get_db()
        service = AgentService(db)
        
        session_type = request.args.get('session_type')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        result = service.list_sessions(
            session_type=session_type,
            status=status,
            page=page,
            page_size=page_size
        )
        
        items = []
        for session in result['items']:
            items.append({
                'session_id': session.session_id,
                'session_type': session.session_type,
                'total_stocks': session.total_stocks,
                'completed_stocks': session.completed_stocks,
                'status': session.status,
                'progress': session.progress,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total': result['total'],
                'page': result['page'],
                'page_size': result['page_size'],
                'items': items
            }
        })
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


@agent_bp.route('/sessions/<session_id>/results', methods=['GET'])
@require_auth
def get_session_results(session_id):
    """获取会话的选股结果"""
    try:
        db = get_db()
        service = AgentService(db)
        
        order_by = request.args.get('order_by', 'score')
        results = service.get_session_results(session_id, order_by=order_by)
        
        items = []
        for result in results:
            items.append({
                'result_id': result.result_id,
                'stock_code': result.stock_code,
                'stock_name': result.stock_name,
                'final_score': result.final_score,
                'recommendation': result.recommendation,
                'consensus_level': result.consensus_level,
                'risk_level': result.risk_level,
                'summary': result.summary,
                'rank': result.rank,
                'agent_scores': result.agent_scores,
                'strengths': result.strengths,
                'weaknesses': result.weaknesses
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': items
        })
        
    except Exception as e:
        logger.error(f"获取会话结果失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500


@agent_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'code': 200,
        'message': 'Agent API is healthy',
        'data': {
            'service': 'agent_api',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    })
