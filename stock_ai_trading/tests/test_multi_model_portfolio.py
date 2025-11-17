"""
多模型资产账簿测试用例

测试多模型投资组合管理系统的各项功能
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
import uuid

from app.services.multi_model_portfolio import (
    MultiModelPortfolio, ModelAccount, Transaction, Position,
    TransactionType, FeeConfig, SlippageConfig
)
from app.services.performance_analyzer import PerformanceAnalyzer


class TestMultiModelPortfolio:
    """多模型投资组合测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.portfolio = MultiModelPortfolio()
        self.model_id = "test_model_001"
        self.initial_cash = Decimal("1000000")
    
    def test_create_account(self):
        """测试创建账户"""
        account = self.portfolio.create_account(self.model_id, self.initial_cash)
        
        assert account.model_id == self.model_id
        assert account.initial_cash == self.initial_cash
        assert account.cash_balance == self.initial_cash
        assert len(account.positions) == 0
        assert len(account.transactions) == 0
        assert account.created_at is not None
    
    def test_create_duplicate_account(self):
        """测试创建重复账户"""
        self.portfolio.create_account(self.model_id, self.initial_cash)
        
        with pytest.raises(ValueError, match="账户已存在"):
            self.portfolio.create_account(self.model_id, self.initial_cash)
    
    def test_get_account(self):
        """测试获取账户"""
        created_account = self.portfolio.create_account(self.model_id, self.initial_cash)
        retrieved_account = self.portfolio.get_account(self.model_id)
        
        assert retrieved_account == created_account
        assert self.portfolio.get_account("non_existent") is None
    
    def test_execute_buy_trade(self):
        """测试买入交易"""
        self.portfolio.create_account(self.model_id, self.initial_cash)
        
        symbol = "000001.SZ"
        quantity = Decimal("1000")
        price = Decimal("10.50")
        
        transaction = self.portfolio.execute_trade(
            model_id=self.model_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            is_buy=True
        )
        
        # 验证交易记录
        assert transaction.model_id == self.model_id
        assert transaction.symbol == symbol
        assert transaction.quantity == quantity
        assert transaction.price == price
        assert transaction.transaction_type == TransactionType.BUY
        assert transaction.amount == quantity * price
        
        # 验证费用计算
        expected_commission = max(transaction.amount * self.portfolio.fee_config.commission_rate, 
                                self.portfolio.fee_config.min_commission)
        assert transaction.commission == expected_commission
        assert transaction.stamp_tax == Decimal("0")  # 买入无印花税
        assert transaction.transfer_fee == transaction.amount * self.portfolio.fee_config.transfer_fee_rate
        
        # 验证账户状态
        account = self.portfolio.get_account(self.model_id)
        assert len(account.positions) == 1
        assert symbol in account.positions
        
        position = account.positions[symbol]
        assert position.quantity == quantity
        assert position.avg_cost == price
        
        # 验证现金余额
        expected_cash = self.initial_cash - transaction.total_cost
        assert account.cash_balance == expected_cash
    
    def test_execute_sell_trade(self):
        """测试卖出交易"""
        self.portfolio.create_account(self.model_id, self.initial_cash)
        
        symbol = "000001.SZ"
        buy_quantity = Decimal("1000")
        buy_price = Decimal("10.50")
        sell_quantity = Decimal("500")
        sell_price = Decimal("11.00")
        
        # 先买入
        self.portfolio.execute_trade(
            model_id=self.model_id,
            symbol=symbol,
            quantity=buy_quantity,
            price=buy_price,
            is_buy=True
        )
        
        # 再卖出
        transaction = self.portfolio.execute_trade(
            model_id=self.model_id,
            symbol=symbol,
            quantity=sell_quantity,
            price=sell_price,
            is_buy=False
        )
        
        # 验证交易记录
        assert transaction.transaction_type == TransactionType.SELL
        assert transaction.stamp_tax > Decimal("0")  # 卖出有印花税
        
        # 验证持仓变化
        account = self.portfolio.get_account(self.model_id)
        position = account.positions[symbol]
        assert position.quantity == buy_quantity - sell_quantity
        
        # 验证已实现盈亏
        expected_realized_pnl = (sell_price - buy_price) * sell_quantity
        assert abs(position.realized_pnl - expected_realized_pnl) < Decimal("1")  # 允许费用误差
    
    def test_insufficient_cash(self):
        """测试资金不足"""
        small_cash = Decimal("1000")
        self.portfolio.create_account(self.model_id, small_cash)
        
        with pytest.raises(ValueError, match="资金不足"):
            self.portfolio.execute_trade(
                model_id=self.model_id,
                symbol="000001.SZ",
                quantity=Decimal("1000"),
                price=Decimal("10.50"),
                is_buy=True
            )
    
    def test_insufficient_position(self):
        """测试持仓不足"""
        self.portfolio.create_account(self.model_id, self.initial_cash)
        
        with pytest.raises(ValueError, match="尝试卖出未持有的股票"):
            self.portfolio.execute_trade(
                model_id=self.model_id,
                symbol="000001.SZ",
                quantity=Decimal("1000"),
                price=Decimal("10.50"),
                is_buy=False
            )
    
    def test_slippage_calculation(self):
        """测试滑点计算"""
        self.portfolio.create_account(self.model_id, self.initial_cash)
        
        symbol = "000001.SZ"
        quantity = Decimal("1000")
        price = Decimal("10.50")
        avg_volume = Decimal("100000")
        
        transaction = self.portfolio.execute_trade(
            model_id=self.model_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            is_buy=True,
            avg_volume=avg_volume
        )
        
        # 验证滑点计算
        assert transaction.slippage > Decimal("0")
        
        # 测试大单滑点
        large_quantity = Decimal("50000")  # 50%的平均成交量
        large_transaction = self.portfolio.execute_trade(
            model_id=self.model_id,
            symbol="000002.SZ",
            quantity=large_quantity,
            price=price,
            is_buy=True,
            avg_volume=avg_volume
        )
        
        # 大单滑点应该更高
        assert large_transaction.slippage > transaction.slippage
    
    def test_update_market_prices(self):
        """测试更新市场价格"""
        self.portfolio.create_account(self.model_id, self.initial_cash)
        
        symbol = "000001.SZ"
        quantity = Decimal("1000")
        buy_price = Decimal("10.50")
        new_price = Decimal("11.50")
        
        # 买入股票
        self.portfolio.execute_trade(
            model_id=self.model_id,
            symbol=symbol,
            quantity=quantity,
            price=buy_price,
            is_buy=True
        )
        
        # 更新价格
        self.portfolio.update_market_prices({symbol: new_price})
        
        # 验证持仓市值更新
        account = self.portfolio.get_account(self.model_id)
        position = account.positions[symbol]
        assert position.last_price == new_price
        assert position.market_value == quantity * new_price
        assert position.unrealized_pnl == (new_price - buy_price) * quantity
    
    def test_get_portfolio_summary(self):
        """测试获取投资组合汇总"""
        # 先创建账户
        self.portfolio.create_account(self.model_id, self.initial_cash)
        
        # 执行交易
        self.portfolio.execute_trade(
            model_id=self.model_id,
            symbol="000001.SZ",
            quantity=Decimal("1000"),
            price=Decimal("10.50"),
            is_buy=True
        )
        
        # 更新市场价格
        self.portfolio.update_market_prices({"000001.SZ": Decimal("11.00")})
        
        summary = self.portfolio.get_portfolio_summary()
        
        # 验证汇总结构
        assert "aggregate" in summary
        assert "accounts" in summary
        
        # 验证汇总数据
        assert summary["aggregate"]["total_cash"] > Decimal("0")
        assert summary["aggregate"]["total_market_value"] > Decimal("0")
        assert summary["aggregate"]["total_assets"] > Decimal("0")
        
        # 验证账户数据
        assert self.model_id in summary["accounts"]
        account_summary = summary["accounts"][self.model_id]
        assert "cash_balance" in account_summary
        assert "market_value" in account_summary
        assert "total_assets" in account_summary
        assert "total_pnl" in account_summary
        assert "return_rate" in account_summary
    
    def test_get_model_positions(self):
        """测试获取模型持仓"""
        self.portfolio.create_account(self.model_id, self.initial_cash)
        
        symbols = ["000001.SZ", "000002.SZ"]
        for symbol in symbols:
            self.portfolio.execute_trade(
                model_id=self.model_id,
                symbol=symbol,
                quantity=Decimal("1000"),
                price=Decimal("10.50"),
                is_buy=True
            )
        
        positions = self.portfolio.get_model_positions(self.model_id)
        
        assert len(positions) == 2
        for symbol in symbols:
            assert symbol in positions
            assert positions[symbol].quantity == Decimal("1000")
    
    def test_get_model_transactions(self):
        """测试获取模型交易记录"""
        self.portfolio.create_account(self.model_id, self.initial_cash)
        
        # 执行多笔交易
        for i in range(5):
            self.portfolio.execute_trade(
                model_id=self.model_id,
                symbol=f"00000{i+1}.SZ",
                quantity=Decimal("1000"),
                price=Decimal("10.50"),
                is_buy=True
            )
        
        # 获取所有交易
        all_transactions = self.portfolio.get_model_transactions(self.model_id)
        assert len(all_transactions) == 5
        
        # 获取限制数量的交易
        limited_transactions = self.portfolio.get_model_transactions(self.model_id, limit=3)
        assert len(limited_transactions) == 3
        
        # 验证交易按时间倒序排列
        for i in range(len(limited_transactions) - 1):
            assert limited_transactions[i].timestamp >= limited_transactions[i + 1].timestamp


