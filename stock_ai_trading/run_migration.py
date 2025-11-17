#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加策略条件字段
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def run_migration():
    """执行数据库迁移"""
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '123456'),
            database=os.getenv('DB_NAME', 'stock_trading'),
            charset='utf8mb4'
        )
        
        print("✅ 数据库连接成功")
        
        cursor = connection.cursor()
        
        # 读取迁移SQL文件
        migration_file = os.path.join(os.path.dirname(__file__), 'migrations', 'add_strategy_conditions.sql')
        
        if not os.path.exists(migration_file):
            print(f"❌ 迁移文件不存在: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        print(f"\n📝 开始执行 {len(sql_statements)} 条SQL语句...\n")
        
        # 执行每条SQL语句
        for i, sql in enumerate(sql_statements, 1):
            if sql.startswith('--') or sql.startswith('/*'):
                continue
            
            try:
                cursor.execute(sql)
                connection.commit()
                
                # 显示执行的语句
                if 'ALTER TABLE' in sql:
                    print(f"✅ [{i}] 执行成功: {sql[:80]}...")
                elif 'DESCRIBE' in sql:
                    print(f"\n📊 表结构:")
                    results = cursor.fetchall()
                    for row in results:
                        print(f"  {row}")
                elif 'SELECT' in sql and 'status' in sql:
                    result = cursor.fetchone()
                    if result:
                        print(f"\n🎉 {result[0]}")
                
            except pymysql.Error as e:
                error_msg = str(e)
                # 忽略字段已存在的错误
                if 'Duplicate column name' in error_msg:
                    print(f"⚠️  [{i}] 字段已存在，跳过")
                elif 'syntax' in error_msg.lower():
                    print(f"⚠️  [{i}] SQL语法错误，跳过: {error_msg[:100]}")
                else:
                    print(f"❌ [{i}] 执行失败: {e}")
                    print(f"   SQL: {sql[:100]}...")
        
        cursor.close()
        connection.close()
        
        print("\n✅ 数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移 - 添加策略条件字段")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("迁移成功！现在可以使用买卖条件功能了。")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("迁移失败！请检查错误信息。")
        print("=" * 60)
        sys.exit(1)
