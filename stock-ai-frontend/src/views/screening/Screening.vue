<template>
  <div class="screening-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><TrendCharts /></el-icon>
        智能选股
      </h1>
      <p class="page-description">基于多维度量化指标的专业选股工具</p>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧：策略选择和条件设置 -->
      <div class="left-panel">
        <!-- 策略选择卡片 -->
        <el-card class="strategy-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>选股策略</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="showCreateStrategyDialog = true"
              >
                自定义策略
              </el-button>
            </div>
          </template>
          
          <StrategySelector 
            v-model="selectedStrategyId"
            :strategies="screeningStore.strategies"
            :loading="screeningStore.loading.strategies"
            @strategy-selected="onStrategySelected"
          />
        </el-card>

        <!-- 筛选条件卡片 -->
        <el-card class="conditions-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>筛选条件</span>
              <div class="header-actions">
                <el-button 
                  size="small" 
                  @click="resetConditions"
                >
                  重置
                </el-button>
                <el-button 
                  size="small" 
                  @click="loadPresetConditions"
                >
                  预设条件
                </el-button>
              </div>
            </div>
          </template>
          
          <ConditionEditor
            v-model="screeningStore.conditionItems"
            :indicators="screeningStore.indicators"
            :loading="screeningStore.loading.indicators"
            @conditions-changed="onConditionsChanged"
          />
        </el-card>

        <!-- 执行按钮 -->
        <div class="execute-section">
          <el-button
            type="primary"
            size="large"
            :loading="screeningStore.isExecuting"
            :disabled="!selectedStrategyId"
            @click="executeScreening"
            class="execute-btn"
          >
            <el-icon><Search /></el-icon>
            {{ screeningStore.isExecuting ? '选股中...' : '开始选股' }}
          </el-button>
        </div>
      </div>

      <!-- 右侧：结果展示 -->
      <div class="right-panel">
        <!-- 结果统计卡片 -->
        <el-card v-if="screeningStore.hasResults" class="stats-card" shadow="hover">
          <template #header>
            <span>选股结果统计</span>
          </template>
          
          <ResultStats 
            :result-detail="screeningStore.resultDetail"
            :loading="screeningStore.loading.results"
          />
        </el-card>

        <!-- 结果列表卡片 -->
        <el-card class="results-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>选股结果</span>
              <div class="header-actions" v-if="screeningStore.hasResults">
                <el-button 
                  size="small" 
                  @click="exportResults"
                >
                  导出
                </el-button>
                <el-button 
                  size="small" 
                  @click="saveToPortfolio"
                >
                  加入组合
                </el-button>
              </div>
            </div>
          </template>
          
          <ResultTable
            :results="screeningStore.results"
            :loading="screeningStore.loading.executing || screeningStore.loading.results"
            @row-click="onResultRowClick"
          />
        </el-card>
      </div>
    </div>

    <!-- 底部：历史记录和数据管理 -->
    <div class="bottom-section">
      <el-tabs v-model="activeTab" class="bottom-tabs">
        <el-tab-pane label="选股历史" name="history">
          <HistoryTable
            :history="screeningStore.history"
            :pagination="screeningStore.historyPagination"
            :loading="screeningStore.loading.history"
            @page-change="onHistoryPageChange"
            @view-result="onViewHistoryResult"
            @rerun-screening="onRerunScreening"
          />
        </el-tab-pane>
        
        <el-tab-pane label="数据管理" name="data">
          <DataManagement
            @sync-data="onSyncData"
          />
        </el-tab-pane>
        
        <el-tab-pane label="偏好设置" name="preferences">
          <PreferencesSettings
            :preferences="screeningStore.preferences"
            :loading="screeningStore.loading.preferences"
            @save-preferences="onSavePreferences"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 创建自定义策略对话框 -->
    <CreateStrategyDialog
      v-model="showCreateStrategyDialog"
      :indicators="screeningStore.indicators"
      @strategy-created="onStrategyCreated"
    />

    <!-- 股票详情对话框 -->
    <StockDetailDialog
      v-model="showStockDetailDialog"
      :stock="selectedStock"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { TrendCharts, Search } from '@element-plus/icons-vue'
