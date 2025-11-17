export interface StockInfo {
  symbol: string
  name: string
  market: string
  industry?: string
  sector?: string
  market_cap?: number
  pe_ratio?: number
  pb_ratio?: number
  dividend_yield?: number
  current_price?: number
  change?: number
  change_percent?: number
  volume?: number
  turnover?: number
  updated_at: string
}

export interface MarketData {
  symbol: string
  name: string
  current_price: number
  open_price: number
  high_price: number
  low_price: number
  close_price: number
  volume: number
  turnover: number
  change: number
  change_percent: number
  timestamp: string
  kline_data?: KlineData[]
}

export interface KlineData {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface StockSearch {
  symbol: string
  name: string
  market: string
  type: string
}

export interface FinancialData {
  symbol: string
  report_date: string
  report_type: string
  revenue: number
  net_income: number
  total_assets: number
  total_liabilities: number
  shareholders_equity: number
  eps: number
  roe: number
  roa: number
}

export interface NewsItem {
  id: string
  title: string
  summary: string
  content: string
  source: string
  author?: string
  publish_time: string
  symbols?: string[]
  category: string
  url?: string
}

export interface AnalysisReport {
  id: string
  title: string
  symbol: string
  analyst: string
  institution: string
  rating: string
  target_price?: number
  summary: string
  publish_time: string
  report_type: string
}