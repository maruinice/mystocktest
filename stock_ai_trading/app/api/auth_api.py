# -*- coding: utf-8 -*-
"""
认证API模块
提供用户认证、授权相关的REST API接口
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any
from datetime import datetime
import re
import logging

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

logger = logging.getLogger(__name__)

class AuthValidator:
    """认证验证器"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """验证密码强度"""
        if len(password) < 8:
            return False
        
        # 检查是否包含大小写字母、数字和特殊字符
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """验证用户名格式"""
        if len(username) < 3 or len(username) > 20:
            return False
        
        # 只允许字母、数字和下划线
        pattern = r'^[a-zA-Z0-9_]+$'
        return re.match(pattern, username) is not None

class MockUserManager:
    """模拟用户管理器"""
    
    def __init__(self):
        self.users = {}
        self.tokens = {}
        self.next_user_id = 1
        # 创建默认admin用户
        self._create_default_admin()
    
    def _create_default_admin(self):
        """创建默认admin用户"""
        admin_user = {
            "user_id": "1",
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123456",  # 实际应用中应该加密存储
            "role": "admin",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.users["1"] = admin_user
        self.next_user_id = 2
    
    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """创建用户"""
        user_id = str(self.next_user_id)
        self.next_user_id += 1
        
        user = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password": password,  # 实际应用中应该加密存储
            "role": "user",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.users[user_id] = user
        return user
    
    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """根据邮箱获取用户"""
        for user in self.users.values():
            if user["email"] == email:
                return user
        return None
    
    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """根据用户名获取用户"""
        for user in self.users.values():
            if user["username"] == username:
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """根据用户ID获取用户"""
        return self.users.get(user_id)
    
    def verify_password(self, user: Dict[str, Any], password: str) -> bool:
        """验证密码"""
        return user["password"] == password  # 实际应用中应该使用哈希验证
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """更新用户信息"""
        if user_id in self.users:
            self.users[user_id].update(updates)
            self.users[user_id]["updated_at"] = datetime.now().isoformat()
            return True
        return False
    
    def create_token(self, user: Dict[str, Any]) -> str:
        """创建访问令牌"""
        import uuid
        token = str(uuid.uuid4())
        self.tokens[token] = {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "created_at": datetime.now().isoformat(),
            "expires_at": datetime.now().isoformat()  # 实际应用中应该设置过期时间
        }
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证访问令牌"""
        token_info = self.tokens.get(token)
        if token_info:
            user = self.get_user_by_id(token_info["user_id"])
            return user
        return None
    
    def revoke_token(self, token: str) -> bool:
        """撤销访问令牌"""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False

# 导入数据库用户管理器
from ..models.user_db import db_user_manager

# 使用数据库用户管理器替代内存管理器
user_manager = db_user_manager

