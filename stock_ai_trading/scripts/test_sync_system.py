"""
数据同步系统测试脚本
用于验证同步服务的基本功能
"""

import asyncio
import sys
from app.services.sync_services.sync_manager import sync_manager
from app.services.sync_services.stock_basic_sync import StockBasicSyncService
from app.services.sync_services.trade_cal_sync import TradeCalSyncService


async def test_service_list():
    """测试获取服务列表"""
    print("\n" + "="*60)
    print("测试1: 获取同步服务列表")
    print("="*60)
    
    services = sync_manager.get_service_list()
    
    print(f"\n共有 {len(services)} 个同步服务：\n")
    
    for service in services:
        status = "✅ 已实现" if service['implemented'] else "⚠️  未实现"
        print(f"{status} {service['name']}")
        print(f"   - Key: {service['key']}")
        print(f"   - 表: {service['table']}")
        print(f"   - 频率: {service['frequency']}")
        print(f"   - API: {service['api']}")
        print()
    
    return True


async def test_stock_basic_sync():
    """测试股票基础信息同步"""
    print("\n" + "="*60)
    print("测试2: 股票基础信息同步")
    print("="*60)
    
    service = StockBasicSyncService()
    
    print("\n开始同步...")
    result = await service.sync()
    
    if result['success']:
        print(f"✅ 同步成功: {result['message']}")
        if 'data' in result:
            print(f"   - 总数: {result['data'].get('total', 0)}")
            print(f"   - 保存: {result['data'].get('saved', 0)}")
    else:
        print(f"❌ 同步失败: {result['message']}")
    
    # 获取同步状态
    status = service.get_sync_status()
    print(f"\n同步状态:")
    print(f"   - 进度: {status['progress']}%")
    print(f"   - 当前: {status['current']}/{status['total']}")
    print(f"   - 消息: {status['message']}")
    
    return result['success']


async def test_trade_cal_sync():
    """测试交易日历同步"""
    print("\n" + "="*60)
    print("测试3: 交易日历同步（增量）")
    print("="*60)
    
    service = TradeCalSyncService()
    
    print("\n开始同步（自动增量）...")
    result = await service.sync()
    
    if result['success']:
        print(f"✅ 同步成功: {result['message']}")
        if 'data' in result:
            print(f"   - 开始日期: {result['data'].get('start_date', 'N/A')}")
            print(f"   - 结束日期: {result['data'].get('end_date', 'N/A')}")
            print(f"   - 总数: {result['data'].get('total', 0)}")
            print(f"   - 保存: {result['data'].get('saved', 0)}")
    else:
        print(f"❌ 同步失败: {result['message']}")
    
    return result['success']


async def test_sync_manager():
    """测试同步管理器"""
    print("\n" + "="*60)
    print("测试4: 同步管理器")
    print("="*60)
    
    # 测试启动同步
    print("\n通过管理器启动同步...")
    result = await sync_manager.start_sync('stock_basic')
    
    if result['success']:
        print(f"✅ 启动成功: {result['message']}")
    else:
        print(f"❌ 启动失败: {result['message']}")
    
    # 测试获取状态
    print("\n获取同步状态...")
    status = sync_manager.get_sync_status('stock_basic')
    print(f"   - 服务: {status.get('service_name', 'N/A')}")
    print(f"   - 运行中: {status.get('is_running', False)}")
    print(f"   - 进度: {status.get('progress', 0)}%")
    
    # 测试获取统计
    print("\n获取数据统计...")
    stats = await sync_manager.get_data_statistics('stock_basic')
    print(f"   - 表: {stats.get('table', 'N/A')}")
    print(f"   - 记录数: {stats.get('total_count', 0)}")
    print(f"   - 最新日期: {stats.get('last_sync_date', 'N/A')}")
    
    return result['success']


async def test_breakpoint_resume():
    """测试断点续传"""
    print("\n" + "="*60)
    print("测试5: 断点续传功能")
    print("="*60)
    
    service = StockBasicSyncService()
    
    # 保存同步位置
    print("\n保存同步位置...")
    await service.save_sync_position('test_sync', '1000')
    print("✅ 位置已保存: 1000")
    
    # 获取同步位置
    print("\n获取同步位置...")
    position = await service.get_sync_position('test_sync')
    print(f"✅ 获取位置: {position}")
    
    # 清除同步位置
    print("\n清除同步位置...")
    await service.clear_sync_position('test_sync')
    print("✅ 位置已清除")
    
    # 验证清除
    position = await service.get_sync_position('test_sync')
    if position is None:
        print("✅ 验证成功: 位置已清除")
        return True
    else:
        print(f"❌ 验证失败: 位置仍存在 ({position})")
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("数据同步系统测试")
    print("="*60)
    
    results = []
    
    try:
        # 测试1: 服务列表
        results.append(("服务列表", await test_service_list()))
        
        # 测试2: 股票基础信息同步
        # results.append(("股票基础信息同步", await test_stock_basic_sync()))
        
        # 测试3: 交易日历同步
        # results.append(("交易日历同步", await test_trade_cal_sync()))
        
        # 测试4: 同步管理器
        # results.append(("同步管理器", await test_sync_manager()))
        
        # 测试5: 断点续传
        results.append(("断点续传", await test_breakpoint_resume()))
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 输出测试结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\n总计: {passed}/{total} 通过")
    
    return passed == total


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
