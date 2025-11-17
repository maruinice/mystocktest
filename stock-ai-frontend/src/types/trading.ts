export interface Order {
  order_id: string
  symbol: string
  side: 'buy' | 'sell'
  order_type: 'market' | 'limit'
  quantity: number
  price?: number
  filled_quantity: number
  status: 'pending' | 'filled' | 'cancelled' | 'rejected'
  created_at: string
  updated_at?: string
}

export interface Position {
  symbol: string
  quantity: number
  available_quantity: number
  avg_cost: number
  market_value: number
  unrealized_pnl: number
  unrealized_pnl_ratio: number
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