#!/usr/bin/env python3
"""诊断选股问题"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.strategy_database_service import strategy_db_service
import pandas as pd
from datetime import datetime, timedelta

print("\n" + "="*70)
print("选股问题诊断")
print("="*70)

# 你的选股条件
conditions = {
    'debt_ratio': {'min': 0, 'max': 60},
    'current_ratio': {'min': 1, 'max': 1.5},
    'change_pct': {'min': -5, 'max': 20},
    'eps': {'min': 0.5, 'max': 10},
    'kdj_d': {'min': 20, 'max': 80},
    'kdj_k': {'min': 20, 'max': 80},
    'profit_growth': {'min': 10, 'max': 100},
    'quick_ratio': {'min': 1, 'max': 3},
    'revenue_growth': {'min': 10, 'max': 100},
    'roa': {'min': 5, 'max': 30},
    'roe': {'min': 10, 'max': 50},
    'rsi12': {'min': 30, 'max': 70},
    'turnover_rate': {'min': 0, 'max': 50},
    'volume_ratio': {'min': 1, 'max': 10}
}

try:
    with strategy_db_service.get_connection() as conn:
        cursor = conn.cursor()
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 1. 检查stock_basic表
        print("\n1. 检查 stock_basic 表")
        print("-"*70)
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM stock_basic 
            WHERE list_status = 'L' AND sync_status = 'active'
        """)
        result = cursor.fetchone()
        print(f"  符合条件的股票数: {result['count']}")
        
        # 2. 检查每个字段的数据覆盖率
        print("\n2. 检查数据覆盖率")
        print("-"*70)
        
        # 获取500只股票样本
        cursor.execute("""
            SELECT ts_code 
            FROM stock_basic 
            WHERE list_status = 'L' AND sync_status = 'active'
            LIMIT 500
        """)
        stocks = cursor.fetchall()
        ts_codes = [s['ts_code'] for s in stocks]
        
        if not ts_codes:
            print("  ❌ 没有找到股票数据！")
            sys.exit(1)
        
        print(f"  样本股票数: {len(ts_codes)}")
        
        # 检查各表数据覆盖率
        tables_fields = {
            'daily_history': ['close_price', 'change_pct', 'turnover_rate', 'volume_ratio'],
            'daily_basic': ['pe', 'pb', 'market_cap'],
            'financial_indicators': ['roe', 'roa', 'eps', 'profit_growth', 'revenue_growth', 
                                    'debt_ratio', 'current_ratio', 'quick_ratio']
        }
        
        for table, fields in tables_fields.items():
            print(f"\n  表: {table}")
            for field in fields:
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT ts_code) as count
                    FROM {table}
                    WHERE ts_code IN ({','.join([f"'{c}'" for c in ts_codes])})
                    AND {field} IS NOT NULL
                    AND trade_date >= '{one_year_ago}'
                """ if table != 'financial_indicators' else f"""
                    SELECT COUNT(DISTINCT ts_code) as count
                    FROM {table}
                    WHERE ts_code IN ({','.join([f"'{c}'" for c in ts_codes])})
                    AND {field} IS NOT NULL
                """)
                result = cursor.fetchone()
                coverage = (result['count'] / len(ts_codes)) * 100
                status = "✅" if coverage > 50 else "⚠️" if coverage > 10 else "❌"
                print(f"    {status} {field}: {result['count']}/{len(ts_codes)} ({coverage:.1f}%)")
        
        # 3. 检查条件字段的数据分布
        print("\n3. 检查条件字段的数据分布")
        print("-"*70)
        
        # 获取一个完整的样本数据
        cursor.execute(f"""
            SELECT 
                sb.ts_code,
                dh.change_pct,
                dh.turnover_rate,
                dh.volume_ratio,
                fi.roe,
                fi.roa,
                fi.eps,
                fi.profit_growth,
                fi.revenue_growth,
                fi.debt_ratio,
                fi.current_ratio,
                fi.quick_ratio
            FROM stock_basic sb
            LEFT JOIN (
                SELECT ts_code, change_pct, turnover_rate, volume_ratio
                FROM daily_history
                WHERE trade_date >= '{one_year_ago}'
                AND ts_code IN ({','.join([f"'{c}'" for c in ts_codes[:100]])})
                GROUP BY ts_code
                HAVING trade_date = MAX(trade_date)
            ) dh ON sb.ts_code = dh.ts_code
            LEFT JOIN (
                SELECT ts_code, roe, roa, eps, profit_growth, revenue_growth, 
                       debt_ratio, current_ratio, quick_ratio
                FROM financial_indicators
                WHERE ts_code IN ({','.join([f"'{c}'" for c in ts_codes[:100]])})
                GROUP BY ts_code
                HAVING updated_at = MAX(updated_at)
            ) fi ON sb.ts_code = fi.ts_code
            WHERE sb.ts_code IN ({','.join([f"'{c}'" for c in ts_codes[:100]])})
            LIMIT 100
        """)
        
        data = cursor.fetchall()
        df = pd.DataFrame(data)
        
        print(f"  样本数据行数: {len(df)}")
        
        # 检查每个条件字段
        for field, condition in conditions.items():
            if field not in df.columns:
                print(f"  ❌ {field}: 字段不存在")
                continue
            
            non_null = df[field].notna().sum()
            if non_null == 0:
                print(f"  ❌ {field}: 无数据 (0/{len(df)})")
                continue
            
            min_val = condition.get('min')
            max_val = condition.get('max')
            
            # 统计满足条件的数量
            mask = df[field].notna()
            if min_val is not None:
                mask &= (df[field] >= min_val)
            if max_val is not None:
                mask &= (df[field] <= max_val)
            
            match_count = mask.sum()
            
            # 显示数据范围
            actual_min = df[field].min()
            actual_max = df[field].max()
            actual_mean = df[field].mean()
            
            status = "✅" if match_count > 0 else "❌"
            print(f"  {status} {field}: {match_count}/{non_null} 满足条件")
            print(f"      条件: [{min_val}, {max_val}]")
            print(f"      实际: [{actual_min:.2f}, {actual_max:.2f}], 平均: {actual_mean:.2f}")
        
        # 4. 模拟完整筛选
        print("\n4. 模拟完整筛选")
        print("-"*70)
        
        filtered_df = df.copy()
        print(f"  初始数据: {len(filtered_df)} 条")
        
        for field, condition in conditions.items():
            if field not in filtered_df.columns:
                continue
            
            before = len(filtered_df)
            min_val = condition.get('min')
            max_val = condition.get('max')
            
            if min_val is not None:
                filtered_df = filtered_df[filtered_df[field] >= min_val]
            if max_val is not None:
                filtered_df = filtered_df[filtered_df[field] <= max_val]
            
            after = len(filtered_df)
            if before != after:
                print(f"  应用 {field}: {before} → {after} (-{before-after})")
            
            if after == 0:
                print(f"  ❌ 在 {field} 条件后，没有股票满足条件！")
                break
        
        print(f"\n  最终结果: {len(filtered_df)} 条")
        
        if len(filtered_df) > 0:
            print("\n  满足条件的股票:")
            for _, row in filtered_df.head(10).iterrows():
                print(f"    {row['ts_code']}")
        
        # 5. 建议
        print("\n5. 建议")
        print("-"*70)
        
        if len(filtered_df) == 0:
            print("  ❌ 当前条件过于严格，建议：")
            print("     1. 放宽某些条件的范围")
            print("     2. 检查数据是否完整同步")
            print("     3. 使用更宽松的条件组合")
        else:
            print("  ✅ 条件合理，应该能选出股票")
        
        print("\n" + "="*70)
        
except Exception as e:
    print(f"\n❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()
