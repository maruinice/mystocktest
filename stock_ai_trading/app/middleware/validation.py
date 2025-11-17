"""
参数验证中间件

提供统一的请求参数验证功能
"""

from functools import wraps
from flask import request, jsonify
import re
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
import json


class ValidationError(Exception):
    """验证错误异常"""
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code or 'validation_error'
        super().__init__(self.message)


class Validator:
    """验证器基类"""
    
    def __init__(self, required: bool = True, message: str = None):
        self.required = required
        self.message = message
    
    def validate(self, value: Any, field_name: str) -> Any:
        """验证值"""
        if value is None or value == '':
            if self.required:
                raise ValidationError(
                    self.message or f"字段 '{field_name}' 是必需的",
                    field=field_name,
                    code='required'
                )
            return None
        
        return self._validate_value(value, field_name)
    
    def _validate_value(self, value: Any, field_name: str) -> Any:
        """子类实现具体验证逻辑"""
        return value


class StringValidator(Validator):
    """字符串验证器"""
    
    def __init__(self, min_length: int = None, max_length: int = None, 
                 pattern: str = None, choices: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.choices = choices
    
    def _validate_value(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            try:
                value = str(value)
            except (ValueError, TypeError):
                raise ValidationError(
                    f"字段 '{field_name}' 必须是字符串",
                    field=field_name,
                    code='invalid_type'
                )
        
        # 长度验证
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                f"字段 '{field_name}' 长度不能少于 {self.min_length} 个字符",
                field=field_name,
                code='min_length'
            )
        
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                f"字段 '{field_name}' 长度不能超过 {self.max_length} 个字符",
                field=field_name,
                code='max_length'
            )
        
        # 正则验证
        if self.pattern and not self.pattern.match(value):
            raise ValidationError(
                f"字段 '{field_name}' 格式不正确",
                field=field_name,
                code='invalid_format'
            )
        
        # 选择验证
        if self.choices and value not in self.choices:
            raise ValidationError(
                f"字段 '{field_name}' 必须是以下值之一: {', '.join(self.choices)}",
                field=field_name,
                code='invalid_choice'
            )
        
        return value


class IntegerValidator(Validator):
    """整数验证器"""
    
    def __init__(self, min_value: int = None, max_value: int = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_value(self, value: Any, field_name: str) -> int:
        try:
            if isinstance(value, str):
                value = int(value)
            elif not isinstance(value, int):
                value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"字段 '{field_name}' 必须是整数",
                field=field_name,
                code='invalid_type'
            )
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"字段 '{field_name}' 不能小于 {self.min_value}",
                field=field_name,
                code='min_value'
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"字段 '{field_name}' 不能大于 {self.max_value}",
                field=field_name,
                code='max_value'
            )
        
        return value


class FloatValidator(Validator):
    """浮点数验证器"""
    
    def __init__(self, min_value: float = None, max_value: float = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_value(self, value: Any, field_name: str) -> float:
        try:
            if isinstance(value, str):
                value = float(value)
            elif not isinstance(value, (int, float)):
                value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"字段 '{field_name}' 必须是数字",
                field=field_name,
                code='invalid_type'
            )
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"字段 '{field_name}' 不能小于 {self.min_value}",
                field=field_name,
                code='min_value'
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"字段 '{field_name}' 不能大于 {self.max_value}",
                field=field_name,
                code='max_value'
            )
        
        return value


class BooleanValidator(Validator):
    """布尔值验证器"""
    
    def _validate_value(self, value: Any, field_name: str) -> bool:
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
        
        if isinstance(value, int):
            return bool(value)
        
        raise ValidationError(
            f"字段 '{field_name}' 必须是布尔值",
            field=field_name,
            code='invalid_type'
        )


class EmailValidator(StringValidator):
    """邮箱验证器"""
    
    def __init__(self, **kwargs):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        super().__init__(pattern=email_pattern, **kwargs)
    
    def _validate_value(self, value: Any, field_name: str) -> str:
        value = super()._validate_value(value, field_name)
        
        if not self.pattern.match(value):
            raise ValidationError(
                f"字段 '{field_name}' 必须是有效的邮箱地址",
                field=field_name,
                code='invalid_email'
            )
        
        return value


class DateTimeValidator(Validator):
    """日期时间验证器"""
    
    def __init__(self, format: str = '%Y-%m-%d %H:%M:%S', **kwargs):
        super().__init__(**kwargs)
        self.format = format
    
    def _validate_value(self, value: Any, field_name: str) -> datetime:
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                return datetime.strptime(value, self.format)
            except ValueError:
                raise ValidationError(
                    f"字段 '{field_name}' 日期格式不正确，应为 {self.format}",
                    field=field_name,
                    code='invalid_datetime'
                )
        
        raise ValidationError(
            f"字段 '{field_name}' 必须是日期时间",
            field=field_name,
            code='invalid_type'
        )


