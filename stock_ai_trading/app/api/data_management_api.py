# -*- coding: utf-8 -*-
"""
数据管理API模块

提供数据源管理和API管理的REST API接口
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.middleware.auth import require_auth
from app.core.database import get_db
from app.services.tushare_service import tushare_service
from app.services.tushare_api_sync import tushare_api_sync_service

# 创建数据管理蓝图
data_mgmt_bp = Blueprint('data_management', __name__, url_prefix='/api/data-management')

logger = logging.getLogger(__name__)

# ==================== 数据源管理接口 ====================

@data_mgmt_bp.route('/data-sources', methods=['GET'])
@require_auth
def get_data_sources():
    """获取数据源列表"""
    try:
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 20))
            type_filter = request.args.get('type')
            status_filter = request.args.get('status')
            
            # 构建查询
            query = """
                SELECT id, name, type, provider, status, api_key, base_url, 
                       timeout, rate_limit, total_calls, success_calls, 
                       last_call_time, created_at, updated_at
                FROM data_sources 
                WHERE 1=1
            """
            params = {}
            
            if type_filter:
                query += " AND type = :type_filter"
                params['type_filter'] = type_filter
                
            if status_filter:
                query += " AND status = :status_filter"
                params['status_filter'] = status_filter
            
            query += " ORDER BY created_at DESC"
            
            # 分页
            offset = (page - 1) * size
            query += f" LIMIT {size} OFFSET {offset}"
            
            result = db_session.execute(text(query), params)
            data_sources = []
            
            for row in result:
                data_source = {
                    'id': row.id,
                    'name': row.name,
                    'type': row.type,
                    'provider': row.provider,
                    'status': row.status,
                    'has_api_key': bool(row.api_key),  # 不返回实际密钥
                    'base_url': row.base_url,
                    'timeout': row.timeout,
                    'rate_limit': row.rate_limit,
                    'total_calls': row.total_calls,
                    'success_calls': row.success_calls,
                    'success_rate': round((row.success_calls / row.total_calls * 100), 2) if row.total_calls > 0 else 0,
                    'last_call_time': row.last_call_time.isoformat() if row.last_call_time else None,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'updated_at': row.updated_at.isoformat() if row.updated_at else None
                }
                data_sources.append(data_source)
            
            # 获取总数
            count_query = "SELECT COUNT(*) as total FROM data_sources WHERE 1=1"
            if type_filter:
                count_query += " AND type = :type_filter"
            if status_filter:
                count_query += " AND status = :status_filter"
                
            total_result = db_session.execute(text(count_query), params)
            total = total_result.fetchone().total
            
            return jsonify({
                "success": True,
                "data": {
                    "items": data_sources,
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": (total + size - 1) // size
                }
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"获取数据源列表失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取数据源列表失败",
            "message": str(e)
        }), 500

@data_mgmt_bp.route('/data-sources', methods=['POST'])
@require_auth
def create_data_source():
    """创建数据源"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['name', 'type', 'provider']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "error": f"缺少必需字段: {field}"
                }), 400
        
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            # 检查名称是否已存在
            check_query = "SELECT COUNT(*) as count FROM data_sources WHERE name = :name"
            result = db_session.execute(text(check_query), {'name': data['name']})
            if result.fetchone().count > 0:
                return jsonify({
                    "success": False,
                    "error": "数据源名称已存在"
                }), 400
            
            # 插入数据源
            insert_query = """
                INSERT INTO data_sources (name, type, provider, status, api_key, api_secret, 
                                        base_url, timeout, rate_limit, config_params, created_by)
                VALUES (:name, :type, :provider, :status, :api_key, :api_secret, 
                        :base_url, :timeout, :rate_limit, :config_params, :created_by)
            """
            
            params = {
                'name': data['name'],
                'type': data['type'],
                'provider': data['provider'],
                'status': data.get('status', 'inactive'),
                'api_key': data.get('api_key'),
                'api_secret': data.get('api_secret'),
                'base_url': data.get('base_url'),
                'timeout': data.get('timeout', 30),
                'rate_limit': data.get('rate_limit', 200),
                'config_params': json.dumps(data.get('config_params', {})),
                'created_by': g.current_user.get('id') if hasattr(g, 'current_user') else None
            }
            
            db_session.execute(text(insert_query), params)
            db_session.commit()
            
            return jsonify({
                "success": True,
                "message": "数据源创建成功"
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"创建数据源失败: {e}")
        return jsonify({
            "success": False,
            "error": "创建数据源失败",
            "message": str(e)
        }), 500

@data_mgmt_bp.route('/data-sources/<int:source_id>', methods=['PUT'])
@require_auth
def update_data_source(source_id):
    """更新数据源"""
    try:
        data = request.get_json()
        
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            # 检查数据源是否存在
            check_query = "SELECT COUNT(*) as count FROM data_sources WHERE id = :id"
            result = db_session.execute(text(check_query), {'id': source_id})
            if result.fetchone().count == 0:
                return jsonify({
                    "success": False,
                    "error": "数据源不存在"
                }), 404
            
            # 构建更新语句
            update_fields = []
            params = {'id': source_id}
            
            allowed_fields = ['name', 'status', 'api_key', 'api_secret', 'base_url', 
                            'timeout', 'rate_limit', 'config_params']
            
            for field in allowed_fields:
                if field in data:
                    if field == 'config_params':
                        update_fields.append(f"{field} = :{field}")
                        params[field] = json.dumps(data[field])
                    else:
                        update_fields.append(f"{field} = :{field}")
                        params[field] = data[field]
            
            if not update_fields:
                return jsonify({
                    "success": False,
                    "error": "没有可更新的字段"
                }), 400
            
            params['updated_by'] = g.current_user.get('id') if hasattr(g, 'current_user') else None
            update_fields.append("updated_by = :updated_by")
            
            update_query = f"""
                UPDATE data_sources 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """
            
            db_session.execute(text(update_query), params)
            db_session.commit()
            
            return jsonify({
                "success": True,
                "message": "数据源更新成功"
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"更新数据源失败: {e}")
        return jsonify({
            "success": False,
            "error": "更新数据源失败",
            "message": str(e)
        }), 500

@data_mgmt_bp.route('/data-sources/<int:source_id>', methods=['DELETE'])
@require_auth
def delete_data_source(source_id):
    """删除数据源"""
    try:
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            # 检查数据源是否存在
            check_query = "SELECT COUNT(*) as count FROM data_sources WHERE id = :id"
            result = db_session.execute(text(check_query), {'id': source_id})
            if result.fetchone().count == 0:
                return jsonify({
                    "success": False,
                    "error": "数据源不存在"
                }), 404
            
            # 删除数据源（级联删除相关API接口）
            delete_query = "DELETE FROM data_sources WHERE id = :id"
            db_session.execute(text(delete_query), {'id': source_id})
            db_session.commit()
            
            return jsonify({
                "success": True,
                "message": "数据源删除成功"
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"删除数据源失败: {e}")
        return jsonify({
            "success": False,
            "error": "删除数据源失败",
            "message": str(e)
        }), 500

@data_mgmt_bp.route('/data-sources/<int:source_id>/test', methods=['POST'])
@require_auth
def test_data_source(source_id):
    """测试数据源连接"""
    try:
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            # 获取数据源信息
            query = """
                SELECT name, type, provider, api_key, base_url, timeout
                FROM data_sources WHERE id = :id
            """
            result = db_session.execute(text(query), {'id': source_id})
            source = result.fetchone()
            
            if not source:
                return jsonify({
                    "success": False,
                    "error": "数据源不存在"
                }), 404
            
            # 根据提供商类型进行测试
            if source.provider == 'tushare':
                # 测试Tushare连接
                test_result = tushare_service.test_connection()
                
                # 更新最后调用时间
                update_query = """
                    UPDATE data_sources 
                    SET last_call_time = CURRENT_TIMESTAMP,
                        total_calls = total_calls + 1
                    WHERE id = :id
                """
                
                if test_result['success']:
                    update_query = update_query.replace(
                        "total_calls = total_calls + 1",
                        "total_calls = total_calls + 1, success_calls = success_calls + 1, last_success_time = CURRENT_TIMESTAMP"
                    )
                
                db_session.execute(text(update_query), {'id': source_id})
                db_session.commit()
                
                return jsonify({
                    "success": test_result['success'],
                    "message": test_result['message'],
                    "data": test_result.get('data')
                })
            else:
                return jsonify({
                    "success": False,
                    "message": f"暂不支持 {source.provider} 数据源测试"
                })
                
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"测试数据源失败: {e}")
        return jsonify({
            "success": False,
            "error": "测试数据源失败",
            "message": str(e)
        }), 500

# ==================== API接口管理 ====================

@data_mgmt_bp.route('/api-interfaces', methods=['GET'])
@require_auth
def get_api_interfaces():
    """获取API接口列表"""
    try:
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 20))
            data_source_id = request.args.get('data_source_id')
            category = request.args.get('category')
            status = request.args.get('status')
            
            # 构建查询
            query = """
                SELECT ai.*, ds.name as data_source_name, ds.provider
                FROM api_interfaces ai
                JOIN data_sources ds ON ai.data_source_id = ds.id
                WHERE 1=1
            """
            params = {}
            
            if data_source_id:
                query += " AND ai.data_source_id = :data_source_id"
                params['data_source_id'] = data_source_id
                
            if category:
                query += " AND ai.api_category = :category"
                params['category'] = category
                
            if status:
                query += " AND ai.status = :status"
                params['status'] = status
            
            query += " ORDER BY ai.api_category, ai.api_code"
            
            # 分页
            offset = (page - 1) * size
            query += f" LIMIT {size} OFFSET {offset}"
            
            result = db_session.execute(text(query), params)
            api_interfaces = []
            
            for row in result:
                api_interface = {
                    'id': row.id,
                    'data_source_id': row.data_source_id,
                    'data_source_name': row.data_source_name,
                    'provider': row.provider,
                    'api_code': row.api_code,
                    'api_name': row.api_name,
                    'api_category': row.api_category,
                    'description': row.description,
                    'endpoint': row.endpoint,
                    'method': row.method,
                    'required_params': json.loads(row.required_params) if row.required_params else [],
                    'optional_params': json.loads(row.optional_params) if row.optional_params else [],
                    'response_fields': json.loads(row.response_fields) if row.response_fields else [],
                    'required_points': row.required_points,
                    'rate_limit': row.rate_limit,
                    'status': row.status,
                    'total_calls': row.total_calls,
                    'success_calls': row.success_calls,
                    'success_rate': round((row.success_calls / row.total_calls * 100), 2) if row.total_calls > 0 else 0,
                    'avg_response_time': float(row.avg_response_time) if row.avg_response_time else 0,
                    'last_call_time': row.last_call_time.isoformat() if row.last_call_time else None,
                    'synced_at': row.synced_at.isoformat() if row.synced_at else None,
                    'created_at': row.created_at.isoformat() if row.created_at else None
                }
                api_interfaces.append(api_interface)
            
            # 获取总数
            count_query = """
                SELECT COUNT(*) as total 
                FROM api_interfaces ai
                JOIN data_sources ds ON ai.data_source_id = ds.id
                WHERE 1=1
            """
            if data_source_id:
                count_query += " AND ai.data_source_id = :data_source_id"
            if category:
                count_query += " AND ai.api_category = :category"
            if status:
                count_query += " AND ai.status = :status"
                
            total_result = db_session.execute(text(count_query), params)
            total = total_result.fetchone().total
            
            return jsonify({
                "success": True,
                "data": {
                    "items": api_interfaces,
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": (total + size - 1) // size
                }
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"获取API接口列表失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取API接口列表失败",
            "message": str(e)
        }), 500