class TestModelAccount:
    """模型账户测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.model_id = "test_model"
        self.initial_cash = Decimal("1000000")
        self.account = ModelAccount(self.model_id, self.initial_cash)
    
    def test_account_initialization(self):
        """测试账户初始化"""
        assert self.account.model_id == self.model_id
        assert self.account.initial_cash == self.initial_cash
        assert self.account.cash_balance == self.initial_cash
        assert len(self.account.positions) == 0
        assert len(self.account.transactions) == 0
        assert self.account.created_at is not None
    
    def test_get_total_market_value(self):
        """测试获取总市值"""
        # 初始市值为0
        assert self.account.get_total_market_value() == Decimal("0")
        
        # 添加持仓
        symbol = "000001.SZ"
        position = Position(
            symbol=symbol,
            quantity=Decimal("1000"),
            avg_cost=Decimal("10.50")
        )
        position.update_market_value(Decimal("11.00"))
        self.account.positions[symbol] = position
        
        expected_market_value = Decimal("1000") * Decimal("11.00")
        assert self.account.get_total_market_value() == expected_market_value
    
    def test_get_total_assets(self):
        """测试获取总资产"""
        # 添加持仓
        symbol = "000001.SZ"
        position = Position(
            symbol=symbol,
            quantity=Decimal("1000"),
            avg_cost=Decimal("10.50")
        )
        position.update_market_value(Decimal("11.00"))
        self.account.positions[symbol] = position
        
        # 模拟现金减少
        self.account.cash_balance = Decimal("900000")
        
        expected_total_assets = Decimal("900000") + Decimal("11000")
        assert self.account.get_total_assets() == expected_total_assets
    
    def test_get_total_pnl(self):
        """测试获取总盈亏"""
        # 添加持仓
        symbol = "000001.SZ"
        position = Position(
            symbol=symbol,
            quantity=Decimal("1000"),
            avg_cost=Decimal("10.50")
        )
        position.update_market_value(Decimal("11.00"))
        position.realized_pnl = Decimal("100")
        self.account.positions[symbol] = position
        
        # 总盈亏 = 未实现盈亏 + 已实现盈亏
        expected_unrealized_pnl = (Decimal("11.00") - Decimal("10.50")) * Decimal("1000")
        expected_total_pnl = expected_unrealized_pnl + Decimal("100")
        
        assert abs(self.account.get_total_pnl() - expected_total_pnl) < Decimal("0.01")
    
    def test_get_return_rate(self):
        """测试获取收益率"""
        # 初始收益率为0
        assert self.account.get_return_rate() == Decimal("0")
        
        # 模拟盈利
        self.account.cash_balance = Decimal("1100000")  # 盈利10万
        
        expected_return_rate = Decimal("100000") / self.initial_cash
        assert self.account.get_return_rate() == expected_return_rate


class TestPosition:
    """持仓测试类"""
    
    def test_position_initialization(self):
        """测试持仓初始化"""
        symbol = "000001.SZ"
        quantity = Decimal("1000")
        avg_cost = Decimal("10.50")
        
        position = Position(symbol, quantity, avg_cost)
        
        assert position.symbol == symbol
        assert position.quantity == quantity
        assert position.avg_cost == avg_cost
        assert position.last_price == Decimal("0")
        assert position.market_value == Decimal("0")
        assert position.unrealized_pnl == Decimal("0")
        assert position.realized_pnl == Decimal("0")
    
    def test_update_price(self):
        """测试更新价格"""
        position = Position("000001.SZ", Decimal("1000"), Decimal("10.50"))
        new_price = Decimal("11.50")
        
        position.update_market_value(new_price)
        
        assert position.last_price == new_price
        assert position.market_value == Decimal("1000") * new_price
        assert position.unrealized_pnl == (new_price - Decimal("10.50")) * Decimal("1000")
    
    def test_add_position(self):
        """测试增加持仓"""
        # 由于Position类没有add_position方法，我们测试通过交易增加持仓
        portfolio = MultiModelPortfolio()
        model_id = "test_model"
        portfolio.create_account(model_id, Decimal("1000000"))
        
        # 第一次买入
        portfolio.execute_trade(
            model_id=model_id,
            symbol="000001.SZ",
            quantity=Decimal("1000"),
            price=Decimal("10.50"),
            is_buy=True
        )
        
        # 第二次买入
        portfolio.execute_trade(
            model_id=model_id,
            symbol="000001.SZ",
            quantity=Decimal("500"),
            price=Decimal("11.00"),
            is_buy=True
        )
        
        account = portfolio.get_account(model_id)
        position = account.positions["000001.SZ"]
        
        # 验证数量和平均成本
        assert position.quantity == Decimal("1500")
        expected_avg_cost = (Decimal("1000") * Decimal("10.50") + Decimal("500") * Decimal("11.00")) / Decimal("1500")
        assert abs(position.avg_cost - expected_avg_cost) < Decimal("0.01")
    
    def test_reduce_position(self):
        """测试减少持仓"""
        # 由于Position类没有reduce_position方法，我们测试通过交易减少持仓
        portfolio = MultiModelPortfolio()
        model_id = "test_model"
        portfolio.create_account(model_id, Decimal("1000000"))
        
        # 先买入
        portfolio.execute_trade(
            model_id=model_id,
            symbol="000001.SZ",
            quantity=Decimal("1000"),
            price=Decimal("10.50"),
            is_buy=True
        )
        
        # 再卖出部分
        portfolio.execute_trade(
            model_id=model_id,
            symbol="000001.SZ",
            quantity=Decimal("300"),
            price=Decimal("11.00"),
            is_buy=False
        )
        
        account = portfolio.get_account(model_id)
        position = account.positions["000001.SZ"]
        
        # 验证剩余数量
        assert position.quantity == Decimal("700")
        # 平均成本应该保持不变
        assert position.avg_cost == Decimal("10.50")


class TestFeeConfig:
    """费率配置测试类"""
    
    def test_default_fee_config(self):
        """测试默认费率配置"""
        config = FeeConfig()
        
        assert config.commission_rate == Decimal("0.0003")  # 万分之三
        assert config.stamp_tax_rate == Decimal("0.001")    # 千分之一
        assert config.transfer_fee_rate == Decimal("0.00002")  # 万分之零点二
        assert config.min_commission == Decimal("5.0")
    
    def test_calculate_fees(self):
        """测试费率计算"""
        fee_config = FeeConfig()
        
        # 测试买入费用（无印花税）
        commission, stamp_tax, transfer_fee = fee_config.calculate_fees(
            amount=Decimal("10000"),
            is_sell=False
        )
        
        expected_commission = max(Decimal("10000") * Decimal("0.0003"), Decimal("5"))  # 万分之三，最低5元
        expected_transfer_fee = Decimal("10000") * Decimal("0.00002")  # 万分之零点二
        
        assert abs(commission - expected_commission) < Decimal("0.01")
        assert stamp_tax == Decimal("0")
        assert abs(transfer_fee - expected_transfer_fee) < Decimal("0.01")
        
        # 测试卖出费用（包含印花税）
        commission, stamp_tax, transfer_fee = fee_config.calculate_fees(
            amount=Decimal("10000"),
            is_sell=True
        )
        
        expected_stamp_tax = Decimal("10000") * Decimal("0.001")  # 千分之一
        
        assert abs(commission - expected_commission) < Decimal("0.01")
        assert abs(stamp_tax - expected_stamp_tax) < Decimal("0.01")
        assert abs(transfer_fee - expected_transfer_fee) < Decimal("0.01")


class TestSlippageConfig:
    """滑点配置测试类"""
    
    def test_default_slippage_config(self):
        """测试默认滑点配置"""
        config = SlippageConfig()
        
        assert config.fixed_slippage_bp == Decimal("7.5")  # 7.5bp
        assert config.liquidity_factor == Decimal("1.0")
        assert config.max_slippage_bp == Decimal("50.0")   # 50bp
    
    def test_calculate_slippage(self):
        """测试滑点计算"""
        config = SlippageConfig()
        price = Decimal("10.50")
        quantity = Decimal("1000")
        avg_volume = Decimal("100000")
        
        # 小单滑点（主要是固定滑点）
        small_slippage = config.calculate_slippage(price, quantity, avg_volume)
        expected_min_slippage = price * quantity * config.fixed_slippage_bp / Decimal("10000")
        assert small_slippage >= expected_min_slippage
        
        # 大单滑点（流动性影响）
        large_quantity = Decimal("50000")  # 50%的平均成交量
        large_slippage = config.calculate_slippage(price, large_quantity, avg_volume)
        assert large_slippage > small_slippage
        
        # 超大单滑点（达到最大滑点）
        huge_quantity = Decimal("200000")  # 200%的平均成交量
        huge_slippage = config.calculate_slippage(price, huge_quantity, avg_volume)
        max_slippage = price * huge_quantity * config.max_slippage_bp / Decimal("10000")
        assert huge_slippage <= max_slippage


class TestPerformanceAnalyzer:
    """绩效分析器测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.portfolio = MultiModelPortfolio()
        self.analyzer = PerformanceAnalyzer(self.portfolio)
        self.model_id = "test_model"
        
        # 创建测试账户
        self.portfolio.create_account(self.model_id, Decimal("1000000"))
    
    def test_calculate_model_performance(self):
        """测试计算模型绩效"""
        # 执行一些交易创建历史数据
        symbols = ["000001.SZ", "000002.SZ"]
        for i, symbol in enumerate(symbols):
            self.portfolio.execute_trade(
                model_id=self.model_id,
                symbol=symbol,
                quantity=Decimal("1000"),
                price=Decimal(f"{10 + i}.50"),
                is_buy=True
            )
        
        # 更新价格模拟盈利
        self.portfolio.update_market_prices({
            "000001.SZ": Decimal("11.50"),
            "000002.SZ": Decimal("12.50")
        })
        
        # 计算绩效指标
        metrics = self.analyzer.calculate_model_performance(self.model_id)
        
        assert metrics is not None
        assert metrics.total_return >= Decimal("0")
        assert metrics.annualized_return is not None
        assert metrics.volatility >= Decimal("0")
        assert metrics.sharpe_ratio is not None
    
    def test_calculate_attribution_analysis(self):
        """测试收益归因分析"""
        # 执行交易
        self.portfolio.execute_trade(
            model_id=self.model_id,
            symbol="000001.SZ",
            quantity=Decimal("1000"),
            price=Decimal("10.50"),
            is_buy=True
        )
        
        # 计算归因分析
        attribution = self.analyzer.calculate_attribution_analysis(self.model_id)
        
        assert attribution is not None
        assert isinstance(attribution.asset_allocation_return, Decimal)
        assert isinstance(attribution.stock_selection_return, Decimal)
        assert isinstance(attribution.sector_attribution, dict)
        assert isinstance(attribution.stock_attribution, dict)
    
    def test_calculate_risk_metrics(self):
        """测试风险指标计算"""
        # 执行交易
        self.portfolio.execute_trade(
            model_id=self.model_id,
            symbol="000001.SZ",
            quantity=Decimal("1000"),
            price=Decimal("10.50"),
            is_buy=True
        )
        
        # 计算风险指标
        risk_metrics = self.analyzer.calculate_risk_metrics(self.model_id)
        
        # 验证返回的是RiskMetrics对象
        assert hasattr(risk_metrics, 'var_95')
        assert hasattr(risk_metrics, 'var_99')
        assert hasattr(risk_metrics, 'cvar_95')
        assert hasattr(risk_metrics, 'maximum_drawdown')
        assert hasattr(risk_metrics, 'drawdown_duration')
        assert hasattr(risk_metrics, 'systematic_risk')
        assert hasattr(risk_metrics, 'idiosyncratic_risk')
        assert hasattr(risk_metrics, 'concentration_risk')
    
    def test_generate_performance_report(self):
        """测试生成绩效报告"""
        # 创建测试数据
        portfolio = MultiModelPortfolio()
        model_id = "test_model"
        portfolio.create_account(model_id, Decimal("1000000"))
        
        # 执行一些交易
        portfolio.execute_trade(model_id, "000001.SZ", Decimal("1000"), Decimal("10.00"), True)
        portfolio.execute_trade(model_id, "000002.SZ", Decimal("500"), Decimal("20.00"), True)
        
        # 更新市场价格
        portfolio.update_market_prices({
            "000001.SZ": Decimal("10.50"),
            "000002.SZ": Decimal("19.50")
        })
        
        # 创建绩效分析器
        analyzer = PerformanceAnalyzer(portfolio)
        
        # 生成绩效报告
        report = analyzer.generate_performance_report(model_id)
        
        # 验证报告结构
        assert isinstance(report, dict)
        assert "model_id" in report
        assert "performance_metrics" in report
        assert "risk_metrics" in report
        assert "attribution_analysis" in report
        assert "positions_analysis" in report
        assert "trading_analysis" in report  # 实际返回的键名
        assert report["model_id"] == model_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])