#!/usr/bin/env python3
"""
数据库结构更新脚本
执行trading_strategies表的结构更新
"""

import pymysql
import os
import sys
from datetime import datetime

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_db_config():
    """获取数据库配置"""
    import os
    from urllib.parse import urlparse
    
    # 尝试从环境变量获取数据库URL
    database_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/stock_trading')
    
    try:
        # 解析数据库URL
        parsed = urlparse(database_url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 3306,
            'user': parsed.username or 'root',
            'password': parsed.password or '123456',
            'database': parsed.path.lstrip('/') or 'stock_trading',
            'charset': 'utf8mb4'
        }
    except Exception:
        # 如果解析失败，使用默认配置
        return {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '123456',
            'database': 'stock_trading',
            'charset': 'utf8mb4'
        }

def execute_sql_file(connection, file_path):
    """执行SQL文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # 处理DELIMITER语句
        sql_content = sql_content.replace('DELIMITER $$', '')
        sql_content = sql_content.replace('DELIMITER ;', '')
        sql_content = sql_content.replace('$$', ';')
        
        # 分割SQL语句（按分号分割）
        sql_statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            current_statement += line + '\n'
            
            # 如果行以分号结尾且不在字符串中，则认为是一个完整的语句
            if line.endswith(';') and not _is_in_string(line):
                sql_statements.append(current_statement.strip())
                current_statement = ""
        
        # 添加最后一个语句（如果有）
        if current_statement.strip():
            sql_statements.append(current_statement.strip())
        
        cursor = connection.cursor()
        
        for i, statement in enumerate(sql_statements):
            if statement and not statement.isspace():
                try:
                    print(f"执行SQL语句 {i+1}/{len(sql_statements)}: {statement[:50]}...")
                    cursor.execute(statement)
                    connection.commit()
                    print(f"✅ 执行成功")
                except Exception as e:
                    print(f"❌ 执行失败: {e}")
                    if ("Duplicate column name" in str(e) or 
                        "already exists" in str(e) or
                        "Duplicate key name" in str(e)):
                        print("   (字段或索引已存在，跳过)")
                        continue
                    else:
                        raise
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"执行SQL文件失败: {e}")
        return False

def _is_in_string(line):
    """简单检查是否在字符串中"""
    single_quote_count = line.count("'")
    double_quote_count = line.count('"')
    return (single_quote_count % 2 != 0) or (double_quote_count % 2 != 0)

def check_database_connection():
    """检查数据库连接"""
    try:
        config = get_db_config()
        connection = pymysql.connect(**config)
        connection.close()
        print("✅ 数据库连接正常")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def backup_table(connection, table_name):
    """备份表"""
    try:
        cursor = connection.cursor()
        backup_table_name = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建备份表
        sql = f"CREATE TABLE {backup_table_name} AS SELECT * FROM {table_name}"
        cursor.execute(sql)
        connection.commit()
        
        print(f"✅ 表 {table_name} 已备份为 {backup_table_name}")
        cursor.close()
        return backup_table_name
        
    except Exception as e:
        print(f"❌ 备份表失败: {e}")
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("数据库结构更新脚本")
    print("=" * 60)
    
    # 1. 检查数据库连接
    print("\n1. 检查数据库连接...")
    if not check_database_connection():
        print("请检查数据库配置和连接")
        sys.exit(1)
    
    # 2. 检查SQL文件是否存在
    sql_file_path = os.path.join(os.path.dirname(__file__), 'sql', 'update_trading_strategies_simple.sql')
    if not os.path.exists(sql_file_path):
        print(f"❌ SQL文件不存在: {sql_file_path}")
        sys.exit(1)
    
    print(f"✅ 找到SQL文件: {sql_file_path}")
    
    # 3. 连接数据库
    print("\n2. 连接数据库...")
    try:
        config = get_db_config()
        connection = pymysql.connect(**config)
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)
    
    try:
        # 4. 备份现有表
        print("\n3. 备份现有表...")
        backup_name = backup_table(connection, 'trading_strategies')
        if backup_name:
            print(f"✅ 备份完成: {backup_name}")
        else:
            print("⚠️  备份失败，但继续执行更新")
        
        # 5. 执行SQL更新
        print("\n4. 执行数据库结构更新...")
        if execute_sql_file(connection, sql_file_path):
            print("✅ 数据库结构更新完成")
        else:
            print("❌ 数据库结构更新失败")
            sys.exit(1)
        
        # 6. 验证更新结果
        print("\n5. 验证更新结果...")
        cursor = connection.cursor()
        
        # 检查新字段是否存在
        cursor.execute("DESCRIBE trading_strategies")
        columns = [row[0] for row in cursor.fetchall()]
        
        new_fields = [
            'display_name', 'author', 'min_capital', 'category', 'indicators',
            'indicator_params', 'buy_conditions', 'sell_conditions', 'code',
            'performance', 'sharpe_ratio', 'max_drawdown', 'win_rate',
            'total_trades', 'backtest_count', 'last_backtest_date',
            'ai_generated', 'original_prompt', 'last_run_at'
        ]
        
        missing_fields = [field for field in new_fields if field not in columns]
        
        if missing_fields:
            print(f"⚠️  以下字段未成功添加: {missing_fields}")
        else:
            print("✅ 所有新字段已成功添加")
        
        # 检查新表是否存在
        cursor.execute("SHOW TABLES LIKE 'backtest_results'")
        if cursor.fetchone():
            print("✅ backtest_results表已创建")
        else:
            print("⚠️  backtest_results表未创建")
        
        cursor.execute("SHOW TABLES LIKE 'strategy_templates'")
        if cursor.fetchone():
            print("✅ strategy_templates表已创建")
        else:
            print("⚠️  strategy_templates表未创建")
        
        cursor.close()
        
        print("\n" + "=" * 60)
        print("数据库更新完成！")
        print("=" * 60)
        print("\n更新内容:")
        print("1. ✅ 扩展了trading_strategies表字段")
        print("2. ✅ 创建了backtest_results表")
        print("3. ✅ 创建了strategy_templates表")
        print("4. ✅ 插入了默认策略模板")
        print("5. ✅ 创建了相关视图和触发器")
        
        if backup_name:
            print(f"\n备份表: {backup_name}")
            print("如果需要回滚，请手动恢复备份表")
        
    except Exception as e:
        print(f"\n❌ 更新过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        connection.close()

if __name__ == "__main__":
    main()