import request from '@/utils/request'

export interface DataSource {
  id?: number
  name: string
  type: 'market_data' | 'trading_data'
  provider: string
  status: 'active' | 'inactive' | 'testing'
  base_url?: string
  api_key?: string
  api_secret?: string
  timeout?: number
  rate_limit?: number
  has_api_key?: boolean
  total_calls?: number
  success_calls?: number
  success_rate?: number
  last_call_time?: string
  created_at?: string
  updated_at?: string
}

export interface ApiInterface {
  id: number
  data_source_id: number
  data_source_name: string
  provider: string
  api_code: string
  api_name: string
  api_category: string
  description: string
  endpoint: string
  method: string
  required_params: Array<{
    name: string
    type: string
    description: string
  }>
  optional_params: Array<{
    name: string
    type: string
    description: string
  }>
  response_fields: Array<{
    name: string
    type: string
    description: string
  }>
  required_points: number
  rate_limit: number
  status: 'active' | 'inactive' | 'deprecated'
  total_calls: number
  success_calls: number
  success_rate: number
  avg_response_time: number
  last_call_time?: string
  synced_at?: string
  created_at?: string
}

export interface ApiCallLog {
  id: number
  call_type: 'test' | 'sync' | 'manual'
  request_params: Record<string, any>
  success: boolean
  response_data?: any
  response_time: number
  error_message?: string
  called_at: string
}

export interface SyncTask {
  id: number
  data_source_id: number
  data_source_name: string
  provider: string
  task_name: string
  task_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  total_apis: number
  new_apis: number
  updated_apis: number
  failed_apis: number
  error_message?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface ApiCategory {
  category: string
  api_count: number
}

export interface PaginationParams {
  page?: number
  size?: number
}

export interface DataSourceFilters extends PaginationParams {
  type?: string
  status?: string
}

export interface ApiInterfaceFilters extends PaginationParams {
  data_source_id?: string
  category?: string
  status?: string
}

export interface PaginatedResponse<T> {
  success: boolean
  data: {
    items: T[]
    total: number
    page: number
    size: number
    pages: number
  }
  error?: string
  message?: string
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export const dataManagementApi = {
  // ==================== 数据源管理 ====================
  
  /**
   * 获取数据源列表
   */
  getDataSources(params: DataSourceFilters = {}): Promise<PaginatedResponse<DataSource>> {
    return request.get('/data-management/data-sources', { params })
  },

  /**
   * 创建数据源
   */
  createDataSource(data: Partial<DataSource>): Promise<ApiResponse> {
    return request.post('/data-management/data-sources', data)
  },

  /**
   * 更新数据源
   */
  updateDataSource(id: number, data: Partial<DataSource>): Promise<ApiResponse> {
    return request.put(`/data-management/data-sources/${id}`, data)
  },

  /**
   * 删除数据源
   */
  deleteDataSource(id: number): Promise<ApiResponse> {
    return request.delete(`/data-management/data-sources/${id}`)
  },

  /**
   * 测试数据源连接
   */
  testDataSource(id: number): Promise<ApiResponse> {
    return request.post(`/data-management/data-sources/${id}/test`)
  },

  // ==================== API接口管理 ====================

  /**
   * 获取API接口列表
   */
  getApiInterfaces(params: ApiInterfaceFilters = {}): Promise<PaginatedResponse<ApiInterface>> {
    return request.get('/data-management/api-interfaces', { params })
  },

  /**
   * 测试API接口
   */
  testApiInterface(id: number, data: { params: Record<string, any> }): Promise<ApiResponse> {
    return request.post(`/data-management/api-interfaces/${id}/test`, data)
  },

  /**
   * 获取API调用日志
   */
  getApiCallLogs(apiId: number, params: PaginationParams = {}): Promise<PaginatedResponse<ApiCallLog>> {
    return request.get(`/data-management/api-interfaces/${apiId}/logs`, { params })
  },

  // ==================== API同步管理 ====================

  /**
   * 同步API接口
   */
  syncApis(dataSourceId: number): Promise<ApiResponse> {
    return request.post(`/data-management/data-sources/${dataSourceId}/sync-apis`)
  },

  /**
   * 获取同步任务列表
   */
  getSyncTasks(params: PaginationParams = {}): Promise<PaginatedResponse<SyncTask>> {
    return request.get('/data-management/sync-tasks', { params })
  },

  /**
   * 获取API分类列表
   */
  getApiCategories(params: { data_source_id?: number } = {}): Promise<ApiResponse<ApiCategory[]>> {
    return request.get('/data-management/api-categories', { params })
  },

  // ==================== 数据同步管理 ====================

  /**
   * 获取同步状态
   */
  getSyncStatus(): Promise<ApiResponse> {
    return request.get('/data-sync/sync/status')
  },

  /**
   * 同步所有数据源
   */
  syncAllData(): Promise<ApiResponse> {
    return request.post('/data-sync/sync/all')
  },

  /**
   * 同步单个数据源
   */
  syncDataSource(sourceId: string, params: Record<string, any> = {}): Promise<ApiResponse> {
    return request.post(`/data-sync/sync/${sourceId}`, params)
  },

  /**
   * 获取同步配置
   */
  getSyncConfig(): Promise<ApiResponse> {
    return request.get('/data-sync/sync/config')
  }
}