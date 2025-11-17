/**
 * 选股功能API接口
 */

import request from '@/utils/request'

// 选股策略接口
export interface ScreeningStrategy {
  id: number
  name: string
  code: string
  type: 'fundamental' | 'technical' | 'mixed' | 'custom'
  description: string
  is_system: boolean
  usage_count: number
  success_rate?: number
  avg_return?: number
  created_at: string
}

// 选股指标接口
export interface ScreeningIndicator {
  code: string
  name: string
  unit: string
  range: [number, number]
}

// 筛选条件接口
export interface ScreeningCondition {
  [key: string]: {
    min?: number
    max?: number
  } | string[] | boolean
}

// 选股结果接口
export interface ScreeningResult {
  ts_code: string
  symbol: string
  name: string
  industry: string
  market: string
  close_price?: number
  change_pct?: number
  turnover_rate?: number
  pe?: number
  pb?: number
  market_cap?: number
  roe?: number
  revenue_growth?: number
  profit_growth?: number
  debt_ratio?: number
  current_ratio?: number
  quick_ratio?: number
  gross_margin?: number
  net_margin?: number
  roa?: number
  composite_score: number
  rank: number
}

// 选股执行结果接口
export interface ScreeningExecutionResult {
  task_id: string
  result_id: number
  total_stocks: number
  filtered_stocks: number
  execution_time: number
  results: ScreeningResult[]
}

// 选股历史接口
export interface ScreeningHistory {
  task_id: string
  strategy_name: string
  strategy_type: string
  screening_date: string
  total_stocks: number
  filtered_stocks: number
  execution_time: number
  status: string
  created_at: string
}

// 用户偏好接口
export interface UserPreferences {
  preferred_strategies: number[]
  default_conditions: Record<string, any>
  notification_settings: Record<string, any>
  risk_level: 'conservative' | 'moderate' | 'aggressive'
  max_position_size: number
  stop_loss_rate: number
}

/**
 * 获取选股策略列表
 */
export function getScreeningStrategies() {
  return request<{
    success: boolean
    data: {
      system: ScreeningStrategy[]
      fundamental: ScreeningStrategy[]
      technical: ScreeningStrategy[]
      mixed: ScreeningStrategy[]
      custom: ScreeningStrategy[]
    }
  }>({
    url: '/screening/strategies',
    method: 'GET'
  })
}

/**
 * 获取可用的筛选指标
 */
export function getScreeningIndicators() {
  return request<{
    success: boolean
    data: {
      fundamental: Record<string, ScreeningIndicator[]>
      technical: Record<string, ScreeningIndicator[]>
      market: Record<string, ScreeningIndicator[]>
    }
  }>({
    url: '/screening/indicators',
    method: 'GET'
  })
}

/**
 * 执行选股
 */
export function executeScreening(data: {
  strategy_id: number
  conditions?: ScreeningCondition
}) {
  return request<{
    success: boolean
    message: string
    data: ScreeningExecutionResult
  }>({
    url: '/screening/execute',
    method: 'POST',
    data
  })
}

/**
 * 获取选股结果
 */
export function getScreeningResult(taskId: string) {
  return request<{
    success: boolean
    data: {
      task_id: string
      strategy_name: string
      strategy_type: string
      screening_date: string
      status: string
      total_stocks: number
      filtered_stocks: number
      execution_time: number
      results: ScreeningResult[]
      summary: Record<string, any>
      created_at: string
    }
  }>({
    url: `/screening/results/${taskId}`,
    method: 'GET'
  })
}

/**
 * 创建自定义策略
 */
export function createCustomStrategy(data: {
  strategy_name: string
  strategy_type: string
  description?: string
  conditions: ScreeningCondition
  config?: Record<string, any>
}) {
  return request<{
    success: boolean
    message: string
    data: {
      strategy_id: number
      strategy_code: string
    }
  }>({
    url: '/screening/strategies/custom',
    method: 'POST',
    data
  })
}

/**
 * 更新自定义策略
 */
export function updateCustomStrategy(strategyId: number, data: {
  strategy_name?: string
  description?: string
  conditions?: ScreeningCondition
  config?: Record<string, any>
}) {
  return request<{
    success: boolean
    message: string
  }>({
    url: `/screening/strategies/${strategyId}`,
    method: 'PUT',
    data
  })
}

/**
 * 删除自定义策略
 */
export function deleteCustomStrategy(strategyId: number) {
  return request<{
    success: boolean
    message: string
  }>({
    url: `/screening/strategies/${strategyId}`,
    method: 'DELETE'
  })
}

/**
 * 获取选股历史
 */
export function getScreeningHistory(params: {
  page?: number
  limit?: number
}) {
  return request<{
    success: boolean
    data: {
      list: ScreeningHistory[]
      pagination: {
        page: number
        limit: number
        total: number
        pages: number
      }
    }
  }>({
    url: '/screening/history',
    method: 'GET',
    params
  })
}

/**
 * 获取用户选股偏好
 */
export function getUserPreferences() {
  return request<{
    success: boolean
    data: UserPreferences
  }>({
    url: '/screening/preferences',
    method: 'GET'
  })
}

/**
 * 保存用户选股偏好
 */
export function saveUserPreferences(data: UserPreferences) {
  return request<{
    success: boolean
    message: string
  }>({
    url: '/screening/preferences',
    method: 'POST',
    data
  })
}

/**
 * 同步股票基础信息
 */
export function syncStockBasic() {
  return request<{
    success: boolean
    message: string
    data: {
      saved_count: number
      total_stocks: number
    }
  }>({
    url: '/screening/data/sync-stock-basic',
    method: 'POST'
  })
}

/**
 * 同步日线行情数据
 */
export function syncDailyQuotes(data?: {
  trade_date?: string
  ts_codes?: string[]
}) {
  return request<{
    success: boolean
    message: string
    data: {
      saved_count: number
      trade_date: string
      stocks_count: number
    }
  }>({
    url: '/screening/data/sync-quotes',
    method: 'POST',
    data
  })
}

/**
 * 同步财务指标数据
 */
export function syncFinancialData(data?: {
  period?: string
  ts_codes?: string[]
}) {
  return request<{
    success: boolean
    message: string
    data: {
      saved_count: number
      period: string
      stocks_count: number
    }
  }>({
    url: '/screening/data/sync-financial',
    method: 'POST',
    data
  })
}

/**
 * 计算技术指标
 */
export function calculateTechnicalIndicators(data?: {
  trade_date?: string
  ts_codes?: string[]
}) {
  return request<{
    success: boolean
    message: string
    data: {
      calculated_count: number
      trade_date: string
    }
  }>({
    url: '/screening/data/calculate-technical',
    method: 'POST',
    data
  })
}