#!/usr/bin/env python3
"""
创建stock_basic表的脚本
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
load_dotenv()

def main():
    db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/stock_ai_trading')
    print(f'数据库URL: {db_url}')

    try:
        engine = create_engine(db_url)
        
        # 读取SQL文件
        sql_file = Path('sql/create_stock_basic_table.sql')
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 执行SQL
        with engine.connect() as conn:
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.upper().startswith(('CREATE', 'ALTER')):
                    print(f'执行: {statement[:50]}...')
                    conn.execute(text(statement))
                    conn.commit()
            
            print('✅ 数据库表创建成功')
            
            # 验证表是否创建成功
            result = conn.execute(text("SHOW TABLES LIKE 'stock_basic'"))
            if result.fetchone():
                print('✅ stock_basic表已创建')
                
                # 查看表结构
                result = conn.execute(text('DESCRIBE stock_basic'))
                columns = result.fetchall()
                print('📊 表结构:')
                for col in columns:
                    print(f'  - {col[0]}: {col[1]}')
            else:
                print('❌ stock_basic表创建失败')
                
    except Exception as e:
        print(f'❌ 执行失败: {e}')

if __name__ == "__main__":
    main()