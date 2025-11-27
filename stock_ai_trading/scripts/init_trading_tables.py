#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化交易相关数据库表
"""

import pymysql
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import DATABASE_URL
import re

def get_db_config():
    """从DATABASE_URL解析数据库配置"""
    match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if not match:
        raise ValueError("Invalid DATABASE_URL format")
    
    user, password, host, port, database = match.groups()
    return {
        'host': host,
        'port': int(port),
        'user': user,
        'password': password,
        'database': database,
        'charset': 'utf8mb4'
    }

def execute_sql_file(sql_file):
    """执行SQL文件"""
    config = get_db_config()
    
    # 读取SQL文件
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 连接数据库
    connection = pymysql.connect(**config)
    
    try:
        with connection.cursor() as cursor:
            # 分割SQL语句（按分号和DELIMITER分割）
            statements = []
            current_statement = []
            delimiter = ';'
            
            for line in sql_content.split('\n'):
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('--'):
                    continue
                
                # 处理DELIMITER命令
                if line.upper().startswith('DELIMITER'):
                    if current_statement:
                        statements.append('\n'.join(current_statement))
                        current_statement = []
                    delimiter = line.split()[1]
                    continue
                
                current_statement.append(line)
                
                # 检查是否到达语句结尾
                if line.endswith(delimiter):
                    stmt = '\n'.join(current_statement)
                    if delimiter != ';':
                        stmt = stmt[:-len(delimiter)]
                    else:
                        stmt = stmt[:-1]
                    
                    if stmt.strip():
                        statements.append(stmt)
                    current_statement = []
            
            # 添加最后一个语句
            if current_statement:
                stmt = '\n'.join(current_statement)
                if stmt.strip():
                    statements.append(stmt)
            
            # 执行每个语句
            for i, statement in enumerate(statements):
                statement = statement.strip()
                if not statement:
                    continue
                
                try:
                    print(f"执行语句 {i+1}/{len(statements)}...")
                    cursor.execute(statement)
                    connection.commit()
                    print(f"✓ 语句 {i+1} 执行成功")
                except Exception as e:
                    print(f"✗ 语句 {i+1} 执行失败: {e}")
                    # 某些语句失败是可以接受的（如已存在的表）
                    if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                        raise
        
        print("\n✓ SQL文件执行完成")
        
    finally:
        connection.close()

if __name__ == '__main__':
    sql_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'sql',
        'trading_tables_schema.sql'
    )
    
    print(f"开始执行SQL文件: {sql_file}")
    execute_sql_file(sql_file)
    print("数据库表初始化完成！")
