"""
选股功能API接口
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
import asyncio
import logging

from app.services.stock_screening_service import stock_screening_service
from app.services.screening_data_service import screening_data_service
from app.services.tushare_daily_service import tushare_daily_service
from app.middleware.auth import require_auth

logger = logging.getLogger(__name__)

# 创建蓝图
screening_bp = Blueprint('screening', __name__)


def async_route(f):
    """异步路由装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


@screening_bp.route('/strategies', methods=['GET'])
@require_auth
@async_route
async def get_strategies():
    """获取选股策略列表"""
    try:
        user_id = g.current_user.get('id')
        result = await stock_screening_service.get_available_strategies(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@screening_bp.route('/indicators', methods=['GET'])
@async_route
async def get_indicators():
    """获取可用的筛选指标"""
    try:
        result = await stock_screening_service.get_screening_indicators()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取指标列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@screening_bp.route('/execute', methods=['POST'])
@async_route
async def execute_screening():
    """执行选股"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        strategy_id = data.get('strategy_id')
        if not strategy_id:
            return jsonify({
                'success': False,
                'message': '策略ID不能为空'
            }), 400
        
        user_id = getattr(g, 'current_user', {}).get('id')
        custom_conditions = data.get('conditions')
        
        result = await stock_screening_service.execute_screening(
            strategy_id=strategy_id,
            user_id=user_id,
            custom_conditions=custom_conditions
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"执行选股失败: {e}")
        return jsonify({
            'success': False,
            'message': f'执行失败: {str(e)}'
        }), 500


@screening_bp.route('/results/<task_id>', methods=['GET'])
@async_route
async def get_screening_result(task_id):
    """获取选股结果"""
    try:
        result = await stock_screening_service.get_screening_result(task_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取选股结果失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@screening_bp.route('/data/sync-three-years', methods=['POST'])
@async_route
async def sync_three_years_data():
    """同步三年历史数据"""
    try:
        data = request.get_json() or {}
        end_date = data.get('end_date')
        
        result = await tushare_daily_service.sync_three_years_data(end_date=end_date)
        return jsonify(result)
    except Exception as e:
        logger.error(f"同步三年历史数据失败: {e}")
        return jsonify({
            'success': False,
            'message': f'同步失败: {str(e)}'
        }), 500

@screening_bp.route('/data/sync-daily-history', methods=['POST'])
@async_route
async def sync_daily_history():
    """同步每日历史行情数据"""
    try:
        data = request.get_json() or {}
        
        # 获取参数
        trade_date = data.get('trade_date')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        ts_codes = data.get('ts_codes')
        
        result = await tushare_daily_service.sync_daily_data(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            ts_codes=ts_codes
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"同步每日历史行情数据失败: {e}")
        return jsonify({
            'success': False,
            'message': f'同步失败: {str(e)}'
        }), 500

@screening_bp.route('/data/sync-stock-basic', methods=['POST'])
@async_route
async def sync_stock_basic():
    """同步股票基础信息"""
    try:
        result = await screening_data_service.sync_stock_basic()
        return jsonify(result)
    except Exception as e:
        logger.error(f"同步股票基础信息失败: {e}")
        return jsonify({
            'success': False,
            'message': f'同步失败: {str(e)}'
        }), 500

@screening_bp.route('/data/sync-quotes', methods=['POST'])
@async_route
async def sync_daily_quotes():
    """同步日线行情数据"""
    try:
        data = request.get_json() or {}
        trade_date = data.get('trade_date')
        ts_codes = data.get('ts_codes')
        
        result = await screening_data_service.sync_daily_quotes(
            trade_date=trade_date,
            ts_codes=ts_codes
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"同步日线数据失败: {e}")
        return jsonify({
            'success': False,
            'message': f'同步失败: {str(e)}'
        }), 500


@screening_bp.route('/data/sync-financial', methods=['POST'])
@async_route
async def sync_financial_data():
    """同步财务指标数据"""
    try:
        data = request.get_json() or {}
        period = data.get('period')
        ts_codes = data.get('ts_codes')
        
        result = await screening_data_service.sync_financial_indicators(
            period=period,
            ts_codes=ts_codes
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"同步财务数据失败: {e}")
        return jsonify({
            'success': False,
            'message': f'同步失败: {str(e)}'
        }), 500


@screening_bp.route('/data/calculate-technical', methods=['POST'])
@async_route
async def calculate_technical_indicators():
    """计算技术指标"""
    try:
        data = request.get_json() or {}
        trade_date = data.get('trade_date')
        ts_codes = data.get('ts_codes')
        
        result = await screening_data_service.calculate_technical_indicators(
            trade_date=trade_date,
            ts_codes=ts_codes
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"计算技术指标失败: {e}")
        return jsonify({
            'success': False,
            'message': f'计算失败: {str(e)}'
        }), 500


@screening_bp.route('/strategies/custom', methods=['POST'])
@async_route
async def create_custom_strategy():
    """创建自定义策略"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        required_fields = ['strategy_name', 'strategy_type', 'conditions']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空'
                }), 400
        
        user_id = getattr(g, 'current_user', {}).get('id', 1)  # 默认用户ID
        
        # 保存自定义策略
        result = await _save_custom_strategy(data, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"创建自定义策略失败: {e}")
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@screening_bp.route('/strategies/<int:strategy_id>', methods=['PUT'])
@async_route
async def update_custom_strategy(strategy_id):
    """更新自定义策略"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        user_id = getattr(g, 'current_user', {}).get('id', 1)
        
        result = await _update_custom_strategy(strategy_id, data, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"更新自定义策略失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@screening_bp.route('/strategies/<int:strategy_id>', methods=['DELETE'])
@async_route
async def delete_custom_strategy(strategy_id):
    """删除自定义策略"""
    try:
        user_id = getattr(g, 'current_user', {}).get('id', 1)
        
        result = await _delete_custom_strategy(strategy_id, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"删除自定义策略失败: {e}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@screening_bp.route('/history', methods=['GET'])
@async_route
async def get_screening_history():
    """获取选股历史"""
    try:
        user_id = getattr(g, 'current_user', {}).get('id', 1)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        result = await _get_user_screening_history(user_id, page, limit)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取选股历史失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@screening_bp.route('/preferences', methods=['GET'])
@async_route
async def get_user_preferences():
    """获取用户选股偏好"""
    try:
        user_id = getattr(g, 'current_user', {}).get('id', 1)
        
        result = await _get_user_preferences(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取用户偏好失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@screening_bp.route('/preferences', methods=['POST'])
@async_route
async def save_user_preferences():
    """保存用户选股偏好"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        user_id = getattr(g, 'current_user', {}).get('id', 1)
        
        result = await _save_user_preferences(user_id, data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"保存用户偏好失败: {e}")
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


