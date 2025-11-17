"""
实盘交易引擎
支持券商API对接、证书安全管理、交易会话管理
"""

import asyncio
import ssl
import aiohttp
import hashlib
import hmac
import base64
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path
import logging

from .trading_engine import (
    BaseTradingEngine, Order, Trade, Position, AccountInfo,
    OrderSide, OrderType, OrderStatus, TradingMode
)

logger = logging.getLogger(__name__)


@dataclass
class BrokerConfig:
    """券商配置"""
    broker_name: str
    api_url: str
    account_id: str
    api_key: str
    api_secret: str
    cert_path: Optional[str] = None
    cert_password: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 100  # 每分钟最大请求数
    sandbox: bool = True  # 是否沙盒环境


@dataclass
class TradingSession:
    """交易会话"""
    session_id: str
    broker_name: str
    account_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool = False
    last_heartbeat: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at

    @property
    def needs_refresh(self) -> bool:
        """是否需要刷新"""
        if not self.expires_at:
            return False
        # 提前5分钟刷新
        return datetime.now() >= (self.expires_at - timedelta(minutes=5))


class BrokerAdapter(ABC):
    """券商适配器接口"""

    def __init__(self, config: BrokerConfig):
        self.config = config
        self.session: Optional[TradingSession] = None
        self.ssl_context: Optional[ssl.SSLContext] = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @abstractmethod
    async def authenticate(self) -> TradingSession:
        """认证登录"""
        pass

    @abstractmethod
    async def place_order(self, order: Order) -> str:
        """下单"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """获取订单状态"""
        pass

    @abstractmethod
    async def get_positions(self) -> Dict[str, Position]:
        """获取持仓"""
        pass

    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """获取账户信息"""
        pass

    @abstractmethod
    async def get_trades(self, symbol: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[Trade]:
        """获取成交记录"""
        pass

    async def setup_ssl_context(self):
        """设置SSL上下文"""
        if not self.config.cert_path:
            return

        try:
            self.ssl_context = ssl.create_default_context()
            
            # 加载客户端证书
            cert_path = Path(self.config.cert_path)
            if cert_path.exists():
                self.ssl_context.load_cert_chain(
                    cert_path,
                    password=self.config.cert_password
                )
                self.logger.info(f"SSL证书加载成功: {cert_path}")
            else:
                self.logger.warning(f"SSL证书文件不存在: {cert_path}")

        except Exception as e:
            self.logger.error(f"SSL证书设置失败: {str(e)}")
            raise

    async def refresh_session(self) -> bool:
        """刷新会话"""
        if not self.session or not self.session.refresh_token:
            return False

        try:
            # 子类实现具体的刷新逻辑
            return await self._refresh_token()
        except Exception as e:
            self.logger.error(f"会话刷新失败: {str(e)}")
            return False

    @abstractmethod
    async def _refresh_token(self) -> bool:
        """刷新令牌（子类实现）"""
        pass

    async def ensure_session_valid(self):
        """确保会话有效"""
        if not self.session or not self.session.is_active:
            self.session = await self.authenticate()
        elif self.session.needs_refresh:
            if not await self.refresh_session():
                self.session = await self.authenticate()

    def generate_signature(self, method: str, url: str, params: Dict[str, Any] = None,
                          body: str = None) -> str:
        """生成API签名"""
        timestamp = str(int(time.time() * 1000))
        
        # 构建签名字符串
        sign_str = f"{method}\n{url}\n"
        
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            sign_str += f"{query_string}\n"
        
        if body:
            sign_str += body
        
        sign_str += timestamp
        
        # HMAC-SHA256签名
        signature = hmac.new(
            self.config.api_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')


class HuataiAdapter(BrokerAdapter):
    """华泰证券适配器"""

    def __init__(self, config: BrokerConfig):
        super().__init__(config)
        self.base_url = config.api_url.rstrip('/')

    async def authenticate(self) -> TradingSession:
        """华泰认证登录"""
        try:
            await self.setup_ssl_context()
            
            auth_data = {
                "account_id": self.config.account_id,
                "api_key": self.config.api_key,
                "timestamp": int(time.time() * 1000)
            }
            
            # 生成签名
            signature = self.generate_signature("POST", "/auth/login", body=json.dumps(auth_data))
            auth_data["signature"] = signature
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.ssl_context),
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.post(
                    f"{self.base_url}/auth/login",
                    json=auth_data
                ) as response:
                    if response.status != 200:
                        raise Exception(f"认证失败: {response.status}")
                    
                    result = await response.json()
                    
                    trading_session = TradingSession(
                        session_id=result.get("session_id"),
                        broker_name="huatai",
                        account_id=self.config.account_id,
                        access_token=result.get("access_token"),
                        refresh_token=result.get("refresh_token"),
                        expires_at=datetime.now() + timedelta(seconds=result.get("expires_in", 3600)),
                        is_active=True,
                        last_heartbeat=datetime.now()
                    )
                    
                    self.logger.info("华泰证券认证成功")
                    return trading_session

        except Exception as e:
            self.logger.error(f"华泰证券认证失败: {str(e)}")
            raise

    async def place_order(self, order: Order) -> str:
        """华泰下单"""
        await self.ensure_session_valid()
        
        try:
            order_data = {
                "symbol": order.symbol,
                "side": order.side.value,
                "order_type": order.order_type.value,
                "quantity": str(order.quantity),
                "price": str(order.price) if order.price else None,
                "stop_price": str(order.stop_price) if order.stop_price else None
            }
            
            headers = {
                "Authorization": f"Bearer {self.session.access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.ssl_context),
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.post(
                    f"{self.base_url}/orders",
                    json=order_data,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise Exception(f"下单失败: {response.status}")
                    
                    result = await response.json()
                    return result.get("order_id")

        except Exception as e:
            self.logger.error(f"华泰下单失败: {str(e)}")
            raise

    async def cancel_order(self, order_id: str) -> bool:
        """华泰撤单"""
        await self.ensure_session_valid()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.session.access_token}"
            }
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.ssl_context),
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.delete(
                    f"{self.base_url}/orders/{order_id}",
                    headers=headers
                ) as response:
                    return response.status == 200

        except Exception as e:
            self.logger.error(f"华泰撤单失败: {str(e)}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """获取华泰订单状态"""
        await self.ensure_session_valid()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.session.access_token}"
            }
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.ssl_context),
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.get(
                    f"{self.base_url}/orders/{order_id}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return None
                    
                    result = await response.json()
                    
                    # 转换为Order对象
                    return Order(
                        order_id=result["order_id"],
                        symbol=result["symbol"],
                        side=OrderSide(result["side"]),
                        order_type=OrderType(result["order_type"]),
                        quantity=Decimal(result["quantity"]),
                        price=Decimal(result["price"]) if result.get("price") else None,
                        stop_price=Decimal(result["stop_price"]) if result.get("stop_price") else None,
                        status=OrderStatus(result["status"]),
                        filled_quantity=Decimal(result.get("filled_quantity", "0")),
                        avg_fill_price=Decimal(result["avg_fill_price"]) if result.get("avg_fill_price") else None,
                        commission=Decimal(result.get("commission", "0")),
                        created_at=datetime.fromisoformat(result["created_at"]),
                        updated_at=datetime.fromisoformat(result["updated_at"])
                    )

        except Exception as e:
            self.logger.error(f"获取华泰订单状态失败: {str(e)}")
            return None

    async def get_positions(self) -> Dict[str, Position]:
        """获取华泰持仓"""
        await self.ensure_session_valid()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.session.access_token}"
            }
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.ssl_context),
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.get(
                    f"{self.base_url}/positions",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return {}
                    
                    result = await response.json()
                    positions = {}
                    
                    for pos_data in result.get("positions", []):
                        position = Position(
                            symbol=pos_data["symbol"],
                            quantity=Decimal(pos_data["quantity"]),
                            avg_cost=Decimal(pos_data["avg_cost"]),
                            market_value=Decimal(pos_data["market_value"]),
                            unrealized_pnl=Decimal(pos_data["unrealized_pnl"]),
                            realized_pnl=Decimal(pos_data.get("realized_pnl", "0")),
                            updated_at=datetime.fromisoformat(pos_data["updated_at"])
                        )
                        positions[position.symbol] = position
                    
                    return positions

        except Exception as e:
            self.logger.error(f"获取华泰持仓失败: {str(e)}")
            return {}

    async def get_account_info(self) -> AccountInfo:
        """获取华泰账户信息"""
        await self.ensure_session_valid()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.session.access_token}"
            }
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.ssl_context),
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.get(
                    f"{self.base_url}/account",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise Exception(f"获取账户信息失败: {response.status}")
                    
                    result = await response.json()
                    
                    # 获取持仓信息
                    positions = await self.get_positions()
                    
                    return AccountInfo(
                        account_id=result["account_id"],
                        total_value=Decimal(result["total_value"]),
                        available_cash=Decimal(result["available_cash"]),
                        used_margin=Decimal(result.get("used_margin", "0")),
                        positions=positions,
                        updated_at=datetime.fromisoformat(result["updated_at"])
                    )

        except Exception as e:
            self.logger.error(f"获取华泰账户信息失败: {str(e)}")
            raise

    async def get_trades(self, symbol: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[Trade]:
        """获取华泰成交记录"""
        await self.ensure_session_valid()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.session.access_token}"
            }
            
            params = {}
            if symbol:
                params["symbol"] = symbol
            if start_time:
                params["start_time"] = start_time.isoformat()
            if end_time:
                params["end_time"] = end_time.isoformat()
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.ssl_context),
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.get(
                    f"{self.base_url}/trades",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return []
                    
                    result = await response.json()
                    trades = []
                    
                    for trade_data in result.get("trades", []):
                        trade = Trade(
                            trade_id=trade_data["trade_id"],
                            order_id=trade_data["order_id"],
                            symbol=trade_data["symbol"],
                            side=OrderSide(trade_data["side"]),
                            quantity=Decimal(trade_data["quantity"]),
                            price=Decimal(trade_data["price"]),
                            commission=Decimal(trade_data.get("commission", "0")),
                            timestamp=datetime.fromisoformat(trade_data["timestamp"])
                        )
                        trades.append(trade)
                    
                    return trades

        except Exception as e:
            self.logger.error(f"获取华泰成交记录失败: {str(e)}")
            return []

    async def _refresh_token(self) -> bool:
        """刷新华泰令牌"""
        if not self.session or not self.session.refresh_token:
            return False

        try:
            refresh_data = {
                "refresh_token": self.session.refresh_token,
                "timestamp": int(time.time() * 1000)
            }
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.ssl_context),
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.post(
                    f"{self.base_url}/auth/refresh",
                    json=refresh_data
                ) as response:
                    if response.status != 200:
                        return False
                    
                    result = await response.json()
                    
                    # 更新会话信息
                    self.session.access_token = result.get("access_token")
                    self.session.expires_at = datetime.now() + timedelta(seconds=result.get("expires_in", 3600))
                    self.session.last_heartbeat = datetime.now()
                    
                    return True

        except Exception as e:
            self.logger.error(f"华泰令牌刷新失败: {str(e)}")
            return False


class LiveTradingEngine(BaseTradingEngine):
    """实盘交易引擎"""

    def __init__(self, broker_configs: List[BrokerConfig]):
        super().__init__(TradingMode.LIVE)
        
        self.broker_adapters: Dict[str, BrokerAdapter] = {}
        self.primary_broker: Optional[str] = None
        
        # 初始化券商适配器
        for config in broker_configs:
            if config.broker_name.lower() == "huatai":
                adapter = HuataiAdapter(config)
            else:
                raise ValueError(f"不支持的券商: {config.broker_name}")
            
            self.broker_adapters[config.broker_name] = adapter
            
            # 设置主要券商
            if not self.primary_broker:
                self.primary_broker = config.broker_name

    async def start(self):
        """启动实盘引擎"""
        await super().start()
        
        # 认证所有券商
        for broker_name, adapter in self.broker_adapters.items():
            try:
                await adapter.authenticate()
                self.logger.info(f"券商 {broker_name} 认证成功")
            except Exception as e:
                self.logger.error(f"券商 {broker_name} 认证失败: {str(e)}")

    async def place_order(self, order: Order) -> str:
        """实盘下单"""
        await self.validate_order(order)
        
        if not self.primary_broker or self.primary_broker not in self.broker_adapters:
            raise ValueError("没有可用的券商适配器")
        
        adapter = self.broker_adapters[self.primary_broker]
        
        try:
            # 通过券商API下单
            broker_order_id = await adapter.place_order(order)
            
            # 更新本地订单记录
            order.order_id = broker_order_id
            order.status = OrderStatus.SUBMITTED
            self.orders[broker_order_id] = order
            
            self.logger.info(f"实盘下单成功: {broker_order_id}")
            return broker_order_id
            
        except Exception as e:
            self.logger.error(f"实盘下单失败: {str(e)}")
            raise

    async def cancel_order(self, order_id: str) -> bool:
        """实盘撤单"""
        if not self.primary_broker or self.primary_broker not in self.broker_adapters:
            return False
        
        adapter = self.broker_adapters[self.primary_broker]
        
        try:
            success = await adapter.cancel_order(order_id)
            
            if success and order_id in self.orders:
                self.orders[order_id].status = OrderStatus.CANCELLED
                self.orders[order_id].updated_at = datetime.now()
            
            return success
            
        except Exception as e:
            self.logger.error(f"实盘撤单失败: {str(e)}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """获取实盘订单状态"""
        if not self.primary_broker or self.primary_broker not in self.broker_adapters:
            return None
        
        adapter = self.broker_adapters[self.primary_broker]
        
        try:
            order = await adapter.get_order_status(order_id)
            
            # 更新本地记录
            if order:
                self.orders[order_id] = order
            
            return order
            
        except Exception as e:
            self.logger.error(f"获取实盘订单状态失败: {str(e)}")
            return None

    async def get_positions(self) -> Dict[str, Position]:
        """获取实盘持仓"""
        if not self.primary_broker or self.primary_broker not in self.broker_adapters:
            return {}
        
        adapter = self.broker_adapters[self.primary_broker]
        
        try:
            positions = await adapter.get_positions()
            self.positions = positions
            return positions
            
        except Exception as e:
            self.logger.error(f"获取实盘持仓失败: {str(e)}")
            return {}

    async def get_account_info(self) -> AccountInfo:
        """获取实盘账户信息"""
        if not self.primary_broker or self.primary_broker not in self.broker_adapters:
            raise ValueError("没有可用的券商适配器")
        
        adapter = self.broker_adapters[self.primary_broker]
        
        try:
            account = await adapter.get_account_info()
            self.account = account
            return account
            
        except Exception as e:
            self.logger.error(f"获取实盘账户信息失败: {str(e)}")
            raise

    async def get_trades(self, symbol: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[Trade]:
        """获取实盘成交记录"""
        if not self.primary_broker or self.primary_broker not in self.broker_adapters:
            return []
        
        adapter = self.broker_adapters[self.primary_broker]
        
        try:
            trades = await adapter.get_trades(symbol, start_time, end_time)
            return trades
            
        except Exception as e:
            self.logger.error(f"获取实盘成交记录失败: {str(e)}")
            return []

    def switch_broker(self, broker_name: str) -> bool:
        """切换主要券商"""
        if broker_name not in self.broker_adapters:
            return False
        
        self.primary_broker = broker_name
        self.logger.info(f"切换到券商: {broker_name}")
        return True

    def get_broker_status(self) -> Dict[str, Any]:
        """获取券商状态"""
        status = {}
        
        for broker_name, adapter in self.broker_adapters.items():
            session = adapter.session
            status[broker_name] = {
                "is_active": session.is_active if session else False,
                "is_expired": session.is_expired if session else True,
                "needs_refresh": session.needs_refresh if session else True,
                "last_heartbeat": session.last_heartbeat.isoformat() if session and session.last_heartbeat else None
            }
        
        return status