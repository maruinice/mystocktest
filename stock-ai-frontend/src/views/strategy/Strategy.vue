<template>
  <div class="strategy-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <el-icon><TrendCharts /></el-icon>
            策略管理中心
          </h1>
          <p class="page-description">专业量化交易策略开发、回测与管理平台</p>
        </div>
        <div class="header-actions">
          <el-button 
            type="primary" 
            @click="handleCreateStrategy" 
            size="large"
          >
            <el-icon><Plus /></el-icon>
            创建策略
          </el-button>
          <el-button @click="handleAIGenerateStrategy" size="large">
            <el-icon><ChatDotRound /></el-icon>
            AI生成策略
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 策略概览仪表板 -->
    <div class="dashboard-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="6">
          <div class="metric-card total-strategies">
            <div class="metric-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ strategies.length }}</div>
              <div class="metric-label">总策略数</div>
              <div class="metric-trend">
                <span class="trend-up">+{{ newStrategiesThisMonth }}</span>
                <span class="trend-text">本月新增</span>
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="6">
          <div class="metric-card active-strategies">
            <div class="metric-icon">
              <el-icon><VideoPlay /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ activeStrategies.length }}</div>
              <div class="metric-label">运行中策略</div>
              <div class="metric-trend">
                <span class="trend-neutral">{{ (activeStrategies.length / strategies.length * 100).toFixed(1) }}%</span>
                <span class="trend-text">活跃率</span>
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="6">
          <div class="metric-card total-return">
            <div class="metric-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">+15.6%</div>
              <div class="metric-label">平均收益率</div>
              <div class="metric-trend">
                <span class="trend-up">+2.3%</span>
                <span class="trend-text">vs基准</span>
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="6">
          <div class="metric-card sharpe-ratio">
            <div class="metric-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">1.85</div>
              <div class="metric-label">平均夏普比率</div>
              <div class="metric-trend">
                <span class="trend-up">优秀</span>
                <span class="trend-text">风险调整收益</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 策略筛选和操作栏 -->
    <div class="strategy-toolbar">
      <div class="filter-section">
        <el-select v-model="filterStatus" placeholder="策略状态" style="width: 120px;" @change="applyFilters">
          <el-option label="全部" value="" />
          <el-option label="运行中" value="active" />
          <el-option label="已停止" value="stopped" />
          <el-option label="草稿" value="draft" />
        </el-select>
        
        <el-select v-model="filterCategory" placeholder="策略类型" style="width: 140px;" @change="applyFilters">
          <el-option label="全部类型" value="" />
          <el-option label="趋势跟踪" value="trend_following" />
          <el-option label="均值回归" value="mean_reversion" />
          <el-option label="动量策略" value="momentum" />
          <el-option label="套利策略" value="arbitrage" />
          <el-option label="多因子" value="multi_factor" />
        </el-select>
        
        <el-select v-model="filterRisk" placeholder="风险等级" style="width: 120px;" @change="applyFilters">
          <el-option label="全部风险" value="" />
          <el-option label="低风险" value="low" />
          <el-option label="中风险" value="medium" />
          <el-option label="高风险" value="high" />
        </el-select>
        
        <el-input
          v-model="searchKeyword"
          placeholder="搜索策略名称或描述..."
          style="width: 300px;"
          clearable
          @input="applyFilters"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <div class="action-section">
        <el-button @click="refreshStrategies">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>
          导入策略
        </el-button>
        <el-button @click="exportSelectedStrategies" :disabled="selectedStrategies.length === 0">
          <el-icon><Download /></el-icon>
          导出策略
        </el-button>
        <el-button @click="batchDeleteStrategies" :disabled="selectedStrategies.length === 0" type="danger">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
    </div>
    
    <!-- 策略列表 -->
    <div class="strategy-list-section">
      <el-table 
        :data="filteredStrategies" 
        v-loading="loading"
        @selection-change="handleSelectionChange"
        row-key="strategy_id"
        class="strategy-table"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="策略信息" min-width="250">
          <template #default="{ row }">
            <div class="strategy-info">
              <div class="strategy-header">
                <span class="strategy-name">{{ row.name }}</span>
                <div class="strategy-badges">
                  <el-tag :type="getStrategyTypeColor(row.category)" size="small">
                    {{ getStrategyTypeText(row.category) }}
                  </el-tag>
                  <el-tag :type="getRiskLevelColor(row.risk_level)" size="small">
                    {{ getRiskLevelText(row.risk_level) }}
                  </el-tag>
                </div>
              </div>
              <div class="strategy-description">{{ row.description }}</div>
              <div class="strategy-meta">
                <span class="meta-item">
                  <el-icon><User /></el-icon>
                  {{ row.author || '系统' }}
                </span>
                <span class="meta-item">
                  <el-icon><Calendar /></el-icon>
                  {{ formatDateTime(row.created_at) }}
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              <el-icon>
                <VideoPlay v-if="row.status === 'active'" />
                <VideoPause v-else-if="row.status === 'paused'" />
                <CircleClose v-else-if="row.status === 'stopped'" />
                <Edit v-else />
              </el-icon>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="性能指标" width="200" align="center">
          <template #default="{ row }">
            <div class="performance-metrics">
              <div class="metric-row">
                <span class="metric-label">收益率:</span>
                <span :class="['metric-value', row.performance >= 0 ? 'positive' : 'negative']">
                  {{ row.performance >= 0 ? '+' : '' }}{{ (row.performance * 100).toFixed(2) }}%
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">夏普比率:</span>
                <span class="metric-value">{{ row.sharpe_ratio || '--' }}</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">最大回撤:</span>
                <span class="metric-value negative">{{ row.max_drawdown ? (row.max_drawdown * 100).toFixed(2) + '%' : '--' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="回测信息" width="150" align="center">
          <template #default="{ row }">
            <div class="backtest-info">
              <div class="backtest-count">
                <el-icon><DataAnalysis /></el-icon>
                {{ row.backtest_count || 0 }} 次回测
              </div>
              <div class="last-backtest" v-if="row.last_backtest_date">
                最近: {{ formatDate(row.last_backtest_date) }}
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <!-- 状态控制按钮 -->
              <el-button-group class="status-controls">
                <el-button
                  v-if="row.status === 'draft' || row.status === 'stopped'"
                  @click="startStrategy(row)"
                  size="small"
                  type="success"
                >
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
                <el-button
                  v-if="row.status === 'active'"
                  @click="pauseStrategy(row)"
                  size="small"
                  type="warning"
                >
                  <el-icon><VideoPause /></el-icon>
                </el-button>
                <el-button
                  v-if="row.status === 'active' || row.status === 'paused'"
                  @click="stopStrategy(row)"
                  size="small"
                  type="danger"
                >
                  <el-icon><VideoStop /></el-icon>
                </el-button>
              </el-button-group>
              
              <!-- 功能按钮 -->
              <el-dropdown @command="(command) => handleStrategyAction(command, row)">
                <el-button size="small">
                  更多操作
                  <el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">
                      <el-icon><Edit /></el-icon>
                      编辑策略
                    </el-dropdown-item>
                    <el-dropdown-item command="copy">
                      <el-icon><CopyDocument /></el-icon>
                      复制策略
                    </el-dropdown-item>
                    <el-dropdown-item command="backtest">
                      <el-icon><DataAnalysis /></el-icon>
                      运行回测
                    </el-dropdown-item>
                    <el-dropdown-item command="backtest_history">
                      <el-icon><Clock /></el-icon>
                      回测历史
                    </el-dropdown-item>
                    <el-dropdown-item command="view_code">
                      <el-icon><View /></el-icon>
                      查看代码
                    </el-dropdown-item>
                    <el-dropdown-item command="export">
                      <el-icon><Download /></el-icon>
                      导出策略
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      删除策略
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-section">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
    
    <!-- 策略构建器对话框 -->
    <el-dialog
      v-model="showStrategyBuilder"
      title="策略构建器"
      width="90%"
      :close-on-click-modal="false"
      class="strategy-builder-dialog"
      destroy-on-close
    >
      <StrategyBuilder
        v-if="showStrategyBuilder"
        @save="handleStrategySave"
        @cancel="showStrategyBuilder = false"
        :edit-strategy="editingStrategy"
      />
    </el-dialog>
    
    <!-- AI策略生成器对话框 -->
    <el-dialog
      v-model="showAIGenerator"
      title="AI策略生成器"
      width="80%"
      :close-on-click-modal="false"
      class="ai-generator-dialog"
    >
      <AIStrategyGenerator
        v-if="showAIGenerator"
        @generate="handleAIGenerate"
        @cancel="showAIGenerator = false"
      />
    </el-dialog>
    
    <!-- 策略导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入策略"
      width="600px"
    >
      <StrategyImporter
        v-if="showImportDialog"
        @import="handleStrategyImport"
        @cancel="showImportDialog = false"
      />
    </el-dialog>
    
    <!-- 回测结果对话框 -->
    <el-dialog
      v-model="showBacktestResult"
      title="回测结果"
      width="90%"
      :close-on-click-modal="false"
    >
      <BacktestResult
        v-if="showBacktestResult && currentBacktestResult"
        :result="currentBacktestResult"
        @close="showBacktestResult = false"
      />
    </el-dialog>
    
    <!-- 策略代码查看器对话框 -->
    <el-dialog
      v-model="showCodeViewer"
      title="策略代码"
      width="80%"
      :close-on-click-modal="false"
    >
      <StrategyCodeViewer
        v-if="showCodeViewer && viewingStrategy"
        :strategy="viewingStrategy"
        @close="showCodeViewer = false"
        @edit="editStrategyCode"
      />
    </el-dialog>

    <!-- 回测配置对话框 -->
    <el-dialog
      v-model="showBacktestConfig"
      title="运行回测"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="backtest-config">
        <el-form label-width="120px">
          <el-form-item label="时间范围">
            <div class="range-row">
              <el-radio-group v-model="backtestConfig.quick_range" @change="(val:any)=>applyQuickRange(val)">
                <el-radio-button label="1w">一周</el-radio-button>
                <el-radio-button label="1m">一月</el-radio-button>
                <el-radio-button label="1y">一年</el-radio-button>
              </el-radio-group>
              <el-date-picker
                v-model="backtestDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                @change="onDateRangeChange"
              />
            </div>
          </el-form-item>
          <el-form-item label="初始资金">
            <el-input-number v-model="backtestConfig.initial_capital" :min="10000" :step="10000" />
          </el-form-item>
          <el-form-item label="股票池来源">
            <el-radio-group v-model="backtestConfig.stock_source">
              <el-radio label="latest">最近一次选股结果</el-radio>
              <el-radio label="history">选择选股历史</el-radio>
              <el-radio label="manual">手动输入代码</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="执行频率">
            <el-radio-group v-model="backtestConfig.frequency">
              <el-radio label="daily">按天执行</el-radio>
              <el-radio label="monthly">按月执行</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="backtestConfig.stock_source === 'history'" label="选股历史">
            <el-select v-model="backtestConfig.selected_task_id" placeholder="选择一次选股任务" @change="onSelectHistoryTask">
              <el-option
                v-for="item in screeningHistory"
                :key="item.task_id"
                :label="`${item.strategy_name}｜${item.filtered_stocks}只｜${item.screening_date}`"
                :value="item.task_id"
              />
            </el-select>
          </el-form-item>
          <el-form-item v-if="backtestConfig.stock_source !== 'manual'" label="股票数量">
            <span>{{ selectedStockPool.length }} 只</span>
          </el-form-item>
          <el-form-item v-if="backtestConfig.stock_source === 'manual'" label="股票代码">
            <el-input
              v-model="manualStockCodes"
              type="textarea"
              :rows="4"
              placeholder="输入股票代码，逗号/空格/换行分隔，如：600000.SH, 000001.SZ"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showBacktestConfig = false">取消</el-button>
        <el-button type="primary" :loading="backtestLoading" @click="confirmRunBacktest">开始回测</el-button>
      </template>
    </el-dialog>

    <!-- 回测历史对话框 -->
    <el-dialog
      v-model="showBacktestHistory"
      :title="`${currentHistoryStrategy?.strategy_name || '策略'} - 回测历史`"
      width="95%"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <BacktestHistory
        v-if="currentHistoryStrategy"
        :strategy-id="currentHistoryStrategy.strategy_id"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { formatDateTime, formatDate } from '@/utils/format'
import strategyApi from '@/api/strategy'
import * as screeningApi from '@/api/screening'
import type { Strategy, BacktestResult as BacktestResultType } from '@/types/strategy'
import type { ScreeningHistory, ScreeningDetailResult } from '@/types/screening'

// 导入子组件
import StrategyBuilder from './components/StrategyBuilder.vue'
import AIStrategyGenerator from './components/AIStrategyGenerator.vue'
import StrategyImporter from './components/StrategyImporter.vue'
import BacktestResult from './components/BacktestResult.vue'
import StrategyCodeViewer from './components/StrategyCodeViewer.vue'
import BacktestHistory from './components/BacktestHistory.vue'

// 响应式数据
const loading = ref(false)
const showStrategyBuilder = ref(false)
const showAIGenerator = ref(false)
const showImportDialog = ref(false)
const showBacktestResult = ref(false)
const showCodeViewer = ref(false)
const showBacktestHistory = ref(false)
const currentHistoryStrategy = ref<Strategy | null>(null)

// 回测配置弹窗
const showBacktestConfig = ref(false)
const backtestingStrategy = ref<Strategy | null>(null)
const backtestLoading = ref(false)
const backtestConfig = reactive({
  start_date: '',
  end_date: '',
  initial_capital: 1000000,
  quick_range: '' as '' | '1w' | '1m' | '1y',
  stock_source: 'latest' as 'latest' | 'history' | 'manual',
  selected_task_id: '',
  frequency: 'daily' as 'daily' | 'monthly'
})
const screeningHistory = ref<ScreeningHistory[]>([])
const selectedStockPool = ref<string[]>([])
const manualStockCodes = ref('')
// 日期范围绑定（用于Element Plus daterange）
const backtestDateRange = ref<[string, string] | null>(null)

// 筛选和搜索
const filterStatus = ref('')
const filterCategory = ref('')
const filterRisk = ref('')
const searchKeyword = ref('')

// 策略数据
const strategies = ref<Strategy[]>([])
const selectedStrategies = ref<Strategy[]>([])
const editingStrategy = ref<Strategy | null>(null)
const viewingStrategy = ref<Strategy | null>(null)
const currentBacktestResult = ref<BacktestResultType | null>(null)

// 统计数据
const newStrategiesThisMonth = ref(3)

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 计算属性
const activeStrategies = computed(() => 
  strategies.value.filter(s => s.status === 'active')
)

const filteredStrategies = computed(() => {
  let filtered = strategies.value

  // 状态筛选
  if (filterStatus.value) {
    filtered = filtered.filter(s => s.status === filterStatus.value)
  }

  // 类型筛选
  if (filterCategory.value) {
    filtered = filtered.filter(s => s.category === filterCategory.value)
  }

  // 风险等级筛选
  if (filterRisk.value) {
    filtered = filtered.filter(s => s.risk_level === filterRisk.value)
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(s => 
      s.name.toLowerCase().includes(keyword) ||
      s.description.toLowerCase().includes(keyword)
    )
  }

  pagination.total = filtered.length
  
  // 分页
  const start = (pagination.page - 1) * pagination.size
  const end = start + pagination.size
  return filtered.slice(start, end)
})

// 工具方法
const getStrategyTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    trend_following: '趋势跟踪',
    mean_reversion: '均值回归',
    momentum: '动量策略',
    arbitrage: '套利策略',
    multi_factor: '多因子',
    custom: '自定义'
  }
  return typeMap[type] || type
}

const getStrategyTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    trend_following: 'primary',
    mean_reversion: 'success',
    momentum: 'warning',
    arbitrage: 'info',
    multi_factor: 'danger',
    custom: ''
  }
  return colorMap[type] || 'info'
}

const getRiskLevelText = (level: string) => {
  const levelMap: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险'
  }
  return levelMap[level] || level
}

const getRiskLevelColor = (level: string) => {
  const colorMap: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return colorMap[level] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    draft: '草稿',
    active: '运行中',
    paused: '已暂停',
    stopped: '已停止'
  }
  return statusMap[status] || status
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    draft: 'info',
    active: 'success',
    paused: 'warning',
    stopped: 'danger'
  }
  return colorMap[status] || 'info'
}

// 事件处理方法
const refreshStrategies = async () => {
  loading.value = true
  try {
    const { data } = await strategyApi.getStrategies({
      page: pagination.page,
      size: pagination.size
    })
    strategies.value = data?.strategies || []
    pagination.total = data?.total || 0
    ElMessage.success('刷新成功')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  pagination.page = 1
}

const handleSelectionChange = (selection: Strategy[]) => {
  selectedStrategies.value = selection
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  refreshStrategies()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  refreshStrategies()
}

// 策略操作方法
const startStrategy = async (strategy: Strategy) => {
  try {
    await ElMessageBox.confirm(`确认启动策略 "${strategy.name}"？`, '确认启动', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await strategyApi.startStrategy(strategy.strategy_id)
    strategy.status = 'active'
    
    ElNotification({
      title: '策略启动成功',
      message: `策略 "${strategy.name}" 已开始运行`,
      type: 'success'
    })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('策略启动失败')
    }
  }
}

const pauseStrategy = async (strategy: Strategy) => {
  try {
    await strategyApi.pauseStrategy(strategy.strategy_id)
    strategy.status = 'paused'
    ElMessage.success('策略已暂停')
  } catch (error) {
    ElMessage.error('策略暂停失败')
  }
}

const stopStrategy = async (strategy: Strategy) => {
  try {
    await ElMessageBox.confirm(`确认停止策略 "${strategy.name}"？`, '确认停止', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await strategyApi.stopStrategy(strategy.strategy_id)
    strategy.status = 'stopped'
    
    ElNotification({
      title: '策略已停止',
      message: `策略 "${strategy.name}" 已停止运行`,
      type: 'info'
    })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('策略停止失败')
    }
  }
}

const handleStrategyAction = async (command: string, strategy: Strategy) => {
  switch (command) {
    case 'edit':
      editingStrategy.value = strategy
      showStrategyBuilder.value = true
      break
      
    case 'copy':
      await copyStrategy(strategy)
      break
      
    case 'backtest':
      openBacktestConfig(strategy)
      break
      
    case 'backtest_history':
      openBacktestHistory(strategy)
      break
      
    case 'view_code':
      viewingStrategy.value = strategy
      showCodeViewer.value = true
      break
      
    case 'export':
      await exportStrategy(strategy)
      break
      
    case 'delete':
      await deleteStrategy(strategy)
      break
  }
}

const copyStrategy = async (strategy: Strategy) => {
  try {
    const { data } = await strategyApi.copyStrategy(strategy.strategy_id)
    strategies.value.unshift(data)
    ElMessage.success(`策略 "${strategy.name}" 复制成功`)
  } catch (error) {
    ElMessage.error('策略复制失败')
  }
}

function openBacktestConfig(strategy: Strategy) {
  backtestingStrategy.value = strategy
  // 默认时间范围：最近一月
  const today = new Date()
  const end = today.toISOString().slice(0, 10)
  const start = new Date(today.getTime() - 30 * 24 * 3600 * 1000).toISOString().slice(0, 10)
  backtestConfig.start_date = start
  backtestConfig.end_date = end
  backtestDateRange.value = [start, end]
  backtestConfig.quick_range = '1m'
  backtestConfig.stock_source = 'latest'
  backtestConfig.selected_task_id = ''
  selectedStockPool.value = []
  manualStockCodes.value = ''
  showBacktestConfig.value = true
  // 预加载选股历史用于选择股票池
  loadScreeningHistory()
  // 加载最近一次选股结果作为默认股票池
  loadLatestScreeningStocks()
}

function openBacktestHistory(strategy: Strategy) {
  currentHistoryStrategy.value = strategy
  showBacktestHistory.value = true
}

function applyQuickRange(range: '1w' | '1m' | '1y') {
  backtestConfig.quick_range = range
  const today = new Date()
  let days = 7
  if (range === '1m') days = 30
  if (range === '1y') days = 365
  const end = today.toISOString().slice(0, 10)
  const start = new Date(today.getTime() - days * 24 * 3600 * 1000).toISOString().slice(0, 10)
  backtestConfig.start_date = start
  backtestConfig.end_date = end
  backtestDateRange.value = [start, end]
  // 根据区间自动设定执行频率：小于一个月按日，否则按月
  backtestConfig.frequency = days < 30 ? 'daily' : 'monthly'
}

function onDateRangeChange(val: any) {
  // 手动选择日期时，清除快捷范围选择，并同步配置
  backtestConfig.quick_range = ''
  if (Array.isArray(val) && val.length === 2) {
    const [start, end] = val
    backtestConfig.start_date = start
    backtestConfig.end_date = end
    // 自动设定执行频率
    const s = new Date(start)
    const e = new Date(end)
    const diffDays = Math.round((e.getTime() - s.getTime()) / (24 * 3600 * 1000))
    backtestConfig.frequency = diffDays < 30 ? 'daily' : 'monthly'
  }
}

async function loadScreeningHistory() {
  try {
    const resp = await screeningApi.getScreeningHistory({ page: 1, limit: 20 })
    if (resp.success && resp.data) {
      screeningHistory.value = resp.data.list || []
    }
  } catch (e) {
    // 忽略错误，仅用于辅助选择
  }
}

async function loadLatestScreeningStocks() {
  try {
    const resp = await screeningApi.getScreeningHistory({ page: 1, limit: 1 })
    if (resp.success && resp.data && resp.data.list && resp.data.list.length > 0) {
      const latest = resp.data.list[0]
      backtestConfig.selected_task_id = latest.task_id
      const detail = await screeningApi.getScreeningResult(latest.task_id)
      if (detail.success && detail.data) {
        selectedStockPool.value = (detail.data.results || []).map((r: ScreeningDetailResult['results'][number]) => r.ts_code)
      }
    }
  } catch (e) {
    selectedStockPool.value = []
  }
}

async function onSelectHistoryTask(taskId: string) {
  backtestConfig.selected_task_id = taskId
  if (!taskId) return
  try {
    const detail = await screeningApi.getScreeningResult(taskId)
    if (detail.success && detail.data) {
      selectedStockPool.value = (detail.data.results || []).map((r: ScreeningDetailResult['results'][number]) => r.ts_code)
    }
  } catch (e) {
    selectedStockPool.value = []
  }
}

function parseManualCodes(input: string): string[] {
  return input
    .split(/[\s,;]+/)
    .map(s => s.trim())
    .filter(s => s.length > 0)
}

async function confirmRunBacktest() {
  if (!backtestingStrategy.value) return
  try {
    backtestLoading.value = true
    ElMessage.info('正在运行回测...')
    // 选择股票池来源
    let stockPool: string[] = []
    if (backtestConfig.stock_source === 'manual') {
      stockPool = parseManualCodes(manualStockCodes.value)
    } else {
      stockPool = selectedStockPool.value
    }
    const payload = {
      strategy_id: backtestingStrategy.value.strategy_id,
      start_date: backtestConfig.start_date,
      end_date: backtestConfig.end_date,
      initial_capital: backtestConfig.initial_capital,
      stock_pool: stockPool,
      frequency: backtestConfig.frequency
    }
    // 简单的前端校验，防止空股票池或日期为空
    if (!payload.start_date || !payload.end_date) {
      ElMessage.error('开始/结束日期不能为空')
      return
    }
    if (!payload.stock_pool || payload.stock_pool.length === 0) {
      ElMessage.error('股票池为空，请先选择选股结果或手动输入代码')
      return
    }
    const resp = await strategyApi.runBacktest(payload)
    const data = resp.data
    if ((data as any)?.status === 'failed') {
      ElMessage.error((data as any)?.error_message || '回测失败')
      // 停止loading但不关闭弹窗，便于用户调整参数
      return
    }
    currentBacktestResult.value = data
    showBacktestConfig.value = false
    showBacktestResult.value = true
    ElMessage.success('回测完成')
  } catch (error) {
    ElMessage.error('回测失败')
  } finally {
    backtestLoading.value = false
  }
}

const exportStrategy = async (strategy: Strategy) => {
  try {
    const { data } = await strategyApi.exportStrategy(strategy.strategy_id)
    
    // 创建下载链接
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${strategy.name}_strategy.json`
    link.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('策略导出成功')
  } catch (error) {
    ElMessage.error('策略导出失败')
  }
}

const deleteStrategy = async (strategy: Strategy) => {
  try {
    await ElMessageBox.confirm(
      `确认删除策略 "${strategy.name}"？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    await strategyApi.deleteStrategy(strategy.strategy_id)
    const index = strategies.value.findIndex(s => s.strategy_id === strategy.strategy_id)
    if (index > -1) {
      strategies.value.splice(index, 1)
    }
    
    ElMessage.success('策略删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('策略删除失败')
    }
  }
}

// 批量操作
const exportSelectedStrategies = async () => {
  try {
    const strategyIds = selectedStrategies.value.map(s => s.strategy_id)
    const { data } = await strategyApi.exportStrategies(strategyIds)
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `strategies_${new Date().getTime()}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success(`成功导出 ${selectedStrategies.value.length} 个策略`)
  } catch (error) {
    ElMessage.error('批量导出失败')
  }
}

const batchDeleteStrategies = async () => {
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${selectedStrategies.value.length} 个策略？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    const strategyIds = selectedStrategies.value.map(s => s.strategy_id)
    await strategyApi.deleteStrategies(strategyIds)
    
    // 从列表中移除已删除的策略
    selectedStrategies.value.forEach(strategy => {
      const index = strategies.value.findIndex(s => s.strategy_id === strategy.strategy_id)
      if (index > -1) {
        strategies.value.splice(index, 1)
      }
    })
    
    selectedStrategies.value = []
    ElMessage.success('批量删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 子组件事件处理
const handleStrategySave = (strategy: Strategy) => {
  if (editingStrategy.value) {
    // 更新现有策略
    const index = strategies.value.findIndex(s => s.strategy_id === editingStrategy.value!.strategy_id)
    if (index > -1) {
      strategies.value[index] = strategy
    }
    editingStrategy.value = null
  } else {
    // 添加新策略
    strategies.value.unshift(strategy)
  }
  
  showStrategyBuilder.value = false
  ElMessage.success('策略保存成功')
}

const handleAIGenerate = (strategy: Strategy) => {
  strategies.value.unshift(strategy)
  showAIGenerator.value = false
  ElMessage.success('AI策略生成成功')
}

const handleStrategyImport = (importedStrategies: Strategy[]) => {
  strategies.value.unshift(...importedStrategies)
  showImportDialog.value = false
  ElMessage.success(`成功导入 ${importedStrategies.length} 个策略`)
}

const editStrategyCode = (strategy: Strategy) => {
  showCodeViewer.value = false
  editingStrategy.value = strategy
  showStrategyBuilder.value = true
}

// 创建策略处理
const handleCreateStrategy = (event?: Event) => {
  console.log('handleCreateStrategy called', event)
  try {
    if (event) {
      event.preventDefault()
      event.stopPropagation()
    }
    editingStrategy.value = null
    showStrategyBuilder.value = true
    console.log('showStrategyBuilder set to:', showStrategyBuilder.value)
    // 使用 nextTick 确保对话框能正确显示
    nextTick(() => {
      console.log('Dialog should be visible now')
    })
  } catch (error) {
    console.error('Error in handleCreateStrategy:', error)
    ElMessage.error('打开策略构建器失败: ' + (error as Error).message)
  }
}

// AI生成策略处理
const handleAIGenerateStrategy = () => {
  showAIGenerator.value = true
}

// 生命周期
onMounted(() => {
  refreshStrategies()
  // 默认设置回测日期为最近一个月
  applyQuickRange('1m')
})
</script>

<style lang="scss" scoped>
.strategy-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

// 页面头部
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
  color: white;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .title-section {
    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 28px;
      font-weight: 600;
      margin: 0 0 8px 0;
      
      .el-icon {
        font-size: 32px;
      }
    }
    
    .page-description {
      font-size: 16px;
      opacity: 0.9;
      margin: 0;
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

// 仪表板
.dashboard-section {
  margin-bottom: 24px;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }
  
  .metric-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20px;
    
    .el-icon {
      font-size: 28px;
      color: white;
    }
  }
  
  .metric-content {
    flex: 1;
  }
  
  .metric-value {
    font-size: 32px;
    font-weight: 700;
    color: #1f2937;
    line-height: 1;
    margin-bottom: 4px;
    font-family: 'Courier New', monospace;
  }
  
  .metric-label {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 8px;
  }
  
  .metric-trend {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .trend-up { color: #10b981; }
    .trend-down { color: #ef4444; }
    .trend-neutral { color: #6b7280; }
    .trend-text { 
      font-size: 12px; 
      color: #9ca3af; 
    }
  }
  
  &.total-strategies .metric-icon {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  &.active-strategies .metric-icon {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  }
  
  &.total-return .metric-icon {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  }
  
  &.sharpe-ratio .metric-icon {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  }
}

// 工具栏
.strategy-toolbar {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  
  .filter-section {
    display: flex;
    gap: 12px;
    align-items: center;
  }
  
  .action-section {
    display: flex;
    gap: 8px;
  }
}

// 策略列表
.strategy-list-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.strategy-table {
  .strategy-info {
    .strategy-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .strategy-name {
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
      }
      
      .strategy-badges {
        display: flex;
        gap: 6px;
      }
    }
    
    .strategy-description {
      font-size: 14px;
      color: #6b7280;
      margin-bottom: 12px;
      line-height: 1.4;
    }
    
    .strategy-meta {
      display: flex;
      gap: 16px;
      
      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #9ca3af;
        
        .el-icon {
          font-size: 14px;
        }
      }
    }
  }
  
  .performance-metrics {
    .metric-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
      
      .metric-label {
        font-size: 12px;
        color: #6b7280;
      }
      
      .metric-value {
        font-size: 12px;
        font-weight: 600;
        font-family: 'Courier New', monospace;
        
        &.positive { color: #10b981; }
        &.negative { color: #ef4444; }
      }
    }
  }
  
  .backtest-info {
    text-align: center;
    
    .backtest-count {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      font-size: 14px;
      color: #6b7280;
      margin-bottom: 4px;
    }
    
    .last-backtest {
      font-size: 12px;
      color: #9ca3af;
    }
  }
  
  .action-buttons {
    display: flex;
    gap: 8px;
    align-items: center;
    
    .status-controls {
      .el-button {
        padding: 6px 8px;
      }
    }
  }
}

// 分页
.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

// 对话框样式
.strategy-builder-dialog,
.ai-generator-dialog {
  :deep(.el-dialog__body) {
    padding: 0;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .strategy-container {
    padding: 16px;
  }
  
  .page-header {
    padding: 20px;
    
    .header-content {
      flex-direction: column;
      gap: 16px;
      text-align: center;
    }
    
    .header-actions {
      width: 100%;
      justify-content: center;
    }
  }
  
  .metric-card {
    margin-bottom: 16px;
  }
  
  .strategy-toolbar {
    flex-direction: column;
    gap: 16px;
    
    .filter-section,
    .action-section {
      width: 100%;
      justify-content: center;
      flex-wrap: wrap;
    }
  }
  
  .strategy-table {
    .el-table__body-wrapper {
      overflow-x: auto;
    }
  }
}
</style>