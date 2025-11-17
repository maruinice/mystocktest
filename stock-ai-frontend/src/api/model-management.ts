import request from '@/utils/request'

// 模型类型枚举
export enum ModelType {
  DEEPSEEK = 'DeepSeek',
  OPENAI = 'ChatGPT', 
  CLAUDE = 'Claude',
  LLAMA = 'Llama',
  CUSTOM = 'Custom'
}

// 权重策略枚举
export enum WeightStrategy {
  EQUAL_WEIGHT = 'equal_weight',
  ACCURACY_WEIGHT = 'accuracy_weight',
  MANUAL_WEIGHT = 'manual_weight',
  DYNAMIC_WEIGHT = 'dynamic_weight',
  PERFORMANCE_WEIGHT = 'performance_weight'
}

// 投票方法枚举
export enum VotingMethod {
  MAJORITY = 'majority',
  WEIGHTED = 'weighted',
  CONFIDENCE = 'confidence',
  THRESHOLD = 'threshold'
}

// 融合策略枚举（保留用于前端UI，但后端使用VotingMethod）
export enum FusionStrategy {
  WEIGHTED_VOTING = 'weighted',
  MAJORITY_VOTING = 'majority',
  CONFIDENCE_BASED = 'confidence',
  THRESHOLD_BASED = 'threshold'
}

// 模型状态枚举
export enum ModelStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  TRAINING = 'training',
  ERROR = 'error'
}

// 模型接口类型定义
export interface AIModel {
  model_id: string
  name: string
  model_type: ModelType
  provider: string
  display_name?: string
  description?: string
  model_version?: string
  base_url: string
  api_key_encrypted?: string
  max_tokens?: number
  temperature?: number
  timeout?: number
  enabled: boolean
  status: ModelStatus
  accuracy?: number
  response_time?: number
  usage_count?: number
  created_at?: string
  updated_at?: string
  last_trained?: string
  config_json?: Record<string, any>
}

// 创建模型请求
export interface CreateModelRequest {
  name: string
  model_type: ModelType
  provider: string
  display_name?: string
  description?: string
  model_version?: string
  base_url: string
  api_key: string
  max_tokens?: number
  temperature?: number
  timeout?: number
  config_json?: Record<string, any>
}

// 更新模型请求
export interface UpdateModelRequest {
  name?: string
  display_name?: string
  description?: string
  model_version?: string
  base_url?: string
  api_key?: string
  max_tokens?: number
  temperature?: number
  timeout?: number
  config_json?: Record<string, any>
}

// 模型组合接口类型
export interface ModelEnsemble {
  ensemble_id: string
  name: string
  display_name?: string
  description?: string
  weight_strategy: WeightStrategy
  fusion_strategy?: FusionStrategy
  voting_method?: string
  confidence_threshold?: number
  enabled: boolean
  model_count?: number
  accuracy?: number
  created_at?: string
  updated_at?: string
  config_json?: Record<string, any>
}

// 创建组合请求
export interface CreateEnsembleRequest {
  name: string
  display_name?: string
  description?: string
  weight_strategy: WeightStrategy
  fusion_strategy?: FusionStrategy
  voting_method?: string
  confidence_threshold?: number
  config_json?: Record<string, any>
}

// 组合模型映射
export interface EnsembleModelMapping {
  ensemble_id: string
  model_id: string
  weight: number
  priority?: number
  enabled: boolean
}

// 测试结果
export interface TestResult {
  test_id: string
  model_id?: string
  ensemble_id?: string
  test_name?: string
  test_description?: string
  success: boolean
  content?: string
  output?: string
  response_time: number
  response_time_ms?: number
  accuracy_score?: number
  similarity_score?: number
  token_count?: number
  input_tokens?: number
  output_tokens?: number
  error_message?: string
  error_code?: string
  timestamp: string
  created_at?: string
  updated_at?: string
  tested_by?: string
  input_data?: {
    input?: string
    [key: string]: any
  }
  actual_output?: {
    output?: string
    [key: string]: any
  }
  expected_output?: {
    output?: string
    [key: string]: any
  }
}

// 性能统计
export interface PerformanceStats {
  total_models: number
  active_models: number
  avg_accuracy: number
  avg_response_time: number
  total_requests: number
  success_rate: number
}

// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  error_code?: string
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

// 模型管理API类
export class ModelManagementAPI {
  // 使用全局 axios baseURL('/api')，避免重复前缀导致 '/api/api'
  private baseURL = ''

