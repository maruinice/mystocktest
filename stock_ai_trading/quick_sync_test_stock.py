#!/usr/bin/env python3
"""
快速同步测试股票数据(603387.SH)
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, SessionLocal
from app.config.settings import settings
from sqlalchemy import text
import tushare as ts

print("="*60)
print("快速同步测试股票数据")
print("="*60)

# 检查Tushare配置
if not settings.TUSHARE_TOKEN:
    print("❌ 未配置TUSHARE_TOKEN!")
    print("   请在.env文件中设置TUSHARE_TOKEN")
    sys.exit(1)

print(f"✅ Tushare Token已配置")

# 初始化Tushare
pro = ts.pro_api(settings.TUSHARE_TOKEN)

# 测试股票列表
test_stocks = ['603387.SH', '600000.SH', '000001.SZ', '000002.SZ', '600036.SH']

# 获取最近10个交易日的数据
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

print(f"\n📅 日期范围: {start_date} ~ {end_date}")
print(f"📊 股票列表: {', '.join(test_stocks)}")
print(f"\n开始获取数据...")

total_records = 0

for ts_code in test_stocks:
    try:
        print(f"\n处理 {ts_code}...")
        
        # 获取日线数据
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            print(f"  ⚠️  没有数据")
            continue
        
        # 获取每日指标
        df_basic = pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        # 合并数据
        if not df_basic.empty:
            # 选择可用的字段
            available_cols = ['ts_code', 'trade_date']
            optional_cols = ['pe', 'pb', 'ps', 'pcf', 'total_mv', 'circ_mv', 'turnover_rate', 'volume_ratio']
            for col in optional_cols:
                if col in df_basic.columns:
                    available_cols.append(col)
            
            df = df.merge(df_basic[available_cols], on=['ts_code', 'trade_date'], how='left')
        
        # 转换字段名
        df = df.rename(columns={
            'open': 'open_price',
            'high': 'high_price',
            'low': 'low_price',
            'close': 'close_price',
            'pre_close': 'pre_close',
            'change': 'change_amount',
            'pct_chg': 'change_pct',
            'vol': 'volume',
            'amount': 'amount',
            'total_mv': 'market_cap'
        })
        
        # 选择需要的字段（只选择存在的字段）
        desired_columns = ['ts_code', 'trade_date', 'open_price', 'high_price', 'low_price', 
                          'close_price', 'pre_close', 'change_amount', 'change_pct', 'volume', 
                          'amount', 'turnover_rate', 'volume_ratio', 'pe', 'pb', 'ps', 'pcf', 
                          'market_cap', 'circ_mv']
        
        columns = [col for col in desired_columns if col in df.columns]
        df = df[columns]
        
        # 填充缺失的字段为None
        for col in desired_columns:
            if col not in df.columns:
                df[col] = None
        
        # 插入数据库
        with engine.begin() as conn:
            for _, row in df.iterrows():
                sql = text("""
                    INSERT INTO daily_quotes 
                    (ts_code, trade_date, open_price, high_price, low_price, close_price,
                     pre_close, change_amount, change_pct, volume, amount, turnover_rate,
                     volume_ratio, pe, pb, ps, pcf, market_cap, circ_mv)
                    VALUES 
                    (:ts_code, :trade_date, :open_price, :high_price, :low_price, :close_price,
                     :pre_close, :change_amount, :change_pct, :volume, :amount, :turnover_rate,
                     :volume_ratio, :pe, :pb, :ps, :pcf, :market_cap, :circ_mv)
                    ON DUPLICATE KEY UPDATE
                     close_price = VALUES(close_price),
                     open_price = VALUES(open_price),
                     high_price = VALUES(high_price),
                     low_price = VALUES(low_price),
                     pre_close = VALUES(pre_close),
                     change_amount = VALUES(change_amount),
                     change_pct = VALUES(change_pct),
                     volume = VALUES(volume),
                     amount = VALUES(amount),
                     updated_at = CURRENT_TIMESTAMP
                """)
                
                conn.execute(sql, row.to_dict())
        
        print(f"  ✅ 成功插入 {len(df)} 条记录")
        total_records += len(df)
        
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        continue

print(f"\n{'='*60}")
print(f"同步完成！")
print(f"总共插入/更新 {total_records} 条记录")
print(f"{'='*60}\n")

