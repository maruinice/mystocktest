#!/usr/bin/env python3
"""
完整的股票基础信息导入脚本
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import tushare as ts

# 加载环境变量
load_dotenv()

def main():
    # 初始化Tushare
    token = os.getenv('TUSHARE_TOKEN')
    if not token:
        print("❌ 未设置TUSHARE_TOKEN")
        return
    
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 数据库连接
    db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/stock_trading')
    engine = create_engine(db_url)
    
    try:
        # 清空现有数据
        print("🔄 清空现有数据...")
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM stock_basic WHERE data_source = 'tushare'"))
            conn.commit()
            print(f"已清空 {result.rowcount} 条现有数据")
        
        # 获取股票数据
        print("🔄 获取股票基础信息...")
        df = pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,fullname,cnspell,market,exchange,list_date,is_hs,act_name,act_ent_type'
        )
        
        if df is None or df.empty:
            print("❌ 未获取到数据")
            return
        
        print(f"✅ 获取到 {len(df)} 条数据")
        
        # 逐条插入数据
        with engine.connect() as conn:
            success_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                try:
                    # 处理日期
                    list_date = None
                    if row.get('list_date') and str(row['list_date']).isdigit():
                        date_str = str(row['list_date'])
                        if len(date_str) == 8:
                            list_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    
                    # 插入数据
                    sql = text("""
                        INSERT INTO stock_basic 
                        (ts_code, symbol, name, area, industry, fullname, cnspell, market, exchange, 
                         list_date, is_hs, act_name, act_ent_type, data_source, sync_status)
                        VALUES (:ts_code, :symbol, :name, :area, :industry, :fullname, :cnspell, 
                                :market, :exchange, :list_date, :is_hs, :act_name, :act_ent_type, 
                                'tushare', 'active')
                        ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        area = VALUES(area),
                        industry = VALUES(industry),
                        fullname = VALUES(fullname),
                        cnspell = VALUES(cnspell),
                        market = VALUES(market),
                        exchange = VALUES(exchange),
                        list_date = VALUES(list_date),
                        is_hs = VALUES(is_hs),
                        act_name = VALUES(act_name),
                        act_ent_type = VALUES(act_ent_type),
                        updated_at = CURRENT_TIMESTAMP
                    """)
                    
                    # 处理空值
                    params = {
                        'ts_code': row.get('ts_code'),
                        'symbol': row.get('symbol'),
                        'name': row.get('name'),
                        'area': row.get('area') if row.get('area') and str(row.get('area')) != 'nan' else None,
                        'industry': row.get('industry') if row.get('industry') and str(row.get('industry')) != 'nan' else None,
                        'fullname': row.get('fullname') if row.get('fullname') and str(row.get('fullname')) != 'nan' else None,
                        'cnspell': row.get('cnspell') if row.get('cnspell') and str(row.get('cnspell')) != 'nan' else None,
                        'market': row.get('market') if row.get('market') and str(row.get('market')) != 'nan' else None,
                        'exchange': row.get('exchange') if row.get('exchange') and str(row.get('exchange')) != 'nan' else None,
                        'list_date': list_date,
                        'is_hs': row.get('is_hs') if row.get('is_hs') and str(row.get('is_hs')) != 'nan' else None,
                        'act_name': row.get('act_name') if row.get('act_name') and str(row.get('act_name')) != 'nan' else None,
                        'act_ent_type': row.get('act_ent_type') if row.get('act_ent_type') and str(row.get('act_ent_type')) != 'nan' else None
                    }
                    
                    conn.execute(sql, params)
                    success_count += 1
                    
                    if success_count % 100 == 0:
                        print(f"已处理 {success_count}/{len(df)} 条数据")
                
                except Exception as e:
                    error_count += 1
                    print(f"❌ 插入失败 {row.get('ts_code')}: {e}")
                    if error_count > 10:  # 如果错误太多就停止
                        print("错误过多，停止导入")
                        break
            
            conn.commit()
            print(f"✅ 成功导入 {success_count} 条数据，失败 {error_count} 条")
            
            # 验证数据
            result = conn.execute(text("SELECT COUNT(*) as count FROM stock_basic WHERE data_source = 'tushare'"))
            count = result.fetchone().count
            print(f"📊 数据库中共有 {count} 条记录")
            
            # 统计信息
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN list_status = 'L' THEN 1 END) as listed_count,
                    COUNT(CASE WHEN is_hs IN ('H', 'S') THEN 1 END) as hs_count,
                    COUNT(DISTINCT exchange) as exchange_count,
                    COUNT(DISTINCT industry) as industry_count
                FROM stock_basic 
                WHERE data_source = 'tushare'
            """))
            
            stats = result.fetchone()
            print(f"\n📈 统计信息:")
            print(f"  总股票数: {stats.total_count}")
            print(f"  沪深港通股票: {stats.hs_count}")
            print(f"  交易所数量: {stats.exchange_count}")
            print(f"  行业数量: {stats.industry_count}")
            
            # 显示样例数据
            result = conn.execute(text("SELECT ts_code, symbol, name, industry, market FROM stock_basic LIMIT 10"))
            print("\n📋 样例数据:")
            for row in result:
                print(f"  {row.ts_code} - {row.symbol} - {row.name} - {row.industry} - {row.market}")
    
    except Exception as e:
        print(f"❌ 导入失败: {e}")

if __name__ == "__main__":
    main()