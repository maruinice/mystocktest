// 策略相关类型定义

// 策略状态枚举
export type StrategyStatus = 'draft' | 'active' | 'paused' | 'stopped' | 'error'

// 策略类型枚举
export type StrategyCategory = 
  | 'trend_following'    // 趋势跟踪
  | 'mean_reversion'     // 均值回归
  | 'momentum'           // 动量策略
  | 'arbitrage'          // 套利策略
  | 'multi_factor'       // 多因子策略
  | 'volatility'         // 波动率策略
  | 'custom'             // 自定义策略

// 风险等级枚举
export type RiskLevel = 'low' | 'medium' | 'high'

// 信号类型枚举
export type SignalType = 'buy' | 'sell' | 'hold'

// 交易条件类型
export interface TradingCondition {
  type: 'indicator' | 'price' | 'volume' | 'custom' | 'risk'
  description: string
  operator?: 'greater_than' | 'less_than' | 'equal' | 'cross_above' | 'cross_below' | 'trigger'
  indicator?: string
  comparison?: string
  value?: string | number
  params?: Record<string, any>
}

// 策略接口
export interface Strategy {
  strategy_id: string
  name: string
  display_name?: string
  description: string
  category: StrategyCategory
  risk_level: RiskLevel
  status: StrategyStatus
  author?: string
  min_capital?: number
  
  // 策略配置
  parameters?: Record<string, any>
  indicators?: string[]
  indicator_params?: Record<string, Record<string, number>>
  
  // 交易规则
  buy_conditions?: TradingCondition[]
  sell_conditions?: TradingCondition[]
  risk_controls?: {
    stop_loss?: number
    take_profit?: number
    position_size?: number
    max_positions?: number
    max_drawdown?: number
    commission?: number
  }
  
  // 策略代码
  code?: string
  
  // 性能指标
  performance?: number
  sharpe_ratio?: number
  max_drawdown?: number
  win_rate?: number
  total_trades?: number
  backtest_count?: number
  last_backtest_date?: string
  
  // 时间戳
  created_at: string
  updated_at?: string
  last_run_at?: string
}

// 回测结果接口
export interface BacktestResult {
  backtest_id: string
  user_id?: string
  strategy_id?: string
  strategy_name: string
  
  // 回测配置
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  parameters?: Record<string, any>
  stock_pool?: string[]
  benchmark?: string
  
  // 收益指标
  total_return: number
  annualized_return: number
  benchmark_return: number
  alpha: number
  beta: number
  
  // 风险指标
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown: number
  volatility: number
  
  // 交易指标
  win_rate: number
  profit_factor: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  avg_win: number
  avg_loss: number
  largest_win: number
  largest_loss: number
  
  // 详细数据
  equity_curve?: Array<{
    date: string
    value: number
    return: number
  }>
  trades?: Array<{
    trade_id: string
    date: string
    code: string
    name: string
    side: 'buy' | 'sell'
    quantity: number
    price: number
    amount: number
    commission: number
    profit_loss: number
  }>
  
  // 状态和时间
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
}

// 交易信号接口
export interface TradingSignal {
  signal_id: string
  user_id: string
  strategy_name: string
  code: string
  name: string
  signal_type: SignalType
  confidence: number
  target_price: number
  stop_loss?: number
  take_profit?: number
  position_size: number
  reason: string
  generated_at: string
  expires_at?: string
  is_executed: boolean
  executed_at?: string
}

// 策略模板接口
export interface StrategyTemplate {
  name: string
  display_name: string
  description: string
  category: StrategyCategory
  risk_level: RiskLevel
  parameter_schema: Record<string, any>
  default_parameters: Record<string, any>
  min_capital: number
  supported_markets: string[]
  code_template: string
}

// API请求/响应类型
export interface CreateStrategyRequest {
  name: string
  description: string
  category: StrategyCategory
  risk_level: RiskLevel
  author?: string
  parameters?: Record<string, any>
  code?: string
}

export interface CreateStrategyResponse {
  data: Strategy
}

export interface GetStrategiesResponse {
  data: {
    strategies: Strategy[]
    total: number
    page: number
    page_size: number
  }
}

export interface GetActiveStrategiesResponse {
  data: Strategy[]
}

export interface GetBacktestsResponse {
  data: BacktestResult[]
}

export interface RunBacktestRequest {
  strategy_id: string
  start_date: string
  end_date: string
  initial_capital?: number
  parameters?: Record<string, any>
  stock_pool?: string[]
  benchmark?: string
}

export interface GetTradingSignalsRequest {
  codes?: string[]
  strategy_names?: string[]
  signal_types?: SignalType[]
  start_time?: string
  end_time?: string
}

// 策略性能指标
export interface PerformanceMetrics {
  period: string
  start_date: string
  end_date: string
  total_return: number
  annualized_return: number
  volatility: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  profit_factor: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  daily_returns: Array<{
    date: string
    return: number
  }>
  strategy_name?: string
  benchmark_return?: number
  alpha?: number
  beta?: number
}

// 策略验证结果
export interface CodeValidationResult {
  valid: boolean
  errors?: string[]
  warnings?: string[]
  suggestions?: string[]
}

// AI生成策略选项
export interface AIGenerateOptions {
  strategy_type?: StrategyCategory
  risk_level?: RiskLevel
  indicators?: string[]
  market_type?: string
  investment_style?: string
}

// 导出类型
export type {
  StrategyStatus,
  StrategyCategory,
  RiskLevel,
  SignalType
}