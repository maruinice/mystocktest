"""
风控系统测试用例

覆盖所有风控规则和紧急干预场景的测试
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.risk_control import (
    RiskControlSystem, RiskConfig, PreTradeRiskControl, InTradeRiskControl,
    PostTradeRiskControl, EmergencyControl, RiskLevel, RiskType, RiskAlert
)


class TestRiskConfig:
    """风控配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = RiskConfig()
        
        assert config.max_single_position_ratio == Decimal("0.20")
        assert config.max_total_positions == 5
        assert config.max_industry_concentration == Decimal("0.40")
        assert config.max_daily_trades == 10
        assert config.min_trade_interval == 300
        assert config.price_deviation_threshold == Decimal("0.05")
        assert config.liquidity_threshold == Decimal("1000000")
        assert config.market_impact_threshold == Decimal("0.02")
        assert config.max_daily_loss == Decimal("0.05")
        assert config.max_total_loss == Decimal("0.20")
        assert config.stop_loss_ratio == Decimal("0.10")
        assert config.take_profit_ratio == Decimal("0.20")
        assert config.var_confidence == Decimal("0.95")
        assert config.var_threshold == Decimal("0.03")
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = RiskConfig(
            max_single_position_ratio=Decimal("0.15"),
            max_total_positions=3,
            max_daily_trades=5
        )
        
        assert config.max_single_position_ratio == Decimal("0.15")
        assert config.max_total_positions == 3
        assert config.max_daily_trades == 5