import { useScreeningStore } from '@/stores/screening'
import type { ScreeningResult, ConditionItem } from '@/types/screening'

// 组件导入
import StrategySelector from './components/StrategySelector.vue'
import ConditionEditor from './components/ConditionEditor.vue'
import ResultStats from './components/ResultStats.vue'
import ResultTable from './components/ResultTable.vue'
import HistoryTable from './components/HistoryTable.vue'
import DataManagement from './components/DataManagement.vue'
import PreferencesSettings from './components/PreferencesSettings.vue'
import CreateStrategyDialog from './components/CreateStrategyDialog.vue'
import StockDetailDialog from './components/StockDetailDialog.vue'

// 状态管理
const screeningStore = useScreeningStore()

// 响应式数据
const selectedStrategyId = ref<number>()
// 条件项直接绑定到 store，避免条件不同步导致后端接收为空
const activeTab = ref('history')
const showCreateStrategyDialog = ref(false)
const showStockDetailDialog = ref(false)
const selectedStock = ref<ScreeningResult>()

// 计算属性
const hasSelectedStrategy = computed(() => !!selectedStrategyId.value)

// 方法
const onStrategySelected = (strategyId: number) => {
  selectedStrategyId.value = strategyId
  const strategy = screeningStore.allStrategies.find(s => s.id === strategyId)
  if (strategy) {
    screeningStore.setSelectedStrategy(strategy)
  }
}

const onConditionsChanged = (items: ConditionItem[]) => {
  screeningStore.updateConditionsFromItems(items)
}

const resetConditions = () => {
  screeningStore.conditionItems = []
  screeningStore.updateConditions({})
}

const loadPresetConditions = async () => {
  // 加载用户偏好的默认条件
  if (screeningStore.preferences.default_conditions) {
    // 将偏好条件转换为条件项
    const items: ConditionItem[] = []
    Object.entries(screeningStore.preferences.default_conditions).forEach(([key, value]) => {
      items.push({
        indicator: key,
        operator: 'range',
        value,
        enabled: true
      })
    })
    screeningStore.conditionItems = items
    screeningStore.updateConditionsFromItems(items)
  }
}

const executeScreening = async () => {
  if (!selectedStrategyId.value) {
    ElMessage.warning('请先选择选股策略')
    return
  }

  try {
    await screeningStore.executeScreening(selectedStrategyId.value)
    // 刷新历史记录
    await screeningStore.fetchHistory()
  } catch (error) {
    console.error('执行选股失败:', error)
  }
}

