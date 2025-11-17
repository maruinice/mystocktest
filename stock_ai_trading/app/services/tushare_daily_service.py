#!/usr/bin/env python3
"""
Tushare数据同步服务
调用Tushare API获取各种历史数据
支持日线行情、复权因子、每日指标、交易日历等数据
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import time
import requests
import tushare as ts

from app.services.strategy_database_service import strategy_db_service

logger = logging.getLogger(__name__)


class TushareDailyService:
    """Tushare数据同步服务"""
    
    def __init__(self):
        self.db_service = strategy_db_service
        # 从环境变量获取token
        import os
        self.token = os.getenv('TUSHARE_TOKEN', '')
        self.use_mock_data = not bool(self.token)  # 有token就用真实数据
        
        if self.use_mock_data:
            logger.warning("未配置Tushare Token，将使用模拟数据")
        else:
            logger.info("已配置Tushare Token，将使用真实数据")
            # 初始化tushare
            ts.set_token(self.token)
            self.pro = ts.pro_api()
    
    async def sync_three_years_data(self, end_date: str = None) -> Dict:
        """
        同步三年历史数据
        
        Args:
            end_date: 结束日期 (YYYYMMDD格式)，默认为今天
        
        Returns:
            同步结果统计
        """
        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            # 计算三年前的日期
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            start_dt = end_dt - timedelta(days=3*365)  # 三年
            start_date = start_dt.strftime('%Y%m%d')
            
            logger.info(f"开始同步三年历史数据: {start_date} - {end_date}")
            
            results = {}
            
            # 1. 同步交易日历
            print("📅 同步交易日历...")
            cal_result = await self.sync_trade_calendar(start_date, end_date)
            results['trade_calendar'] = cal_result
            
            # 2. 同步股票基础信息
            print("📊 同步股票基础信息...")
            basic_result = await self.sync_stock_basic()
            results['stock_basic'] = basic_result
            
            # 3. 获取活跃股票列表
            active_stocks = await self._get_active_stock_codes()
            if len(active_stocks) > 200:  # 限制数量避免超时
                active_stocks = active_stocks[:200]
            
            print(f"📈 准备同步 {len(active_stocks)} 只股票的历史数据...")
            
            # 4. 同步日线行情数据
            print("📈 同步日线行情数据...")
            daily_result = await self.sync_daily_data(
                start_date=start_date, 
                end_date=end_date, 
                ts_codes=active_stocks
            )
            results['daily_data'] = daily_result
            
            # 5. 同步每日指标
            print("📊 同步每日指标...")
            basic_daily_result = await self.sync_daily_basic(
                start_date=start_date,
                end_date=end_date,
                ts_codes=active_stocks
            )
            results['daily_basic'] = basic_daily_result
            
            # 6. 同步复权因子
            print("🔄 同步复权因子...")
            adj_result = await self.sync_adj_factor(
                start_date=start_date,
                end_date=end_date,
                ts_codes=active_stocks
            )
            results['adj_factor'] = adj_result
            
            # 统计总结果
            total_records = sum([
                r.get('data', {}).get('saved_count', 0) 
                for r in results.values() 
                if isinstance(r, dict) and r.get('success')
            ])
            
            return {
                'success': True,
                'message': f'三年历史数据同步完成，总计{total_records}条记录',
                'data': {
                    'date_range': f'{start_date} - {end_date}',
                    'stocks_count': len(active_stocks),
                    'total_records': total_records,
                    'use_mock_data': self.use_mock_data,
                    'details': results
                }
            }
            
        except Exception as e:
            logger.error(f"同步三年历史数据失败: {e}")
            return {'success': False, 'message': f'同步失败: {str(e)}'}
    
    async def sync_trade_calendar(self, start_date: str, end_date: str) -> Dict:
        """同步交易日历"""
        try:
            logger.info(f"同步交易日历: {start_date} - {end_date}")
            
            if self.use_mock_data:
                cal_df = await self._get_mock_trade_calendar(start_date, end_date)
            else:
                cal_df = await self._get_tushare_trade_calendar(start_date, end_date)
            
            if not cal_df.empty:
                saved_count = await self._save_trade_calendar(cal_df)
                return {
                    'success': True,
                    'message': f'成功同步{saved_count}条交易日历',
                    'data': {'saved_count': saved_count}
                }
            else:
                return {'success': False, 'message': '未获取到交易日历数据'}
                
        except Exception as e:
            logger.error(f"同步交易日历失败: {e}")
            return {'success': False, 'message': f'同步失败: {str(e)}'}
    
    async def sync_daily_basic(self, start_date: str, end_date: str, ts_codes: List[str] = None) -> Dict:
        """同步每日指标"""
        try:
            logger.info(f"同步每日指标: {start_date} - {end_date}")
            
            if not ts_codes:
                ts_codes = await self._get_active_stock_codes()
            
            total_saved = 0
            
            if self.use_mock_data:
                # 模拟数据
                for ts_code in ts_codes[:50]:  # 限制数量
                    basic_df = await self._get_mock_daily_basic(ts_code, start_date, end_date)
                    if not basic_df.empty:
                        saved_count = await self._save_daily_basic(basic_df)
                        total_saved += saved_count
                    await asyncio.sleep(0.01)
            else:
                # 真实数据 - 按日期批量获取
                dates = await self._get_trade_dates(start_date, end_date)
                for trade_date in dates:
                    try:
                        basic_df = await self._get_tushare_daily_basic(trade_date)
                        if not basic_df.empty:
                            saved_count = await self._save_daily_basic(basic_df)
                            total_saved += saved_count
                        await asyncio.sleep(0.2)  # 控制请求频率
                    except Exception as e:
                        logger.warning(f"获取{trade_date}每日指标失败: {e}")
                        continue
            
            return {
                'success': True,
                'message': f'成功同步{total_saved}条每日指标',
                'data': {'saved_count': total_saved}
            }
            
        except Exception as e:
            logger.error(f"同步每日指标失败: {e}")
            return {'success': False, 'message': f'同步失败: {str(e)}'}
    
    async def sync_adj_factor(self, start_date: str, end_date: str, ts_codes: List[str] = None) -> Dict:
        """同步复权因子 - 使用批量调用优化"""
        try:
            logger.info(f"同步复权因子: {start_date} - {end_date}")
            
            if not ts_codes:
                ts_codes = await self._get_active_stock_codes()
            
            total_saved = 0
            
            # 分批处理股票 - 每批10个股票代码
            batch_size = 10
            total_batches = (len(ts_codes) + batch_size - 1) // batch_size
            
            for i in range(0, len(ts_codes), batch_size):
                batch_codes = ts_codes[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                logger.info(f"处理第 {batch_num}/{total_batches} 批复权因子: {len(batch_codes)}只股票")
                
                try:
                    if self.use_mock_data:
                        # 模拟数据模式：逐个处理
                        batch_df_list = []
                        for ts_code in batch_codes:
                            adj_df = await self._get_mock_adj_factor(ts_code, start_date, end_date)
                            if not adj_df.empty:
                                batch_df_list.append(adj_df)
                        
                        if batch_df_list:
                            combined_df = pd.concat(batch_df_list, ignore_index=True)
                            saved_count = await self._save_adj_factor(combined_df)
                            total_saved += saved_count
                    else:
                        # 真实数据模式：批量调用
                        adj_df = await self._get_tushare_adj_factor(batch_codes, start_date, end_date)
                        
                        if not adj_df.empty:
                            saved_count = await self._save_adj_factor(adj_df)
                            total_saved += saved_count
                            logger.info(f"第 {batch_num} 批保存了 {saved_count} 条复权因子记录")
                    
                    # 批次间延迟，避免API调用过于频繁
                    if i + batch_size < len(ts_codes):
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"第 {batch_num} 批复权因子同步失败: {e}")
                    continue
            
            logger.info(f"复权因子同步完成: 总计{total_saved}条记录")
            
            return {
                'success': True,
                'message': f'成功同步{total_saved}条复权因子',
                'data': {
                    'saved_count': total_saved,
                    'stocks_count': len(ts_codes),
                    'batch_size': batch_size,
                    'total_batches': total_batches
                }
            }
            
        except Exception as e:
            logger.error(f"同步复权因子失败: {e}")
            return {'success': False, 'message': f'同步失败: {str(e)}'}
    
    async def sync_stock_basic(self) -> Dict:
        """同步股票基础信息"""
        try:
            logger.info("同步股票基础信息")
            
            if self.use_mock_data:
                stocks_df = await self._create_mock_stocks()
            else:
                stocks_df = await self._get_tushare_stock_basic()
            
            if not stocks_df.empty:
                saved_count = await self._save_stock_basic(stocks_df)
                return {
                    'success': True,
                    'message': f'成功同步{saved_count}条股票基础信息',
                    'data': {'saved_count': saved_count}
                }
            else:
                return {'success': False, 'message': '未获取到股票基础信息'}
                
        except Exception as e:
            logger.error(f"同步股票基础信息失败: {e}")
            return {'success': False, 'message': f'同步失败: {str(e)}'}
    
    async def sync_daily_data(self, trade_date: str = None, ts_codes: List[str] = None, 
                             start_date: str = None, end_date: str = None) -> Dict:
        """
        同步每日行情数据 <mcreference link="https://tushare.pro/document/2?doc_id=27" index="0">0</mcreference>
        
        Args:
            trade_date: 交易日期 (YYYYMMDD格式)
            ts_codes: 股票代码列表
            start_date: 开始日期 (YYYYMMDD格式)
            end_date: 结束日期 (YYYYMMDD格式)
        
        Returns:
            同步结果统计
        """
        try:
            logger.info(f"开始同步每日行情数据: trade_date={trade_date}, start_date={start_date}, end_date={end_date}")
            
            # 获取股票列表
            if not ts_codes:
                ts_codes = await self._get_active_stock_codes()
            
            # 限制股票数量避免超时
            if len(ts_codes) > 100:
                ts_codes = ts_codes[:100]
                logger.info(f"限制股票数量为100只: {len(ts_codes)}")
            
            total_saved = 0
            
            if self.use_mock_data:
                # 使用模拟数据
                daily_df = await self._get_mock_daily_data(ts_codes, trade_date, start_date, end_date)
                if not daily_df.empty:
                    total_saved = await self._save_daily_history(daily_df)
            else:
                # 使用真实Tushare数据
                if trade_date:
                    # 按单日获取
                    daily_df = await self._get_tushare_daily_by_date(trade_date)
                    if not daily_df.empty:
                        total_saved = await self._save_daily_history(daily_df)
                else:
                    # 按日期范围获取
                    dates = await self._get_trade_dates(start_date, end_date)
                    for date in dates:
                        try:
                            daily_df = await self._get_tushare_daily_by_date(date)
                            if not daily_df.empty:
                                saved_count = await self._save_daily_history(daily_df)
                                total_saved += saved_count
                            await asyncio.sleep(0.2)  # 控制请求频率
                        except Exception as e:
                            logger.warning(f"获取{date}行情数据失败: {e}")
                            continue
            
            logger.info(f"每日行情数据同步完成: 总计{total_saved}条记录")
            
            return {
                'success': True,
                'message': f'成功同步{total_saved}条每日行情数据',
                'data': {
                    'saved_count': total_saved,
                    'stocks_count': len(ts_codes),
                    'date_range': f"{start_date or trade_date} - {end_date or trade_date}",
                    'use_mock_data': self.use_mock_data
                }
            }
            
        except Exception as e:
            logger.error(f"同步每日行情数据失败: {e}")
            return {'success': False, 'message': f'同步失败: {str(e)}'}
    
    # ==================== Tushare API调用方法 ====================
    
    async def _get_tushare_stock_basic(self) -> pd.DataFrame:
        """从Tushare获取股票基础信息"""
        try:
            df = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,exchange,curr_type,list_status,list_date,delist_date,is_hs')
            return df
        except Exception as e:
            logger.error(f"获取Tushare股票基础信息失败: {e}")
            return pd.DataFrame()
    
    async def _get_tushare_trade_calendar(self, start_date: str, end_date: str) -> pd.DataFrame:
        """从Tushare获取交易日历"""
        try:
            # 获取上交所和深交所的交易日历
            sse_df = self.pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)
            szse_df = self.pro.trade_cal(exchange='SZSE', start_date=start_date, end_date=end_date)
            
            # 合并数据
            df = pd.concat([sse_df, szse_df], ignore_index=True)
            return df
        except Exception as e:
            logger.error(f"获取Tushare交易日历失败: {e}")
            return pd.DataFrame()
    
    async def _get_tushare_daily_by_date(self, trade_date: str) -> pd.DataFrame:
        """从Tushare按日期获取日线数据"""
        try:
            df = self.pro.daily(trade_date=trade_date)
            return df
        except Exception as e:
            logger.error(f"获取Tushare日线数据失败 {trade_date}: {e}")
            return pd.DataFrame()
    
    async def _get_tushare_daily_basic(self, trade_date: str) -> pd.DataFrame:
        """从Tushare获取每日指标"""
        try:
            df = self.pro.daily_basic(trade_date=trade_date)
            return df
        except Exception as e:
            logger.error(f"获取Tushare每日指标失败 {trade_date}: {e}")
            return pd.DataFrame()
    
    async def _get_tushare_adj_factor(self, ts_codes: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """从Tushare获取复权因子 - 支持批量股票代码"""
        try:
            # 将股票代码列表转换为逗号分隔的字符串
            ts_codes_str = ','.join(ts_codes)
            logger.info(f"获取复权因子: {len(ts_codes)}只股票, {start_date}-{end_date}")
            
            df = self.pro.adj_factor(ts_code=ts_codes_str, start_date=start_date, end_date=end_date)
            logger.info(f"获取到复权因子数据: {len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"获取Tushare复权因子失败 {ts_codes}: {e}")
            return pd.DataFrame()
    
    # ==================== 辅助方法 ====================
    
    async def _get_active_stock_codes(self) -> List[str]:
        """获取活跃股票代码列表"""
        try:
            with self.db_service.get_connection() as conn:
                sql = """
                SELECT ts_code FROM stock_basic 
                WHERE list_status = 'L' 
                ORDER BY ts_code 
                LIMIT 200
                """
                df = pd.read_sql(sql, conn)
                return df['ts_code'].tolist() if not df.empty else []
        except Exception as e:
            logger.error(f"获取股票代码列表失败: {e}")
            # 返回一些默认的股票代码
            return [
                '000001.SZ', '000002.SZ', '000858.SZ', '002415.SZ', '300059.SZ',
                '600000.SH', '600036.SH', '600519.SH', '600887.SH', '601318.SH'
            ]
    
    async def _get_trade_dates(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日期列表"""
        try:
            with self.db_service.get_connection() as conn:
                sql = """
                SELECT DISTINCT cal_date 
                FROM trade_cal 
                WHERE cal_date BETWEEN %s AND %s 
                AND is_open = 1 
                ORDER BY cal_date
                """
                df = pd.read_sql(sql, conn, params=[start_date, end_date])
                if not df.empty:
                    return [d.strftime('%Y%m%d') for d in df['cal_date']]
                else:
                    # 如果没有交易日历数据，生成工作日
                    dates = []
                    start_dt = datetime.strptime(start_date, '%Y%m%d')
                    end_dt = datetime.strptime(end_date, '%Y%m%d')
                    current = start_dt
                    while current <= end_dt:
                        if current.weekday() < 5:  # 周一到周五
                            dates.append(current.strftime('%Y%m%d'))
                        current += timedelta(days=1)
                    return dates
        except Exception as e:
            logger.error(f"获取交易日期失败: {e}")
            return []
    
    # ==================== 模拟数据生成方法 ====================
    
    async def _create_mock_stocks(self) -> pd.DataFrame:
        """创建模拟股票数据"""
        mock_stocks = []
        
        # 创建一些模拟的股票数据
        industries = ['银行', '证券', '保险', '房地产', '医药生物', '电子', '计算机', '机械设备']
        markets = ['主板', '创业板', '科创板']
        
        for i in range(200):  # 创建200只模拟股票
            ts_code = f"{str(i+1).zfill(6)}.{'SZ' if i % 2 == 0 else 'SH'}"
            mock_stocks.append({
                'ts_code': ts_code,
                'symbol': str(i+1).zfill(6),
                'name': f'模拟股票{i+1:03d}',
                'area': '深圳' if i % 2 == 0 else '上海',
                'industry': np.random.choice(industries),
                'market': np.random.choice(markets),
                'exchange': 'SZSE' if i % 2 == 0 else 'SSE',
                'curr_type': 'CNY',
                'list_status': 'L',
                'list_date': '20200101',
                'is_hs': 'S' if i % 3 == 0 else 'N'
            })
        
        return pd.DataFrame(mock_stocks)
    
    async def _get_mock_trade_calendar(self, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟交易日历"""
        try:
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            
            data_list = []
            current = start_dt
            
            while current <= end_dt:
                # 工作日为交易日
                is_open = 1 if current.weekday() < 5 else 0
                
                for exchange in ['SSE', 'SZSE']:
                    data_list.append({
                        'exchange': exchange,
                        'cal_date': current.date(),
                        'is_open': is_open
                    })
                
                current += timedelta(days=1)
            
            return pd.DataFrame(data_list)
            
        except Exception as e:
            logger.error(f"生成模拟交易日历失败: {e}")
            return pd.DataFrame()
    
    async def _get_mock_daily_basic(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟每日指标数据"""
        try:
            dates = await self._get_trade_dates(start_date, end_date)
            if not dates:
                # 生成工作日
                start_dt = datetime.strptime(start_date, '%Y%m%d')
                end_dt = datetime.strptime(end_date, '%Y%m%d')
                dates = []
                current = start_dt
                while current <= end_dt:
                    if current.weekday() < 5:
                        dates.append(current.strftime('%Y%m%d'))
                    current += timedelta(days=1)
            
            data_list = []
            base_price = np.random.uniform(10, 200)
            
            for trade_date in dates:
                data_list.append({
                    'ts_code': ts_code,
                    'trade_date': datetime.strptime(trade_date, '%Y%m%d').date(),
                    'close': round(base_price * np.random.uniform(0.95, 1.05), 4),
                    'turnover_rate': round(np.random.uniform(0.1, 15), 4),
                    'volume_ratio': round(np.random.uniform(0.5, 3.0), 4),
                    'pe': round(np.random.uniform(8, 80), 4),
                    'pe_ttm': round(np.random.uniform(8, 80), 4),
                    'pb': round(np.random.uniform(0.8, 15), 4),
                    'ps': round(np.random.uniform(1, 20), 4),
                    'ps_ttm': round(np.random.uniform(1, 20), 4),
                    'total_mv': round(np.random.uniform(1000000, 50000000), 2),
                    'circ_mv': round(np.random.uniform(800000, 40000000), 2)
                })
            
            return pd.DataFrame(data_list)
            
        except Exception as e:
            logger.error(f"生成模拟每日指标失败: {e}")
            return pd.DataFrame()
    
    async def _get_mock_adj_factor(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟复权因子数据"""
        try:
            dates = await self._get_trade_dates(start_date, end_date)
            if not dates:
                # 生成工作日
                start_dt = datetime.strptime(start_date, '%Y%m%d')
                end_dt = datetime.strptime(end_date, '%Y%m%d')
                dates = []
                current = start_dt
                while current <= end_dt:
                    if current.weekday() < 5:
                        dates.append(current.strftime('%Y%m%d'))
                    current += timedelta(days=1)
            
            data_list = []
            base_factor = 1.0
            
            for trade_date in dates:
                # 偶尔调整复权因子（模拟除权除息）
                if np.random.random() < 0.01:  # 1%概率调整
                    base_factor *= np.random.uniform(0.8, 1.2)
                
                data_list.append({
                    'ts_code': ts_code,
                    'trade_date': datetime.strptime(trade_date, '%Y%m%d').date(),
                    'adj_factor': round(base_factor, 6)
                })
            
            return pd.DataFrame(data_list)
            
        except Exception as e:
            logger.error(f"生成模拟复权因子失败: {e}")
            return pd.DataFrame()
    
    async def _get_mock_daily_data(self, ts_codes: List[str], trade_date: str = None,
                                 start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """生成模拟的每日行情数据"""
        try:
            # 确定日期范围
            if trade_date:
                dates = [datetime.strptime(trade_date, '%Y%m%d').date()]
            elif start_date and end_date:
                start = datetime.strptime(start_date, '%Y%m%d').date()
                end = datetime.strptime(end_date, '%Y%m%d').date()
                dates = []
                current = start
                while current <= end:
                    # 跳过周末
                    if current.weekday() < 5:
                        dates.append(current)
                    current += timedelta(days=1)
            else:
                # 默认最近5个交易日
                dates = []
                current = datetime.now().date()
                count = 0
                while count < 5:
                    if current.weekday() < 5:  # 跳过周末
                        dates.append(current)
                        count += 1
                    current -= timedelta(days=1)
                dates.reverse()
            
            data_list = []
            
            for ts_code in ts_codes:
                # 为每只股票生成基础价格
                base_price = np.random.uniform(10, 200)
                
                for trade_date in dates:
                    # 生成当日价格波动
                    price_change = np.random.uniform(-0.1, 0.1)  # ±10%波动
                    current_price = base_price * (1 + price_change)
                    
                    # 生成OHLC数据
                    open_price = current_price * np.random.uniform(0.98, 1.02)
                    high_price = max(open_price, current_price) * np.random.uniform(1.0, 1.05)
                    low_price = min(open_price, current_price) * np.random.uniform(0.95, 1.0)
                    close_price = current_price
                    pre_close = base_price
                    
                    # 计算涨跌幅
                    change_amount = close_price - pre_close
                    change_pct = (change_amount / pre_close) * 100
                    
                    data_list.append({
                        'ts_code': ts_code,
                        'trade_date': trade_date.strftime('%Y-%m-%d'),
                        'open_price': round(open_price, 4),
                        'high_price': round(high_price, 4),
                        'low_price': round(low_price, 4),
                        'close_price': round(close_price, 4),
                        'pre_close': round(pre_close, 4),
                        'change_amount': round(change_amount, 4),
                        'change_pct': round(change_pct, 4),
                        'volume': np.random.randint(10000, 1000000),
                        'amount': round(np.random.uniform(100000, 10000000), 2),
                        'turnover_rate': round(np.random.uniform(0.1, 15), 4),
                        'volume_ratio': round(np.random.uniform(0.5, 3.0), 4),
                        'pe': round(np.random.uniform(8, 80), 4),
                        'pb': round(np.random.uniform(0.8, 15), 4),
                        'ps': round(np.random.uniform(1, 20), 4),
                        'pcf': round(np.random.uniform(5, 50), 4),
                        'market_cap': round(np.random.uniform(1000000, 50000000), 2),
                        'circ_mv': round(np.random.uniform(800000, 40000000), 2)
                    })
                
                # 更新基础价格用于下一个交易日
                base_price = current_price
            
            return pd.DataFrame(data_list)
            
        except Exception as e:
            logger.error(f"生成模拟数据失败: {e}")
            return pd.DataFrame()
    
    # ==================== 数据保存方法 ====================
    
    async def _save_stock_basic(self, df: pd.DataFrame) -> int:
        """保存股票基础信息到数据库"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                saved_count = 0
                for _, row in df.iterrows():
                    try:
                        sql = """
                        INSERT INTO stock_basic (
                            ts_code, symbol, name, area, industry, market, exchange, 
                            curr_type, list_status, list_date, delist_date, is_hs
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            name = VALUES(name),
                            area = VALUES(area),
                            industry = VALUES(industry),
                            market = VALUES(market),
                            exchange = VALUES(exchange),
                            curr_type = VALUES(curr_type),
                            list_status = VALUES(list_status),
                            delist_date = VALUES(delist_date),
                            is_hs = VALUES(is_hs),
                            updated_at = CURRENT_TIMESTAMP
                        """
                        
                        cursor.execute(sql, (
                            row['ts_code'], row['symbol'], row['name'],
                            row.get('area'), row.get('industry'), row.get('market'),
                            row.get('exchange'), row.get('curr_type', 'CNY'),
                            row.get('list_status', 'L'), row.get('list_date'),
                            row.get('delist_date'), row.get('is_hs')
                        ))
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"保存股票基础信息失败 {row['ts_code']}: {e}")
                        continue
                
                conn.commit()
                return saved_count
                
        except Exception as e:
            logger.error(f"保存股票基础信息失败: {e}")
            return 0
    
    async def _save_trade_calendar(self, df: pd.DataFrame) -> int:
        """保存交易日历到数据库"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                saved_count = 0
                for _, row in df.iterrows():
                    try:
                        sql = """
                        INSERT INTO trade_cal (
                            exchange, cal_date, is_open, pretrade_date
                        ) VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            is_open = VALUES(is_open),
                            pretrade_date = VALUES(pretrade_date),
                            updated_at = CURRENT_TIMESTAMP
                        """
                        
                        cursor.execute(sql, (
                            row['exchange'], row['cal_date'], row['is_open'],
                            row.get('pretrade_date')
                        ))
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"保存交易日历失败: {e}")
                        continue
                
                conn.commit()
                return saved_count
                
        except Exception as e:
            logger.error(f"保存交易日历失败: {e}")
            return 0
    
    async def _save_daily_basic(self, df: pd.DataFrame) -> int:
        """保存每日指标到数据库"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                saved_count = 0
                for _, row in df.iterrows():
                    try:
                        sql = """
                        INSERT INTO daily_basic (
                            ts_code, trade_date, close, turnover_rate, turnover_rate_f,
                            volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm,
                            total_share, float_share, free_share, total_mv, circ_mv
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            close = VALUES(close),
                            turnover_rate = VALUES(turnover_rate),
                            turnover_rate_f = VALUES(turnover_rate_f),
                            volume_ratio = VALUES(volume_ratio),
                            pe = VALUES(pe),
                            pe_ttm = VALUES(pe_ttm),
                            pb = VALUES(pb),
                            ps = VALUES(ps),
                            ps_ttm = VALUES(ps_ttm),
                            dv_ratio = VALUES(dv_ratio),
                            dv_ttm = VALUES(dv_ttm),
                            total_share = VALUES(total_share),
                            float_share = VALUES(float_share),
                            free_share = VALUES(free_share),
                            total_mv = VALUES(total_mv),
                            circ_mv = VALUES(circ_mv),
                            updated_at = CURRENT_TIMESTAMP
                        """
                        
                        cursor.execute(sql, (
                            row['ts_code'], row['trade_date'], row.get('close'),
                            row.get('turnover_rate'), row.get('turnover_rate_f'),
                            row.get('volume_ratio'), row.get('pe'), row.get('pe_ttm'),
                            row.get('pb'), row.get('ps'), row.get('ps_ttm'),
                            row.get('dv_ratio'), row.get('dv_ttm'), row.get('total_share'),
                            row.get('float_share'), row.get('free_share'),
                            row.get('total_mv'), row.get('circ_mv')
                        ))
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"保存每日指标失败 {row['ts_code']}: {e}")
                        continue
                
                conn.commit()
                return saved_count
                
        except Exception as e:
            logger.error(f"保存每日指标失败: {e}")
            return 0
    
    async def _save_adj_factor(self, df: pd.DataFrame) -> int:
        """保存复权因子到数据库"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                saved_count = 0
                for _, row in df.iterrows():
                    try:
                        sql = """
                        INSERT INTO adj_factor (
                            ts_code, trade_date, adj_factor
                        ) VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            adj_factor = VALUES(adj_factor),
                            updated_at = CURRENT_TIMESTAMP
                        """
                        
                        cursor.execute(sql, (
                            row['ts_code'], row['trade_date'], row.get('adj_factor')
                        ))
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"保存复权因子失败 {row['ts_code']}: {e}")
                        continue
                
                conn.commit()
                return saved_count
                
        except Exception as e:
            logger.error(f"保存复权因子失败: {e}")
            return 0
        """生成模拟的每日行情数据"""
        try:
            # 确定日期范围
            if trade_date:
                dates = [datetime.strptime(trade_date, '%Y%m%d').date()]
            elif start_date and end_date:
                start = datetime.strptime(start_date, '%Y%m%d').date()
                end = datetime.strptime(end_date, '%Y%m%d').date()
                dates = []
                current = start
                while current <= end:
                    # 跳过周末
                    if current.weekday() < 5:
                        dates.append(current)
                    current += timedelta(days=1)
            else:
                # 默认最近5个交易日
                dates = []
                current = datetime.now().date()
                count = 0
                while count < 5:
                    if current.weekday() < 5:  # 跳过周末
                        dates.append(current)
                        count += 1
                    current -= timedelta(days=1)
                dates.reverse()
            
            data_list = []
            
            for ts_code in ts_codes:
                # 为每只股票生成基础价格
                base_price = np.random.uniform(10, 200)
                
                for trade_date in dates:
                    # 生成当日价格波动
                    price_change = np.random.uniform(-0.1, 0.1)  # ±10%波动
                    current_price = base_price * (1 + price_change)
                    
                    # 生成OHLC数据
                    open_price = current_price * np.random.uniform(0.98, 1.02)
                    high_price = max(open_price, current_price) * np.random.uniform(1.0, 1.05)
                    low_price = min(open_price, current_price) * np.random.uniform(0.95, 1.0)
                    close_price = current_price
                    pre_close = base_price
                    
                    # 计算涨跌幅
                    change_amount = close_price - pre_close
                    change_pct = (change_amount / pre_close) * 100
                    
                    data_list.append({
                        'ts_code': ts_code,
                        'trade_date': trade_date.strftime('%Y-%m-%d'),
                        'open_price': round(open_price, 4),
                        'high_price': round(high_price, 4),
                        'low_price': round(low_price, 4),
                        'close_price': round(close_price, 4),
                        'pre_close': round(pre_close, 4),
                        'change_amount': round(change_amount, 4),
                        'change_pct': round(change_pct, 4),
                        'volume': np.random.randint(10000, 1000000),
                        'amount': round(np.random.uniform(100000, 10000000), 2),
                        'turnover_rate': round(np.random.uniform(0.1, 15), 4),
                        'volume_ratio': round(np.random.uniform(0.5, 3.0), 4),
                        'pe': round(np.random.uniform(8, 80), 4),
                        'pb': round(np.random.uniform(0.8, 15), 4),
                        'ps': round(np.random.uniform(1, 20), 4),
                        'pcf': round(np.random.uniform(5, 50), 4),
                        'market_cap': round(np.random.uniform(1000000, 50000000), 2),
                        'circ_mv': round(np.random.uniform(800000, 40000000), 2)
                    })
                
                # 更新基础价格用于下一个交易日
                base_price = current_price
            
            return pd.DataFrame(data_list)
            
        except Exception as e:
            logger.error(f"生成模拟数据失败: {e}")
            return pd.DataFrame()
    
    def _format_tushare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """格式化Tushare数据"""
        try:
            if df.empty:
                return df
            
            # 重命名字段以匹配数据库结构
            column_mapping = {
                'open': 'open_price',
                'high': 'high_price', 
                'low': 'low_price',
                'close': 'close_price',
                'change': 'change_amount',
                'pct_chg': 'change_pct',
                'vol': 'volume',
                'amount': 'amount'
            }
            
            df = df.rename(columns=column_mapping)
            
            # 转换数据类型
            numeric_columns = [
                'open_price', 'high_price', 'low_price', 'close_price', 'pre_close',
                'change_amount', 'change_pct', 'volume', 'amount', 'turnover_rate',
                'volume_ratio', 'pe', 'pb', 'ps', 'pcf', 'market_cap', 'circ_mv'
            ]
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 转换日期格式
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
            
            return df
            
        except Exception as e:
            logger.error(f"格式化Tushare数据失败: {e}")
            return df
    
    async def _save_daily_history(self, df: pd.DataFrame) -> int:
        """保存每日行情数据到数据库"""
        try:
            if df.empty:
                return 0
            
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                saved_count = 0
                for _, row in df.iterrows():
                    try:
                        sql = """
                        INSERT INTO daily_history (
                            ts_code, trade_date, open_price, high_price, low_price, close_price,
                            pre_close, change_amount, change_pct, volume, amount, turnover_rate,
                            volume_ratio, pe, pb, ps, pcf, market_cap, circ_mv
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            open_price = VALUES(open_price),
                            high_price = VALUES(high_price),
                            low_price = VALUES(low_price),
                            close_price = VALUES(close_price),
                            pre_close = VALUES(pre_close),
                            change_amount = VALUES(change_amount),
                            change_pct = VALUES(change_pct),
                            volume = VALUES(volume),
                            amount = VALUES(amount),
                            turnover_rate = VALUES(turnover_rate),
                            volume_ratio = VALUES(volume_ratio),
                            pe = VALUES(pe),
                            pb = VALUES(pb),
                            ps = VALUES(ps),
                            pcf = VALUES(pcf),
                            market_cap = VALUES(market_cap),
                            circ_mv = VALUES(circ_mv),
                            updated_at = CURRENT_TIMESTAMP
                        """
                        
                        cursor.execute(sql, (
                            row['ts_code'], row['trade_date'], row.get('open_price'),
                            row.get('high_price'), row.get('low_price'), row.get('close_price'),
                            row.get('pre_close'), row.get('change_amount'), row.get('change_pct'),
                            row.get('volume'), row.get('amount'), row.get('turnover_rate'),
                            row.get('volume_ratio'), row.get('pe'), row.get('pb'),
                            row.get('ps'), row.get('pcf'), row.get('market_cap'), row.get('circ_mv')
                        ))
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"保存行情数据失败 {row['ts_code']}: {e}")
                        continue
                
                conn.commit()
                return saved_count
                
        except Exception as e:
            logger.error(f"保存每日行情数据失败: {e}")
            return 0


# 创建全局实例
tushare_daily_service = TushareDailyService()