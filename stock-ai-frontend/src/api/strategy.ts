import { http } from '@/utils/request'
import type {
  Strategy,
  BacktestResult,
  CreateStrategyRequest,
  CreateStrategyResponse,
  GetActiveStrategiesResponse,
  GetBacktestsResponse
} from '@/types/strategy'

export const strategyApi = {
  // 获取策略列表
  getStrategies(params?: { 
    page?: number
    size?: number
    keyword?: string
    status?: string
    category?: string
    risk_level?: string
  }): Promise<{ 
    data: { 
      strategies: Strategy[]
      total: number
      page: number
      page_size: number
    } 
  }> {
    return http.get('/strategy/list', { params })
  },

  // 获取正在运行的策略列表
  getActiveStrategies(): Promise<GetActiveStrategiesResponse> {
    return http.get('/strategy/active')
  },

  // 创建策略
  createStrategy(payload: CreateStrategyRequest): Promise<CreateStrategyResponse> {
    return http.post('/strategy', payload)
  },

  // 更新策略
  updateStrategy(strategyId: string, payload: Partial<Strategy>): Promise<{ data: Strategy }> {
    return http.put(`/strategy/${strategyId}`, payload)
  },

  // 复制策略
  copyStrategy(strategyId: string): Promise<{ data: Strategy }> {
    return http.post(`/strategy/${strategyId}/copy`)
  },

  // 启动策略
  startStrategy(strategyId: string): Promise<{ data: { strategy_id: string; status: string } }> {
    return http.post(`/strategy/${strategyId}/start`)
  },

  // 暂停策略
  pauseStrategy(strategyId: string): Promise<{ data: { strategy_id: string; status: string } }> {
    return http.post(`/strategy/${strategyId}/pause`)
  },

  // 停止策略
  stopStrategy(strategyId: string): Promise<{ data: { strategy_id: string; status: string } }> {
    return http.post(`/strategy/${strategyId}/stop`)
  },

  // 删除策略
  deleteStrategy(strategyId: string): Promise<{ data: { strategy_id: string; deleted: boolean } }> {
    return http.delete(`/strategy/${strategyId}`)
  },

  // 批量删除策略
  deleteStrategies(strategyIds: string[]): Promise<{ data: { deleted_count: number } }> {
    return http.post('/strategy/batch-delete', { strategy_ids: strategyIds })
  },

  // 导出策略
  exportStrategy(strategyId: string): Promise<{ data: Strategy }> {
    return http.get(`/strategy/${strategyId}/export`)
  },

  // 批量导出策略
  exportStrategies(strategyIds: string[]): Promise<{ data: Strategy[] }> {
    return http.post('/strategy/batch-export', { strategy_ids: strategyIds })
  },

  // 导入策略
  importStrategies(strategies: Strategy[]): Promise<{ data: { imported_count: number } }> {
    return http.post('/strategy/import', { strategies })
  },

  // 运行回测
  runBacktest(payload: {
    strategy_id: string
    start_date: string
    end_date: string
    initial_capital?: number
    parameters?: Record<string, any>
    stock_pool?: string[]
    benchmark?: string
  }): Promise<{ data: BacktestResult }> {
    return http.post('/strategy/backtest', payload)
  },

  // 获取回测历史
  getBacktests(params?: {
    strategy_name?: string
    start_date?: string
    end_date?: string
    page?: number
    size?: number
  }): Promise<GetBacktestsResponse> {
    return http.get('/strategy/backtests', { params })
  },

  // 获取回测结果
  getBacktestResult(backtest_id: string): Promise<{ data: BacktestResult }> {
    return http.get(`/strategy/backtest/${backtest_id}`)
  },

  // 获取回测历史
  getBacktestHistory(params?: {
    strategy_id?: string
    page?: number
    size?: number
  }): Promise<{ 
    data: { 
      success: boolean
      data: {
        results: any[]
        total: number
        page: number
        size: number
        pages: number
      }
    } 
  }> {
    return http.get('/strategy/backtest/history', { params })
  },

  // 获取回测详情
  getBacktestDetail(backtest_id: string): Promise<{ 
    data: { 
      success: boolean
      data: BacktestResult
    } 
  }> {
    return http.get(`/strategy/backtest/${backtest_id}`)
  },

  // 获取策略性能
  getPerformance(strategyId: string, period?: string): Promise<{ 
    data: { 
      total_return: number
      sharpe_ratio?: number
      max_drawdown?: number
      win_rate?: number
      [key: string]: any
    } 
  }> {
    return http.get(`/strategy/${strategyId}/performance`, { params: { period } })
  },

  // 获取交易信号
  getTradingSignals(params?: {
    codes?: string[]
    strategy_names?: string[]
    signal_types?: string[]
    start_time?: string
    end_time?: string
  }): Promise<{ data: any[] }> {
    return http.get('/strategy/signals', { params })
  },

  // 获取最新信号
  getLatestSignals(limit?: number, min_confidence?: number): Promise<{ data: any[] }> {
    return http.get('/strategy/signals/latest', { 
      params: { limit, min_confidence } 
    })
  },

  // 验证策略代码
  validateCode(code: string): Promise<{ 
    data: { 
      valid: boolean
      errors?: string[]
      warnings?: string[]
    } 
  }> {
    return http.post('/strategy/validate-code', { code })
  },

  // 格式化策略代码
  formatCode(code: string): Promise<{ data: { formatted_code: string } }> {
    return http.post('/strategy/format-code', { code })
  },

  // AI生成策略
  generateStrategy(prompt: string, options?: {
    strategy_type?: string
    risk_level?: string
    indicators?: string[]
  }): Promise<{ data: Strategy }> {
    return http.post('/strategy/ai-generate', { prompt, options })
  }
}

export default strategyApi