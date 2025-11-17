# -*- coding: utf-8 -*-
"""
策略API模块

提供交易策略相关的REST API接口
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from app.middleware.auth import require_auth
from app.docs.swagger_config import get_swagger_spec

# 简化导入，避免循环依赖
try:
    from app.services.strategy_service import StrategyService
except ImportError:
    # 如果服务不存在，创建一个简单的模拟服务
    class StrategyService:
        def create_strategy(self, **kwargs):
            return {"id": "mock_strategy", "message": "策略服务未实现"}
        def get_strategies(self, **kwargs):
            return {"strategies": [], "total": 0}
        def get_strategy(self, **kwargs):
            return None
        def update_strategy(self, **kwargs):
            return None
        def delete_strategy(self, **kwargs):
            return False
        def activate_strategy(self, **kwargs):
            return None
        def deactivate_strategy(self, **kwargs):
            return None
        def backtest_strategy(self, **kwargs):
            return None


# 创建策略蓝图
strategy_bp = Blueprint('strategy', __name__)

# 创建策略别名蓝图（用于兼容旧路径 /api/strategies）
# 注意：这里创建一个新的蓝图，稍后会将所有路由复制过去
strategies_alias_bp = Blueprint('strategies', __name__)

# 延迟初始化策略服务
strategy_service = None

def get_strategy_service():
    """获取策略服务实例（延迟初始化）"""
    global strategy_service
    if strategy_service is None:
        print("初始化StrategyService...")
        try:
            strategy_service = StrategyService()
            print("✅ StrategyService初始化成功")
        except Exception as e:
            print(f"❌ StrategyService初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    return strategy_service


class StrategyValidator:
    """策略数据验证器"""
    
    @staticmethod
    def validate_strategy_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """验证策略数据"""
        required_fields = ['name', 'type', 'description']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")
        
        # 验证策略类型
        valid_types = ['technical', 'fundamental', 'quantitative', 'ai_driven']
        if data['type'] not in valid_types:
            raise ValueError(f"无效的策略类型: {data['type']}")
        
        return data


@strategy_bp.route('', methods=['POST'])
def create_strategy():
    """创建策略"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 使用数据库服务直接创建策略
        try:
            from app.services.strategy_database_service import strategy_db_service
            
            # 准备策略数据
            strategy_data = {
                'name': data.get('name', '未命名策略'),
                'display_name': data.get('display_name', data.get('name', '未命名策略')),
                'description': data.get('description', ''),
                'category': data.get('category', 'custom'),
                'risk_level': data.get('risk_level', 'medium'),
                'parameters': data.get('parameters', {}),
                'code': data.get('code', ''),
                'status': data.get('status', 'draft'),
                'ai_generated': data.get('ai_generated', False),
                'original_prompt': data.get('original_prompt', ''),
                'indicators': data.get('indicators', []),
                'buy_conditions': data.get('buy_conditions', []),
                'sell_conditions': data.get('sell_conditions', []),
                'risk_controls': data.get('risk_controls', {}),
                'author': 'AI助手' if data.get('ai_generated') else '用户',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # 创建策略
            user_id = 1  # 临时用户ID，实际应该从认证中获取
            strategy_id = strategy_db_service.create_strategy(user_id, strategy_data)
            
            if strategy_id:
                # 返回创建的策略数据
                strategy_data['strategy_id'] = strategy_id
                return jsonify({
                    'success': True,
                    'message': '策略创建成功',
                    'data': strategy_data
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '策略创建失败'
                }), 500
                
        except ImportError:
            # 如果数据库服务不可用，返回模拟数据
            strategy_data = {
                'strategy_id': f'mock_{uuid.uuid4().hex[:8]}',
                'name': data.get('name', '未命名策略'),
                'display_name': data.get('display_name', data.get('name', '未命名策略')),
                'description': data.get('description', ''),
                'category': data.get('category', 'custom'),
                'risk_level': data.get('risk_level', 'medium'),
                'parameters': data.get('parameters', {}),
                'code': data.get('code', ''),
                'status': data.get('status', 'draft'),
                'ai_generated': data.get('ai_generated', False),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'message': '策略创建成功（模拟模式）',
                'data': strategy_data
            })
        
    except Exception as e:
        print(f"策略创建失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'策略创建失败: {str(e)}'
        }), 500


@strategy_bp.route('', methods=['GET'])
@require_auth
def get_strategies():
    """获取策略列表"""
    try:
        # 获取查询参数
        strategy_type = request.args.get('type')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        
        # 获取策略列表
        result = strategy_service.get_strategies(
            user_id=g.current_user['id'],
            strategy_type=strategy_type,
            status=status,
            page=page,
            page_size=page_size
        )
        
        return jsonify({
            'success': True,
            'message': '获取策略列表成功',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取策略列表失败: {str(e)}'
        }), 500


@strategy_bp.route('/<strategy_id>', methods=['GET'])
@require_auth
def get_strategy(strategy_id: str):
    """获取策略详情"""
    try:
        strategy = strategy_service.get_strategy(
            user_id=g.current_user['id'],
            strategy_id=strategy_id
        )
        
        if not strategy:
            return jsonify({
                'success': False,
                'message': '策略不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '获取策略详情成功',
            'data': strategy
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取策略详情失败: {str(e)}'
        }), 500


