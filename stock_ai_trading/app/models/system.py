"""
系统相关数据模型

包括系统状态、健康检查、告警、备份等数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"           # 信息
    WARNING = "warning"     # 警告
    ERROR = "error"         # 错误
    CRITICAL = "critical"   # 严重


class AlertStatus(Enum):
    """告警状态"""
    ACTIVE = "active"               # 活跃
    ACKNOWLEDGED = "acknowledged"   # 已确认
    RESOLVED = "resolved"          # 已解决
    CLOSED = "closed"              # 已关闭


class SystemHealthStatus(Enum):
    """系统健康状态"""
    HEALTHY = "healthy"     # 健康
    WARNING = "warning"     # 警告
    CRITICAL = "critical"   # 严重
    ERROR = "error"         # 错误


@dataclass
class SystemStatus:
    """系统状态"""
    status: str
    uptime: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_in: int
    network_out: int
    active_connections: int
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'status': self.status,
            'uptime': self.uptime,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_in': self.network_in,
            'network_out': self.network_out,
            'active_connections': self.active_connections,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class SystemHealth:
    """系统健康状态"""
    status: SystemHealthStatus
    checks: List[Dict[str, Any]] = field(default_factory=list)
    uptime: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'status': self.status.value,
            'checks': self.checks,
            'uptime': self.uptime,
            'timestamp': self.timestamp.isoformat()
        }
    
    @property
    def is_healthy(self) -> bool:
        """检查是否健康"""
        return self.status == SystemHealthStatus.HEALTHY
    
    def add_check(self, name: str, status: str, value: str, threshold: str, message: str):
        """添加健康检查"""
        self.checks.append({
            'name': name,
            'status': status,
            'value': value,
            'threshold': threshold,
            'message': message
        })


@dataclass
class SystemMetrics:
    """系统性能指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_in: int
    network_out: int
    active_processes: int
    load_average: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'disk_percent': self.disk_percent,
            'network_in': self.network_in,
            'network_out': self.network_out,
            'active_processes': self.active_processes,
            'load_average': self.load_average
        }


@dataclass
class SystemAlert:
    """系统告警"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    category: str
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    comment: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'alert_id': self.alert_id,
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'source': self.source,
            'category': self.category,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'comment': self.comment,
            'metadata': self.metadata
        }
    
    @property
    def is_active(self) -> bool:
        """检查告警是否活跃"""
        return self.status == AlertStatus.ACTIVE
    
    @property
    def is_critical(self) -> bool:
        """检查是否为严重告警"""
        return self.level == AlertLevel.CRITICAL
    
    def acknowledge(self, user_id: str, comment: str = ""):
        """确认告警"""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = user_id
        self.comment = comment
    
    def resolve(self, user_id: str, comment: str = ""):
        """解决告警"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.resolved_by = user_id
        if comment:
            self.comment = comment


@dataclass
class BackupInfo:
    """备份信息"""
    backup_id: str
    backup_type: str  # full, incremental, differential
    description: str
    file_path: str
    file_size: int
    status: str  # in_progress, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'backup_id': self.backup_id,
            'backup_type': self.backup_type,
            'description': self.description,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_mb': round(self.file_size / (1024 * 1024), 2),
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self._get_duration(),
            'error_message': self.error_message,
            'metadata': self.metadata
        }
    
    def _get_duration(self) -> Optional[str]:
        """获取备份持续时间"""
        if not self.completed_at:
            return None
        
        duration = self.completed_at - self.created_at
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}小时{minutes}分"
    
    @property
    def is_completed(self) -> bool:
        """检查备份是否完成"""
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        """检查备份是否失败"""
        return self.status == 'failed'


@dataclass
class MaintenanceTask:
    """维护任务"""
    task_id: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'action': self.action,
            'parameters': self.parameters,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self._get_duration(),
            'result': self.result,
            'error': self.error
        }
    
    def _get_duration(self) -> Optional[str]:
        """获取任务持续时间"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now()
        duration = end_time - self.started_at
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}小时{minutes}分"
    
    def start(self):
        """开始任务"""
        self.status = "running"
        self.started_at = datetime.now()
    
    def complete(self, result: Dict[str, Any] = None):
        """完成任务"""
        self.status = "completed"
        self.completed_at = datetime.now()
        if result:
            self.result = result
    
    def fail(self, error: str):
        """任务失败"""
        self.status = "failed"
        self.completed_at = datetime.now()
        self.error = error


@dataclass
class SystemConfig:
    """系统配置"""
    section: str
    key: str
    value: Any
    description: str = ""
    data_type: str = "string"  # string, int, float, bool, json
    is_sensitive: bool = False
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'section': self.section,
            'key': self.key,
            'value': self.value if not self.is_sensitive else "***",
            'description': self.description,
            'data_type': self.data_type,
            'is_sensitive': self.is_sensitive,
            'updated_at': self.updated_at.isoformat(),
            'updated_by': self.updated_by
        }
    
    def update_value(self, value: Any, user_id: str):
        """更新配置值"""
        self.value = value
        self.updated_at = datetime.now()
        self.updated_by = user_id


@dataclass
class SystemLog:
    """系统日志"""
    log_id: str
    timestamp: datetime
    level: str
    source: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'log_id': self.log_id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'source': self.source,
            'message': self.message,
            'details': self.details,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address
        }
    
    @property
    def is_error(self) -> bool:
        """检查是否为错误日志"""
        return self.level in ['ERROR', 'CRITICAL']
    
    @property
    def is_warning(self) -> bool:
        """检查是否为警告日志"""
        return self.level == 'WARNING'


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    snapshot_id: str
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_in_rate: float
    network_out_rate: float
    active_connections: int
    response_time: float
    throughput: float
    error_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'snapshot_id': self.snapshot_id,
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_in_rate': self.network_in_rate,
            'network_out_rate': self.network_out_rate,
            'active_connections': self.active_connections,
            'response_time': self.response_time,
            'throughput': self.throughput,
            'error_rate': self.error_rate
        }
    
    @property
    def health_score(self) -> float:
        """计算健康评分（0-100）"""
        # 简单的健康评分算法
        cpu_score = max(0, 100 - self.cpu_usage)
        memory_score = max(0, 100 - self.memory_usage)
        disk_score = max(0, 100 - self.disk_usage)
        error_score = max(0, 100 - self.error_rate * 100)
        
        return (cpu_score + memory_score + disk_score + error_score) / 4