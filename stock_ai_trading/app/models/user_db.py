"""
基于数据库的用户模型和管理器
"""

import hashlib
import secrets
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, BigInteger, String, Enum, DECIMAL, TIMESTAMP, text
from sqlalchemy.orm import Session
import pymysql
import logging

from ..core.database import Base, get_db, DATABASE_URL

logger = logging.getLogger(__name__)


class User(Base):
    """用户数据库模型"""
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, comment='邮箱')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    full_name = Column(String(100), comment='真实姓名')
    phone = Column(String(20), comment='手机号')
    status = Column(Enum('active', 'inactive', 'suspended'), default='active', comment='用户状态')
    role = Column(Enum('admin', 'trader', 'viewer'), default='trader', comment='用户角色')
    initial_capital = Column(DECIMAL(15, 2), default=0.00, comment='初始资金')
    current_capital = Column(DECIMAL(15, 2), default=0.00, comment='当前资金')
    risk_level = Column(Enum('conservative', 'moderate', 'aggressive'), default='moderate', comment='风险偏好')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')
    last_login_at = Column(TIMESTAMP, nullable=True, comment='最后登录时间')


class DatabaseUserManager:
    """基于数据库的用户管理器"""
    
    def __init__(self):
        self.tokens = {}  # 临时存储token，实际应用中应该使用Redis
        self._ensure_admin_user()
    
    def _get_db_connection(self):
        """获取数据库连接"""
        try:
            # 解析DATABASE_URL
            import re
            match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
            if not match:
                raise ValueError("Invalid DATABASE_URL format")
            
            user, password, host, port, database = match.groups()
            
            connection = pymysql.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return salt + password_hash.hex()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            if len(password_hash) < 32:
                return False
            
            salt = password_hash[:32]
            stored_hash = password_hash[32:]
            
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return computed_hash.hex() == stored_hash
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False
    
    def _ensure_admin_user(self):
        """确保存在admin用户"""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # 检查admin用户是否存在
                cursor.execute("SELECT id FROM users WHERE email = %s", ('admin@example.com',))
                admin_user = cursor.fetchone()
                
                if not admin_user:
                    # 创建admin用户
                    password_hash = self._hash_password('admin123456')
                    
                    insert_sql = """
                    INSERT INTO users (username, email, password_hash, full_name, role, 
                                     initial_capital, current_capital, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_sql, (
                        'admin',
                        'admin@example.com',
                        password_hash,
                        '系统管理员',
                        'admin',
                        1000000.00,
                        1000000.00,
                        'active'
                    ))
                    connection.commit()
                    logger.info("已创建默认admin用户")
                
            connection.close()
        except Exception as e:
            logger.error(f"确保admin用户失败: {e}")
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
            connection.close()
            return user
        except Exception as e:
            logger.error(f"根据邮箱获取用户失败: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
            connection.close()
            return user
        except Exception as e:
            logger.error(f"根据用户名获取用户失败: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据用户ID获取用户"""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
            connection.close()
            return user
        except Exception as e:
            logger.error(f"根据用户ID获取用户失败: {e}")
            return None
    
    def verify_password(self, user: Dict[str, Any], password: str) -> bool:
        """验证密码"""
        return self._verify_password(password, user['password_hash'])
    
    def create_user(self, username: str, email: str, password: str, **kwargs) -> Optional[Dict[str, Any]]:
        """创建用户"""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # 检查用户名和邮箱是否已存在
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    return None
                
                password_hash = self._hash_password(password)
                
                insert_sql = """
                INSERT INTO users (username, email, password_hash, full_name, role, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_sql, (
                    username,
                    email,
                    password_hash,
                    kwargs.get('full_name', ''),
                    kwargs.get('role', 'trader'),
                    'active'
                ))
                
                user_id = cursor.lastrowid
                connection.commit()
                
                # 获取创建的用户
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
            connection.close()
            return user
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return None
    
    def update_last_login(self, user_id: int):
        """更新最后登录时间"""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET last_login_at = NOW() WHERE id = %s",
                    (user_id,)
                )
                connection.commit()
            connection.close()
        except Exception as e:
            logger.error(f"更新最后登录时间失败: {e}")
    
    def create_token(self, user: Dict[str, Any]) -> str:
        """创建访问令牌"""
        from ..utils.jwt_utils import jwt_manager
        
        # 使用JWT创建token
        token = jwt_manager.create_access_token(
            user_id=str(user["id"]),
            username=user["username"],
            permissions=self._get_user_permissions(user),
            email=user["email"],
            role=user["role"]
        )
        
        # 同时在内存中存储token信息（用于快速验证）
        self.tokens[token] = {
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "created_at": datetime.now().isoformat(),
            "expires_at": datetime.now().isoformat()  # JWT本身包含过期时间
        }
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证访问令牌"""
        from ..utils.jwt_utils import jwt_manager
        
        try:
            # 首先尝试JWT验证
            payload = jwt_manager.verify_access_token(token)
            if payload:
                user_id = payload.get('sub')
                if user_id:
                    # 从数据库获取最新用户信息
                    user = self.get_user_by_id(int(user_id))
                    return user
            
            # 如果JWT验证失败，尝试内存token验证（向后兼容）
            token_info = self.tokens.get(token)
            if token_info:
                user = self.get_user_by_id(token_info["user_id"])
                return user
                
        except Exception as e:
            logger.error(f"Token验证失败: {e}")
        
        return None
    
    def _get_user_permissions(self, user: Dict[str, Any]) -> list:
        """根据用户角色获取权限列表"""
        role_permissions = {
            'admin': [
                'user:read', 'user:write', 'user:delete',
                'trade:read', 'trade:write', 'trade:delete',
                'strategy:read', 'strategy:write', 'strategy:delete',
                'risk:read', 'risk:write',
                'system:read', 'system:write', 'system:control',
                'data:read'
            ],
            'trader': [
                'trade:read', 'trade:write',
                'strategy:read', 'strategy:write',
                'risk:read',
                'data:read',
                'system:read'
            ],
            'viewer': [
                'trade:read',
                'strategy:read',
                'risk:read',
                'data:read',
                'system:read'
            ]
        }
        
        return role_permissions.get(user.get('role', 'viewer'), [])
    
    def revoke_token(self, token: str) -> bool:
        """撤销访问令牌"""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False


# 全局数据库用户管理器实例
db_user_manager = DatabaseUserManager()