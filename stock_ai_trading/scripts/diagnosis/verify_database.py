#!/usr/bin/env python3
"""
数据库结构验证脚本
"""

import pymysql
import os
from urllib.parse import urlparse

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_db_config():
    """获取数据库配置"""
    database_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/stock_trading')
    
    try:
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
        return {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '123456',
            'database': 'stock_trading',
            'charset': 'utf8mb4'
        }

def main():
    """主函数"""
    print("=" * 60)
    print("数据库结构验证")
    print("=" * 60)
    
    try:
        config = get_db_config()
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        
        print("\n1. trading_strategies表结构:")
        cursor.execute('DESCRIBE trading_strategies')
        columns = cursor.fetchall()
        
        new_fields = [
            'display_name', 'author', 'min_capital', 'category', 'indicators',
            'indicator_params', 'buy_conditions', 'sell_conditions', 'code',
            'performance', 'sharpe_ratio', 'max_drawdown', 'win_rate',
            'total_trades', 'backtest_count', 'last_backtest_date',
            'ai_generated', 'original_prompt', 'last_run_at'
        ]
        
        existing_columns = [col[0] for col in columns]
        
        for field in new_fields:
            if field in existing_columns:
                print(f"✅ {field}")
            else:
                print(f"❌ {field} - 缺失")
        
        print(f"\n总字段数: {len(existing_columns)}")
        
        print("\n2. 检查新表:")
        
        # 检查backtest_results表
        cursor.execute("SHOW TABLES LIKE 'backtest_results'")
        if cursor.fetchone():
            print("✅ backtest_results表已创建")
        else:
            print("❌ backtest_results表不存在")
        
        # 检查strategy_templates表
        cursor.execute("SHOW TABLES LIKE 'strategy_templates'")
        if cursor.fetchone():
            print("✅ strategy_templates表已创建")
            
            # 检查模板数据
            cursor.execute('SELECT COUNT(*) FROM strategy_templates')
            count = cursor.fetchone()[0]
            print(f"   - 包含 {count} 个策略模板")
            
            cursor.execute('SELECT template_name, display_name FROM strategy_templates')
            templates = cursor.fetchall()
            for template in templates:
                print(f"   - {template[0]}: {template[1]}")
        else:
            print("❌ strategy_templates表不存在")
        
        print("\n3. 检查索引:")
        cursor.execute("SHOW INDEX FROM trading_strategies WHERE Key_name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        
        expected_indexes = ['idx_category', 'idx_author', 'idx_ai_generated', 'idx_performance', 'idx_last_backtest_date']
        existing_indexes = [idx[2] for idx in indexes]
        
        for idx in expected_indexes:
            if idx in existing_indexes:
                print(f"✅ {idx}")
            else:
                print(f"❌ {idx} - 缺失")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("验证完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    main()