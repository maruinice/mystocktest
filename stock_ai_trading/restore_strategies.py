import pymysql
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/meiming/source_code/xl_ai_stock_trading/stock_ai_trading/.env')

# Connect to database
conn = pymysql.connect(
    host='localhost',
    user='root',
    password=os.getenv('MYSQL_ROOT_PASSWORD', '123456'),
    database='stock_trading',
    port=3306
)
cursor = conn.cursor()

try:
    # Get admin user id
    cursor.execute('SELECT id FROM users WHERE email = "admin@example.com"')
    result = cursor.fetchone()
    if not result:
        print("Admin user not found. Please run create_test_user.py first.")
        exit(1)
    
    user_id = result[0]

    # Sample strategies
    strategies = [
        {
            "name": "双均线策略",
            "type": "technical",
            "description": "基于5日和20日均线的金叉死叉策略",
            "parameters": json.dumps({"short_window": 5, "long_window": 20}),
            "risk_level": "medium",
            "status": "active"
        },
        {
            "name": "RSI超卖反转",
            "type": "technical",
            "description": "当RSI低于30时买入，高于70时卖出",
            "parameters": json.dumps({"rsi_period": 14, "buy_threshold": 30, "sell_threshold": 70}),
            "risk_level": "high",
            "status": "testing"
        },
        {
            "name": "AI情感分析策略",
            "type": "ai_driven",
            "description": "基于新闻和社交媒体情感分析的交易策略",
            "parameters": json.dumps({"model": "bert-base-chinese", "sentiment_threshold": 0.8}),
            "risk_level": "medium",
            "status": "inactive"
        }
    ]

    print(f"Restoring strategies for user_id: {user_id}...")

    for strat in strategies:
        cursor.execute('''
            INSERT INTO trading_strategies 
            (user_id, strategy_name, strategy_type, description, parameters, risk_level, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, strat['name'], strat['type'], strat['description'], strat['parameters'], strat['risk_level'], strat['status']))

    conn.commit()
    print(f"Successfully restored {len(strategies)} strategies.")

except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
