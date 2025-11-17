"""
股票相关数据模型

包括股票基本信息、行情数据、财务数据、市场指标等
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, Any, Optional
from enum import Enum


class StockStatus(Enum):
    """股票状态"""
    ACTIVE = "active"           # 正常交易
    SUSPENDED = "suspended"     # 停牌
    DELISTED = "delisted"      # 退市
    ST = "st"                  # ST股票
    STAR_ST = "star_st"        # *ST股票


class MarketType(Enum):
    """市场类型"""
    SH = "sh"    # 上海证券交易所
    SZ = "sz"    # 深圳证券交易所
    BJ = "bj"    # 北京证券交易所


@dataclass
class Stock:
    """股票基本信息"""
    code: str                           # 股票代码
    name: str                           # 股票名称
    industry: str                       # 所属行业
    market: str                         # 交易市场
    listing_date: date                  # 上市日期
    total_shares: int                   # 总股本
    float_shares: int                   # 流通股本
    market_cap: float                   # 总市值
    pe_ratio: Optional[float] = None    # 市盈率
    pb_ratio: Optional[float] = None    # 市净率
    dividend_yield: Optional[float] = None  # 股息率
    status: str = StockStatus.ACTIVE.value  # 股票状态
    sector: Optional[str] = None        # 板块
    concept: Optional[str] = None       # 概念
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'industry': self.industry,
            'market': self.market,
            'listing_date': self.listing_date.isoformat() if self.listing_date else None,
            'total_shares': self.total_shares,
            'float_shares': self.float_shares,
            'market_cap': self.market_cap,
            'pe_ratio': self.pe_ratio,
            'pb_ratio': self.pb_ratio,
            'dividend_yield': self.dividend_yield,
            'status': self.status,
            'sector': self.sector,
            'concept': self.concept,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def is_active(self) -> bool:
        """是否为正常交易状态"""
        return self.status == StockStatus.ACTIVE.value
    
    def is_suspended(self) -> bool:
        """是否停牌"""
        return self.status == StockStatus.SUSPENDED.value
    
    def is_st_stock(self) -> bool:
        """是否为ST股票"""
        return self.status in [StockStatus.ST.value, StockStatus.STAR_ST.value]


@dataclass
class StockQuote:
    """股票行情数据"""
    code: str                           # 股票代码
    date: date                          # 交易日期
    open_price: float                   # 开盘价
    high_price: float                   # 最高价
    low_price: float                    # 最低价
    close_price: float                  # 收盘价
    volume: int                         # 成交量（股）
    turnover: float                     # 成交额（元）
    change_amount: Optional[float] = None    # 涨跌额
    change_percent: Optional[float] = None   # 涨跌幅（%）
    amplitude: Optional[float] = None        # 振幅（%）
    turnover_rate: Optional[float] = None    # 换手率（%）
    timestamp: Optional[datetime] = None     # 时间戳（实时行情）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'date': self.date.isoformat() if self.date else None,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume,
            'turnover': self.turnover,
            'change_amount': self.change_amount,
            'change_percent': self.change_percent,
            'amplitude': self.amplitude,
            'turnover_rate': self.turnover_rate,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def is_limit_up(self) -> bool:
        """是否涨停"""
        return self.change_percent and self.change_percent >= 9.9
    
    def is_limit_down(self) -> bool:
        """是否跌停"""
        return self.change_percent and self.change_percent <= -9.9
    
    def get_ohlc(self) -> tuple[float, float, float, float]:
        """获取OHLC数据"""
        return self.open_price, self.high_price, self.low_price, self.close_price


@dataclass
class FinancialData:
    """财务数据"""
    code: str                           # 股票代码
    report_date: date                   # 报告期
    report_type: str                    # 报告类型（annual/quarterly）
    revenue: float                      # 营业收入
    net_profit: float                   # 净利润
    total_assets: float                 # 总资产
    total_liabilities: float            # 总负债
    shareholders_equity: float          # 股东权益
    operating_cash_flow: float          # 经营活动现金流
    roe: Optional[float] = None         # 净资产收益率（%）
    roa: Optional[float] = None         # 总资产收益率（%）
    gross_margin: Optional[float] = None     # 毛利率（%）
    net_margin: Optional[float] = None       # 净利率（%）
    debt_ratio: Optional[float] = None       # 资产负债率（%）
    current_ratio: Optional[float] = None    # 流动比率
    eps: Optional[float] = None         # 每股收益
    bps: Optional[float] = None         # 每股净资产
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'report_type': self.report_type,
            'revenue': self.revenue,
            'net_profit': self.net_profit,
            'total_assets': self.total_assets,
            'total_liabilities': self.total_liabilities,
            'shareholders_equity': self.shareholders_equity,
            'operating_cash_flow': self.operating_cash_flow,
            'roe': self.roe,
            'roa': self.roa,
            'gross_margin': self.gross_margin,
            'net_margin': self.net_margin,
            'debt_ratio': self.debt_ratio,
            'current_ratio': self.current_ratio,
            'eps': self.eps,
            'bps': self.bps
        }
    
    def is_profitable(self) -> bool:
        """是否盈利"""
        return self.net_profit > 0
    
    def get_debt_to_equity_ratio(self) -> Optional[float]:
        """计算负债权益比"""
        if self.shareholders_equity > 0:
            return self.total_liabilities / self.shareholders_equity
        return None


@dataclass
class MarketIndicator:
    """市场指标"""
    name: str                           # 指标名称
    code: str                           # 指标代码
    value: float                        # 指标值
    change_amount: Optional[float] = None    # 变化量
    change_percent: Optional[float] = None   # 变化百分比
    date: Optional[date] = None         # 日期
    category: Optional[str] = None      # 分类（index/sector/macro）
    description: Optional[str] = None   # 描述
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'code': self.code,
            'value': self.value,
            'change_amount': self.change_amount,
            'change_percent': self.change_percent,
            'date': self.date.isoformat() if self.date else None,
            'category': self.category,
            'description': self.description
        }
    
    def is_rising(self) -> bool:
        """是否上涨"""
        return self.change_percent and self.change_percent > 0
    
    def is_falling(self) -> bool:
        """是否下跌"""
        return self.change_percent and self.change_percent < 0


@dataclass
class TechnicalIndicator:
    """技术指标"""
    code: str                           # 股票代码
    date: date                          # 日期
    ma5: Optional[float] = None         # 5日均线
    ma10: Optional[float] = None        # 10日均线
    ma20: Optional[float] = None        # 20日均线
    ma60: Optional[float] = None        # 60日均线
    ema12: Optional[float] = None       # 12日指数移动平均
    ema26: Optional[float] = None       # 26日指数移动平均
    macd: Optional[float] = None        # MACD
    macd_signal: Optional[float] = None # MACD信号线
    macd_histogram: Optional[float] = None  # MACD柱状图
    rsi: Optional[float] = None         # RSI相对强弱指标
    kdj_k: Optional[float] = None       # KDJ指标K值
    kdj_d: Optional[float] = None       # KDJ指标D值
    kdj_j: Optional[float] = None       # KDJ指标J值
    bollinger_upper: Optional[float] = None  # 布林带上轨
    bollinger_middle: Optional[float] = None # 布林带中轨
    bollinger_lower: Optional[float] = None  # 布林带下轨
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'date': self.date.isoformat() if self.date else None,
            'ma5': self.ma5,
            'ma10': self.ma10,
            'ma20': self.ma20,
            'ma60': self.ma60,
            'ema12': self.ema12,
            'ema26': self.ema26,
            'macd': self.macd,
            'macd_signal': self.macd_signal,
            'macd_histogram': self.macd_histogram,
            'rsi': self.rsi,
            'kdj_k': self.kdj_k,
            'kdj_d': self.kdj_d,
            'kdj_j': self.kdj_j,
            'bollinger_upper': self.bollinger_upper,
            'bollinger_middle': self.bollinger_middle,
            'bollinger_lower': self.bollinger_lower
        }
    
    def is_oversold(self) -> bool:
        """是否超卖（RSI < 30）"""
        return self.rsi and self.rsi < 30
    
    def is_overbought(self) -> bool:
        """是否超买（RSI > 70）"""
        return self.rsi and self.rsi > 70


@dataclass
class StockNews:
    """股票新闻"""
    id: str                             # 新闻ID
    title: str                          # 标题
    content: str                        # 内容
    source: str                         # 来源
    author: Optional[str] = None        # 作者
    publish_time: datetime = field(default_factory=datetime.now)  # 发布时间
    related_stocks: list[str] = field(default_factory=list)  # 相关股票代码
    sentiment: Optional[str] = None     # 情感倾向（positive/negative/neutral）
    importance: int = 1                 # 重要性（1-5）
    tags: list[str] = field(default_factory=list)  # 标签
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'author': self.author,
            'publish_time': self.publish_time.isoformat(),
            'related_stocks': self.related_stocks,
            'sentiment': self.sentiment,
            'importance': self.importance,
            'tags': self.tags
        }
    
    def is_positive(self) -> bool:
        """是否为正面新闻"""
        return self.sentiment == 'positive'
    
    def is_negative(self) -> bool:
        """是否为负面新闻"""
        return self.sentiment == 'negative'
    
    def is_important(self) -> bool:
        """是否为重要新闻"""
        return self.importance >= 4


@dataclass
class Watchlist:
    """自选股列表"""
    user_id: str                        # 用户ID
    name: str                           # 列表名称
    stocks: list[str] = field(default_factory=list)  # 股票代码列表
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_default: bool = False            # 是否为默认列表
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'stocks': self.stocks,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_default': self.is_default,
            'count': len(self.stocks)
        }
    
    def add_stock(self, code: str) -> bool:
        """添加股票"""
        if code not in self.stocks:
            self.stocks.append(code)
            self.updated_at = datetime.now()
            return True
        return False
    
    def remove_stock(self, code: str) -> bool:
        """移除股票"""
        if code in self.stocks:
            self.stocks.remove(code)
            self.updated_at = datetime.now()
            return True
        return False
    
    def has_stock(self, code: str) -> bool:
        """是否包含股票"""
        return code in self.stocks