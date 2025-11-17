import { http } from '@/utils/request'
import type { StockInfo, MarketData, StockSearch } from '@/types/data'

export const dataApi = {
  // 获取股票列表
  getStockList(params?: {
    market?: string
    page?: number
    page_size?: number
  }): Promise<{
    data: {
      stocks: StockInfo[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }
  }> {
    return http.get('/data/stocks', { params })
  },

  // 获取股票行情
  getMarketData(symbol: string, params?: {
    period?: string
    start_date?: string
    end_date?: string
  }): Promise<{ data: MarketData }> {
    return http.get(`/data/market/${symbol}`, { params })
  },

  // 获取股票基本信息
  getStockInfo(symbol: string): Promise<{ data: StockInfo }> {
    return http.get(`/data/stock/${symbol}`)
  },

  // 搜索股票
  searchStocks(params: {
    keyword: string
    limit?: number
  }): Promise<{ data: StockSearch[] }> {
    return http.get('/data/search', { params })
  },

  // 获取财务数据
  getFinancialData(symbol: string, params?: {
    report_type?: string
    period?: string
  }): Promise<{ data: any }> {
    return http.get(`/data/financial/${symbol}`, { params })
  },

  // 获取新闻
  getNews(params?: {
    symbol?: string
    category?: string
    page?: number
    page_size?: number
  }): Promise<{
    data: {
      news: any[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }
  }> {
    return http.get('/data/news', { params })
  },

  // 获取分析报告
  getAnalysisReports(params?: {
    symbol?: string
    analyst?: string
    page?: number
    page_size?: number
  }): Promise<{
    data: {
      reports: any[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }
  }> {
    return http.get('/data/analysis', { params })
  },

  // 获取市场指标
  getMarketIndicators(): Promise<{ data: any }> {
    return http.get('/data/market-indicators')
  },

  // 获取市场概况
  getMarketOverview(): Promise<{ data: any }> {
    return http.get('/data/market-overview')
  },

  // 添加到关注列表
  addToWatchlist(symbol: string): Promise<void> {
    return http.post('/data/watchlist', { symbol })
  },

  // 从关注列表移除
  removeFromWatchlist(symbol: string): Promise<void> {
    return http.delete(`/data/watchlist/${symbol}`)
  },

  // 获取关注列表
  getWatchlist(): Promise<{ data: StockInfo[] }> {
    return http.get('/data/watchlist')
  }
}