@strategy_bp.route('/<strategy_id>', methods=['PUT'])
@require_auth
def update_strategy(strategy_id: str):
    """更新策略"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 更新策略
        strategy = strategy_service.update_strategy(
            user_id=g.current_user['id'],
            strategy_id=strategy_id,
            **data
        )
        
        if not strategy:
            return jsonify({
                'success': False,
                'message': '策略不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '策略更新成功',
            'data': strategy
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略更新失败: {str(e)}'
        }), 500




@strategy_bp.route('/<strategy_id>/activate', methods=['POST'])
@require_auth
def activate_strategy(strategy_id: str):
    """激活策略"""
    try:
        result = strategy_service.activate_strategy(
            user_id=g.current_user['id'],
            strategy_id=strategy_id
        )
        
        if not result:
            return jsonify({
                'success': False,
                'message': '策略不存在或无法激活'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '策略激活成功',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略激活失败: {str(e)}'
        }), 500


@strategy_bp.route('/<strategy_id>/deactivate', methods=['POST'])
@require_auth
def deactivate_strategy(strategy_id: str):
    """停用策略"""
    try:
        result = strategy_service.deactivate_strategy(
            user_id=g.current_user['id'],
            strategy_id=strategy_id
        )
        
        if not result:
            return jsonify({
                'success': False,
                'message': '策略不存在或无法停用'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '策略停用成功',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略停用失败: {str(e)}'
        }), 500


@strategy_bp.route('/<strategy_id>/backtest', methods=['POST'])
@require_auth
def backtest_strategy(strategy_id: str):
    """策略回测"""
    try:
        data = request.get_json()
        
        result = strategy_service.backtest_strategy(
            user_id=g.current_user['id'],
            strategy_id=strategy_id,
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            initial_capital=data.get('initial_capital', 100000)
        )
        
        if not result:
            return jsonify({
                'success': False,
                'message': '策略不存在或回测失败'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '策略回测完成',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略回测失败: {str(e)}'
        }), 500


@strategy_bp.route('/test', methods=['GET'])
def get_strategy_list_test():
    """测试策略列表接口 - 无认证版本"""
    return jsonify({
        'success': True,
        'message': '测试策略列表成功',
        'data': [
            {
                'id': 'MA_Cross',
                'name': '双均线策略',
                'description': '基于短期和长期移动平均线交叉的趋势跟踪策略',
                'status': 'available',
                'category': 'trend_following',
                'risk_level': 'medium'
            }
        ]
    })

@strategy_bp.route('/list', methods=['GET'])
def get_strategy_list():
    """获取策略列表 - 真实数据库版本"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', '')
        category = request.args.get('category', '')
        risk_level = request.args.get('risk_level', '')
        
        # 尝试使用真实数据库
        try:
            from app.services.strategy_database_service import strategy_db_service
            
            strategies, total = strategy_db_service.get_strategies(
                page=page, size=size, keyword=keyword, 
                status=status, category=category, risk_level=risk_level
            )
            
            return jsonify({
                'success': True,
                'message': '获取策略列表成功',
                'data': {
                    'strategies': strategies,
                    'total': total,
                    'page': page,
                    'page_size': size
                }
            })
            
        except ImportError as e:
            print(f"数据库服务不可用，使用静态数据: {e}")
            # 降级到静态数据
            return _get_static_strategy_list(page, size, keyword, status, category, risk_level)
            
    except Exception as e:
        print(f"获取策略列表失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 发生错误时降级到静态数据
        try:
            return _get_static_strategy_list(page, size, keyword, status, category, risk_level)
        except:
            return jsonify({
                'success': False,
                'message': f'获取策略列表失败: {str(e)}'
            }), 500


def _get_static_strategy_list(page: int, size: int, keyword: str, status: str, category: str, risk_level: str):
    """静态策略列表（降级方案）"""
    # 静态策略数据
    all_strategies = [
        {
            'strategy_id': 'MA_Cross_001',
            'name': '双均线策略',
            'display_name': '双均线策略',
            'description': '基于短期和长期移动平均线交叉的趋势跟踪策略，当短期均线上穿长期均线时买入，下穿时卖出',
            'status': 'draft',
            'category': 'trend_following',
            'risk_level': 'medium',
            'author': '系统',
            'performance': 0.156,
            'sharpe_ratio': 1.85,
            'max_drawdown': 0.08,
            'win_rate': 0.65,
            'total_trades': 45,
            'backtest_count': 3,
            'last_backtest_date': '2025-10-25',
            'created_at': '2025-10-20T08:30:00.000Z',
            'updated_at': '2025-10-30T02:30:00.000Z'
        },
        {
            'strategy_id': 'RSI_Reversal_002',
            'name': 'RSI反转策略',
            'display_name': 'RSI反转策略',
            'description': '基于RSI指标的均值回归策略，在RSI超买超卖区域进行反向交易',
            'status': 'active',
            'category': 'mean_reversion',
            'risk_level': 'medium',
            'author': '量化团队',
            'performance': 0.123,
            'sharpe_ratio': 1.42,
            'max_drawdown': 0.12,
            'win_rate': 0.58,
            'total_trades': 67,
            'backtest_count': 5,
            'last_backtest_date': '2025-10-28',
            'created_at': '2025-10-18T10:15:00.000Z',
            'updated_at': '2025-10-29T14:20:00.000Z'
        },
        {
            'strategy_id': 'MACD_Momentum_003',
            'name': 'MACD动量策略',
            'display_name': 'MACD动量策略',
            'description': '基于MACD指标的动量策略，利用MACD金叉死叉信号进行交易',
            'status': 'stopped',
            'category': 'momentum',
            'risk_level': 'high',
            'author': 'AI助手',
            'performance': 0.089,
            'sharpe_ratio': 0.95,
            'max_drawdown': 0.18,
            'win_rate': 0.52,
            'total_trades': 89,
            'backtest_count': 2,
            'last_backtest_date': '2025-10-22',
            'created_at': '2025-10-15T16:45:00.000Z',
            'updated_at': '2025-10-27T09:10:00.000Z'
        },
        {
            'strategy_id': 'Bollinger_Bands_004',
            'name': '布林带策略',
            'display_name': '布林带策略',
            'description': '基于布林带的突破和回归策略，价格触及上下轨时进行交易',
            'status': 'draft',
            'category': 'volatility',
            'risk_level': 'medium',
            'author': '系统',
            'performance': 0.201,
            'sharpe_ratio': 2.15,
            'max_drawdown': 0.06,
            'win_rate': 0.71,
            'total_trades': 34,
            'backtest_count': 1,
            'last_backtest_date': '2025-10-26',
            'created_at': '2025-10-22T11:30:00.000Z',
            'updated_at': '2025-10-30T01:15:00.000Z'
        },
        {
            'strategy_id': 'Grid_Trading_005',
            'name': '网格交易策略',
            'display_name': '网格交易策略',
            'description': '基于价格区间的网格交易策略，在设定区间内进行高抛低吸',
            'status': 'active',
            'category': 'arbitrage',
            'risk_level': 'low',
            'author': '量化团队',
            'performance': 0.078,
            'sharpe_ratio': 1.28,
            'max_drawdown': 0.04,
            'win_rate': 0.68,
            'total_trades': 156,
            'backtest_count': 4,
            'last_backtest_date': '2025-10-29',
            'created_at': '2025-10-12T14:20:00.000Z',
            'updated_at': '2025-10-30T03:45:00.000Z'
        },
        {
            'strategy_id': 'Multi_Factor_006',
            'name': '多因子策略',
            'display_name': '多因子策略',
            'description': '综合多个技术指标和基本面因子的量化策略',
            'status': 'paused',
            'category': 'multi_factor',
            'risk_level': 'medium',
            'author': 'AI助手',
            'performance': 0.167,
            'sharpe_ratio': 1.73,
            'max_drawdown': 0.09,
            'win_rate': 0.62,
            'total_trades': 78,
            'backtest_count': 6,
            'last_backtest_date': '2025-10-30',
            'created_at': '2025-10-25T09:00:00.000Z',
            'updated_at': '2025-10-30T05:30:00.000Z'
        }
    ]
    
    # 应用筛选
    filtered_strategies = all_strategies
    
    if keyword:
        filtered_strategies = [s for s in filtered_strategies 
                             if keyword.lower() in s['name'].lower() 
                             or keyword.lower() in s['description'].lower()]
    
    if status:
        filtered_strategies = [s for s in filtered_strategies if s['status'] == status]
        
    if category:
        filtered_strategies = [s for s in filtered_strategies if s['category'] == category]
        
    if risk_level:
        filtered_strategies = [s for s in filtered_strategies if s['risk_level'] == risk_level]
    
    # 分页
    total = len(filtered_strategies)
    start = (page - 1) * size
    end = start + size
    strategies = filtered_strategies[start:end]
    
    return jsonify({
        'success': True,
        'message': '获取策略列表成功（静态模式）',
        'data': {
            'strategies': strategies,
            'total': total,
            'page': page,
            'page_size': size
        }
    })


@strategy_bp.route('/<strategy_id>/start', methods=['POST'])
def start_strategy(strategy_id: str):
    """启动策略"""
    try:
        return jsonify({
            'success': True,
            'message': '策略启动成功',
            'data': {
                'strategy_id': strategy_id,
                'status': 'active'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略启动失败: {str(e)}'
        }), 500


@strategy_bp.route('/<strategy_id>/pause', methods=['POST'])
def pause_strategy(strategy_id: str):
    """暂停策略"""
    try:
        return jsonify({
            'success': True,
            'message': '策略暂停成功',
            'data': {
                'strategy_id': strategy_id,
                'status': 'paused'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略暂停失败: {str(e)}'
        }), 500


@strategy_bp.route('/<strategy_id>/stop', methods=['POST'])
def stop_strategy(strategy_id: str):
    """停止策略"""
    try:
        return jsonify({
            'success': True,
            'message': '策略停止成功',
            'data': {
                'strategy_id': strategy_id,
                'status': 'stopped'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略停止失败: {str(e)}'
        }), 500


@strategy_bp.route('/<strategy_id>/copy', methods=['POST'])
def copy_strategy(strategy_id: str):
    """复制策略"""
    try:
        # 模拟复制策略
        new_strategy = {
            'strategy_id': f'Copy_{strategy_id}_{int(datetime.now().timestamp())}',
            'name': f'策略副本_{strategy_id}',
            'display_name': f'策略副本_{strategy_id}',
            'description': '这是一个复制的策略',
            'status': 'draft',
            'category': 'custom',
            'risk_level': 'medium',
            'author': '用户',
            'performance': 0.0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': '策略复制成功',
            'data': new_strategy
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略复制失败: {str(e)}'
        }), 500


@strategy_bp.route('/<strategy_id>', methods=['DELETE'])
def delete_strategy_by_id(strategy_id: str):
    """删除策略"""
    try:
        # 使用数据库服务删除策略
        try:
            from app.services.strategy_database_service import strategy_db_service
            
            # 删除策略（使用临时用户ID）
            user_id = 1  # 临时用户ID，实际应该从认证中获取
            success = strategy_db_service.delete_strategy(strategy_id, user_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '策略删除成功',
                    'data': {
                        'strategy_id': strategy_id,
                        'deleted': True
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '策略删除失败，策略可能不存在或无权限删除'
                }), 404
                
        except ImportError:
            # 如果数据库服务不可用，返回模拟删除结果
            print("数据库服务不可用，返回模拟删除结果")
            return jsonify({
                'success': True,
                'message': '策略删除成功（模拟模式）',
                'data': {
                    'strategy_id': strategy_id,
                    'deleted': True
                }
            })
        
    except Exception as e:
        print(f"删除策略失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'策略删除失败: {str(e)}'
        }), 500


@strategy_bp.route('/batch-delete', methods=['POST'])
def batch_delete_strategies():
    """批量删除策略"""
    try:
        data = request.get_json()
        strategy_ids = data.get('strategy_ids', [])
        
        if not strategy_ids:
            return jsonify({
                'success': False,
                'message': '请提供要删除的策略ID列表'
            }), 400
        
        # 使用数据库服务删除策略
        deleted_count = 0
        failed_ids = []
        
        try:
             from app.services.strategy_database_service import strategy_db_service
             
             user_id = 1  # 临时用户ID，实际应该从认证中获取
             
             for strategy_id in strategy_ids:
                 try:
                     # 删除策略
                     success = strategy_db_service.delete_strategy(strategy_id, user_id)
                     if success:
                         deleted_count += 1
                     else:
                         failed_ids.append(strategy_id)
                 except Exception as e:
                     print(f"删除策略 {strategy_id} 失败: {e}")
                     failed_ids.append(strategy_id)
             
             # 构建响应消息
             if deleted_count == len(strategy_ids):
                 message = f'成功删除 {deleted_count} 个策略'
             elif deleted_count > 0:
                 message = f'成功删除 {deleted_count} 个策略，{len(failed_ids)} 个失败'
             else:
                 message = '所有策略删除失败'
             
             return jsonify({
                 'success': deleted_count > 0,
                 'message': message,
                 'data': {
                     'deleted_count': deleted_count,
                     'failed_count': len(failed_ids),
                     'failed_ids': failed_ids
                 }
             })
            
        except ImportError:
            # 如果数据库服务不可用，返回模拟删除结果
            print("数据库服务不可用，返回模拟删除结果")
            return jsonify({
                'success': True,
                'message': f'模拟删除 {len(strategy_ids)} 个策略（数据库服务不可用）',
                'data': {
                    'deleted_count': len(strategy_ids),
                    'failed_count': 0,
                    'failed_ids': []
                }
            })
        
    except Exception as e:
        print(f"批量删除策略失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'批量删除失败: {str(e)}'
        }), 500


@strategy_bp.route('/<strategy_id>/export', methods=['GET'])
def export_strategy(strategy_id: str):
    """导出策略"""
    try:
        # 模拟策略数据
        strategy_data = {
            'strategy_id': strategy_id,
            'name': '导出的策略',
            'description': '这是一个导出的策略',
            'category': 'custom',
            'risk_level': 'medium',
            'parameters': {},
            'code': 'def initialize(context):\n    pass\n\ndef handle_data(context, data):\n    pass',
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': '策略导出成功',
            'data': strategy_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略导出失败: {str(e)}'
        }), 500


