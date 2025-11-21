# -*- coding: utf-8 -*-
"""
数据API模块
提供股票数据、市场数据相关的REST API接口
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging

# 创建蓝图
data_bp = Blueprint('data', __name__, url_prefix='/api/data')

logger = logging.getLogger(__name__)

class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_stock_code(code: str) -> bool:
        """验证股票代码格式（支持带后缀和不带后缀）"""
        if not code or len(code) < 6:
            return False
        
        # 支持格式：
        # 1. 6位纯数字（如603387）
        # 2. 带市场后缀（如603387.SH, 000001.SZ）
        
        # 去掉市场后缀
        if '.' in code:
            stock_num, market = code.split('.')
            if market not in ['SH', 'SZ', 'BJ']:
                return False
            code = stock_num
        
        # 验证6位数字代码
        if len(code) != 6 or not code.isdigit():
            return False
        
        # 验证代码前缀（沪市60/68/90，深市00/30/20，北交所8/4）
        return code[:2] in ['00', '30', '60', '68', '90', '20'] or code[0] in ['8', '4']
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> tuple[bool, str]:
        """验证日期范围"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start > end:
                return False, "开始日期不能晚于结束日期"
            
            if end > datetime.now():
                return False, "结束日期不能晚于当前日期"
            
            return True, ""
        except ValueError:
            return False, "日期格式错误，请使用YYYY-MM-DD格式"
    
    @staticmethod
    def validate_pagination(page: int, size: int) -> tuple[bool, str]:
        """验证分页参数"""
        if page < 1:
            return False, "页码必须大于0"
        
        if size < 1 or size > 100:
            return False, "每页数量必须在1-100之间"
        
        return True, ""

