#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查持仓数据"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.trading_db import DBPosition
from sqlalchemy import text

def check_positions():
    """检查持仓数据"""
    db = SessionLocal()
    try:
        # 查询所有持仓
        positions = db.query(DBPosition).filter(DBPosition.user_id == 1).all()
        
        print("=" * 80)
        print("持仓数据:")
        print("=" * 80)
        
        if not positions:
            print("没有持仓数据")
            return
        
        for pos in positions:
            print(f"\n股票代码: {pos.stock_code}")
            print(f"股票名称: {pos.stock_name}")
            print(f"持仓数量: {pos.quantity}")
            print(f"可用数量: {pos.available_quantity}")
            print(f"平均成本: ¥{pos.avg_cost:.3f}")
            print(f"最新价格: ¥{pos.last_price:.3f}")
            print(f"市值: ¥{pos.market_value:.2f}")
            print(f"盈亏: ¥{pos.profit_loss:.2f}")
            print(f"盈亏率: {(pos.profit_loss / (pos.avg_cost * pos.quantity) * 100) if pos.quantity > 0 else 0:.2f}%")
        
        print("\n" + "=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    check_positions()
