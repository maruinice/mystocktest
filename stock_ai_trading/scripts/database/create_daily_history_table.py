#!/usr/bin/env python3
"""
创建每日历史行情表
"""

import pymysql
import os
from pathlib import Path

def create_daily_history_table():
    """创建每日历史行情表"""
    print("🔧 创建每日历史行情表...")
    
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
        sql_file = Path(__file__).parent / 'sql' / 'create_daily_history_table.sql'
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
                    raise
        
        print("🎉 每日历史行情表创建完成！")
        
        # 验证表是否创建成功
        cursor.execute("SHOW TABLES LIKE 'daily_history'")
        result = cursor.fetchone()
        if result:
            print("✅ 表创建验证成功")
            
            # 查看表结构
            cursor.execute("DESCRIBE daily_history")
            columns = cursor.fetchall()
            print(f"📊 表结构 ({len(columns)}个字段):")
            for col in columns[:10]:  # 显示前10个字段
                print(f"   - {col[0]} ({col[1]})")
            if len(columns) > 10:
                print(f"   ... 还有{len(columns)-10}个字段")
        else:
            print("❌ 表创建验证失败")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_daily_history_table()