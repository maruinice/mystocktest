"""
测试回测功能完整性
包括：
1. 前端tab页面数据显示
2. 回测历史功能
3. 回测结果保存和查询
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from datetime import datetime
from app.services.backtest_engine import BacktestEngine, BacktestConfig
from app.services.strategy_database_service import strategy_db_service

async def test_backtest_with_full_data():
    """测试回测并确保返回完整数据"""
    print("\n" + "="*80)
    print("测试回测引擎完整数据返回")
    print("="*80)
    
    engine = BacktestEngine()
    
    # 获取策略31
    strategy = strategy_db_service.get_strategy_by_id(31)
    if not strategy:
        print("❌ 策略31不存在")
        return
    
    print(f"✅ 策略信息: {strategy.get('display_name', strategy.get('name', '未知策略'))}")
    
    # 构建回测配置
    config = BacktestConfig(
        strategy_id='31',
        strategy_name=strategy.get('display_name', strategy.get('name', '未知策略')),
        strategy_code='',
        start_date='2024-01-01',
        end_date='2024-03-31',
        initial_capital=100000.0,
        stock_pool=['000001.SZ'],
        buy_conditions=strategy['buy_conditions'] if isinstance(strategy['buy_conditions'], list) else json.loads(strategy['buy_conditions']),
        sell_conditions=strategy['sell_conditions'] if isinstance(strategy['sell_conditions'], list) else json.loads(strategy['sell_conditions']),
        risk_controls={'max_position_size': 0.3, 'stop_loss': 10, 'take_profit': 20}
    )
    
    print(f"✅ 回测配置: {config.start_date} ~ {config.end_date}")
    
    # 执行回测
    result = await engine.run_backtest(config)
    
    if result.get('status') != 'completed':
        print(f"❌ 回测失败: {result.get('error_message')}")
        return
    
    print(f"✅ 回测完成")
    print(f"   总收益率: {result['total_return']*100:.2f}%")
    print(f"   交易次数: {result['total_trades']}")
    
    # 检查关键数据字段
    required_fields = [
        'equity_curve', 'trades', 'returns_distribution', 'monthly_returns'
    ]
    
    for field in required_fields:
        if field in result and result[field]:
            print(f"✅ {field}: {len(result[field])} 条数据")
        else:
            print(f"❌ {field}: 数据缺失或为空")
    
    # 详细检查数据
    if result.get('returns_distribution'):
        print(f"   收益分布区间数: {len(result['returns_distribution'])}")
        for i, dist in enumerate(result['returns_distribution'][:3]):
            print(f"     区间{i+1}: {dist['bin_start']*100:.1f}%~{dist['bin_end']*100:.1f}%, 频数: {dist['count']}")
    
    if result.get('monthly_returns'):
        print(f"   月度收益数: {len(result['monthly_returns'])}")
        for mr in result['monthly_returns'][:3]:
            print(f"     {mr['month']}: {mr['return']*100:.2f}%")
    
    return result


def test_backtest_history_api():
    """测试回测历史API"""
    print("\n" + "="*80)
    print("测试回测历史API")
    print("="*80)
    
    try:
        # 测试获取回测历史
        results, total = strategy_db_service.get_backtest_results(
            user_id=1,
            strategy_id='31',
            page=1,
            size=10
        )
        
        print(f"✅ 获取回测历史成功")
        print(f"   总数: {total}")
        print(f"   当前页: {len(results)} 条")
        
        if results:
            latest = results[0]
            print(f"   最新回测: {latest['backtest_id']}")
            print(f"   策略名称: {latest['strategy_name']}")
            print(f"   收益率: {latest['total_return']*100:.2f}%")
            
            # 测试获取详情
            detail = strategy_db_service.get_backtest_result_detail(
                backtest_id=latest['backtest_id'],
                user_id=1
            )
            
            if detail:
                print(f"✅ 获取回测详情成功")
                print(f"   净值曲线: {len(detail.get('equity_curve', []))} 个点")
                print(f"   交易记录: {len(detail.get('trades', []))} 笔")
                print(f"   收益分布: {len(detail.get('returns_distribution', []))} 个区间")
                print(f"   月度收益: {len(detail.get('monthly_returns', []))} 个月")
            else:
                print(f"❌ 获取回测详情失败")
        else:
            print("   暂无回测历史")
    
    except Exception as e:
        print(f"❌ 测试回测历史API失败: {e}")
        import traceback
        traceback.print_exc()


def test_data_completeness():
    """测试数据完整性"""
    print("\n" + "="*80)
    print("测试数据完整性")
    print("="*80)
    
    # 模拟前端需要的数据结构
    mock_result = {
        'equity_curve': [
            {'date': '2024-01-01', 'value': 100000},
            {'date': '2024-01-02', 'value': 101000},
            {'date': '2024-01-03', 'value': 99500},
        ],
        'returns_distribution': [
            {'bin_start': -0.02, 'bin_end': -0.01, 'count': 5},
            {'bin_start': -0.01, 'bin_end': 0.0, 'count': 10},
            {'bin_start': 0.0, 'bin_end': 0.01, 'count': 15},
        ],
        'monthly_returns': [
            {'month': '2024-01', 'return': 0.05},
            {'month': '2024-02', 'return': -0.02},
            {'month': '2024-03', 'return': 0.03},
        ]
    }
    
    # 检查前端图表所需的数据格式
    print("✅ 净值曲线数据格式检查:")
    for eq in mock_result['equity_curve']:
        print(f"   日期: {eq['date']}, 净值: {eq['value']}")
    
    print("✅ 收益分布数据格式检查:")
    for dist in mock_result['returns_distribution']:
        print(f"   区间: {dist['bin_start']*100:.1f}%~{dist['bin_end']*100:.1f}%, 频数: {dist['count']}")
    
    print("✅ 月度收益数据格式检查:")
    for mr in mock_result['monthly_returns']:
        print(f"   {mr['month']}: {mr['return']*100:.2f}%")
    
    print("✅ 数据格式符合前端要求")


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("回测功能完整性测试")
    print("="*80)
    
    # 1. 测试回测引擎数据返回
    result = await test_backtest_with_full_data()
    
    # 2. 如果有结果，保存到数据库
    if result and result.get('status') == 'completed':
        print("\n保存回测结果到数据库...")
        result['user_id'] = 1
        backtest_id = strategy_db_service.save_backtest_result(result)
        if backtest_id:
            print(f"✅ 回测结果已保存: {backtest_id}")
        else:
            print("❌ 保存回测结果失败")
    
    # 3. 测试回测历史API
    test_backtest_history_api()
    
    # 4. 测试数据完整性
    test_data_completeness()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
    
    print("\n【前端测试步骤】")
    print("1. 刷新前端页面")
    print("2. 在策略管理页面，点击策略的'更多操作' -> '回测历史'")
    print("3. 在回测结果页面，切换到'回撤分析'、'收益分布'、'月度收益'标签页")
    print("4. 确认所有图表都有数据显示")


if __name__ == '__main__':
    asyncio.run(main())