# 辅助函数
async def _save_custom_strategy(data, user_id):
    """保存自定义策略"""
    try:
        from app.services.strategy_database_service import strategy_db_service
        import json
        import uuid
        
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # 生成策略代码
            strategy_code = f"custom_{uuid.uuid4().hex[:8]}"
            
            sql = """
            INSERT INTO screening_strategies (
                strategy_name, strategy_code, strategy_type, description,
                config, conditions, sort_rules, creator_id, is_system, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                data['strategy_name'],
                strategy_code,
                data['strategy_type'],
                data.get('description', ''),
                json.dumps(data.get('config', {}), ensure_ascii=False),
                json.dumps(data['conditions'], ensure_ascii=False),
                json.dumps(data.get('sort_rules', {}), ensure_ascii=False),
                user_id,
                False,
                True
            ))
            
            strategy_id = cursor.lastrowid
            conn.commit()
            
            return {
                'success': True,
                'message': '策略创建成功',
                'data': {
                    'strategy_id': strategy_id,
                    'strategy_code': strategy_code
                }
            }
            
    except Exception as e:
        logger.error(f"保存自定义策略失败: {e}")
        return {'success': False, 'message': f'保存失败: {str(e)}'}


async def _update_custom_strategy(strategy_id, data, user_id):
    """更新自定义策略"""
    try:
        from app.services.strategy_database_service import strategy_db_service
        import json
        
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查策略是否存在且属于当前用户
            cursor.execute("""
                SELECT id FROM screening_strategies 
                WHERE id = %s AND (creator_id = %s OR creator_id IS NULL)
            """, (strategy_id, user_id))
            
            if not cursor.fetchone():
                return {'success': False, 'message': '策略不存在或无权限修改'}
            
            # 更新策略
            sql = """
            UPDATE screening_strategies 
            SET strategy_name = %s, description = %s, config = %s, 
                conditions = %s, sort_rules = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            cursor.execute(sql, (
                data.get('strategy_name'),
                data.get('description', ''),
                json.dumps(data.get('config', {}), ensure_ascii=False),
                json.dumps(data.get('conditions', {}), ensure_ascii=False),
                json.dumps(data.get('sort_rules', {}), ensure_ascii=False),
                strategy_id
            ))
            
            conn.commit()
            
            return {
                'success': True,
                'message': '策略更新成功'
            }
            
    except Exception as e:
        logger.error(f"更新自定义策略失败: {e}")
        return {'success': False, 'message': f'更新失败: {str(e)}'}


async def _delete_custom_strategy(strategy_id, user_id):
    """删除自定义策略"""
    try:
        from app.services.strategy_database_service import strategy_db_service
        
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查策略是否存在且属于当前用户
            cursor.execute("""
                SELECT id FROM screening_strategies 
                WHERE id = %s AND creator_id = %s AND is_system = FALSE
            """, (strategy_id, user_id))
            
            if not cursor.fetchone():
                return {'success': False, 'message': '策略不存在或无权限删除'}
            
            # 删除策略
            cursor.execute("DELETE FROM screening_strategies WHERE id = %s", (strategy_id,))
            conn.commit()
            
            return {
                'success': True,
                'message': '策略删除成功'
            }
            
    except Exception as e:
        logger.error(f"删除自定义策略失败: {e}")
        return {'success': False, 'message': f'删除失败: {str(e)}'}