def require_auth(f):
    """认证装饰器"""
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "未提供有效的认证令牌"}), 401
        
        token = auth_header.split(' ')[1]
        user = user_manager.verify_token(token)
        if not user:
            return jsonify({"error": "无效的认证令牌"}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    wrapper.__name__ = f.__name__
    return wrapper

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "error": f"缺少必需字段: {field}"
                }), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        
        # 验证输入格式
        if not AuthValidator.validate_username(username):
            return jsonify({
                "success": False,
                "error": "用户名格式不正确（3-20个字符，只允许字母、数字和下划线）"
            }), 400
        
        if not AuthValidator.validate_email(email):
            return jsonify({
                "success": False,
                "error": "邮箱格式不正确"
            }), 400
        
        if not AuthValidator.validate_password(password):
            return jsonify({
                "success": False,
                "error": "密码强度不够（至少8位，包含大小写字母、数字和特殊字符）"
            }), 400
        
        # 检查用户名和邮箱是否已存在
        if user_manager.get_user_by_username(username):
            return jsonify({
                "success": False,
                "error": "用户名已存在"
            }), 409
        
        if user_manager.get_user_by_email(email):
            return jsonify({
                "success": False,
                "error": "邮箱已被注册"
            }), 409
        
        # 创建用户
        user = user_manager.create_user(username, email, password, full_name=full_name)
        
        if not user:
            return jsonify({
                "success": False,
                "error": "用户创建失败，用户名或邮箱可能已存在"
            }), 409
        
        # 创建访问令牌
        token = user_manager.create_token(user)
        
        return jsonify({
            "success": True,
            "message": "注册成功",
            "data": {
                "user": {
                    "user_id": str(user["id"]),
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "status": user["status"]
                },
                "token": token
            }
        }), 201
        
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "注册失败，请稍后重试"
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        if not data.get('email') or not data.get('password'):
            return jsonify({
                "success": False,
                "error": "邮箱和密码不能为空"
            }), 400
        
        email = data['email']
        password = data['password']
        
        # 查找用户
        user = user_manager.get_user_by_email(email)
        if not user:
            return jsonify({
                "success": False,
                "error": "邮箱或密码错误"
            }), 401
        
        # 验证密码
        if not user_manager.verify_password(user, password):
            return jsonify({
                "success": False,
                "error": "邮箱或密码错误"
            }), 401
        
        # 检查用户状态
        if user["status"] != "active":
            return jsonify({
                "success": False,
                "error": "账户已被禁用"
            }), 403
        
        # 更新最后登录时间
        user_manager.update_last_login(user["id"])
        
        # 创建访问令牌
        token = user_manager.create_token(user)
        
        return jsonify({
            "success": True,
            "message": "登录成功",
            "data": {
                "user": {
                    "user_id": str(user["id"]),
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "status": user["status"]
                },
                "token": token
            }
        })
        
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "登录失败，请稍后重试"
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """用户登出"""
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        
        # 撤销令牌
        user_manager.revoke_token(token)
        
        return jsonify({
            "success": True,
            "message": "登出成功"
        })
        
    except Exception as e:
        logger.error(f"登出失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "登出失败，请稍后重试"
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """获取用户资料"""
    try:
        user = g.current_user
        
        return jsonify({
            "success": True,
            "data": {
                "user_id": str(user["id"]),
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "status": user["status"],
                "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
                "updated_at": user["updated_at"].isoformat() if user.get("updated_at") else None
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户资料失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取用户资料失败"
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """更新用户资料"""
    try:
        data = request.get_json()
        user = g.current_user
        
        # 允许更新的字段
        allowed_fields = ['username', 'email']
        updates = {}
        
        for field in allowed_fields:
            if field in data:
                value = data[field]
                
                # 验证字段格式
                if field == 'username' and not AuthValidator.validate_username(value):
                    return jsonify({
                        "success": False,
                        "error": "用户名格式不正确"
                    }), 400
                
                if field == 'email' and not AuthValidator.validate_email(value):
                    return jsonify({
                        "success": False,
                        "error": "邮箱格式不正确"
                    }), 400
                
                # 检查是否与其他用户冲突
                if field == 'username':
                    existing_user = user_manager.get_user_by_username(value)
                    if existing_user and existing_user["user_id"] != user["user_id"]:
                        return jsonify({
                            "success": False,
                            "error": "用户名已存在"
                        }), 409
                
                if field == 'email':
                    existing_user = user_manager.get_user_by_email(value)
                    if existing_user and existing_user["user_id"] != user["user_id"]:
                        return jsonify({
                            "success": False,
                            "error": "邮箱已被使用"
                        }), 409
                
                updates[field] = value
        
        if not updates:
            return jsonify({
                "success": False,
                "error": "没有提供要更新的字段"
            }), 400
        
        # 更新用户信息
        user_manager.update_user(user["user_id"], updates)
        
        # 获取更新后的用户信息
        updated_user = user_manager.get_user_by_id(user["user_id"])
        
        return jsonify({
            "success": True,
            "message": "用户资料更新成功",
            "data": {
                "user_id": updated_user["user_id"],
                "username": updated_user["username"],
                "email": updated_user["email"],
                "role": updated_user["role"],
                "status": updated_user["status"],
                "updated_at": updated_user["updated_at"]
            }
        })
        
    except Exception as e:
        logger.error(f"更新用户资料失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "更新用户资料失败"
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """修改密码"""
    try:
        data = request.get_json()
        user = g.current_user
        
        # 验证必需字段
        if not data.get('old_password') or not data.get('new_password'):
            return jsonify({
                "success": False,
                "error": "旧密码和新密码不能为空"
            }), 400
        
        old_password = data['old_password']
        new_password = data['new_password']
        
        # 验证旧密码
        if not user_manager.verify_password(user, old_password):
            return jsonify({
                "success": False,
                "error": "旧密码错误"
            }), 401
        
        # 验证新密码强度
        if not AuthValidator.validate_password(new_password):
            return jsonify({
                "success": False,
                "error": "新密码强度不够（至少8位，包含大小写字母、数字和特殊字符）"
            }), 400
        
        # 更新密码
        user_manager.update_user(user["user_id"], {"password": new_password})
        
        return jsonify({
            "success": True,
            "message": "密码修改成功"
        })
        
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "修改密码失败"
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@require_auth
def refresh_token():
    """刷新访问令牌"""
    try:
        # 获取当前用户信息
        user = user_manager.get_user_by_id(g.current_user['id'])
        if not user:
            return jsonify({
                "success": False,
                "error": "用户不存在"
            }), 404
        
        # 生成新的token
        new_token = user_manager.create_token(user)
        
        return jsonify({
            "success": True,
            "message": "令牌刷新成功",
            "data": {
                "token": new_token
            }
        })
        
    except Exception as e:
        logger.error(f"令牌刷新失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "令牌刷新失败"
        }), 500


@auth_bp.route('/user', methods=['GET'])
@require_auth
def get_user():
    """获取用户信息（别名接口）"""
    return get_profile()


@auth_bp.route('/user', methods=['PUT'])
@require_auth
def update_user():
    """更新用户信息（别名接口）"""
    return update_profile()


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """忘记密码"""
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({
                "success": False,
                "error": "缺少邮箱参数"
            }), 400
        
        email = data['email']
        user = user_manager.get_user_by_email(email)
        
        if not user:
            # 为了安全，即使用户不存在也返回成功
            return jsonify({
                "success": True,
                "message": "如果该邮箱存在，重置链接已发送"
            })
        
        # 这里应该发送重置密码邮件，暂时返回成功
        return jsonify({
            "success": True,
            "message": "重置密码链接已发送到您的邮箱"
        })
        
    except Exception as e:
        logger.error(f"忘记密码处理失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "处理失败"
        }), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['token', 'password', 'confirmPassword']):
            return jsonify({
                "success": False,
                "error": "缺少必要参数"
            }), 400
        
        if data['password'] != data['confirmPassword']:
            return jsonify({
                "success": False,
                "error": "两次输入的密码不一致"
            }), 400
        
        # 这里应该验证重置token并更新密码，暂时返回成功
        return jsonify({
            "success": True,
            "message": "密码重置成功"
        })
        
    except Exception as e:
        logger.error(f"重置密码失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "重置密码失败"
        }), 500


@auth_bp.route('/validate', methods=['GET', 'POST'])
def validate_token():
    """验证令牌有效性（简化版）"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "valid": False,
                "message": "未提供有效的认证令牌"
            }), 401
        
        token = auth_header.split(' ')[1]
        user = user_manager.verify_token(token)
        
        if not user:
            return jsonify({
                "success": False,
                "valid": False,
                "message": "无效的认证令牌"
            }), 401
        
        return jsonify({
            "success": True,
            "valid": True,
            "message": "令牌有效",
            "data": {
                "user": {
                    "user_id": user["id"],  # 修复字段名
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"令牌验证失败: {str(e)}")
        return jsonify({
            "success": False,
            "valid": False,
            "message": "令牌验证失败"
        }), 500


@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """验证访问令牌"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "error": "未提供有效的认证令牌"
            }), 401
        
        token = auth_header.split(' ')[1]
        user = user_manager.verify_token(token)
        
        if not user:
            return jsonify({
                "success": False,
                "error": "无效的认证令牌"
            }), 401
        
        return jsonify({
            "success": True,
            "message": "令牌验证成功",
            "data": {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "status": user["status"]
            }
        })
        
    except Exception as e:
        logger.error(f"令牌验证失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "令牌验证失败"
        }), 500

@auth_bp.route('/health', methods=['GET'])
def health_check():
    """认证服务健康检查"""
    try:
        return jsonify({
            "success": True,
            "message": "认证服务运行正常",
            "data": {
                "status": "healthy",
                "users_count": len(user_manager.users),
                "active_tokens": len(user_manager.tokens),
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "健康检查失败"
        }), 500

@auth_bp.route('/test', methods=['POST'])
def test_auth():
    """测试认证功能"""
    try:
        # 创建测试用户
        test_user = user_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!"
        )
        
        # 创建测试令牌
        test_token = user_manager.create_token(test_user)
        
        return jsonify({
            "success": True,
            "message": "认证功能测试成功",
            "data": {
                "test_user": {
                    "user_id": test_user["user_id"],
                    "username": test_user["username"],
                    "email": test_user["email"]
                },
                "test_token": test_token,
                "users_count": len(user_manager.users),
                "tokens_count": len(user_manager.tokens)
            }
        })
        
    except Exception as e:
        logger.error(f"认证功能测试失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "认证功能测试失败"
        }), 500








