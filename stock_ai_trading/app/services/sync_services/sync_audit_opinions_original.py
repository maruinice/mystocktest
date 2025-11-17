#!/usr/bin/env python3
"""
同步审计意见数据（近3年）
Tushare接口: fina_audit
"""
import sys
import os
import asyncio
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.tushare_enhanced_service import TushareEnhancedService
from app.config.settings import settings
from sqlalchemy import text
import pandas as pd

print("\n" + "="*70)
print("审计意见数据同步")
print("="*70)

# 检查配置
if not settings.TUSHARE_TOKEN:
    print("❌ Tushare Token未配置！")
    sys.exit(1)
else:
    print(f"✅ Tushare Token已配置")

class AuditOpinionsSyncService:
    """审计意见同步服务"""
    
    def __init__(self):
        self.tushare = TushareEnhancedService()
        self.db = next(get_db())
    
    async def sync_all_audit_opinions(self, start_date: str = None, end_date: str = None, start_position: int = 1):
        """
        同步所有审计意见数据
        
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
            print(f"⏳ 预计需要30-60分钟，请耐心等待...\n")
            
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
                    
                    # 调用Tushare API获取审计意见
                    count = await self._sync_stock_audit_opinions(
                        ts_code, start_date, end_date
                    )
                    
                    if count > 0:
                        print(f"✅ {count} 条")
                        success_count += 1
                        total_count += count
                    else:
                        print("⚠️  无数据")
                    
                    # 延迟控制：每分钟最多60次，即每次至少1秒
                    time.sleep(1.2)  # 1.2秒确保每分钟不超过50次
                    
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
            
            # 4. 数据库统计
            print("\n数据库统计:")
            print("-"*70)
            self._print_database_stats()
            
            print("\n" + "="*70)
            print("🎉 审计意见数据同步完成！")
            print("="*70)
            
        except Exception as e:
            print(f"\n❌ 同步失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_all_stock_codes(self) -> list:
        """
        从stock_basic表获取所有股票代码
        
        Returns:
            股票代码列表
        """
        try:
            result = self.db.execute(text("""
                SELECT ts_code FROM stock_basic 
                WHERE list_status = 'L'
                ORDER BY ts_code
            """)).fetchall()
            
            return [row.ts_code for row in result]
            
        except Exception as e:
            print(f"❌ 获取股票代码失败: {e}")
            return []
    
    async def _sync_stock_audit_opinions(self, ts_code: str, start_date: str, end_date: str) -> int:
        """
        同步单只股票的审计意见数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            插入的记录数
        """
        try:
            # 调用Tushare API
            df = await self._get_tushare_audit_opinions(ts_code, start_date, end_date)
            
            if df.empty:
                return 0
            
            count = 0
            for _, row in df.iterrows():
                if await self._insert_audit_opinion(row):
                    count += 1
            
            return count
            
        except Exception as e:
            raise e
    
    async def _get_tushare_audit_opinions(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        调用Tushare审计意见接口
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        接口: fina_audit
        字段: ts_code, ann_date, end_date, audit_result, audit_fees, 
              audit_agency, audit_sign, opinion_type
        """
        try:
            # 调用Tushare API（按股票代码查询）
            df = self.tushare.pro.fina_audit(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,ann_date,end_date,audit_result,audit_fees,'
                       'audit_agency,audit_sign,opinion_type'
            )
            
            return df
            
        except Exception as e:
            raise e
    
    async def _insert_audit_opinion(self, row) -> bool:
        """
        插入单条审计意见数据
        
        Args:
            row: 数据行
            
        Returns:
            是否成功
        """
        try:
            # 检查必要字段
            ts_code = row.get('ts_code', '')
            ann_date = row.get('ann_date', '')
            end_date = row.get('end_date', '')
            
            if not ts_code or not ann_date:
                return False
            
            # 插入SQL
            insert_sql = text("""
                INSERT INTO audit_opinions 
                (ts_code, ann_date, end_date, audit_result, audit_fees, 
                 audit_agency, audit_sign, opinion_type, created_at)
                VALUES (:ts_code, :ann_date, :end_date, :audit_result, :audit_fees,
                        :audit_agency, :audit_sign, :opinion_type, :created_at)
                ON DUPLICATE KEY UPDATE
                audit_result = VALUES(audit_result),
                audit_fees = VALUES(audit_fees),
                audit_agency = VALUES(audit_agency),
                audit_sign = VALUES(audit_sign),
                opinion_type = VALUES(opinion_type)
            """)
            
            # 处理日期
            ann_date_val = pd.to_datetime(str(ann_date)).date() if pd.notna(ann_date) and ann_date else None
            end_date_val = pd.to_datetime(str(end_date)).date() if pd.notna(end_date) and end_date else None
            
            # 处理审计费用
            audit_fees_val = None
            if pd.notna(row.get('audit_fees')) and row.get('audit_fees'):
                try:
                    audit_fees_val = float(row.get('audit_fees', 0))
                except (ValueError, TypeError):
                    audit_fees_val = None
            
            self.db.execute(insert_sql, {
                'ts_code': ts_code,
                'ann_date': ann_date_val,
                'end_date': end_date_val,
                'audit_result': row.get('audit_result', ''),
                'audit_fees': audit_fees_val,
                'audit_agency': row.get('audit_agency', ''),
                'audit_sign': row.get('audit_sign', ''),
                'opinion_type': row.get('opinion_type', ''),
                'created_at': datetime.now()
            })
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"\n  插入失败: {e}")
            return False
    
    def _print_database_stats(self):
        """打印数据库统计信息"""
        try:
            # 总记录数
            result = self.db.execute(text("""
                SELECT COUNT(*) as count FROM audit_opinions
            """)).first()
            print(f"总记录数: {result.count:,}")
            
            # 按年份统计
            result = self.db.execute(text("""
                SELECT YEAR(ann_date) as year, COUNT(*) as count
                FROM audit_opinions
                GROUP BY YEAR(ann_date)
                ORDER BY year DESC
                LIMIT 5
            """)).fetchall()
            print("\n按年份统计:")
            for row in result:
                print(f"  {row.year}: {row.count:,} 条")
            
            # 按审计意见类型统计
            result = self.db.execute(text("""
                SELECT opinion_type, COUNT(*) as count
                FROM audit_opinions
                WHERE opinion_type IS NOT NULL AND opinion_type != ''
                GROUP BY opinion_type
                ORDER BY count DESC
            """)).fetchall()
            print("\n按审计意见类型统计:")
            for row in result:
                print(f"  {row.opinion_type}: {row.count:,} 条")
            
            # 按审计机构统计
            result = self.db.execute(text("""
                SELECT audit_agency, COUNT(*) as count
                FROM audit_opinions
                WHERE audit_agency IS NOT NULL AND audit_agency != ''
                GROUP BY audit_agency
                ORDER BY count DESC
                LIMIT 10
            """)).fetchall()
            print("\n审计机构TOP10:")
            for row in result:
                print(f"  {row.audit_agency}: {row.count:,} 条")
            
            # 最新数据
            result = self.db.execute(text("""
                SELECT ts_code, ann_date, end_date, audit_result, opinion_type, audit_agency
                FROM audit_opinions
                ORDER BY ann_date DESC, created_at DESC
                LIMIT 5
            """)).fetchall()
            print("\n最新5条记录:")
            for row in result:
                print(f"  {row.ts_code} | {row.ann_date} | {row.audit_result} | {row.opinion_type} | {row.audit_agency}")
            
        except Exception as e:
            print(f"统计失败: {e}")


async def main():
    """主函数"""
    service = AuditOpinionsSyncService()
    
    # 解析命令行参数
    import sys
    start_position = 2711  # 默认从2711开始
    
    if len(sys.argv) > 1:
        try:
            start_position = int(sys.argv[1])
            print(f"📍 从第 {start_position} 只股票开始同步")
        except ValueError:
            print(f"⚠️  起始位置参数无效，使用默认值 {start_position}")
    
    # 同步近3年的审计意见数据
    await service.sync_all_audit_opinions(start_position=start_position)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  同步被用户中断")
    except Exception as e:
        print(f"\n\n❌ 同步过程出错: {e}")
        import traceback
        traceback.print_exc()
