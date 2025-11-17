# -*- coding: utf-8 -*-
"""
系统API模块

提供系统相关的REST API接口，包括系统监控、配置管理等功能
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any, List, Optional
from datetime import datetime
import psutil
import os

from app.middleware.auth import require_auth
from app.docs.swagger_config import get_swagger_spec


# 创建系统蓝图
system_bp = Blueprint('system', __name__, url_prefix='/api/system')


class SystemValidator:
    """系统数据验证器"""
    
    @staticmethod
    def validate_config_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置数据"""
        if not data:
            raise ValueError("配置数据不能为空")
        
        # 验证配置键值对
        for key, value in data.items():
            if not isinstance(key, str) or len(key.strip()) == 0:
                raise ValueError("配置键必须是非空字符串")
        
        return data


@system_bp.route('/health', methods=['GET'])
def health_check():
    """
    系统健康检查
    ---
    tags:
      - 系统
    summary: 系统健康检查
    description: 检查系统运行状态和健康指标
    responses:
      200:
        description: 系统正常
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "系统运行正常"
            data:
              type: object
              properties:
                status:
                  type: string
                  example: "healthy"
                timestamp:
                  type: string
                  format: date-time
                  example: "2023-12-01T15:30:00Z"
                uptime:
                  type: number
                  description: 系统运行时间（秒）
                  example: 86400
                version:
                  type: string
                  example: "1.0.0"
    """
    try:
        # 获取系统运行时间
        uptime = psutil.boot_time()
        current_time = datetime.now().timestamp()
        uptime_seconds = current_time - uptime
        
        return jsonify({
            'success': True,
            'message': '系统运行正常',
            'data': {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': uptime_seconds,
                'version': '1.0.0'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'系统健康检查失败: {str(e)}'
        }), 500


@system_bp.route('/status', methods=['GET'])
@require_auth
def get_system_status():
    """
    获取系统状态
    ---
    tags:
      - 系统
    summary: 获取系统状态
    description: 获取详细的系统运行状态信息
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "获取系统状态成功"
            data:
              type: object
              properties:
                cpu:
                  type: object
                  properties:
                    usage_percent:
                      type: number
                      example: 25.5
                    core_count:
                      type: integer
                      example: 8
                memory:
                  type: object
                  properties:
                    total:
                      type: number
                      description: 总内存（GB）
                      example: 16.0
                    used:
                      type: number
                      description: 已用内存（GB）
                      example: 8.5
                    usage_percent:
                      type: number
                      example: 53.1
                disk:
                  type: object
                  properties:
                    total:
                      type: number
                      description: 总磁盘空间（GB）
                      example: 500.0
                    used:
                      type: number
                      description: 已用磁盘空间（GB）
                      example: 250.0
                    usage_percent:
                      type: number
                      example: 50.0
                network:
                  type: object
                  properties:
                    bytes_sent:
                      type: number
                      example: 1024000
                    bytes_recv:
                      type: number
                      example: 2048000
                processes:
                  type: integer
                  description: 运行中的进程数
                  example: 156
      401:
        description: 未授权
      500:
        description: 服务器内部错误
    """
    try:
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024**3)
        memory_used_gb = memory.used / (1024**3)
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024**3)
        disk_used_gb = disk.used / (1024**3)
        
        # 网络信息
        network = psutil.net_io_counters()
        
        # 进程数
        process_count = len(psutil.pids())
        
        return jsonify({
            'success': True,
            'message': '获取系统状态成功',
            'data': {
                'cpu': {
                    'usage_percent': round(cpu_percent, 1),
                    'core_count': cpu_count
                },
                'memory': {
                    'total': round(memory_total_gb, 1),
                    'used': round(memory_used_gb, 1),
                    'usage_percent': round(memory.percent, 1)
                },
                'disk': {
                    'total': round(disk_total_gb, 1),
                    'used': round(disk_used_gb, 1),
                    'usage_percent': round(disk.percent, 1)
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                'processes': process_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取系统状态失败: {str(e)}'
        }), 500


@system_bp.route('/config', methods=['GET'])
@require_auth
def get_system_config():
    """
    获取系统配置
    ---
    tags:
      - 系统
    summary: 获取系统配置
    description: 获取系统配置信息
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "获取系统配置成功"
            data:
              type: object
              properties:
                database:
                  type: object
                  properties:
                    host:
                      type: string
                      example: "localhost"
                    port:
                      type: integer
                      example: 5432
                    name:
                      type: string
                      example: "stock_trading"
                redis:
                  type: object
                  properties:
                    host:
                      type: string
                      example: "localhost"
                    port:
                      type: integer
                      example: 6379
                api:
                  type: object
                  properties:
                    rate_limit:
                      type: integer
                      example: 1000
                    timeout:
                      type: integer
                      example: 30
                trading:
                  type: object
                  properties:
                    commission_rate:
                      type: number
                      example: 0.0003
                    slippage:
                      type: number
                      example: 0.001
      401:
        description: 未授权
      500:
        description: 服务器内部错误
    """
    try:
        # 模拟系统配置
        config = {
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'name': os.getenv('DB_NAME', 'stock_trading')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379))
            },
            'api': {
                'rate_limit': int(os.getenv('API_RATE_LIMIT', 1000)),
                'timeout': int(os.getenv('API_TIMEOUT', 30))
            },
            'trading': {
                'commission_rate': float(os.getenv('COMMISSION_RATE', 0.0003)),
                'slippage': float(os.getenv('SLIPPAGE', 0.001))
            }
        }
        
        return jsonify({
            'success': True,
            'message': '获取系统配置成功',
            'data': config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取系统配置失败: {str(e)}'
        }), 500


