"""
多模型组合API

提供多模型组合管理的RESTful API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import logging

from ..services.multi_model_portfolio import (
    MultiModelPortfolio, ModelAccount, Transaction, Position,
    TransactionType, FeeConfig, SlippageConfig
)
from ..services.performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

# 初始化组合管理器和性能分析器
portfolio_manager = MultiModelPortfolio()
performance_analyzer = PerformanceAnalyzer(portfolio_manager)

router = APIRouter(prefix="/api/v1/portfolio", tags=["多模型组合"])


# Pydantic模型定义
class CreateAccountRequest(BaseModel):
    model_id: str = Field(..., description="模型ID")
    initial_cash: float = Field(1000000.0, description="初始资金", gt=0)


class TradeRequest(BaseModel):
    model_id: str = Field(..., description="模型ID")
    symbol: str = Field(..., description="股票代码")
    quantity: float = Field(..., description="数量", gt=0)
    price: float = Field(..., description="价格", gt=0)
    is_buy: bool = Field(..., description="是否买入")
    avg_volume: Optional[float] = Field(None, description="平均成交量")


class UpdatePricesRequest(BaseModel):
    prices: Dict[str, float] = Field(..., description="价格字典")


class PerformanceRequest(BaseModel):
    model_id: str = Field(..., description="模型ID")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    benchmark_returns: Optional[List[float]] = Field(None, description="基准收益")


class FeeConfigRequest(BaseModel):
    commission_rate: float = Field(0.0003, description="佣金费率")
    stamp_tax_rate: float = Field(0.001, description="印花税费率")
    transfer_fee_rate: float = Field(0.00002, description="过户费费率")
    min_commission: float = Field(5.0, description="最低佣金")


class SlippageConfigRequest(BaseModel):
    fixed_slippage_bp: float = Field(7.5, description="固定滑点(bp)")
    liquidity_factor: float = Field(1.0, description="流动性因子")
    max_slippage_bp: float = Field(50.0, description="最大滑点")


# API接口
@router.post("/accounts", summary="创建模型账户")
async def create_account(request: CreateAccountRequest):
    """创建新的模型账户"""
    try:
        account = portfolio_manager.create_account(
            model_id=request.model_id,
            initial_cash=Decimal(str(request.initial_cash))
        )
        
        return {
            "success": True,
            "message": f"成功创建模型账户: {request.model_id}",
            "data": {
                "model_id": account.model_id,
                "initial_cash": float(account.initial_cash),
                "cash_balance": float(account.cash_balance),
                "created_at": account.created_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建账户失败: {e}")
        raise HTTPException(status_code=500, detail="创建账户失败")


@router.get("/accounts", summary="获取所有账户")
async def get_all_accounts():
    """获取所有模型账户"""
    try:
        accounts_data = []
        for model_id, account in portfolio_manager.accounts.items():
            accounts_data.append({
                "model_id": model_id,
                "cash_balance": float(account.cash_balance),
                "market_value": float(account.get_total_market_value()),
                "total_assets": float(account.get_total_assets()),
                "total_pnl": float(account.get_total_pnl()),
                "return_rate": float(account.get_return_rate()),
                "positions_count": len(account.positions),
                "transactions_count": len(account.transactions),
                "created_at": account.created_at.isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "total_accounts": len(accounts_data),
                "accounts": accounts_data
            }
        }
    except Exception as e:
        logger.error(f"获取账户列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取账户列表失败")


@router.get("/accounts/{model_id}", summary="获取指定账户")
async def get_account(model_id: str):
    """获取指定模型账户信息"""
    try:
        account = portfolio_manager.get_account(model_id)
        if not account:
            raise HTTPException(status_code=404, detail=f"账户不存在: {model_id}")
        
        return {
            "success": True,
            "data": {
                "model_id": account.model_id,
                "cash_balance": float(account.cash_balance),
                "initial_cash": float(account.initial_cash),
                "market_value": float(account.get_total_market_value()),
                "total_assets": float(account.get_total_assets()),
                "total_pnl": float(account.get_total_pnl()),
                "return_rate": float(account.get_return_rate()),
                "positions_count": len(account.positions),
                "transactions_count": len(account.transactions),
                "created_at": account.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取账户信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取账户信息失败")


@router.post("/trades", summary="执行交易")
async def execute_trade(request: TradeRequest):
    """执行交易操作"""
    try:
        transaction = portfolio_manager.execute_trade(
            model_id=request.model_id,
            symbol=request.symbol,
            quantity=Decimal(str(request.quantity)),
            price=Decimal(str(request.price)),
            is_buy=request.is_buy,
            avg_volume=Decimal(str(request.avg_volume)) if request.avg_volume else None
        )
        
        return {
            "success": True,
            "message": f"交易执行成功",
            "data": {
                "transaction_id": transaction.transaction_id,
                "model_id": transaction.model_id,
                "symbol": transaction.symbol,
                "quantity": float(transaction.quantity),
                "price": float(transaction.price),
                "amount": float(transaction.amount),
                "transaction_type": transaction.transaction_type.value,
                "commission": float(transaction.commission),
                "stamp_tax": float(transaction.stamp_tax),
                "transfer_fee": float(transaction.transfer_fee),
                "slippage": float(transaction.slippage),
                "total_cost": float(transaction.total_cost),
                "timestamp": transaction.timestamp.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"执行交易失败: {e}")
        raise HTTPException(status_code=500, detail="执行交易失败")


@router.put("/prices", summary="更新市场价格")
async def update_prices(request: UpdatePricesRequest):
    """更新市场价格"""
    try:
        prices_decimal = {symbol: Decimal(str(price)) for symbol, price in request.prices.items()}
        portfolio_manager.update_market_prices(prices_decimal)
        
        return {
            "success": True,
            "message": f"成功更新 {len(request.prices)} 个股票价格",
            "data": {
                "updated_symbols": list(request.prices.keys()),
                "update_time": datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception as e:
        logger.error(f"更新价格失败: {e}")
        raise HTTPException(status_code=500, detail="更新价格失败")


@router.get("/summary", summary="获取组合摘要")
async def get_portfolio_summary():
    """获取投资组合摘要"""
    try:
        summary = portfolio_manager.get_portfolio_summary()
        
        # 将Decimal转换为float
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, Decimal):
                return float(obj)
            else:
                return obj
        
        summary_converted = convert_decimals(summary)
        
        return {
            "success": True,
            "data": summary_converted
        }
    except Exception as e:
        logger.error(f"获取组合摘要失败: {e}")
        raise HTTPException(status_code=500, detail="获取组合摘要失败")


@router.get("/accounts/{model_id}/positions", summary="获取持仓")
async def get_model_positions(model_id: str):
    """获取指定模型的持仓"""
    try:
        positions = portfolio_manager.get_model_positions(model_id)
        
        positions_data = []
        for symbol, position in positions.items():
            positions_data.append({
                "symbol": symbol,
                "quantity": float(position.quantity),
                "avg_cost": float(position.avg_cost),
                "market_value": float(position.market_value),
                "last_price": float(position.last_price),
                "unrealized_pnl": float(position.unrealized_pnl),
                "realized_pnl": float(position.realized_pnl)
            })
        
        return {
            "success": True,
            "data": {
                "model_id": model_id,
                "positions_count": len(positions_data),
                "positions": positions_data
            }
        }
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(status_code=500, detail="获取持仓失败")


@router.get("/accounts/{model_id}/transactions", summary="获取交易记录")
async def get_model_transactions(
    model_id: str,
    limit: Optional[int] = Query(50, description="记录数量限制", ge=1, le=1000)
):
    """获取指定模型的交易记录"""
    try:
        transactions = portfolio_manager.get_model_transactions(model_id, limit)
        
        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                "transaction_id": transaction.transaction_id,
                "symbol": transaction.symbol,
                "quantity": float(transaction.quantity),
                "price": float(transaction.price),
                "amount": float(transaction.amount),
                "transaction_type": transaction.transaction_type.value,
                "commission": float(transaction.commission),
                "stamp_tax": float(transaction.stamp_tax),
                "transfer_fee": float(transaction.transfer_fee),
                "slippage": float(transaction.slippage),
                "total_cost": float(transaction.total_cost),
                "timestamp": transaction.timestamp.isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "model_id": model_id,
                "transactions_count": len(transactions_data),
                "transactions": transactions_data
            }
        }
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        raise HTTPException(status_code=500, detail="获取交易记录失败")


@router.delete("/accounts/{model_id}", summary="删除账户")
async def delete_account(model_id: str):
    """删除指定模型账户"""
    try:
        if model_id not in portfolio_manager.accounts:
            raise HTTPException(status_code=404, detail=f"账户不存在: {model_id}")
        
        del portfolio_manager.accounts[model_id]
        
        return {
            "success": True,
            "message": f"成功删除账户: {model_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除账户失败: {e}")
        raise HTTPException(status_code=500, detail="删除账户失败")


@router.get("/health", summary="健康检查")
async def health_check():
    """API健康检查"""
    return {
        "success": True,
        "message": "多模型组合API运行正常",
        "data": {
            "total_accounts": len(portfolio_manager.accounts),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }








