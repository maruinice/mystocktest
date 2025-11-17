#!/usr/bin/env python3
"""
继续同步审计意见数据
从第60只股票开始继续同步
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_audit_opinions import AuditOpinionsSyncService
import asyncio

print("\n" + "="*70)
print("继续同步审计意见数据")
print("="*70)

async def continue_sync():
    """继续同步"""
    service = AuditOpinionsSyncService()
    
    # 从第847只开始（上次失败位置）
    start_position = 847
    
    print(f"📍 从第 {start_position} 只股票开始继续同步")
    print(f"⏱️  API调用频率：每次1.2秒（每分钟约50次）")
    print(f"📊 已同步: 710只 (12.72%) | 剩余: 4,736只")
    print(f"⏰ 预估剩余时间: 1.58小时")
    print("="*70)
    
    # 继续同步
    await service.sync_all_audit_opinions(start_position=start_position)

if __name__ == '__main__':
    try:
        asyncio.run(continue_sync())
    except KeyboardInterrupt:
        print("\n\n⚠️  同步被用户中断")
    except Exception as e:
        print(f"\n\n❌ 同步过程出错: {e}")
        import traceback
        traceback.print_exc()
