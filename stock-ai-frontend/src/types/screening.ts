/**
 * 选股功能相关类型定义
 */

// 选股策略类型
export type StrategyType = 'fundamental' | 'technical' | 'mixed' | 'custom'

// 风险等级
export type RiskLevel = 'conservative' | 'moderate' | 'aggressive'

// 选股状态
export type ScreeningStatus = 'pending' | 'running' | 'completed' | 'failed'

// 选股策略
export interface ScreeningStrategy {
  id: number
  name: string
  code: string
  type: StrategyType
  description: string
  is_system: boolean
  usage_count: number
  success_rate?: number
  avg_return?: number
  created_at: string
}

// 选股指标
export interface ScreeningIndicator {
  code: string
  name: string
  unit: string
  range: [number, number]
}

// 指标分组
export interface IndicatorGroup {
  [groupName: string]: ScreeningIndicator[]
}

// 筛选条件值类型
export type ConditionValue = {
  min?: number
  max?: number
} | string[] | boolean

// 筛选条件
export interface ScreeningCondition {
  [indicatorCode: string]: ConditionValue
}

// 选股结果
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

// 选股执行结果
export interface ScreeningExecutionResult {
  task_id: string
  result_id: number
  total_stocks: number
  filtered_stocks: number
  execution_time: number
  results: ScreeningResult[]
}

// 选股详细结果
export interface ScreeningDetailResult {
  task_id: string
  strategy_name: string
  strategy_type: string
  screening_date: string
  status: ScreeningStatus
  total_stocks: number
  filtered_stocks: number
  execution_time: number
  results: ScreeningResult[]
  summary: {
    total_count: number
    avg_score: number
    industry_distribution: Record<string, number>
    market_distribution: Record<string, number>
    score_distribution: {
      excellent: number
      good: number
      average: number
      poor: number
    }
    avg_roe?: number
    avg_pe?: number
    avg_market_cap?: number
  }
  created_at: string
}

// 选股历史记录
export interface ScreeningHistory {
  task_id: string
  strategy_name: string
  strategy_type: string
  screening_date: string
  total_stocks: number
  filtered_stocks: number
  execution_time: number
  status: ScreeningStatus
  created_at: string
}

// 分页信息
export interface Pagination {
  page: number
  limit: number
  total: number
  pages: number
}

// 选股历史响应
export interface ScreeningHistoryResponse {
  list: ScreeningHistory[]
  pagination: Pagination
}

// 用户选股偏好
export interface UserPreferences {
  preferred_strategies: number[]
  default_conditions: Record<string, any>
  notification_settings: Record<string, any>
  risk_level: RiskLevel
  max_position_size: number
  stop_loss_rate: number
}

// 策略配置
export interface StrategyConfig {
  [key: string]: number | string | boolean
}

// 自定义策略创建参数
export interface CreateCustomStrategyParams {
  strategy_name: string
  strategy_type: StrategyType
  description?: string
  conditions: ScreeningCondition
  config?: StrategyConfig
}

// 自定义策略更新参数
export interface UpdateCustomStrategyParams {
  strategy_name?: string
  description?: string
  conditions?: ScreeningCondition
  config?: StrategyConfig
}

// 数据同步参数
export interface SyncDataParams {
  trade_date?: string
  ts_codes?: string[]
}

// 数据同步结果
export interface SyncDataResult {
  saved_count: number
  trade_date?: string
  period?: string
  stocks_count?: number
  calculated_count?: number
}

// 选股表单数据
export interface ScreeningFormData {
  strategy_id: number
  conditions: ScreeningCondition
}

// 条件编辑器项目
export interface ConditionItem {
  indicator: string
  operator: 'range' | 'in' | 'boolean'
  value: any
  enabled: boolean
}

// 选股组件状态
export interface ScreeningState {
  // 策略相关
  strategies: {
    system: ScreeningStrategy[]
    fundamental: ScreeningStrategy[]
    technical: ScreeningStrategy[]
    mixed: ScreeningStrategy[]
    custom: ScreeningStrategy[]
  }
  selectedStrategy?: ScreeningStrategy
  
  // 指标相关
  indicators: {
    fundamental: IndicatorGroup
    technical: IndicatorGroup
    market: IndicatorGroup
  }
  
  // 筛选条件
  conditions: ScreeningCondition
  conditionItems: ConditionItem[]
  
  // 执行状态
  isExecuting: boolean
  currentTask?: string
  
  // 结果相关
  results: ScreeningResult[]
  resultDetail?: ScreeningDetailResult
  
  // 历史记录
  history: ScreeningHistory[]
  historyPagination: Pagination
  
  // 用户偏好
  preferences: UserPreferences
  
  // 加载状态
  loading: {
    strategies: boolean
    indicators: boolean
    executing: boolean
    results: boolean
    history: boolean
    preferences: boolean
  }
}

// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
}

// 错误信息
export interface ScreeningError {
  code: string
  message: string
  details?: any
}