#!/usr/bin/env python3
"""修复 suspend_info 表结构"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from sqlalchemy import text

print("\n" + "="*70)
print("修复 suspend_info 表结构")
print("="*70)

try:
    db = next(get_db())
    
    # 1. 查看当前表结构
    print("\n1. 当前表结构:")
    print("-"*70)
    result = db.execute(text("DESCRIBE suspend_info")).fetchall()
    for row in result:
        print(f"  {row.Field:<20} {row.Type:<20} {row.Null:<5} {row.Key:<5} {row.Default}")
    
    # 2. 修改字段长度
    print("\n2. 修改字段长度...")
    print("-"*70)
    
    # 修改 suspend_timing 字段
    print("  修改 suspend_timing 字段长度为 VARCHAR(100)")
    db.execute(text("""
        ALTER TABLE suspend_info 
        MODIFY COLUMN suspend_timing VARCHAR(100) DEFAULT NULL COMMENT '停牌时间'
    """))
    db.commit()
    print("  ✅ suspend_timing 字段修改成功")
    
    # 修改 suspend_type 字段
    print("  修改 suspend_type 字段长度为 VARCHAR(50)")
    db.execute(text("""
        ALTER TABLE suspend_info 
        MODIFY COLUMN suspend_type VARCHAR(50) DEFAULT NULL COMMENT '停牌类型'
    """))
    db.commit()
    print("  ✅ suspend_type 字段修改成功")
    
    # 3. 验证修改后的表结构
    print("\n3. 修改后的表结构:")
    print("-"*70)
    result = db.execute(text("DESCRIBE suspend_info")).fetchall()
    for row in result:
        print(f"  {row.Field:<20} {row.Type:<20} {row.Null:<5} {row.Key:<5} {row.Default}")
    
    # 4. 查看现有数据
    print("\n4. 现有数据统计:")
    print("-"*70)
    result = db.execute(text("SELECT COUNT(*) as count FROM suspend_info")).first()
    print(f"  总记录数: {result.count}")
    
    if result.count > 0:
        print("\n  最新5条记录:")
        result = db.execute(text("""
            SELECT ts_code, suspend_date, suspend_timing, suspend_type, is_suspended 
            FROM suspend_info 
            ORDER BY suspend_date DESC 
            LIMIT 5
        """)).fetchall()
        for row in result:
            print(f"    {row.ts_code} | {row.suspend_date} | {row.suspend_timing} | {row.suspend_type} | {row.is_suspended}")
    
    print("\n" + "="*70)
    print("✅ 表结构修复完成！")
    print("="*70)
    print("\n现在可以运行: python sync_suspend_only.py")
    print()
    
except Exception as e:
    print(f"\n❌ 修复失败: {e}")
    import traceback
    traceback.print_exc()