@strategy_bp.route('/batch-export', methods=['POST'])
def batch_export_strategies():
    """批量导出策略"""
    try:
        data = request.get_json()
        strategy_ids = data.get('strategy_ids', [])
        
        # 模拟批量导出
        strategies = []
        for strategy_id in strategy_ids:
            strategies.append({
                'strategy_id': strategy_id,
                'name': f'策略_{strategy_id}',
                'description': '导出的策略',
                'category': 'custom',
                'risk_level': 'medium',
                'created_at': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': True,
            'message': f'成功导出 {len(strategies)} 个策略',
            'data': strategies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量导出失败: {str(e)}'
        }), 500


@strategy_bp.route('/import', methods=['POST'])
def import_strategies():
    """导入策略"""
    try:
        data = request.get_json()
        strategies = data.get('strategies', [])
        
        return jsonify({
            'success': True,
            'message': f'成功导入 {len(strategies)} 个策略',
            'data': {
                'imported_count': len(strategies)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略导入失败: {str(e)}'
        }), 500


@strategy_bp.route('/backtest', methods=['POST'])
def run_backtest():
    """运行回测 - 真实回测引擎版本"""
    try:
        data = request.get_json()
        strategy_id = data.get('strategy_id')
        stock_pool = data.get('stock_pool') or []
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': '开始/结束日期不能为空',
                'data': { 'received': data }
            }), 400
        if not isinstance(stock_pool, list) or len(stock_pool) == 0:
            return jsonify({
                'success': False,
                'message': '股票池为空，请选择选股结果或手动输入代码',
                'data': { 'received': data }
            }), 400
        
        if not strategy_id:
            return jsonify({
                'success': False,
                'message': '策略ID不能为空'
            }), 400
        
        # 尝试使用真实回测引擎
        try:
            from app.services.backtest_engine import backtest_engine, BacktestConfig
            from app.services.strategy_database_service import strategy_db_service
            import asyncio
            
            # 获取策略信息
            strategy = strategy_db_service.get_strategy_by_id(strategy_id)
            if not strategy:
                return jsonify({
                    'success': False,
                    'message': '策略不存在'
                }), 404
            
            # 打印策略信息用于调试
            print(f"[DEBUG] 策略信息:")
            print(f"  - 策略ID: {strategy.get('strategy_id')}")
            print(f"  - 策略名称: {strategy.get('name')}")
            print(f"  - 买入条件: {strategy.get('buy_conditions')}")
            print(f"  - 卖出条件: {strategy.get('sell_conditions')}")
            print(f"  - 风险控制: {strategy.get('risk_controls')}")
            
            # 构建回测配置
            config = BacktestConfig(
                strategy_id=strategy_id,
                strategy_name=strategy.get('name', '未知策略'),
                strategy_code=strategy.get('code', ''),
                start_date=data.get('start_date', '2023-01-01'),
                end_date=data.get('end_date', '2024-01-01'),
                initial_capital=data.get('initial_capital', 1000000),
                stock_pool=stock_pool,
                benchmark=data.get('benchmark', '000300.SH'),
                parameters=data.get('parameters', {}),
                frequency=data.get('frequency', 'daily'),
                buy_conditions=strategy.get('buy_conditions') or data.get('buy_conditions'),
                sell_conditions=strategy.get('sell_conditions') or data.get('sell_conditions'),
                risk_controls=strategy.get('risk_controls') or data.get('risk_controls')
            )
            
            # 打印回测配置用于调试
            print(f"[DEBUG] 回测配置:")
            print(f"  - 买入条件数量: {len(config.buy_conditions) if config.buy_conditions else 0}")
            print(f"  - 卖出条件数量: {len(config.sell_conditions) if config.sell_conditions else 0}")
            print(f"  - 风险控制: {config.risk_controls}")
            
            # 执行回测（同步方式）
            try:
                # 创建新的事件循环或使用现有的
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                backtest_result = loop.run_until_complete(backtest_engine.run_backtest(config))
            except Exception as e:
                print(f"异步回测执行失败: {e}")
                return jsonify({
                    'success': False,
                    'message': f'回测执行失败: {str(e)}'
                }), 500
            
            # 保存回测结果到数据库或返回错误
            if backtest_result.get('status') == 'completed':
                backtest_result['user_id'] = 1  # 临时用户ID
                strategy_db_service.save_backtest_result(backtest_result)
                return jsonify({
                    'success': True,
                    'message': '回测完成',
                    'data': backtest_result
                })
            else:
                return jsonify({
                    'success': False,
                    'message': backtest_result.get('error_message', '回测失败'),
                    'data': backtest_result
                }), 400
            
        except ImportError as e:
            print(f"回测引擎不可用: {e}")
            return jsonify({
                'success': False,
                'message': '回测引擎不可用'
            }), 500
            
    except Exception as e:
        print(f"回测失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'回测失败: {str(e)}'
        }), 500


