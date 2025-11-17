"""
交易执行引擎测试用例
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.trading_engine import OrderSide, OrderType, OrderStatus, TradingMode, Order, Trade
from app.services.simulation_engine import SimulationEngine
from app.services.live_trading_engine import LiveTradingEngine, BrokerConfig
from app.services.execution_optimizer import ExecutionOptimizer, AlgorithmConfig, AlgorithmType, ExecutionReport
from app.services.execution_analyzer import ExecutionAnalyzer, StressTester, MarketDataGenerator, MarketData, ExecutionMetrics


class TestSimulationEngine:
    """仿真交易引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建仿真引擎实例"""
        return SimulationEngine()
    
    @pytest.mark.asyncio
    async def test_place_order(self, engine):
        """测试下单功能"""
        from app.services.trading_engine import Order
        
        order = Order(
            order_id="",  # 空字符串，让引擎自动生成
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1000,
            price=Decimal("10.50")
        )
        
        order_id = await engine.place_order(order)
        
        assert order_id is not None
        assert len(order_id) > 0
        
        # 检查订单状态
        stored_order = await engine.get_order_status(order_id)
        assert stored_order.symbol == "000001.SZ"
        assert stored_order.side == OrderSide.BUY
        assert stored_order.quantity == 1000
        assert stored_order.price == Decimal("10.50")
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, engine):
        """测试撤单功能"""
        from app.services.trading_engine import Order
        
        # 先下单
        order = Order(
            order_id="",  # 空字符串，让引擎自动生成
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=500,
            price=Decimal("10.30")
        )
        
        order_id = await engine.place_order(order)
        
        # 撤单
        success = await engine.cancel_order(order_id)
        assert success is True
        
        # 检查订单状态
        cancelled_order = await engine.get_order_status(order_id)
        assert cancelled_order.status == OrderStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_market_order_execution(self, engine):
        """测试市价单执行"""
        from app.services.trading_engine import Order
        
        order = Order(
            order_id="",  # 空字符串，让引擎自动生成
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )
        
        order_id = await engine.place_order(order)
        
        # 等待执行
        await asyncio.sleep(0.5)  # 增加等待时间
        
        # 检查订单状态
        executed_order = await engine.get_order_status(order_id)
        assert executed_order.status in [OrderStatus.FILLED, OrderStatus.PARTIAL_FILLED, OrderStatus.SUBMITTED]
    
    @pytest.mark.asyncio
    async def test_account_info(self, engine):
        """测试账户信息查询"""
        account = await engine.get_account_info()
        
        assert account.account_id is not None
        assert account.total_value >= 0
        assert account.available_cash >= 0
    
    @pytest.mark.asyncio
    async def test_positions(self, engine):
        """测试持仓查询"""
        positions = await engine.get_positions()
        assert isinstance(positions, dict)
    
    @pytest.mark.asyncio
    async def test_stress_scenario(self, engine):
        """测试极端行情场景"""
        # 运行压力测试
        test_config = {
            "scenarios": ["price_crash", "high_volatility"],
            "duration_minutes": 1,
            "test_orders": 10
        }
        
        results = await engine.run_stress_test(test_config)
        
        assert "test_scenarios" in results
        assert len(results["test_scenarios"]) > 0
        
        # 检查测试结果
        for scenario in results["test_scenarios"]:
            assert "name" in scenario
            assert "description" in scenario


class TestLiveTradingEngine:
    """实盘交易引擎测试"""
    
    @pytest.fixture
    def broker_config(self):
        """创建券商配置"""
        return BrokerConfig(
            broker_name="huatai",
            api_url="https://api.test.com",
            account_id="test_account",
            api_key="test_key",
            api_secret="test_secret"
        )
    
    @pytest.fixture
    def engine(self, broker_config):
        """创建实盘引擎实例"""
        return LiveTradingEngine([broker_config])
    
    def test_engine_initialization(self, engine, broker_config):
        """测试引擎初始化"""
        assert engine is not None
        assert len(engine.broker_adapters) == 1
        assert "huatai" in engine.broker_adapters
        assert engine.primary_broker == "huatai"
    
    @pytest.mark.asyncio
    async def test_session_management(self, engine):
        """测试会话管理"""
        # 启动引擎会自动进行认证
        await engine.start()
        
        # 检查适配器状态
        status = engine.get_broker_status()
        assert "huatai" in status
        assert "last_heartbeat" in status["huatai"]


class TestExecutionOptimizer:
    """执行优化器测试"""
    
    @pytest.fixture
    def optimizer(self):
        """创建执行优化器实例"""
        engine = SimulationEngine()
        return ExecutionOptimizer(engine)
    
    @pytest.fixture
    def simulation_engine(self):
        return SimulationEngine()
    
    @pytest.mark.asyncio
    async def test_vwap_algorithm(self, optimizer, simulation_engine):
        """测试VWAP算法"""
        config = AlgorithmConfig(
            algorithm_type=AlgorithmType.VWAP,
            symbol="000001.SZ",
            total_quantity=Decimal("10000"),
            side=OrderSide.BUY,
            duration_minutes=60
        )
        
        # 执行算法
        algorithm_id = await optimizer.start_algorithm(config)
        assert algorithm_id is not None
        
        # 检查算法状态
        status = optimizer.get_algorithm_status(algorithm_id)
        assert status is not None
    
    @pytest.mark.asyncio
    async def test_twap_algorithm(self, optimizer, simulation_engine):
        """测试TWAP算法"""
        config = AlgorithmConfig(
            algorithm_type=AlgorithmType.TWAP,
            symbol="000001.SZ",
            total_quantity=Decimal("5000"),
            side=OrderSide.BUY,
            duration_minutes=30
        )
        
        # 执行算法
        algorithm_id = await optimizer.start_algorithm(config)
        assert algorithm_id is not None
        
        # 检查算法状态
        status = optimizer.get_algorithm_status(algorithm_id)
        assert status is not None
    
    @pytest.mark.asyncio
    async def test_smart_order_algorithm(self, optimizer, simulation_engine):
        """测试智能订单算法"""
        config = AlgorithmConfig(
            algorithm_type=AlgorithmType.SMART_ORDER,
            symbol="000001.SZ",
            total_quantity=Decimal("8000"),
            side=OrderSide.BUY,
            duration_minutes=45,
            max_order_size=Decimal("1000")
        )
        
        # 执行算法
        algorithm_id = await optimizer.start_algorithm(config)
        assert algorithm_id is not None
        
        # 检查算法状态
        status = optimizer.get_algorithm_status(algorithm_id)
        assert status is not None


class TestExecutionAnalyzer:
    """执行分析器测试"""
    
    @pytest.fixture
    def analyzer(self):
        """创建执行分析器实例"""
        return ExecutionAnalyzer()
    
    @pytest.fixture
    def market_data_generator(self):
        """创建市场数据生成器"""
        return MarketDataGenerator()
    
    def test_market_data_generation(self, market_data_generator):
        """测试市场数据生成"""
        # 生成正常市场数据
        data = market_data_generator.generate_normal_data(count=50)
        assert len(data) == 50
        assert all(isinstance(d, MarketData) for d in data)
        
        # 检查数据合理性
        for d in data:
            assert d.price > 0
            assert d.volume > 0
            assert d.bid_price <= d.ask_price
    
    def test_execution_quality_analysis(self, analyzer, market_data_generator):
        """测试执行质量分析"""
        # 生成测试数据
        market_data = market_data_generator.generate_normal_data(count=100)
        trades = [
            Trade(
                trade_id="1",
                order_id="order_1",
                symbol="000001.SZ",
                side=OrderSide.BUY,
                quantity=Decimal("500"),
                price=Decimal("10.0"),
                commission=Decimal("5.0"),
                timestamp=datetime.now()
            ),
            Trade(
                trade_id="2",
                order_id="order_2",
                symbol="000001.SZ",
                side=OrderSide.BUY,
                quantity=Decimal("500"),
                price=Decimal("10.1"),
                commission=Decimal("5.0"),
                timestamp=datetime.now()
            )
        ]
        
        # 分析执行质量
        metrics = analyzer.analyze_execution(
            ExecutionReport(
                algorithm_id="test",
                symbol="000001.SZ",
                total_quantity=Decimal("1000"),
                executed_quantity=Decimal("1000"),
                remaining_quantity=Decimal("0"),
                avg_execution_price=Decimal("10.0"),
                vwap_benchmark=None,
                slippage_bps=0.0,
                participation_rate=0.1,
                execution_time=timedelta(minutes=30),
                orders=[],
                trades=trades,
                status="completed",
                created_at=datetime.now()
            ),
            market_data
        )
        assert isinstance(metrics, ExecutionMetrics)
        assert metrics.total_quantity == Decimal("1000")
        assert metrics.executed_quantity == Decimal("1000")


class TestStressTester:
    """压力测试器测试"""
    
    @pytest.fixture
    def stress_tester(self):
        """创建压力测试器实例"""
        return StressTester()
    
    @pytest.fixture
    def simulation_engine(self):
        """创建仿真引擎"""
        return SimulationEngine()
    
    def test_scenario_creation(self, stress_tester):
        """测试压力测试场景创建"""
        scenarios = stress_tester.create_stress_scenarios()
        assert len(scenarios) > 0
        
        # 检查场景属性
        for scenario in scenarios:
            assert hasattr(scenario, 'name')
            assert hasattr(scenario, 'description')
            assert hasattr(scenario, 'market_regime')
            assert scenario.price_volatility >= 0
            assert 0 <= scenario.liquidity_reduction <= 1
    
    @pytest.mark.asyncio
    async def test_stress_test_execution(self, stress_tester, simulation_engine):
        """测试压力测试执行"""
        # 创建测试场景
        scenarios = stress_tester.create_stress_scenarios()
        scenario = scenarios[0]  # 使用第一个场景
        
        # 创建算法配置
        from app.services.execution_optimizer import AlgorithmConfig, AlgorithmType
        config = AlgorithmConfig(
            algorithm_type=AlgorithmType.VWAP,
            symbol="000001.SZ",
            total_quantity=Decimal('1000'),
            side=OrderSide.BUY,
            duration_minutes=30
        )
        
        # 运行压力测试
        result = await stress_tester.run_stress_test(scenario, config)
        
        # 验证结果
        assert 'scenario' in result
        assert 'execution_metrics' in result
        assert 'risk_assessment' in result


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_trading_workflow(self):
        """测试完整交易流程"""
        from app.services.trading_engine import Order
        
        # 初始化引擎
        engine = SimulationEngine()
        await engine.start()
        
        # 下单
        order = Order(
            order_id="",  # 空字符串，让引擎自动生成
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1000,
            price=Decimal("10.50")
        )
        
        order_id = await engine.place_order(order)
        assert order_id is not None
        
        # 算法交易执行
        optimizer = ExecutionOptimizer(engine)
        config = AlgorithmConfig(
            algorithm_type=AlgorithmType.VWAP,
            symbol="000001.SZ",
            side=OrderSide.BUY,
            total_quantity=Decimal("5000"),
            max_order_size=Decimal("500"),
            duration_minutes=30,
            max_participation_rate=0.2
        )
        
        algorithm_id = await optimizer.start_algorithm(config)
        assert algorithm_id is not None
        
        # 等待一段时间
        await asyncio.sleep(0.5)
        
        # 执行质量分析
        analyzer = ExecutionAnalyzer()
        generator = MarketDataGenerator()
        
        # 生成测试数据
        market_data = generator.generate_normal_data(count=100)
        trades = [
            Trade(
                trade_id="trade_001",
                order_id="order_001",
                symbol="000001.SZ",
                side=OrderSide.BUY,
                quantity=Decimal('100'),
                price=Decimal('10.50'),
                commission=Decimal('1.00'),
                timestamp=datetime.now()
            )
        ]
        
        # 分析执行质量
        metrics = analyzer.analyze_execution(
            ExecutionReport(
                algorithm_id="test",
                symbol="000001.SZ",
                total_quantity=Decimal("1000"),
                executed_quantity=Decimal("1000"),
                remaining_quantity=Decimal("0"),
                avg_execution_price=Decimal("10.0"),
                vwap_benchmark=None,
                slippage_bps=0.0,
                participation_rate=0.1,
                execution_time=timedelta(minutes=30),
                orders=[],
                trades=trades,
                status="completed",
                created_at=datetime.now()
            ),
            market_data
        )
        assert isinstance(metrics, ExecutionMetrics)
        assert metrics.total_quantity == Decimal("1000")
        assert metrics.executed_quantity == Decimal("1000")
        
        # 检查账户状态
        account_info = await engine.get_account_info()
        assert account_info.total_value > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])