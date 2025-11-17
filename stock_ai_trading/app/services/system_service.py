"""
系统服务

提供系统状态监控、控制、性能指标等功能
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import psutil
import platform
import uuid
import random
import json
import os

from app.models.system import (
    SystemStatus, SystemHealth, SystemMetrics, SystemAlert,
    AlertLevel, AlertStatus, BackupInfo, MaintenanceTask
)


class SystemService:
    """系统服务类"""
    
    def __init__(self):
        # 模拟数据存储
        self.alerts: Dict[str, SystemAlert] = {}
        self.backups: List[BackupInfo] = []
        self.maintenance_tasks: Dict[str, MaintenanceTask] = {}
        self.system_config: Dict[str, Any] = {}
        self.performance_history: List[Dict[str, Any]] = []
        
        # 初始化示例数据
        self._init_sample_data()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        # 创建示例告警
        sample_alerts = [
            {
                'level': AlertLevel.WARNING,
                'title': 'CPU使用率过高',
                'message': 'CPU使用率达到85%，建议检查系统负载',
                'source': 'system_monitor',
                'category': 'performance'
            },
            {
                'level': AlertLevel.INFO,
                'title': '系统备份完成',
                'message': '定时备份任务已成功完成',
                'source': 'backup_service',
                'category': 'backup'
            },
            {
                'level': AlertLevel.ERROR,
                'title': '数据库连接异常',
                'message': '数据库连接池出现异常，部分连接失败',
                'source': 'database',
                'category': 'database'
            }
        ]
        
        for alert_data in sample_alerts:
            alert = SystemAlert(
                alert_id=str(uuid.uuid4()),
                level=alert_data['level'],
                title=alert_data['title'],
                message=alert_data['message'],
                source=alert_data['source'],
                category=alert_data['category'],
                status=AlertStatus.ACTIVE,
                created_at=datetime.now() - timedelta(minutes=random.randint(1, 1440))
            )
            self.alerts[alert.alert_id] = alert
        
        # 创建示例备份
        for i in range(5):
            backup = BackupInfo(
                backup_id=str(uuid.uuid4()),
                backup_type='full' if i % 2 == 0 else 'incremental',
                description=f'自动备份 #{i+1}',
                file_path=f'/backups/backup_{i+1}.tar.gz',
                file_size=random.randint(100, 1000) * 1024 * 1024,  # MB
                status='completed',
                created_at=datetime.now() - timedelta(days=i+1),
                completed_at=datetime.now() - timedelta(days=i+1, hours=-1)
            )
            self.backups.append(backup)
        
        # 初始化系统配置
        self.system_config = {
            'trading': {
                'max_positions': 50,
                'max_order_amount': 1000000,
                'risk_check_enabled': True,
                'auto_trade_enabled': False
            },
            'risk_control': {
                'max_daily_loss': 0.05,
                'max_position_size': 0.1,
                'stop_loss_enabled': True,
                'emergency_stop_enabled': True
            },
            'system': {
                'log_level': 'INFO',
                'backup_enabled': True,
                'backup_frequency': 'daily',
                'alert_enabled': True,
                'maintenance_window': '02:00-04:00'
            },
            'api': {
                'rate_limit_enabled': True,
                'max_requests_per_minute': 1000,
                'jwt_expiry_hours': 24,
                'api_key_enabled': True
            }
        }
        
        # 生成性能历史数据
        self._generate_performance_history()
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # 获取系统基本信息
            system_info = {
                'hostname': platform.node(),
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'uptime': self._get_system_uptime(),
                'current_time': datetime.now().isoformat()
            }
            
            # 获取CPU信息
            cpu_info = {
                'usage_percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'count_logical': psutil.cpu_count(logical=True),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
            
            # 获取内存信息
            memory = psutil.virtual_memory()
            memory_info = {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'usage_percent': memory.percent,
                'free': memory.free
            }
            
            # 获取磁盘信息
            disk = psutil.disk_usage('/')
            disk_info = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'usage_percent': (disk.used / disk.total) * 100
            }
            
            # 获取网络信息
            network = psutil.net_io_counters()
            network_info = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # 获取进程信息
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按CPU使用率排序，取前10个
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            top_processes = processes[:10]
            
            # 获取服务状态
            services_status = self._get_services_status()
            
            return {
                'system_info': system_info,
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'network': network_info,
                'top_processes': top_processes,
                'services': services_status,
                'status': 'running',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            health_checks = []
            overall_status = 'healthy'
            
            # CPU健康检查
            cpu_usage = psutil.cpu_percent(interval=1)
            cpu_status = 'healthy' if cpu_usage < 80 else 'warning' if cpu_usage < 95 else 'critical'
            health_checks.append({
                'name': 'CPU使用率',
                'status': cpu_status,
                'value': f"{cpu_usage}%",
                'threshold': '80%',
                'message': f"CPU使用率: {cpu_usage}%"
            })
            
            # 内存健康检查
            memory = psutil.virtual_memory()
            memory_status = 'healthy' if memory.percent < 80 else 'warning' if memory.percent < 95 else 'critical'
            health_checks.append({
                'name': '内存使用率',
                'status': memory_status,
                'value': f"{memory.percent}%",
                'threshold': '80%',
                'message': f"内存使用率: {memory.percent}%"
            })
            
            # 磁盘健康检查
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_status = 'healthy' if disk_percent < 80 else 'warning' if disk_percent < 95 else 'critical'
            health_checks.append({
                'name': '磁盘使用率',
                'status': disk_status,
                'value': f"{disk_percent:.1f}%",
                'threshold': '80%',
                'message': f"磁盘使用率: {disk_percent:.1f}%"
            })
            
            # 数据库连接检查（模拟）
            db_status = random.choice(['healthy', 'warning'])
            health_checks.append({
                'name': '数据库连接',
                'status': db_status,
                'value': 'connected' if db_status == 'healthy' else 'slow',
                'threshold': 'connected',
                'message': '数据库连接正常' if db_status == 'healthy' else '数据库连接缓慢'
            })
            
            # API服务检查（模拟）
            api_status = 'healthy'
            health_checks.append({
                'name': 'API服务',
                'status': api_status,
                'value': 'running',
                'threshold': 'running',
                'message': 'API服务运行正常'
            })
            
            # 确定整体状态
            if any(check['status'] == 'critical' for check in health_checks):
                overall_status = 'critical'
            elif any(check['status'] == 'warning' for check in health_checks):
                overall_status = 'warning'
            
            return {
                'status': overall_status,
                'checks': health_checks,
                'timestamp': datetime.now().isoformat(),
                'uptime': self._get_system_uptime()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_system_metrics(self, period: str = '1h', metric_types: List[str] = None) -> Dict[str, Any]:
        """获取系统性能指标"""
        try:
            # 计算时间范围
            period_minutes = {
                '5m': 5,
                '15m': 15,
                '1h': 60,
                '6h': 360,
                '24h': 1440,
                '7d': 10080
            }.get(period, 60)
            
            start_time = datetime.now() - timedelta(minutes=period_minutes)
            
            # 过滤历史数据
            filtered_data = [
                data for data in self.performance_history
                if datetime.fromisoformat(data['timestamp']) >= start_time
            ]
            
            # 如果没有指定指标类型，返回所有类型
            if not metric_types:
                metric_types = ['cpu', 'memory', 'disk', 'network']
            
            metrics = {
                'period': period,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'data_points': len(filtered_data)
            }
            
            # 处理不同类型的指标
            for metric_type in metric_types:
                if metric_type == 'cpu':
                    metrics['cpu'] = self._process_cpu_metrics(filtered_data)
                elif metric_type == 'memory':
                    metrics['memory'] = self._process_memory_metrics(filtered_data)
                elif metric_type == 'disk':
                    metrics['disk'] = self._process_disk_metrics(filtered_data)
                elif metric_type == 'network':
                    metrics['network'] = self._process_network_metrics(filtered_data)
            
            return metrics
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_performance_stats(self, start_time: str = '', end_time: str = '') -> Dict[str, Any]:
        """获取性能统计"""
        try:
            # 解析时间范围
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_dt = datetime.now() - timedelta(hours=24)
            
            if end_time:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            else:
                end_dt = datetime.now()
            
            # 过滤数据
            filtered_data = [
                data for data in self.performance_history
                if start_dt <= datetime.fromisoformat(data['timestamp']) <= end_dt
            ]
            
            if not filtered_data:
                return {
                    'message': '指定时间范围内没有数据',
                    'start_time': start_dt.isoformat(),
                    'end_time': end_dt.isoformat()
                }
            
            # 计算统计信息
            cpu_values = [data['cpu_percent'] for data in filtered_data]
            memory_values = [data['memory_percent'] for data in filtered_data]
            disk_values = [data['disk_percent'] for data in filtered_data]
            
            stats = {
                'time_range': {
                    'start_time': start_dt.isoformat(),
                    'end_time': end_dt.isoformat(),
                    'duration_hours': (end_dt - start_dt).total_seconds() / 3600
                },
                'data_points': len(filtered_data),
                'cpu': {
                    'avg': sum(cpu_values) / len(cpu_values),
                    'min': min(cpu_values),
                    'max': max(cpu_values),
                    'current': cpu_values[-1] if cpu_values else 0
                },
                'memory': {
                    'avg': sum(memory_values) / len(memory_values),
                    'min': min(memory_values),
                    'max': max(memory_values),
                    'current': memory_values[-1] if memory_values else 0
                },
                'disk': {
                    'avg': sum(disk_values) / len(disk_values),
                    'min': min(disk_values),
                    'max': max(disk_values),
                    'current': disk_values[-1] if disk_values else 0
                }
            }
            
            # 添加趋势分析
            if len(filtered_data) >= 2:
                stats['trends'] = self._analyze_trends(filtered_data)
            
            return stats
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def execute_control_action(self, action: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行系统控制操作"""
        try:
            if parameters is None:
                parameters = {}
            
            result = {'success': False, 'message': '', 'data': {}}
            
            if action == 'restart_service':
                service_name = parameters.get('service_name', '')
                if not service_name:
                    result['message'] = '服务名称不能为空'
                else:
                    # 模拟重启服务
                    result['success'] = True
                    result['message'] = f'服务 {service_name} 重启成功'
                    result['data'] = {'service_name': service_name, 'status': 'restarted'}
            
            elif action == 'clear_cache':
                cache_type = parameters.get('cache_type', 'all')
                # 模拟清理缓存
                result['success'] = True
                result['message'] = f'缓存清理成功: {cache_type}'
                result['data'] = {'cache_type': cache_type, 'cleared_size': '128MB'}
            
            elif action == 'update_config':
                config_section = parameters.get('section', '')
                config_data = parameters.get('config', {})
                if not config_section:
                    result['message'] = '配置节不能为空'
                else:
                    # 模拟更新配置
                    result['success'] = True
                    result['message'] = f'配置更新成功: {config_section}'
                    result['data'] = {'section': config_section, 'updated_keys': list(config_data.keys())}
            
            elif action == 'emergency_stop':
                # 模拟紧急停止
                result['success'] = True
                result['message'] = '紧急停止执行成功'
                result['data'] = {'stopped_services': ['trading', 'risk_control'], 'timestamp': datetime.now().isoformat()}
            
            else:
                result['message'] = f'不支持的操作: {action}'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f'执行控制操作失败: {str(e)}',
                'data': {}
            }
    
    def get_system_logs(self, level: str = 'INFO', start_time: str = '', end_time: str = '',
                       limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """获取系统日志"""
        try:
            # 模拟日志数据
            log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            log_sources = ['system', 'trading', 'risk_control', 'api', 'database']
            
            logs = []
            total_logs = 500  # 模拟总日志数
            
            # 生成模拟日志
            for i in range(min(limit, total_logs - offset)):
                log_level = random.choice(log_levels)
                if level != 'ALL' and log_level != level:
                    continue
                
                log_entry = {
                    'id': str(uuid.uuid4()),
                    'timestamp': (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat(),
                    'level': log_level,
                    'source': random.choice(log_sources),
                    'message': self._generate_log_message(log_level),
                    'details': {}
                }
                logs.append(log_entry)
            
            # 按时间倒序排序
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'logs': logs,
                'total': total_logs,
                'limit': limit,
                'offset': offset,
                'level': level,
                'start_time': start_time,
                'end_time': end_time
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'logs': [],
                'total': 0
            }
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self.system_config.copy()
    
    def update_system_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新系统配置"""
        try:
            updated_sections = []
            
            for section, values in config_data.items():
                if section in self.system_config:
                    self.system_config[section].update(values)
                    updated_sections.append(section)
                else:
                    self.system_config[section] = values
                    updated_sections.append(section)
            
            return {
                'success': True,
                'message': '配置更新成功',
                'updated_sections': updated_sections,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'配置更新失败: {str(e)}'
            }
    
    def create_backup(self, backup_type: str = 'full', description: str = '') -> Dict[str, Any]:
        """创建系统备份"""
        try:
            backup = BackupInfo(
                backup_id=str(uuid.uuid4()),
                backup_type=backup_type,
                description=description or f'{backup_type}备份',
                file_path=f'/backups/backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.tar.gz',
                file_size=random.randint(100, 1000) * 1024 * 1024,  # MB
                status='in_progress',
                created_at=datetime.now()
            )
            
            # 模拟备份过程
            import time
            time.sleep(1)  # 模拟备份时间
            
            backup.status = 'completed'
            backup.completed_at = datetime.now()
            
            self.backups.append(backup)
            
            return {
                'success': True,
                'message': '备份创建成功',
                'backup': backup.to_dict()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'备份创建失败: {str(e)}'
            }
    
    def list_backups(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取备份列表"""
        try:
            # 按创建时间倒序排序
            sorted_backups = sorted(self.backups, key=lambda x: x.created_at, reverse=True)
            
            # 分页
            total = len(sorted_backups)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            backups = sorted_backups[start_idx:end_idx]
            
            return {
                'backups': [backup.to_dict() for backup in backups],
                'total': total,
                'page': page,
                'size': size,
                'pages': (total + size - 1) // size
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'backups': [],
                'total': 0
            }
    
    def execute_maintenance(self, action: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行维护操作"""
        try:
            if parameters is None:
                parameters = {}
            
            task = MaintenanceTask(
                task_id=str(uuid.uuid4()),
                action=action,
                parameters=parameters,
                status='running',
                created_at=datetime.now()
            )
            
            self.maintenance_tasks[task.task_id] = task
            
            # 模拟不同的维护操作
            if action == 'cleanup_logs':
                # 模拟清理日志
                task.status = 'completed'
                task.completed_at = datetime.now()
                task.result = {'cleaned_files': 25, 'freed_space': '512MB'}
                message = '日志清理完成'
            
            elif action == 'optimize_database':
                # 模拟数据库优化
                task.status = 'completed'
                task.completed_at = datetime.now()
                task.result = {'optimized_tables': 15, 'time_saved': '2.3s'}
                message = '数据库优化完成'
            
            elif action == 'update_system':
                # 模拟系统更新
                task.status = 'completed'
                task.completed_at = datetime.now()
                task.result = {'updated_packages': 8, 'restart_required': False}
                message = '系统更新完成'
            
            else:
                task.status = 'failed'
                task.error = f'不支持的维护操作: {action}'
                message = f'维护操作失败: 不支持的操作 {action}'
            
            return {
                'success': task.status == 'completed',
                'message': message,
                'task': task.to_dict()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'维护操作失败: {str(e)}'
            }
    
    def get_system_alerts(self, level: str = '', status: str = '', start_time: str = '', 
                         end_time: str = '', page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取系统告警"""
        try:
            # 过滤告警
            filtered_alerts = []
            for alert in self.alerts.values():
                if level and alert.level.value != level.lower():
                    continue
                
                if status and alert.status.value != status.lower():
                    continue
                
                if start_time:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if alert.created_at < start_dt:
                        continue
                
                if end_time:
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    if alert.created_at > end_dt:
                        continue
                
                filtered_alerts.append(alert)
            
            # 按创建时间倒序排序
            filtered_alerts.sort(key=lambda x: x.created_at, reverse=True)
            
            # 分页
            total = len(filtered_alerts)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            alerts = filtered_alerts[start_idx:end_idx]
            
            return {
                'alerts': [alert.to_dict() for alert in alerts],
                'total': total,
                'page': page,
                'size': size,
                'pages': (total + size - 1) // size
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'alerts': [],
                'total': 0
            }
    
    def acknowledge_alert(self, alert_id: str, user_id: str, comment: str = '') -> Dict[str, Any]:
        """确认告警"""
        try:
            alert = self.alerts.get(alert_id)
            if not alert:
                return {
                    'success': False,
                    'message': '告警不存在'
                }
            
            if alert.status == AlertStatus.ACKNOWLEDGED:
                return {
                    'success': False,
                    'message': '告警已经被确认'
                }
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.now()
            alert.comment = comment
            
            return {
                'success': True,
                'message': '告警确认成功',
                'alert': alert.to_dict()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'确认告警失败: {str(e)}'
            }
    
    def _get_system_uptime(self) -> str:
        """获取系统运行时间"""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_hours = uptime_seconds / 3600
            
            if uptime_hours < 24:
                return f"{uptime_hours:.1f} 小时"
            else:
                uptime_days = uptime_hours / 24
                return f"{uptime_days:.1f} 天"
        except:
            return "未知"
    
    def _get_services_status(self) -> Dict[str, str]:
        """获取服务状态（模拟）"""
        return {
            'trading_engine': 'running',
            'risk_control': 'running',
            'data_service': 'running',
            'api_gateway': 'running',
            'database': 'running',
            'redis': 'running',
            'message_queue': 'running'
        }
    
    def _generate_performance_history(self):
        """生成性能历史数据"""
        now = datetime.now()
        
        for i in range(1440):  # 24小时的分钟数据
            timestamp = now - timedelta(minutes=i)
            
            # 模拟性能数据
            data_point = {
                'timestamp': timestamp.isoformat(),
                'cpu_percent': random.uniform(10, 80),
                'memory_percent': random.uniform(30, 70),
                'disk_percent': random.uniform(40, 60),
                'network_in': random.randint(1000, 10000),
                'network_out': random.randint(500, 5000)
            }
            
            self.performance_history.append(data_point)
        
        # 按时间排序
        self.performance_history.sort(key=lambda x: x['timestamp'])
    
    def _process_cpu_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理CPU指标"""
        cpu_values = [d['cpu_percent'] for d in data]
        
        return {
            'current': cpu_values[-1] if cpu_values else 0,
            'average': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            'min': min(cpu_values) if cpu_values else 0,
            'max': max(cpu_values) if cpu_values else 0,
            'timeline': [{'timestamp': d['timestamp'], 'value': d['cpu_percent']} for d in data[-50:]]
        }
    
    def _process_memory_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理内存指标"""
        memory_values = [d['memory_percent'] for d in data]
        
        return {
            'current': memory_values[-1] if memory_values else 0,
            'average': sum(memory_values) / len(memory_values) if memory_values else 0,
            'min': min(memory_values) if memory_values else 0,
            'max': max(memory_values) if memory_values else 0,
            'timeline': [{'timestamp': d['timestamp'], 'value': d['memory_percent']} for d in data[-50:]]
        }
    
    def _process_disk_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理磁盘指标"""
        disk_values = [d['disk_percent'] for d in data]
        
        return {
            'current': disk_values[-1] if disk_values else 0,
            'average': sum(disk_values) / len(disk_values) if disk_values else 0,
            'min': min(disk_values) if disk_values else 0,
            'max': max(disk_values) if disk_values else 0,
            'timeline': [{'timestamp': d['timestamp'], 'value': d['disk_percent']} for d in data[-50:]]
        }
    
    def _process_network_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理网络指标"""
        network_in = [d['network_in'] for d in data]
        network_out = [d['network_out'] for d in data]
        
        return {
            'current_in': network_in[-1] if network_in else 0,
            'current_out': network_out[-1] if network_out else 0,
            'avg_in': sum(network_in) / len(network_in) if network_in else 0,
            'avg_out': sum(network_out) / len(network_out) if network_out else 0,
            'timeline': [
                {
                    'timestamp': d['timestamp'], 
                    'in': d['network_in'], 
                    'out': d['network_out']
                } for d in data[-50:]
            ]
        }
    
    def _analyze_trends(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """分析趋势"""
        if len(data) < 2:
            return {}
        
        # 简单的趋势分析
        first_half = data[:len(data)//2]
        second_half = data[len(data)//2:]
        
        cpu_trend = 'stable'
        memory_trend = 'stable'
        
        if len(first_half) > 0 and len(second_half) > 0:
            cpu_first = sum(d['cpu_percent'] for d in first_half) / len(first_half)
            cpu_second = sum(d['cpu_percent'] for d in second_half) / len(second_half)
            
            if cpu_second > cpu_first * 1.1:
                cpu_trend = 'increasing'
            elif cpu_second < cpu_first * 0.9:
                cpu_trend = 'decreasing'
            
            memory_first = sum(d['memory_percent'] for d in first_half) / len(first_half)
            memory_second = sum(d['memory_percent'] for d in second_half) / len(second_half)
            
            if memory_second > memory_first * 1.1:
                memory_trend = 'increasing'
            elif memory_second < memory_first * 0.9:
                memory_trend = 'decreasing'
        
        return {
            'cpu': cpu_trend,
            'memory': memory_trend
        }
    
    def _generate_log_message(self, level: str) -> str:
        """生成日志消息"""
        messages = {
            'DEBUG': [
                '数据库查询执行完成',
                '缓存命中率: 85%',
                '用户会话创建成功',
                'API请求处理完成'
            ],
            'INFO': [
                '系统启动完成',
                '定时任务执行成功',
                '用户登录成功',
                '数据同步完成'
            ],
            'WARNING': [
                'CPU使用率较高: 85%',
                '内存使用率达到警告阈值',
                '数据库连接池接近满载',
                'API响应时间较慢'
            ],
            'ERROR': [
                '数据库连接失败',
                'API请求处理异常',
                '文件读取错误',
                '网络连接超时'
            ],
            'CRITICAL': [
                '系统内存不足',
                '数据库服务不可用',
                '磁盘空间严重不足',
                '服务器响应异常'
            ]
        }
        
        return random.choice(messages.get(level, ['未知日志消息']))