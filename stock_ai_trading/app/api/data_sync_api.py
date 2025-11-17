"""
数据同步API
提供增强数据的同步接口和管理功能
"""
from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.core.database import get_db
from app.services.data_sync_enhanced_service import data_sync_enhanced_service
from app.services.sync_services.sync_manager import sync_manager

logger = logging.getLogger(__name__)

data_sync_bp = Blueprint('data_sync', __name__)

# 线程池用于执行异步任务
executor = ThreadPoolExecutor(max_workers=10)


@data_sync_bp.route('/sync/industry', methods=['POST'])
def sync_industry_classification():
    """
    同步行业分类数据
    
    Request Body:
        {
            "src": "SW2021",  # 分类标准
            "level": "L1"     # 行业级别
        }
    """
    try:
        data = request.get_json() or {}
        src = data.get('src', 'SW2021')
        level = data.get('level', 'L1')
        
        # 运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        db = next(get_db())
        result = loop.run_until_complete(
            data_sync_enhanced_service.sync_industry_classification(db, src, level)
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"同步行业分类失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/sync/limit-prices', methods=['POST'])
def sync_limit_prices():
    """
    同步涨跌停价格数据
    
    Request Body:
        {
            "trade_date": "20240101",  # 可选
            "start_date": "20240101",  # 可选
            "end_date": "20240131"     # 可选
        }
    """
    try:
        data = request.get_json() or {}
        trade_date = data.get('trade_date')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        db = next(get_db())
        result = loop.run_until_complete(
            data_sync_enhanced_service.sync_limit_prices(db, trade_date, start_date, end_date)
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"同步涨跌停数据失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/sync/suspend', methods=['POST'])
def sync_suspend_info():
    """
    同步停复牌信息
    
    Request Body:
        {
            "start_date": "20240101",  # 可选
            "end_date": "20240131"     # 可选
        }
    """
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        db = next(get_db())
        result = loop.run_until_complete(
            data_sync_enhanced_service.sync_suspend_info(db, start_date, end_date)
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"同步停复牌数据失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/sync/audit', methods=['POST'])
def sync_audit_opinions():
    """
    同步审计意见数据
    
    Request Body:
        {
            "start_date": "20240101",  # 可选
            "end_date": "20240131"     # 可选
        }
    """
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        db = next(get_db())
        result = loop.run_until_complete(
            data_sync_enhanced_service.sync_audit_opinions(db, start_date, end_date)
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"同步审计意见失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/sync/all', methods=['POST'])
def sync_all_data():
    """
    同步所有增强数据
    """
    try:
        results = {}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        db = next(get_db())
        
        # 同步行业分类
        logger.info("开始同步行业分类...")
        results['industry'] = loop.run_until_complete(
            data_sync_enhanced_service.sync_industry_classification(db, 'SW2021', 'L1')
        )
        
        # 同步涨跌停
        logger.info("开始同步涨跌停数据...")
        results['limit_prices'] = loop.run_until_complete(
            data_sync_enhanced_service.sync_limit_prices(db)
        )
        
        # 同步停复牌
        logger.info("开始同步停复牌数据...")
        results['suspend'] = loop.run_until_complete(
            data_sync_enhanced_service.sync_suspend_info(db)
        )
        
        # 同步审计意见
        logger.info("开始同步审计意见...")
        results['audit'] = loop.run_until_complete(
            data_sync_enhanced_service.sync_audit_opinions(db)
        )
        
        success_count = sum(1 for r in results.values() if r.get('success'))
        
        return jsonify({
            'success': success_count == len(results),
            'message': f'完成{success_count}/{len(results)}个数据源同步',
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"批量同步失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/sync/status', methods=['GET'])
def get_sync_status():
    """
    获取数据同步状态
    """
    try:
        db = next(get_db())
        
        # 查询各表最新数据日期
        from sqlalchemy import text
        
        status = {}
        
        # 行业分类
        result = db.execute(text("SELECT COUNT(*) as count FROM industry_classification")).first()
        status['industry'] = {'count': result.count if result else 0}
        
        # 涨跌停
        result = db.execute(text("SELECT MAX(trade_date) as last_date, COUNT(*) as count FROM limit_prices")).first()
        status['limit_prices'] = {
            'count': result.count if result else 0,
            'last_date': result.last_date.strftime('%Y-%m-%d') if result and result.last_date else None
        }
        
        # 停复牌
        result = db.execute(text("SELECT MAX(suspend_date) as last_date, COUNT(*) as count FROM suspend_info")).first()
        status['suspend'] = {
            'count': result.count if result else 0,
            'last_date': result.last_date.strftime('%Y-%m-%d') if result and result.last_date else None
        }
        
        # 审计意见
        result = db.execute(text("SELECT MAX(ann_date) as last_date, COUNT(*) as count FROM audit_opinions")).first()
        status['audit'] = {
            'count': result.count if result else 0,
            'last_date': result.last_date.strftime('%Y-%m-%d') if result and result.last_date else None
        }
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/sync/config', methods=['GET'])
def get_sync_config():
    """
    获取数据同步配置
    """
    config = {
        'data_sources': [
            {
                'id': 'industry',
                'name': '行业分类',
                'api': '/api/data-sync/sync/industry',
                'params': {'src': 'SW2021', 'level': 'L1'},
                'schedule': 'weekly',
                'priority': 'high',
                'description': '申万行业分类数据'
            },
            {
                'id': 'limit_prices',
                'name': '涨跌停价格',
                'api': '/api/data-sync/sync/limit-prices',
                'params': {},
                'schedule': 'daily',
                'priority': 'high',
                'description': '每日涨跌停价格数据'
            },
            {
                'id': 'suspend',
                'name': '停复牌信息',
                'api': '/api/data-sync/sync/suspend',
                'params': {},
                'schedule': 'daily',
                'priority': 'high',
                'description': '股票停复牌信息'
            },
            {
                'id': 'audit',
                'name': '审计意见',
                'api': '/api/data-sync/sync/audit',
                'params': {},
                'schedule': 'monthly',
                'priority': 'medium',
                'description': '上市公司审计意见'
            }
        ]
    }
    
    return jsonify(config), 200


# ==================== 新的统一同步管理接口 ====================

@data_sync_bp.route('/services', methods=['GET'])
def get_sync_services():
    """
    获取所有同步服务列表
    
    Returns:
        {
            "success": true,
            "data": [
                {
                    "key": "stock_basic",
                    "name": "股票基础信息",
                    "description": "...",
                    "table": "stock_basic",
                    "frequency": "每日",
                    "api": "stock_basic",
                    "implemented": true
                },
                ...
            ]
        }
    """
    try:
        services = sync_manager.get_service_list()
        return jsonify({'success': True, 'data': services}), 200
        
    except Exception as e:
        logger.error(f"获取同步服务列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/services/<service_key>/start', methods=['POST'])
def start_sync_service(service_key: str):
    """
    启动同步任务（异步执行，立即返回）
    
    Args:
        service_key: 服务标识
        
    Request Body:
        {
            "start_date": "20240101",  # 可选
            "end_date": "20241231"     # 可选
        }
        
    Returns:
        {
            "success": true,
            "message": "同步任务已启动",
            "data": {
                "service_key": "stock_basic",
                "service_name": "股票基础信息"
            }
        }
    """
    try:
        params = request.get_json() or {}
        
        # 在后台线程中执行同步任务
        def run_sync():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(sync_manager.start_sync(service_key, **params))
                logger.info(f"同步任务完成: {service_key}, 结果: {result}")
            except Exception as e:
                logger.error(f"同步任务执行失败: {service_key}, 错误: {e}")
            finally:
                loop.close()
        
        # 提交到线程池
        executor.submit(run_sync)
        
        service_info = sync_manager.SYNC_SERVICES.get(service_key, {})
        
        return jsonify({
            'success': True,
            'message': '同步任务已启动',
            'data': {
                'service_key': service_key,
                'service_name': service_info.get('name', service_key),
                'params': params
            }
        }), 200
        
    except Exception as e:
        logger.error(f"启动同步任务失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/services/<service_key>/status', methods=['GET'])
def get_sync_service_status(service_key: str):
    """
    获取同步任务状态
    
    Args:
        service_key: 服务标识
        
    Returns:
        {
            "success": true,
            "data": {
                "service_key": "stock_basic",
                "service_name": "股票基础信息",
                "is_running": true,
                "progress": 45,
                "current": 2500,
                "total": 5582,
                "message": "正在同步...",
                "start_time": "2024-01-01T10:00:00",
                "end_time": null,
                "error": null
            }
        }
    """
    try:
        status = sync_manager.get_sync_status(service_key)
        return jsonify({'success': True, 'data': status}), 200
        
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/services/<service_key>/statistics', methods=['GET'])
def get_sync_service_statistics(service_key: str):
    """
    获取数据统计信息
    
    Args:
        service_key: 服务标识
        
    Returns:
        {
            "success": true,
            "data": {
                "table": "stock_basic",
                "total_count": 5582,
                "last_sync_date": "20241107",
                "implemented": true
            }
        }
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        stats = loop.run_until_complete(sync_manager.get_data_statistics(service_key))
        loop.close()
        
        return jsonify({'success': True, 'data': stats}), 200
        
    except Exception as e:
        logger.error(f"获取数据统计失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sync_bp.route('/services/batch-status', methods=['POST'])
def get_batch_sync_status():
    """
    批量获取多个服务的状态
    
    Request Body:
        {
            "service_keys": ["stock_basic", "trade_cal", "daily_history"]
        }
        
    Returns:
        {
            "success": true,
            "data": {
                "stock_basic": {...},
                "trade_cal": {...},
                ...
            }
        }
    """
    try:
        data = request.get_json() or {}
        service_keys = data.get('service_keys', [])
        
        result = {}
        for key in service_keys:
            result[key] = sync_manager.get_sync_status(key)
        
        return jsonify({'success': True, 'data': result}), 200
        
    except Exception as e:
        logger.error(f"批量获取状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