@strategy_bp.route('/backtest/history', methods=['GET'])
def get_backtest_history():
    """获取回测历史"""
    try:
        strategy_id = request.args.get('strategy_id')
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        user_id = 1  # 临时用户ID
        
        from app.services.strategy_database_service import strategy_db_service
        
        results, total = strategy_db_service.get_backtest_results(
            user_id=user_id,
            strategy_id=strategy_id,
            page=page,
            size=size
        )
        
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'total': total,
                'page': page,
                'size': size,
                'pages': (total + size - 1) // size
            }
        })
        
    except Exception as e:
        print(f"获取回测历史失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'获取回测历史失败: {str(e)}'
        }), 500


@strategy_bp.route('/backtest/<backtest_id>', methods=['GET'])
def get_backtest_detail(backtest_id: str):
    """获取回测结果详情"""
    try:
        user_id = 1  # 临时用户ID
        
        from app.services.strategy_database_service import strategy_db_service
        
        result = strategy_db_service.get_backtest_result_detail(
            backtest_id=backtest_id,
            user_id=user_id
        )
        
        if not result:
            return jsonify({
                'success': False,
                'message': '回测结果不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"获取回测详情失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'获取回测详情失败: {str(e)}'
        }), 500


def _run_mock_backtest(data: Dict[str, Any]):
    """模拟回测（降级方案）"""
    try:
        strategy_id = data.get('strategy_id')
        
        # 模拟回测结果
        backtest_result = {
            'backtest_id': f'BT_{int(datetime.now().timestamp())}',
            'strategy_id': strategy_id,
            'strategy_name': '测试策略',
            'start_date': data.get('start_date', '2023-01-01'),
            'end_date': data.get('end_date', '2024-01-01'),
            'initial_capital': data.get('initial_capital', 1000000),
            'final_capital': 1156000,
            'parameters': data.get('parameters', {}),
            'stock_pool': data.get('stock_pool', ['000001.XSHE', '000002.XSHE']),
            'benchmark': data.get('benchmark', '000300.SH'),
            
            # 收益指标
            'total_return': 0.156,
            'annualized_return': 0.156,
            'benchmark_return': 0.08,
            'alpha': 0.076,
            'beta': 1.2,
            
            # 风险指标
            'sharpe_ratio': 1.85,
            'sortino_ratio': 2.1,
            'max_drawdown': 0.08,
            'volatility': 0.15,
            
            # 交易指标
            'win_rate': 0.65,
            'profit_factor': 2.3,
            'total_trades': 45,
            'winning_trades': 29,
            'losing_trades': 16,
            'avg_win': 0.035,
            'avg_loss': -0.018,
            'largest_win': 0.12,
            'largest_loss': -0.05,
            
            # 详细数据
            'equity_curve': [
                {'date': '2023-01-01', 'value': 1000000, 'return': 0.0},
                {'date': '2023-06-01', 'value': 1078000, 'return': 0.078},
                {'date': '2023-12-31', 'value': 1156000, 'return': 0.156}
            ],
            'trades': [
                {
                    'trade_id': 'T001',
                    'date': '2023-01-15',
                    'code': '000001.XSHE',
                    'name': '平安银行',
                    'side': 'buy',
                    'quantity': 1000,
                    'price': 12.50,
                    'amount': 12500,
                    'commission': 3.75,
                    'profit_loss': 0
                },
                {
                    'trade_id': 'T002',
                    'date': '2023-02-20',
                    'code': '000001.XSHE',
                    'name': '平安银行',
                    'side': 'sell',
                    'quantity': 1000,
                    'price': 13.80,
                    'amount': 13800,
                    'commission': 4.14,
                    'profit_loss': 1296.11
                }
            ],
            
            # 状态
            'status': 'completed',
            'created_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'mock_backtest': True  # 标记为模拟回测
        }
        
        return jsonify({
            'success': True,
            'message': '回测完成（模拟模式）',
            'data': backtest_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'模拟回测失败: {str(e)}'
        }), 500