const exportResults = () => {
  if (!screeningStore.hasResults) {
    ElMessage.warning('暂无结果可导出')
    return
  }

  // 导出CSV格式
  const headers = ['股票代码', '股票名称', '行业', '市场', '收盘价', '涨跌幅', '换手率', 'PE', 'PB', '市值', 'ROE', '营收增长率', '利润增长率', '资产负债率', '流动比率', '速动比率', '毛利率', '净利率', 'ROA', '综合评分', '排名']
  const csvContent = [
    headers.join(','),
    ...screeningStore.results.map(item => [
      item.symbol,
      item.name,
      item.industry,
      item.market,
      item.close_price || '',
      item.change_pct || '',
      item.turnover_rate || '',
      item.pe || '',
      item.pb || '',
      item.market_cap || '',
      item.roe || '',
      item.revenue_growth || '',
      item.profit_growth || '',
      item.debt_ratio || '',
      item.current_ratio || '',
      item.quick_ratio || '',
      item.gross_margin || '',
      item.net_margin || '',
      item.roa || '',
      item.composite_score,
      item.rank
    ].join(','))
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `选股结果_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  
  ElMessage.success('结果导出成功')
}

const saveToPortfolio = async () => {
  if (!screeningStore.hasResults) {
    ElMessage.warning('暂无结果可保存')
    return
  }

  try {
    await ElMessageBox.confirm('是否将选股结果添加到投资组合？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })

    // TODO: 调用投资组合API
    ElMessage.success('已添加到投资组合')
  } catch {
    // 用户取消
  }
}

const onResultRowClick = (result: ScreeningResult) => {
  selectedStock.value = result
  showStockDetailDialog.value = true
}

const onHistoryPageChange = (page: number) => {
  screeningStore.fetchHistory(page)
}

const onViewHistoryResult = async (taskId: string) => {
  await screeningStore.fetchResultDetail(taskId)
  // 回填策略选择到UI
  if (screeningStore.selectedStrategy) {
    selectedStrategyId.value = screeningStore.selectedStrategy.id
  }
  // 切换到结果展示区域
  activeTab.value = 'history'
  ElMessage.success('已加载历史选股条件，可以修改后重新执行')
}

const onRerunScreening = async (taskId: string) => {
  try {
    // 先加载历史条件
    await screeningStore.fetchResultDetail(taskId)
    
    // 回填策略选择到UI
    if (screeningStore.selectedStrategy) {
      selectedStrategyId.value = screeningStore.selectedStrategy.id
    }
    
    // 确认是否立即执行
    await ElMessageBox.confirm(
      '已加载历史选股条件，是否立即执行选股？',
      '重新执行选股',
      {
        confirmButtonText: '立即执行',
        cancelButtonText: '稍后执行',
        type: 'info'
      }
    )
    
    // 用户确认后执行选股
    if (selectedStrategyId.value) {
      await executeScreening()
    }
  } catch (error) {
    // 用户取消或其他错误
    if (error !== 'cancel') {
      console.error('重新执行选股失败:', error)
    } else {
      ElMessage.info('已加载历史条件，可以修改后手动执行')
    }
  }
}

const onSyncData = async (type: string, params?: any) => {
  await screeningStore.syncData(type as any, params)
}

const onSavePreferences = async (preferences: any) => {
  await screeningStore.savePreferences(preferences)
}

const onStrategyCreated = () => {
  showCreateStrategyDialog.value = false
  screeningStore.fetchStrategies()
}

// 生命周期
onMounted(async () => {
  await screeningStore.initialize()
  await screeningStore.fetchHistory()
})
</script>

<style scoped lang="scss">
.screening-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
  
  .page-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 8px 0;
  }
  
  .page-description {
    color: #606266;
    margin: 0;
    font-size: 14px;
  }
}

.main-content {
// width: 100%;
  display: grid;
  grid-template-columns: 49% 49%;
  // grid-row-gap: 20px;
  grid-column-gap: 20px;
  margin-bottom: 24px;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.strategy-card,
.conditions-card {
  .el-card__body {
    padding: 16px;
  }
}

.execute-section {
  .execute-btn {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 600;
  }
}

.stats-card {
  .el-card__body {
    padding: 16px;
  }
}

.results-card {
  flex: 1;
  
  .el-card__body {
    padding: 0;
    height: 500px;
    overflow: hidden;
  }
}

.bottom-section {
  .bottom-tabs {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    
    :deep(.el-tabs__header) {
      margin: 0;
      padding: 0 20px;
      background: #fafafa;
      border-radius: 8px 8px 0 0;
    }
    
    :deep(.el-tabs__content) {
      padding: 20px;
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .left-panel {
    order: 2;
  }
  
  .right-panel {
    order: 1;
  }
}

@media (max-width: 768px) {
  .screening-container {
    padding: 12px;
  }
  
  .main-content {
    gap: 12px;
  }
  
  .left-panel,
  .right-panel {
    gap: 12px;
  }
}
</style>