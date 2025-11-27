#!/usr/bin/env python3
"""
执行Agent表迁移脚本
"""
import os
from sqlalchemy import create_engine, text

# 数据库连接URL
DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/stock_trading?charset=utf8mb4"

def run_migration():
    """执行数据库迁移"""
    # 创建数据库连接
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # 读取SQL文件
    sql_file = os.path.join(os.path.dirname(__file__), 'add_agent_tables.sql')
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割SQL语句
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # 跳过注释和空行
        if not line or line.startswith('--'):
            continue
            
        # 跳过SET语句
        if line.upper().startswith('SET '):
            continue
            
        current_statement.append(line)
        
        # 检查是否是语句结束
        if line.endswith(';'):
            stmt = ' '.join(current_statement)
            if stmt and not stmt.upper().startswith('SET'):
                statements.append(stmt)
            current_statement = []
    
    # 执行SQL语句
    success_count = 0
    with engine.connect() as conn:
        for i, stmt in enumerate(statements, 1):
            try:
                print(f"执行语句 {i}/{len(statements)}...")
                conn.execute(text(stmt))
                conn.commit()
                success_count += 1
            except Exception as e:
                error_msg = str(e)
                # 如果是表已存在的错误，忽略
                if 'already exists' in error_msg or 'Duplicate' in error_msg:
                    print(f"  ⚠️  表已存在，跳过")
                    success_count += 1
                else:
                    print(f"  ❌ 执行失败: {stmt[:80]}...")
                    print(f"  错误: {error_msg}")
                continue
    
    print(f"\n✅ 迁移完成！成功执行 {success_count}/{len(statements)} 条SQL语句")

if __name__ == '__main__':
    run_migration()
