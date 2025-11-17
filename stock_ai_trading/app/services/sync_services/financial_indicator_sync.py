"""
财务指标同步服务
基于 sync_financial_indicators.py 改造
"""

import logging
import time
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text
import pandas as pd

from .base_sync_service import BaseSyncService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class FinancialIndicatorSyncService(BaseSyncService):
    """财务指标同步服务"""
    
    async def sync(self, start_date: str = None, end_date: str = None, start_position: int = 1, **kwargs) -> Dict[str, Any]:
        """
        同步财务指标数据
        
        Args:
            start_date: 开始日期 (YYYYMMDD)，默认为数据库最新日期
            end_date: 结束日期 (YYYYMMDD)，默认为今天
            start_position: 起始位置（断点续传）
            
        Returns:
            同步结果
        """
        try:
            self.start_sync()
            
            if not self.pro:
                raise ValueError("Tushare API未初始化")
            
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            if not start_date:
                # 尝试从数据库获取最新日期
                last_date = await self.get_last_sync_date('financial_indicators', 'ann_date')
                if last_date:
                    start_date = last_date
                else:
                    # 默认3年前
                    start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
            
            self.update_progress(0, 1, f"准备同步财务指标: {start_date} - {end_date}")
            
            # 获取所有股票代码
            stock_codes = await self._get_all_stock_codes()
            if not stock_codes:
                self.finish_sync(False, "未找到股票代码")
                return {'success': False, 'message': '未找到股票代码'}
            
            total_stocks = len(stock_codes)
            
            # 检查断点续传
            saved_position = await self.get_sync_position('financial_indicator_sync')
            if saved_position and start_position == 1:
                start_position = int(saved_position)
                logger.info(f"从断点位置继续: {start_position}")
            
            if start_position > total_stocks:
                self.finish_sync(False, f"起始位置超出范围: {start_position} > {total_stocks}")
                return {'success': False, 'message': '起始位置超出范围'}
            
            self.update_progress(0, total_stocks, f"开始同步 {total_stocks} 只股票的财务指标")
            
            # 逐个股票同步
            total_count = 0
            success_count = 0
            
            for i, ts_code in enumerate(stock_codes[start_position-1:], start_position):
                try:
                    count = await self._sync_stock_financial_indicators(
                        ts_code, start_date, end_date
                    )
                    
                    if count > 0:
                        success_count += 1
                        total_count += count
                    
                    # 更新进度
                    self.update_progress(
                        i, 
                        total_stocks, 
                        f"已同步 {i}/{total_stocks} 只股票，共 {total_count} 条记录"
                    )
                    
                    # 保存断点
                    if i % 10 == 0:
                        await self.save_sync_position('financial_indicator_sync', str(i))
                    
                    # API频率控制
                    if i % 10 == 0:
                        time.sleep(0.5)
                    else:
                        time.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"同步股票 {ts_code} 失败: {e}")
                    continue
            
            # 清除断点
            await self.clear_sync_position('financial_indicator_sync')
            
            self.update_progress(total_stocks, total_stocks, f"同步完成，共 {total_count} 条记录")
            self.finish_sync(True)
            
            return {
                'success': True,
                'message': f'成功同步{total_count}条财务指标',
                'data': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_stocks': total_stocks,
                    'success_stocks': success_count,
                    'total_records': total_count,
                    'sync_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            error_msg = f"同步失败: {str(e)}"
            logger.error(error_msg)
            self.finish_sync(False, error_msg)
            return {'success': False, 'message': error_msg}
    
    async def _get_all_stock_codes(self):
        """获取所有股票代码"""
        try:
            db = next(get_db())
            query = text("SELECT ts_code FROM stock_basic WHERE list_status='L' ORDER BY ts_code")
            result = db.execute(query).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"获取股票代码失败: {e}")
            return []
    
    async def _sync_stock_financial_indicators(self, ts_code: str, start_date: str, end_date: str) -> int:
        """同步单只股票的财务指标"""
        try:
            # 调用Tushare API
            df = self.pro.fina_indicator(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,ann_date,end_date,eps,dt_eps,total_revenue_ps,revenue_ps,'
                       'capital_rese_ps,surplus_rese_ps,undist_profit_ps,extra_item,profit_dedt,'
                       'gross_margin,current_ratio,quick_ratio,cash_ratio,invturn_days,arturn_days,'
                       'inv_turn,ar_turn,ca_turn,fa_turn,assets_turn,op_income,valuechange_income,'
                       'interst_income,daa,ebit,ebitda,fcff,fcfe,current_exint,noncurrent_exint,'
                       'interestdebt,netdebt,tangible_asset,working_capital,networking_capital,'
                       'invest_capital,retained_earnings,diluted2_eps,bps,ocfps,retainedps,cfps,'
                       'ebit_ps,fcff_ps,fcfe_ps,netprofit_margin,grossprofit_margin,cogs_of_sales,'
                       'expense_of_sales,profit_to_gr,saleexp_to_gr,adminexp_of_gr,finaexp_of_gr,'
                       'impai_ttm,gc_of_gr,op_of_gr,ebit_of_gr,roe,roe_waa,roe_dt,roa,npta,roic,'
                       'roe_yearly,roa_yearly,roe_avg,opincome_of_ebt,investincome_of_ebt,'
                       'n_op_profit_of_ebt,tax_to_ebt,dtprofit_to_profit,salescash_to_or,'
                       'ocf_to_or,ocf_to_opincome,capitalized_to_da,debt_to_assets,assets_to_eqt,'
                       'dp_assets_to_eqt,ca_to_assets,nca_to_assets,tbassets_to_totalassets,'
                       'int_to_talcap,eqt_to_talcapital,currentdebt_to_debt,longdeb_to_debt,'
                       'ocf_to_shortdebt,debt_to_eqt,eqt_to_debt,eqt_to_interestdebt,'
                       'tangibleasset_to_debt,tangasset_to_intdebt,tangibleasset_to_netdebt,'
                       'ocf_to_debt,ocf_to_interestdebt,ocf_to_netdebt,ebit_to_interest,'
                       'longdebt_to_workingcapital,ebitda_to_debt,turn_days,roa_dp,fixed_assets,'
                       'profit_prefin_exp,non_op_profit,op_to_ebt,nop_to_ebt,ocf_to_profit,'
                       'cash_to_liqdebt,cash_to_liqdebt_withinterest,op_to_liqdebt,op_to_debt,'
                       'roic_yearly,total_fa_trun,profit_to_op,q_opincome,q_investincome,'
                       'q_dtprofit,q_eps,q_netprofit_margin,q_gsprofit_margin,q_exp_to_sales,'
                       'q_profit_to_gr,q_saleexp_to_gr,q_adminexp_to_gr,q_finaexp_to_gr,'
                       'q_impair_to_gr_ttm,q_gc_to_gr,q_op_to_gr,q_roe,q_dt_roe,q_npta,'
                       'q_opincome_to_ebt,q_investincome_to_ebt,q_dtprofit_to_profit,'
                       'q_salescash_to_or,q_ocf_to_sales,q_ocf_to_or,basic_eps_yoy,dt_eps_yoy,'
                       'cfps_yoy,op_yoy,ebt_yoy,netprofit_yoy,dt_netprofit_yoy,ocf_yoy,roe_yoy,'
                       'bps_yoy,assets_yoy,eqt_yoy,tr_yoy,or_yoy,q_gr_yoy,q_gr_qoq,q_sales_yoy,'
                       'q_sales_qoq,q_op_yoy,q_op_qoq,q_profit_yoy,q_profit_qoq,q_netprofit_yoy,'
                       'q_netprofit_qoq,equity_yoy,rd_exp,update_flag'
            )
            
            if df.empty:
                return 0
            
            # 保存到数据库
            db = next(get_db())
            count = 0
            
            for _, row in df.iterrows():
                try:
                    # 构建插入SQL（字段太多，这里简化处理）
                    insert_sql = text("""
                        INSERT INTO financial_indicators 
                        (ts_code, ann_date, end_date, eps, roe, roa, gross_margin, debt_to_assets, 
                         current_ratio, quick_ratio, updated_at)
                        VALUES (:ts_code, :ann_date, :end_date, :eps, :roe, :roa, :gross_margin, 
                                :debt_to_assets, :current_ratio, :quick_ratio, NOW())
                        ON DUPLICATE KEY UPDATE
                        eps = VALUES(eps),
                        roe = VALUES(roe),
                        roa = VALUES(roa),
                        gross_margin = VALUES(gross_margin),
                        debt_to_assets = VALUES(debt_to_assets),
                        current_ratio = VALUES(current_ratio),
                        quick_ratio = VALUES(quick_ratio),
                        updated_at = NOW()
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': row['ts_code'],
                        'ann_date': row.get('ann_date', ''),
                        'end_date': row.get('end_date', ''),
                        'eps': row.get('eps', None),
                        'roe': row.get('roe', None),
                        'roa': row.get('roa', None),
                        'gross_margin': row.get('gross_margin', None),
                        'debt_to_assets': row.get('debt_to_assets', None),
                        'current_ratio': row.get('current_ratio', None),
                        'quick_ratio': row.get('quick_ratio', None)
                    })
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"插入财务指标失败: {e}")
                    continue
            
            db.commit()
            return count
            
        except Exception as e:
            logger.error(f"同步股票 {ts_code} 财务指标失败: {e}")
            return 0
