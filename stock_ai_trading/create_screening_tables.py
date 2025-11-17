#!/usr/bin/env python3
"""
创建选股功能相关数据库表
"""

import pymysql
import os

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='stock_trading',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def execute_sql_file():
    """执行SQL文件"""
    sql_file = 'sql/create_screening_tables.sql'
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL文件不存在: {sql_file}")
        return False
    
    try:
        # 读取SQL文件
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        sql_statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                current_statement += line + '\n'
                if line.endswith(';'):
                    sql_statements.append(current_statement.strip())
                    current_statement = ""
        
        # 执行SQL语句
        connection = get_db_connection()
        cursor = connection.cursor()
        
        print("开始创建选股相关数据表...")
        
        success_count = 0
        for i, sql in enumerate(sql_statements, 1):
            if sql.strip():
                try:
                    cursor.execute(sql)
                    connection.commit()
                    
                    # 提取表名或操作类型
                    if 'CREATE TABLE' in sql.upper():
                        table_name = sql.split('CREATE TABLE')[1].split('(')[0].strip().replace('IF NOT EXISTS', '').strip()
                        print(f"✅ {i}. 创建表: {table_name}")
                    elif 'CREATE OR REPLACE VIEW' in sql.upper():
                        view_name = sql.split('CREATE OR REPLACE VIEW')[1].split('AS')[0].strip()
                        print(f"✅ {i}. 创建视图: {view_name}")
                    elif 'INSERT INTO' in sql.upper():
                        table_name = sql.split('INSERT INTO')[1].split('(')[0].strip()
                        print(f"✅ {i}. 插入数据到: {table_name}")
                    else:
                        print(f"✅ {i}. 执行SQL语句")
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"❌ {i}. SQL执行失败: {str(e)[:100]}...")
                    print(f"   SQL: {sql[:100]}...")
        
        connection.close()
        
        print(f"\n✅ 完成! 成功执行 {success_count}/{len(sql_statements)} 条SQL语句")
        return True
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def verify_tables():
    """验证表创建结果"""
    print("\n验证表创建结果...")
    
    expected_tables = [
        'daily_quotes',
        'financial_indicators', 
        'technical_indicators',
        'money_flow',
        'screening_strategies',
        'screening_results',
        'screening_history',
        'user_screening_preferences'
    ]
    
    expected_views = [
        'v_latest_quotes',
        'v_latest_financial',
        'v_latest_technical'
    ]
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 检查表
        print("\n数据表:")
        for table in expected_tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if cursor.fetchone():
                cursor.execute(f"SELECT COUNT(*) as count FROM information_schema.columns WHERE table_schema='stock_trading' AND table_name='{table}'")
                column_count = cursor.fetchone()['count']
                print(f"  ✅ {table} ({column_count}列)")
            else:
                print(f"  ❌ {table} - 不存在")
        
        # 检查视图
        print("\n视图:")
        for view in expected_views:
            cursor.execute(f"SHOW TABLES LIKE '{view}'")
            if cursor.fetchone():
                print(f"  ✅ {view}")
            else:
                print(f"  ❌ {view} - 不存在")
        
        # 检查预设策略
        cursor.execute("SELECT COUNT(*) as count FROM screening_strategies WHERE is_system = TRUE")
        strategy_count = cursor.fetchone()['count']
        print(f"\n预设策略: {strategy_count}个")
        
        if strategy_count > 0:
            cursor.execute("SELECT strategy_name, strategy_code FROM screening_strategies WHERE is_system = TRUE")
            strategies = cursor.fetchall()
            for strategy in strategies:
                print(f"  - {strategy['strategy_name']} ({strategy['strategy_code']})")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("选股功能数据库表创建工具")
    print("=" * 60)
    
    if execute_sql_file():
        verify_tables()
    
    print("\n" + "=" * 60)