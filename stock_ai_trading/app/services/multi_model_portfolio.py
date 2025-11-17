"""
多模型资产账簿系统

实现每个LLM模型的独立资产核算，包括：
- 独立现金账户
- 独立持仓记录
- 独立盈亏计算
- 统一费率管理
- 滑点管理
- 绩效分析
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """交易类型"""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    CASH_DEPOSIT = "cash_deposit"
    CASH_WITHDRAWAL = "cash_withdrawal"


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    market_value: Decimal = Decimal('0')
    unrealized_pnl: Decimal = Decimal('0')
    realized_pnl: Decimal = Decimal('0')
    last_price: Decimal = Decimal('0')
    
    def update_market_value(self, current_price: Decimal):
        """更新市值和未实现盈亏"""
        self.last_price = current_price
        self.market_value = self.quantity * current_price
        self.unrealized_pnl = self.market_value - (self.quantity * self.avg_cost)


@dataclass
class Transaction:
    """交易记录"""
    transaction_id: str
    model_id: str
    timestamp: datetime
    transaction_type: TransactionType
    symbol: str
    quantity: Decimal
    price: Decimal
    amount: Decimal
    commission: Decimal = Decimal('0')
    stamp_tax: Decimal = Decimal('0')
    transfer_fee: Decimal = Decimal('0')
    slippage: Decimal = Decimal('0')
    total_cost: Decimal = Decimal('0')
    
    def __post_init__(self):
        """计算总成本"""
        self.total_cost = self.amount + self.commission + self.stamp_tax + self.transfer_fee + self.slippage


@dataclass
class FeeConfig:
    """费率配置"""
    commission_rate: Decimal = Decimal('0.0003')  # 万分之三
    stamp_tax_rate: Decimal = Decimal('0.001')    # 千分之一（仅卖出）
    transfer_fee_rate: Decimal = Decimal('0.00002')  # 万分之零点二
    min_commission: Decimal = Decimal('5')        # 最低佣金5元
    
    def calculate_fees(self, amount: Decimal, is_sell: bool = False) -> Tuple[Decimal, Decimal, Decimal]:
        """计算交易费用"""
        # 佣金
        commission = max(amount * self.commission_rate, self.min_commission)
        
        # 印花税（仅卖出）
        stamp_tax = amount * self.stamp_tax_rate if is_sell else Decimal('0')
        
        # 过户费
        transfer_fee = amount * self.transfer_fee_rate
        
        return commission, stamp_tax, transfer_fee


@dataclass
class SlippageConfig:
    """滑点配置"""
    fixed_slippage_bp: Decimal = Decimal('7.5')  # 固定滑点7.5bp
    liquidity_factor: Decimal = Decimal('1.0')   # 流动性因子
    max_slippage_bp: Decimal = Decimal('50')     # 最大滑点50bp
    
    def calculate_slippage(self, price: Decimal, quantity: Decimal, 
                          avg_volume: Optional[Decimal] = None) -> Decimal:
        """计算滑点成本"""
        # 基础固定滑点
        base_slippage = price * (self.fixed_slippage_bp / Decimal('10000'))
        
        # 流动性自适应滑点
        if avg_volume and avg_volume > 0:
            volume_impact = (quantity / avg_volume) * Decimal('10')  # 简化的冲击模型
            adaptive_slippage = price * (volume_impact / Decimal('10000'))
            adaptive_slippage = min(adaptive_slippage, 
                                  price * (self.max_slippage_bp / Decimal('10000')))
        else:
            adaptive_slippage = Decimal('0')
        
        total_slippage = base_slippage + adaptive_slippage
        return total_slippage * quantity


class ModelAccount:
    """单个模型的账户"""
    
    def __init__(self, model_id: str, initial_cash: Decimal = Decimal('1000000')):
        self.model_id = model_id
        self.cash_balance = initial_cash
        self.initial_cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.transactions: List[Transaction] = []
        self.created_at = datetime.now(timezone.utc)
        
    def get_total_market_value(self) -> Decimal:
        """获取总市值"""
        return sum(pos.market_value for pos in self.positions.values())
    
    def get_total_assets(self) -> Decimal:
        """获取总资产"""
        return self.cash_balance + self.get_total_market_value()
    
    def get_total_pnl(self) -> Decimal:
        """获取总盈亏"""
        realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        return realized_pnl + unrealized_pnl
    
    def get_return_rate(self) -> Decimal:
        """获取收益率"""
        if self.initial_cash == 0:
            return Decimal('0')
        return (self.get_total_assets() - self.initial_cash) / self.initial_cash
    
    def update_positions_market_value(self, market_prices: Dict[str, Decimal]):
        """更新所有持仓的市值"""
        for symbol, position in self.positions.items():
            if symbol in market_prices:
                position.update_market_value(market_prices[symbol])
    
    def add_transaction(self, transaction: Transaction):
        """添加交易记录"""
        self.transactions.append(transaction)
        
        if transaction.transaction_type == TransactionType.BUY:
            self._process_buy_transaction(transaction)
        elif transaction.transaction_type == TransactionType.SELL:
            self._process_sell_transaction(transaction)
        elif transaction.transaction_type == TransactionType.CASH_DEPOSIT:
            self.cash_balance += transaction.amount
        elif transaction.transaction_type == TransactionType.CASH_WITHDRAWAL:
            self.cash_balance -= transaction.amount
    
    def _process_buy_transaction(self, transaction: Transaction):
        """处理买入交易"""
        symbol = transaction.symbol
        
        # 更新现金余额
        self.cash_balance -= transaction.total_cost
        
        # 更新持仓
        if symbol in self.positions:
            position = self.positions[symbol]
            total_cost = position.quantity * position.avg_cost + transaction.amount
            total_quantity = position.quantity + transaction.quantity
            position.avg_cost = total_cost / total_quantity
            position.quantity = total_quantity
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=transaction.quantity,
                avg_cost=transaction.price
            )
    
    def _process_sell_transaction(self, transaction: Transaction):
        """处理卖出交易"""
        symbol = transaction.symbol
        
        if symbol not in self.positions:
            raise ValueError(f"尝试卖出未持有的股票: {symbol}")
        
        position = self.positions[symbol]
        if position.quantity < transaction.quantity:
            raise ValueError(f"持仓不足，当前持仓: {position.quantity}, 尝试卖出: {transaction.quantity}")
        
        # 计算已实现盈亏
        cost_basis = position.avg_cost * transaction.quantity
        realized_pnl = transaction.amount - cost_basis
        position.realized_pnl += realized_pnl
        
        # 更新持仓
        position.quantity -= transaction.quantity
        
        # 更新现金余额
        net_proceeds = transaction.amount - (transaction.commission + transaction.stamp_tax + 
                                           transaction.transfer_fee + transaction.slippage)
        self.cash_balance += net_proceeds
        
        # 如果持仓为0，删除持仓记录
        if position.quantity == 0:
            del self.positions[symbol]


class MultiModelPortfolio:
    """多模型资产账簿管理器"""
    
    def __init__(self, fee_config: Optional[FeeConfig] = None, 
                 slippage_config: Optional[SlippageConfig] = None):
        self.accounts: Dict[str, ModelAccount] = {}
        self.fee_config = fee_config or FeeConfig()
        self.slippage_config = slippage_config or SlippageConfig()
        self.market_prices: Dict[str, Decimal] = {}
        
    def create_account(self, model_id: str, initial_cash: Decimal = Decimal('1000000')) -> ModelAccount:
        """创建模型账户"""
        if model_id in self.accounts:
            raise ValueError(f"账户已存在: {model_id}")
        
        account = ModelAccount(model_id, initial_cash)
        self.accounts[model_id] = account
        logger.info(f"创建模型账户: {model_id}, 初始资金: {initial_cash}")
        return account
    
    def get_account(self, model_id: str) -> Optional[ModelAccount]:
        """获取模型账户"""
        return self.accounts.get(model_id)
    
    def update_market_prices(self, prices: Dict[str, Decimal]):
        """更新市场价格"""
        self.market_prices.update(prices)
        
        # 更新所有账户的持仓市值
        for account in self.accounts.values():
            account.update_positions_market_value(self.market_prices)
    
    def execute_trade(self, model_id: str, symbol: str, quantity: Decimal, 
                     price: Decimal, is_buy: bool, avg_volume: Optional[Decimal] = None) -> Transaction:
        """执行交易"""
        account = self.get_account(model_id)
        if not account:
            raise ValueError(f"账户不存在: {model_id}")
        
        # 计算交易金额
        amount = quantity * price
        
        # 计算费用
        commission, stamp_tax, transfer_fee = self.fee_config.calculate_fees(amount, not is_buy)
        
        # 计算滑点
        slippage = self.slippage_config.calculate_slippage(price, quantity, avg_volume)
        
        # 创建交易记录
        transaction = Transaction(
            transaction_id=f"{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            model_id=model_id,
            timestamp=datetime.now(timezone.utc),
            transaction_type=TransactionType.BUY if is_buy else TransactionType.SELL,
            symbol=symbol,
            quantity=quantity,
            price=price,
            amount=amount,
            commission=commission,
            stamp_tax=stamp_tax,
            transfer_fee=transfer_fee,
            slippage=slippage
        )
        
        # 检查资金是否充足（买入时）
        if is_buy and account.cash_balance < transaction.total_cost:
            raise ValueError(f"资金不足，需要: {transaction.total_cost}, 可用: {account.cash_balance}")
        
        # 执行交易
        account.add_transaction(transaction)
        
        logger.info(f"执行交易 - 模型: {model_id}, 股票: {symbol}, "
                   f"{'买入' if is_buy else '卖出'}: {quantity}, 价格: {price}, "
                   f"总成本: {transaction.total_cost}")
        
        return transaction
    
    def get_portfolio_summary(self) -> Dict:
        """获取投资组合汇总"""
        summary = {
            'total_accounts': len(self.accounts),
            'accounts': {},
            'aggregate': {
                'total_assets': Decimal('0'),
                'total_cash': Decimal('0'),
                'total_market_value': Decimal('0'),
                'total_pnl': Decimal('0'),
                'avg_return_rate': Decimal('0')
            }
        }
        
        total_initial_cash = Decimal('0')
        
        for model_id, account in self.accounts.items():
            account_summary = {
                'cash_balance': account.cash_balance,
                'market_value': account.get_total_market_value(),
                'total_assets': account.get_total_assets(),
                'total_pnl': account.get_total_pnl(),
                'return_rate': account.get_return_rate(),
                'positions_count': len(account.positions),
                'transactions_count': len(account.transactions)
            }
            
            summary['accounts'][model_id] = account_summary
            summary['aggregate']['total_assets'] += account_summary['total_assets']
            summary['aggregate']['total_cash'] += account_summary['cash_balance']
            summary['aggregate']['total_market_value'] += account_summary['market_value']
            summary['aggregate']['total_pnl'] += account_summary['total_pnl']
            total_initial_cash += account.initial_cash
        
        # 计算平均收益率
        if total_initial_cash > 0:
            summary['aggregate']['avg_return_rate'] = (
                (summary['aggregate']['total_assets'] - total_initial_cash) / total_initial_cash
            )
        
        return summary
    
    def get_model_positions(self, model_id: str) -> Dict[str, Position]:
        """获取模型持仓"""
        account = self.get_account(model_id)
        if not account:
            return {}
        return account.positions.copy()
    
    def get_model_transactions(self, model_id: str, limit: Optional[int] = None) -> List[Transaction]:
        """获取模型交易记录"""
        account = self.get_account(model_id)
        if not account:
            return []
        
        transactions = sorted(account.transactions, key=lambda x: x.timestamp, reverse=True)
        if limit:
            transactions = transactions[:limit]
        
        return transactions