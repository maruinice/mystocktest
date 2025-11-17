#!/usr/bin/env python3
"""
同步申万行业分类数据
Tushare接口: index_classify
接口文档: https://tushare.pro/document/2?doc_id=181
"""
import sys
import os
import asyncio
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.tushare_enhanced_service import TushareEnhancedService
from app.config.settings import settings
from sqlalchemy import text
import pandas as pd

print("\n" + "="*70)
print("申万行业分类数据同步")
print("="*70)

# 检查配置
if not settings.TUSHARE_TOKEN:
    print("❌ Tushare Token未配置！")
    sys.exit(1)
else:
    print(f"✅ Tushare Token已配置")

class IndustryClassificationSyncService:
    """行业分类同步服务"""
    
    def __init__(self):
        self.tushare = TushareEnhancedService()
        self.db = next(get_db())
    
    async def sync_all_industries(self):
        """
        同步所有股票的申万行业分类数据
        按级别一次性获取所有行业分类数据
        """
        try:
            print(f"\n同步申万行业分类（SW2021标准）")
            print(f"⏳ 预计需要5-10分钟（需要获取每个行业的成分股）...\n")
            
            # 申万行业分类支持三个级别：L1(一级)、L2(二级)、L3(三级)
            levels = ['L1', 'L2', 'L3']
            level_names = {'L1': '一级行业', 'L2': '二级行业', 'L3': '三级行业'}
            
            total_count = 0
            
            # 按级别同步
            for level in levels:
                try:
                    print(f"\n正在同步 {level_names[level]}...", end=' ', flush=True)
                    
                    # 一次性获取该级别的所有行业分类
                    df = await self._get_tushare_industry_all(level)
                    
                    if df.empty:
                        print("⚠️  无数据")
                        continue
                    
                    # 批量插入数据
                    count = await self._batch_insert_industries(df, level)
                    
                    print(f"✅ {count} 条记录")
                    total_count += count
                    
                    # 延迟控制
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ 失败: {e}")
                    continue
            
            # 汇总统计
            print("\n" + "="*70)
            print("同步汇总")
            print("="*70)
            print(f"总记录数: {total_count}")
            
            # 数据库统计
            print("\n数据库统计:")
            print("-"*70)
            self._print_database_stats()
            
            print("\n" + "="*70)
            print("🎉 申万行业分类数据同步完成！")
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
    
    async def _get_tushare_industry_all(self, level: str) -> pd.DataFrame:
        """
        获取所有股票的行业分类数据
        
        Args:
            level: 行业级别 (L1/L2/L3)
            
        Returns:
            股票行业分类DataFrame
            
        接口: ths_member (同花顺概念和行业成分)
        字段: ts_code, code, name
        """
        try:
            # 先获取该级别的所有行业代码
            industry_list = self.tushare.pro.index_classify(level=level, src='SW2021')
            
            print(f"\n  获取到 {len(industry_list)} 个行业")
            
            all_stocks = []
            
            # 对每个行业，获取其成分股
            for _, industry in industry_list.iterrows():
                index_code = industry['index_code']
                industry_name = industry['industry_name']
                industry_code = industry['industry_code']
                
                try:
                    # 获取该行业的成分股
                    members = self.tushare.pro.index_member(index_code=index_code)
                    
                    if not members.empty:
                        # 添加行业信息
                        members['industry_code'] = industry_code
                        members['industry_name'] = industry_name
                        members['level'] = level
                        all_stocks.append(members)
                        print(f"    {industry_name}: {len(members)} 只股票", end='\r')
                    
                    time.sleep(0.3)  # 控制频率
                    
                except Exception as e:
                    print(f"\n    获取 {industry_name} 成分股失败: {e}")
                    continue
            
            if all_stocks:
                df = pd.concat(all_stocks, ignore_index=True)
                print(f"\n  合计 {len(df)} 条股票-行业关系")
                return df
            else:
                return pd.DataFrame()
            
        except Exception as e:
            raise e
    
    async def _batch_insert_industries(self, df: pd.DataFrame, level: str) -> int:
        """
        批量插入行业分类数据
        
        Args:
            df: 行业分类数据
            level: 行业级别
            
        Returns:
            插入的记录数
        """
        try:
            count = 0
            level_map = {'L1': 1, 'L2': 2, 'L3': 3}
            level_num = level_map.get(level, 1)
            
            for _, row in df.iterrows():
                try:
                    # 从index_member返回的字段获取数据
                    ts_code = row.get('con_code', '')  # 成分股代码
                    industry_code = row.get('industry_code', '')  # 我们添加的行业代码
                    industry_name = row.get('industry_name', '')  # 我们添加的行业名称
                    
                    if not ts_code or not industry_code:
                        continue
                    
                    # 插入SQL
                    insert_sql = text("""
                        INSERT INTO industry_classification 
                        (ts_code, industry_code, industry_name, level, classification_type, created_at, updated_at)
                        VALUES (:ts_code, :industry_code, :industry_name, :level, :classification_type, :created_at, :updated_at)
                        ON DUPLICATE KEY UPDATE
                        industry_name = VALUES(industry_name),
                        updated_at = VALUES(updated_at)
                    """)
                    
                    self.db.execute(insert_sql, {
                        'ts_code': ts_code,
                        'industry_code': industry_code,
                        'industry_name': industry_name,
                        'level': level_num,
                        'classification_type': 'SW2021',
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    })
                    
                    count += 1
                    
                except Exception as e:
                    print(f"\n  插入失败 {row.get('con_code', '')}: {e}")
                    continue
            
            self.db.commit()
            return count
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    
    def _print_database_stats(self):
        """打印数据库统计信息"""
        try:
            # 总记录数
            result = self.db.execute(text("""
                SELECT COUNT(*) as count FROM industry_classification
            """)).first()
            print(f"总记录数: {result.count:,}")
            
            # 按级别统计
            result = self.db.execute(text("""
                SELECT level, COUNT(*) as count
                FROM industry_classification
                GROUP BY level
                ORDER BY level
            """)).fetchall()
            print("\n按级别统计:")
            level_names = {1: '一级行业', 2: '二级行业', 3: '三级行业'}
            for row in result:
                print(f"  {level_names.get(row.level, f'级别{row.level}')}: {row.count:,} 条")
            
            # 股票覆盖率
            result = self.db.execute(text("""
                SELECT COUNT(DISTINCT ts_code) as count
                FROM industry_classification
            """)).first()
            print(f"\n股票覆盖数: {result.count:,}")
            
            # 一级行业分布
            result = self.db.execute(text("""
                SELECT industry_name, COUNT(*) as count
                FROM industry_classification
                WHERE level = 1
                GROUP BY industry_name
                ORDER BY count DESC
                LIMIT 10
            """)).fetchall()
            print("\n一级行业TOP10:")
            for row in result:
                print(f"  {row.industry_name}: {row.count:,} 只股票")
            
            # 最新数据示例
            result = self.db.execute(text("""
                SELECT ts_code, industry_code, industry_name, level
                FROM industry_classification
                WHERE level = 1
                ORDER BY updated_at DESC
                LIMIT 5
            """)).fetchall()
            print("\n最新5条记录（一级行业）:")
            for row in result:
                print(f"  {row.ts_code} | {row.industry_code} | {row.industry_name}")
            
        except Exception as e:
            print(f"统计失败: {e}")


async def main():
    """主函数"""
    service = IndustryClassificationSyncService()
    
    # 同步申万行业分类数据（一次性获取所有级别）
    await service.sync_all_industries()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  同步被用户中断")
    except Exception as e:
        print(f"\n\n❌ 同步过程出错: {e}")
        import traceback
        traceback.print_exc()