@system_bp.route('/config', methods=['PUT'])
@require_auth
def update_system_config():
    """
    更新系统配置
    ---
    tags:
      - 系统
    summary: 更新系统配置
    description: 更新系统配置信息
    parameters:
      - in: body
        name: config
        description: 配置信息
        required: true
        schema:
          type: object
          properties:
            api:
              type: object
              properties:
                rate_limit:
                  type: integer
                  example: 1500
                timeout:
                  type: integer
                  example: 60
            trading:
              type: object
              properties:
                commission_rate:
                  type: number
                  example: 0.0005
                slippage:
                  type: number
                  example: 0.002
    responses:
      200:
        description: 更新成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "系统配置更新成功"
            data:
              type: object
              properties:
                updated_fields:
                  type: array
                  items:
                    type: string
                  example: ["api.rate_limit", "trading.commission_rate"]
                updated_at:
                  type: string
                  format: date-time
                  example: "2023-12-01T16:30:00Z"
      400:
        description: 请求参数错误
      401:
        description: 未授权
      500:
        description: 服务器内部错误
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证配置数据
        validated_data = SystemValidator.validate_config_data(data)
        
        # 模拟更新配置
        updated_fields = []
        for section, config in validated_data.items():
            if isinstance(config, dict):
                for key, value in config.items():
                    updated_fields.append(f"{section}.{key}")
        
        return jsonify({
            'success': True,
            'message': '系统配置更新成功',
            'data': {
                'updated_fields': updated_fields,
                'updated_at': datetime.now().isoformat()
            }
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'系统配置更新失败: {str(e)}'
        }), 500


@system_bp.route('/logs', methods=['GET'])
@require_auth
def get_system_logs():
    """
    获取系统日志
    ---
    tags:
      - 系统
    summary: 获取系统日志
    description: 获取系统运行日志
    parameters:
      - in: query
        name: level
        type: string
        description: 日志级别筛选
        enum: [DEBUG, INFO, WARNING, ERROR, CRITICAL]
        example: "ERROR"
      - in: query
        name: start_time
        type: string
        format: date-time
        description: 开始时间
        example: "2023-12-01T00:00:00Z"
      - in: query
        name: end_time
        type: string
        format: date-time
        description: 结束时间
        example: "2023-12-01T23:59:59Z"
      - in: query
        name: page
        type: integer
        minimum: 1
        default: 1
        description: 页码
        example: 1
      - in: query
        name: page_size
        type: integer
        minimum: 1
        maximum: 100
        default: 50
        description: 每页数量
        example: 50
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "获取系统日志成功"
            data:
              type: object
              properties:
                logs:
                  type: array
                  items:
                    type: object
                    properties:
                      timestamp:
                        type: string
                        format: date-time
                        example: "2023-12-01T15:30:00Z"
                      level:
                        type: string
                        example: "INFO"
                      module:
                        type: string
                        example: "trading_engine"
                      message:
                        type: string
                        example: "交易订单执行成功"
                      details:
                        type: object
                        example: {"order_id": "ORD_001", "symbol": "000001.SZ"}
                total:
                  type: integer
                  example: 1250
                page:
                  type: integer
                  example: 1
                page_size:
                  type: integer
                  example: 50
                total_pages:
                  type: integer
                  example: 25
      401:
        description: 未授权
      500:
        description: 服务器内部错误
    """
    try:
        # 获取查询参数
        level = request.args.get('level')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 50)), 100)
        
        # 模拟日志数据
        logs = [
            {
                'timestamp': datetime.now().isoformat(),
                'level': level or 'INFO',
                'module': 'trading_engine',
                'message': f'系统日志消息 {i}',
                'details': {'log_id': f'LOG_{i:03d}'}
            }
            for i in range(1, 26)
        ]
        
        total = len(logs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = logs[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'message': '获取系统日志成功',
            'data': {
                'logs': paginated_logs,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取系统日志失败: {str(e)}'
        }), 500


@system_bp.route('/metrics', methods=['GET'])
@require_auth
def get_system_metrics():
    """
    获取系统指标
    ---
    tags:
      - 系统
    summary: 获取系统指标
    description: 获取系统性能指标和统计信息
    parameters:
      - in: query
        name: period
        type: string
        description: 时间周期
        enum: [1h, 6h, 24h, 7d, 30d]
        default: "24h"
        example: "24h"
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "获取系统指标成功"
            data:
              type: object
              properties:
                period:
                  type: string
                  example: "24h"
                metrics:
                  type: object
                  properties:
                    api_requests:
                      type: object
                      properties:
                        total:
                          type: integer
                          example: 15420
                        success_rate:
                          type: number
                          example: 99.2
                        avg_response_time:
                          type: number
                          description: 平均响应时间（毫秒）
                          example: 125.5
                    trading:
                      type: object
                      properties:
                        orders_processed:
                          type: integer
                          example: 1250
                        success_rate:
                          type: number
                          example: 98.8
                        avg_execution_time:
                          type: number
                          description: 平均执行时间（毫秒）
                          example: 85.2
                    system:
                      type: object
                      properties:
                        avg_cpu_usage:
                          type: number
                          example: 35.2
                        avg_memory_usage:
                          type: number
                          example: 68.5
                        error_count:
                          type: integer
                          example: 12
      401:
        description: 未授权
      500:
        description: 服务器内部错误
    """
    try:
        period = request.args.get('period', '24h')
        
        # 模拟系统指标数据
        metrics = {
            'period': period,
            'metrics': {
                'api_requests': {
                    'total': 15420,
                    'success_rate': 99.2,
                    'avg_response_time': 125.5
                },
                'trading': {
                    'orders_processed': 1250,
                    'success_rate': 98.8,
                    'avg_execution_time': 85.2
                },
                'system': {
                    'avg_cpu_usage': 35.2,
                    'avg_memory_usage': 68.5,
                    'error_count': 12
                }
            }
        }
        
        return jsonify({
            'success': True,
            'message': '获取系统指标成功',
            'data': metrics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取系统指标失败: {str(e)}'
        }), 500








