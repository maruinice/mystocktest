"""
交易服务

提供订单管理、持仓管理、账户信息等功能
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import random

from app.models.trade import Order, Position, Trade, OrderType, OrderStatus, OrderSide
from app.models.stock import Stock


class TradeService:
    """交易服务类"""
    
    def __init__(self):
        # 模拟数据存储
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.trades: Dict[str, Trade] = {}
        self.accounts: Dict[str, Dict[str, Any]] = {}
        
        # 初始化示例数据
        self._init_sample_data()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        # 创建示例账户
        sample_user_id = "user_001"
        self.accounts[sample_user_id] = {
            'user_id': sample_user_id,
            'total_assets': 1000000.0,  # 总资产
            'available_cash': 500000.0,  # 可用资金
            'frozen_cash': 50000.0,     # 冻结资金
            'market_value': 450000.0,   # 持仓市值
            'profit_loss': 25000.0,     # 浮动盈亏
            'profit_loss_pct': 5.88,    # 盈亏比例
            'buying_power': 500000.0,   # 购买力
            'margin_used': 0.0,         # 已用保证金
            'margin_available': 0.0,    # 可用保证金
            'created_at': datetime.now() - timedelta(days=365),
            'updated_at': datetime.now()
        }
        
        # 创建示例持仓
        sample_positions = [
            {
                'user_id': sample_user_id,
                'code': '000001',
                'name': '平安银行',
                'quantity': 1000,
                'available_quantity': 1000,
                'avg_cost': 12.50,
                'last_price': 13.20,
                'market_value': 13200.0,
                'profit_loss': 700.0,
                'profit_loss_pct': 5.6
            },
            {
                'user_id': sample_user_id,
                'code': '000002',
                'name': '万科A',
                'quantity': 2000,
                'available_quantity': 2000,
                'avg_cost': 18.80,
                'last_price': 19.50,
                'market_value': 39000.0,
                'profit_loss': 1400.0,
                'profit_loss_pct': 3.72
            }
        ]
        
        for pos_data in sample_positions:
            position = Position(
                position_id=str(uuid.uuid4()),
                user_id=pos_data['user_id'],
                code=pos_data['code'],
                name=pos_data['name'],
                quantity=pos_data['quantity'],
                available_quantity=pos_data['available_quantity'],
                avg_cost=pos_data['avg_cost'],
                last_price=pos_data['last_price'],
                market_value=pos_data['market_value'],
                profit_loss=pos_data['profit_loss'],
                profit_loss_pct=pos_data['profit_loss_pct'],
                created_at=datetime.now() - timedelta(days=30),
                updated_at=datetime.now()
            )
            self.positions[f"{pos_data['user_id']}_{pos_data['code']}"] = position
        
        # 创建示例订单
        sample_orders = [
            {
                'user_id': sample_user_id,
                'code': '000001',
                'name': '平安银行',
                'side': OrderSide.BUY,
                'type': OrderType.LIMIT,
                'quantity': 500,
                'price': 13.00,
                'status': OrderStatus.PENDING
            },
            {
                'user_id': sample_user_id,
                'code': '000002',
                'name': '万科A',
                'side': OrderSide.SELL,
                'type': OrderType.MARKET,
                'quantity': 300,
                'price': 0.0,
                'status': OrderStatus.FILLED
            }
        ]
        
        for order_data in sample_orders:
            order = Order(
                order_id=str(uuid.uuid4()),
                user_id=order_data['user_id'],
                code=order_data['code'],
                name=order_data['name'],
                side=order_data['side'],
                order_type=order_data['type'],
                quantity=order_data['quantity'],
                price=order_data['price'],
                filled_quantity=order_data['quantity'] if order_data['status'] == OrderStatus.FILLED else 0,
                avg_price=order_data['price'] if order_data['status'] == OrderStatus.FILLED else 0.0,
                status=order_data['status'],
                created_at=datetime.now() - timedelta(hours=random.randint(1, 24)),
                updated_at=datetime.now()
            )
            self.orders[order.order_id] = order
    
    def place_order(self, user_id: int, symbol: str, side: str, order_type: str,
                   quantity: int, price: float = None) -> Dict[str, Any]:
        """
        下单（兼容API调用）
        
        Args:
            user_id: 用户ID
            symbol: 股票代码（如603387.SH）
            side: 方向（buy/sell）
            order_type: 订单类型（limit/market）
            quantity: 数量
            price: 价格（限价单必须）
            
        Returns:
            订单信息字典
        """
        # 转换参数
        user_id_str = str(user_id)
        code = symbol.split('.')[0]  # 去掉后缀：603387.SH -> 603387
        
        # 转换枚举类型
        side_enum = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        order_type_enum = OrderType.LIMIT if order_type.lower() == 'limit' else OrderType.MARKET
        
        # 调用创建订单
        order = self.create_order(
            user_id=user_id_str,
            code=code,
            side=side_enum,
            order_type=order_type_enum,
            quantity=quantity,
            price=price if price else 0.0
        )
        
        if not order:
            raise ValueError("下单失败：资金不足或持仓不足")
        
        # 转换为字典返回
        return {
            'order_id': order.order_id,
            'user_id': order.user_id,
            'symbol': symbol,
            'code': order.code,
            'name': order.name,
            'side': order.side.value,
            'order_type': order.order_type.value,
            'quantity': order.quantity,
            'price': order.price,
            'filled_quantity': order.filled_quantity,
            'avg_price': order.avg_price,
            'status': order.status.value,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat()
        }
    
    def create_order(self, user_id: str, code: str, side: OrderSide, order_type: OrderType,
                    quantity: int, price: float = 0.0, stop_price: float = 0.0,
                    time_in_force: str = 'day', notes: str = '') -> Optional[Order]:
        """创建订单"""
        try:
            # 检查账户资金
            account = self.accounts.get(user_id)
            if not account:
                return None
            
            # 估算订单金额
            estimated_amount = quantity * (price if price > 0 else self._get_market_price(code))
            
            # 买入检查资金
            if side == OrderSide.BUY:
                if account['available_cash'] < estimated_amount:
                    return None
            
            # 卖出检查持仓
            if side == OrderSide.SELL:
                position_key = f"{user_id}_{code}"
                position = self.positions.get(position_key)
                if not position or position.available_quantity < quantity:
                    return None
            
            # 创建订单
            order = Order(
                order_id=str(uuid.uuid4()),
                user_id=user_id,
                code=code,
                name=self._get_stock_name(code),
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                time_in_force=time_in_force,
                notes=notes,
                status=OrderStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.orders[order.order_id] = order
            
            # 冻结资金或持仓
            if side == OrderSide.BUY:
                account['available_cash'] -= estimated_amount
                account['frozen_cash'] += estimated_amount
            else:
                position_key = f"{user_id}_{code}"
                position = self.positions.get(position_key)
                if position:
                    position.available_quantity -= quantity
            
            # 模拟订单处理（市价单立即成交）
            if order_type == OrderType.MARKET:
                self._fill_order(order)
            
            return order
            
        except Exception as e:
            print(f"创建订单失败: {e}")
            return None
    
    def cancel_order(self, user_id: str, order_id: str) -> bool:
        """撤销订单"""
        try:
            order = self.orders.get(order_id)
            if not order or order.user_id != user_id:
                return False
            
            if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIAL]:
                return False
            
            # 更新订单状态
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            
            # 释放冻结资金或持仓
            account = self.accounts.get(user_id)
            if account:
                if order.side == OrderSide.BUY:
                    unfilled_amount = (order.quantity - order.filled_quantity) * order.price
                    account['available_cash'] += unfilled_amount
                    account['frozen_cash'] -= unfilled_amount
                else:
                    position_key = f"{user_id}_{order.code}"
                    position = self.positions.get(position_key)
                    if position:
                        position.available_quantity += (order.quantity - order.filled_quantity)
            
            return True
            
        except Exception as e:
            print(f"撤销订单失败: {e}")
            return False
    
    def modify_order(self, user_id: str, order_id: str, update_data: Dict[str, Any]) -> bool:
        """修改订单"""
        try:
            order = self.orders.get(order_id)
            if not order or order.user_id != user_id:
                return False
            
            if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIAL]:
                return False
            
            # 更新订单字段
            for field, value in update_data.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            
            order.updated_at = datetime.now()
            return True
            
        except Exception as e:
            print(f"修改订单失败: {e}")
            return False
    
    def get_orders(self, user_id: str, status: str = '', code: str = '', side: str = '',
                  start_date: str = '', end_date: str = '', page: int = 1, size: int = 20) -> Tuple[List[Order], int]:
        """获取订单列表"""
        try:
            # 过滤订单
            filtered_orders = []
            for order in self.orders.values():
                if order.user_id != user_id:
                    continue
                
                if status and order.status.value != status:
                    continue
                
                if code and order.code != code:
                    continue
                
                if side and order.side.value != side:
                    continue
                
                if start_date:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if order.created_at < start_dt:
                        continue
                
                if end_date:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if order.created_at > end_dt:
                        continue
                
                filtered_orders.append(order)
            
            # 按创建时间倒序排序
            filtered_orders.sort(key=lambda x: x.created_at, reverse=True)
            
            # 分页
            total = len(filtered_orders)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            orders = filtered_orders[start_idx:end_idx]
            
            return orders, total
            
        except Exception as e:
            print(f"获取订单列表失败: {e}")
            return [], 0
    
    def get_order_by_id(self, user_id: str, order_id: str) -> Optional[Order]:
        """根据ID获取订单"""
        order = self.orders.get(order_id)
        if order and order.user_id == user_id:
            return order
        return None
    
    def get_positions(self, user_id: str, code: str = '', include_zero: bool = False) -> List[Position]:
        """获取持仓列表"""
        try:
            positions = []
            for position in self.positions.values():
                if position.user_id != user_id:
                    continue
                
                if code and position.code != code:
                    continue
                
                if not include_zero and position.quantity == 0:
                    continue
                
                # 更新实时价格和盈亏
                current_price = self._get_market_price(position.code)
                position.last_price = current_price
                position.market_value = position.quantity * current_price
                position.profit_loss = position.market_value - (position.quantity * position.avg_cost)
                position.profit_loss_pct = (position.profit_loss / (position.quantity * position.avg_cost) * 100 
                                          if position.quantity > 0 and position.avg_cost > 0 else 0)
                position.updated_at = datetime.now()
                
                positions.append(position)
            
            return positions
            
        except Exception as e:
            print(f"获取持仓列表失败: {e}")
            return []
    
    def get_position_by_code(self, user_id: str, code: str) -> Optional[Position]:
        """根据股票代码获取持仓"""
        position_key = f"{user_id}_{code}"
        position = self.positions.get(position_key)
        if position:
            # 更新实时价格和盈亏
            current_price = self._get_market_price(code)
            position.last_price = current_price
            position.market_value = position.quantity * current_price
            position.profit_loss = position.market_value - (position.quantity * position.avg_cost)
            position.profit_loss_pct = (position.profit_loss / (position.quantity * position.avg_cost) * 100 
                                      if position.quantity > 0 and position.avg_cost > 0 else 0)
            position.updated_at = datetime.now()
        return position
    
    def get_account_info(self, user_id: str) -> Dict[str, Any]:
        """获取账户信息"""
        account = self.accounts.get(user_id, {})
        if not account:
            # 创建默认账户
            account = {
                'user_id': user_id,
                'total_assets': 100000.0,
                'available_cash': 100000.0,
                'frozen_cash': 0.0,
                'market_value': 0.0,
                'profit_loss': 0.0,
                'profit_loss_pct': 0.0,
                'buying_power': 100000.0,
                'margin_used': 0.0,
                'margin_available': 0.0,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            self.accounts[user_id] = account
        
        # 更新账户信息
        positions = self.get_positions(user_id)
        total_market_value = sum(pos.market_value for pos in positions)
        total_profit_loss = sum(pos.profit_loss for pos in positions)
        
        account['market_value'] = total_market_value
        account['profit_loss'] = total_profit_loss
        account['total_assets'] = account['available_cash'] + account['frozen_cash'] + total_market_value
        account['profit_loss_pct'] = (total_profit_loss / (total_market_value - total_profit_loss) * 100 
                                    if total_market_value > total_profit_loss else 0)
        account['updated_at'] = datetime.now()
        
        return account
    
    def get_trades(self, user_id: str, code: str = '', side: str = '',
                  start_date: str = '', end_date: str = '', page: int = 1, size: int = 20) -> Tuple[List[Trade], int]:
        """获取成交记录"""
        try:
            # 过滤成交记录
            filtered_trades = []
            for trade in self.trades.values():
                if trade.user_id != user_id:
                    continue
                
                if code and trade.code != code:
                    continue
                
                if side and trade.side.value != side:
                    continue
                
                if start_date:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if trade.trade_time < start_dt:
                        continue
                
                if end_date:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if trade.trade_time > end_dt:
                        continue
                
                filtered_trades.append(trade)
            
            # 按成交时间倒序排序
            filtered_trades.sort(key=lambda x: x.trade_time, reverse=True)
            
            # 分页
            total = len(filtered_trades)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            trades = filtered_trades[start_idx:end_idx]
            
            return trades, total
            
        except Exception as e:
            print(f"获取成交记录失败: {e}")
            return [], 0
    
    def batch_cancel_orders(self, user_id: str, order_ids: List[str]) -> List[Dict[str, Any]]:
        """批量撤销订单"""
        results = []
        for order_id in order_ids:
            success = self.cancel_order(user_id, order_id)
            results.append({
                'order_id': order_id,
                'success': success,
                'message': '撤销成功' if success else '撤销失败'
            })
        return results
    
    def _fill_order(self, order: Order):
        """模拟订单成交"""
        try:
            # 获取市场价格
            market_price = self._get_market_price(order.code)
            
            # 更新订单状态
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.avg_price = market_price if order.order_type == OrderType.MARKET else order.price
            order.updated_at = datetime.now()
            
            # 创建成交记录
            trade = Trade(
                trade_id=str(uuid.uuid4()),
                order_id=order.order_id,
                user_id=order.user_id,
                code=order.code,
                name=order.name,
                side=order.side,
                quantity=order.quantity,
                price=order.avg_price,
                amount=order.quantity * order.avg_price,
                commission=order.quantity * order.avg_price * 0.0003,  # 万三手续费
                trade_time=datetime.now()
            )
            self.trades[trade.trade_id] = trade
            
            # 更新账户和持仓
            self._update_account_and_position(order, trade)
            
        except Exception as e:
            print(f"订单成交处理失败: {e}")
    
    def _update_account_and_position(self, order: Order, trade: Trade):
        """更新账户和持仓"""
        try:
            account = self.accounts.get(order.user_id)
            if not account:
                return
            
            position_key = f"{order.user_id}_{order.code}"
            
            if order.side == OrderSide.BUY:
                # 买入：减少现金，增加持仓
                total_cost = trade.amount + trade.commission
                account['available_cash'] -= total_cost
                account['frozen_cash'] -= trade.amount
                
                # 更新持仓
                position = self.positions.get(position_key)
                if position:
                    # 计算新的平均成本
                    total_quantity = position.quantity + trade.quantity
                    total_cost_basis = (position.quantity * position.avg_cost + 
                                      trade.quantity * trade.price + trade.commission)
                    position.avg_cost = total_cost_basis / total_quantity
                    position.quantity = total_quantity
                    position.available_quantity = total_quantity
                else:
                    # 创建新持仓
                    position = Position(
                        position_id=str(uuid.uuid4()),
                        user_id=order.user_id,
                        code=order.code,
                        name=order.name,
                        quantity=trade.quantity,
                        available_quantity=trade.quantity,
                        avg_cost=(trade.price + trade.commission / trade.quantity),
                        last_price=trade.price,
                        market_value=trade.quantity * trade.price,
                        profit_loss=0.0,
                        profit_loss_pct=0.0,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self.positions[position_key] = position
            
            else:  # 卖出
                # 卖出：增加现金，减少持仓
                net_amount = trade.amount - trade.commission
                account['available_cash'] += net_amount
                
                # 更新持仓
                position = self.positions.get(position_key)
                if position:
                    position.quantity -= trade.quantity
                    position.available_quantity = position.quantity
                    if position.quantity == 0:
                        position.avg_cost = 0.0
                        position.market_value = 0.0
                        position.profit_loss = 0.0
                        position.profit_loss_pct = 0.0
            
            account['updated_at'] = datetime.now()
            
        except Exception as e:
            print(f"更新账户和持仓失败: {e}")
    
    def _get_market_price(self, code: str) -> float:
        """获取市场价格（模拟）"""
        # 模拟价格数据
        base_prices = {
            '000001': 13.20,
            '000002': 19.50,
            '000858': 25.80,
            '002415': 45.60,
            '600036': 35.20,
            '600519': 1680.00
        }
        
        base_price = base_prices.get(code, 10.0)
        # 添加随机波动
        volatility = random.uniform(-0.05, 0.05)
        return round(base_price * (1 + volatility), 2)
    
    def _get_stock_name(self, code: str) -> str:
        """获取股票名称（模拟）"""
        names = {
            '000001': '平安银行',
            '000002': '万科A',
            '000858': '五粮液',
            '002415': '海康威视',
            '600036': '招商银行',
            '600519': '贵州茅台'
        }
        return names.get(code, f'股票{code}')