#!/usr/bin/env python3
"""强制同步数据"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.data_sync_enhanced_service import DataSyncEnhancedService
from app.config.settings import settings

print("\n" + "="*60)
print("强制同步数据")
print("="*60)

# 检查配置
print("\n检查配置...")
if not settings.TUSHARE_TOKEN:
    print("❌ Tushare Token未配置！")
    print("   请在 .env 文件中设置 TUSHARE_TOKEN")
    sys.exit(1)
else:
    print(f"✅ Tushare Token已配置 (长度: {len(settings.TUSHARE_TOKEN)})")

async def force_sync():
    service = DataSyncEnhancedService()
    db = next(get_db())
    
    success_count = 0
    total_count = 0
    
    # 1. 同步行业分类
    print("\n" + "-"*60)
    print("1. 同步行业分类 (申万一级)")
    print("-"*60)
    try:
        result = await service.sync_industry_classification(db, src='SW2021', level='L1')
        total_count += 1
        
        if result.get('success'):
            success_count += 1
            count = result.get('count', 0)
            total = result.get('total', 0)
            print(f"✅ 同步成功: 新增/更新 {count} 条，总共 {total} 条")
        else:
            print(f"❌ 同步失败: {result.get('message', '未知错误')}")
    except Exception as e:
        total_count += 1
        print(f"❌ 同步异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 同步涨跌停（近3年）
    print("\n" + "-"*60)
    print("2. 同步涨跌停价格 (近3年)")
    print("-"*60)
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
        print(f"   日期范围: {start_date} - {end_date}")
        print(f"   ⏳ 预计需要较长时间，请耐心等待...")
        
        result = await service.sync_limit_prices(db, start_date=start_date, end_date=end_date)
        total_count += 1
        
        if result.get('success'):
            success_count += 1
            count = result.get('count', 0)
            total = result.get('total', 0)
            print(f"✅ 同步成功: 新增/更新 {count} 条，总共 {total} 条")
        else:
            print(f"❌ 同步失败: {result.get('message', '未知错误')}")
    except Exception as e:
        total_count += 1
        print(f"❌ 同步异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 同步停复牌（近3年）
    print("\n" + "-"*60)
    print("3. 同步停复牌信息 (近3年)")
    print("-"*60)
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
        print(f"   日期范围: {start_date} - {end_date}")
        print(f"   ⏳ 预计需要较长时间，请耐心等待...")
        
        result = await service.sync_suspend_info(db, start_date=start_date, end_date=end_date)
        total_count += 1
        
        if result.get('success'):
            success_count += 1
            count = result.get('count', 0)
            suspend_count = result.get('suspend_count', 0)
            resume_count = result.get('resume_count', 0)
            print(f"✅ 同步成功: 新增/更新 {count} 条")
            print(f"   停牌: {suspend_count} 条，复牌: {resume_count} 条")
        else:
            print(f"❌ 同步失败: {result.get('message', '未知错误')}")
    except Exception as e:
        total_count += 1
        print(f"❌ 同步异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 同步审计意见（近3年）
    print("\n" + "-"*60)
    print("4. 同步审计意见 (近3年)")
    print("-"*60)
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
        print(f"   日期范围: {start_date} - {end_date}")
        print(f"   ⏳ 预计需要较长时间，请耐心等待...")
        
        result = await service.sync_audit_opinions(db, start_date=start_date, end_date=end_date)
        total_count += 1
        
        if result.get('success'):
            success_count += 1
            count = result.get('count', 0)
            total = result.get('total', 0)
            print(f"✅ 同步成功: 新增/更新 {count} 条，总共 {total} 条")
        else:
            print(f"❌ 同步失败: {result.get('message', '未知错误')}")
    except Exception as e:
        total_count += 1
        print(f"❌ 同步异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 汇总
    print("\n" + "="*60)
    print("同步汇总")
    print("="*60)
    print(f"总任务数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    
    if success_count == total_count:
        print("\n🎉 所有数据同步成功！")
    elif success_count > 0:
        print(f"\n⚠️  部分数据同步成功 ({success_count}/{total_count})")
    else:
        print("\n❌ 所有数据同步失败，请检查错误信息")
    
    print("\n运行 'python check_data.py' 查看数据")
    print("="*60)

if __name__ == '__main__':
    try:
        asyncio.run(force_sync())
    except KeyboardInterrupt:
        print("\n\n⚠️  同步被用户中断")
    except Exception as e:
        print(f"\n\n❌ 同步过程出错: {e}")
        import traceback
        traceback.print_exc()
