<template>
  <div class="dashboard-container">
    <div class="page-header">
      <h1 class="page-title">仪表盘</h1>
      <p class="page-description">欢迎使用股票AI交易系统</p>
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
              {{ totalPnl >= 0 ? '+' : '' }}¥{{ formatNumber(totalPnl) }}
            </div>
            <div class="card-subtitle" :class="totalPnl >= 0 ? 'stock-up' : 'stock-down'">
              {{ totalPnl >= 0 ? '+' : '' }}{{ (totalPnlRatio * 100).toFixed(2) }}%
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    
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
            <v-chart :option="positionChartOption" style="height: 300px;" />
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
            <el-link type="primary" @click="$router.push('/trading')">
              查看全部
            </el-link>
          </div>
          <el-table :data="recentOrders" style="width: 100%">
            <el-table-column prop="symbol" label="股票" width="80" />
            <el-table-column prop="side" label="方向" width="60">
              <template #default="{ row }">
                <el-tag :type="row.side === 'buy' ? 'danger' : 'success'" size="small">
                  {{ row.side === 'buy' ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="price" label="价格" width="80">
              <template #default="{ row }">
¥{{ row.price ? row.price.toFixed(2) : '0.00' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag
                  size="small"
                >
                  {{ getOrderStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>持仓概览</h3>
            <el-link type="primary" @click="$router.push('/portfolio')">
              查看全部
            </el-link>
          </div>
          <el-table :data="topPositions" style="width: 100%">
            <el-table-column prop="symbol" label="股票" width="80" />
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="market_value" label="市值" width="100">
              <template #default="{ row }">
                ¥{{ formatNumber(row.market_value) }}
              </template>
            </el-table-column>
            <el-table-column prop="unrealized_pnl" label="盈亏">
              <template #default="{ row }">
                <span :class="row.unrealized_pnl >= 0 ? 'stock-up' : 'stock-down'">
                  {{ row.unrealized_pnl >= 0 ? '+' : '' }}¥{{ formatNumber(row.unrealized_pnl) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="unrealized_pnl_ratio" label="收益率">
              <template #default="{ row }">
                <span :class="row.unrealized_pnl_ratio >= 0 ? 'stock-up' : 'stock-down'">
                  {{ row.unrealized_pnl_ratio >= 0 ? '+' : '' }}{{ (row.unrealized_pnl_ratio * 100).toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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

// 计算属性
const totalAssets = computed(() => tradingStore.totalAssets)
const availableCash = computed(() => tradingStore.availableCash)
const marketValue = computed(() => tradingStore.marketValue)
const totalPnl = computed(() => tradingStore.totalPnl)
const totalPnlRatio = computed(() => tradingStore.totalPnlRatio)

const recentOrders = computed(() => 
  tradingStore.orders.slice(0, 5)
)

const topPositions = computed(() => {
  // 确保positions是数组
  const positions = Array.isArray(tradingStore.positions) ? tradingStore.positions : []
  return positions
    .sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
    .slice(0, 5)
})
const positionsAll = computed(() => {
  return Array.isArray(tradingStore.positions) ? tradingStore.positions : []
})

// 图表配置
const assetChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['09:30', '10:00', '10:30', '11:00', '11:30', '13:00', '13:30', '14:00', '14:30', '15:00']
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: (value: number) => `¥${formatNumber(value)}`
    }
  },
  series: [{
    data: [100000, 101200, 99800, 102500, 103000, 102800, 104200, 103500, 105000, 106000],
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
    formatter: '{a} <br/>{b}: ¥{c} ({d}%)'
  },
  series: [{
    name: '持仓分布',
    type: 'pie',
    radius: ['40%', '70%'],
    data: positionsAll.value.map(p => ({ value: p.market_value || 0, name: p.symbol })),
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowColor: 'rgba(0, 0, 0, 0.5)'
      }
    }
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
  tradingStore.initialize()
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 24px;
}

.overview-cards {
  margin-bottom: 24px;
}

.overview-card {
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
  margin-bottom: 4px;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-family: 'Courier New', monospace;
}

.card-subtitle {
  font-size: 12px;
  margin-top: 4px;
}

.charts-section,
.data-section {
  margin-bottom: 24px;
}

.card {
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 20px;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

.chart-container {
  width: 100%;
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .overview-card {
    margin-bottom: 16px;
  }
  
  .card-value {
    font-size: 20px;
  }
}
</style>
