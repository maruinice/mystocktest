export interface Order {
  order_id: string
  symbol: string
  code?: string
  name?: string
  side: 'buy' | 'sell'
  order_type: 'market' | 'limit'
  quantity: number
  price?: number
  avg_price?: number
  commission?: number
  filled_quantity: number
  status: 'pending' | 'filled' | 'cancelled' | 'rejected'
  created_at: string
  updated_at?: string
  filled_at?: string
}

export interface Position {
  symbol: string
  code?: string
  name?: string
  quantity: number
  available_quantity: number
  frozen_quantity?: number
  avg_cost: number
  last_price?: number
  market_value: number
  profit_loss?: number
  profit_loss_pct?: number
  unrealized_pnl?: number // 兼容旧字段
  unrealized_pnl_ratio?: number // 兼容旧字段
  cost_basis?: number
  updated_at: string
}

export interface Account {
  account_id: string
  total_assets: number
  available_cash: number
  frozen_cash: number
  market_value: number
  total_pnl: number
  total_pnl_ratio: number
  buying_power: number
  updated_at: string
}

export interface Trade {
  trade_id: string
  order_id: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  amount: number
  commission: number
  executed_at: string
}

export interface PlaceOrderRequest {
  symbol: string
  side: 'buy' | 'sell'
  order_type: 'market' | 'limit'
  quantity: number
  price?: number
}