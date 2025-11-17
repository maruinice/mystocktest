import { http } from '@/utils/request'
import type { Order, Position, Account, Trade } from '@/types/trading'

export const tradingApi = {
  // 下单
  placeOrder(data: {
    symbol: string
    side: 'buy' | 'sell'
    order_type: 'market' | 'limit'
    quantity: number
    price?: number
  }): Promise<{ data: Order }> {
    return http.post('/trade/order', data)
  },

  // 撤单
  cancelOrder(orderId: string): Promise<{ data: { order_id: string; status: string } }> {
    return http.delete(`/trade/order/${orderId}`)
  },

  // 获取订单列表
  getOrders(params?: {
    status?: string
    symbol?: string
    page?: number
    page_size?: number
  }): Promise<{
    data: {
      orders: Order[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }
  }> {
    return http.get('/trade/orders', { params })
  },

  // 获取持仓列表
  getPositions(symbol?: string): Promise<{ data: Position[] }> {
    const params = symbol ? { symbol } : undefined
    return http.get('/trade/positions', { params })
  },

  // 获取账户信息
  getAccount(): Promise<{ data: Account }> {
    return http.get('/trade/account')
  },

  // 获取成交记录
  getTrades(params?: {
    symbol?: string
    start_date?: string
    end_date?: string
    page?: number
    page_size?: number
  }): Promise<{
    data: {
      trades: Trade[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }
  }> {
    return http.get('/trade/trades', { params })
  },

  // 健康检查
  healthCheck(): Promise<{
    data: {
      service: string
      status: string
      timestamp: string
    }
  }> {
    return http.get('/trade/health')
  }
}