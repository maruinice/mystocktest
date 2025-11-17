"""
JWT工具类

用于生成和验证JWT令牌
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
import secrets
import os


@dataclass
class JWTConfig:
    """JWT配置"""
    secret_key: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    issuer: str = "stock_ai_trading"
    audience: str = "api_users"


class JWTManager:
    """JWT管理器"""
    
    def __init__(self, config: Optional[JWTConfig] = None):
        self.config = config or JWTConfig()
    
    def create_access_token(self, user_id: str, username: str, 
                          permissions: list, **extra_claims) -> str:
        """创建访问令牌"""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.config.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,  # subject (用户ID)
            "username": username,
            "permissions": permissions,
            "iat": now,  # issued at
            "exp": expire,  # expiration time
            "iss": self.config.issuer,  # issuer
            "aud": self.config.audience,  # audience
            "type": "access"
        }
        
        # 添加额外声明
        payload.update(extra_claims)
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def create_refresh_token(self, user_id: str, username: str) -> str:
        """创建刷新令牌"""
        now = datetime.utcnow()
        expire = now + timedelta(days=self.config.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "username": username,
            "iat": now,
            "exp": expire,
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise JWTError("令牌已过期")
        except jwt.InvalidTokenError as e:
            raise JWTError(f"无效令牌: {str(e)}")
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证访问令牌"""
        payload = self.verify_token(token)
        if payload and payload.get("type") == "access":
            return payload
        raise JWTError("无效的访问令牌")
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证刷新令牌"""
        payload = self.verify_token(token)
        if payload and payload.get("type") == "refresh":
            return payload
        raise JWTError("无效的刷新令牌")
    
    def refresh_access_token(self, refresh_token: str, user_permissions: list) -> str:
        """使用刷新令牌生成新的访问令牌"""
        payload = self.verify_refresh_token(refresh_token)
        
        return self.create_access_token(
            user_id=payload["sub"],
            username=payload["username"],
            permissions=user_permissions
        )
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """不验证签名解码令牌（用于调试）"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """获取令牌过期时间"""
        payload = self.decode_token_without_verification(token)
        if payload and "exp" in payload:
            return datetime.utcfromtimestamp(payload["exp"])
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """检查令牌是否过期"""
        expiry = self.get_token_expiry(token)
        if expiry:
            return datetime.utcnow() > expiry
        return True


class JWTError(Exception):
    """JWT相关错误"""
    pass


class TokenBlacklist:
    """令牌黑名单管理"""
    
    def __init__(self):
        self.blacklisted_tokens = set()
        self.blacklisted_users = set()
    
    def add_token(self, token: str):
        """添加令牌到黑名单"""
        self.blacklisted_tokens.add(token)
    
    def add_user(self, user_id: str):
        """添加用户到黑名单（使该用户所有令牌失效）"""
        self.blacklisted_users.add(user_id)
    
    def remove_user(self, user_id: str):
        """从黑名单移除用户"""
        self.blacklisted_users.discard(user_id)
    
    def is_token_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        return token in self.blacklisted_tokens
    
    def is_user_blacklisted(self, user_id: str) -> bool:
        """检查用户是否在黑名单中"""
        return user_id in self.blacklisted_users
    
    def is_valid_token(self, token: str, jwt_manager: JWTManager) -> bool:
        """检查令牌是否有效（未在黑名单且未过期）"""
        if self.is_token_blacklisted(token):
            return False
        
        try:
            payload = jwt_manager.verify_token(token)
            user_id = payload.get("sub")
            return not self.is_user_blacklisted(user_id)
        except JWTError:
            return False
    
    def cleanup_expired_tokens(self, jwt_manager: JWTManager):
        """清理过期的令牌"""
        expired_tokens = []
        for token in self.blacklisted_tokens:
            if jwt_manager.is_token_expired(token):
                expired_tokens.append(token)
        
        for token in expired_tokens:
            self.blacklisted_tokens.remove(token)


# 全局实例
jwt_manager = JWTManager()
token_blacklist = TokenBlacklist()


def create_token_pair(user_id: str, username: str, permissions: list) -> Dict[str, str]:
    """创建令牌对（访问令牌和刷新令牌）"""
    access_token = jwt_manager.create_access_token(user_id, username, permissions)
    refresh_token = jwt_manager.create_refresh_token(user_id, username)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": jwt_manager.config.access_token_expire_minutes * 60
    }


def verify_and_decode_token(token: str) -> Dict[str, Any]:
    """验证并解码令牌"""
    if token_blacklist.is_token_blacklisted(token):
        raise JWTError("令牌已被撤销")
    
    payload = jwt_manager.verify_access_token(token)
    user_id = payload.get("sub")
    
    if token_blacklist.is_user_blacklisted(user_id):
        raise JWTError("用户已被禁用")
    
    return payload


def logout_user(token: str):
    """用户登出（将令牌加入黑名单）"""
    token_blacklist.add_token(token)


def revoke_user_tokens(user_id: str):
    """撤销用户所有令牌"""
    token_blacklist.add_user(user_id)