class TestPreTradeRiskControl:
    """事前风控测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = RiskConfig()
        self.pre_control = PreTradeRiskControl(self.config)
        self.model_id = "test_model"
        
        # 模拟投资组合数据
        self.portfolio_data = {
            'accounts': {
                self.model_id: {
                    'total_assets': 100000,
                    'cash_balance': 50000,
                    'positions': {
                        '000001': {
                            'quantity': 1000,
                            'avg_cost': 10.0,
                            'market_value': 12000,
                            'last_price': 12.0
                        }
                    }
                }
            }
        }
    
    def test_position_limit_check_pass(self):
        """测试单票仓位限制检查通过"""
        result = self.pre_control.check_trade_risk(
            model_id=self.model_id,
            symbol="000002",
            quantity=Decimal("500"),
            price=Decimal("20.0"),
            side="buy",
            portfolio_data=self.portfolio_data
        )
        
        assert result.is_allowed is True
        assert len(result.risk_alerts) == 0
    
    def test_position_limit_check_fail(self):
        """测试单票仓位限制检查失败"""
        result = self.pre_control.check_trade_risk(
            model_id=self.model_id,
            symbol="000002",
            quantity=Decimal("2000"),
            price=Decimal("20.0"),
            side="buy",
            portfolio_data=self.portfolio_data
        )
        
        assert result.is_allowed is False
        assert len(result.risk_alerts) > 0
        assert result.risk_alerts[0].risk_type == RiskType.POSITION_LIMIT
    
    def test_total_positions_limit_check(self):
        """测试总持仓限制检查"""
        # 添加更多持仓到达限制
        for i in range(2, 7):  # 添加5个持仓
            self.portfolio_data['accounts'][self.model_id]['positions'][f'00000{i}'] = {
                'quantity': 100,
                'avg_cost': 10.0,
                'market_value': 1000,
                'last_price': 10.0
            }
        
        result = self.pre_control.check_trade_risk(
            model_id=self.model_id,
            symbol="000007",  # 新股票
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            side="buy",
            portfolio_data=self.portfolio_data
        )
        
        assert result.is_allowed is False
        assert any(alert.risk_type == RiskType.CONCENTRATION for alert in result.risk_alerts)
    
    def test_industry_concentration_check(self):
        """测试行业集中度检查"""
        # 添加同行业股票（前缀相同）
        self.portfolio_data['accounts'][self.model_id]['positions']['000002'] = {
            'quantity': 1000,
            'avg_cost': 15.0,
            'market_value': 18000,
            'last_price': 18.0
        }
        self.portfolio_data['accounts'][self.model_id]['positions']['000003'] = {
            'quantity': 500,
            'avg_cost': 20.0,
            'market_value': 12000,
            'last_price': 24.0
        }
        
        result = self.pre_control.check_trade_risk(
            model_id=self.model_id,
            symbol="000004",  # 同行业新股票
            quantity=Decimal("1000"),
            price=Decimal("15.0"),
            side="buy",
            portfolio_data=self.portfolio_data
        )
        
        # 检查是否有行业集中度预警
        concentration_alerts = [alert for alert in result.risk_alerts 
                              if alert.risk_type == RiskType.CONCENTRATION]
        assert len(concentration_alerts) > 0
    
    def test_trading_frequency_check(self):
        """测试交易频率检查"""
        # 模拟达到日交易次数限制
        for _ in range(self.config.max_daily_trades):
            self.pre_control.record_trade(self.model_id)
        
        result = self.pre_control.check_trade_risk(
            model_id=self.model_id,
            symbol="000002",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            side="buy",
            portfolio_data=self.portfolio_data
        )
        
        assert result.is_allowed is False
        assert any(alert.risk_type == RiskType.FREQUENCY for alert in result.risk_alerts)
    
    def test_trading_interval_check(self):
        """测试交易间隔检查"""
        # 记录一次交易
        self.pre_control.record_trade(self.model_id)
        
        result = self.pre_control.check_trade_risk(
            model_id=self.model_id,
            symbol="000002",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            side="buy",
            portfolio_data=self.portfolio_data
        )
        
        # 应该有交易间隔预警
        frequency_alerts = [alert for alert in result.risk_alerts 
                          if alert.risk_type == RiskType.FREQUENCY]
        assert len(frequency_alerts) > 0


class TestInTradeRiskControl:
    """事中风控测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = RiskConfig()
        self.in_control = InTradeRiskControl(self.config)
    
    def test_price_deviation_monitor_normal(self):
        """测试价格偏离监控正常情况"""
        alert = self.in_control.monitor_price_deviation(
            symbol="000001",
            expected_price=Decimal("10.0"),
            current_price=Decimal("10.2")
        )
        
        assert alert is None
    
    def test_price_deviation_monitor_alert(self):
        """测试价格偏离监控预警"""
        alert = self.in_control.monitor_price_deviation(
            symbol="000001",
            expected_price=Decimal("10.0"),
            current_price=Decimal("11.0")
        )
        
        assert alert is not None
        assert alert.risk_type == RiskType.MARKET_IMPACT
        assert alert.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
    
    def test_liquidity_check_normal(self):
        """测试流动性检查正常情况"""
        alert = self.in_control.check_liquidity(
            symbol="000001",
            volume=Decimal("1000"),
            avg_volume=Decimal("2000000")
        )
        
        assert alert is None
    
    def test_liquidity_check_alert(self):
        """测试流动性检查预警"""
        alert = self.in_control.check_liquidity(
            symbol="000001",
            volume=Decimal("1000"),
            avg_volume=Decimal("500000")
        )
        
        assert alert is not None
        assert alert.risk_type == RiskType.LIQUIDITY
        assert alert.risk_level == RiskLevel.MEDIUM
    
    def test_market_impact_assessment_normal(self):
        """测试市场冲击评估正常情况"""
        alert = self.in_control.assess_market_impact(
            symbol="000001",
            trade_volume=Decimal("1000"),
            market_volume=Decimal("100000")
        )
        
        assert alert is None
    
    def test_market_impact_assessment_alert(self):
        """测试市场冲击评估预警"""
        alert = self.in_control.assess_market_impact(
            symbol="000001",
            trade_volume=Decimal("5000"),
            market_volume=Decimal("100000")
        )
        
        assert alert is not None
        assert alert.risk_type == RiskType.MARKET_IMPACT
        assert alert.risk_level == RiskLevel.MEDIUM


