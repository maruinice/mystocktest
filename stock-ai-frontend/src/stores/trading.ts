import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { tradingApi } from '@/api/trading'
import type { Order, Position, Account } from '@/types/trading'

export const useTradingStore = defineStore('trading', () => {
  // 状态
  const orders = ref<Order[]>([])
  const positions = ref<Position[]>([])
  const account = ref<Account | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const totalAssets = computed(() => account.value?.total_assets || 0)
  const availableCash = computed(() => account.value?.available_cash || 0)
  const marketValue = computed(() => account.value?.market_value || 0)
  const totalPnl = computed(() => account.value?.total_pnl || 0)
  const totalPnlRatio = computed(() => account.value?.total_pnl_ratio || 0)

  const pendingOrders = computed(() => 
    orders.value.filter(order => order.status === 'pending')
  )

  const filledOrders = computed(() => 
    orders.value.filter(order => order.status === 'filled')
  )

  // 获取订单列表
  const fetchOrders = async (params?: {
    status?: string
    symbol?: string
    page?: number
    page_size?: number
  }) => {
    loading.value = true
    error.value = null
    try {
      const response = await tradingApi.getOrders(params)
      orders.value = response.data.orders
      return response
    } catch (err: any) {
      error.value = err.message || '获取订单失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取持仓列表
  const fetchPositions = async (symbol?: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await tradingApi.getPositions(symbol)
      positions.value = response.data
      return response
    } catch (err: any) {
      error.value = err.message || '获取持仓失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取账户信息
  const fetchAccount = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await tradingApi.getAccount()
      account.value = response.data
      return response
    } catch (err: any) {
      error.value = err.message || '获取账户信息失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 下单
  const placeOrder = async (orderData: {
    symbol: string
    side: 'buy' | 'sell'
    order_type: 'market' | 'limit'
    quantity: number
    price?: number
  }) => {
    loading.value = true
    error.value = null
    try {
      const response = await tradingApi.placeOrder(orderData)
      // 刷新订单列表
      await fetchOrders()
      return response
    } catch (err: any) {
      error.value = err.message || '下单失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 撤单
  const cancelOrder = async (orderId: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await tradingApi.cancelOrder(orderId)
      // 刷新订单列表
      await fetchOrders()
      return response
    } catch (err: any) {
      error.value = err.message || '撤单失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 清除错误
  const clearError = () => {
    error.value = null
  }

  // 初始化数据
  const initialize = async () => {
    try {
      await Promise.all([
        fetchAccount(),
        fetchOrders(),
        fetchPositions()
      ])
    } catch (error) {
      console.error('Trading store initialization failed:', error)
    }
  }

  return {
    // 状态
    orders: readonly(orders),
    positions: readonly(positions),
    account: readonly(account),
    loading: readonly(loading),
    error: readonly(error),
    
    // 计算属性
    totalAssets,
    availableCash,
    marketValue,
    totalPnl,
    totalPnlRatio,
    pendingOrders,
    filledOrders,
    
    // 方法
    fetchOrders,
    fetchPositions,
    fetchAccount,
    placeOrder,
    cancelOrder,
    clearError,
    initialize
  }
})