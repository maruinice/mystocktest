"""
Tushare增强服务 - 新增数据接口
包括：行业分类、涨跌停、停复牌、审计意见、指数成分
"""
import tushare as ts
import pandas as pd
from typing import Optional, List
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.services.tushare_service import TushareService

logger = logging.getLogger(__name__)


class TushareEnhancedService(TushareService):
    """Tushare增强服务类"""
    
    def __init__(self):
        super().__init__()
    
    # ==================== 行业分类数据 ====================
    
    async def get_industry_classification(self, ts_code: str = '', src: str = 'SW2021', level: str = 'L1') -> pd.DataFrame:
        """
        获取行业分类数据（支持批量股票代码）
        
        Args:
            ts_code: 股票代码，支持多个代码用逗号分隔（如：'000001.SZ,000002.SZ'）
            src: 分类标准(SW2021申万/ZJHHY证监会)
            level: 行业级别(L1一级/L2二级/L3三级)
            
        Returns:
            行业分类DataFrame，包含字段：
            - ts_code: 股票代码
            - index_code: 行业代码
            - index_name: 行业名称
            - level: 行业级别
            - src: 分类标准
        """
        try:
            params = {'src': src, 'level': level}
            if ts_code:
                params['ts_code'] = ts_code
                
            df = await self._api_call('index_classify', **params)
            logger.info(f"获取行业分类成功: {src} {level}, ts_code={ts_code[:50] if ts_code else 'all'}, 共{len(df)}条")
            return df
        except Exception as e:
            logger.error(f"获取行业分类失败: {e}")
            return pd.DataFrame()
    
    async def get_stock_basic(self, exchange: str = '', list_status: str = 'L') -> pd.DataFrame:
        """
        获取股票基础信息
        
        Args:
            exchange: 交易所(SSE上交所/SZSE深交所)
            list_status: 上市状态(L上市/D退市/P暂停上市)
            
        Returns:
            股票基础信息DataFrame
        """
        try:
            params = {}
            if exchange:
                params['exchange'] = exchange
            if list_status:
                params['list_status'] = list_status
                
            df = await self._api_call('stock_basic', **params)
            logger.info(f"获取股票基础信息成功: exchange={exchange}, 共{len(df)}条")
            return df
        except Exception as e:
            logger.error(f"获取股票基础信息失败: {e}")
            return pd.DataFrame()
    
    async def get_stock_industry(self, ts_code: str = '', symbol: str = '') -> pd.DataFrame:
        """
        获取股票所属行业
        
        Args:
            ts_code: 股票代码
            symbol: 股票简称
            
        Returns:
            股票行业DataFrame
        """
        try:
            df = await self._api_call('ths_member', ts_code=ts_code, code=symbol)
            logger.info(f"获取股票行业成功: {ts_code}")
            return df
        except Exception as e:
            logger.error(f"获取股票行业失败: {e}")
            return pd.DataFrame()
    
    # ==================== 涨跌停数据 ====================
    
    async def get_stk_limit(self, trade_date: str = '', ts_code: str = '',
                           start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """
        获取每日涨跌停价格
        接口：stk_limit
        
        Args:
            trade_date: 交易日期(YYYYMMDD)
            ts_code: 股票代码
            start_date: 开始日期(YYYYMMDD)
            end_date: 结束日期(YYYYMMDD)
            
        Returns:
            涨跌停价格DataFrame，包含字段：
            - trade_date: 交易日期
            - ts_code: 股票代码
            - up_limit: 涨停价
            - down_limit: 跌停价
        """
        try:
            params = {}
            if trade_date:
                params['trade_date'] = trade_date
            if ts_code:
                params['ts_code'] = ts_code
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            df = await self._api_call('stk_limit', **params)
            logger.info(f"获取涨跌停价格成功: {trade_date or f'{start_date}-{end_date}'}, 共{len(df)}条")
            return df
        except Exception as e:
            logger.error(f"获取涨跌停价格失败: {e}")
            return pd.DataFrame()
    
    async def get_daily_basic_with_limit(self, ts_code: str = '', trade_date: str = '',
                                        start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """
        获取每日指标(包含涨跌停价)
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            每日指标DataFrame(包含up_limit, down_limit)
        """
        try:
            df = await self._api_call('daily_basic', ts_code=ts_code, 
                                    trade_date=trade_date,
                                    start_date=start_date, end_date=end_date)
            logger.info(f"获取每日指标成功: {ts_code}, 共{len(df)}条")
            return df
        except Exception as e:
            logger.error(f"获取每日指标失败: {e}")
            return pd.DataFrame()
    
    # ==================== 停复牌数据 ====================
    
    async def get_suspend_data(self, ts_code: str = '', trade_date: str = '',
                              suspend_type: str = 'S', start_date: str = '',
                              end_date: str = '') -> pd.DataFrame:
        """
        获取每日停复牌信息
        接口：suspend_d
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期(YYYYMMDD)
            suspend_type: 停复牌类型(S停牌/R复牌)
            start_date: 开始日期(YYYYMMDD)
            end_date: 结束日期(YYYYMMDD)
            
        Returns:
            停复牌DataFrame，包含字段：
            - ts_code: 股票代码
            - suspend_type: 停复牌类型
            - trade_date: 交易日期
            - suspend_timing: 停牌时段
        """
        try:
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
            if suspend_type:
                params['suspend_type'] = suspend_type
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            df = await self._api_call('suspend_d', **params)
            logger.info(f"获取停复牌数据成功: {trade_date or f'{start_date}-{end_date}'}, 共{len(df)}条")
            return df
        except Exception as e:
            logger.error(f"获取停复牌数据失败: {e}")
            return pd.DataFrame()
    
    # ==================== 审计意见数据 ====================
    
    async def get_audit_opinion(self, ts_code: str = '', ann_date: str = '',
                               start_date: str = '', end_date: str = '',
                               period: str = '') -> pd.DataFrame:
        """
        获取财务审计意见
        接口：fina_audit
        
        Args:
            ts_code: 股票代码
            ann_date: 公告日期(YYYYMMDD)
            start_date: 开始日期(YYYYMMDD)
            end_date: 结束日期(YYYYMMDD)
            period: 报告期(YYYYMMDD)
            
        Returns:
            审计意见DataFrame，包含字段：
            - ts_code: 股票代码
            - ann_date: 公告日期
            - end_date: 报告期
            - audit_result: 审计结果
            - audit_agency: 审计机构
            - audit_sign: 签字会计师
        """
        try:
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if ann_date:
                params['ann_date'] = ann_date
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            if period:
                params['period'] = period
                
            df = await self._api_call('fina_audit', **params)
            logger.info(f"获取审计意见成功: {ts_code or f'{start_date}-{end_date}'}, 共{len(df)}条")
            return df
        except Exception as e:
            logger.error(f"获取审计意见失败: {e}")
            return pd.DataFrame()
    
    # ==================== 指数成分数据 ====================
    
    async def get_index_weight(self, index_code: str, trade_date: str = '',
                              start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """
        获取指数成分和权重
        
        Args:
            index_code: 指数代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指数成分DataFrame
        """
        try:
            df = await self._api_call('index_weight', index_code=index_code,
                                    trade_date=trade_date,
                                    start_date=start_date, end_date=end_date)
            logger.info(f"获取指数成分成功: {index_code}, 共{len(df)}条")
            return df
        except Exception as e:
            logger.error(f"获取指数成分失败: {e}")
            return pd.DataFrame()
    
    async def get_index_member(self, index_code: str, is_new: str = 'Y') -> pd.DataFrame:
        """
        获取指数成分股
        
        Args:
            index_code: 指数代码
            is_new: 是否最新(Y是/N否)
            
        Returns:
            成分股DataFrame
        """
        try:
            df = await self._api_call('index_member', index_code=index_code, is_new=is_new)
            logger.info(f"获取指数成分股成功: {index_code}, 共{len(df)}条")
            return df
        except Exception as e:
            logger.error(f"获取指数成分股失败: {e}")
            return pd.DataFrame()


# 全局增强服务实例
tushare_enhanced_service = TushareEnhancedService()