class TestPostTradeRiskControl:
    """事后风控测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = RiskConfig()
        self.post_control = PostTradeRiskControl(self.config)
        self.model_id = "test_model"
    
    def test_pnl_monitor_normal(self):
        """测试盈亏监控正常情况"""
        portfolio_data = {
            'accounts': {
                self.model_id: {
                    'total_assets': 100000,
                    'daily_pnl': 1000,
                    'total_pnl': 5000
                }
            }
        }
        
        alerts = self.post_control.monitor_pnl(self.model_id, portfolio_data)
        assert len(alerts) == 0
    
    def test_pnl_monitor_daily_loss_alert(self):
        """测试日损失预警"""
        portfolio_data = {
            'accounts': {
                self.model_id: {
                    'total_assets': 100000,
                    'daily_pnl': -6000,  # 6%日损失
                    'total_pnl': -6000
                }
            }
        }
        
        alerts = self.post_control.monitor_pnl(self.model_id, portfolio_data)
        assert len(alerts) > 0
        assert alerts[0].risk_type == RiskType.PNL
        assert alerts[0].risk_level == RiskLevel.HIGH
    
    def test_pnl_monitor_total_loss_alert(self):
        """测试总损失预警"""
        portfolio_data = {
            'accounts': {
                self.model_id: {
                    'total_assets': 100000,
                    'daily_pnl': -1000,
                    'total_pnl': -25000  # 25%总损失
                }
            }
        }
        
        alerts = self.post_control.monitor_pnl(self.model_id, portfolio_data)
        assert len(alerts) > 0
        assert any(alert.risk_level == RiskLevel.CRITICAL for alert in alerts)
    
    def test_stop_loss_check(self):
        """测试止损检查"""
        portfolio_data = {
            'accounts': {
                self.model_id: {
                    'positions': {
                        '000001': {
                            'quantity': 1000,
                            'avg_cost': 10.0,
                            'last_price': 8.5  # 15%亏损，触发止损
                        }
                    }
                }
            }
        }
        
        alerts = self.post_control.check_stop_loss_take_profit(self.model_id, portfolio_data)
        assert len(alerts) > 0
        assert alerts[0].risk_type == RiskType.PNL
        assert alerts[0].risk_level == RiskLevel.HIGH
        assert "止损" in alerts[0].message
    
    def test_take_profit_check(self):
        """测试止盈检查"""
        portfolio_data = {
            'accounts': {
                self.model_id: {
                    'positions': {
                        '000001': {
                            'quantity': 1000,
                            'avg_cost': 10.0,
                            'last_price': 12.5  # 25%盈利，触发止盈
                        }
                    }
                }
            }
        }
        
        alerts = self.post_control.check_stop_loss_take_profit(self.model_id, portfolio_data)
        assert len(alerts) > 0
        assert alerts[0].risk_type == RiskType.PNL
        assert alerts[0].risk_level == RiskLevel.MEDIUM
        assert "止盈" in alerts[0].message
    
    def test_var_calculation(self):
        """测试VaR计算"""
        returns = [Decimal(str(x)) for x in [-0.05, -0.03, -0.01, 0.01, 0.02, 0.03, -0.02, -0.04]]
        var = self.post_control.calculate_var(returns)
        
        assert var > 0
        assert isinstance(var, Decimal)
    
    def test_var_calculation_empty_returns(self):
        """测试空收益率列表的VaR计算"""
        var = self.post_control.calculate_var([])
        assert var == Decimal('0')


class TestEmergencyControl:
    """紧急干预测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.emergency_control = EmergencyControl()
        self.model_id = "test_model"
    
    def test_force_close_position(self):
        """测试强制平仓"""
        result = self.emergency_control.force_close_position(
            self.model_id, "000001", "测试强制平仓"
        )
        assert result is True
    
    def test_suspend_model_trading(self):
        """测试暂停模型交易"""
        result = self.emergency_control.suspend_model_trading(
            self.model_id, "测试暂停"
        )
        assert result is True
        assert self.emergency_control.is_model_suspended(self.model_id) is True
    
    def test_resume_model_trading(self):
        """测试恢复模型交易"""
        # 先暂停
        self.emergency_control.suspend_model_trading(self.model_id, "测试")
        
        # 再恢复
        result = self.emergency_control.resume_model_trading(self.model_id)
        assert result is True
        assert self.emergency_control.is_model_suspended(self.model_id) is False
    
    def test_emergency_stop_all(self):
        """测试系统紧急停止"""
        result = self.emergency_control.emergency_stop_all("测试紧急停止")
        assert result is True
        assert self.emergency_control.is_system_emergency_stopped() is True
    
    def test_is_model_suspended_false(self):
        """测试模型未暂停状态"""
        assert self.emergency_control.is_model_suspended("unknown_model") is False
    
    def test_is_system_emergency_stopped_false(self):
        """测试系统未紧急停止状态"""
        assert self.emergency_control.is_system_emergency_stopped() is False


