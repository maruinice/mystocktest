"""
绩效分析模块

实现多模型投资组合的绩效分析功能：
- 实时市值计算
- 收益归因分析
- 风险指标计算
- 基准对比分析
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import math
import numpy as np
from collections import defaultdict
import logging

from .multi_model_portfolio import MultiModelPortfolio, ModelAccount, Transaction, Position

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """绩效指标"""
    # 收益指标
    total_return: Decimal
    annualized_return: Decimal
    daily_return: Decimal
    
    # 风险指标
    volatility: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    
    # 其他指标
    win_rate: Decimal
    profit_loss_ratio: Decimal
    calmar_ratio: Decimal
    
    # 基准对比
    alpha: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    information_ratio: Optional[Decimal] = None
    tracking_error: Optional[Decimal] = None


@dataclass
class AttributionAnalysis:
    """收益归因分析"""
    # 资产配置归因
    asset_allocation_return: Decimal
    stock_selection_return: Decimal
    interaction_return: Decimal
    
    # 行业归因
    sector_attribution: Dict[str, Decimal]
    
    # 个股归因
    stock_attribution: Dict[str, Decimal]
    
    # 时间归因
    timing_attribution: Decimal


@dataclass
class RiskMetrics:
    """风险指标"""
    var_95: Decimal  # 95% VaR
    var_99: Decimal  # 99% VaR
    cvar_95: Decimal  # 95% CVaR
    maximum_drawdown: Decimal
    drawdown_duration: int  # 最大回撤持续天数
    
    # 风险分解
    systematic_risk: Decimal
    idiosyncratic_risk: Decimal
    concentration_risk: Decimal


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self, portfolio: MultiModelPortfolio):
        self.portfolio = portfolio
        self.risk_free_rate = Decimal('0.03')  # 无风险利率3%
        
    def calculate_model_performance(self, model_id: str, 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> PerformanceMetrics:
        """计算单个模型的绩效指标"""
        account = self.portfolio.get_account(model_id)
        if not account:
            raise ValueError(f"账户不存在: {model_id}")
        
        # 获取交易历史
        transactions = self._filter_transactions_by_date(
            account.transactions, start_date, end_date
        )
        
        if not transactions:
            return self._create_empty_metrics()
        
        # 计算日收益率序列
        daily_returns = self._calculate_daily_returns(account, transactions, start_date, end_date)
        
        if not daily_returns:
            return self._create_empty_metrics()
        
        # 计算各项指标
        total_return = account.get_return_rate()
        annualized_return = self._calculate_annualized_return(daily_returns)
        volatility = self._calculate_volatility(daily_returns)
        max_drawdown = self._calculate_max_drawdown(daily_returns)
        sharpe_ratio = self._calculate_sharpe_ratio(annualized_return, volatility)
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        win_rate = self._calculate_win_rate(daily_returns)
        profit_loss_ratio = self._calculate_profit_loss_ratio(daily_returns)
        calmar_ratio = self._calculate_calmar_ratio(annualized_return, max_drawdown)
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            daily_return=daily_returns[-1] if daily_returns else Decimal('0'),
            volatility=volatility,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            calmar_ratio=calmar_ratio
        )
    
    def calculate_attribution_analysis(self, model_id: str,
                                     benchmark_weights: Optional[Dict[str, Decimal]] = None,
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None) -> AttributionAnalysis:
        """计算收益归因分析"""
        account = self.portfolio.get_account(model_id)
        if not account:
            raise ValueError(f"账户不存在: {model_id}")
        
        # 获取持仓权重
        portfolio_weights = self._calculate_portfolio_weights(account)
        
        # 如果没有提供基准权重，使用等权重基准
        if benchmark_weights is None:
            symbols = list(portfolio_weights.keys())
            benchmark_weights = {symbol: Decimal('1') / len(symbols) for symbol in symbols}
        
        # 计算个股收益率
        stock_returns = self._calculate_stock_returns(account, start_date, end_date)
        
        # 资产配置归因 (Brinson归因模型)
        asset_allocation_return = Decimal('0')
        stock_selection_return = Decimal('0')
        interaction_return = Decimal('0')
        
        benchmark_return = Decimal('0')
        portfolio_return = Decimal('0')
        
        for symbol in set(list(portfolio_weights.keys()) + list(benchmark_weights.keys())):
            wp = portfolio_weights.get(symbol, Decimal('0'))  # 组合权重
            wb = benchmark_weights.get(symbol, Decimal('0'))  # 基准权重
            rs = stock_returns.get(symbol, Decimal('0'))      # 个股收益率
            rb = stock_returns.get(symbol, Decimal('0'))      # 基准中该股收益率
            
            # 资产配置效应
            asset_allocation_return += (wp - wb) * rb
            
            # 个股选择效应
            stock_selection_return += wb * (rs - rb)
            
            # 交互效应
            interaction_return += (wp - wb) * (rs - rb)
            
            benchmark_return += wb * rb
            portfolio_return += wp * rs
        
        # 行业归因（简化版，按股票代码前缀分类）
        sector_attribution = self._calculate_sector_attribution(
            portfolio_weights, benchmark_weights, stock_returns
        )
        
        # 个股归因
        stock_attribution = {}
        for symbol, weight in portfolio_weights.items():
            stock_return = stock_returns.get(symbol, Decimal('0'))
            stock_attribution[symbol] = weight * stock_return
        
        # 时间归因（简化为0，实际需要更复杂的计算）
        timing_attribution = Decimal('0')
        
        return AttributionAnalysis(
            asset_allocation_return=asset_allocation_return,
            stock_selection_return=stock_selection_return,
            interaction_return=interaction_return,
            sector_attribution=sector_attribution,
            stock_attribution=stock_attribution,
            timing_attribution=timing_attribution
        )
    
    def calculate_risk_metrics(self, model_id: str,
                             confidence_level: Decimal = Decimal('0.95'),
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> RiskMetrics:
        """计算风险指标"""
        account = self.portfolio.get_account(model_id)
        if not account:
            raise ValueError(f"账户不存在: {model_id}")
        
        # 获取日收益率序列
        transactions = self._filter_transactions_by_date(
            account.transactions, start_date, end_date
        )
        daily_returns = self._calculate_daily_returns(account, transactions, start_date, end_date)
        
        if not daily_returns:
            return self._create_empty_risk_metrics()
        
        # 计算VaR
        var_95 = self._calculate_var(daily_returns, Decimal('0.95'))
        var_99 = self._calculate_var(daily_returns, Decimal('0.99'))
        
        # 计算CVaR
        cvar_95 = self._calculate_cvar(daily_returns, Decimal('0.95'))
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(daily_returns)
        drawdown_duration = self._calculate_drawdown_duration(daily_returns)
        
        # 风险分解（简化版）
        portfolio_variance = self._calculate_portfolio_variance(account)
        systematic_risk = portfolio_variance * Decimal('0.7')  # 假设70%为系统性风险
        idiosyncratic_risk = portfolio_variance * Decimal('0.3')  # 30%为特异性风险
        concentration_risk = self._calculate_concentration_risk(account)
        
        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            maximum_drawdown=max_drawdown,
            drawdown_duration=drawdown_duration,
            systematic_risk=systematic_risk,
            idiosyncratic_risk=idiosyncratic_risk,
            concentration_risk=concentration_risk
        )
    
    def compare_with_benchmark(self, model_id: str, 
                             benchmark_returns: List[Decimal],
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> PerformanceMetrics:
        """与基准对比分析"""
        # 获取模型绩效
        model_metrics = self.calculate_model_performance(model_id, start_date, end_date)
        
        account = self.portfolio.get_account(model_id)
        if not account:
            return model_metrics
        
        # 获取模型收益率序列
        transactions = self._filter_transactions_by_date(
            account.transactions, start_date, end_date
        )
        model_returns = self._calculate_daily_returns(account, transactions, start_date, end_date)
        
        if not model_returns or not benchmark_returns:
            return model_metrics
        
        # 确保两个序列长度一致
        min_length = min(len(model_returns), len(benchmark_returns))
        model_returns = model_returns[-min_length:]
        benchmark_returns = benchmark_returns[-min_length:]
        
        # 计算Alpha和Beta
        alpha, beta = self._calculate_alpha_beta(model_returns, benchmark_returns)
        
        # 计算信息比率和跟踪误差
        tracking_error = self._calculate_tracking_error(model_returns, benchmark_returns)
        information_ratio = self._calculate_information_ratio(
            model_returns, benchmark_returns, tracking_error
        )
        
        # 更新绩效指标
        model_metrics.alpha = alpha
        model_metrics.beta = beta
        model_metrics.information_ratio = information_ratio
        model_metrics.tracking_error = tracking_error
        
        return model_metrics
    
    def generate_performance_report(self, model_id: str,
                                  benchmark_returns: Optional[List[Decimal]] = None,
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """生成综合绩效报告"""
        account = self.portfolio.get_account(model_id)
        if not account:
            return {"error": f"账户不存在: {model_id}"}
        
        # 基础绩效指标
        performance_metrics = self.calculate_model_performance(model_id, start_date, end_date)
        
        # 收益归因分析
        attribution_analysis = self.calculate_attribution_analysis(model_id, None, start_date, end_date)
        
        # 风险指标
        risk_metrics = self.calculate_risk_metrics(model_id, Decimal('0.95'), start_date, end_date)
        
        # 基准对比（如果提供）
        if benchmark_returns:
            performance_metrics = self.compare_with_benchmark(
                model_id, benchmark_returns, start_date, end_date
            )
        
        # 持仓分析
        positions_analysis = self._analyze_positions(account)
        
        # 交易分析
        trading_analysis = self._analyze_trading_behavior(account, start_date, end_date)
        
        report = {
            "model_id": model_id,
            "report_date": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "performance_metrics": {
                "total_return": float(performance_metrics.total_return),
                "annualized_return": float(performance_metrics.annualized_return),
                "volatility": float(performance_metrics.volatility),
                "max_drawdown": float(performance_metrics.max_drawdown),
                "sharpe_ratio": float(performance_metrics.sharpe_ratio),
                "sortino_ratio": float(performance_metrics.sortino_ratio),
                "win_rate": float(performance_metrics.win_rate),
                "calmar_ratio": float(performance_metrics.calmar_ratio),
                "alpha": float(performance_metrics.alpha) if performance_metrics.alpha else None,
                "beta": float(performance_metrics.beta) if performance_metrics.beta else None,
                "information_ratio": float(performance_metrics.information_ratio) if performance_metrics.information_ratio else None
            },
            "attribution_analysis": {
                "asset_allocation_return": float(attribution_analysis.asset_allocation_return),
                "stock_selection_return": float(attribution_analysis.stock_selection_return),
                "interaction_return": float(attribution_analysis.interaction_return),
                "sector_attribution": {k: float(v) for k, v in attribution_analysis.sector_attribution.items()},
                "stock_attribution": {k: float(v) for k, v in attribution_analysis.stock_attribution.items()}
            },
            "risk_metrics": {
                "var_95": float(risk_metrics.var_95),
                "var_99": float(risk_metrics.var_99),
                "cvar_95": float(risk_metrics.cvar_95),
                "maximum_drawdown": float(risk_metrics.maximum_drawdown),
                "concentration_risk": float(risk_metrics.concentration_risk)
            },
            "positions_analysis": positions_analysis,
            "trading_analysis": trading_analysis
        }
        
        return report
    
    # 私有辅助方法
    def _filter_transactions_by_date(self, transactions: List[Transaction],
                                   start_date: Optional[datetime],
                                   end_date: Optional[datetime]) -> List[Transaction]:
        """按日期过滤交易记录"""
        filtered = transactions
        
        if start_date:
            filtered = [t for t in filtered if t.timestamp >= start_date]
        
        if end_date:
            filtered = [t for t in filtered if t.timestamp <= end_date]
        
        return filtered
    
    def _calculate_daily_returns(self, account: ModelAccount, 
                               transactions: List[Transaction],
                               start_date: Optional[datetime],
                               end_date: Optional[datetime]) -> List[Decimal]:
        """计算日收益率序列"""
        if not transactions:
            return []
        
        # 简化版：基于交易计算收益率
        # 实际应用中需要基于每日净值计算
        daily_returns = []
        prev_value = account.initial_cash
        
        # 按日期分组交易
        daily_transactions = defaultdict(list)
        for transaction in transactions:
            date_key = transaction.timestamp.date()
            daily_transactions[date_key].append(transaction)
        
        # 计算每日收益率
        for date in sorted(daily_transactions.keys()):
            day_transactions = daily_transactions[date]
            
            # 计算当日净值变化
            day_pnl = Decimal('0')
            for transaction in day_transactions:
                if transaction.transaction_type.value in ['buy', 'sell']:
                    # 简化计算：假设当日收益为0，实际需要考虑价格变动
                    day_pnl += transaction.amount * Decimal('0.001')  # 假设0.1%的日收益
            
            if prev_value > 0:
                daily_return = day_pnl / prev_value
                daily_returns.append(daily_return)
                prev_value += day_pnl
        
        return daily_returns
    
    def _calculate_annualized_return(self, daily_returns: List[Decimal]) -> Decimal:
        """计算年化收益率"""
        if not daily_returns:
            return Decimal('0')
        
        # 复合收益率
        cumulative_return = Decimal('1')
        for daily_return in daily_returns:
            cumulative_return *= (Decimal('1') + daily_return)
        
        # 年化
        trading_days = len(daily_returns)
        if trading_days == 0:
            return Decimal('0')
        
        annualized = cumulative_return ** (Decimal('252') / Decimal(str(trading_days))) - Decimal('1')
        return annualized
    
    def _calculate_volatility(self, daily_returns: List[Decimal]) -> Decimal:
        """计算波动率"""
        if len(daily_returns) < 2:
            return Decimal('0')
        
        # 计算标准差
        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        volatility = Decimal(str(math.sqrt(float(variance))))
        
        # 年化波动率
        return volatility * Decimal(str(math.sqrt(252)))
    
    def _calculate_max_drawdown(self, daily_returns: List[Decimal]) -> Decimal:
        """计算最大回撤"""
        if not daily_returns:
            return Decimal('0')
        
        cumulative_returns = []
        cumulative = Decimal('1')
        
        for daily_return in daily_returns:
            cumulative *= (Decimal('1') + daily_return)
            cumulative_returns.append(cumulative)
        
        max_drawdown = Decimal('0')
        peak = cumulative_returns[0]
        
        for value in cumulative_returns:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self, annualized_return: Decimal, volatility: Decimal) -> Decimal:
        """计算夏普比率"""
        if volatility == 0:
            return Decimal('0')
        
        excess_return = annualized_return - self.risk_free_rate
        return excess_return / volatility
    
    def _calculate_sortino_ratio(self, daily_returns: List[Decimal]) -> Decimal:
        """计算索提诺比率"""
        if not daily_returns:
            return Decimal('0')
        
        # 计算下行波动率
        negative_returns = [r for r in daily_returns if r < 0]
        if not negative_returns:
            return Decimal('0')
        
        downside_variance = sum(r ** 2 for r in negative_returns) / len(negative_returns)
        downside_volatility = Decimal(str(math.sqrt(float(downside_variance))))
        
        if downside_volatility == 0:
            return Decimal('0')
        
        # 年化
        annualized_return = self._calculate_annualized_return(daily_returns)
        excess_return = annualized_return - self.risk_free_rate
        
        return excess_return / (downside_volatility * Decimal(str(math.sqrt(252))))
    
    def _calculate_win_rate(self, daily_returns: List[Decimal]) -> Decimal:
        """计算胜率"""
        if not daily_returns:
            return Decimal('0')
        
        winning_days = sum(1 for r in daily_returns if r > 0)
        return Decimal(str(winning_days)) / Decimal(str(len(daily_returns)))
    
    def _calculate_profit_loss_ratio(self, daily_returns: List[Decimal]) -> Decimal:
        """计算盈亏比"""
        if not daily_returns:
            return Decimal('0')
        
        positive_returns = [r for r in daily_returns if r > 0]
        negative_returns = [r for r in daily_returns if r < 0]
        
        if not positive_returns or not negative_returns:
            return Decimal('0')
        
        avg_profit = sum(positive_returns) / len(positive_returns)
        avg_loss = abs(sum(negative_returns) / len(negative_returns))
        
        if avg_loss == 0:
            return Decimal('0')
        
        return avg_profit / avg_loss
    
    def _calculate_calmar_ratio(self, annualized_return: Decimal, max_drawdown: Decimal) -> Decimal:
        """计算卡玛比率"""
        if max_drawdown == 0:
            return Decimal('0')
        
        return annualized_return / max_drawdown
    
    def _create_empty_metrics(self) -> PerformanceMetrics:
        """创建空的绩效指标"""
        return PerformanceMetrics(
            total_return=Decimal('0'),
            annualized_return=Decimal('0'),
            daily_return=Decimal('0'),
            volatility=Decimal('0'),
            max_drawdown=Decimal('0'),
            sharpe_ratio=Decimal('0'),
            sortino_ratio=Decimal('0'),
            win_rate=Decimal('0'),
            profit_loss_ratio=Decimal('0'),
            calmar_ratio=Decimal('0')
        )
    
    def _create_empty_risk_metrics(self) -> RiskMetrics:
        """创建空的风险指标"""
        return RiskMetrics(
            var_95=Decimal('0'),
            var_99=Decimal('0'),
            cvar_95=Decimal('0'),
            maximum_drawdown=Decimal('0'),
            drawdown_duration=0,
            systematic_risk=Decimal('0'),
            idiosyncratic_risk=Decimal('0'),
            concentration_risk=Decimal('0')
        )
    
    def _calculate_portfolio_weights(self, account: ModelAccount) -> Dict[str, Decimal]:
        """计算投资组合权重"""
        total_value = account.get_total_market_value()
        if total_value == 0:
            return {}
        
        weights = {}
        for symbol, position in account.positions.items():
            weights[symbol] = position.market_value / total_value
        
        return weights
    
    def _calculate_stock_returns(self, account: ModelAccount,
                               start_date: Optional[datetime],
                               end_date: Optional[datetime]) -> Dict[str, Decimal]:
        """计算个股收益率"""
        # 简化版：返回固定收益率
        # 实际应用中需要从市场数据计算
        stock_returns = {}
        for symbol in account.positions.keys():
            stock_returns[symbol] = Decimal('0.05')  # 假设5%收益率
        
        return stock_returns
    
    def _calculate_sector_attribution(self, portfolio_weights: Dict[str, Decimal],
                                    benchmark_weights: Dict[str, Decimal],
                                    stock_returns: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """计算行业归因"""
        # 简化版：按股票代码前缀分类
        sector_attribution = defaultdict(Decimal)
        
        for symbol in set(list(portfolio_weights.keys()) + list(benchmark_weights.keys())):
            # 简单的行业分类（实际应用中需要更复杂的分类）
            if symbol.startswith('00'):
                sector = '主板'
            elif symbol.startswith('30'):
                sector = '创业板'
            elif symbol.startswith('68'):
                sector = '科创板'
            else:
                sector = '其他'
            
            wp = portfolio_weights.get(symbol, Decimal('0'))
            wb = benchmark_weights.get(symbol, Decimal('0'))
            rs = stock_returns.get(symbol, Decimal('0'))
            
            sector_attribution[sector] += (wp - wb) * rs
        
        return dict(sector_attribution)
    
    def _calculate_var(self, daily_returns: List[Decimal], confidence_level: Decimal) -> Decimal:
        """计算VaR"""
        if not daily_returns:
            return Decimal('0')
        
        sorted_returns = sorted(daily_returns)
        index = int((Decimal('1') - confidence_level) * len(sorted_returns))
        
        if index >= len(sorted_returns):
            index = len(sorted_returns) - 1
        
        return abs(sorted_returns[index])
    
    def _calculate_cvar(self, daily_returns: List[Decimal], confidence_level: Decimal) -> Decimal:
        """计算CVaR"""
        if not daily_returns:
            return Decimal('0')
        
        var = self._calculate_var(daily_returns, confidence_level)
        tail_returns = [r for r in daily_returns if r <= -var]
        
        if not tail_returns:
            return var
        
        return abs(sum(tail_returns) / len(tail_returns))
    
    def _calculate_drawdown_duration(self, daily_returns: List[Decimal]) -> int:
        """计算最大回撤持续天数"""
        if not daily_returns:
            return 0
        
        cumulative_returns = []
        cumulative = Decimal('1')
        
        for daily_return in daily_returns:
            cumulative *= (Decimal('1') + daily_return)
            cumulative_returns.append(cumulative)
        
        max_duration = 0
        current_duration = 0
        peak = cumulative_returns[0]
        
        for value in cumulative_returns:
            if value > peak:
                peak = value
                current_duration = 0
            else:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
        
        return max_duration
    
    def _calculate_portfolio_variance(self, account: ModelAccount) -> Decimal:
        """计算投资组合方差"""
        # 简化版：假设所有股票方差相同
        if not account.positions:
            return Decimal('0')
        
        # 假设单个股票年化波动率为20%
        stock_variance = Decimal('0.04')  # 20%^2
        
        # 简化的投资组合方差计算
        weights = self._calculate_portfolio_weights(account)
        portfolio_variance = sum(w ** 2 * stock_variance for w in weights.values())
        
        return portfolio_variance
    
    def _calculate_concentration_risk(self, account: ModelAccount) -> Decimal:
        """计算集中度风险"""
        weights = self._calculate_portfolio_weights(account)
        if not weights:
            return Decimal('0')
        
        # 使用赫芬达尔指数衡量集中度
        hhi = sum(w ** 2 for w in weights.values())
        return hhi
    
    def _calculate_alpha_beta(self, portfolio_returns: List[Decimal],
                            benchmark_returns: List[Decimal]) -> Tuple[Decimal, Decimal]:
        """计算Alpha和Beta"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return Decimal('0'), Decimal('1')
        
        # 转换为numpy数组进行计算
        p_returns = np.array([float(r) for r in portfolio_returns])
        b_returns = np.array([float(r) for r in benchmark_returns])
        
        # 计算协方差和方差
        covariance = np.cov(p_returns, b_returns)[0, 1]
        benchmark_variance = np.var(b_returns, ddof=1)
        
        if benchmark_variance == 0:
            return Decimal('0'), Decimal('1')
        
        beta = Decimal(str(covariance / benchmark_variance))
        
        # 计算Alpha
        portfolio_mean = Decimal(str(np.mean(p_returns)))
        benchmark_mean = Decimal(str(np.mean(b_returns)))
        alpha = portfolio_mean - beta * benchmark_mean
        
        return alpha, beta
    
    def _calculate_tracking_error(self, portfolio_returns: List[Decimal],
                                benchmark_returns: List[Decimal]) -> Decimal:
        """计算跟踪误差"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return Decimal('0')
        
        # 计算超额收益
        excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        
        # 计算超额收益的标准差
        mean_excess = sum(excess_returns) / len(excess_returns)
        variance = sum((r - mean_excess) ** 2 for r in excess_returns) / (len(excess_returns) - 1)
        
        tracking_error = Decimal(str(math.sqrt(float(variance))))
        
        # 年化
        return tracking_error * Decimal(str(math.sqrt(252)))
    
    def _calculate_information_ratio(self, portfolio_returns: List[Decimal],
                                   benchmark_returns: List[Decimal],
                                   tracking_error: Decimal) -> Decimal:
        """计算信息比率"""
        if tracking_error == 0:
            return Decimal('0')
        
        # 计算平均超额收益
        excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        avg_excess_return = sum(excess_returns) / len(excess_returns)
        
        # 年化
        annualized_excess_return = avg_excess_return * Decimal('252')
        
        return annualized_excess_return / tracking_error
    
    def _analyze_positions(self, account: ModelAccount) -> Dict[str, Any]:
        """分析持仓"""
        if not account.positions:
            return {"total_positions": 0}
        
        total_value = account.get_total_market_value()
        positions_data = []
        
        for symbol, position in account.positions.items():
            weight = position.market_value / total_value if total_value > 0 else Decimal('0')
            positions_data.append({
                "symbol": symbol,
                "quantity": float(position.quantity),
                "avg_cost": float(position.avg_cost),
                "market_value": float(position.market_value),
                "weight": float(weight),
                "unrealized_pnl": float(position.unrealized_pnl),
                "realized_pnl": float(position.realized_pnl)
            })
        
        # 按市值排序
        positions_data.sort(key=lambda x: x["market_value"], reverse=True)
        
        return {
            "total_positions": len(account.positions),
            "total_market_value": float(total_value),
            "positions": positions_data[:10],  # 只返回前10大持仓
            "concentration": {
                "top_5_weight": sum(p["weight"] for p in positions_data[:5]),
                "top_10_weight": sum(p["weight"] for p in positions_data[:10])
            }
        }
    
    def _analyze_trading_behavior(self, account: ModelAccount,
                                start_date: Optional[datetime],
                                end_date: Optional[datetime]) -> Dict[str, Any]:
        """分析交易行为"""
        transactions = self._filter_transactions_by_date(
            account.transactions, start_date, end_date
        )
        
        if not transactions:
            return {"total_transactions": 0}
        
        buy_transactions = [t for t in transactions if t.transaction_type.value == 'buy']
        sell_transactions = [t for t in transactions if t.transaction_type.value == 'sell']
        
        total_buy_amount = sum(t.amount for t in buy_transactions)
        total_sell_amount = sum(t.amount for t in sell_transactions)
        total_commission = sum(t.commission for t in transactions)
        total_slippage = sum(t.slippage for t in transactions)
        
        return {
            "total_transactions": len(transactions),
            "buy_transactions": len(buy_transactions),
            "sell_transactions": len(sell_transactions),
            "total_buy_amount": float(total_buy_amount),
            "total_sell_amount": float(total_sell_amount),
            "total_commission": float(total_commission),
            "total_slippage": float(total_slippage),
            "avg_transaction_size": float(
                (total_buy_amount + total_sell_amount) / len(transactions)
            ) if transactions else 0,
            "turnover_rate": float(
                (total_buy_amount + total_sell_amount) / (2 * account.get_total_assets())
            ) if account.get_total_assets() > 0 else 0
        }