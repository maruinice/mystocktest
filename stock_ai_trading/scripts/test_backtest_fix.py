"""
测试回测引擎修复效果
对比修复前后的差异
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.services.backtest_engine import BacktestEngine, BacktestConfig

async def test_position_calculation():
    """测试仓位计算逻辑"""
    print("\n" + "="*80)
    print("测试仓位计算逻辑")
    print("="*80)
    
    # 模拟场景
    print("\n场景: 连续3次买入信号")
    print("初始资金: 100,000")
    print("股价: 100元")
    print("仓位大小: 30%")
    print("滑点: 0.1%")
    print("手续费: 0.03%")
    
    initial_capital = 100000
    stock_price = 100
    position_size = 0.3
    slippage = 0.001
    commission = 0.0003
    
    # 模拟持仓
    cash = initial_capital
    quantity = 0
    
    print("\n" + "-"*80)
    
    for i in range(1, 4):
        print(f"\n第{i}次买入信号:")
        
        # 当前总资产
        total_value = cash + quantity * stock_price
        print(f"  当前总资产: {total_value:,.2f}")
        print(f"  当前现金: {cash:,.2f}")
        print(f"  当前持仓: {quantity}股 = {quantity * stock_price:,.2f}元")
        
        # 计算目标持仓市值
        target_position_value = total_value * position_size
        print(f"  目标持仓市值: {target_position_value:,.2f} ({position_size*100:.0f}%)")
        
        # 当前持仓市值
        current_position_value = quantity * stock_price
        print(f"  当前持仓市值: {current_position_value:,.2f}")
        
        # 需要买入的金额
        buy_value = target_position_value - current_position_value
        print(f"  需要买入金额: {buy_value:,.2f}")
        
        if buy_value <= 0:
            print(f"  ✅ 已达到目标仓位，无需买入")
            continue
        
        # 买入价格（含滑点）
        trade_price = stock_price * (1 + slippage)
        print(f"  买入价格: {trade_price:.2f} (含滑点)")
        
        # 买入数量
        target_quantity = int(buy_value / trade_price / 100) * 100
        max_quantity = int(cash / trade_price / 100) * 100
        buy_quantity = min(target_quantity, max_quantity)
        
        print(f"  目标买入数量: {target_quantity}股")
        print(f"  最大可买数量: {max_quantity}股")
        print(f"  实际买入数量: {buy_quantity}股")
        
        if buy_quantity >= 100:
            # 执行买入
            trade_amount = buy_quantity * trade_price
            commission_fee = trade_amount * commission
            total_cost = trade_amount + commission_fee
            
            print(f"  交易金额: {trade_amount:,.2f}")
            print(f"  手续费: {commission_fee:,.2f}")
            print(f"  总花费: {total_cost:,.2f}")
            
            # 更新持仓
            cash -= total_cost
            quantity += buy_quantity
            
            print(f"  ✅ 买入成功")
            print(f"  更新后现金: {cash:,.2f}")
            print(f"  更新后持仓: {quantity}股 = {quantity * stock_price:,.2f}元")
            print(f"  实际仓位: {quantity * stock_price / total_value * 100:.1f}%")
        else:
            print(f"  ❌ 买入数量不足100股")
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
    
    final_total = cash + quantity * stock_price
    print(f"\n最终状态:")
    print(f"  总资产: {final_total:,.2f}")
    print(f"  现金: {cash:,.2f} ({cash/final_total*100:.1f}%)")
    print(f"  持仓: {quantity}股 = {quantity * stock_price:,.2f}元 ({quantity * stock_price/final_total*100:.1f}%)")


async def test_slippage_calculation():
    """测试滑点计算"""
    print("\n" + "="*80)
    print("测试滑点计算")
    print("="*80)
    
    stock_price = 100
    slippage = 0.001
    
    print(f"\n当前股价: {stock_price}元")
    print(f"滑点设置: {slippage*100:.2f}%")
    
    # 买入价格
    buy_price = stock_price * (1 + slippage)
    print(f"\n买入价格: {buy_price:.2f}元 (高于市价 {(buy_price - stock_price):.2f}元)")
    
    # 卖出价格
    sell_price = stock_price * (1 - slippage)
    print(f"卖出价格: {sell_price:.2f}元 (低于市价 {(stock_price - sell_price):.2f}元)")
    
    # 一买一卖的损失
    loss = buy_price - sell_price
    loss_pct = loss / stock_price * 100
    print(f"\n一买一卖的滑点损失: {loss:.2f}元 ({loss_pct:.2f}%)")


async def test_full_backtest():
    """测试完整回测"""
    print("\n" + "="*80)
    print("测试完整回测（修复后）")
    print("="*80)
    
    try:
        from app.services.backtest_engine import BacktestEngine, BacktestConfig
        
        engine = BacktestEngine()
        
        # 创建测试配置
        config = BacktestConfig(
            strategy_id='TEST_FIX',
            strategy_name='测试修复后的回测',
            strategy_code='',
            start_date='2023-10-01',
            end_date='2023-11-01',
            initial_capital=100000.0,
            stock_pool=['000001.SZ'],
            buy_conditions=[
                {
                    'type': 'price',
                    'operator': 'greater_than',
                    'value': 'MA20',
                    'description': '价格突破MA20'
                }
            ],
            sell_conditions=[
                {
                    'type': 'price',
                    'operator': 'less_than',
                    'value': 'MA20',
                    'description': '价格跌破MA20'
                }
            ],
            risk_controls={
                'max_position_size': 0.3,  # 单只股票最大30%
                'max_total_position': 0.8,  # 总仓位最大80%
                'stop_loss': 10,
                'take_profit': 20
            }
        )
        
        print(f"\n回测配置:")
        print(f"  策略: {config.strategy_name}")
        print(f"  期间: {config.start_date} ~ {config.end_date}")
        print(f"  初始资金: {config.initial_capital:,.0f}")
        print(f"  股票池: {config.stock_pool}")
        print(f"  最大单只仓位: {config.risk_controls['max_position_size']*100:.0f}%")
        
        # 运行回测
        print(f"\n开始回测...")
        result = await engine.run_backtest(config)
        
        if result.get('status') == 'completed':
            print(f"\n✅ 回测完成:")
            print(f"  总收益率: {result['total_return']*100:.2f}%")
            print(f"  年化收益: {result['annualized_return']*100:.2f}%")
            print(f"  最大回撤: {result['max_drawdown']*100:.2f}%")
            print(f"  夏普比率: {result['sharpe_ratio']:.2f}")
            print(f"  总交易数: {result['total_trades']}")
            print(f"  胜率: {result['win_rate']*100:.2f}%")
            
            # 检查交易记录
            trades = result.get('trades', [])
            if trades:
                print(f"\n交易记录 (前10笔):")
                for i, trade in enumerate(trades[:10], 1):
                    print(f"  {i}. {trade['date']} {trade['side']:4s} {trade['code']} "
                          f"数量:{trade['quantity']:6d} 价格:{trade['price']:8.2f} "
                          f"金额:{trade['amount']:12.2f}")
                
                # 分析买入交易
                buy_trades = [t for t in trades if t['side'] == 'buy']
                if buy_trades:
                    print(f"\n买入交易分析:")
                    print(f"  买入次数: {len(buy_trades)}")
                    print(f"  平均买入金额: {sum(t['amount'] for t in buy_trades) / len(buy_trades):,.2f}")
                    
                    # 检查是否有重复买入
                    buy_dates = [t['date'] for t in buy_trades]
                    unique_dates = set(buy_dates)
                    if len(buy_dates) != len(unique_dates):
                        print(f"  ⚠️ 发现重复买入！")
                    else:
                        print(f"  ✅ 没有重复买入")
            else:
                print(f"\n  ⚠️ 没有交易记录")
            
            # 检查最终资产
            final_capital = result['final_capital']
            initial_capital = result['initial_capital']
            
            print(f"\n资产变化:")
            print(f"  初始资金: {initial_capital:,.2f}")
            print(f"  最终资金: {final_capital:,.2f}")
            print(f"  盈亏: {final_capital - initial_capital:,.2f}")
            
            if final_capital < initial_capital * 0.5:
                print(f"  🔴 警告: 资金损失超过50%，可能仍有问题！")
            elif final_capital < initial_capital * 0.8:
                print(f"  ⚠️ 注意: 资金损失超过20%")
            else:
                print(f"  ✅ 资金变化正常")
                
        else:
            print(f"\n❌ 回测失败:")
            print(f"  错误: {result.get('error_message', '未知错误')}")
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("回测引擎修复验证")
    print("="*80)
    
    # 1. 测试仓位计算
    await test_position_calculation()
    
    # 2. 测试滑点计算
    await test_slippage_calculation()
    
    # 3. 测试完整回测
    await test_full_backtest()
    
    print("\n" + "="*80)
    print("所有测试完成")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