class MockDataService:
    """模拟数据服务"""
    
    def __init__(self):
        self.stocks = self._generate_mock_stocks()
        self.watchlists = {}
    
    def _generate_mock_stocks(self) -> List[Dict[str, Any]]:
        """生成模拟股票数据"""
        stocks = []
        for i in range(100):
            code = f"{600000 + i:06d}"
            stocks.append({
                "code": code,
                "name": f"股票{i+1}",
                "market": "SH" if code.startswith("60") else "SZ",
                "industry": "科技" if i % 3 == 0 else "金融" if i % 3 == 1 else "制造",
                "current_price": 10.0 + i * 0.1,
                "change": (i % 10 - 5) * 0.1,
                "change_percent": (i % 10 - 5) * 0.01,
                "volume": 1000000 + i * 10000,
                "market_cap": 1000000000 + i * 10000000,
                "pe_ratio": 15.0 + i * 0.1,
                "pb_ratio": 1.5 + i * 0.01
            })
        return stocks
    
    def get_stock_list(self, market: str = None, industry: str = None, 
                      keyword: str = None, page: int = 1, size: int = 20) -> tuple[List[Dict], int]:
        """获取股票列表"""
        filtered_stocks = self.stocks.copy()
        
        if market:
            filtered_stocks = [s for s in filtered_stocks if s["market"] == market]
        
        if industry:
            filtered_stocks = [s for s in filtered_stocks if s["industry"] == industry]
        
        if keyword:
            filtered_stocks = [s for s in filtered_stocks 
                             if keyword.lower() in s["name"].lower() or keyword in s["code"]]
        
        total = len(filtered_stocks)
        start = (page - 1) * size
        end = start + size
        
        return filtered_stocks[start:end], total
    
    def get_stock_quotes(self, code: str, period: str = "day", 
                        start_date: str = None, end_date: str = None, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """获取股票行情数据"""
        quotes = []
        base_price = 10.0
        
        for i in range(min(limit, 30)):
            date = datetime.now() - timedelta(days=i)
            price = base_price + (i % 10 - 5) * 0.1
            
            quotes.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": price,
                "high": price * 1.05,
                "low": price * 0.95,
                "close": price,
                "volume": 1000000 + i * 10000,
                "amount": price * (1000000 + i * 10000)
            })
        
        return quotes
    
    def get_stock_info(self, code: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        stock = next((s for s in self.stocks if s["code"] == code), None)
        if not stock:
            return None
        
        return {
            **stock,
            "description": f"这是{stock['name']}的详细信息",
            "listing_date": "2020-01-01",
            "total_shares": 1000000000,
            "float_shares": 800000000,
            "website": "https://example.com",
            "business": "主营业务描述"
        }
    
    def get_stock_financials(self, code: str, report_type: str = "annual", 
                           year: int = None, limit: int = 5) -> List[Dict[str, Any]]:
        """获取股票财务数据"""
        financials = []
        current_year = datetime.now().year
        
        for i in range(limit):
            year_offset = current_year - i
            financials.append({
                "year": year_offset,
                "quarter": 4 if report_type == "annual" else 1,
                "revenue": 1000000000 + i * 100000000,
                "net_profit": 100000000 + i * 10000000,
                "total_assets": 5000000000 + i * 500000000,
                "total_liabilities": 3000000000 + i * 300000000,
                "shareholders_equity": 2000000000 + i * 200000000,
                "eps": 1.0 + i * 0.1,
                "roe": 0.15 + i * 0.01,
                "roa": 0.08 + i * 0.005
            })
        
        return financials
    
    def get_stock_news(self, code: str, start_date: str = None, 
                      end_date: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """获取股票新闻"""
        news = []
        
        for i in range(limit):
            date = datetime.now() - timedelta(days=i)
            news.append({
                "id": f"news_{i}",
                "title": f"关于{code}的重要新闻{i+1}",
                "summary": f"这是关于股票{code}的新闻摘要{i+1}",
                "content": f"这是关于股票{code}的详细新闻内容{i+1}",
                "source": "财经新闻网",
                "publish_time": date.isoformat(),
                "url": f"https://news.example.com/{i}"
            })
        
        return news
    
    def get_stock_analysis(self, code: str, start_date: str = None, 
                          end_date: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取股票分析报告"""
        analyses = []
        
        for i in range(limit):
            date = datetime.now() - timedelta(days=i*7)
            analyses.append({
                "id": f"analysis_{i}",
                "title": f"{code}投资分析报告{i+1}",
                "analyst": f"分析师{i+1}",
                "institution": f"投资机构{i+1}",
                "rating": ["买入", "持有", "卖出"][i % 3],
                "target_price": 12.0 + i * 0.5,
                "publish_time": date.isoformat(),
                "summary": f"对{code}的分析摘要{i+1}"
            })
        
        return analyses
    
    def search_stocks(self, keyword: str, search_type: str = "all", 
                     limit: int = 20) -> List[Dict[str, Any]]:
        """搜索股票"""
        results = []
        
        for stock in self.stocks:
            if len(results) >= limit:
                break
            
            if search_type == "all":
                if (keyword.lower() in stock["name"].lower() or 
                    keyword in stock["code"]):
                    results.append(stock)
            elif search_type == "code":
                if keyword in stock["code"]:
                    results.append(stock)
            elif search_type == "name":
                if keyword.lower() in stock["name"].lower():
                    results.append(stock)
        
        return results
    
    def get_watchlist(self, user_id: str) -> List[str]:
        """获取用户关注列表"""
        return self.watchlists.get(user_id, [])
    
    def add_to_watchlist(self, user_id: str, code: str) -> bool:
        """添加到关注列表"""
        if user_id not in self.watchlists:
            self.watchlists[user_id] = []
        
        if code not in self.watchlists[user_id]:
            self.watchlists[user_id].append(code)
            return True
        
        return False
    
    def remove_from_watchlist(self, user_id: str, code: str) -> bool:
        """从关注列表移除"""
        if user_id in self.watchlists and code in self.watchlists[user_id]:
            self.watchlists[user_id].remove(code)
            return True
        
        return False
    
    def get_market_indicators(self, indicator_type: str = "all", 
                            start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """获取市场指标"""
        indicators = []
        
        if indicator_type in ["all", "index"]:
            indicators.extend([
                {"name": "上证指数", "code": "000001", "value": 3200.0, "change": 1.2, "change_percent": 0.038},
                {"name": "深证成指", "code": "399001", "value": 12000.0, "change": -5.5, "change_percent": -0.046},
                {"name": "创业板指", "code": "399006", "value": 2800.0, "change": 8.8, "change_percent": 0.032}
            ])
        
        if indicator_type in ["all", "sector"]:
            indicators.extend([
                {"name": "科技板块", "value": 1500.0, "change": 2.1, "change_percent": 0.014},
                {"name": "金融板块", "value": 1200.0, "change": -1.8, "change_percent": -0.015},
                {"name": "制造板块", "value": 1800.0, "change": 3.2, "change_percent": 0.018}
            ])
        
        return indicators
    
    def get_market_summary(self) -> Dict[str, Any]:
        """获取市场概况"""
        return {
            "total_stocks": len(self.stocks),
            "rising_stocks": 45,
            "falling_stocks": 35,
            "unchanged_stocks": 20,
            "total_volume": 50000000000,
            "total_amount": 800000000000,
            "market_cap": 60000000000000,
            "timestamp": datetime.now().isoformat()
        }

# 全局数据服务实例
from app.services.data_service import DataService
data_service = DataService()

def require_auth(f):
    """认证装饰器（简化版）"""
    def wrapper(*args, **kwargs):
        # 这里应该验证用户认证，简化处理
        g.current_user = {"user_id": "test_user", "username": "testuser"}
        return f(*args, **kwargs)
    
    wrapper.__name__ = f.__name__
    return wrapper

@data_bp.route('/stocks', methods=['GET'])
@require_auth
def get_stock_list():
    """获取股票列表"""
    try:
        # 获取查询参数
        market = request.args.get('market', '').upper()
        industry = request.args.get('industry', '')
        keyword = request.args.get('keyword', '')
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        
        # 验证分页参数
        is_valid, message = DataValidator.validate_pagination(page, size)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": message
            }), 400
        
        # 获取股票列表
        stocks, total = data_service.get_stock_list(
            market=market if market else None,
            industry=industry if industry else None,
            keyword=keyword if keyword else None,
            page=page,
            size=size
        )
        
        return jsonify({
            "success": True,
            "data": {
                "stocks": stocks,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"获取股票列表失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取股票列表失败"
        }), 500

@data_bp.route('/stocks/<code>/quotes', methods=['GET'])
@require_auth
def get_stock_quotes(code: str):
    """获取股票行情数据"""
    try:
        # 验证股票代码
        if not DataValidator.validate_stock_code(code):
            return jsonify({
                "success": False,
                "error": "无效的股票代码"
            }), 400
        
        # 获取查询参数
        period = request.args.get('period', 'day')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        # 验证周期参数
        if period not in ['day', 'week', 'month']:
            return jsonify({
                "success": False,
                "error": "无效的周期参数，支持: day, week, month"
            }), 400
        
        # 验证日期范围
        if start_date and end_date:
            is_valid, message = DataValidator.validate_date_range(start_date, end_date)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": message
                }), 400
        
        # 获取行情数据
        quotes = data_service.get_stock_quotes(
            code=code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": {
                "code": code,
                "period": period,
                "quotes": quotes
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"获取股票行情失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取股票行情失败"
        }), 500

@data_bp.route('/stock/<code>', methods=['GET'])
@data_bp.route('/stocks/<code>/info', methods=['GET'])
@require_auth
def get_stock_info(code: str):
    """获取股票基本信息（支持两种路由）"""
    try:
        # 验证股票代码（允许带后缀的代码如603387.SH）
        # 移除.SH/.SZ后缀进行验证
        base_code = code.split('.')[0]
        if not base_code.isdigit() or len(base_code) != 6:
            return jsonify({
                "success": False,
                "error": "无效的股票代码"
            }), 400
        
        # 获取股票信息
        stock_info = data_service.get_stock_info(code)
        if not stock_info:
            return jsonify({
                "success": False,
                "error": "股票不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "data": stock_info
        })
        
    except Exception as e:
        logger.error(f"获取股票信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取股票信息失败"
        }), 500

@data_bp.route('/stocks/<code>/financials', methods=['GET'])
@require_auth
def get_stock_financials(code: str):
    """获取股票财务数据"""
    try:
        # 验证股票代码
        if not DataValidator.validate_stock_code(code):
            return jsonify({
                "success": False,
                "error": "无效的股票代码"
            }), 400
        
        # 获取查询参数
        report_type = request.args.get('type', 'annual')
        year = request.args.get('year')
        limit = int(request.args.get('limit', 5))
        
        # 验证报告类型
        if report_type not in ['annual', 'quarterly']:
            return jsonify({
                "success": False,
                "error": "无效的报告类型，支持: annual, quarterly"
            }), 400
        
        # 验证年份
        if year:
            try:
                year = int(year)
                if year < 2000 or year > datetime.now().year:
                    return jsonify({
                        "success": False,
                        "error": "无效的年份"
                    }), 400
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "年份格式错误"
                }), 400
        
        # 获取财务数据
        financials = data_service.get_stock_financials(
            code=code,
            report_type=report_type,
            year=year,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": {
                "code": code,
                "type": report_type,
                "financials": financials
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"获取财务数据失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取财务数据失败"
        }), 500

@data_bp.route('/stocks/<code>/news', methods=['GET'])
@require_auth
def get_stock_news(code: str):
    """获取股票新闻"""
    try:
        # 验证股票代码
        if not DataValidator.validate_stock_code(code):
            return jsonify({
                "success": False,
                "error": "无效的股票代码"
            }), 400
        
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 20))
        
        # 验证日期范围
        if start_date and end_date:
            is_valid, message = DataValidator.validate_date_range(start_date, end_date)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": message
                }), 400
        
        # 获取新闻数据
        news = data_service.get_stock_news(
            code=code,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": {
                "code": code,
                "news": news
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"获取股票新闻失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取股票新闻失败"
        }), 500

@data_bp.route('/stocks/<code>/analysis', methods=['GET'])
@require_auth
def get_stock_analysis(code: str):
    """获取股票分析报告"""
    try:
        # 验证股票代码
        if not DataValidator.validate_stock_code(code):
            return jsonify({
                "success": False,
                "error": "无效的股票代码"
            }), 400
        
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 10))
        
        # 验证日期范围
        if start_date and end_date:
            is_valid, message = DataValidator.validate_date_range(start_date, end_date)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": message
                }), 400
        
        # 获取分析报告
        analyses = data_service.get_stock_analysis(
            code=code,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": {
                "code": code,
                "analyses": analyses
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"获取分析报告失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取分析报告失败"
        }), 500

@data_bp.route('/search', methods=['GET', 'OPTIONS'])
def search_api():
    """股票搜索API接口"""
    if request.method == 'OPTIONS':
        # 处理预检请求，不需要认证
        return '', 200
    
    # 只对非OPTIONS请求进行认证检查
    from app.middleware.auth import auth_middleware
    success, user_info, error_msg = auth_middleware.authenticate_request()
    if not success:
        return jsonify({
            "success": False,
            "error": "认证失败",
            "message": error_msg
        }), 401
        
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not keyword:
            return jsonify({
                "success": False,
                "error": "搜索关键词不能为空"
            }), 400
        
        # 搜索股票
        stocks = data_service.search_stocks(
            keyword=keyword,
            search_type='all',
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": stocks,
            "message": f"找到 {len(stocks)} 条股票记录"
        })
        
    except ValueError as e:
        logger.error(f"搜索股票参数错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        return jsonify({
            "success": False,
            "error": "搜索股票失败"
        }), 500

@data_bp.route('/stocks/search', methods=['GET'])
@require_auth
def search_stocks():
    """搜索股票"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        search_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 20))
        
        if not keyword:
            return jsonify({
                "success": False,
                "error": "搜索关键词不能为空"
            }), 400
        
        # 验证搜索类型
        valid_types = ['all', 'code', 'name', 'pinyin']
        if search_type not in valid_types:
            return jsonify({
                "success": False,
                "error": f"无效的搜索类型，支持: {', '.join(valid_types)}"
            }), 400
        
        # 搜索股票
        stocks = data_service.search_stocks(
            keyword=keyword,
            search_type=search_type,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": {
                "keyword": keyword,
                "type": search_type,
                "stocks": stocks
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"搜索股票失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "搜索股票失败"
        }), 500

@data_bp.route('/watchlist', methods=['GET'])
@require_auth
def get_watchlist():
    """获取关注列表"""
    try:
        user = g.current_user
        codes = data_service.get_watchlist(user["user_id"])
        
        # 获取关注股票的详细信息
        stocks = []
        for code in codes:
            stock_info = data_service.get_stock_info(code)
            if stock_info:
                stocks.append(stock_info)
        
        return jsonify({
            "success": True,
            "data": {
                "stocks": stocks
            }
        })
        
    except Exception as e:
        logger.error(f"获取关注列表失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取关注列表失败"
        }), 500

@data_bp.route('/watchlist', methods=['POST'])
@require_auth
def add_to_watchlist():
    """添加到关注列表"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400
        
        code = data.get('code', '').strip()
        if not code:
            return jsonify({
                "success": False,
                "error": "股票代码不能为空"
            }), 400
        
        # 验证股票代码
        if not DataValidator.validate_stock_code(code):
            return jsonify({
                "success": False,
                "error": "无效的股票代码"
            }), 400
        
        user = g.current_user
        
        # 添加到关注列表
        success = data_service.add_to_watchlist(user["user_id"], code)
        if not success:
            return jsonify({
                "success": False,
                "error": "股票已在关注列表中"
            }), 409
        
        return jsonify({
            "success": True,
            "message": "添加成功",
            "data": {
                "code": code
            }
        }), 201
        
    except Exception as e:
        logger.error(f"添加关注失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "添加关注失败"
        }), 500

@data_bp.route('/watchlist/<code>', methods=['DELETE'])
@require_auth
def remove_from_watchlist(code: str):
    """从关注列表移除"""
    try:
        user = g.current_user
        
        # 从关注列表移除
        success = data_service.remove_from_watchlist(user["user_id"], code)
        if not success:
            return jsonify({
                "success": False,
                "error": "股票不在关注列表中"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "移除成功",
            "data": {
                "code": code
            }
        })
        
    except Exception as e:
        logger.error(f"移除关注失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "移除关注失败"
        }), 500

@data_bp.route('/market/<string:symbol>', methods=['GET'])
@require_auth
def get_market_data(symbol: str):
    """获取股票行情数据"""
    try:
        # 获取查询参数
        period = request.args.get('period', '1D')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 验证股票代码
        if not symbol:
            return jsonify({
                "success": False,
                "error": "股票代码不能为空"
            }), 400
        
        # 验证日期范围
        if start_date and end_date:
            is_valid, message = DataValidator.validate_date_range(start_date, end_date)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": message
                }), 400
        
        # 获取行情数据（返回StockQuote对象列表）
        quotes = data_service.get_stock_quotes(
            code=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=500
        )
        
        if not quotes:
            return jsonify({
                "success": False,
                "error": "未找到行情数据"
            }), 404
        
        # 处理K线数据
        kline_data = []
        current_price = 0
        for quote in quotes:
            kline_data.append({
                'date': quote.date.strftime('%Y-%m-%d') if hasattr(quote.date, 'strftime') else str(quote.date),
                'open': quote.open_price,
                'close': quote.close_price,
                'high': quote.high_price,
                'low': quote.low_price,
                'volume': quote.volume
            })
            current_price = quote.close_price  # 最后一条是最新价格
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": symbol,
                "current_price": current_price,
                "kline_data": kline_data,
                "period": period
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"获取行情数据失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取行情数据失败"
        }), 500

@data_bp.route('/financial/<string:symbol>', methods=['GET'])
@require_auth
def get_financial_data_api(symbol: str):
    """获取股票财务数据（前端专用API）"""
    try:
        # 验证股票代码
        if not symbol:
            return jsonify({
                "success": False,
                "error": "股票代码不能为空"
            }), 400
        
        # 获取查询参数
        report_type = request.args.get('report_type', 'annual')
        year = request.args.get('year')
        limit = int(request.args.get('limit', 5))
        
        # 获取财务数据
        financials = data_service.get_stock_financials(
            code=symbol,
            report_type=report_type,
            year=year,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": financials
        })
        
    except Exception as e:
        logger.error(f"获取财务数据失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取财务数据失败"
        }), 500

@data_bp.route('/market/indicators', methods=['GET'])
@require_auth
def get_market_indicators():
    """获取市场指标"""
    try:
        # 获取查询参数
        indicator_type = request.args.get('type', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 验证指标类型
        valid_types = ['all', 'index', 'sector', 'macro']
        if indicator_type not in valid_types:
            return jsonify({
                "success": False,
                "error": f"无效的指标类型，支持: {', '.join(valid_types)}"
            }), 400
        
        # 验证日期范围
        if start_date and end_date:
            is_valid, message = DataValidator.validate_date_range(start_date, end_date)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": message
                }), 400
        
        # 获取市场指标
        indicators = data_service.get_market_indicators(
            indicator_type=indicator_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            "success": True,
            "data": {
                "type": indicator_type,
                "indicators": indicators
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"获取市场指标失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取市场指标失败"
        }), 500

@data_bp.route('/market/summary', methods=['GET'])
@require_auth
def get_market_summary():
    """获取市场概况"""
    try:
        summary = data_service.get_market_summary()
        
        return jsonify({
            "success": True,
            "data": summary
        })
        
    except Exception as e:
        logger.error(f"获取市场概况失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取市场概况失败"
        }), 500

@data_bp.route('/news', methods=['GET'])
@require_auth
def get_news():
    """获取新闻（支持按股票代码筛选，通过大模型获取）"""
    try:
        # 获取查询参数
        symbol = request.args.get('symbol')
        category = request.args.get('category')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 验证分页参数
        is_valid, message = DataValidator.validate_pagination(page, page_size)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": message
            }), 400
        
        # 通过大模型获取新闻数据
        try:
            from app.services.llm_gateway import gateway, GatewayRequest
            import asyncio
            
            # 构建提示词
            prompt = f"""请生成关于{symbol or '股票市场'}的最新财经新闻，要求：
1. 生成{page_size}条新闻
2. 每条新闻包含：标题、摘要、内容、来源、发布时间
3. 新闻内容要真实、专业、有参考价值
4. 返回JSON格式，格式如下：
{{
  "news": [
    {{
      "id": "news_1",
      "title": "新闻标题",
      "summary": "新闻摘要",
      "content": "新闻详细内容",
      "source": "新闻来源",
      "publish_time": "2025-01-20T10:00:00",
      "url": "https://example.com/news/1",
      "symbol": "{symbol or ''}"
    }}
  ]
}}"""
            
            # 调用大模型
            request_obj = GatewayRequest(
                messages=[
                    {"role": "system", "content": "你是一个专业的财经新闻生成助手，能够生成真实、专业的股票市场新闻。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # 同步调用（在Flask中）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(gateway.generate(request_obj))
                loop.close()
            except Exception:
                loop.close()
                raise
            
            if response.success:
                # 解析LLM返回的JSON
                import json
                try:
                    # 尝试从响应中提取JSON
                    content = response.content.strip()
                    # 移除可能的markdown代码块标记
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.startswith('```'):
                        content = content[3:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()
                    
                    llm_data = json.loads(content)
                    news = llm_data.get('news', [])
                except json.JSONDecodeError:
                    # 如果解析失败，使用模拟数据
                    logger.warning("LLM返回数据解析失败，使用模拟数据")
                    news = []
                    for i in range(page_size):
                        date = datetime.now() - timedelta(days=i)
                        news.append({
                            "id": f"news_{i}",
                            "title": f"{symbol or '市场'}重要新闻{i+1}",
                            "summary": f"这是关于{symbol or '市场'}的新闻摘要{i+1}",
                            "content": f"这是关于{symbol or '市场'}的详细新闻内容{i+1}",
                            "source": "财经新闻网",
                            "publish_time": date.isoformat(),
                            "url": f"https://news.example.com/{i}",
                            "symbol": symbol
                        })
            else:
                # LLM调用失败，使用模拟数据
                logger.warning(f"LLM调用失败: {response.error}，使用模拟数据")
                news = []
                for i in range(page_size):
                    date = datetime.now() - timedelta(days=i)
                    news.append({
                        "id": f"news_{i}",
                        "title": f"{symbol or '市场'}重要新闻{i+1}",
                        "summary": f"这是关于{symbol or '市场'}的新闻摘要{i+1}",
                        "content": f"这是关于{symbol or '市场'}的详细新闻内容{i+1}",
                        "source": "财经新闻网",
                        "publish_time": date.isoformat(),
                        "url": f"https://news.example.com/{i}",
                        "symbol": symbol
                    })
        except Exception as llm_error:
            # LLM调用异常，使用模拟数据
            logger.warning(f"LLM调用异常: {str(llm_error)}，使用模拟数据")
            news = []
            for i in range(page_size):
                date = datetime.now() - timedelta(days=i)
                news.append({
                    "id": f"news_{i}",
                    "title": f"{symbol or '市场'}重要新闻{i+1}",
                    "summary": f"这是关于{symbol or '市场'}的新闻摘要{i+1}",
                    "content": f"这是关于{symbol or '市场'}的详细新闻内容{i+1}",
                    "source": "财经新闻网",
                    "publish_time": date.isoformat(),
                    "url": f"https://news.example.com/{i}",
                    "symbol": symbol
                })
        
        # 分页处理
        total = len(news)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_news = news[start:end]
        
        return jsonify({
            "success": True,
            "data": {
                "news": paginated_news,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"获取新闻失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取新闻失败"
        }), 500

@data_bp.route('/analysis', methods=['GET'])
@require_auth
def get_analysis_reports():
    """获取分析报告（支持按股票代码筛选，通过大模型获取）"""
    try:
        # 获取查询参数
        symbol = request.args.get('symbol')
        analyst = request.args.get('analyst')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 验证分页参数
        is_valid, message = DataValidator.validate_pagination(page, page_size)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": message
            }), 400
        
        # 通过大模型获取分析报告
        try:
            from app.services.llm_gateway import gateway, GatewayRequest
            import asyncio
            
            # 构建提示词
            prompt = f"""请生成关于{symbol or '股票市场'}的专业投资分析报告，要求：
1. 生成{page_size}份分析报告
2. 每份报告包含：标题、分析师、机构、评级、目标价、发布时间、摘要
3. 评级包括：买入、持有、卖出
4. 分析内容要专业、有参考价值
5. 返回JSON格式，格式如下：
{{
  "reports": [
    {{
      "id": "analysis_1",
      "title": "分析报告标题",
      "analyst": "分析师姓名",
      "institution": "投资机构名称",
      "rating": "买入",
      "target_price": 15.5,
      "publish_time": "2025-01-20T10:00:00",
      "summary": "分析报告摘要",
      "symbol": "{symbol or ''}"
    }}
  ]
}}"""
            
            # 调用大模型
            request_obj = GatewayRequest(
                messages=[
                    {"role": "system", "content": "你是一个专业的股票投资分析专家，能够生成专业、有价值的投资分析报告。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # 同步调用（在Flask中）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(gateway.generate(request_obj))
                loop.close()
            except Exception:
                loop.close()
                raise
            
            if response.success:
                # 解析LLM返回的JSON
                import json
                try:
                    # 尝试从响应中提取JSON
                    content = response.content.strip()
                    # 移除可能的markdown代码块标记
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.startswith('```'):
                        content = content[3:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()
                    
                    llm_data = json.loads(content)
                    reports = llm_data.get('reports', [])
                except json.JSONDecodeError:
                    # 如果解析失败，使用模拟数据
                    logger.warning("LLM返回数据解析失败，使用模拟数据")
                    reports = []
                    for i in range(page_size):
                        date = datetime.now() - timedelta(days=i*7)
                        reports.append({
                            "id": f"analysis_{i}",
                            "title": f"{symbol or '市场'}投资分析报告{i+1}",
                            "analyst": f"分析师{i+1}",
                            "institution": f"投资机构{i+1}",
                            "rating": ["买入", "持有", "卖出"][i % 3],
                            "target_price": 12.0 + i * 0.5,
                            "publish_time": date.isoformat(),
                            "summary": f"对{symbol or '市场'}的分析摘要{i+1}",
                            "symbol": symbol
                        })
            else:
                # LLM调用失败，使用模拟数据
                logger.warning(f"LLM调用失败: {response.error}，使用模拟数据")
                reports = []
                for i in range(page_size):
                    date = datetime.now() - timedelta(days=i*7)
                    reports.append({
                        "id": f"analysis_{i}",
                        "title": f"{symbol or '市场'}投资分析报告{i+1}",
                        "analyst": f"分析师{i+1}",
                        "institution": f"投资机构{i+1}",
                        "rating": ["买入", "持有", "卖出"][i % 3],
                        "target_price": 12.0 + i * 0.5,
                        "publish_time": date.isoformat(),
                        "summary": f"对{symbol or '市场'}的分析摘要{i+1}",
                        "symbol": symbol
                    })
        except Exception as llm_error:
            # LLM调用异常，使用模拟数据
            logger.warning(f"LLM调用异常: {str(llm_error)}，使用模拟数据")
            reports = []
            for i in range(page_size):
                date = datetime.now() - timedelta(days=i*7)
                reports.append({
                    "id": f"analysis_{i}",
                    "title": f"{symbol or '市场'}投资分析报告{i+1}",
                    "analyst": f"分析师{i+1}",
                    "institution": f"投资机构{i+1}",
                    "rating": ["买入", "持有", "卖出"][i % 3],
                    "target_price": 12.0 + i * 0.5,
                    "publish_time": date.isoformat(),
                    "summary": f"对{symbol or '市场'}的分析摘要{i+1}",
                    "symbol": symbol
                })
        
        # 分页处理
        total = len(reports)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_reports = reports[start:end]
        
        return jsonify({
            "success": True,
            "data": {
                "reports": paginated_reports,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"参数错误: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"获取分析报告失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取分析报告失败"
        }), 500

@data_bp.route('/health', methods=['GET'])
def health_check():
    """数据服务健康检查"""
    try:
        return jsonify({
            "success": True,
            "message": "数据服务运行正常",
            "data": {
                "status": "healthy",
                "stocks_count": len(data_service.stocks),
                "watchlists_count": len(data_service.watchlists),
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "健康检查失败"
        }), 500

@data_bp.route('/test', methods=['POST'])
def test_data_service():
    """测试数据服务功能"""
    try:
        # 测试获取股票列表
        stocks, total = data_service.get_stock_list(limit=5)
        
        # 测试搜索功能
        search_results = data_service.search_stocks("股票1", limit=3)
        
        return jsonify({
            "success": True,
            "message": "数据服务测试成功",
            "data": {
                "stocks_sample": stocks[:3],
                "total_stocks": total,
                "search_results": search_results,
                "market_summary": data_service.get_market_summary()
            }
        })
        
    except Exception as e:
        logger.error(f"数据服务测试失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "数据服务测试失败"
        }), 500








