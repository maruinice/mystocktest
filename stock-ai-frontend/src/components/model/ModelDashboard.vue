<template>
  <div class="model-dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <div class="stat-card total-models">
          <div class="card-icon">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">总模型数</div>
            <div class="card-value">{{ dashboardStats.total_models }}</div>
            <div class="card-trend" :class="{ positive: modelTrend > 0, negative: modelTrend < 0 }">
              <el-icon v-if="modelTrend > 0"><TrendCharts /></el-icon>
              <el-icon v-else-if="modelTrend < 0"><Bottom /></el-icon>
              <span>{{ modelTrend > 0 ? '+' : '' }}{{ modelTrend }}</span>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="6">
        <div class="stat-card active-models">
          <div class="card-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">活跃模型</div>
            <div class="card-value">{{ dashboardStats.active_models }}</div>
            <div class="card-subtitle">
              活跃率: {{ activeRate }}%
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="6">
        <div class="stat-card avg-accuracy">
          <div class="card-icon">
            <el-icon><Trophy /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">平均准确率</div>
            <div class="card-value">{{ ((dashboardStats.avg_accuracy || 0) * 100).toFixed(1) }}%</div>
            <div class="card-progress">
              <el-progress
                :percentage="(dashboardStats.avg_accuracy || 0) * 100"
                :color="getAccuracyColor(dashboardStats.avg_accuracy || 0)"
                :stroke-width="4"
                :show-text="false"
              />
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="6">
        <div class="stat-card total-requests">
          <div class="card-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">总请求数</div>
            <div class="card-value">{{ formatNumber(dashboardStats.total_requests) }}</div>
            <div class="card-subtitle">
              成功率: {{ ((dashboardStats.success_rate || 0) * 100).toFixed(1) }}%
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <!-- 模型类型分布图 -->
      <el-col :span="8">
        <div class="chart-card">
          <div class="card-header">
            <h4>模型类型分布</h4>
            <el-button size="small" @click="refreshModelTypeChart">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="chart-container" ref="modelTypeChartRef"></div>
        </div>
      </el-col>
      
      <!-- 性能趋势图 -->
      <el-col :span="16">
        <div class="chart-card">
          <div class="card-header">
            <h4>性能趋势</h4>
            <div class="header-controls">
              <el-select
                v-model="trendTimeRange"
                size="small"
                style="width: 120px; margin-right: 8px"
                @change="refreshPerformanceTrend"
              >
                <el-option label="最近7天" value="7d" />
                <el-option label="最近30天" value="30d" />
                <el-option label="最近90天" value="90d" />
              </el-select>
              <el-button size="small" @click="refreshPerformanceTrend">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </div>
          <div class="chart-container" ref="performanceTrendChartRef"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="bottom-row">
      <!-- 模型排行榜 -->
      <el-col :span="12">
        <div class="ranking-card">
          <div class="card-header">
            <h4>模型性能排行</h4>
            <el-select
              v-model="rankingMetric"
              size="small"
              style="width: 120px"
              @change="refreshRanking"
            >
              <el-option label="准确率" value="accuracy" />
              <el-option label="响应时间" value="response_time" />
              <el-option label="使用次数" value="usage_count" />
            </el-select>
          </div>
          
          <div class="ranking-list">
            <div
              v-for="(model, index) in modelRanking"
              :key="model.model_id"
              class="ranking-item"
            >
              <div class="rank-number" :class="`rank-${index + 1}`">
                {{ index + 1 }}
              </div>
              <div class="model-info">
                <div class="model-name">{{ model.name }}</div>
                <div class="model-type">
                  <el-tag size="small" :type="getModelTypeColor(model.model_type)">
                    {{ getModelTypeText(model.model_type) }}
                  </el-tag>
                </div>
              </div>
              <div class="metric-value">
                <span v-if="rankingMetric === 'accuracy'">
                  {{ ((model.accuracy || 0) * 100).toFixed(1) }}%
                </span>
                <span v-else-if="rankingMetric === 'response_time'">
                  {{ model.response_time?.toFixed(2) }}s
                </span>
                <span v-else>
                  {{ formatNumber(model.usage_count || 0) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      
      <!-- 最近活动 -->
      <el-col :span="12">
        <div class="activity-card">
          <div class="card-header">
            <h4>最近活动</h4>
            <el-button size="small" @click="refreshRecentActivity">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          
          <div class="activity-list">
            <div
              v-for="activity in recentActivities"
              :key="activity.id"
              class="activity-item"
            >
              <div class="activity-icon" :class="activity.type">
                <el-icon v-if="activity.type === 'model_created'">
                  <Plus />
                </el-icon>
                <el-icon v-else-if="activity.type === 'model_tested'">
                  <ChatDotRound />
                </el-icon>
                <el-icon v-else-if="activity.type === 'ensemble_created'">
                  <Collection />
                </el-icon>
                <el-icon v-else>
                  <Operation />
                </el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-description">{{ activity.description }}</div>
                <div class="activity-time">
                  {{ formatDateTime(activity.timestamp) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { formatDateTime } from '../../utils/format'
import { getTagType } from '../../utils/element-plus'
import {
  modelManagementAPI,
  type PerformanceStats,
  type AIModel,
  ModelType
} from '../../api/model-management'

// 响应式数据
const _loading = ref(false)
const trendTimeRange = ref('7d')
const rankingMetric = ref('accuracy')

// 图表引用
const modelTypeChartRef = ref<HTMLElement>()
const performanceTrendChartRef = ref<HTMLElement>()

// 图表实例
let modelTypeChart: echarts.ECharts | null = null
let performanceTrendChart: echarts.ECharts | null = null

// 仪表盘统计数据
const dashboardStats = ref<PerformanceStats>({
  total_models: 0,
  active_models: 0,
  avg_accuracy: 0,
  avg_response_time: 0,
  total_requests: 0,
  success_rate: 0
})

// 模型排行数据
const modelRanking = ref<AIModel[]>([])

// 最近活动数据
interface Activity {
  id: string
  type: 'model_created' | 'model_tested' | 'ensemble_created' | 'other'
  title: string
  description: string
  timestamp: string
}

const recentActivities = ref<Activity[]>([])

// 趋势数据
const modelTrend = ref(0)

// 计算属性
const activeRate = computed(() => {
  if (!dashboardStats.value || dashboardStats.value.total_models === 0) return 0
  return Math.round(((dashboardStats.value.active_models || 0) / dashboardStats.value.total_models) * 100)
})

// 方法
const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const getAccuracyColor = (accuracy: number) => {
  if (accuracy >= 0.9) return '#67C23A'
  if (accuracy >= 0.8) return '#E6A23C'
  if (accuracy >= 0.7) return '#F56C6C'
  return '#909399'
}

const getModelTypeText = (type: ModelType) => {
  const typeMap = {
    [ModelType.DEEPSEEK]: 'DeepSeek',
    [ModelType.OPENAI]: 'OpenAI',
    [ModelType.CLAUDE]: 'Claude',
    [ModelType.CUSTOM]: '自定义'
  }
  return typeMap[type] || type
}

const getModelTypeColor = (type: ModelType): TagType => {
  const colorMap = {
    [ModelType.DEEPSEEK]: 'primary',
    [ModelType.OPENAI]: 'success',
    [ModelType.CLAUDE]: 'warning',
    [ModelType.CUSTOM]: 'info'
  }
  return getTagType(colorMap[type] || 'info')
}

// 加载仪表盘统计数据
const loadDashboardStats = async () => {
  try {
    const response = await modelManagementAPI.getDashboardStats()
    
    if (response.success && response.data) {
      dashboardStats.value = response.data
    }
  } catch (error) {
    console.error('加载仪表盘统计失败:', error)
    ElMessage.error('加载仪表盘统计失败')
  }
}

// 加载模型排行
const loadModelRanking = async () => {
  try {
    const response = await modelManagementAPI.getModels({ per_page: 10 })
    
    if (response.success && response.data) {
      let models = response.data.items
      
      // 根据选择的指标排序
      models.sort((a, b) => {
        switch (rankingMetric.value) {
          case 'accuracy':
            return (b.accuracy || 0) - (a.accuracy || 0)
          case 'response_time':
            return (a.response_time || Infinity) - (b.response_time || Infinity)
          case 'usage_count':
            return (b.usage_count || 0) - (a.usage_count || 0)
          default:
            return 0
        }
      })
      
      modelRanking.value = models.slice(0, 5)
    }
  } catch (error) {
    console.error('加载模型排行失败:', error)
  }
}

// 加载最近活动
const loadRecentActivity = async () => {
  // 模拟最近活动数据
  recentActivities.value = [
    {
      id: '1',
      type: 'model_created',
      title: '创建新模型',
      description: 'DeepSeek Chat 模型已成功创建',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString()
    },
    {
      id: '2',
      type: 'model_tested',
      title: '模型测试完成',
      description: 'GPT-4 模型测试，准确率 92.5%',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString()
    },
    {
      id: '3',
      type: 'ensemble_created',
      title: '创建模型组合',
      description: '多模型融合组合已创建，包含3个模型',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString()
    },
    {
      id: '4',
      type: 'other',
      title: '系统优化',
      description: '模型响应时间优化完成，平均提升15%',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 8).toISOString()
    }
  ]
}

// 初始化模型类型分布图
const initModelTypeChart = async () => {
  if (!modelTypeChartRef.value) return

  modelTypeChart = echarts.init(modelTypeChartRef.value)
  
  // 模拟数据
  const data = [
    { name: 'DeepSeek', value: 3, color: '#409EFF' },
    { name: 'OpenAI', value: 2, color: '#67C23A' },
    { name: 'Claude', value: 2, color: '#E6A23C' },
    { name: '自定义', value: 1, color: '#909399' }
  ]

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '模型类型',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: data.map(item => ({
          ...item,
          itemStyle: { color: item.color }
        }))
      }
    ]
  }

  modelTypeChart.setOption(option)
}