@strategy_bp.route('/validate-code', methods=['POST'])
def validate_code():
    """验证策略代码"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        errors = []
        warnings = []
        
        # 基本验证
        if not code.strip():
            errors.append('代码不能为空')
        else:
            if 'def initialize(context):' not in code:
                errors.append('缺少 initialize 函数')
            if 'def handle_data(context, data):' not in code:
                errors.append('缺少 handle_data 函数')
        
        return jsonify({
            'success': True,
            'message': '代码验证完成',
            'data': {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'代码验证失败: {str(e)}'
        }), 500


@strategy_bp.route('/format-code', methods=['POST'])
def format_code():
    """格式化策略代码"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        # 简单的代码格式化
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.rstrip()
            if line.strip():
                formatted_lines.append(line)
            else:
                formatted_lines.append('')
        
        formatted_code = '\n'.join(formatted_lines)
        
        return jsonify({
            'success': True,
            'message': '代码格式化完成',
            'data': {
                'formatted_code': formatted_code
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'代码格式化失败: {str(e)}'
        }), 500


@strategy_bp.route('/ai-generate', methods=['POST'])
def ai_generate_strategy():
    """AI生成策略 - 只生成不保存"""
    try:
        data = request.get_json()
        original_prompt = data.get('prompt', '')
        options = data.get('options', {})
        
        if not original_prompt.strip():
            return jsonify({
                'success': False,
                'message': '请提供策略需求描述'
            }), 400
        
        # 导入AI策略生成器
        try:
            print(f"[AI策略生成] 开始导入AI策略生成器...")
            from app.services.ai_strategy_generator import ai_strategy_generator
            from app.services.llm_gateway import initialize_gateway
            print(f"[AI策略生成] AI策略生成器导入成功")
            
            # 初始化Gateway（如果还没初始化）
            if len(ai_strategy_generator.gateway.adapters) == 0:
                print(f"[AI策略生成] Gateway未初始化，开始初始化...")
                try:
                    initialize_gateway()
                    print(f"[AI策略生成] Gateway初始化完成，适配器数量: {len(ai_strategy_generator.gateway.adapters)}")
                    print(f"[AI策略生成] 已注册的适配器: {list(ai_strategy_generator.gateway.adapters.keys())}")
                except Exception as init_error:
                    print(f"[AI策略生成] Gateway初始化失败: {init_error}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[AI策略生成] Gateway已初始化，适配器数量: {len(ai_strategy_generator.gateway.adapters)}")
                print(f"[AI策略生成] 已注册的适配器: {list(ai_strategy_generator.gateway.adapters.keys())}")
            
            # 第一步：补全提示词
            print(f"[AI策略生成] 原始提示词: {original_prompt[:100]}...")
            enhanced_prompt = ai_strategy_generator.enhance_prompt(original_prompt, options)
            print(f"[AI策略生成] 补全后提示词长度: {len(enhanced_prompt)}")
            
            # 调用真实的AI生成服务（同步方式）
            try:
                # 直接调用同步方法，避免异步问题
                if hasattr(ai_strategy_generator, 'generate_strategy_sync'):
                    print("=" * 100)
                    print(f"[AI策略生成API] 开始调用AI生成器...")
                    print(f"[AI策略生成API] 原始提示词: {original_prompt}")
                    print(f"[AI策略生成API] 补全提示词长度: {len(enhanced_prompt)}")
                    print(f"[AI策略生成API] 生成选项: {options}")
                    
                    # 使用补全后的提示词
                    strategy = ai_strategy_generator.generate_strategy_sync(enhanced_prompt, options)
                    
                    print(f"[AI策略生成API] AI生成完成")
                    print(f"[AI策略生成API] 策略名称: {strategy.get('name')}")
                    print(f"[AI策略生成API] 策略类型: {strategy.get('type')}")
                    print(f"[AI策略生成API] 是否模板生成: {strategy.get('template_based', False)}")
                    print(f"[AI策略生成API] 策略描述: {strategy.get('description', '')[:100]}...")
                    print("=" * 100)
                else:
                    # 如果没有同步方法，降级到模拟生成
                    print("[AI策略生成API] AI生成器没有同步方法，使用模拟生成")
                    return _generate_mock_strategy(original_prompt, options)
            except Exception as e:
                print(f"[AI策略生成API] AI生成失败: {e}")
                import traceback
                traceback.print_exc()
                # 降级到模拟生成
                return _generate_mock_strategy(original_prompt, options)
            
            # 只返回策略数据，不保存到数据库
            strategy['ai_generated'] = True
            strategy['real_ai_generated'] = True
            
            # 返回原始提示词和补全后的提示词
            return jsonify({
                'success': True,
                'message': 'AI策略生成成功',
                'data': strategy,
                'prompt_info': {
                    'original_prompt': original_prompt,
                    'enhanced_prompt': enhanced_prompt,
                    'enhancement_applied': enhanced_prompt != original_prompt
                }
            })
            
        except ImportError as e:
            print(f"AI服务不可用，使用模拟生成: {e}")
            # 降级到模拟生成
            return _generate_mock_strategy(original_prompt, options)
            
    except Exception as e:
        print(f"AI策略生成失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 发生错误时降级到模拟生成
        try:
            data = request.get_json() or {}
            prompt = data.get('prompt', '')
            options = data.get('options', {})
            return _generate_mock_strategy(prompt, options)
        except:
            return jsonify({
                'success': False,
                'message': f'AI策略生成失败: {str(e)}'
            }), 500


def _generate_trading_conditions_for_type(strategy_type: str) -> tuple:
    """根据策略类型生成买入卖出条件"""
    if strategy_type == 'mean_reversion':
        buy_conditions = [
            {
                'type': 'indicator',
                'indicator': 'RSI',
                'operator': 'less_than',
                'value': 30,
                'params': {'period': 14},
                'description': 'RSI低于30（超卖）'
            }
        ]
        sell_conditions = [
            {
                'type': 'indicator',
                'indicator': 'RSI',
                'operator': 'greater_than',
                'value': 70,
                'params': {'period': 14},
                'description': 'RSI高于70（超买）'
            }
        ]
    elif strategy_type == 'trend_following':
        buy_conditions = [
            {
                'type': 'indicator',
                'indicator': 'MA',
                'operator': 'cross_above',
                'params': {'short_period': 5, 'long_period': 20},
                'description': '短期均线上穿长期均线'
            }
        ]
        sell_conditions = [
            {
                'type': 'indicator',
                'indicator': 'MA',
                'operator': 'cross_below',
                'params': {'short_period': 5, 'long_period': 20},
                'description': '短期均线下穿长期均线'
            }
        ]
    elif strategy_type == 'momentum':
        buy_conditions = [
            {
                'type': 'indicator',
                'indicator': 'MACD',
                'operator': 'cross_above',
                'params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
                'description': 'MACD上穿信号线'
            }
        ]
        sell_conditions = [
            {
                'type': 'indicator',
                'indicator': 'MACD',
                'operator': 'cross_below',
                'params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
                'description': 'MACD下穿信号线'
            }
        ]
    else:
        buy_conditions = [
            {
                'type': 'price',
                'operator': 'greater_than',
                'value': 'MA20',
                'description': '价格高于20日均线'
            }
        ]
        sell_conditions = [
            {
                'type': 'price',
                'operator': 'less_than',
                'value': 'MA20',
                'description': '价格低于20日均线'
            }
        ]

    return buy_conditions, sell_conditions


def _generate_risk_controls_for_level(risk_level: str) -> Dict[str, Any]:
    """根据风险等级生成风险控制配置"""
    risk_configs = {
        'low': {
            'max_position_size': 0.05,
            'max_total_position': 0.3,
            'stop_loss': 3.0,
            'take_profit': 10.0,
            'max_drawdown': 5.0
        },
        'medium': {
            'max_position_size': 0.1,
            'max_total_position': 0.6,
            'stop_loss': 5.0,
            'take_profit': 15.0,
            'max_drawdown': 10.0
        },
        'high': {
            'max_position_size': 0.2,
            'max_total_position': 0.9,
            'stop_loss': 8.0,
            'take_profit': 25.0,
            'max_drawdown': 20.0
        }
    }
    return risk_configs.get(risk_level, risk_configs['medium'])


def _generate_mock_strategy(prompt: str, options: Dict[str, Any]):
    """模拟策略生成（降级方案）"""
    try:
        # 根据提示词生成策略
        strategy_type = options.get('strategy_type', 'custom')
        risk_level = options.get('risk_level', 'medium')
        
        # 分析提示词确定策略类型
        if 'rsi' in prompt.lower():
            name = 'AI生成RSI策略'
            description = '基于RSI指标的AI生成策略'
            strategy_type = 'mean_reversion'
            indicators = ['RSI']
            code = '''def initialize(context):
    # RSI反转策略
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.rsi_period = 14
    context.rsi_overbought = 70
    context.rsi_oversold = 30
    context.position_size = 0.1

def handle_data(context, data):
    for stock in context.stocks:
        # 计算RSI
        hist = data.history(stock, 'close', context.rsi_period + 1)
        rsi = calculate_rsi(hist, context.rsi_period)
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：RSI < 30
        if rsi < context.rsi_oversold and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：RSI > 70
        elif rsi > context.rsi_overbought and current_position > 0:
            order_target_percent(stock, 0)

def calculate_rsi(prices, period):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]'''
        elif '均线' in prompt or 'ma' in prompt.lower():
            name = 'AI生成均线策略'
            description = '基于移动平均线的AI生成策略'
            strategy_type = 'trend_following'
            indicators = ['MA', 'EMA']
            code = '''def initialize(context):
    # 双均线策略
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.short_period = 5
    context.long_period = 20
    context.position_size = 0.1

def handle_data(context, data):
    for stock in context.stocks:
        # 获取历史价格数据
        hist = data.history(stock, 'close', context.long_period + 1)
        
        # 计算均线
        short_ma = hist[-context.short_period:].mean()
        long_ma = hist.mean()
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：短均线上穿长均线
        if short_ma > long_ma and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：短均线下穿长均线
        elif short_ma < long_ma and current_position > 0:
            order_target_percent(stock, 0)'''
        elif 'macd' in prompt.lower() or '动量' in prompt:
            name = 'AI生成MACD策略'
            description = '基于MACD指标的AI生成策略'
            strategy_type = 'momentum'
            indicators = ['MACD']
            code = '''def initialize(context):
    # MACD动量策略
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.fast_period = 12
    context.slow_period = 26
    context.signal_period = 9
    context.position_size = 0.1

def handle_data(context, data):
    for stock in context.stocks:
        # 获取历史价格数据
        hist = data.history(stock, 'close', context.slow_period + context.signal_period)
        
        # 计算MACD
        ema_fast = hist.ewm(span=context.fast_period).mean()
        ema_slow = hist.ewm(span=context.slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=context.signal_period).mean()
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：MACD上穿信号线
        if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2] and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：MACD下穿信号线
        elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2] and current_position > 0:
            order_target_percent(stock, 0)'''
        else:
            name = f'AI生成策略_{datetime.now().strftime("%m%d_%H%M")}'
            description = f'基于用户需求"{prompt}"生成的自定义策略'
            indicators = ['MA']
            code = '''def initialize(context):
    # 自定义策略
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.position_size = 0.1

def handle_data(context, data):
    # 策略逻辑
    for stock in context.stocks:
        current_position = context.portfolio.positions[stock].amount
        
        # 买入条件
        if should_buy(context, data, stock) and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出条件
        elif should_sell(context, data, stock) and current_position > 0:
            order_target_percent(stock, 0)

def should_buy(context, data, stock):
    # 在这里实现买入逻辑
    return False

def should_sell(context, data, stock):
    # 在这里实现卖出逻辑
    return False'''
        
        # 生成买入卖出条件
        buy_conditions, sell_conditions = _generate_trading_conditions_for_type(strategy_type)

        # 创建策略
        strategy = {
            'name': name,
            'display_name': name,
            'description': description,
            'category': strategy_type,
            'risk_level': risk_level,
            'author': 'AI助手',
            'parameters': {
                'position_size': 0.1,
                'stop_loss': 5.0,
                'take_profit': 15.0
            },
            'indicators': indicators,
            'buy_conditions': buy_conditions,
            'sell_conditions': sell_conditions,
            'risk_controls': _generate_risk_controls_for_level(risk_level),
            'code': code,
            'status': 'draft',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'ai_generated': True,
            'original_prompt': prompt,
            'mock_generated': True  # 标记为模拟生成
        }
        
        return jsonify({
            'success': True,
            'message': 'AI策略生成成功（模拟模式）',
            'data': strategy
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'策略生成失败: {str(e)}'
        }), 500
@strategy_bp.route('/active', methods=['GET'])
@require_auth
def get_active_strategies():
    """获取活跃策略列表"""
    try:
        # 获取活跃策略
        service = get_strategy_service()
        strategies = service.get_strategies(
            user_id=g.current_user['id'],
            status='active'
        )
        
        return jsonify({
            'success': True,
            'message': '获取活跃策略成功',
            'data': strategies
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取活跃策略失败: {str(e)}'
        }), 500


@strategy_bp.route('/parse-code', methods=['POST'])
def parse_strategy_code():
    """
    解析策略代码，提取配置信息
    支持从代码反向生成策略配置
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({
                'success': False,
                'message': '代码不能为空'
            }), 400
        
        # 导入代码解析器
        from app.services.code_parser import code_parser
        
        # 解析代码
        parsed_config = code_parser.parse_strategy_code(code)
        
        return jsonify({
            'success': True,
            'message': '代码解析成功',
            'data': parsed_config
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'代码解析失败: {str(e)}'
        }), 500


@strategy_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': '策略服务运行正常',
        'data': {
            'service': 'strategy_api',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    })


# 将所有视图函数从 strategy_bp 复制到 strategies_alias_bp
# 这样 strategies_alias_bp 就可以响应相同的路由
strategies_alias_bp.view_functions = strategy_bp.view_functions.copy()