  // 模型管理接口
  async getModels(params?: {
    page?: number
    per_page?: number
    search?: string
    model_type?: ModelType
    status?: ModelStatus
  }): Promise<ApiResponse<PaginatedResponse<AIModel>>> {
    return request.get(`${this.baseURL}/models`, { params })
  }

  async getModel(modelId: string): Promise<ApiResponse<AIModel>> {
    return request.get(`${this.baseURL}/models/${modelId}`)
  }

  async createModel(data: CreateModelRequest): Promise<ApiResponse<AIModel>> {
    return request.post(`${this.baseURL}/models`, data)
  }

  async updateModel(modelId: string, data: UpdateModelRequest): Promise<ApiResponse<AIModel>> {
    return request.put(`${this.baseURL}/models/${modelId}`, data)
  }

  async deleteModel(modelId: string): Promise<ApiResponse<void>> {
    return request.delete(`${this.baseURL}/models/${modelId}`)
  }

  async toggleModelStatus(modelId: string, enabled: boolean): Promise<ApiResponse<AIModel>> {
    return request.patch(`${this.baseURL}/models/${modelId}/status`, { enabled })
  }

  // 模型组合接口
  async getEnsembles(params?: {
    page?: number
    per_page?: number
    search?: string
  }): Promise<ApiResponse<PaginatedResponse<ModelEnsemble>>> {
    return request.get(`${this.baseURL}/ensembles`, { params })
  }

  async getEnsemble(ensembleId: string): Promise<ApiResponse<ModelEnsemble>> {
    return request.get(`${this.baseURL}/ensembles/${ensembleId}`)
  }

  async createEnsemble(data: CreateEnsembleRequest): Promise<ApiResponse<ModelEnsemble>> {
    return request.post(`${this.baseURL}/ensembles`, data)
  }

  async updateEnsemble(ensembleId: string, data: Partial<CreateEnsembleRequest>): Promise<ApiResponse<ModelEnsemble>> {
    return request.put(`${this.baseURL}/ensembles/${ensembleId}`, data)
  }

  async deleteEnsemble(ensembleId: string): Promise<ApiResponse<void>> {
    return request.delete(`${this.baseURL}/ensembles/${ensembleId}`)
  }

  // 组合模型管理
  async getEnsembleModels(ensembleId: string): Promise<ApiResponse<EnsembleModelMapping[]>> {
    return request.get(`${this.baseURL}/ensembles/${ensembleId}/models`)
  }

  async addModelToEnsemble(ensembleId: string, data: {
    model_id: string
    weight: number
    priority?: number
  }): Promise<ApiResponse<EnsembleModelMapping>> {
    return request.post(`${this.baseURL}/ensembles/${ensembleId}/models`, data)
  }

  async removeModelFromEnsemble(ensembleId: string, modelId: string): Promise<ApiResponse<void>> {
    return request.delete(`${this.baseURL}/ensembles/${ensembleId}/models/${modelId}`)
  }

  async updateEnsembleModelWeight(ensembleId: string, modelId: string, weight: number): Promise<ApiResponse<EnsembleModelMapping>> {
    return request.patch(`${this.baseURL}/ensembles/${ensembleId}/models/${modelId}`, { weight })
  }

  // 模型测试接口
  async testSingleModel(data: {
    model_id: string
    input: string
    expected_output?: string
    test_name?: string
    test_description?: string
  }): Promise<ApiResponse<TestResult>> {
    return request.post(`${this.baseURL}/models/test`, data)
  }

  async testEnsemble(data: {
    ensemble_id: string
    input: string
    expected_output?: string
    test_name?: string
    test_description?: string
  }): Promise<ApiResponse<TestResult>> {
    return request.post(`${this.baseURL}/ensembles/test`, data)
  }

  async getTestRecords(modelId: string, params?: {
    page?: number
    per_page?: number
    test_type?: string
    success?: boolean
  }): Promise<ApiResponse<PaginatedResponse<TestResult>>> {
    return request.get(`${this.baseURL}/models/${modelId}/test-records`, { params })
  }

  // 仪表盘统计接口
  async getDashboardStats(): Promise<ApiResponse<PerformanceStats>> {
    return request.get(`${this.baseURL}/dashboard/stats`)
  }

  async getPerformanceMetrics(params?: {
    days?: number
    model_ids?: string[]
  }): Promise<ApiResponse<any>> {
    return request.get(`${this.baseURL}/dashboard/performance`, { params })
  }

  // 健康检查
  async healthCheck(): Promise<ApiResponse<any>> {
    return request.get(`${this.baseURL}/models/health`)
  }
}

// 导出API实例
export const modelManagementAPI = new ModelManagementAPI()
