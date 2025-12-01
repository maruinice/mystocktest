"""
市场热点服务
提供市场热点数据，包括涨跌幅榜、成交量榜、板块热点等
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import text, desc
from decimal import Decimal
import tushare as ts
import requests

from ..core.database import get_db

logger = logging.getLogger(__name__)


class MarketHotspotService:
    """市场热点服务"""
    
    def __init__(self):
        try:
            self.pro = ts.pro_api()
        except Exception as e:
            logger.warning(f"Tushare API初始化失败: {e}")
            self.pro = None
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://quote.eastmoney.com',
        }
        
        # 数据源优先级：东方财富 > 新浪财经 > 腾讯财经
        self.data_sources = ['eastmoney', 'sina', 'tencent']
        self.current_source_index = 0
    
    def _get_hotspots_from_eastmoney(self, source: str, limit: int) -> List[Dict[str, Any]]:
        """从东方财富获取实时热点"""
        try:
            # 根据source类型选择排序字段
            sort_field_map = {
                'gainers': 'f3',    # 涨幅榜
                'losers': 'f3',     # 跌幅榜
                'volume': 'f5',     # 成交量榜
                'turnover': 'f8',   # 换手率榜
            }
            
            sort_field = sort_field_map.get(source, 'f3')
            sort_order = 0 if source == 'losers' else 1  # 0:升序, 1:降序
            
            url = 'http://push2.eastmoney.com/api/qt/clist/get'
            params = {
                'pn': 1,
                'pz': limit,
                'po': sort_order,
                'np': 1,
                'fltt': 2,
                'invt': 2,
                'fid': sort_field,
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',  # A股
                'fields': 'f12,f14,f2,f3,f4,f5,f6,f8,f15,f16,f17,f18',
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('data') and result['data'].get('diff'):
                    hotspots = []
                    for item in result['data']['diff']:
                        hotspots.append({
                            'code': item.get('f12', ''),
                            'name': item.get('f14', ''),
                            'price': item.get('f2', 0),            # 最新价
                            'change_pct': item.get('f3', 0),       # 涨跌幅%
                            'change': item.get('f4', 0),           # 涨跌额
                            'volume': item.get('f5', 0),           # 成交量（手）
                            'amount': item.get('f6', 0),           # 成交额
                            'turnover_rate': item.get('f8', 0),    # 换手率%
                            'high': item.get('f15', 0),            # 最高价
                            'low': item.get('f16', 0),             # 最低价
                            'open': item.get('f17', 0),            # 开盘价
                            'close': item.get('f18', 0),           # 昨收价
                            'type': source,
                            'source': 'eastmoney'
                        })
                    
                    logger.info(f"从东方财富获取实时{source}榜成功，共{len(hotspots)}条")
                    return hotspots
            
            return []
        except Exception as e:
            logger.warning(f"从东方财富获取热点失败: {e}")
            return []
    
    def _get_hotspots_from_sina(self, source: str, limit: int) -> List[Dict[str, Any]]:
        """从新浪财经获取实时热点"""
        try:
            # 新浪财经的热点榜单API
            # 涨幅榜: up, 跌幅榜: down, 成交量榜: volume, 换手率榜: turnover
            source_map = {
                'gainers': 'up',
                'losers': 'down',
                'volume': 'volume',
                'turnover': 'turnover'
            }
            
            sina_source = source_map.get(source, 'up')
            url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData'
            params = {
                'page': 1,
                'num': limit,
                'sort': 'changepercent' if source in ['gainers', 'losers'] else 'volume' if source == 'volume' else 'turnoverratio',
                'asc': 0 if source == 'losers' else 1,
                'node': 'hs_a',
                'symbol': '',
                '_s_r_a': 'page'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200 and response.text:
                import json
                # 新浪返回的是JavaScript数组格式，需要解析
                data = json.loads(response.text)
                if data:
                    hotspots = []
                    for item in data[:limit]:
                        try:
                            hotspots.append({
                                'code': item.get('code', ''),
                                'name': item.get('name', ''),
                                'price': float(item.get('trade', 0)),
                                'change_pct': float(item.get('changepercent', 0)),
                                'change': float(item.get('pricechange', 0)),
                                'volume': int(float(item.get('volume', 0))),
                                'amount': float(item.get('amount', 0)),
                                'turnover_rate': float(item.get('turnoverratio', 0)),
                                'high': float(item.get('high', 0)),
                                'low': float(item.get('low', 0)),
                                'open': float(item.get('open', 0)),
                                'close': float(item.get('settlement', 0)),
                                'type': source,
                                'source': 'sina'
                            })
                        except (ValueError, TypeError) as e:
                            logger.warning(f"解析新浪数据项失败: {e}")
                            continue
                    
                    logger.info(f"从新浪财经获取实时{source}榜成功，共{len(hotspots)}条")
                    return hotspots
            
            return []
        except Exception as e:
            logger.warning(f"从新浪财经获取热点失败: {e}")
            return []
    
    def _get_hotspots_from_tencent(self, source: str, limit: int) -> List[Dict[str, Any]]:
        """从腾讯财经获取实时热点"""
        try:
            # 腾讯财经的热点榜单API
            # 使用腾讯的行情中心API
            sort_map = {
                'gainers': 'changePercent',   # 涨幅
                'losers': 'changePercent',    # 跌幅
                'volume': 'volume',           # 成交量
                'turnover': 'turnoverRate'    # 换手率
            }
            
            sort_field = sort_map.get(source, 'changePercent')
            sort_order = 'asc' if source == 'losers' else 'desc'
            
            url = 'http://qt.gtimg.cn/q='
            # 获取沪深A股的热点股票列表
            # 这里使用一个技巧：先获取指数成分股，然后排序
            # 实际上腾讯没有直接的热点榜单API，这里作为备用数据源
            
            # 使用腾讯的批量查询接口
            # 由于腾讯没有直接的榜单API，这里返回空，让系统切换到其他数据源
            logger.info("腾讯财经暂不支持热点榜单，跳过")
            return []
            
        except Exception as e:
            logger.warning(f"从腾讯财经获取热点失败: {e}")
            return []
    
    def get_realtime_hotspots(self, source: str = 'gainers', limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取实时市场热点（多数据源自动切换）
        
        Args:
            source: 数据源类型 (gainers/losers/volume/turnover)
            limit: 返回数量
            
        Returns:
            实时热点列表
        """
        # 尝试所有数据源
        for i, data_source in enumerate(self.data_sources):
            try:
                logger.info(f"尝试从{data_source}获取实时热点数据...")
                
                if data_source == 'eastmoney':
                    hotspots = self._get_hotspots_from_eastmoney(source, limit)
                elif data_source == 'sina':
                    hotspots = self._get_hotspots_from_sina(source, limit)
                elif data_source == 'tencent':
                    hotspots = self._get_hotspots_from_tencent(source, limit)
                else:
                    continue
                
                # 如果成功获取到数据，返回
                if hotspots and len(hotspots) > 0:
                    self.current_source_index = i  # 记录成功的数据源
                    return hotspots
                    
            except Exception as e:
                logger.warning(f"从{data_source}获取数据失败: {e}")
                continue
        
        # 所有数据源都失败
        logger.error("所有实时数据源都无法获取热点数据")
        return []
    
    def get_top_gainers(self, limit: int = 10, trade_date: str = None) -> List[Dict[str, Any]]:
        """
        获取涨幅榜
        
        Args:
            limit: 返回数量
            trade_date: 交易日期 (YYYYMMDD)，默认为最新交易日
            
        Returns:
            涨幅榜列表
        """
        try:
            db = next(get_db())
            
            # 如果没有指定日期，获取最新交易日
            if not trade_date:
                cal_query = text("""
                    SELECT cal_date FROM trade_cal 
                    WHERE is_open = 1 AND cal_date <= :today
                    ORDER BY cal_date DESC LIMIT 1
                """)
                result = db.execute(cal_query, {'today': datetime.now().strftime('%Y%m%d')}).fetchone()
                trade_date = result[0] if result else datetime.now().strftime('%Y%m%d')
            
            # 从 daily_history 和 daily_basic 表联合查询
            query = text("""
                SELECT 
                    dh.ts_code,
                    sb.name,
                    dh.close_price,
                    dh.change_pct,
                    db.turnover_rate,
                    db.volume_ratio,
                    db.pe,
                    db.total_mv
                FROM daily_history dh
                LEFT JOIN stock_basic sb ON dh.ts_code = sb.ts_code
                LEFT JOIN daily_basic db ON dh.ts_code = db.ts_code AND dh.trade_date = db.trade_date
                WHERE dh.trade_date = :trade_date
                AND dh.change_pct IS NOT NULL
                AND sb.list_status = 'L'
                ORDER BY dh.change_pct DESC
                LIMIT :limit
            """)
            
            results = db.execute(query, {'trade_date': trade_date, 'limit': limit}).fetchall()
            
            hotspots = []
            for row in results:
                hotspots.append({
                    'code': row[0].split('.')[0] if row[0] else '',
                    'name': row[1] or '',
                    'price': float(row[2]) if row[2] else 0.0,
                    'change_pct': float(row[3]) if row[3] else 0.0,
                    'turnover_rate': float(row[4]) if row[4] else 0.0,
                    'volume_ratio': float(row[5]) if row[5] else 0.0,
                    'pe': float(row[6]) if row[6] else 0.0,
                    'market_value': float(row[7]) if row[7] else 0.0,
                    'type': 'gainer'
                })
            
            return hotspots
            
        except Exception as e:
            logger.error(f"获取涨幅榜失败: {e}", exc_info=True)
            return []
        finally:
            db.close()
    
    def get_top_losers(self, limit: int = 10, trade_date: str = None) -> List[Dict[str, Any]]:
        """
        获取跌幅榜
        
        Args:
            limit: 返回数量
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            跌幅榜列表
        """
        try:
            db = next(get_db())
            
            if not trade_date:
                cal_query = text("""
                    SELECT cal_date FROM trade_cal 
                    WHERE is_open = 1 AND cal_date <= :today
                    ORDER BY cal_date DESC LIMIT 1
                """)
                result = db.execute(cal_query, {'today': datetime.now().strftime('%Y%m%d')}).fetchone()
                trade_date = result[0] if result else datetime.now().strftime('%Y%m%d')
            
            query = text("""
                SELECT 
                    dh.ts_code,
                    sb.name,
                    dh.close_price,
                    dh.change_pct,
                    db.turnover_rate,
                    db.volume_ratio,
                    db.pe,
                    db.total_mv
                FROM daily_history dh
                LEFT JOIN stock_basic sb ON dh.ts_code = sb.ts_code
                LEFT JOIN daily_basic db ON dh.ts_code = db.ts_code AND dh.trade_date = db.trade_date
                WHERE dh.trade_date = :trade_date
                AND dh.change_pct IS NOT NULL
                AND sb.list_status = 'L'
                ORDER BY dh.change_pct ASC
                LIMIT :limit
            """)
            
            results = db.execute(query, {'trade_date': trade_date, 'limit': limit}).fetchall()
            
            hotspots = []
            for row in results:
                hotspots.append({
                    'code': row[0].split('.')[0] if row[0] else '',
                    'name': row[1] or '',
                    'price': float(row[2]) if row[2] else 0.0,
                    'change_pct': float(row[3]) if row[3] else 0.0,
                    'turnover_rate': float(row[4]) if row[4] else 0.0,
                    'volume_ratio': float(row[5]) if row[5] else 0.0,
                    'pe': float(row[6]) if row[6] else 0.0,
                    'market_value': float(row[7]) if row[7] else 0.0,
                    'type': 'loser'
                })
            
            return hotspots
            
        except Exception as e:
            logger.error(f"获取跌幅榜失败: {e}", exc_info=True)
            return []
        finally:
            db.close()
    
    def get_top_volume(self, limit: int = 10, trade_date: str = None) -> List[Dict[str, Any]]:
        """
        获取成交量榜
        
        Args:
            limit: 返回数量
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            成交量榜列表
        """
        try:
            db = next(get_db())
            
            if not trade_date:
                cal_query = text("""
                    SELECT cal_date FROM trade_cal 
                    WHERE is_open = 1 AND cal_date <= :today
                    ORDER BY cal_date DESC LIMIT 1
                """)
                result = db.execute(cal_query, {'today': datetime.now().strftime('%Y%m%d')}).fetchone()
                trade_date = result[0] if result else datetime.now().strftime('%Y%m%d')
            
            query = text("""
                SELECT 
                    dh.ts_code,
                    sb.name,
                    dh.close_price,
                    dh.change_pct,
                    dh.volume,
                    dh.amount,
                    db.turnover_rate,
                    db.volume_ratio
                FROM daily_history dh
                LEFT JOIN stock_basic sb ON dh.ts_code = sb.ts_code
                LEFT JOIN daily_basic db ON dh.ts_code = db.ts_code AND dh.trade_date = db.trade_date
                WHERE dh.trade_date = :trade_date
                AND dh.volume IS NOT NULL
                AND sb.list_status = 'L'
                ORDER BY dh.volume DESC
                LIMIT :limit
            """)
            
            results = db.execute(query, {'trade_date': trade_date, 'limit': limit}).fetchall()
            
            hotspots = []
            for row in results:
                hotspots.append({
                    'code': row[0].split('.')[0] if row[0] else '',
                    'name': row[1] or '',
                    'price': float(row[2]) if row[2] else 0.0,
                    'change_pct': float(row[3]) if row[3] else 0.0,
                    'volume': float(row[4]) if row[4] else 0.0,
                    'amount': float(row[5]) if row[5] else 0.0,
                    'turnover_rate': float(row[6]) if row[6] else 0.0,
                    'volume_ratio': float(row[7]) if row[7] else 0.0,
                    'type': 'volume'
                })
            
            return hotspots
            
        except Exception as e:
            logger.error(f"获取成交量榜失败: {e}", exc_info=True)
            return []
        finally:
            db.close()
    
    def get_top_turnover(self, limit: int = 10, trade_date: str = None) -> List[Dict[str, Any]]:
        """
        获取换手率榜
        
        Args:
            limit: 返回数量
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            换手率榜列表
        """
        try:
            db = next(get_db())
            
            if not trade_date:
                cal_query = text("""
                    SELECT cal_date FROM trade_cal 
                    WHERE is_open = 1 AND cal_date <= :today
                    ORDER BY cal_date DESC LIMIT 1
                """)
                result = db.execute(cal_query, {'today': datetime.now().strftime('%Y%m%d')}).fetchone()
                trade_date = result[0] if result else datetime.now().strftime('%Y%m%d')
            
            query = text("""
                SELECT 
                    db.ts_code,
                    sb.name,
                    dh.close_price,
                    dh.change_pct,
                    db.turnover_rate,
                    db.volume_ratio,
                    dh.volume,
                    dh.amount
                FROM daily_basic db
                LEFT JOIN stock_basic sb ON db.ts_code = sb.ts_code
                LEFT JOIN daily_history dh ON db.ts_code = dh.ts_code AND db.trade_date = dh.trade_date
                WHERE db.trade_date = :trade_date
                AND db.turnover_rate IS NOT NULL
                AND sb.list_status = 'L'
                ORDER BY db.turnover_rate DESC
                LIMIT :limit
            """)
            
            results = db.execute(query, {'trade_date': trade_date, 'limit': limit}).fetchall()
            
            hotspots = []
            for row in results:
                hotspots.append({
                    'code': row[0].split('.')[0] if row[0] else '',
                    'name': row[1] or '',
                    'price': float(row[2]) if row[2] else 0.0,
                    'change_pct': float(row[3]) if row[3] else 0.0,
                    'turnover_rate': float(row[4]) if row[4] else 0.0,
                    'volume_ratio': float(row[5]) if row[5] else 0.0,
                    'volume': float(row[6]) if row[6] else 0.0,
                    'amount': float(row[7]) if row[7] else 0.0,
                    'type': 'turnover'
                })
            
            return hotspots
            
        except Exception as e:
            logger.error(f"获取换手率榜失败: {e}", exc_info=True)
            return []
        finally:
            db.close()
    
    def get_market_hotspots(self, source: str = 'gainers', limit: int = 10) -> Dict[str, Any]:
        """
        获取市场热点（仅使用实时数据）
        
        Args:
            source: 数据源类型 (gainers/losers/volume/turnover)
            limit: 返回数量
            
        Returns:
            市场热点数据
        """
        try:
            # 只使用实时数据，不再降级到数据库
            data = self.get_realtime_hotspots(source, limit)
            
            if data and len(data) > 0:
                logger.info(f"成功获取实时{source}榜数据，共{len(data)}条")
                return {
                    'success': True,
                    'data': {
                        'source': source,
                        'hotspots': data,
                        'update_time': datetime.now().isoformat(),
                        'data_source': data[0].get('source', 'realtime') if data else 'realtime'
                    }
                }
            else:
                # 所有实时数据源都失败
                logger.error(f"所有实时数据源都无法获取{source}榜数据")
                return {
                    'success': False,
                    'message': '暂时无法获取实时市场数据，请稍后重试',
                    'data': {
                        'source': source,
                        'hotspots': [],
                        'update_time': datetime.now().isoformat(),
                        'data_source': 'none'
                    }
                }
            
        except Exception as e:
            logger.error(f"获取市场热点失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'获取市场热点失败: {str(e)}',
                'data': {
                    'source': source,
                    'hotspots': [],
                    'update_time': datetime.now().isoformat(),
                    'data_source': 'error'
                }
            }


# 全局实例
market_hotspot_service = MarketHotspotService()
