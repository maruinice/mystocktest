#!/usr/bin/env python3
"""
核心字段迁移脚本 - 只添加回测必需的3个字段
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def run_core_migration():
    """执行核心字段迁移"""
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'stock_trading'),
            charset='utf8mb4'
        )
        
        print("✅ 数据库连接成功")
        
        cursor = connection.cursor()
        
        # 核心字段列表
        core_fields = [
            ('buy_conditions', 'JSON', '买入条件(JSON格式)'),
            ('sell_conditions', 'JSON', '卖出条件(JSON格式)'),
            ('risk_controls', 'JSON', '风险控制参数(JSON格式)')
        ]
        
        print(f"\n📝 开始添加 {len(core_fields)} 个核心字段...\n")
        
        for field_name, field_type, comment in core_fields:
            try:
                # 检查字段是否已存在
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = '{os.getenv('DB_NAME', 'stock_trading')}' 
                    AND TABLE_NAME = 'trading_strategies' 
                    AND COLUMN_NAME = '{field_name}'
                """)
                
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    print(f"⚠️  字段 '{field_name}' 已存在，跳过")
                    continue
                
                # 添加字段
                sql = f"ALTER TABLE trading_strategies ADD COLUMN {field_name} {field_type} COMMENT '{comment}'"
                cursor.execute(sql)
                connection.commit()
                print(f"✅ 成功添加字段: {field_name}")
                
            except pymysql.Error as e:
                print(f"❌ 添加字段 '{field_name}' 失败: {e}")
                return False
        
        # 验证字段
        print("\n🔍 验证字段...")
        cursor.execute("DESCRIBE trading_strategies")
        columns = cursor.fetchall()
        
        print("\n📊 当前表结构:")
        for col in columns:
            if col[0] in ['buy_conditions', 'sell_conditions', 'risk_controls']:
                print(f"  ✅ {col[0]}: {col[1]}")
        
        cursor.close()
        connection.close()
        
        print("\n✅ 核心字段迁移完成！")
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("核心字段迁移 - 添加回测必需字段")
    print("=" * 60)
    print()
    
    success = run_core_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 迁移成功！")
        print("\n下一步:")
        print("  1. 重启Flask服务器")
        print("  2. 使用AI生成新策略")
        print("  3. 执行回测")
        print("  4. 查看交易记录")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ 迁移失败！请检查错误信息。")
        print("=" * 60)
        sys.exit(1)
