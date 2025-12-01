<template>
  <div class="portfolio-container">
    <div class="page-header">
      <h1 class="page-title">投资组合</h1>
      <p class="page-description">管理您的投资组合和持仓</p>
    </div>
    
    <!-- 组合概览 -->
    <el-row :gutter="16" class="portfolio-overview">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="overview-card">
          <div class="card-icon total-value">
            <el-icon><Money /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">总市值</div>
            <div class="card-value">¥{{ formatNumber(totalMarketValue) }}</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="overview-card">
          <div class="card-icon total-cost">
            <el-icon><Wallet /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">总成本</div>
            <div class="card-value">¥{{ formatNumber(totalCost) }}</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="overview-card">
          <div class="card-icon total-pnl" :class="totalPnl >= 0 ? 'profit' : 'loss'">
            <el-icon><TrendCharts /></el-icon>
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
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="overview-card">
          <div class="card-icon position-count">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">持仓数量</div>
            <div class="card-value">{{ positions.length }}</div>
            <div class="card-subtitle">只股票</div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 持仓分布图表 -->
    <el-row :gutter="16" class="charts-section">
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>持仓分布</h3>
          </div>
          <div class="chart-container">
            <v-chart :option="positionDistributionOption" style="height: 300px;" />
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>行业分布</h3>
          </div>
          <div class="chart-container">
            <v-chart :option="industryDistributionOption" style="height: 300px;" />
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 持仓列表 -->
    <div class="card">
      <div class="card-header">
        <h3>持仓明细</h3>
        <div class="header-actions">
          <el-button @click="refreshPositions" size="small">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button @click="exportPositions" size="small">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </div>
      </div>
      
      <el-table :data="positions" v-loading="loading" @row-click="viewStockDetail">
        <el-table-column prop="symbol" label="股票代码" width="180">
          <template #default="{ row }">
            <div class="stock-info">
              <div class="stock-symbol">{{ row.code || row.symbol }}（{{ row.name }}）</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="quantity" label="持仓数量" width="120" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.quantity, 0) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="available_quantity" label="可用数量" width="120" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.available_quantity, 0) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="avg_cost" label="成本价" width="120" align="right">
          <template #default="{ row }">
            <span class="stock-price">¥{{ row.avg_cost.toFixed(2) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="current_price" label="现价" width="120" align="right">
          <template #default="{ row }">
            <span class="stock-price">¥{{ (row.last_price || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="market_value" label="市值" width="140" align="right">
          <template #default="{ row }">
            <span class="stock-price">¥{{ formatNumber(row.market_value) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="profit_loss" label="浮动盈亏" width="140" align="right">
          <template #default="{ row }">
            <div class="pnl-info">
              <div :class="(row.profit_loss || 0) >= 0 ? 'stock-up' : 'stock-down'">
                {{ (row.profit_loss || 0) >= 0 ? '+' : '' }}¥{{ formatNumber(row.profit_loss || 0) }}
              </div>
              <div class="pnl-ratio" :class="(row.profit_loss_pct || 0) >= 0 ? 'stock-up' : 'stock-down'">
                {{ (row.profit_loss_pct || 0) >= 0 ? '+' : '' }}{{ (row.profit_loss_pct || 0).toFixed(2) }}%
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="weight" label="权重" width="100" align="right">
          <template #default="{ row }">
            {{ ((row.market_value / totalMarketValue) * 100).toFixed(2) }}%
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-dropdown @command="handleAction">
              <el-button size="small" text>
                操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{ action: 'buy', symbol: row.symbol }">
                    <el-icon><Plus /></el-icon>
                    买入
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ action: 'sell', symbol: row.symbol }">
                    <el-icon><Minus /></el-icon>
                    卖出
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ action: 'detail', symbol: row.symbol }" divided>
                    <el-icon><View /></el-icon>
                    详情
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 交易记录 -->
    <div class="card mt-4">
      <div class="card-header">
        <h3>最近交易</h3>
        <el-link type="primary" @click="viewAllTrades">
          查看全部
        </el-link>
      </div>
      
      <el-table :data="recentTrades" size="small">
        <el-table-column prop="symbol" label="股票代码" width="100" />
        <el-table-column prop="side" label="方向" width="80">
          <template #default="{ row }">
            <el-tag :type="row.side === 'buy' ? 'danger' : 'success'" size="small">
              {{ row.side === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="100" align="right" />
        <el-table-column prop="price" label="价格" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ formatNumber(row.amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="executed_at" label="成交时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.executed_at) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 股票详情对话框 -->
    <StockDetailDialog 
      v-model="showDetailDialog" 
      :symbol="selectedSymbol"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useTradingStore } from '@/stores/trading'
import { formatNumber, formatDateTime } from '@/utils/format'
import { dataApi } from '@/api/data'
import StockDetailDialog from '@/components/StockDetailDialog.vue'

use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent
])

const router = useRouter()
const tradingStore = useTradingStore()
const loading = ref(false)

// 股票详情对话框
const showDetailDialog = ref(false)
const selectedSymbol = ref('')

// 计算属性
const positions = computed(() => {
  // 确保返回数组
  return Array.isArray(tradingStore.positions) ? tradingStore.positions : []
})
const totalMarketValue = computed(() => 
  positions.value.reduce((sum, pos) => sum + (pos.market_value || 0), 0)
)
const totalCost = computed(() => 
  positions.value.reduce((sum, pos) => sum + ((pos.avg_cost || 0) * (pos.quantity || 0)), 0)
)
const totalPnl = computed(() => totalMarketValue.value - totalCost.value)
const totalPnlRatio = computed(() => 
  totalCost.value > 0 ? totalPnl.value / totalCost.value : 0
)

// 最近交易数据
const recentTrades = computed(() => {
  return tradingStore.filledOrders.slice(0, 10).map(order => ({
    symbol: order.code || order.symbol,
    side: order.side,
    quantity: order.filled_quantity || order.quantity,
    price: order.avg_price || order.price,
    amount: (order.filled_quantity || order.quantity) * (order.avg_price || order.price || 0),
    executed_at: order.updated_at || order.created_at
  }))
})

// 图表配置
const positionDistributionOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: ¥{c} ({d}%)'
  },
  series: [{
    name: '持仓分布',
    type: 'pie',
    radius: ['40%', '70%'],
    data: positions.value.map(pos => ({
      value: pos.market_value,
      name: pos.symbol
    })),
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowColor: 'rgba(0, 0, 0, 0.5)'
      }
    }
  }]
}))

const industryDistributionOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {d}%'
  },
  series: [{
    name: '行业分布',
    type: 'pie',
    radius: '70%',
    data: [
      { value: 35, name: '金融' },
      { value: 25, name: '科技' },
      { value: 20, name: '消费' },
      { value: 15, name: '医药' },
      { value: 5, name: '其他' }
    ],
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowColor: 'rgba(0, 0, 0, 0.5)'
      }
    }
  }]
}))

// 方法
const priceMap = ref<Record<string, number>>({})

const loadPrices = async () => {
  const symbols = positions.value.map(p => p.symbol)
  for (const s of symbols) {
    try {
      const info = await dataApi.getStockInfo(s)
      priceMap.value[s] = info.data?.current_price || 0
    } catch {}
  }
}

const refreshPositions = async () => {
  loading.value = true
  try {
    await tradingStore.fetchPositions()
    await loadPrices()
    ElMessage.success('刷新成功')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const exportPositions = () => {
  // 导出持仓数据
  const csvContent = [
    ['股票代码', '持仓数量', '成本价', '市值', '浮动盈亏', '盈亏比例'].join(','),
    ...positions.value.map(pos => [
      pos.symbol,
      pos.quantity,
      pos.avg_cost.toFixed(2),
      pos.market_value.toFixed(2),
      pos.unrealized_pnl.toFixed(2),
      (pos.unrealized_pnl_ratio * 100).toFixed(2) + '%'
    ].join(','))
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `持仓明细_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  
  ElMessage.success('导出成功')
}

const handleAction = (command: { action: string; symbol: string }) => {
  const { action, symbol } = command
  
  switch (action) {
    case 'buy':
    case 'sell':
      router.push({
        path: '/admin/trading',
        query: { symbol, action }
      })
      break
    case 'detail':
      viewStockDetail({ symbol })
      break
  }
}

const viewStockDetail = (row: { symbol: string }) => {
  // 打开股票详情对话框
  selectedSymbol.value = row.symbol
  showDetailDialog.value = true
}

const viewAllTrades = () => {
  router.push('/admin/trading?tab=trades')
}

onMounted(async () => {
  await tradingStore.initialize()
  await loadPrices()
})
watch(positions, async () => {
  await loadPrices()
})
</script>

<style lang="scss" scoped>
.portfolio-container {
  padding: 24px;
}

.portfolio-overview {
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
  
  &.total-value {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  &.total-cost {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }
  
  &.total-pnl {
    &.profit {
      background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    
    &.loss {
      background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }
  }
  
  &.position-count {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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

.charts-section {
  margin-bottom: 24px;
}

.card {
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
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

.header-actions {
  display: flex;
  gap: 8px;
}

.stock-info {
  .stock-symbol {
    font-weight: 600;
    color: var(--el-color-primary);
  }
}

.pnl-info {
  .pnl-ratio {
    font-size: 12px;
    margin-top: 2px;
  }
}

.chart-container {
  width: 100%;
}

@media (max-width: 768px) {
  .portfolio-container {
    padding: 16px;
  }
  
  .overview-card {
    margin-bottom: 16px;
  }
  
  .card {
    padding: 16px;
  }
  
  .card-value {
    font-size: 20px;
  }
}
</style>
