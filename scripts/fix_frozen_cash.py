import sys
import os
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到 python path
sys.path.append(os.getcwd())

from stock_ai_trading.app.core.database import get_db
from stock_ai_trading.app.models.trading_db import DBAccount, DBOrder

def fix_account_frozen_cash():
    print("开始修复账户冻结资金...")
    
    db = next(get_db())
    try:
        # 获取所有账户
        accounts = db.query(DBAccount).all()
        
        for account in accounts:
            print(f"检查账户: User ID {account.user_id}")
            print(f"当前状态: 可用 {account.available_cash}, 冻结 {account.frozen_cash}, 市值 {account.market_value}, 总资产 {account.total_assets}")
            
            # 获取该用户所有 pending 订单
            pending_orders = db.query(DBOrder).filter(
                DBOrder.user_id == account.user_id,
                DBOrder.status == 'pending',
                DBOrder.side == 'buy'  # 只有买单冻结资金
            ).all()
            
            expected_frozen = Decimal('0.00')
            for order in pending_orders:
                if order.order_type == 'market':
                    # 市价单按 10.0 估算
                    frozen_price = Decimal('10.0')
                else:
                    frozen_price = order.price
                
                amount = Decimal(str(order.quantity)) * frozen_price
                expected_frozen += amount
                print(f"  - Pending订单 {order.order_id}: {order.quantity}股 @ {frozen_price} = {amount}")
            
            print(f"期望冻结资金: {expected_frozen}")
            
            if abs(account.frozen_cash - expected_frozen) > Decimal('0.01'):
                diff = account.frozen_cash - expected_frozen
                print(f"发现差异! 当前冻结 {account.frozen_cash}, 应该冻结 {expected_frozen}, 差异 {diff}")
                print(f"正在修复... 将 {diff} 从冻结资金移回可用资金")
                
                account.frozen_cash = expected_frozen
                account.available_cash += diff
                # total_assets 保持不变，因为它等于 available + frozen + market
                
                print(f"修复后: 可用 {account.available_cash}, 冻结 {account.frozen_cash}")
            else:
                print("冻结资金正常，无需修复")
                
        db.commit()
        print("修复完成")
        
    except Exception as e:
        db.rollback()
        print(f"修复失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_account_frozen_cash()
