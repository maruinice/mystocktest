"""
用户模型

定义用户基本信息和权限管理
"""

from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
import hashlib
import secrets


class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = "admin"          # 管理员
    TRADER = "trader"        # 交易员
    VIEWER = "viewer"        # 观察者
    ANALYST = "analyst"      # 分析师


class UserStatus(Enum):
    """用户状态枚举"""
    ACTIVE = "active"        # 活跃
    INACTIVE = "inactive"    # 非活跃
    SUSPENDED = "suspended"  # 暂停
    DELETED = "deleted"      # 已删除


@dataclass
class User:
    """用户模型"""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0
    failed_login_count: int = 0
    last_failed_login: Optional[datetime] = None
    api_key: Optional[str] = None
    permissions: List[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.permissions is None:
            self.permissions = self._get_default_permissions()
    
    def _get_default_permissions(self) -> List[str]:
        """根据角色获取默认权限"""
        permission_map = {
            UserRole.ADMIN: [
                "user:read", "user:write", "user:delete",
                "trade:read", "trade:write", "trade:delete",
                "strategy:read", "strategy:write", "strategy:delete",
                "risk:read", "risk:write",
                "system:read", "system:write", "system:control",
                "data:read"
            ],
            UserRole.TRADER: [
                "trade:read", "trade:write",
                "strategy:read", "strategy:write",
                "risk:read",
                "data:read",
                "system:read"
            ],
            UserRole.ANALYST: [
                "strategy:read", "strategy:write",
                "risk:read",
                "data:read",
                "system:read"
            ],
            UserRole.VIEWER: [
                "trade:read",
                "strategy:read",
                "risk:read",
                "data:read",
                "system:read"
            ]
        }
        return permission_map.get(self.role, [])
    
    def has_permission(self, permission: str) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.permissions
    
    def is_active(self) -> bool:
        """检查用户是否活跃"""
        return self.status == UserStatus.ACTIVE
    
    def can_login(self) -> bool:
        """检查用户是否可以登录"""
        return self.status in [UserStatus.ACTIVE, UserStatus.INACTIVE]
    
    def update_login_info(self, success: bool = True):
        """更新登录信息"""
        now = datetime.now()
        if success:
            self.last_login = now
            self.login_count += 1
            self.failed_login_count = 0  # 重置失败次数
            if self.status == UserStatus.INACTIVE:
                self.status = UserStatus.ACTIVE
        else:
            self.failed_login_count += 1
            self.last_failed_login = now
    
    def generate_api_key(self) -> str:
        """生成API密钥"""
        self.api_key = secrets.token_urlsafe(32)
        return self.api_key
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """转换为字典"""
        data = {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "permissions": self.permissions
        }
        
        if include_sensitive:
            data.update({
                "password_hash": self.password_hash,
                "failed_login_count": self.failed_login_count,
                "last_failed_login": self.last_failed_login.isoformat() if self.last_failed_login else None,
                "api_key": self.api_key
            })
        
        return data


class UserManager:
    """用户管理器"""
    
    def __init__(self):
        self.users = {}  # 实际应用中应该使用数据库
        self._create_default_admin()
    
    def _create_default_admin(self):
        """创建默认管理员账户"""
        admin_user = User(
            user_id="admin_001",
            username="admin",
            email="admin@example.com",
            password_hash=self.hash_password("admin123"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        admin_user.generate_api_key()
        self.users[admin_user.user_id] = admin_user
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash_check.hex() == stored_hash
        except ValueError:
            return False
    
    def create_user(self, username: str, email: str, password: str, 
                   role: UserRole = UserRole.VIEWER) -> User:
        """创建用户"""
        # 检查用户名和邮箱是否已存在
        for user in self.users.values():
            if user.username == username:
                raise ValueError(f"用户名 {username} 已存在")
            if user.email == email:
                raise ValueError(f"邮箱 {email} 已存在")
        
        user_id = f"user_{len(self.users) + 1:03d}"
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            role=role,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        user.generate_api_key()
        
        self.users[user_id] = user
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not user.can_login():
            return None
        
        if self.verify_password(password, user.password_hash):
            user.update_login_info(success=True)
            return user
        else:
            user.update_login_info(success=False)
            return None
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """更新用户信息"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # 更新允许的字段
        allowed_fields = ['email', 'role', 'status', 'permissions']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        user.updated_at = datetime.now()
        return True
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        if not self.verify_password(old_password, user.password_hash):
            return False
        
        user.password_hash = self.hash_password(new_password)
        user.updated_at = datetime.now()
        return True
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户（软删除）"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.status = UserStatus.DELETED
        user.updated_at = datetime.now()
        return True
    
    def list_users(self, include_deleted: bool = False) -> List[User]:
        """获取用户列表"""
        users = list(self.users.values())
        if not include_deleted:
            users = [user for user in users if user.status != UserStatus.DELETED]
        return users


# 全局用户管理器实例
user_manager = UserManager()