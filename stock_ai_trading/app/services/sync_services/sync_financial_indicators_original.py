#!/usr/bin/env python3
"""
同步财务指标数据
Tushare接口文档: https://tushare.pro/document/2?doc_id=79
"""
import sys
import os
import asyncio
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.tushare_service import TushareService
from app.config.settings import settings
from sqlalchemy import text
import pandas as pd

print("\n" + "="*70)
print("财务指标数据同步")
print("="*70)

# 检查配置
if not settings.TUSHARE_TOKEN:
    print("❌ Tushare Token未配置！")
    sys.exit(1)
else:
    print(f"✅ Tushare Token已配置")

class FinancialIndicatorsSyncService:
    """财务指标同步服务"""
    
    def __init__(self):
        self.tushare = TushareService()
        self.db = next(get_db())
    
    async def sync_all_stocks(self, start_date: str = None, end_date: str = None, start_position: int = 1):
        """
        同步所有股票的财务指标数据
        
        Args:
            start_date: 开始日期 (YYYYMMDD)，默认为3年前
            end_date: 结束日期 (YYYYMMDD)，默认为今天
            start_position: 起始位置（从第几只股票开始），默认为1
        """
        try:
            # 设置默认日期范围（近3年）
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
            
            print(f"\n日期范围: {start_date} - {end_date}")
            if start_position > 1:
                print(f"⚠️  从第 {start_position} 只股票开始继续同步")
            print(f"⏳ 预计需要较长时间，请耐心等待...\n")
            
            # 1. 获取所有股票代码
            stock_codes = self._get_all_stock_codes()
            if not stock_codes:
                print("❌ 未找到股票代码")
                return
            
            print(f"获取到 {len(stock_codes)} 只股票")
            print("-"*70)
            
            # 检查起始位置
            if start_position > len(stock_codes):
                print(f"❌ 起始位置 {start_position} 超过了总股票数 {len(stock_codes)}")
                return
            
            # 2. 逐个股票同步
            total_count = 0
            success_count = 0
            failed_stocks = []
            
            # 从指定位置开始
            for i, ts_code in enumerate(stock_codes[start_position-1:], start_position):
                try:
                    print(f"[{i}/{len(stock_codes)}] 同步 {ts_code}...", end=' ', flush=True)
                    
                    # 调用Tushare API获取财务指标
                    count = await self._sync_stock_financial_indicators(
                        ts_code, start_date, end_date
                    )
                    
                    if count > 0:
                        print(f"✅ {count} 条")
                        success_count += 1
                        total_count += count
                    else:
                        print(f"⚠️  无数据")
                    
                    # 每10只股票延迟一下，避免API限流
                    if i % 10 == 0:
                        time.sleep(0.5)
                    else:
                        time.sleep(0.2)
                    
                except Exception as e:
                    print(f"❌ 失败: {e}")
                    failed_stocks.append(ts_code)
                    continue
            
            # 3. 汇总统计
            print("\n" + "="*70)
            print("同步汇总")
            print("="*70)
            print(f"总股票数: {len(stock_codes)}")
            print(f"成功: {success_count}")
            print(f"失败: {len(failed_stocks)}")
            print(f"总记录数: {total_count}")
            
            if failed_stocks:
                print(f"\n失败的股票 ({len(failed_stocks)}):")
                for code in failed_stocks[:20]:  # 只显示前20个
                    print(f"  - {code}")
                if len(failed_stocks) > 20:
                    print(f"  ... 还有 {len(failed_stocks)-20} 只")
            
            # 4. 数据库统计
            print("\n数据库统计:")
            print("-"*70)
            self._print_database_stats()
            
            print("\n" + "="*70)
            print("🎉 财务指标数据同步完成！")
            print("="*70)
            
        except Exception as e:
            print(f"\n❌ 同步失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_all_stock_codes(self) -> list:
        """从stock_basic表获取所有股票代码"""
        try:
            sql = text("""
                SELECT ts_code, name 
                FROM stock_basic 
                WHERE list_status = 'L'
                ORDER BY ts_code
            """)
            result = self.db.execute(sql).fetchall()
            return [row.ts_code for row in result]
        except Exception as e:
            print(f"❌ 获取股票代码失败: {e}")
            return []
    
    async def _sync_stock_financial_indicators(self, ts_code: str, 
                                               start_date: str, 
                                               end_date: str) -> int:
        """
        同步单只股票的财务指标数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            插入/更新的记录数
        """
        try:
            # 调用Tushare API
            df = await self._get_tushare_fina_indicator(ts_code, start_date, end_date)
            
            if df.empty:
                return 0
            
            # 插入数据库
            count = 0
            for _, row in df.iterrows():
                try:
                    upsert_sql = text("""
                        INSERT INTO financial_indicators (
                            ts_code, ann_date, end_date, report_type,
                            roe, roa, roic, gross_margin, net_margin,
                            revenue_growth, profit_growth, eps_growth,
                            debt_ratio, current_ratio, quick_ratio,
                            pe_ttm, pb_mrq, ps_ttm, peg,
                            eps, bps, revenue_per_share, cash_per_share,
                            created_at, updated_at
                        ) VALUES (
                            :ts_code, :ann_date, :end_date, :report_type,
                            :roe, :roa, :roic, :gross_margin, :net_margin,
                            :revenue_growth, :profit_growth, :eps_growth,
                            :debt_ratio, :current_ratio, :quick_ratio,
                            :pe_ttm, :pb_mrq, :ps_ttm, :peg,
                            :eps, :bps, :revenue_per_share, :cash_per_share,
                            :created_at, :updated_at
                        )
                        ON DUPLICATE KEY UPDATE
                            roe = VALUES(roe),
                            roa = VALUES(roa),
                            roic = VALUES(roic),
                            gross_margin = VALUES(gross_margin),
                            net_margin = VALUES(net_margin),
                            revenue_growth = VALUES(revenue_growth),
                            profit_growth = VALUES(profit_growth),
                            eps_growth = VALUES(eps_growth),
                            debt_ratio = VALUES(debt_ratio),
                            current_ratio = VALUES(current_ratio),
                            quick_ratio = VALUES(quick_ratio),
                            pe_ttm = VALUES(pe_ttm),
                            pb_mrq = VALUES(pb_mrq),
                            ps_ttm = VALUES(ps_ttm),
                            peg = VALUES(peg),
                            eps = VALUES(eps),
                            bps = VALUES(bps),
                            revenue_per_share = VALUES(revenue_per_share),
                            cash_per_share = VALUES(cash_per_share),
                            updated_at = VALUES(updated_at)
                    """)
                    
                    # 处理日期
                    ann_date = pd.to_datetime(str(row.get('ann_date', ''))).date() if pd.notna(row.get('ann_date')) else None
                    end_date_val = pd.to_datetime(str(row.get('end_date', ''))).date() if pd.notna(row.get('end_date')) else None
                    
                    self.db.execute(upsert_sql, {
                        'ts_code': ts_code,
                        'ann_date': ann_date,
                        'end_date': end_date_val,
                        'report_type': self._get_report_type(end_date_val),
                        
                        # 盈利能力指标
                        'roe': self._safe_float(row.get('roe'), -100, 100),
                        'roa': self._safe_float(row.get('roa'), -100, 100),
                        'roic': self._safe_float(row.get('roic'), -100, 100),
                        'gross_margin': self._safe_float(row.get('grossprofit_margin'), -100, 100),
                        'net_margin': self._safe_float(row.get('netprofit_margin'), -100, 100),
                        
                        # 成长能力指标（限制在合理范围）
                        'revenue_growth': self._safe_float(row.get('or_yoy'), -100, 1000),
                        'profit_growth': self._safe_float(row.get('profit_to_gr'), -100, 1000),
                        'eps_growth': self._safe_float(row.get('basic_eps_yoy'), -100, 1000),
                        
                        # 偿债能力指标
                        'debt_ratio': self._safe_float(row.get('debt_to_assets'), 0, 100),
                        'current_ratio': self._safe_float(row.get('current_ratio'), 0, 100),
                        'quick_ratio': self._safe_float(row.get('quick_ratio'), 0, 100),
                        
                        # 估值指标
                        'pe_ttm': self._safe_float(row.get('pe_ttm'), -1000, 10000),
                        'pb_mrq': self._safe_float(row.get('pb_mrq'), -100, 1000),
                        'ps_ttm': self._safe_float(row.get('ps_ttm'), -100, 1000),
                        'peg': self._safe_float(row.get('peg'), -100, 100),
                        
                        # 每股指标
                        'eps': self._safe_float(row.get('basic_eps'), -100, 100),
                        'bps': self._safe_float(row.get('bps'), -100, 1000),
                        'revenue_per_share': self._safe_float(row.get('revenue_ps'), -100, 1000),
                        'cash_per_share': self._safe_float(row.get('cfps'), -100, 1000),
                        
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    })
                    
                    count += 1
                    
                except Exception as e:
                    print(f"\n  插入数据失败: {e}")
                    continue
            
            self.db.commit()
            return count
            
        except Exception as e:
            print(f"\n  同步失败: {e}")
            return 0
    
    async def _get_tushare_fina_indicator(self, ts_code: str, 
                                         start_date: str, 
                                         end_date: str) -> pd.DataFrame:
        """
        调用Tushare财务指标接口
        
        接口: fina_indicator
        文档: https://tushare.pro/document/2?doc_id=79
        """
        try:
            # 调用Tushare API
            df = self.tushare.pro.fina_indicator(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,ann_date,end_date,roe,roa,roic,grossprofit_margin,netprofit_margin,'
                       'or_yoy,profit_to_gr,basic_eps_yoy,debt_to_assets,current_ratio,quick_ratio,'
                       'pe_ttm,pb_mrq,ps_ttm,peg,basic_eps,bps,revenue_ps,cfps'
            )
            
            return df
            
        except Exception as e:
            raise e
    
    def _safe_float(self, value, min_val: float = None, max_val: float = None) -> float:
        """
        安全转换浮点数，限制在合理范围内
        
        Args:
            value: 原始值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            处理后的浮点数或None
        """
        if pd.isna(value) or value is None:
            return None
        
        try:
            float_val = float(value)
            
            # 过滤异常值
            if float_val == float('inf') or float_val == float('-inf'):
                return None
            
            # 限制范围
            if min_val is not None and float_val < min_val:
                float_val = min_val
            if max_val is not None and float_val > max_val:
                float_val = max_val
            
            return float_val
        except (ValueError, TypeError):
            return None
    
    def _get_report_type(self, end_date) -> str:
        """根据报告期判断报告类型"""
        if not end_date:
            return 'unknown'
        
        month_day = end_date.strftime('%m%d')
        if month_day == '0331':
            return '一季报'
        elif month_day == '0630':
            return '半年报'
        elif month_day == '0930':
            return '三季报'
        elif month_day == '1231':
            return '年报'
        else:
            return 'other'
    
    def _print_database_stats(self):
        """打印数据库统计信息"""
        try:
            # 总记录数
            result = self.db.execute(text("""
                SELECT COUNT(*) as count FROM financial_indicators
            """)).first()
            print(f"总记录数: {result.count:,}")
            
            # 按年份统计
            result = self.db.execute(text("""
                SELECT YEAR(end_date) as year, COUNT(*) as count
                FROM financial_indicators
                GROUP BY YEAR(end_date)
                ORDER BY year DESC
                LIMIT 5
            """)).fetchall()
            print("\n按年份统计:")
            for row in result:
                print(f"  {row.year}: {row.count:,} 条")
            
            # 按报告类型统计
            result = self.db.execute(text("""
                SELECT report_type, COUNT(*) as count
                FROM financial_indicators
                GROUP BY report_type
                ORDER BY count DESC
            """)).fetchall()
            print("\n按报告类型统计:")
            for row in result:
                print(f"  {row.report_type}: {row.count:,} 条")
            
            # 股票覆盖率
            result = self.db.execute(text("""
                SELECT COUNT(DISTINCT ts_code) as count
                FROM financial_indicators
            """)).first()
            print(f"\n股票覆盖数: {result.count:,}")
            
            # 最新数据
            result = self.db.execute(text("""
                SELECT ts_code, end_date, roe, roa, eps
                FROM financial_indicators
                ORDER BY end_date DESC, updated_at DESC
                LIMIT 5
            """)).fetchall()
            print("\n最新5条记录:")
            for row in result:
                print(f"  {row.ts_code} | {row.end_date} | ROE:{row.roe:.2f}% | ROA:{row.roa:.2f}% | EPS:{row.eps:.2f}")
            
        except Exception as e:
            print(f"统计失败: {e}")


async def main():
    """主函数"""
    service = FinancialIndicatorsSyncService()
    
    # 解析命令行参数
    import sys
    start_position = 1
    
    if len(sys.argv) > 1:
        try:
            start_position = int(sys.argv[1])
            print(f"📍 从第 {start_position} 只股票开始同步")
        except ValueError:
            print("⚠️  起始位置参数无效，使用默认值 1")
    
    # 同步近3年的财务指标数据
    await service.sync_all_stocks(start_position=start_position)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  同步被用户中断")
    except Exception as e:
        print(f"\n\n❌ 同步过程出错: {e}")
        import traceback
        traceback.print_exc()