class ListValidator(Validator):
    """列表验证器"""
    
    def __init__(self, item_validator: Validator = None, min_items: int = None, 
                 max_items: int = None, **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_items = min_items
        self.max_items = max_items
    
    def _validate_value(self, value: Any, field_name: str) -> List[Any]:
        if not isinstance(value, list):
            raise ValidationError(
                f"字段 '{field_name}' 必须是列表",
                field=field_name,
                code='invalid_type'
            )
        
        if self.min_items is not None and len(value) < self.min_items:
            raise ValidationError(
                f"字段 '{field_name}' 至少需要 {self.min_items} 个项目",
                field=field_name,
                code='min_items'
            )
        
        if self.max_items is not None and len(value) > self.max_items:
            raise ValidationError(
                f"字段 '{field_name}' 最多允许 {self.max_items} 个项目",
                field=field_name,
                code='max_items'
            )
        
        # 验证列表项
        if self.item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = self.item_validator.validate(item, f"{field_name}[{i}]")
                    validated_items.append(validated_item)
                except ValidationError as e:
                    raise ValidationError(
                        f"字段 '{field_name}' 第 {i+1} 项: {e.message}",
                        field=field_name,
                        code=e.code
                    )
            return validated_items
        
        return value


class DictValidator(Validator):
    """字典验证器"""
    
    def __init__(self, schema: Dict[str, Validator] = None, **kwargs):
        super().__init__(**kwargs)
        self.schema = schema or {}
    
    def _validate_value(self, value: Any, field_name: str) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise ValidationError(
                f"字段 '{field_name}' 必须是对象",
                field=field_name,
                code='invalid_type'
            )
        
        validated_data = {}
        
        # 验证已定义的字段
        for key, validator in self.schema.items():
            try:
                validated_data[key] = validator.validate(
                    value.get(key), f"{field_name}.{key}"
                )
            except ValidationError as e:
                raise ValidationError(
                    e.message,
                    field=e.field,
                    code=e.code
                )
        
        # 保留未定义的字段
        for key, val in value.items():
            if key not in self.schema:
                validated_data[key] = val
        
        return validated_data


class ValidationMiddleware:
    """验证中间件"""
    
    @staticmethod
    def validate_request(schema: Dict[str, Validator], location: str = 'json'):
        """
        验证请求数据装饰器
        
        Args:
            schema: 验证模式
            location: 数据位置 ('json', 'form', 'args', 'headers')
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    # 获取请求数据
                    if location == 'json':
                        data = request.get_json() or {}
                    elif location == 'form':
                        data = request.form.to_dict()
                    elif location == 'args':
                        data = request.args.to_dict()
                    elif location == 'headers':
                        data = dict(request.headers)
                    else:
                        raise ValueError(f"不支持的数据位置: {location}")
                    
                    # 验证数据
                    validated_data = {}
                    errors = []
                    
                    for field_name, validator in schema.items():
                        try:
                            validated_data[field_name] = validator.validate(
                                data.get(field_name), field_name
                            )
                        except ValidationError as e:
                            errors.append({
                                'field': e.field,
                                'message': e.message,
                                'code': e.code
                            })
                    
                    if errors:
                        return jsonify({
                            'error': 'validation_error',
                            'message': '请求参数验证失败',
                            'details': errors
                        }), 400
                    
                    # 将验证后的数据添加到请求上下文
                    request.validated_data = validated_data
                    
                    return func(*args, **kwargs)
                
                except Exception as e:
                    return jsonify({
                        'error': 'validation_error',
                        'message': f'参数验证异常: {str(e)}'
                    }), 400
            
            return wrapper
        return decorator
    
    @staticmethod
    def validate_query_params(**validators):
        """验证查询参数装饰器"""
        return ValidationMiddleware.validate_request(validators, 'args')
    
    @staticmethod
    def validate_json(**validators):
        """验证JSON数据装饰器"""
        return ValidationMiddleware.validate_request(validators, 'json')
    
    @staticmethod
    def validate_form(**validators):
        """验证表单数据装饰器"""
        return ValidationMiddleware.validate_request(validators, 'form')


# 常用验证器实例
class CommonValidators:
    """常用验证器"""
    
    # 用户相关
    username = StringValidator(
        min_length=3, max_length=50,
        pattern=r'^[a-zA-Z0-9_]+$',
        message="用户名只能包含字母、数字和下划线，长度3-50个字符"
    )
    
    password = StringValidator(
        min_length=6, max_length=128,
        message="密码长度必须在6-128个字符之间"
    )
    
    email = EmailValidator(message="请输入有效的邮箱地址")
    
    # 股票相关
    stock_code = StringValidator(
        pattern=r'^[0-9]{6}$',
        message="股票代码必须是6位数字"
    )
    
    # 分页相关
    page = IntegerValidator(min_value=1, required=False, message="页码必须大于0")
    page_size = IntegerValidator(
        min_value=1, max_value=100, required=False,
        message="每页数量必须在1-100之间"
    )
    
    # 交易相关
    order_side = StringValidator(
        choices=['buy', 'sell'],
        message="订单方向必须是 buy 或 sell"
    )
    
    order_type = StringValidator(
        choices=['market', 'limit', 'stop'],
        message="订单类型必须是 market、limit 或 stop"
    )
    
    quantity = IntegerValidator(
        min_value=1,
        message="数量必须大于0"
    )
    
    price = FloatValidator(
        min_value=0.01,
        message="价格必须大于0.01"
    )
    
    # 日期时间相关
    start_date = StringValidator(
        pattern=r'^\d{4}-\d{2}-\d{2}$',
        required=False,
        message="开始日期格式必须是 YYYY-MM-DD"
    )
    
    end_date = StringValidator(
        pattern=r'^\d{4}-\d{2}-\d{2}$',
        required=False,
        message="结束日期格式必须是 YYYY-MM-DD"
    )


# 导出常用装饰器
validate_json = ValidationMiddleware.validate_json
validate_query_params = ValidationMiddleware.validate_query_params
validate_form = ValidationMiddleware.validate_form