async def _get_user_screening_history(user_id, page, limit):
    """获取用户选股历史"""
    try:
        from app.services.strategy_database_service import strategy_db_service
        
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            offset = (page - 1) * limit
            
            sql = """
            SELECT sr.task_id, sr.screening_date, sr.total_stocks, sr.filtered_stocks,
                   sr.execution_time, sr.status, sr.created_at,
                   ss.strategy_name, ss.strategy_type
            FROM screening_results sr
            LEFT JOIN screening_strategies ss ON sr.strategy_id = ss.id
            WHERE sr.user_id = %s OR sr.user_id IS NULL
            ORDER BY sr.created_at DESC
            LIMIT %s OFFSET %s
            """
            
            cursor.execute(sql, (user_id, limit, offset))
            results = cursor.fetchall()
            
            # 获取总数
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM screening_results 
                WHERE user_id = %s OR user_id IS NULL
            """, (user_id,))
            total = cursor.fetchone()['total']
            
            history_list = []
            for result in results:
                history_list.append({
                    'task_id': result['task_id'],
                    'strategy_name': result['strategy_name'],
                    'strategy_type': result['strategy_type'],
                    'screening_date': result['screening_date'].strftime('%Y-%m-%d'),
                    'total_stocks': result['total_stocks'],
                    'filtered_stocks': result['filtered_stocks'],
                    'execution_time': result['execution_time'],
                    'status': result['status'],
                    'created_at': result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return {
                'success': True,
                'data': {
                    'list': history_list,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total,
                        'pages': (total + limit - 1) // limit
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"获取选股历史失败: {e}")
        return {'success': False, 'message': f'获取失败: {str(e)}'}


async def _get_user_preferences(user_id):
    """获取用户偏好"""
    try:
        from app.services.strategy_database_service import strategy_db_service
        import json
        
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM user_screening_preferences WHERE user_id = %s
            """, (user_id,))
            
            preferences = cursor.fetchone()
            
            if preferences:
                return {
                    'success': True,
                    'data': {
                        'preferred_strategies': json.loads(preferences['preferred_strategies']) if preferences['preferred_strategies'] else [],
                        'default_conditions': json.loads(preferences['default_conditions']) if preferences['default_conditions'] else {},
                        'notification_settings': json.loads(preferences['notification_settings']) if preferences['notification_settings'] else {},
                        'risk_level': preferences['risk_level'],
                        'max_position_size': float(preferences['max_position_size']) if preferences['max_position_size'] else 10.0,
                        'stop_loss_rate': float(preferences['stop_loss_rate']) if preferences['stop_loss_rate'] else 10.0
                    }
                }
            else:
                # 返回默认偏好
                return {
                    'success': True,
                    'data': {
                        'preferred_strategies': [],
                        'default_conditions': {},
                        'notification_settings': {},
                        'risk_level': 'moderate',
                        'max_position_size': 10.0,
                        'stop_loss_rate': 10.0
                    }
                }
                
    except Exception as e:
        logger.error(f"获取用户偏好失败: {e}")
        return {'success': False, 'message': f'获取失败: {str(e)}'}


async def _save_user_preferences(user_id, data):
    """保存用户偏好"""
    try:
        from app.services.strategy_database_service import strategy_db_service
        import json
        
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = """
            INSERT INTO user_screening_preferences (
                user_id, preferred_strategies, default_conditions, notification_settings,
                risk_level, max_position_size, stop_loss_rate
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                preferred_strategies = VALUES(preferred_strategies),
                default_conditions = VALUES(default_conditions),
                notification_settings = VALUES(notification_settings),
                risk_level = VALUES(risk_level),
                max_position_size = VALUES(max_position_size),
                stop_loss_rate = VALUES(stop_loss_rate),
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(sql, (
                user_id,
                json.dumps(data.get('preferred_strategies', []), ensure_ascii=False),
                json.dumps(data.get('default_conditions', {}), ensure_ascii=False),
                json.dumps(data.get('notification_settings', {}), ensure_ascii=False),
                data.get('risk_level', 'moderate'),
                data.get('max_position_size', 10.0),
                data.get('stop_loss_rate', 10.0)
            ))
            
            conn.commit()
            
            return {
                'success': True,
                'message': '偏好设置保存成功'
            }
            
    except Exception as e:
        logger.error(f"保存用户偏好失败: {e}")
        return {'success': False, 'message': f'保存失败: {str(e)}'}


# 将异步路由转换为同步 - 移除重复的路由定义
# 路由已经在函数定义时通过装饰器注册，不需要重复注册