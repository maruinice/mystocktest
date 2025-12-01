<template>
  <div class="dashboard-container">
    <div class="page-header">
      <h1 class="page-title">仪表盘</h1>
      <p class="page-description">
        欢迎使用迅龙AI股票交易系统
        <el-tag size="small" type="success" class="ml-2">
          实时行情
        </el-tag>
      </p>
    </div>
    
    <!-- 概览卡片 -->
    <el-row :gutter="16" class="overview-cards">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="overview-card">
          <div class="card-icon total-assets">
            <el-icon><Money /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">总资产</div>
            <div class="card-value">¥{{ formatNumber(totalAssets) }}</div>
            <div class="card-subtitle">
              <el-icon><TrendCharts /></el-icon>
              {{ totalAssets >= 100000 ? '+' : '' }}{{ ((totalAssets - 100000) / 1000).toFixed(2) }}k
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="overview-card">
          <div class="card-icon available-cash">
            <el-icon><Wallet /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">可用资金</div>
            <div class="card-value">¥{{ formatNumber(availableCash) }}</div>
            <div class="card-subtitle">
              占比 {{ ((availableCash / totalAssets) * 100).toFixed(1) }}%
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="overview-card">
          <div class="card-icon market-value">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">持仓市值</div>
            <div class="card-value">¥{{ formatNumber(marketValue) }}</div>
            <div class="card-subtitle">
              {{ positionsAll.length }} 只股票
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="overview-card">
          <div class="card-icon total-pnl" :class="totalPnl >= 0 ? 'profit' : 'loss'">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">总盈亏</div>
            <div class="card-value" :class="totalPnl >= 0 ? 'stock-up' : 'stock-down'">
              {{ totalPnl >= 0 ? '+' : '' }}¥{{ formatNumber(Math.abs(totalPnl)) }}
            </div>
            <div class="card-subtitle" :class="totalPnl >= 0 ? 'stock-up' : 'stock-down'">
              {{ totalPnl >= 0 ? '+' : '' }}{{ (totalPnlRatio * 100).toFixed(2) }}%
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 市场热点 -->
    <div class="card mb-4">
      <div class="card-header">
        <h3>
          <el-icon><TrendCharts /></el-icon>
          市场热点
          <el-tag v-if="marketRefreshInterval > 0" size="small" type="success" class="ml-2">
            自动刷新 {{ marketRefreshInterval }}秒
          </el-tag>
        </h3>
        <div class="header-actions">
          <el-select 
            v-model="hotspotSource" 
            size="small" 
            style="width: 120px; margin-right: 8px"
            @change="fetchMarketHotStocks"
          >
            <el-option label="涨幅榜" value="gainers" />
            <el-option label="跌幅榜" value="losers" />
            <el-option label="成交量榜" value="volume" />
            <el-option label="换手率榜" value="turnover" />
          </el-select>
          <el-select 
            v-model="hotspotLimit" 
            size="small" 
            style="width: 100px; margin-right: 8px"
            @change="fetchMarketHotStocks"
            allow-create
            filterable
            default-first-option
          >
            <el-option label="4条" :value="4" />
            <el-option label="8条" :value="8" />
            <el-option label="12条" :value="12" />
            <el-option label="16条" :value="16" />
            <el-option label="20条" :value="20" />
          </el-select>
          <el-select 
            v-model="marketRefreshInterval" 
            size="small" 
            style="width: 120px; margin-right: 8px"
            @change="updateMarketRefreshInterval"
          >
            <el-option label="不刷新" :value="0" />
            <el-option label="5秒" :value="5" />
            <el-option label="10秒" :value="10" />
            <el-option label="30秒" :value="30" />
            <el-option label="60秒" :value="60" />
          </el-select>
          <el-button size="small" @click="refreshMarketData" :loading="marketLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="6" v-for="stock in marketHotStocks" :key="stock.code">
          <div class="market-stock-card">
            <div class="stock-header">
              <span class="stock-code">{{ stock.code }}</span>
              <el-tag :type="stock.change_pct >= 0 ? 'danger' : 'success'" size="small">
                {{ stock.change_pct >= 0 ? '+' : '' }}{{ stock.change_pct.toFixed(2) }}%
              </el-tag>
            </div>
            <div class="stock-name">{{ stock.name }}</div>
            <div class="stock-price" :class="stock.change_pct >= 0 ? 'price-up' : 'price-down'">
              ¥{{ stock.price.toFixed(2) }}
            </div>
            <div class="stock-info">
              <span v-if="stock.turnover_rate">换手率: {{ stock.turnover_rate.toFixed(2) }}%</span>
              <span v-if="stock.volume">成交量: {{ formatVolume(stock.volume) }}</span>
            </div>
          </div>
        </el-col>
      </el-row>
      <el-empty v-if="marketHotStocks.length === 0 && !marketLoading" description="暂无数据" :image-size="80" />
    </div>
    
    <!-- 图表和数据 -->
    <el-row :gutter="16" class="charts-section">
      <el-col :xs="24" :lg="16">
        <div class="card">
          <div class="card-header">
            <h3>资产趋势</h3>
            <el-radio-group v-model="chartPeriod" size="small">
              <el-radio-button label="1D">日</el-radio-button>
              <el-radio-button label="1W">周</el-radio-button>
              <el-radio-button label="1M">月</el-radio-button>
              <el-radio-button label="3M">季</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-container">
            <v-chart :option="assetChartOption" style="height: 300px;" />
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <div class="card">
          <div class="card-header">
            <h3>持仓分布</h3>
          </div>
          <div class="chart-container">
            <v-chart v-if="positionsAll.length > 0" :option="positionChartOption" style="height: 300px;" />
            <div v-else class="empty-chart">
              <el-icon><PieChartIcon /></el-icon>
              <p>暂无持仓</p>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 最新订单和持仓 -->
    <el-row :gutter="16" class="data-section">
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>最新订单</h3>
            <el-link type="primary" @click="$router.push('/admin/trading')">
              查看全部
            </el-link>
          </div>
          <el-table :data="recentOrders" style="width: 100%" v-if="recentOrders.length > 0">
            <el-table-column prop="code" label="股票" width="100">
              <template #default="{ row }">
                <div>
                  <div class="stock-code-small">{{ row.code || row.symbol }}</div>
                  <div class="stock-name-small">{{ row.name }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="side" label="方向" width="60">
              <template #default="{ row }">
                <el-tag :type="row.side === 'buy' ? 'danger' : 'success'" size="small">
                  {{ row.side === 'buy' ? '买' : '卖' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="price" label="价格" width="120">
              <template #default="{ row }">
                <div v-if="row.status === 'filled'">
                  <span class="text-success">成交: ¥{{ (row.avg_price || row.price).toFixed(2) }}</span>
                </div>
                <div v-else>
                  <span class="text-secondary">委托: ¥{{ row.price.toFixed(2) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getOrderStatusType(row.status)" size="small">
                  {{ getOrderStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无订单" :image-size="100" />
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>持仓概览</h3>
            <el-link type="primary" @click="$router.push('/admin/portfolio')">
              查看全部
            </el-link>
          </div>
          <el-table :data="topPositions" style="width: 100%" v-if="topPositions.length > 0">
            <el-table-column prop="symbol" label="股票" width="100">
              <template #default="{ row }">
                <div>
                  <div class="stock-code-small">{{ row.code || row.symbol }}</div>
                  <div class="stock-name-small">{{ row.name }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="current_price" label="现价" width="90">
              <template #default="{ row }">
                <span :class="row.profit_loss >= 0 ? 'price-up' : 'price-down'">
                  ¥{{ row.current_price ? row.current_price.toFixed(2) : row.last_price ? row.last_price.toFixed(2) : '0.00' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="profit_loss" label="盈亏">
              <template #default="{ row }">
                <div>
                  <div :class="row.profit_loss >= 0 ? 'stock-up' : 'stock-down'">
                    {{ row.profit_loss >= 0 ? '+' : '' }}¥{{ Math.abs(row.profit_loss || 0).toFixed(2) }}
                  </div>
                  <div class="profit-pct" :class="row.profit_loss_pct >= 0 ? 'stock-up' : 'stock-down'">
                    {{ row.profit_loss_pct >= 0 ? '+' : '' }}{{ (row.profit_loss_pct || 0).toFixed(2) }}%
                  </div>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无持仓" :image-size="100" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { 
  Money, 
  Wallet, 
  TrendCharts, 
  DataAnalysis, 
  Refresh,
  PieChart as PieChartIcon
} from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useTradingStore } from '@/stores/trading'
import { formatNumber } from '@/utils/format'
import axios from 'axios'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const tradingStore = useTradingStore()
const chartPeriod = ref('1D')
const marketLoading = ref(false)
const marketHotStocks = ref<any[]>([])
const marketRefreshInterval = ref(30) // 默认30秒
const hotspotSource = ref('gainers') // 默认涨幅榜
const hotspotLimit = ref(8) // 默认8条
let refreshTimer: number | null = null

// 计算属性
const totalAssets = computed(() => tradingStore.totalAssets || 100000)
const availableCash = computed(() => tradingStore.availableCash || 0)
const marketValue = computed(() => tradingStore.marketValue || 0)
const totalPnl = computed(() => tradingStore.totalPnl || 0)
const totalPnlRatio = computed(() => tradingStore.totalPnlRatio || 0)

const recentOrders = computed(() => {
  const orders = tradingStore.orders || []
  return orders.slice(0, 5)
})

const topPositions = computed(() => {
  const positions = Array.isArray(tradingStore.positions) ? tradingStore.positions : []
  return positions
    .sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
    .slice(0, 5)
})

const positionsAll = computed(() => {
  return Array.isArray(tradingStore.positions) ? tradingStore.positions : []
})

// 获取市场热点股票
const fetchMarketHotStocks = async () => {
  marketLoading.value = true
  try {
    const response = await axios.get('/api/market/hotspots', {
      params: {
        source: hotspotSource.value,
        limit: hotspotLimit.value
        // 不传 trade_date，让后端自动使用最新交易日
      }
    })
    
    if (response.data.success) {
      marketHotStocks.value = response.data.data.hotspots || []
    }
  } catch (error) {
    console.error('获取市场热点失败:', error)
    marketHotStocks.value = []
  } finally {
    marketLoading.value = false
  }
}

const refreshMarketData = () => {
  fetchMarketHotStocks()
  tradingStore.fetchPositions()
}

// 更新刷新间隔
const updateMarketRefreshInterval = () => {
  // 清除旧的定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  
  // 设置新的定时器
  if (marketRefreshInterval.value > 0) {
    refreshTimer = window.setInterval(() => {
      fetchMarketHotStocks()
    }, marketRefreshInterval.value * 1000)
  }
  
  // 保存到localStorage
  localStorage.setItem('marketRefreshInterval', marketRefreshInterval.value.toString())
}

// 格式化成交量
const formatVolume = (volume: number) => {
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万'
  }
  return volume.toString()
}

// 图表配置
const assetChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: ['09:30', '10:00', '10:30', '11:00', '11:30', '13:00', '13:30', '14:00', '14:30', '15:00'],
    boundaryGap: false
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: (value: number) => `¥${formatNumber(value)}`
    }
  },
  series: [{
    data: [
      totalAssets.value * 0.98,
      totalAssets.value * 0.99,
      totalAssets.value * 0.97,
      totalAssets.value * 1.01,
      totalAssets.value * 1.02,
      totalAssets.value * 1.01,
      totalAssets.value * 1.03,
      totalAssets.value * 1.02,
      totalAssets.value * 1.04,
      totalAssets.value
    ],
    type: 'line',
    smooth: true,
    itemStyle: {
      color: '#409eff'
    },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [{
          offset: 0, color: 'rgba(64, 158, 255, 0.3)'
        }, {
          offset: 1, color: 'rgba(64, 158, 255, 0.1)'
        }]
      }
    }
  }]
}))

const positionChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: ¥{c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    right: 10,
    top: 'center',
    textStyle: {
      fontSize: 12
    }
  },
  series: [{
    name: '持仓分布',
    type: 'pie',
    radius: ['40%', '70%'],
    avoidLabelOverlap: false,
    label: {
      show: false
    },
    emphasis: {
      label: {
        show: true,
        fontSize: 14,
        fontWeight: 'bold'
      }
    },
    data: positionsAll.value.map(p => ({
      value: p.market_value || 0,
      name: `${p.code || p.symbol} ${p.name || ''}`
    }))
  }]
}))

// 工具函数
const getOrderStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'warning',
    filled: 'success',
    cancelled: 'info',
    rejected: 'danger'
  }
  return statusMap[status] || 'info'
}

const getOrderStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待成交',
    filled: '已成交',
    cancelled: '已撤销',
    rejected: '已拒绝'
  }
  return statusMap[status] || status
}

onMounted(() => {
  // 从localStorage读取刷新间隔设置
  const savedInterval = localStorage.getItem('marketRefreshInterval')
  if (savedInterval) {
    marketRefreshInterval.value = parseInt(savedInterval)
  }
  
  tradingStore.initialize()
  fetchMarketHotStocks()
  
  // 启动自动刷新
  updateMarketRefreshInterval()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
  
  .page-title {
    font-size: 28px;
    font-weight: 600;
    margin-bottom: 8px;
  }
  
  .page-description {
    color: var(--el-text-color-secondary);
    display: flex;
    align-items: center;
  }
}

.overview-cards {
  margin-bottom: 24px;
}

.overview-card {
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  height: 100%;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  
  .el-icon {
    font-size: 28px;
    color: white;
  }
  
  &.total-assets {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  &.available-cash {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }
  
  &.market-value {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  }
  
  &.total-pnl {
    &.profit {
      background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    
    &.loss {
      background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }
  }
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.card-value {
  font-size: 26px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-family: 'Courier New', monospace;
  margin-bottom: 4px;
}

.card-subtitle {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.market-stock-card {
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  transition: all 0.3s;
  
  &:hover {
    background: var(--el-fill-color);
    transform: translateY(-2px);
  }
  
  .stock-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .stock-code {
    font-weight: 600;
    font-size: 16px;
  }
  
  .stock-name {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-bottom: 8px;
  }
  
  .stock-price {
    font-size: 22px;
    font-weight: 600;
    font-family: 'Courier New', monospace;
    margin-bottom: 4px;
  }
  
  .stock-volume {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  
  .stock-info {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
}

.charts-section,
.data-section {
  margin-bottom: 24px;
}

.card {
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 20px;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-container {
  width: 100%;
}

.empty-chart {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
  
  .el-icon {
    font-size: 64px;
    margin-bottom: 16px;
  }
}

.stock-code-small {
  font-weight: 600;
  font-size: 14px;
}

.stock-name-small {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.profit-pct {
  font-size: 12px;
  margin-top: 2px;
}

.mb-4 {
  margin-bottom: 24px;
}

.ml-2 {
  margin-left: 8px;
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .overview-card {
    margin-bottom: 16px;
  }
  
  .card-value {
    font-size: 22px;
  }
}
</style>
