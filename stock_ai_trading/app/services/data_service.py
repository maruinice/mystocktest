"""
数据服务

提供股票数据、行情、财务数据、市场指标等功能
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import random
from sqlalchemy import text

from app.models.stock import Stock, StockQuote, FinancialData, MarketIndicator
from app.models.stock_models import StockBasic
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


class DataService:
    """数据服务类"""
    
    def __init__(self):
        """初始化数据服务"""
        # 移除内存缓存，改用数据库查询
        pass
    
    def get_stock_list(self, market: str = 'all', industry: str = '', 
                      keyword: str = '', page: int = 1, size: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        """获取股票列表（从数据库查询）"""
        try:
            from app.core.database import engine
            
            # 构建查询条件
            conditions = ["sb.list_status = 'L'"]
            params = {}
            
            # 市场筛选
            if market and market != 'all':
                if market.upper() == 'SH':
                    conditions.append("sb.market = 'SH'")
                elif market.upper() == 'SZ':
                    conditions.append("sb.market = 'SZ'")
            
            # 行业筛选
            if industry:
                conditions.append("sb.industry LIKE :industry")
                params['industry'] = f"%{industry}%"
            
            # 关键词搜索
            if keyword:
                conditions.append("(sb.ts_code LIKE :keyword OR sb.symbol LIKE :keyword OR sb.name LIKE :keyword)")
                params['keyword'] = f"%{keyword}%"
            
            where_clause = "WHERE " + " AND ".join(conditions)
            
            # 先查询总数
            count_sql = text(f"""
                SELECT COUNT(*) as total
                FROM stock_basic sb
                {where_clause}
            """)
            
            with engine.connect() as conn:
                result = conn.execute(count_sql, params)
                total = result.fetchone()[0]
            
            # 查询分页数据
            offset = (page - 1) * size
            params['limit'] = size
            params['offset'] = offset
            
            query_sql = text(f"""
                SELECT 
                    sb.ts_code, sb.symbol, sb.name, sb.area, sb.industry, 
                    sb.market, sb.list_date, sb.is_hs,
                    dq.close_price as current_price,
                    dq.change_pct as change_percent,
                    dq.pe, dq.pb, dq.market_cap
                FROM stock_basic sb
                LEFT JOIN daily_quotes dq ON sb.ts_code = dq.ts_code
                    AND dq.trade_date = (
                        SELECT MAX(trade_date) 
                        FROM daily_quotes 
                        WHERE ts_code = sb.ts_code
                    )
                {where_clause}
                ORDER BY sb.ts_code
                LIMIT :limit OFFSET :offset
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query_sql, params)
                rows = result.fetchall()
            
            # 转换为字典列表
            stocks = []
            for row in rows:
                change_percent = float(row[9]) / 100.0 if row[9] else 0.0
                
                stocks.append({
                    'code': row[0],  # ts_code
                    'symbol': row[1],  # 6位代码
                    'name': row[2],
                    'area': row[3],
                    'industry': row[4],
                    'market': row[5],
                    'listing_date': str(row[6]) if row[6] else None,
                    'is_hs': row[7],
                    'current_price': float(row[8]) if row[8] else 0.0,
                    'change_percent': change_percent,
                    'pe_ratio': float(row[10]) if row[10] else 0.0,
                    'pb_ratio': float(row[11]) if row[11] else 0.0,
                    'market_cap': float(row[12]) if row[12] else 0.0,
                    'status': 'active',
                    'type': 'stock'
                })
            
            logger.info(f"获取股票列表: market={market}, industry={industry}, keyword={keyword}, "
                       f"page={page}, size={size}, total={total}, returned={len(stocks)}")
            return stocks, total
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}", exc_info=True)
            return [], 0
    
    def get_stock_quotes(self, code: str, period: str = 'day', 
                        start_date: str = '', end_date: str = '', 
                        limit: int = 100) -> List[StockQuote]:
        """获取股票行情数据（从数据库查询）"""
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            # 处理股票代码（支持带后缀和不带后缀）
            if '.' in code:
                ts_code = code
            else:
                # 根据代码前缀判断市场
                if code.startswith('6'):
                    ts_code = f"{code}.SH"
                elif code.startswith(('0', '3')):
                    ts_code = f"{code}.SZ"
                else:
                    ts_code = code
            
            conditions.append("ts_code = :ts_code")
            params['ts_code'] = ts_code
            
            # 日期范围条件（trade_date是DATE类型，格式为'YYYY-MM-DD'）
            if start_date:
                conditions.append("trade_date >= :start_date")
                params['start_date'] = start_date  # 保持YYYY-MM-DD格式
            
            if end_date:
                conditions.append("trade_date <= :end_date")
                params['end_date'] = end_date  # 保持YYYY-MM-DD格式
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 构建SQL查询（注意：表中没有amplitude字段，需要计算）
            sql = text(f"""
                SELECT 
                    ts_code, trade_date, open_price, high_price, low_price, close_price,
                    pre_close, change_amount, change_pct, volume, amount, 
                    turnover_rate
                FROM daily_history
                {where_clause}
                ORDER BY trade_date DESC
                LIMIT :limit
            """)
            params['limit'] = limit
            
            # 执行查询
            from app.core.database import engine
            with engine.connect() as conn:
                result = conn.execute(sql, params)
                rows = result.fetchall()
            
            # 转换为StockQuote对象列表
            quotes = []
            for row in rows:
                # 处理日期格式：数据库返回的是date对象或字符串
                if isinstance(row[1], str):
                    trade_date = datetime.strptime(row[1], '%Y-%m-%d').date()
                else:
                    # row[1]已经是date对象
                    trade_date = row[1]
                
                # 涨跌幅转换：数据库存储的是百分比，需要转为小数
                change_percent = float(row[8]) / 100.0 if row[8] else 0.0
                
                # 计算振幅：(最高价 - 最低价) / 昨收价 * 100
                high_price = float(row[3]) if row[3] else 0.0
                low_price = float(row[4]) if row[4] else 0.0
                pre_close = float(row[6]) if row[6] else 0.0
                amplitude = ((high_price - low_price) / pre_close * 100) if pre_close > 0 else 0.0
                
                quote = StockQuote(
                    code=code,
                    date=trade_date,
                    open_price=float(row[2]) if row[2] else 0.0,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=float(row[5]) if row[5] else 0.0,
                    volume=int(row[9]) if row[9] else 0,
                    turnover=float(row[10]) if row[10] else 0.0,
                    change_amount=float(row[7]) if row[7] else 0.0,
                    change_percent=change_percent,
                    amplitude=amplitude,
                    turnover_rate=float(row[11]) if row[11] else 0.0
                )
                quotes.append(quote)
            
            # 按日期升序返回（K线图需要从旧到新）
            quotes.reverse()
            
            logger.info(f"查询股票行情: code={code}, period={period}, 找到 {len(quotes)} 条记录")
            return quotes
            
        except Exception as e:
            logger.error(f"获取股票行情失败: {str(e)}")
            return []
    
    def get_realtime_quote(self, code: str) -> Optional[Dict[str, Any]]:
        """获取实时行情（返回最新一日的行情数据）"""
        try:
            from app.core.database import engine
            
            # 处理股票代码
            if '.' not in code:
                if code.startswith('6'):
                    ts_code = f"{code}.SH"
                elif code.startswith(('0', '3')):
                    ts_code = f"{code}.SZ"
                else:
                    ts_code = code
            else:
                ts_code = code
            
            # 查询最新一日的行情数据
            sql = text("""
                SELECT 
                    ts_code, trade_date, open_price, high_price, low_price, close_price,
                    pre_close, change_amount, change_pct, volume, amount, 
                    turnover_rate, pe, pb
                FROM daily_history
                WHERE ts_code = :ts_code
                ORDER BY trade_date DESC
                LIMIT 1
            """)
            
            with engine.connect() as conn:
                result = conn.execute(sql, {'ts_code': ts_code})
                row = result.fetchone()
            
            if not row:
                logger.warning(f"未找到股票行情: {code}")
                return None
            
            # 涨跌幅转换
            change_percent = float(row[8]) / 100.0 if row[8] else 0.0
            
            # 计算振幅
            high_price = float(row[3]) if row[3] else 0.0
            low_price = float(row[4]) if row[4] else 0.0
            pre_close = float(row[6]) if row[6] else 0.0
            amplitude = ((high_price - low_price) / pre_close * 100) if pre_close > 0 else 0.0
            
            quote = {
                'code': code,
                'date': str(row[1]),
                'open_price': float(row[2]) if row[2] else 0.0,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': float(row[5]) if row[5] else 0.0,
                'pre_close': pre_close,
                'change_amount': float(row[7]) if row[7] else 0.0,
                'change_percent': change_percent,
                'volume': int(row[9]) if row[9] else 0,
                'turnover': float(row[10]) if row[10] else 0.0,
                'turnover_rate': float(row[11]) if row[11] else 0.0,
                'amplitude': amplitude,
                'pe_ratio': float(row[12]) if row[12] else 0.0,
                'pb_ratio': float(row[13]) if row[13] else 0.0,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"获取实时行情: code={code}, price={quote['close_price']}, date={quote['date']}")
            return quote
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {str(e)}", exc_info=True)
            return None
    
    def get_stock_financials(self, code: str, report_type: str = 'annual', 
                           year: str = '', limit: int = 10) -> List[Dict[str, Any]]:
        """获取股票财务数据（暂时返回空列表，待实现）"""
        try:
            # TODO: 从数据库查询财务数据
            # 当前数据库可能没有财务数据表，返回空列表
            logger.info(f"获取财务数据: code={code}, type={report_type}, year={year} (暂未实现)")
            return []
        except Exception as e:
            logger.error(f"获取财务数据失败: {str(e)}", exc_info=True)
            return []
    
    def get_market_indicators(self, indicator_type: str = 'all', 
                            start_date: str = '', end_date: str = '') -> List[Dict[str, Any]]:
        """获取市场指标（暂时返回空列表，待实现）"""
        try:
            # TODO: 从数据库查询市场指标数据
            logger.info(f"获取市场指标: type={indicator_type} (暂未实现)")
            return []
        except Exception as e:
            logger.error(f"获取市场指标失败: {str(e)}", exc_info=True)
            return []
    
    def get_market_summary(self) -> Dict[str, Any]:
        """获取市场概览（基于数据库统计）"""
        try:
            from app.core.database import engine
            
            # 统计总股票数
            count_sql = text("SELECT COUNT(*) FROM stock_basic WHERE list_status = 'L'")
            with engine.connect() as conn:
                result = conn.execute(count_sql)
                total_stocks = result.fetchone()[0]
            
            # 获取最新交易日
            date_sql = text("SELECT MAX(trade_date) FROM daily_quotes")
            with engine.connect() as conn:
                result = conn.execute(date_sql)
                trading_date = result.fetchone()[0]
                trading_date_str = str(trading_date) if trading_date else datetime.now().strftime('%Y-%m-%d')
            
            # 统计涨跌股票数（基于最新交易日）
            stats_sql = text("""
                SELECT 
                    COUNT(CASE WHEN change_pct > 0 THEN 1 END) as rising,
                    COUNT(CASE WHEN change_pct < 0 THEN 1 END) as falling,
                    COUNT(CASE WHEN change_pct = 0 THEN 1 END) as unchanged,
                    SUM(amount) as total_turnover,
                    SUM(volume) as total_volume
                FROM daily_quotes
                WHERE trade_date = :trade_date
            """)
            
            with engine.connect() as conn:
                result = conn.execute(stats_sql, {'trade_date': trading_date_str})
                stats_row = result.fetchone()
            
            # 判断交易状态（简化版）
            now = datetime.now()
            market_status = 'closed'
            if now.weekday() < 5:  # 周一到周五
                current_time = now.time()
                if datetime.strptime('09:30', '%H:%M').time() <= current_time <= datetime.strptime('15:00', '%H:%M').time():
                    if datetime.strptime('11:30', '%H:%M').time() < current_time < datetime.strptime('13:00', '%H:%M').time():
                        market_status = 'closed'  # 午休
                    else:
                        market_status = 'open'
            
            return {
                'market_status': market_status,
                'trading_date': trading_date_str,
                'indices': {
                    'shanghai': {
                        'name': '上证指数',
                        'code': '000001.SH',
                        'value': 0.0,  # TODO: 需要指数数据
                        'change': 0.0,
                        'change_percent': 0.0
                    },
                    'shenzhen': {
                        'name': '深证成指',
                        'code': '399001.SZ',
                        'value': 0.0,
                        'change': 0.0,
                        'change_percent': 0.0
                    }
                },
                'market_stats': {
                    'total_stocks': total_stocks,
                    'rising_stocks': int(stats_row[0]) if stats_row and stats_row[0] else 0,
                    'falling_stocks': int(stats_row[1]) if stats_row and stats_row[1] else 0,
                    'unchanged_stocks': int(stats_row[2]) if stats_row and stats_row[2] else 0,
                    'total_turnover': float(stats_row[3]) if stats_row and stats_row[3] else 0.0,
                    'total_volume': int(stats_row[4]) if stats_row and stats_row[4] else 0
                },
                'hot_sectors': []  # TODO: 需要行业数据
            }
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {str(e)}", exc_info=True)
            return {
                'market_status': 'unknown',
                'trading_date': datetime.now().strftime('%Y-%m-%d'),
                'indices': {},
                'market_stats': {},
                'hot_sectors': []
            }
    
    def search_stocks(self, keyword: str, search_type: str = 'all', 
                     limit: int = 20) -> List[Dict[str, Any]]:
        """搜索股票 - 从数据库查询（包含最新价格信息）"""
        try:
            from app.core.database import engine
            keyword_pattern = f"%{keyword}%"
            
            # 构建SQL查询条件
            if search_type == 'code':
                where_clause = "WHERE sb.list_status = 'L' AND (sb.ts_code LIKE :keyword OR sb.symbol LIKE :keyword)"
            elif search_type == 'name':
                where_clause = "WHERE sb.list_status = 'L' AND sb.name LIKE :keyword"
            elif search_type == 'pinyin':
                where_clause = "WHERE sb.list_status = 'L' AND (sb.cnspell LIKE :keyword OR sb.name LIKE :keyword)"
            else:
                # 'all' 类型：搜索代码、名称和拼音
                where_clause = """WHERE sb.list_status = 'L' AND 
                    (sb.ts_code LIKE :keyword OR sb.symbol LIKE :keyword OR 
                     sb.name LIKE :keyword OR sb.cnspell LIKE :keyword)"""
            
            # 联合查询基本信息和最新行情数据
            sql = text(f"""
                SELECT 
                    sb.ts_code, sb.symbol, sb.name, sb.market, sb.exchange, sb.industry,
                    dq.close_price as current_price,
                    dq.change_pct as change_percent,
                    dq.change_amount,
                    dq.trade_date
                FROM stock_basic sb
                LEFT JOIN daily_quotes dq ON sb.ts_code = dq.ts_code
                    AND dq.trade_date = (
                        SELECT MAX(trade_date) 
                        FROM daily_quotes 
                        WHERE ts_code = sb.ts_code
                    )
                {where_clause}
                LIMIT :limit
            """)
            
            with engine.connect() as conn:
                result = conn.execute(sql, {'keyword': keyword_pattern, 'limit': limit})
                rows = result.fetchall()
            
            # 转换为字典格式
            results = []
            for row in rows:
                # 涨跌幅转换：数据库中存储的是百分比形式（如-1.6298），需要除以100转为小数形式（-0.016298）
                change_percent = float(row[7]) / 100.0 if row[7] else 0.0
                
                results.append({
                    'symbol': row[0],  # ts_code
                    'code': row[1],    # symbol（6位代码）
                    'name': row[2],
                    'market': row[3] or row[4],
                    'industry': row[5],
                    'type': 'stock',
                    # 行情数据
                    'current_price': float(row[6]) if row[6] else 0.0,
                    'change_percent': change_percent,
                    'change': float(row[8]) if row[8] else 0.0,
                    'trade_date': str(row[9]) if row[9] else None
                })
            
            logger.info(f"搜索股票: keyword={keyword}, type={search_type}, 找到 {len(results)} 条记录")
            return results
            
        except Exception as e:
            logger.error(f"搜索股票失败: {e}", exc_info=True)
            return []
    
    def get_stock_info(self, code: str) -> Optional[Dict[str, Any]]:
        """获取股票详细信息 - 从数据库查询（包含基本信息和最新行情）"""
        try:
            from app.core.database import engine
            
            # 支持完整代码（如603387.SH）和简码（如603387）
            # 联合查询股票基本信息和最新行情数据
            sql = text("""
                SELECT 
                    sb.ts_code, sb.symbol, sb.name, sb.area, sb.industry, sb.fullname, 
                    sb.market, sb.exchange, sb.list_date, sb.is_hs,
                    dq.close_price as current_price,
                    dq.open_price, dq.high_price, dq.low_price,
                    dq.pre_close, dq.change_amount, dq.change_pct,
                    dq.volume, dq.amount, dq.turnover_rate,
                    dq.pe, dq.pb, dq.market_cap, dq.trade_date
                FROM stock_basic sb
                LEFT JOIN daily_quotes dq ON sb.ts_code = dq.ts_code
                    AND dq.trade_date = (
                        SELECT MAX(trade_date) 
                        FROM daily_quotes 
                        WHERE ts_code = sb.ts_code
                    )
                WHERE sb.list_status = 'L' AND (sb.ts_code = :code OR sb.symbol = :code)
                LIMIT 1
            """)
            
            with engine.connect() as conn:
                result = conn.execute(sql, {'code': code})
                row = result.fetchone()
            
            if not row:
                logger.warning(f"股票不存在: {code}")
                return None
            
            # 转换为字典格式（包含基本信息和行情数据）
            # 涨跌幅转换：数据库中存储的是百分比形式（如-1.6298），需要除以100转为小数形式（-0.016298）
            change_percent = float(row[16]) / 100.0 if row[16] else 0.0
            
            stock_info = {
                # 基本信息
                'symbol': row[0],        # ts_code (603387.SH)
                'code': row[1],          # symbol (603387)
                'name': row[2],
                'area': row[3],
                'industry': row[4],
                'fullname': row[5],
                'market': row[6] or row[7],
                'exchange': row[7],
                'list_date': row[8],
                'is_hs': row[9],
                'type': 'stock',
                # 行情数据（如果有）
                'current_price': float(row[10]) if row[10] else 0.0,
                'open_price': float(row[11]) if row[11] else 0.0,
                'high_price': float(row[12]) if row[12] else 0.0,
                'low_price': float(row[13]) if row[13] else 0.0,
                'pre_close': float(row[14]) if row[14] else 0.0,
                'change': float(row[15]) if row[15] else 0.0,
                'change_percent': change_percent,
                'volume': int(row[17]) if row[17] else 0,
                'amount': float(row[18]) if row[18] else 0.0,
                'turnover_rate': float(row[19]) if row[19] else 0.0,
                'pe': float(row[20]) if row[20] else 0.0,
                'pb': float(row[21]) if row[21] else 0.0,
                'market_cap': float(row[22]) if row[22] else 0.0,
                'trade_date': str(row[23]) if row[23] else None
            }
            
            logger.info(f"获取股票信息: code={code}, name={stock_info['name']}, price={stock_info['current_price']}")
            return stock_info
            
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}", exc_info=True)
            return None
    
    def get_user_watchlist(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户自选股（从数据库查询）"""
        try:
            from app.core.database import engine
            
            # 查询用户自选股
            sql = text("""
                SELECT 
                    w.stock_code, w.added_at,
                    sb.symbol, sb.name, sb.industry, sb.market,
                    dq.close_price as current_price,
                    dq.change_pct as change_percent,
                    dq.change_amount,
                    dq.trade_date
                FROM user_watchlist w
                JOIN stock_basic sb ON w.stock_code = sb.ts_code
                LEFT JOIN daily_quotes dq ON sb.ts_code = dq.ts_code
                    AND dq.trade_date = (
                        SELECT MAX(trade_date) 
                        FROM daily_quotes 
                        WHERE ts_code = sb.ts_code
                    )
                WHERE w.user_id = :user_id
                ORDER BY w.added_at DESC
            """)
            
            with engine.connect() as conn:
                result = conn.execute(sql, {'user_id': user_id})
                rows = result.fetchall()
            
            watchlist = []
            for row in rows:
                change_percent = float(row[7]) / 100.0 if row[7] else 0.0
                
                watchlist.append({
                    'code': row[0],
                    'symbol': row[2],
                    'name': row[3],
                    'industry': row[4],
                    'market': row[5],
                    'current_price': float(row[6]) if row[6] else 0.0,
                    'change_percent': change_percent,
                    'change_amount': float(row[8]) if row[8] else 0.0,
                    'trade_date': str(row[9]) if row[9] else None,
                    'added_at': str(row[1])
                })
            
            logger.info(f"获取自选股: user_id={user_id}, count={len(watchlist)}")
            return watchlist
            
        except Exception as e:
            logger.error(f"获取自选股失败: {str(e)}", exc_info=True)
            return []
    
    def add_to_watchlist(self, user_id: int, code: str) -> bool:
        """添加股票到自选股（写入数据库）"""
        try:
            from app.core.database import engine
            
            # 检查是否已存在
            check_sql = text("""
                SELECT COUNT(*) FROM user_watchlist 
                WHERE user_id = :user_id AND stock_code = :code
            """)
            
            with engine.connect() as conn:
                result = conn.execute(check_sql, {'user_id': user_id, 'code': code})
                exists = result.fetchone()[0] > 0
            
            if exists:
                logger.info(f"自选股已存在: user_id={user_id}, code={code}")
                return False
            
            # 插入自选股
            insert_sql = text("""
                INSERT INTO user_watchlist (user_id, stock_code, added_at)
                VALUES (:user_id, :code, NOW())
            """)
            
            with engine.begin() as conn:
                conn.execute(insert_sql, {'user_id': user_id, 'code': code})
            
            logger.info(f"添加自选股成功: user_id={user_id}, code={code}")
            return True
            
        except Exception as e:
            logger.error(f"添加自选股失败: {str(e)}", exc_info=True)
            return False
    
    def remove_from_watchlist(self, user_id: int, code: str) -> bool:
        """从自选股中移除股票（从数据库删除）"""
        try:
            from app.core.database import engine
            
            delete_sql = text("""
                DELETE FROM user_watchlist 
                WHERE user_id = :user_id AND stock_code = :code
            """)
            
            with engine.begin() as conn:
                result = conn.execute(delete_sql, {'user_id': user_id, 'code': code})
                affected_rows = result.rowcount
            
            if affected_rows > 0:
                logger.info(f"移除自选股成功: user_id={user_id}, code={code}")
                return True
            else:
                logger.info(f"自选股不存在: user_id={user_id}, code={code}")
                return False
            
        except Exception as e:
            logger.error(f"移除自选股失败: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def is_trading_time() -> Tuple[bool, str]:
        """
        判断当前是否为A股交易时间
        
        Returns:
            Tuple[bool, str]: (是否可交易, 状态描述)
        """
        from datetime import time
        
        now = datetime.now()
        
        # 检查是否为工作日（周一=0到周五=4）
        if now.weekday() >= 5:
            return False, "非交易日（周末）"
        
        # TODO: 添加节假日判断（需要节假日数据表或API）
        
        # 获取当前时间
        current_time = now.time()
        
        # 开盘集合竞价时间：9:15-9:25
        if time(9, 15) <= current_time <= time(9, 25):
            return True, "开盘集合竞价时间（仅限价单）"
        
        # 上午交易时间：9:30-11:30
        if time(9, 30) <= current_time <= time(11, 30):
            return True, "上午交易时间"
        
        # 午间休市：11:30-13:00
        if time(11, 30) < current_time < time(13, 0):
            return False, "午间休市时间"
        
        # 下午交易时间：13:00-14:57
        if time(13, 0) <= current_time < time(14, 57):
            return True, "下午交易时间"
        
        # 尾盘集合竞价时间：14:57-15:00
        if time(14, 57) <= current_time <= time(15, 0):
            return True, "尾盘集合竞价时间"
        
        # 盘后时间
        if current_time > time(15, 0):
            return False, "收盘后（当日交易结束）"
        
        # 盘前时间
        return False, "未开盘（交易日盘前）"
    
    @staticmethod
    def get_market_status() -> str:
        """
        获取当前市场状态
        
        Returns:
            str: 市场状态 (pre_market, open, closed, after_market)
        """
        is_trading, _ = DataService.is_trading_time()
        
        if not is_trading:
            now = datetime.now()
            if now.weekday() >= 5:
                return "closed"  # 周末
            
            current_time = now.time()
            if current_time < datetime.strptime('09:15', '%H:%M').time():
                return "pre_market"  # 盘前
            elif current_time > datetime.strptime('15:00', '%H:%M').time():
                return "after_market"  # 盘后
            else:
                return "closed"  # 午休
        
        return "open"  # 交易中