// 初始化性能趋势图
const initPerformanceTrendChart = async () => {
  if (!performanceTrendChartRef.value) return

  performanceTrendChart = echarts.init(performanceTrendChartRef.value)
  
  // 模拟数据
  const dates = []
  const accuracyData = []
  const responseTimeData = []
  
  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toLocaleDateString())
    accuracyData.push((Math.random() * 0.2 + 0.8).toFixed(3))
    responseTimeData.push((Math.random() * 0.5 + 1.0).toFixed(2))
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      }
    },
    legend: {
      data: ['准确率', '响应时间'],
      textStyle: {
        fontSize: 12
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLabel: {
          fontSize: 11
        }
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: '准确率',
        min: 0.7,
        max: 1.0,
        position: 'left',
        axisLabel: {
          formatter: '{value}',
          fontSize: 11
        }
      },
      {
        type: 'value',
        name: '响应时间(s)',
        min: 0.5,
        max: 2.0,
        position: 'right',
        axisLabel: {
          formatter: '{value}s',
          fontSize: 11
        }
      }
    ],
    series: [
      {
        name: '准确率',
        type: 'line',
        smooth: true,
        itemStyle: {
          color: '#67C23A'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
          ])
        },
        data: accuracyData
      },
      {
        name: '响应时间',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        itemStyle: {
          color: '#E6A23C'
        },
        data: responseTimeData
      }
    ]
  }

  performanceTrendChart.setOption(option)
}