class TestRiskControlSystem:
    """风控系统集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.risk_system = RiskControlSystem()
        self.model_id = "test_model"
        
        # 模拟投资组合数据
        self.portfolio_data = {
            'accounts': {
                self.model_id: {
                    'total_assets': 100000,
                    'cash_balance': 50000,
                    'daily_pnl': 0,
                    'total_pnl': 0,
                    'positions': {
                        '000001': {
                            'quantity': 1000,
                            'avg_cost': 10.0,
                            'market_value': 12000,
                            'last_price': 12.0
                        }
                    }
                }
            }
        }
    
    def test_check_pre_trade_risk_normal(self):
        """测试事前风控检查正常情况"""
        result = self.risk_system.check_pre_trade_risk(
            model_id=self.model_id,
            symbol="000002",
            quantity=Decimal("500"),
            price=Decimal("10.0"),
            side="buy",
            portfolio_data=self.portfolio_data
        )
        
        assert result.is_allowed is True
        assert len(result.risk_alerts) == 0
    
    def test_check_pre_trade_risk_system_stopped(self):
        """测试系统紧急停止时的事前风控"""
        self.risk_system.emergency_control.emergency_stop_all("测试")
        
        result = self.risk_system.check_pre_trade_risk(
            model_id=self.model_id,
            symbol="000002",
            quantity=Decimal("500"),
            price=Decimal("10.0"),
            side="buy",
            portfolio_data=self.portfolio_data
        )
        
        assert result.is_allowed is False
        assert "系统紧急停止" in result.reason
    
    def test_check_pre_trade_risk_model_suspended(self):
        """测试模型暂停时的事前风控"""
        self.risk_system.emergency_control.suspend_model_trading(self.model_id, "测试")
        
        result = self.risk_system.check_pre_trade_risk(
            model_id=self.model_id,
            symbol="000002",
            quantity=Decimal("500"),
            price=Decimal("10.0"),
            side="buy",
            portfolio_data=self.portfolio_data
        )
        
        assert result.is_allowed is False
        assert "模型交易已暂停" in result.reason
    
    def test_monitor_in_trade_risk(self):
        """测试事中风控监控"""
        alerts = self.risk_system.monitor_in_trade_risk(
            symbol="000001",
            expected_price=Decimal("10.0"),
            current_price=Decimal("11.0"),  # 10%偏离
            volume=Decimal("1000"),
            avg_volume=Decimal("2000000"),
            market_volume=Decimal("100000")
        )
        
        assert len(alerts) > 0
        assert any(alert.risk_type == RiskType.MARKET_IMPACT for alert in alerts)
    
    def test_monitor_post_trade_risk_normal(self):
        """测试事后风控监控正常情况"""
        # 调整价格避免触发止盈条件（10%涨幅，未达到20%止盈阈值）
        self.portfolio_data['accounts'][self.model_id]['positions']['000001']['last_price'] = 11.0
        self.portfolio_data['accounts'][self.model_id]['positions']['000001']['market_value'] = 11000
        
        alerts = self.risk_system.monitor_post_trade_risk(
            self.model_id, self.portfolio_data
        )
        
        assert len(alerts) == 0
    
    def test_monitor_post_trade_risk_with_loss(self):
        """测试事后风控监控亏损情况"""
        # 设置亏损数据
        self.portfolio_data['accounts'][self.model_id]['daily_pnl'] = -6000
        self.portfolio_data['accounts'][self.model_id]['total_pnl'] = -6000
        
        alerts = self.risk_system.monitor_post_trade_risk(
            self.model_id, self.portfolio_data
        )
        
        assert len(alerts) > 0
        assert any(alert.risk_type == RiskType.PNL for alert in alerts)
    
    def test_monitor_post_trade_risk_auto_suspend(self):
        """测试事后风控自动暂停"""
        # 设置严重亏损数据
        self.portfolio_data['accounts'][self.model_id]['total_pnl'] = -25000
        
        alerts = self.risk_system.monitor_post_trade_risk(
            self.model_id, self.portfolio_data
        )
        
        # 检查是否自动暂停了模型交易
        assert self.risk_system.emergency_control.is_model_suspended(self.model_id)
    
    def test_get_risk_summary(self):
        """测试获取风险摘要"""
        # 添加一些风险预警
        alert = RiskAlert(
            risk_type=RiskType.POSITION_LIMIT,
            risk_level=RiskLevel.HIGH,
            message="测试预警",
            timestamp=datetime.now(),
            model_id=self.model_id
        )
        self.risk_system.risk_alerts.append(alert)
        
        summary = self.risk_system.get_risk_summary()
        
        assert summary['total_alerts'] == 1
        assert summary['risk_level_counts']['high'] == 1
        assert summary['risk_type_counts']['position_limit'] == 1
        assert len(summary['recent_alerts']) == 1
    
    def test_get_risk_summary_filtered(self):
        """测试获取特定模型的风险摘要"""
        # 添加不同模型的预警
        alert1 = RiskAlert(
            risk_type=RiskType.POSITION_LIMIT,
            risk_level=RiskLevel.HIGH,
            message="模型1预警",
            timestamp=datetime.now(),
            model_id=self.model_id
        )
        alert2 = RiskAlert(
            risk_type=RiskType.FREQUENCY,
            risk_level=RiskLevel.MEDIUM,
            message="模型2预警",
            timestamp=datetime.now(),
            model_id="other_model"
        )
        
        self.risk_system.risk_alerts.extend([alert1, alert2])
        
        summary = self.risk_system.get_risk_summary(self.model_id)
        
        assert summary['total_alerts'] == 1
        assert summary['recent_alerts'][0].model_id == self.model_id
    
    def test_clear_old_alerts(self):
        """测试清理历史预警"""
        # 添加新旧预警
        old_alert = RiskAlert(
            risk_type=RiskType.POSITION_LIMIT,
            risk_level=RiskLevel.HIGH,
            message="旧预警",
            timestamp=datetime.now() - timedelta(hours=25),
            model_id=self.model_id
        )
        new_alert = RiskAlert(
            risk_type=RiskType.FREQUENCY,
            risk_level=RiskLevel.MEDIUM,
            message="新预警",
            timestamp=datetime.now(),
            model_id=self.model_id
        )
        
        self.risk_system.risk_alerts.extend([old_alert, new_alert])
        
        # 清理24小时前的预警
        self.risk_system.clear_old_alerts(24)
        
        assert len(self.risk_system.risk_alerts) == 1
        assert self.risk_system.risk_alerts[0].message == "新预警"


class TestRiskAlert:
    """风险预警测试"""
    
    def test_risk_alert_creation(self):
        """测试风险预警创建"""
        alert = RiskAlert(
            risk_type=RiskType.POSITION_LIMIT,
            risk_level=RiskLevel.HIGH,
            message="测试预警",
            timestamp=datetime.now(),
            model_id="test_model",
            symbol="000001",
            current_value=Decimal("0.25"),
            threshold_value=Decimal("0.20"),
            suggested_action="减少仓位"
        )
        
        assert alert.risk_type == RiskType.POSITION_LIMIT
        assert alert.risk_level == RiskLevel.HIGH
        assert alert.message == "测试预警"
        assert alert.model_id == "test_model"
        assert alert.symbol == "000001"
        assert alert.current_value == Decimal("0.25")
        assert alert.threshold_value == Decimal("0.20")
        assert alert.suggested_action == "减少仓位"


if __name__ == "__main__":
    pytest.main([__file__])