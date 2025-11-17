/**
 * 选股功能状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ScreeningStrategy,
  ScreeningIndicator,
  ScreeningCondition,
  ScreeningResult,
  ScreeningDetailResult,
  ScreeningHistory,
  UserPreferences,
  Pagination,
  IndicatorGroup,
  ConditionItem,
  ApiResponse
} from '@/types/screening'
import * as screeningApi from '@/api/screening'
import { ElMessage } from 'element-plus'

export const useScreeningStore = defineStore('screening', () => {
  // 策略相关状态
  const strategies = ref<{
    system: ScreeningStrategy[]
    fundamental: ScreeningStrategy[]
    technical: ScreeningStrategy[]
    mixed: ScreeningStrategy[]
    custom: ScreeningStrategy[]
  }>({
    system: [],
    fundamental: [],
    technical: [],
    mixed: [],
    custom: []
  })
  
  const selectedStrategy = ref<ScreeningStrategy>()
  
  // 指标相关状态
  const indicators = ref<{
    fundamental: IndicatorGroup
    technical: IndicatorGroup
    market: IndicatorGroup
  }>({
    fundamental: {},
    technical: {},
    market: {}
  })
  
  // 筛选条件
  const conditions = ref<ScreeningCondition>({})
  const conditionItems = ref<ConditionItem[]>([])
  
  // 执行状态
  const isExecuting = ref(false)
  const currentTask = ref<string>()
  
  // 结果相关
  const results = ref<ScreeningResult[]>([])
  const resultDetail = ref<ScreeningDetailResult>()
  
  // 历史记录
  const history = ref<ScreeningHistory[]>([])
  const historyPagination = ref<Pagination>({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0
  })
  
  // 用户偏好
  const preferences = ref<UserPreferences>({
    preferred_strategies: [],
    default_conditions: {},
    notification_settings: {},
    risk_level: 'moderate',
    max_position_size: 10.0,
    stop_loss_rate: 10.0
  })
  
  // 加载状态
  const loading = ref({
    strategies: false,
    indicators: false,
    executing: false,
    results: false,
    history: false,
    preferences: false
  })
  
  // 计算属性
  const allStrategies = computed(() => {
    return [
      ...strategies.value.system,
      ...strategies.value.fundamental,
      ...strategies.value.technical,
      ...strategies.value.mixed,
      ...strategies.value.custom
    ]
  })
  
  const systemStrategies = computed(() => strategies.value.system)
  const customStrategies = computed(() => strategies.value.custom)
  
  const hasResults = computed(() => results.value.length > 0)
  const hasHistory = computed(() => history.value.length > 0)
  
  // Actions
  
  /**
   * 获取选股策略列表
   */
  async function fetchStrategies() {
    loading.value.strategies = true
    try {
      const response = await screeningApi.getScreeningStrategies()
      if (response.success && response.data) {
        strategies.value = response.data
      }
    } catch (error) {
      console.error('获取策略列表失败:', error)
      ElMessage.error('获取策略列表失败')
    } finally {
      loading.value.strategies = false
    }
  }
  
  /**
   * 获取筛选指标
   */
  async function fetchIndicators() {
    loading.value.indicators = true
    try {
      const response = await screeningApi.getScreeningIndicators()
      if (response.success && response.data) {
        indicators.value = response.data
      }
    } catch (error) {
      console.error('获取指标列表失败:', error)
      ElMessage.error('获取指标列表失败')
    } finally {
      loading.value.indicators = false
    }
  }
  
  /**
   * 执行选股
   */
  async function executeScreening(strategyId: number, customConditions?: ScreeningCondition) {
    if (isExecuting.value) {
      ElMessage.warning('选股正在执行中，请稍候')
      return
    }
    
    isExecuting.value = true
    loading.value.executing = true
    
    try {
      const response = await screeningApi.executeScreening({
        strategy_id: strategyId,
        conditions: customConditions || conditions.value
      })
      
      if (response.success && response.data) {
        currentTask.value = response.data.task_id
        results.value = response.data.results
        
        ElMessage.success(`选股完成！筛选出 ${response.data.filtered_stocks} 只股票`)
        
        // 获取详细结果
        if (response.data.task_id) {
          await fetchResultDetail(response.data.task_id)
        }
        
        return response.data
      } else {
        ElMessage.error(response.message || '选股执行失败')
      }
    } catch (error) {
      console.error('执行选股失败:', error)
      ElMessage.error('执行选股失败')
    } finally {
      isExecuting.value = false
      loading.value.executing = false
    }
  }
  
  /**
   * 获取选股结果详情
   */
  async function fetchResultDetail(taskId: string) {
    loading.value.results = true
    try {
      const response = await screeningApi.getScreeningResult(taskId)
      if (response.success && response.data) {
        results.value = response.data.results || []
        resultDetail.value = response.data
        
        // 回填筛选条件
        if (response.data.conditions) {
          conditions.value = response.data.conditions
          // 将条件转换为条件项
          const items: ConditionItem[] = []
          Object.entries(response.data.conditions).forEach(([key, value]: [string, any]) => {
            if (value && typeof value === 'object' && ('min' in value || 'max' in value)) {
              items.push({
                indicator: key,
                operator: 'range',
                value: value,
                enabled: true
              })
            }
          })
          conditionItems.value = items
        }
        
        // 回填策略选择
        if (response.data.strategy_id) {
          const strategy = allStrategies.value.find(s => s.id === response.data.strategy_id)
          if (strategy) {
            selectedStrategy.value = strategy
          }
        }
      }
    } catch (error) {
      console.error('获取选股结果失败:', error)
      ElMessage.error('获取选股结果失败')
    } finally {
      loading.value.results = false
    }
  }
  
  /**
   * 创建自定义策略
   */
  async function createCustomStrategy(data: {
    strategy_name: string
    strategy_type: string
    description?: string
    conditions: ScreeningCondition
    config?: Record<string, any>
  }) {
    try {
      const response = await screeningApi.createCustomStrategy(data)
      if (response.success) {
        ElMessage.success('自定义策略创建成功')
        // 重新获取策略列表
        await fetchStrategies()
        return response.data
      } else {
        ElMessage.error(response.message || '创建策略失败')
      }
    } catch (error) {
      console.error('创建自定义策略失败:', error)
      ElMessage.error('创建策略失败')
    }
  }
  
  /**
   * 更新自定义策略
   */
  async function updateCustomStrategy(strategyId: number, data: {
    strategy_name?: string
    description?: string
    conditions?: ScreeningCondition
    config?: Record<string, any>
  }) {
    try {
      const response = await screeningApi.updateCustomStrategy(strategyId, data)
      if (response.success) {
        ElMessage.success('策略更新成功')
        await fetchStrategies()
      } else {
        ElMessage.error(response.message || '更新策略失败')
      }
    } catch (error) {
      console.error('更新自定义策略失败:', error)
      ElMessage.error('更新策略失败')
    }
  }
  
  /**
   * 删除自定义策略
   */
  async function deleteCustomStrategy(strategyId: number) {
    try {
      const response = await screeningApi.deleteCustomStrategy(strategyId)
      if (response.success) {
        ElMessage.success('策略删除成功')
        await fetchStrategies()
      } else {
        ElMessage.error(response.message || '删除策略失败')
      }
    } catch (error) {
      console.error('删除自定义策略失败:', error)
      ElMessage.error('删除策略失败')
    }
  }
  
  /**
   * 获取选股历史
   */
  async function fetchHistory(page = 1, limit = 20) {
    loading.value.history = true
    try {
      const response = await screeningApi.getScreeningHistory({ page, limit })
      
      // 兼容两种返回格式
      if (response.success && response.data) {
        // 新格式：{ success: true, data: { list: [], pagination: {} } }
        history.value = response.data.list
        historyPagination.value = response.data.pagination
      } else if (response.results) {
        // 旧格式：{ page, pages, results, size, total }
        history.value = response.results
        historyPagination.value = {
          page: response.page,
          limit: response.size,
          total: response.total,
          pages: response.pages
        }
      }
    } catch (error) {
      console.error('获取选股历史失败:', error)
      ElMessage.error('获取选股历史失败')
    } finally {
      loading.value.history = false
    }
  }
  
  /**
   * 获取用户偏好
   */
  async function fetchPreferences() {
    loading.value.preferences = true
    try {
      const response = await screeningApi.getUserPreferences()
      if (response.success && response.data) {
        preferences.value = response.data
      }
    } catch (error) {
      console.error('获取用户偏好失败:', error)
      ElMessage.error('获取用户偏好失败')
    } finally {
      loading.value.preferences = false
    }
  }
  
  /**
   * 保存用户偏好
   */
  async function savePreferences(data: UserPreferences) {
    try {
      const response = await screeningApi.saveUserPreferences(data)
      if (response.success) {
        preferences.value = data
        ElMessage.success('偏好设置保存成功')
      } else {
        ElMessage.error(response.message || '保存偏好设置失败')
      }
    } catch (error) {
      console.error('保存用户偏好失败:', error)
      ElMessage.error('保存偏好设置失败')
    }
  }
  
  /**
   * 同步数据
   */
  async function syncData(type: 'stock-basic' | 'quotes' | 'financial' | 'technical', params?: any) {
    try {
      let response: ApiResponse<any>
      
      switch (type) {
        case 'stock-basic':
          response = await screeningApi.syncStockBasic()
          break
        case 'quotes':
          response = await screeningApi.syncDailyQuotes(params)
          break
        case 'financial':
          response = await screeningApi.syncFinancialData(params)
          break
        case 'technical':
          response = await screeningApi.calculateTechnicalIndicators(params)
          break
        default:
          throw new Error('未知的数据类型')
      }
      
      if (response.success) {
        ElMessage.success(response.message || '数据同步成功')
        return response.data
      } else {
        ElMessage.error(response.message || '数据同步失败')
      }
    } catch (error) {
      console.error('数据同步失败:', error)
      ElMessage.error('数据同步失败')
    }
  }
  
  /**
   * 设置选中的策略
   */
  function setSelectedStrategy(strategy: ScreeningStrategy) {
    selectedStrategy.value = strategy
  }
  
  /**
   * 更新筛选条件
   */
  function updateConditions(newConditions: ScreeningCondition) {
    conditions.value = { ...newConditions }
  }
  
  /**
   * 添加筛选条件项
   */
  function addConditionItem(item: ConditionItem) {
    conditionItems.value.push(item)
    updateConditionsFromItems()
  }
  
  /**
   * 移除筛选条件项
   */
  function removeConditionItem(index: number) {
    conditionItems.value.splice(index, 1)
    updateConditionsFromItems()
  }
  
  /**
   * 更新筛选条件项
   */
  function updateConditionItem(index: number, item: ConditionItem) {
    conditionItems.value[index] = item
    updateConditionsFromItems()
  }
  
  /**
   * 从条件项更新筛选条件
   */
  function updateConditionsFromItems(items?: ConditionItem[]) {
    const newConditions: ScreeningCondition = {}
    const source = items ?? conditionItems.value
    
    source.forEach(item => {
      if (item.enabled) {
        if (item.operator === 'range') {
          const val: any = item.value || {}
          const hasMin = val.min !== undefined && val.min !== null
          const hasMax = val.max !== undefined && val.max !== null
          if (hasMin || hasMax) {
            newConditions[item.indicator] = { min: val.min, max: val.max }
          }
        } else {
          newConditions[item.indicator] = item.value as any
        }
      }
    })
    
    conditions.value = newConditions
  }
  
  /**
   * 清空结果
   */
  function clearResults() {
    results.value = []
    resultDetail.value = undefined
    currentTask.value = undefined
  }
  
  /**
   * 重置状态
   */
  function reset() {
    selectedStrategy.value = undefined
    conditions.value = {}
    conditionItems.value = []
    clearResults()
  }
  
  /**
   * 初始化
   */
  async function initialize() {
    await Promise.all([
      fetchStrategies(),
      fetchIndicators(),
      fetchPreferences()
    ])
  }
  
  return {
    // 状态
    strategies,
    selectedStrategy,
    indicators,
    conditions,
    conditionItems,
    isExecuting,
    currentTask,
    results,
    resultDetail,
    history,
    historyPagination,
    preferences,
    loading,
    
    // 计算属性
    allStrategies,
    systemStrategies,
    customStrategies,
    hasResults,
    hasHistory,
    
    // 方法
    fetchStrategies,
    fetchIndicators,
    executeScreening,
    fetchResultDetail,
    createCustomStrategy,
    updateCustomStrategy,
    deleteCustomStrategy,
    fetchHistory,
    fetchPreferences,
    savePreferences,
    syncData,
    setSelectedStrategy,
    updateConditions,
    addConditionItem,
    removeConditionItem,
    updateConditionItem,
    updateConditionsFromItems,
    clearResults,
    reset,
    initialize
  }
})