// 刷新方法
const refreshModelTypeChart = () => {
  initModelTypeChart()
}

const refreshPerformanceTrend = () => {
  initPerformanceTrendChart()
}

const refreshRanking = () => {
  loadModelRanking()
}

const refreshRecentActivity = () => {
  loadRecentActivity()
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  if (modelTypeChart) {
    modelTypeChart.resize()
  }
  if (performanceTrendChart) {
    performanceTrendChart.resize()
  }
}

// 组件挂载时初始化
onMounted(async () => {
  await Promise.all([
    loadDashboardStats(),
    loadModelRanking(),
    loadRecentActivity()
  ])
  
  await nextTick()
  
  // 初始化图表
  initModelTypeChart()
  initPerformanceTrendChart()
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
onUnmounted(() => {
  if (modelTypeChart) {
    modelTypeChart.dispose()
  }
  if (performanceTrendChart) {
    performanceTrendChart.dispose()
  }
  
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.model-dashboard {
  padding: 20px;
  
  .stats-cards {
    margin-bottom: 20px;
  }
  
  .stat-card {
    background: var(--el-bg-color-overlay);
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    padding: 20px;
    display: flex;
    align-items: center;
    transition: all 0.3s ease;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .card-icon {
      width: 48px;
      height: 48px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 16px;
      
      .el-icon {
        font-size: 24px;
        color: white;
      }
    }
    
    .card-content {
      flex: 1;
      
      .card-title {
        font-size: 14px;
        color: var(--el-text-color-regular);
        margin-bottom: 4px;
      }
      
      .card-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        font-family: 'Courier New', monospace;
        margin-bottom: 4px;
      }
      
      .card-subtitle {
        font-size: 12px;
        color: var(--el-text-color-regular);
      }
      
      .card-trend {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        
        &.positive {
          color: #67C23A;
        }
        
        &.negative {
          color: #F56C6C;
        }
      }
      
      .card-progress {
        margin-top: 8px;
      }
    }
    
    &.total-models .card-icon {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    &.active-models .card-icon {
      background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    
    &.avg-accuracy .card-icon {
      background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }
    
    &.total-requests .card-icon {
      background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    }
  }
  
  .charts-row,
  .bottom-row {
    margin-bottom: 20px;
  }
  
  .chart-card,
  .ranking-card,
  .activity-card {
    background: var(--el-bg-color-overlay);
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    padding: 20px;
    height: 400px;
    display: flex;
    flex-direction: column;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--el-border-color-light);
      
      h4 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
      
      .header-controls {
        display: flex;
        align-items: center;
      }
    }
    
    .chart-container {
      flex: 1;
      min-height: 300px;
    }
  }
  
  .ranking-list,
  .activity-list {
    flex: 1;
    overflow-y: auto;
  }
  
  .ranking-item {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    &:last-child {
      border-bottom: none;
    }
    
    .rank-number {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      color: white;
      margin-right: 12px;
      
      &.rank-1 {
        background: #FFD700;
      }
      
      &.rank-2 {
        background: #C0C0C0;
      }
      
      &.rank-3 {
        background: #CD7F32;
      }
      
      &:not(.rank-1):not(.rank-2):not(.rank-3) {
        background: var(--el-color-info);
      }
    }
    
    .model-info {
      flex: 1;
      
      .model-name {
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
    }
    
    .metric-value {
      font-weight: 600;
      color: var(--el-text-color-primary);
      font-family: 'Courier New', monospace;
    }
  }
  
  .activity-item {
    display: flex;
    align-items: flex-start;
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    &:last-child {
      border-bottom: none;
    }
    
    .activity-icon {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 12px;
      
      .el-icon {
        font-size: 16px;
        color: white;
      }
      
      &.model_created {
        background: #67C23A;
      }
      
      &.model_tested {
        background: #409EFF;
      }
      
      &.ensemble_created {
        background: #E6A23C;
      }
      
      &.other {
        background: #909399;
      }
    }
    
    .activity-content {
      flex: 1;
      
      .activity-title {
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .activity-description {
        font-size: 13px;
        color: var(--el-text-color-regular);
        margin-bottom: 4px;
      }
      
      .activity-time {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}
</style>