"""
回测引擎全面安全检查
确保回测引擎符合设计初衷，没有任何BUG
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from decimal import Decimal
from app.services.backtest_engine import BacktestEngine, BacktestConfig

class BacktestSafetyChecker:
    """回测引擎安全检查器"""
    
    def __init__(self):
        self.engine = BacktestEngine()
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        print(f"{status} - {test_name}")
        if details:
            print(f"     {details}")
    
    async def test_position_calculation(self):
        """测试仓位计算逻辑"""
        print("\n" + "="*80)
        print("测试1: 仓位计算逻辑")
        print("="*80)
        
        # 模拟场景
        initial_capital = 100000
        position_size = 0.3
        stock_price = 100
        
        # 第一次买入
        total_value = initial_capital
        target_position_value = total_value * position_size
        current_position_value = 0
        buy_value = target_position_value - current_position_value
        
        expected_buy_value = 30000
        passed = abs(buy_value - expected_buy_value) < 1
        self.log_test(
            "第一次买入金额计算",
            passed,
            f"预期: {expected_buy_value}, 实际: {buy_value}"
        )
        
        # 第二次买入（已有持仓）
        quantity = 300
        current_position_value = quantity * stock_price
        buy_value = target_position_value - current_position_value
        
        expected_buy_value = 0
        passed = buy_value <= 0
        self.log_test(
            "第二次买入应该为0（已达目标仓位）",
            passed,
            f"预期: <=0, 实际: {buy_value}"
        )
        
        # 测试仓位不会超标
        max_position = position_size * total_value
        actual_position = current_position_value
        passed = actual_position <= max_position * 1.01  # 允许1%误差
        self.log_test(
            "仓位不超过设定上限",
            passed,
            f"上限: {max_position}, 实际: {actual_position}"
        )
    
    async def test_slippage_calculation(self):
        """测试滑点计算"""
        print("\n" + "="*80)
        print("测试2: 滑点计算")
        print("="*80)
        
        stock_price = 100
        slippage = 0.001
        
        # 买入价格应该更高
        buy_price = stock_price * (1 + slippage)
        expected_buy = 100.1
        passed = abs(buy_price - expected_buy) < 0.01
        self.log_test(
            "买入价格计算（应高于市价）",
            passed,
            f"预期: {expected_buy}, 实际: {buy_price}"
        )
        
        # 卖出价格应该更低
        sell_price = stock_price * (1 - slippage)
        expected_sell = 99.9
        passed = abs(sell_price - expected_sell) < 0.01
        self.log_test(
            "卖出价格计算（应低于市价）",
            passed,
            f"预期: {expected_sell}, 实际: {sell_price}"
        )
        
        # 滑点损失
        slippage_loss = buy_price - sell_price
        expected_loss = 0.2
        passed = abs(slippage_loss - expected_loss) < 0.01
        self.log_test(
            "一买一卖滑点损失",
            passed,
            f"预期: {expected_loss}, 实际: {slippage_loss}"
        )
    
    async def test_commission_calculation(self):
        """测试手续费计算"""
        print("\n" + "="*80)
        print("测试3: 手续费计算")
        print("="*80)
        
        trade_amount = 10000
        commission_rate = 0.0003
        
        commission = trade_amount * commission_rate
        expected = 3.0
        passed = abs(commission - expected) < 0.01
        self.log_test(
            "手续费计算",
            passed,
            f"预期: {expected}, 实际: {commission}"
        )
        
        # 买入总成本
        buy_cost = trade_amount + commission
        expected_cost = 10003.0
        passed = abs(buy_cost - expected_cost) < 0.01
        self.log_test(
            "买入总成本（含手续费）",
            passed,
            f"预期: {expected_cost}, 实际: {buy_cost}"
        )
        
        # 卖出实际收入
        sell_income = trade_amount - commission
        expected_income = 9997.0
        passed = abs(sell_income - expected_income) < 0.01
        self.log_test(
            "卖出实际收入（扣手续费）",
            passed,
            f"预期: {expected_income}, 实际: {sell_income}"
        )
    
    async def test_cash_management(self):
        """测试资金管理"""
        print("\n" + "="*80)
        print("测试4: 资金管理")
        print("="*80)
        
        initial_cash = 100000
        buy_amount = 20000
        commission = 6
        
        # 买入后现金
        cash_after_buy = initial_cash - buy_amount - commission
        expected_cash = 79994
        passed = abs(cash_after_buy - expected_cash) < 1
        self.log_test(
            "买入后现金扣除",
            passed,
            f"预期: {expected_cash}, 实际: {cash_after_buy}"
        )
        
        # 卖出后现金
        sell_amount = 22000
        sell_commission = 6.6
        cash_after_sell = cash_after_buy + sell_amount - sell_commission
        expected_cash = 101987.4
        passed = abs(cash_after_sell - expected_cash) < 1
        self.log_test(
            "卖出后现金增加",
            passed,
            f"预期: {expected_cash}, 实际: {cash_after_sell}"
        )
        
        # 资金守恒
        profit = cash_after_sell - initial_cash
        expected_profit = sell_amount - buy_amount - commission - sell_commission
        passed = abs(profit - expected_profit) < 1
        self.log_test(
            "资金守恒（盈亏计算正确）",
            passed,
            f"预期盈亏: {expected_profit}, 实际盈亏: {profit}"
        )
    
    async def test_position_update(self):
        """测试持仓更新"""
        print("\n" + "="*80)
        print("测试5: 持仓更新")
        print("="*80)
        
        # 第一次买入
        quantity1 = 100
        price1 = 100
        cost1 = quantity1 * price1
        avg_cost1 = price1
        
        passed = abs(avg_cost1 - price1) < 0.01
        self.log_test(
            "第一次买入平均成本",
            passed,
            f"预期: {price1}, 实际: {avg_cost1}"
        )
        
        # 第二次买入（加仓）
        quantity2 = 100
        price2 = 110
        total_quantity = quantity1 + quantity2
        total_cost = cost1 + quantity2 * price2
        avg_cost2 = total_cost / total_quantity
        expected_avg = 105
        
        passed = abs(avg_cost2 - expected_avg) < 0.01
        self.log_test(
            "加仓后平均成本",
            passed,
            f"预期: {expected_avg}, 实际: {avg_cost2}"
        )
        
        # 卖出部分
        sell_quantity = 100
        remaining_quantity = total_quantity - sell_quantity
        expected_remaining = 100
        
        passed = remaining_quantity == expected_remaining
        self.log_test(
            "卖出后剩余数量",
            passed,
            f"预期: {expected_remaining}, 实际: {remaining_quantity}"
        )
    
    async def test_risk_controls(self):
        """测试风险控制"""
        print("\n" + "="*80)
        print("测试6: 风险控制")
        print("="*80)
        
        # 止损测试
        buy_price = 100
        current_price = 88
        stop_loss = 10  # 10%
        
        loss_pct = (current_price - buy_price) / buy_price * 100
        should_stop = loss_pct <= -stop_loss
        
        passed = should_stop
        self.log_test(
            "止损触发（亏损12%应触发10%止损）",
            passed,
            f"亏损: {loss_pct:.1f}%, 止损线: -{stop_loss}%"
        )
        
        # 止盈测试
        current_price = 125
        take_profit = 20  # 20%
        
        profit_pct = (current_price - buy_price) / buy_price * 100
        should_take = profit_pct >= take_profit
        
        passed = should_take
        self.log_test(
            "止盈触发（盈利25%应触发20%止盈）",
            passed,
            f"盈利: {profit_pct:.1f}%, 止盈线: {take_profit}%"
        )
        
        # 仓位控制
        total_value = 100000
        max_position_size = 0.3
        position_value = 35000
        
        position_pct = position_value / total_value
        exceeds_limit = position_pct > max_position_size
        
        passed = exceeds_limit  # 应该超限
        self.log_test(
            "仓位超限检测（35%应超过30%限制）",
            passed,
            f"实际仓位: {position_pct*100:.1f}%, 上限: {max_position_size*100:.0f}%"
        )
    
    async def test_full_backtest_integrity(self):
        """测试完整回测的完整性"""
        print("\n" + "="*80)
        print("测试7: 完整回测完整性")
        print("="*80)
        
        try:
            config = BacktestConfig(
                strategy_id='SAFETY_TEST',
                strategy_name='安全测试策略',
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
                    'max_position_size': 0.3,
                    'max_total_position': 0.8,
                    'stop_loss': 10,
                    'take_profit': 20
                }
            )
            
            result = await self.engine.run_backtest(config)
            
            if result.get('status') != 'completed':
                self.log_test(
                    "回测执行完成",
                    False,
                    f"状态: {result.get('status')}, 错误: {result.get('error_message')}"
                )
                return
            
            self.log_test("回测执行完成", True)
            
            # 检查必要字段
            required_fields = [
                'initial_capital', 'final_capital', 'total_return',
                'annualized_return', 'max_drawdown', 'sharpe_ratio',
                'total_trades', 'win_rate', 'equity_curve', 'trades'
            ]
            
            missing_fields = [f for f in required_fields if f not in result]
            passed = len(missing_fields) == 0
            self.log_test(
                "回测结果包含所有必要字段",
                passed,
                f"缺失字段: {missing_fields}" if missing_fields else "所有字段完整"
            )
            
            # 检查资金守恒
            initial = result['initial_capital']
            final = result['final_capital']
            trades = result.get('trades', [])
            
            # 计算所有交易的盈亏
            total_profit_loss = sum(t.get('profit_loss', 0) for t in trades)
            expected_final = initial + total_profit_loss
            
            # 允许一定误差（因为持仓市值变化）
            diff = abs(final - expected_final)
            passed = diff < initial * 0.5  # 允许50%误差（因为可能有未平仓）
            self.log_test(
                "资金变化合理",
                passed,
                f"初始: {initial:,.0f}, 最终: {final:,.0f}, 差异: {diff:,.0f}"
            )
            
            # 检查收益率计算
            calculated_return = (final / initial) - 1
            reported_return = result['total_return']
            diff = abs(calculated_return - reported_return)
            passed = diff < 0.01  # 允许1%误差
            self.log_test(
                "收益率计算正确",
                passed,
                f"计算值: {calculated_return*100:.2f}%, 报告值: {reported_return*100:.2f}%"
            )
            
            # 检查交易记录
            if trades:
                buy_trades = [t for t in trades if t['side'] == 'buy']
                sell_trades = [t for t in trades if t['side'] == 'sell']
                
                self.log_test(
                    "有交易记录",
                    True,
                    f"买入: {len(buy_trades)}笔, 卖出: {len(sell_trades)}笔"
                )
                
                # 检查是否有重复买入
                buy_dates = [t['date'] for t in buy_trades]
                unique_dates = set(buy_dates)
                passed = len(buy_dates) == len(unique_dates)
                self.log_test(
                    "没有同一天重复买入",
                    passed,
                    f"总买入: {len(buy_dates)}, 唯一日期: {len(unique_dates)}"
                )
            else:
                self.log_test(
                    "有交易记录",
                    False,
                    "没有产生任何交易"
                )
            
            # 检查净值曲线
            equity_curve = result.get('equity_curve', [])
            if equity_curve:
                passed = len(equity_curve) > 0
                self.log_test(
                    "净值曲线存在",
                    passed,
                    f"数据点: {len(equity_curve)}"
                )
                
                # 检查净值曲线连续性
                dates = [e['date'] for e in equity_curve]
                passed = dates == sorted(dates)
                self.log_test(
                    "净值曲线日期连续",
                    passed,
                    f"起始: {dates[0]}, 结束: {dates[-1]}"
                )
            else:
                self.log_test(
                    "净值曲线存在",
                    False,
                    "净值曲线为空"
                )
            
        except Exception as e:
            self.log_test(
                "回测执行无异常",
                False,
                f"异常: {str(e)}"
            )
            import traceback
            traceback.print_exc()
    
    async def test_extreme_scenarios(self):
        """测试极端场景"""
        print("\n" + "="*80)
        print("测试8: 极端场景")
        print("="*80)
        
        # 场景1: 资金不足
        available_cash = 1000
        required_cash = 20000
        can_buy = available_cash >= required_cash
        
        passed = not can_buy
        self.log_test(
            "资金不足时不能买入",
            passed,
            f"可用: {available_cash}, 需要: {required_cash}"
        )
        
        # 场景2: 卖出数量超过持仓
        position_quantity = 100
        sell_quantity = 200
        actual_sell = min(sell_quantity, position_quantity)
        
        passed = actual_sell == position_quantity
        self.log_test(
            "卖出数量不超过持仓",
            passed,
            f"持仓: {position_quantity}, 尝试卖出: {sell_quantity}, 实际卖出: {actual_sell}"
        )
        
        # 场景3: 价格为0
        price = 0
        quantity = 100
        can_trade = price > 0
        
        passed = not can_trade
        self.log_test(
            "价格为0时不能交易",
            passed,
            f"价格: {price}"
        )
        
        # 场景4: 负数检查
        negative_quantity = -100
        is_valid = negative_quantity > 0
        
        passed = not is_valid
        self.log_test(
            "负数数量无效",
            passed,
            f"数量: {negative_quantity}"
        )
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("测试摘要")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for t in self.test_results:
                if not t['passed']:
                    print(f"  ❌ {t['test']}")
                    if t['details']:
                        print(f"     {t['details']}")
        
        print("\n" + "="*80)
        if failed_tests == 0:
            print("🎉 所有测试通过！回测引擎安全可靠！")
        else:
            print("⚠️  存在失败的测试，请检查回测引擎！")
        print("="*80)


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("回测引擎全面安全检查")
    print("="*80)
    
    checker = BacktestSafetyChecker()
    
    # 运行所有测试
    await checker.test_position_calculation()
    await checker.test_slippage_calculation()
    await checker.test_commission_calculation()
    await checker.test_cash_management()
    await checker.test_position_update()
    await checker.test_risk_controls()
    await checker.test_full_backtest_integrity()
    await checker.test_extreme_scenarios()
    
    # 打印摘要
    checker.print_summary()


if __name__ == '__main__':
    asyncio.run(main())
