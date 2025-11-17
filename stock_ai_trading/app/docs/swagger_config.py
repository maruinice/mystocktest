"""
Swagger文档配置
"""

from flask import Flask
from flasgger import Swagger
from flasgger.utils import swag_from


# Swagger配置
SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

# Swagger模板
SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "AI股票交易系统API",
        "description": "基于人工智能的股票交易系统API文档",
        "contact": {
            "name": "开发团队",
            "email": "dev@example.com",
            "url": "https://github.com/example/stock-ai-trading"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        "version": "1.0.0"
    },
    "host": "localhost:5000",
    "basePath": "/api",
    "schemes": [
        "http",
        "https"
    ],
    "consumes": [
        "application/json"
    ],
    "produces": [
        "application/json"
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT授权头，格式: Bearer <token>"
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ],
    "tags": [
        {
            "name": "认证",
            "description": "用户认证相关接口"
        },
        {
            "name": "数据",
            "description": "股票数据相关接口"
        },
        {
            "name": "交易",
            "description": "交易相关接口"
        },
        {
            "name": "策略",
            "description": "交易策略相关接口"
        },
        {
            "name": "系统",
            "description": "系统管理相关接口"
        }
    ],
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "用户ID"
                },
                "username": {
                    "type": "string",
                    "description": "用户名"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "邮箱地址"
                },
                "full_name": {
                    "type": "string",
                    "description": "全名"
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time",
                    "description": "创建时间"
                }
            }
        },
        "Stock": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码"
                },
                "name": {
                    "type": "string",
                    "description": "股票名称"
                },
                "price": {
                    "type": "number",
                    "format": "float",
                    "description": "当前价格"
                },
                "change": {
                    "type": "number",
                    "format": "float",
                    "description": "涨跌额"
                },
                "change_pct": {
                    "type": "number",
                    "format": "float",
                    "description": "涨跌幅(%)"
                },
                "volume": {
                    "type": "integer",
                    "description": "成交量"
                },
                "turnover": {
                    "type": "number",
                    "format": "float",
                    "description": "成交额"
                }
            }
        },
        "Order": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "订单ID"
                },
                "symbol": {
                    "type": "string",
                    "description": "股票代码"
                },
                "side": {
                    "type": "string",
                    "enum": ["buy", "sell"],
                    "description": "交易方向"
                },
                "order_type": {
                    "type": "string",
                    "enum": ["market", "limit"],
                    "description": "订单类型"
                },
                "quantity": {
                    "type": "integer",
                    "description": "数量"
                },
                "price": {
                    "type": "number",
                    "format": "float",
                    "description": "价格"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "filled", "cancelled"],
                    "description": "订单状态"
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time",
                    "description": "创建时间"
                }
            }
        },
        "Strategy": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "策略ID"
                },
                "name": {
                    "type": "string",
                    "description": "策略名称"
                },
                "description": {
                    "type": "string",
                    "description": "策略描述"
                },
                "parameters": {
                    "type": "object",
                    "description": "策略参数"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive"],
                    "description": "策略状态"
                }
            }
        },
        "BacktestResult": {
            "type": "object",
            "properties": {
                "backtest_id": {
                    "type": "string",
                    "description": "回测ID"
                },
                "strategy_id": {
                    "type": "string",
                    "description": "策略ID"
                },
                "symbol": {
                    "type": "string",
                    "description": "股票代码"
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "开始日期"
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "结束日期"
                },
                "initial_capital": {
                    "type": "number",
                    "format": "float",
                    "description": "初始资金"
                },
                "final_capital": {
                    "type": "number",
                    "format": "float",
                    "description": "最终资金"
                },
                "total_return": {
                    "type": "number",
                    "format": "float",
                    "description": "总收益率"
                },
                "sharpe_ratio": {
                    "type": "number",
                    "format": "float",
                    "description": "夏普比率"
                },
                "max_drawdown": {
                    "type": "number",
                    "format": "float",
                    "description": "最大回撤"
                }
            }
        },
        "ApiResponse": {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "请求是否成功"
                },
                "message": {
                    "type": "string",
                    "description": "响应消息"
                },
                "data": {
                    "type": "object",
                    "description": "响应数据"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "响应时间"
                }
            }
        },
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "default": False,
                    "description": "请求是否成功"
                },
                "error": {
                    "type": "string",
                    "description": "错误类型"
                },
                "message": {
                    "type": "string",
                    "description": "错误消息"
                },
                "details": {
                    "type": "object",
                    "description": "错误详情"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "错误时间"
                }
            }
        },
        "PaginationInfo": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "description": "当前页码"
                },
                "per_page": {
                    "type": "integer",
                    "description": "每页数量"
                },
                "total": {
                    "type": "integer",
                    "description": "总数量"
                },
                "pages": {
                    "type": "integer",
                    "description": "总页数"
                },
                "has_prev": {
                    "type": "boolean",
                    "description": "是否有上一页"
                },
                "has_next": {
                    "type": "boolean",
                    "description": "是否有下一页"
                }
            }
        }
    },
    "responses": {
        "200": {
            "description": "请求成功",
            "schema": {
                "$ref": "#/definitions/ApiResponse"
            }
        },
        "400": {
            "description": "请求参数错误",
            "schema": {
                "$ref": "#/definitions/ErrorResponse"
            }
        },
        "401": {
            "description": "未授权",
            "schema": {
                "$ref": "#/definitions/ErrorResponse"
            }
        },
        "403": {
            "description": "禁止访问",
            "schema": {
                "$ref": "#/definitions/ErrorResponse"
            }
        },
        "404": {
            "description": "资源不存在",
            "schema": {
                "$ref": "#/definitions/ErrorResponse"
            }
        },
        "429": {
            "description": "请求过于频繁",
            "schema": {
                "$ref": "#/definitions/ErrorResponse"
            }
        },
        "500": {
            "description": "服务器内部错误",
            "schema": {
                "$ref": "#/definitions/ErrorResponse"
            }
        }
    }
}