@data_mgmt_bp.route('/api-interfaces/<int:api_id>/test', methods=['POST'])
@require_auth
async def test_api_interface(api_id):
    """测试API接口"""
    try:
        data = request.get_json()
        test_params = data.get('params', {})
        
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            # 获取API接口信息
            query = """
                SELECT ai.*, ds.provider, ds.api_key
                FROM api_interfaces ai
                JOIN data_sources ds ON ai.data_source_id = ds.id
                WHERE ai.id = :id
            """
            result = db_session.execute(text(query), {'id': api_id})
            api_info = result.fetchone()
            
            if not api_info:
                return jsonify({
                    "success": False,
                    "error": "API接口不存在"
                }), 404
            
            # 记录调用开始时间
            start_time = datetime.now()
            
            # 根据提供商调用API
            if api_info.provider == 'tushare':
                # 调用Tushare API
                try:
                    # 这里需要根据具体的API代码调用相应的方法
                    if api_info.api_code == 'stock_basic':
                        df = await tushare_service.get_stock_basic(**test_params)
                        if df is not None and not df.empty:
                            response_data = df.head(10).to_dict('records')  # 只返回前10条数据
                            success = True
                            error_message = None
                        else:
                            response_data = []
                            success = False
                            error_message = "未获取到数据"
                    else:
                        # 其他API接口的调用逻辑
                        response_data = {"message": f"API {api_info.api_code} 测试功能待实现"}
                        success = True
                        error_message = None
                        
                except Exception as api_error:
                    response_data = None
                    success = False
                    error_message = str(api_error)
            else:
                response_data = {"message": f"暂不支持 {api_info.provider} 提供商的API测试"}
                success = False
                error_message = "不支持的提供商"
            
            # 计算响应时间
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # 记录调用日志
            log_query = """
                INSERT INTO api_call_logs (api_interface_id, call_type, request_params, 
                                         success, response_data, response_time, error_message, called_by)
                VALUES (:api_id, 'test', :request_params, :success, :response_data, 
                        :response_time, :error_message, :called_by)
            """
            
            log_params = {
                'api_id': api_id,
                'request_params': json.dumps(test_params),
                'success': success,
                'response_data': json.dumps(response_data) if response_data else None,
                'response_time': response_time,
                'error_message': error_message,
                'called_by': g.current_user.get('id') if hasattr(g, 'current_user') else None
            }
            
            db_session.execute(text(log_query), log_params)
            
            # 更新API接口统计
            update_query = """
                UPDATE api_interfaces 
                SET total_calls = total_calls + 1,
                    last_call_time = CURRENT_TIMESTAMP,
                    avg_response_time = CASE 
                        WHEN total_calls = 0 THEN :response_time
                        ELSE (avg_response_time * total_calls + :response_time) / (total_calls + 1)
                    END
            """
            
            if success:
                update_query += ", success_calls = success_calls + 1, last_success_time = CURRENT_TIMESTAMP"
            
            update_query += " WHERE id = :api_id"
            
            db_session.execute(text(update_query), {
                'api_id': api_id,
                'response_time': response_time
            })
            
            db_session.commit()
            
            return jsonify({
                "success": success,
                "message": "API测试完成" if success else f"API测试失败: {error_message}",
                "data": {
                    "response_data": response_data,
                    "response_time": response_time,
                    "error_message": error_message
                }
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"测试API接口失败: {e}")
        return jsonify({
            "success": False,
            "error": "测试API接口失败",
            "message": str(e)
        }), 500

@data_mgmt_bp.route('/api-interfaces/<int:api_id>/logs', methods=['GET'])
@require_auth
def get_api_call_logs(api_id):
    """获取API调用日志"""
    try:
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 20))
            
            # 获取调用日志
            query = """
                SELECT id, call_type, request_params, success, response_data, 
                       response_time, error_message, called_at
                FROM api_call_logs 
                WHERE api_interface_id = :api_id
                ORDER BY called_at DESC
                LIMIT :size OFFSET :offset
            """
            
            offset = (page - 1) * size
            result = db_session.execute(text(query), {
                'api_id': api_id,
                'size': size,
                'offset': offset
            })
            
            logs = []
            for row in result:
                log = {
                    'id': row.id,
                    'call_type': row.call_type,
                    'request_params': json.loads(row.request_params) if row.request_params else {},
                    'success': row.success,
                    'response_data': json.loads(row.response_data) if row.response_data else None,
                    'response_time': float(row.response_time) if row.response_time else 0,
                    'error_message': row.error_message,
                    'called_at': row.called_at.isoformat() if row.called_at else None
                }
                logs.append(log)
            
            # 获取总数
            count_query = "SELECT COUNT(*) as total FROM api_call_logs WHERE api_interface_id = :api_id"
            total_result = db_session.execute(text(count_query), {'api_id': api_id})
            total = total_result.fetchone().total
            
            return jsonify({
                "success": True,
                "data": {
                    "items": logs,
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": (total + size - 1) // size
                }
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"获取API调用日志失败: {e}")
        return jsonify({
                "success": False,
                "error": "获取API调用日志失败",
                "message": str(e)
            }), 500

# ==================== API同步管理 ====================

@data_mgmt_bp.route('/data-sources/<int:source_id>/sync-apis', methods=['POST'])
@require_auth
def sync_apis(source_id):
    """同步API接口"""
    try:
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            # 检查数据源是否存在且为Tushare
            query = """
                SELECT provider FROM data_sources 
                WHERE id = :id AND status = 'active'
            """
            result = db_session.execute(text(query), {'id': source_id})
            source = result.fetchone()
            
            if not source:
                return jsonify({
                    "success": False,
                    "error": "数据源不存在或未启用"
                }), 404
            
            if source.provider != 'tushare':
                return jsonify({
                    "success": False,
                    "error": "仅支持Tushare数据源的API同步"
                }), 400
            
            # 执行同步
            sync_result = tushare_api_sync_service.sync_apis_to_database(source_id)
            
            if sync_result['success']:
                return jsonify({
                    "success": True,
                    "message": "API同步成功",
                    "data": sync_result['data']
                })
            else:
                return jsonify({
                    "success": False,
                    "error": sync_result['error'],
                    "message": sync_result['message']
                }), 500
                
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"同步API失败: {e}")
        return jsonify({
            "success": False,
            "error": "同步API失败",
            "message": str(e)
        }), 500

