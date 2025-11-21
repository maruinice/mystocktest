#!/usr/bin/env python3
"""
继续同步财务指标数据
从指定位置开始继续同步
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_financial_indicators import FinancialIndicatorsSyncService
import asyncio

print("\n" + "="*70)
print("继续同步财务指标数据")
print("="*70)

async def continue_sync():
    """继续同步"""
    service = FinancialIndicatorsSyncService()
    
    # 从第670条开始
    start_position = 2685
    
    print(f"📍 从第 {start_position} 只股票开始继续同步")
    print("="*70)
    
    # 继续同步
    await service.sync_all_stocks(start_position=start_position)

if __name__ == '__main__':
    try:
        asyncio.run(continue_sync())
    except KeyboardInterrupt:
        print("\n\n⚠️  同步被用户中断")
    except Exception as e:
        print(f"\n\n❌ 同步过程出错: {e}")
        import traceback
        traceback.print_exc()
