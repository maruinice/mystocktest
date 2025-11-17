#!/usr/bin/env python3
"""
创建数据管理功能相关表的脚本
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
load_dotenv()

def main():
    db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/stock_trading')
    print(f'数据库URL: {db_url}')

    try:
        engine = create_engine(db_url)
        
        # 读取SQL文件
        sql_file = Path('sql/create_data_management_tables.sql')
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 执行SQL
        with engine.connect() as conn:
            # 更好的SQL分割逻辑，处理注释
            statements = []
            current_statement = ""
            
            for line in sql_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('--'):
                    current_statement += line + " "
                    if line.endswith(';'):
                        statements.append(current_statement.strip()[:-1])  # 移除最后的分号
                        current_statement = ""
            
            print(f'总共解析到 {len(statements)} 条SQL语句')
            
            for i, statement in enumerate(statements):
                if statement.strip():
                    print(f'第{i+1}条语句开头: {statement[:50]}...')
                    try:
                        print(f'  执行: {statement[:80]}...')
                        conn.execute(text(statement))
                        conn.commit()
                        print(f'  ✅ 成功')
                    except Exception as e:
                        print(f'  ❌ 失败: {e}')
            
            print('✅ SQL执行完成')
            
            # 验证表是否创建成功
            tables = ['data_sources', 'api_interfaces', 'api_call_logs', 'api_sync_tasks']
            for table in tables:
                result = conn.execute(text(f"SHOW TABLES LIKE '{table}'"))
                if result.fetchone():
                    print(f'✅ {table}表已创建')
                    
                    # 显示表结构
                    result = conn.execute(text(f'DESCRIBE {table}'))
                    columns = result.fetchall()
                    print(f'   字段数: {len(columns)}')
                else:
                    print(f'❌ {table}表创建失败')
                    
    except Exception as e:
        print(f'❌ 执行失败: {e}')

if __name__ == "__main__":
    main()