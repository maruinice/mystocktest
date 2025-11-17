import { http } from '@/utils/request'

// AI决策相关接口
export const aiDecisionApi = {
  // 获取决策列表
  getDecisions(params?: {
    status?: string
    symbol?: string
    page?: number
    page_size?: number
  }): Promise<{
    data: {
      decisions: any[]
      total: number
      page: number
      page_size: number
    }
  }> {
    return http.get('/ai-decision/decisions', { params })
  },

  // 生成新决策
  generateDecision(data: {
    symbol?: string
    strategy_type?: string
    force_analysis?: boolean
  }): Promise<{ data: any }> {
    return http.post('/ai-decision/generate', data)
  },

  // 执行决策
  executeDecision(decisionId: string): Promise<{ data: any }> {
    return http.post(`/ai-decision/execute/${decisionId}`)
  },

  // 获取决策详情
  getDecisionDetail(decisionId: string): Promise<{ data: any }> {
    return http.get(`/ai-decision/decisions/${decisionId}`)
  },

  // 取消决策
  cancelDecision(decisionId: string): Promise<{ data: any }> {
    return http.delete(`/ai-decision/decisions/${decisionId}`)
  }
}

// 风险控制相关接口
export const riskControlApi = {
  // 获取风险概览
  getRiskOverview(): Promise<{
    data: {
      risk_level: string
      var_value: number
      max_drawdown: number
      active_alerts: number
    }
  }> {
    return http.get('/risk-control/overview')
  },

  // 获取风险指标
  getRiskMetrics(): Promise<{
    data: {
      sharpe_ratio: number
      volatility: number
      beta: number
      information_ratio: number
    }
  }> {
    return http.get('/risk-control/metrics')
  },

  // 获取风险警报
  getRiskAlerts(params?: {
    level?: string
    status?: string
    page?: number
    page_size?: number
  }): Promise<{
    data: {
      alerts: any[]
      total: number
    }
  }> {
    return http.get('/risk-control/alerts', { params })
  },

  // 运行风险检查
  runRiskCheck(): Promise<{ data: any }> {
    return http.post('/risk-control/check')
  },

  // 获取风险设置
  getRiskSettings(): Promise<{ data: any }> {
    return http.get('/risk-control/settings')
  },

  // 更新风险设置
  updateRiskSettings(data: {
    max_position?: number
    stop_loss?: number
    var_threshold?: number
    auto_stop_loss?: boolean
    risk_alert?: boolean
  }): Promise<{ data: any }> {
    return http.put('/risk-control/settings', data)
  },

  // 处理风险警报
  handleAlert(alertId: string, action: string): Promise<{ data: any }> {
    return http.post(`/risk-control/alerts/${alertId}/handle`, { action })
  }
}

// LLM网关相关接口
export const llmGatewayApi = {
  // 聊天对话
  chat(data: {
    messages: Array<{ role: string; content: string }>
    model?: string
    max_tokens?: number
    temperature?: number
    stream?: boolean
    provider?: string
  }): Promise<{ data: any }> {
    return http.post('/llm/chat', data)
  },

  // 获取可用模型
  getModels(): Promise<{
    data: {
      models: Array<{
        id: string
        name: string
        provider: string
        description: string
        max_tokens: number
        available: boolean
      }>
    }
  }> {
    return http.get('/llm/models')
  },

  // 获取提供商列表
  getProviders(): Promise<{
    data: {
      providers: Array<{
        name: string
        enabled: boolean
        priority: number
        rate_limit: number
      }>
    }
  }> {
    return http.get('/llm/providers')
  },

  // 添加提供商
  addProvider(data: {
    name: string
    config: {
      api_key: string
      base_url?: string
      enabled?: boolean
      priority?: number
      rate_limit?: number
    }
  }): Promise<{ data: any }> {
    return http.post('/llm/providers', data)
  },

  // 更新提供商配置
  updateProvider(name: string, config: any): Promise<{ data: any }> {
    return http.put(`/llm/providers/${name}`, { config })
  },

  // 删除提供商
  deleteProvider(name: string): Promise<{ data: any }> {
    return http.delete(`/llm/providers/${name}`)
  },

  // 测试提供商连接
  testProvider(name: string): Promise<{ data: any }> {
    return http.post(`/llm/providers/${name}/test`)
  }
}

// 多模型组合相关接口
export const multiModelApi = {
  // 获取模型列表
  getModels(params?: {
    status?: string
    type?: string
    page?: number
    page_size?: number
  }): Promise<{
    data: {
      models: any[]
      total: number
    }
  }> {
    return http.get('/v1/portfolio/models', { params })
  },

  // 创建模型
  createModel(data: {
    name: string
    type: string
    description?: string
    config?: any
  }): Promise<{ data: any }> {
    return http.post('/v1/portfolio/models', data)
  },

  // 训练模型
  trainModel(modelId: string, data?: any): Promise<{ data: any }> {
    return http.post(`/v1/portfolio/models/${modelId}/train`, data)
  },

  // 启用/停用模型
  toggleModel(modelId: string, enabled: boolean): Promise<{ data: any }> {
    return http.put(`/v1/portfolio/models/${modelId}/toggle`, { enabled })
  },

  // 获取模型组合列表
  getPortfolios(): Promise<{
    data: {
      portfolios: any[]
    }
  }> {
    return http.get('/v1/portfolio/portfolios')
  },

  // 创建模型组合
  createPortfolio(data: {
    name: string
    model_ids: string[]
    weight_strategy: string
    config?: any
  }): Promise<{ data: any }> {
    return http.post('/v1/portfolio/portfolios', data)
  },

  // 启动/停止组合
  togglePortfolio(portfolioId: string, active: boolean): Promise<{ data: any }> {
    return http.put(`/v1/portfolio/portfolios/${portfolioId}/toggle`, { active })
  },

  // 获取组合绩效
  getPortfolioPerformance(portfolioId: string, params?: {
    start_date?: string
    end_date?: string
  }): Promise<{ data: any }> {
    return http.get(`/v1/portfolio/portfolios/${portfolioId}/performance`, { params })
  }
}

export default {
  aiDecisionApi,
  riskControlApi,
  llmGatewayApi,
  multiModelApi
}