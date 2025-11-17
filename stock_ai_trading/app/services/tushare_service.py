"""
Tushare数据集成服务
提供股票数据的获取、处理和存储功能
"""
import tushare as ts
import pandas as pd
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import asyncio
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
import hashlib
import json

from app.config.settings import settings
from app.core.database import get_db
from app.core.redis_client import redis_client
from app.utils.retry_decorator import retry_with_backoff
from app.utils.data_validator import DataValidator

logger = logging.getLogger(__name__)

class TushareService:
    """Tushare数据服务类"""
    
    def __init__(self):
        """初始化Tushare服务"""
        self.token = settings.TUSHARE_TOKEN
        if not self.token:
            logger.warning("Tushare token not configured, some features may not work")
            self.pro = None
        else:
            # 初始化Tushare API
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        
        # 数据验证器
        self.validator = DataValidator()
        
        # API调用限制配置
        self.api_limits = {
            'default': {'calls_per_minute': 200, 'points_per_minute': 2000},
            'premium': {'calls_per_minute': 500, 'points_per_minute': 5000}
        }
        
        # 缓存配置
        self.cache_config = {
            'stock_basic': 3600 * 24,  # 基础数据缓存24小时
            'daily_quotes': 3600 * 2,  # 日线数据缓存2小时
            'financial_data': 3600 * 12,  # 财务数据缓存12小时
        }
    
    def _get_cache_key(self, data_type: str, **params) -> str:
        """生成缓存键"""
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"tushare:{data_type}:{param_hash}"
    
    def _check_api_limit(self) -> bool:
        """检查API调用限制"""
        current_minute = datetime.now().strftime("%Y%m%d%H%M")
        calls_key = f"tushare:calls:{current_minute}"
        points_key = f"tushare:points:{current_minute}"
        
        current_calls = int(redis_client.get(calls_key) or 0)
        current_points = int(redis_client.get(points_key) or 0)
        
        limits = self.api_limits['default']  # 可根据用户等级调整
        
        if current_calls >= limits['calls_per_minute']:
            logger.warning(f"API调用次数达到限制: {current_calls}")
            return False
        
        if current_points >= limits['points_per_minute']:
            logger.warning(f"API积分消耗达到限制: {current_points}")
            return False
        
        return True
    
    def _update_api_usage(self, points: int = 1):
        """更新API使用统计"""
        current_minute = datetime.now().strftime("%Y%m%d%H%M")
        calls_key = f"tushare:calls:{current_minute}"
        points_key = f"tushare:points:{current_minute}"
        
        redis_client.redis_client.incr(calls_key)
        redis_client.redis_client.incr(points_key, points)
        redis_client.redis_client.expire(calls_key, 60)
        redis_client.redis_client.expire(points_key, 60)
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    async def _api_call(self, api_name: str, **kwargs) -> pd.DataFrame:
        """统一的API调用方法"""
        if not self.pro:
            raise ValueError("Tushare API not initialized. Please configure TUSHARE_TOKEN.")
            
        if not self._check_api_limit():
            await asyncio.sleep(60)  # 等待1分钟后重试
        
        try:
            # 根据API名称调用相应方法
            api_method = getattr(self.pro, api_name)
            df = api_method(**kwargs)
            
            # 更新API使用统计
            self._update_api_usage()
            
            logger.info(f"API调用成功: {api_name}, 返回{len(df)}条记录")
            return df
            
        except Exception as e:
            logger.error(f"API调用失败: {api_name}, 错误: {str(e)}")
            raise
    
    # ==================== 基础数据获取 ====================
    
    async def get_stock_basic(self, exchange: str = '', list_status: str = 'L') -> pd.DataFrame:
        """获取股票基础信息"""
        cache_key = self._get_cache_key('stock_basic', exchange=exchange, list_status=list_status)
        
        # 尝试从缓存获取
        cached_data = redis_client.get_json(cache_key)
        if cached_data:
            return pd.DataFrame(cached_data)
        
        # 从API获取数据
        df = await self._api_call('stock_basic', exchange=exchange, list_status=list_status)
        
        # 数据验证
        if self.validator.validate_stock_basic(df):
            # 缓存数据
            redis_client.set_json(cache_key, df.to_dict('records'), 
                                self.cache_config['stock_basic'])
            return df
        else:
            raise ValueError("股票基础数据验证失败")
    
    async def get_index_basic(self, market: str = 'SSE') -> pd.DataFrame:
        """获取指数基础信息"""
        cache_key = self._get_cache_key('index_basic', market=market)
        
        cached_data = redis_client.get_json(cache_key)
        if cached_data:
            return pd.DataFrame(cached_data)
        
        df = await self._api_call('index_basic', market=market)
        
        if self.validator.validate_index_basic(df):
            redis_client.set_json(cache_key, df.to_dict('records'), 
                                self.cache_config['stock_basic'])
            return df
        else:
            raise ValueError("指数基础数据验证失败")
    
    # ==================== 行情数据获取 ====================
    
    async def get_daily_quotes(self, ts_code: str = '', trade_date: str = '', 
                             start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """获取日线行情数据"""
        cache_key = self._get_cache_key('daily_quotes', ts_code=ts_code, 
                                      trade_date=trade_date, start_date=start_date, end_date=end_date)
        
        cached_data = redis_client.get_json(cache_key)
        if cached_data:
            return pd.DataFrame(cached_data)
        
        df = await self._api_call('daily', ts_code=ts_code, trade_date=trade_date,
                                start_date=start_date, end_date=end_date)
        
        if self.validator.validate_daily_quotes(df):
            redis_client.set_json(cache_key, df.to_dict('records'), 
                                self.cache_config['daily_quotes'])
            return df
        else:
            raise ValueError("日线数据验证失败")
    
    async def get_adj_factor(self, ts_code: str = '', trade_date: str = '',
                           start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """获取复权因子"""
        df = await self._api_call('adj_factor', ts_code=ts_code, trade_date=trade_date,
                                start_date=start_date, end_date=end_date)
        return df
    
    async def get_minute_data(self, ts_code: str, freq: str = '1min',
                            start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """获取分钟级行情数据"""
        df = await self._api_call('stk_mins', ts_code=ts_code, freq=freq,
                                start_date=start_date, end_date=end_date)
        return df
    
    # ==================== 财务数据获取 ====================
    
    async def get_income_statement(self, ts_code: str = '', ann_date: str = '',
                                 start_date: str = '', end_date: str = '',
                                 period: str = '') -> pd.DataFrame:
        """获取利润表数据"""
        cache_key = self._get_cache_key('income', ts_code=ts_code, ann_date=ann_date,
                                      start_date=start_date, end_date=end_date, period=period)
        
        cached_data = redis_client.get_json(cache_key)
        if cached_data:
            return pd.DataFrame(cached_data)
        
        df = await self._api_call('income', ts_code=ts_code, ann_date=ann_date,
                                start_date=start_date, end_date=end_date, period=period)
        
        if self.validator.validate_financial_data(df):
            redis_client.set_json(cache_key, df.to_dict('records'), 
                                self.cache_config['financial_data'])
            return df
        else:
            raise ValueError("利润表数据验证失败")
    
    async def get_balance_sheet(self, ts_code: str = '', ann_date: str = '',
                              start_date: str = '', end_date: str = '',
                              period: str = '') -> pd.DataFrame:
        """获取资产负债表数据"""
        df = await self._api_call('balancesheet', ts_code=ts_code, ann_date=ann_date,
                                start_date=start_date, end_date=end_date, period=period)
        return df
    
    async def get_cash_flow(self, ts_code: str = '', ann_date: str = '',
                          start_date: str = '', end_date: str = '',
                          period: str = '') -> pd.DataFrame:
        """获取现金流量表数据"""
        df = await self._api_call('cashflow', ts_code=ts_code, ann_date=ann_date,
                                start_date=start_date, end_date=end_date, period=period)
        return df
    
    async def get_financial_indicators(self, ts_code: str = '', ann_date: str = '',
                                     start_date: str = '', end_date: str = '',
                                     period: str = '') -> pd.DataFrame:
        """获取财务指标数据"""
        df = await self._api_call('fina_indicator', ts_code=ts_code, ann_date=ann_date,
                                start_date=start_date, end_date=end_date, period=period)
        return df
    
    # ==================== 参考数据获取 ====================
    
    async def get_dividend_data(self, ts_code: str = '', ann_date: str = '',
                              record_date: str = '', ex_date: str = '') -> pd.DataFrame:
        """获取分红送股数据"""
        df = await self._api_call('dividend', ts_code=ts_code, ann_date=ann_date,
                                record_date=record_date, ex_date=ex_date)
        return df
    
    async def get_share_float(self, ts_code: str = '', ann_date: str = '',
                            float_date: str = '', start_date: str = '',
                            end_date: str = '') -> pd.DataFrame:
        """获取限售股解禁数据"""
        df = await self._api_call('share_float', ts_code=ts_code, ann_date=ann_date,
                                float_date=float_date, start_date=start_date, end_date=end_date)
        return df
    
    async def get_top10_holders(self, ts_code: str = '', period: str = '',
                              ann_date: str = '', start_date: str = '',
                              end_date: str = '') -> pd.DataFrame:
        """获取前十大股东数据"""
        df = await self._api_call('top10_holders', ts_code=ts_code, period=period,
                                ann_date=ann_date, start_date=start_date, end_date=end_date)
        return df
    
    # ==================== 特色数据获取 ====================
    
    async def get_top_list(self, trade_date: str = '', ts_code: str = '') -> pd.DataFrame:
        """获取龙虎榜数据"""
        df = await self._api_call('top_list', trade_date=trade_date, ts_code=ts_code)
        return df
    
    async def get_moneyflow(self, ts_code: str = '', trade_date: str = '',
                          start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """获取资金流向数据"""
        df = await self._api_call('moneyflow', ts_code=ts_code, trade_date=trade_date,
                                start_date=start_date, end_date=end_date)
        return df
    
    async def get_limit_list(self, trade_date: str = '', ts_code: str = '',
                           limit_type: str = 'U') -> pd.DataFrame:
        """获取涨跌停数据"""
        df = await self._api_call('limit_list', trade_date=trade_date, ts_code=ts_code,
                                limit_type=limit_type)
        return df
    
    # ==================== 增量更新机制 ====================
    
    async def get_incremental_data(self, data_type: str, last_update: datetime) -> pd.DataFrame:
        """获取增量数据"""
        current_date = datetime.now().strftime('%Y%m%d')
        last_date = last_update.strftime('%Y%m%d')
        
        if data_type == 'daily_quotes':
            return await self.get_daily_quotes(start_date=last_date, end_date=current_date)
        elif data_type == 'financial_data':
            return await self.get_income_statement(start_date=last_date, end_date=current_date)
        # 可以添加更多数据类型的增量更新逻辑
        
        return pd.DataFrame()
    
    async def update_data_timestamp(self, data_type: str, timestamp: datetime):
        """更新数据时间戳"""
        key = f"tushare:last_update:{data_type}"
        redis_client.set(key, timestamp.isoformat(), expire=3600*24*30)  # 保存30天
    
    async def get_last_update_time(self, data_type: str) -> Optional[datetime]:
        """获取最后更新时间"""
        key = f"tushare:last_update:{data_type}"
        timestamp_str = redis_client.get(key)
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str)
        return None

# 全局Tushare服务实例
tushare_service = TushareService()