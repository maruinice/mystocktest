#!/usr/bin/env python3
"""
创建Tushare相关数据表
"""

import pymysql
import os
from pathlib import Path

def create_tushare_tables():
    """创建Tushare相关数据表"""
    print("🔧 创建Tushare相关数据表...")
    
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'stock_trading',
        'charset': 'utf8mb4'
    }
    
    try:
        # 读取SQL文件
        sql_file = Path(__file__).parent / 'sql' / 'create_tushare_tables.sql'
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 连接数据库
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        # 分割SQL语句并执行
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, sql in enumerate(sql_statements, 1):
            try:
                print(f"📋 执行SQL语句 {i}/{len(sql_statements)}...")
                cursor.execute(sql)
                connection.commit()
                print(f"   ✅ 成功")
            except Exception as e:
                print(f"   ❌ 失败: {e}")
                if "already exists" not in str(e).lower():
                    continue  # 继续执行其他语句
        
        print("🎉 Tushare相关数据表创建完成！")
        
        # 验证表是否创建成功
        tables_to_check = ['adj_factor', 'daily_basic', 'trade_cal']
        for table in tables_to_check:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            result = cursor.fetchone()
            if result:
                print(f"✅ 表 {table} 创建成功")
            else:
                print(f"❌ 表 {table} 创建失败")
        
        # 检查视图
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
        views = cursor.fetchall()
        print(f"📊 创建的视图: {len(views)}个")
        for view in views:
            if 'latest_daily_basic' in view[0]:
                print(f"   - {view[0]}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_tushare_tables()