def init_swagger(app: Flask) -> Swagger:
    """
    初始化Swagger文档
    
    Args:
        app: Flask应用实例
        
    Returns:
        Swagger实例
    """
    return Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)


def get_swagger_spec(endpoint_name: str, methods: list = None):
    """
    获取Swagger规范装饰器
    
    Args:
        endpoint_name: 端点名称
        methods: HTTP方法列表
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        spec_file = f"specs/{endpoint_name}.yml"
        return swag_from(spec_file, methods=methods)(func)
    return decorator


# 通用参数定义
COMMON_PARAMETERS = {
    "page": {
        "name": "page",
        "in": "query",
        "type": "integer",
        "default": 1,
        "minimum": 1,
        "description": "页码"
    },
    "per_page": {
        "name": "per_page",
        "in": "query",
        "type": "integer",
        "default": 20,
        "minimum": 1,
        "maximum": 100,
        "description": "每页数量"
    },
    "symbol": {
        "name": "symbol",
        "in": "path",
        "type": "string",
        "required": True,
        "description": "股票代码"
    },
    "start_date": {
        "name": "start_date",
        "in": "query",
        "type": "string",
        "format": "date",
        "description": "开始日期 (YYYY-MM-DD)"
    },
    "end_date": {
        "name": "end_date",
        "in": "query",
        "type": "string",
        "format": "date",
        "description": "结束日期 (YYYY-MM-DD)"
    }
}

# 通用响应头
COMMON_HEADERS = {
    "X-RateLimit-Limit": {
        "description": "速率限制",
        "type": "integer"
    },
    "X-RateLimit-Remaining": {
        "description": "剩余请求数",
        "type": "integer"
    },
    "X-RateLimit-Reset": {
        "description": "限制重置时间",
        "type": "integer"
    }
}