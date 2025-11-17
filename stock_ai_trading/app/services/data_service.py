"""
数据服务

提供股票数据、行情、财务数据、市场指标等功能
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import random

from app.models.stock import Stock, StockQuote, FinancialData, MarketIndicator


class DataService:
    """数据服务类"""
    
    def __init__(self):
        """初始化数据服务"""
        self._stocks_cache = {}
        self._quotes_cache = {}
        self._financials_cache = {}
        self._watchlists = {}  # user_id -> [stock_codes]
        self._init_sample_data()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        # 示例股票数据
        sample_stocks = [
            {
                'code': '000001.SZ',
                'name': '平安银行',
                'industry': '银行',
                'market': 'sz',
                'listing_date': '1991-04-03'
            },
            {
                'code': '000002.SZ',
                'name': '万科A',
                'industry': '房地产开发',
                'market': 'sz',
                'listing_date': '1991-01-29'
            },
            {
                'code': '600000.SH',
                'name': '浦发银行',
                'industry': '银行',
                'market': 'sh',
                'listing_date': '1999-11-10'
            },
            {
                'code': '600036.SH',
                'name': '招商银行',
                'industry': '银行',
                'market': 'sh',
                'listing_date': '2002-04-09'
            },
            {
                'code': '000858.SZ',
                'name': '五粮液',
                'industry': '白酒',
                'market': 'sz',
                'listing_date': '1998-04-27'
            }
        ]
        
        for stock_data in sample_stocks:
            stock = Stock(
                code=stock_data['code'],
                name=stock_data['name'],
                industry=stock_data['industry'],
                market=stock_data['market'],
                listing_date=datetime.strptime(stock_data['listing_date'], '%Y-%m-%d').date(),
                total_shares=1000000000,  # 10亿股
                float_shares=800000000,   # 8亿股
                market_cap=50000000000,   # 500亿市值
                pe_ratio=15.5,
                pb_ratio=1.2,
                dividend_yield=0.025,
                status='active'
            )
            self._stocks_cache[stock.code] = stock
    
    def get_stock_list(self, market: str = 'all', industry: str = '', 
                      keyword: str = '', page: int = 1, size: int = 50) -> Tuple[List[Stock], int]:
        """获取股票列表"""
        stocks = list(self._stocks_cache.values())
        
        # 市场筛选
        if market != 'all':
            stocks = [s for s in stocks if s.market == market]
        
        # 行业筛选
        if industry:
            stocks = [s for s in stocks if industry.lower() in s.industry.lower()]
        
        # 关键词搜索
        if keyword:
            keyword = keyword.lower()
            stocks = [s for s in stocks if 
                     keyword in s.code.lower() or 
                     keyword in s.name.lower()]
        
        total = len(stocks)
        
        # 分页
        start = (page - 1) * size
        end = start + size
        stocks = stocks[start:end]
        
        return stocks, total
    
    def get_stock_quotes(self, code: str, period: str = 'day', 
                        start_date: str = '', end_date: str = '', 
                        limit: int = 100) -> List[StockQuote]:
        """获取股票行情数据"""
        if code not in self._stocks_cache:
            return []
        
        # 生成示例行情数据
        quotes = []
        base_price = 10.0
        base_volume = 1000000
        
        # 确定日期范围
        if start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = datetime.now()
            start = end - timedelta(days=limit)
        
        current_date = start
        current_price = base_price
        
        while current_date <= end and len(quotes) < limit:
            # 模拟价格波动
            change_pct = random.uniform(-0.05, 0.05)  # ±5%波动
            current_price *= (1 + change_pct)
            
            # 生成OHLC数据
            open_price = current_price * random.uniform(0.98, 1.02)
            high_price = max(open_price, current_price) * random.uniform(1.0, 1.03)
            low_price = min(open_price, current_price) * random.uniform(0.97, 1.0)
            close_price = current_price
            
            volume = int(base_volume * random.uniform(0.5, 2.0))
            turnover = volume * close_price
            
            quote = StockQuote(
                code=code,
                date=current_date.date(),
                open_price=round(open_price, 2),
                high_price=round(high_price, 2),
                low_price=round(low_price, 2),
                close_price=round(close_price, 2),
                volume=volume,
                turnover=round(turnover, 2),
                change_amount=round(close_price - base_price, 2),
                change_percent=round((close_price - base_price) / base_price * 100, 2),
                amplitude=round((high_price - low_price) / open_price * 100, 2),
                turnover_rate=round(volume / 800000000 * 100, 2)  # 基于流通股本
            )
            quotes.append(quote)
            
            # 下一个交易日
            current_date += timedelta(days=1)
            # 跳过周末
            while current_date.weekday() >= 5:
                current_date += timedelta(days=1)
        
        return quotes[-limit:] if quotes else []
    
    def get_realtime_quote(self, code: str) -> Optional[StockQuote]:
        """获取实时行情"""
        if code not in self._stocks_cache:
            return None
        
        # 生成实时行情数据
        base_price = 10.0
        current_price = base_price * random.uniform(0.95, 1.05)
        
        quote = StockQuote(
            code=code,
            date=datetime.now().date(),
            open_price=round(current_price * 0.99, 2),
            high_price=round(current_price * 1.02, 2),
            low_price=round(current_price * 0.98, 2),
            close_price=round(current_price, 2),
            volume=int(1000000 * random.uniform(0.5, 2.0)),
            turnover=round(current_price * 1000000, 2),
            change_amount=round(current_price - base_price, 2),
            change_percent=round((current_price - base_price) / base_price * 100, 2),
            amplitude=round(0.04 * 100, 2),  # 4%振幅
            turnover_rate=round(0.125, 2),   # 0.125%换手率
            timestamp=datetime.now()
        )
        
        return quote
    
    def get_stock_financials(self, code: str, report_type: str = 'annual', 
                           year: str = '', limit: int = 10) -> List[FinancialData]:
        """获取股票财务数据"""
        if code not in self._stocks_cache:
            return []
        
        financials = []
        current_year = datetime.now().year
        start_year = int(year) if year else current_year - limit + 1
        
        for i in range(limit):
            report_year = start_year + i
            if report_year > current_year:
                break
            
            if report_type == 'annual':
                periods = [f'{report_year}-12-31']
            else:  # quarterly
                periods = [
                    f'{report_year}-03-31',
                    f'{report_year}-06-30',
                    f'{report_year}-09-30',
                    f'{report_year}-12-31'
                ]
            
            for period in periods:
                # 生成示例财务数据
                base_revenue = 10000000000  # 100亿营收
                growth_rate = random.uniform(-0.1, 0.2)  # -10%到20%增长
                
                financial = FinancialData(
                    code=code,
                    report_date=datetime.strptime(period, '%Y-%m-%d').date(),
                    report_type=report_type,
                    revenue=round(base_revenue * (1 + growth_rate), 2),
                    net_profit=round(base_revenue * 0.1 * (1 + growth_rate), 2),
                    total_assets=round(base_revenue * 2, 2),
                    total_liabilities=round(base_revenue * 1.2, 2),
                    shareholders_equity=round(base_revenue * 0.8, 2),
                    operating_cash_flow=round(base_revenue * 0.12, 2),
                    roe=round(10 + growth_rate * 50, 2),  # ROE
                    roa=round(5 + growth_rate * 25, 2),   # ROA
                    gross_margin=round(25 + random.uniform(-2, 2), 2),
                    net_margin=round(10 + random.uniform(-1, 1), 2),
                    debt_ratio=round(60 + random.uniform(-5, 5), 2),
                    current_ratio=round(1.5 + random.uniform(-0.2, 0.2), 2),
                    eps=round(1.0 + growth_rate, 2),  # 每股收益
                    bps=round(8.0 + growth_rate * 2, 2)  # 每股净资产
                )
                financials.append(financial)
        
        return financials[-limit:]
    
    def get_market_indicators(self, indicator_type: str = 'all', 
                            start_date: str = '', end_date: str = '') -> List[MarketIndicator]:
        """获取市场指标"""
        indicators = []
        
        # 确定日期范围
        if start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = datetime.now()
            start = end - timedelta(days=30)
        
        # 生成指标数据
        indicator_configs = []
        
        if indicator_type in ['all', 'index']:
            indicator_configs.extend([
                {'name': '上证指数', 'code': '000001', 'base_value': 3000},
                {'name': '深证成指', 'code': '399001', 'base_value': 12000},
                {'name': '创业板指', 'code': '399006', 'base_value': 2500}
            ])
        
        if indicator_type in ['all', 'sector']:
            indicator_configs.extend([
                {'name': '银行指数', 'code': 'BK0475', 'base_value': 1200},
                {'name': '科技指数', 'code': 'BK0727', 'base_value': 1800}
            ])
        
        if indicator_type in ['all', 'macro']:
            indicator_configs.extend([
                {'name': 'A股总市值', 'code': 'TOTAL_CAP', 'base_value': 80000000000000},
                {'name': '成交金额', 'code': 'TURNOVER', 'base_value': 800000000000}
            ])
        
        current_date = start
        while current_date <= end:
            for config in indicator_configs:
                # 模拟指标波动
                change_pct = random.uniform(-0.02, 0.02)
                value = config['base_value'] * (1 + change_pct)
                
                indicator = MarketIndicator(
                    name=config['name'],
                    code=config['code'],
                    value=round(value, 2),
                    change_amount=round(value * change_pct, 2),
                    change_percent=round(change_pct * 100, 2),
                    date=current_date.date(),
                    category=indicator_type if indicator_type != 'all' else 'index'
                )
                indicators.append(indicator)
            
            current_date += timedelta(days=1)
        
        return indicators
    
    def get_market_summary(self) -> Dict[str, Any]:
        """获取市场概览"""
        return {
            'market_status': 'open',  # open, closed, pre_market, after_market
            'trading_date': datetime.now().strftime('%Y-%m-%d'),
            'indices': {
                'shanghai': {
                    'name': '上证指数',
                    'code': '000001',
                    'value': 3000.0 + random.uniform(-50, 50),
                    'change': random.uniform(-30, 30),
                    'change_percent': random.uniform(-1.0, 1.0)
                },
                'shenzhen': {
                    'name': '深证成指',
                    'code': '399001',
                    'value': 12000.0 + random.uniform(-200, 200),
                    'change': random.uniform(-100, 100),
                    'change_percent': random.uniform(-1.0, 1.0)
                }
            },
            'market_stats': {
                'total_stocks': len(self._stocks_cache),
                'rising_stocks': random.randint(1500, 2500),
                'falling_stocks': random.randint(1500, 2500),
                'unchanged_stocks': random.randint(100, 300),
                'total_turnover': round(random.uniform(800, 1200) * 100000000, 2),
                'total_volume': random.randint(80000000000, 120000000000)
            },
            'hot_sectors': [
                {'name': '银行', 'change_percent': random.uniform(-2, 2)},
                {'name': '科技', 'change_percent': random.uniform(-3, 3)},
                {'name': '医药', 'change_percent': random.uniform(-2, 2)}
            ]
        }
    
    def search_stocks(self, keyword: str, search_type: str = 'all', 
                     limit: int = 20) -> List[Stock]:
        """搜索股票"""
        stocks = list(self._stocks_cache.values())
        results = []
        
        keyword = keyword.lower()
        
        for stock in stocks:
            match = False
            
            if search_type in ['all', 'code']:
                if keyword in stock.code.lower():
                    match = True
            
            if search_type in ['all', 'name']:
                if keyword in stock.name.lower():
                    match = True
            
            if search_type in ['all', 'pinyin']:
                # 简单的拼音匹配（实际应用中需要更复杂的拼音库）
                if keyword in stock.name.lower():
                    match = True
            
            if match:
                results.append(stock)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_user_watchlist(self, user_id: str) -> List[Stock]:
        """获取用户自选股"""
        if user_id not in self._watchlists:
            return []
        
        stock_codes = self._watchlists[user_id]
        return [self._stocks_cache[code] for code in stock_codes 
                if code in self._stocks_cache]
    
    def add_to_watchlist(self, user_id: str, code: str) -> bool:
        """添加股票到自选股"""
        if code not in self._stocks_cache:
            return False
        
        if user_id not in self._watchlists:
            self._watchlists[user_id] = []
        
        if code not in self._watchlists[user_id]:
            self._watchlists[user_id].append(code)
            return True
        
        return False  # 已存在
    
    def remove_from_watchlist(self, user_id: str, code: str) -> bool:
        """从自选股中移除股票"""
        if user_id not in self._watchlists:
            return False
        
        if code in self._watchlists[user_id]:
            self._watchlists[user_id].remove(code)
            return True
        
        return False  # 不存在