@data_mgmt_bp.route('/sync-tasks', methods=['GET'])
@require_auth
def get_sync_tasks():
    """获取同步任务列表"""
    try:
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 20))
            data_source_id = request.args.get('data_source_id')
            
            # 构建查询
            query = """
                SELECT st.*, ds.name as data_source_name, ds.provider
                FROM api_sync_tasks st
                JOIN data_sources ds ON st.data_source_id = ds.id
                WHERE 1=1
            """
            params = {}
            
            if data_source_id:
                query += " AND st.data_source_id = :data_source_id"
                params['data_source_id'] = data_source_id
            
            query += " ORDER BY st.created_at DESC"
            
            # 分页
            offset = (page - 1) * size
            query += f" LIMIT {size} OFFSET {offset}"
            
            result = db_session.execute(text(query), params)
            tasks = []
            
            for row in result:
                task = {
                    'id': row.id,
                    'data_source_id': row.data_source_id,
                    'data_source_name': row.data_source_name,
                    'provider': row.provider,
                    'task_name': row.task_name,
                    'task_type': row.task_type,
                    'status': row.status,
                    'progress': row.progress,
                    'total_apis': row.total_apis,
                    'new_apis': row.new_apis,
                    'updated_apis': row.updated_apis,
                    'failed_apis': row.failed_apis,
                    'error_message': row.error_message,
                    'started_at': row.started_at.isoformat() if row.started_at else None,
                    'completed_at': row.completed_at.isoformat() if row.completed_at else None,
                    'created_at': row.created_at.isoformat() if row.created_at else None
                }
                tasks.append(task)
            
            # 获取总数
            count_query = """
                SELECT COUNT(*) as total 
                FROM api_sync_tasks st
                JOIN data_sources ds ON st.data_source_id = ds.id
                WHERE 1=1
            """
            if data_source_id:
                count_query += " AND st.data_source_id = :data_source_id"
                
            total_result = db_session.execute(text(count_query), params)
            total = total_result.fetchone().total
            
            return jsonify({
                "success": True,
                "data": {
                    "items": tasks,
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": (total + size - 1) // size
                }
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"获取同步任务列表失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取同步任务列表失败",
            "message": str(e)
        }), 500

@data_mgmt_bp.route('/api-categories', methods=['GET'])
@require_auth
def get_api_categories():
    """获取API分类列表"""
    try:
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            data_source_id = request.args.get('data_source_id')
            
            query = """
                SELECT api_category, COUNT(*) as api_count
                FROM api_interfaces
                WHERE 1=1
            """
            params = {}
            
            if data_source_id:
                query += " AND data_source_id = :data_source_id"
                params['data_source_id'] = data_source_id
            
            query += " GROUP BY api_category ORDER BY api_category"
            
            result = db_session.execute(text(query), params)
            categories = []
            
            for row in result:
                categories.append({
                    'category': row.api_category,
                    'api_count': row.api_count
                })
            
            return jsonify({
                "success": True,
                "data": categories
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"获取API分类失败: {e}")
        return jsonify({
            "success": False,
            "error": "获取API分类失败",
            "message": str(e)
        }), 500