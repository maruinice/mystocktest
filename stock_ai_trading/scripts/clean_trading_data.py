"""
数据清理脚本
清空交易相关的错误数据，重置为初始状态
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_trading_data():
    """清空交易数据"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL 未设置")
        return False
    
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 1. 清空订单表
                logger.info("清空订单表...")
                result = conn.execute(text("DELETE FROM orders"))
                logger.info(f"删除了 {result.rowcount} 条订单记录")
                
                # 2. 清空持仓表
                logger.info("清空持仓表...")
                result = conn.execute(text("DELETE FROM positions"))
                logger.info(f"删除了 {result.rowcount} 条持仓记录")
                
                # 3. 重置账户资金（保留账户，只重置资金）
                logger.info("重置账户资金...")
                result = conn.execute(text("""
                    UPDATE accounts 
                    SET available_cash = 100000.00,
                        total_assets = 100000.00,
                        frozen_cash = 0.00,
                        updated_at = NOW()
                    WHERE user_id = 1
                """))
                logger.info(f"重置了 {result.rowcount} 个账户")
                
                # 4. 清空交易记录（如果有的话）
                logger.info("清空交易记录...")
                try:
                    result = conn.execute(text("DELETE FROM trades"))
                    logger.info(f"删除了 {result.rowcount} 条交易记录")
                except Exception as e:
                    logger.warning(f"清空交易记录失败（表可能不存在）: {e}")
                
                # 提交事务
                trans.commit()
                logger.info("✅ 数据清理完成！")
                
                # 验证清理结果
                logger.info("\n验证清理结果:")
                
                result = conn.execute(text("SELECT COUNT(*) as count FROM orders"))
                order_count = result.fetchone()[0]
                logger.info(f"  订单数量: {order_count}")
                
                result = conn.execute(text("SELECT COUNT(*) as count FROM positions"))
                position_count = result.fetchone()[0]
                logger.info(f"  持仓数量: {position_count}")
                
                result = conn.execute(text("""
                    SELECT user_id, available_cash, total_assets 
                    FROM accounts 
                    WHERE user_id = 1
                """))
                account = result.fetchone()
                if account:
                    logger.info(f"  账户资金: 可用={account.available_cash}, 总资产={account.total_assets}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"清理数据失败: {e}")
                return False
                
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


def confirm_clean():
    """确认清理操作"""
    print("\n" + "="*60)
    print("⚠️  警告：此操作将清空所有交易数据！")
    print("="*60)
    print("\n将要执行以下操作:")
    print("  1. 删除所有订单记录")
    print("  2. 删除所有持仓记录")
    print("  3. 重置账户资金为 ¥100,000.00")
    print("  4. 删除所有交易记录")
    print("\n此操作不可恢复！")
    print("="*60)
    
    response = input("\n确认要继续吗？(输入 'YES' 确认): ")
    return response.strip() == 'YES'


if __name__ == '__main__':
    print("\n数据清理工具")
    print("="*60)
    
    if confirm_clean():
        print("\n开始清理数据...")
        if clean_trading_data():
            print("\n✅ 数据清理成功！")
            print("\n现在可以开始全新的交易了。")
            print("初始资金: ¥100,000.00")
        else:
            print("\n❌ 数据清理失败！")
            sys.exit(1)
    else:
        print("\n操作已取消。")
        sys.exit(0)
