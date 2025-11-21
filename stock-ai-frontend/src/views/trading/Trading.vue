<template>
  <div class="trading-container">
    <div class="page-header">
      <h1 class="page-title">交易中心</h1>
      <p class="page-description">实时交易，智能决策</p>
    </div>
    
    <el-row :gutter="16">
      <!-- 左侧：股票搜索和行情 -->
      <el-col :xs="24" :lg="16">
        <div class="card">
          <div class="card-header">
            <h3>股票搜索</h3>
          </div>
          <el-input
            v-model="searchKeyword"
            placeholder="输入股票代码或名称"
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <div v-if="searchResults.length > 0" class="search-results">
            <el-table :data="searchResults" @row-click="selectStock">
              <el-table-column prop="symbol" label="代码" width="100" />
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="current_price" label="现价" width="100">
                <template #default="{ row }">
                  <span class="stock-price">¥{{ row.current_price?.toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="change_percent" label="涨跌幅" width="100">
                <template #default="{ row }">
                  <span :class="getChangeClass(row.change_percent)">
                    {{ formatPercent(row.change_percent) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        
        <!-- 选中股票的详细信息 -->
        <div v-if="selectedStock" class="card mt-4">
          <div class="card-header">
            <h3>{{ selectedStock.symbol }} - {{ selectedStock.name }}</h3>
            <el-button @click="addToWatchlist" size="small">
              <el-icon><Star /></el-icon>
              加入自选
            </el-button>
          </div>
          
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="stock-info">
                <div class="price-info">
                  <span class="current-price">¥{{ selectedStock.current_price?.toFixed(2) }}</span>
                  <span :class="getChangeClass(selectedStock.change)">
                    {{ selectedStock.change >= 0 ? '+' : '' }}{{ selectedStock.change?.toFixed(2) }}
                    ({{ formatPercent(selectedStock.change_percent) }})
                  </span>
                </div>
                <div class="stock-details">
                  <el-descriptions :column="2" size="small">
                    <el-descriptions-item label="开盘">¥{{ selectedStock.open_price?.toFixed(2) }}</el-descriptions-item>
                    <el-descriptions-item label="最高">¥{{ selectedStock.high_price?.toFixed(2) }}</el-descriptions-item>
                    <el-descriptions-item label="最低">¥{{ selectedStock.low_price?.toFixed(2) }}</el-descriptions-item>
                    <el-descriptions-item label="成交量">{{ formatNumber(selectedStock.volume) }}</el-descriptions-item>
                  </el-descriptions>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <!-- K线图 -->
              <div v-loading="klineLoading" class="kline-chart-container">
                <v-chart 
                  v-if="klineData.length > 0"
                  :option="klineChartOption" 
                  :autoresize="true"
                  style="height: 200px;"
                />
                <div v-else class="chart-placeholder">
                  <el-icon><TrendCharts /></el-icon>
                  <p>暂无K线数据</p>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-col>
      
      <!-- 右侧：交易面板 -->
      <el-col :xs="24" :lg="8">
        <div class="card">
          <div class="card-header">
            <h3>交易面板</h3>
          </div>
          
          <el-form :model="orderForm" :rules="orderRules" ref="orderFormRef">
            <el-form-item label="股票代码" prop="symbol">
              <el-input v-model="orderForm.symbol" placeholder="请选择股票" readonly />
            </el-form-item>
            
            <el-form-item label="交易方向" prop="side">
              <el-radio-group v-model="orderForm.side">
                <el-radio-button label="buy">买入</el-radio-button>
                <el-radio-button label="sell">卖出</el-radio-button>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="订单类型" prop="order_type">
              <el-select v-model="orderForm.order_type" style="width: 100%">
                <el-option label="市价单" value="market" />
                <el-option label="限价单" value="limit" />
              </el-select>
            </el-form-item>
            
            <el-form-item v-if="orderForm.order_type === 'limit'" label="价格" prop="price">
              <el-input-number
                v-model="orderForm.price"
                :min="0.01"
                :precision="2"
                style="width: 100%"
                placeholder="请输入价格"
              />
            </el-form-item>
            
            <el-form-item label="数量" prop="quantity">
              <el-input-number
                v-model="orderForm.quantity"
                :min="100"
                :step="100"
                style="width: 100%"
                placeholder="请输入数量"
              />
            </el-form-item>
            
            <el-form-item>
              <div class="order-summary">
                <p>预估金额: ¥{{ estimatedAmount.toFixed(2) }}</p>
                <p>可用资金: ¥{{ formatNumber(availableCash) }}</p>
              </div>
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                @click="handlePlaceOrder"
                :loading="orderLoading"
                style="width: 100%"
                :disabled="!canPlaceOrder"
              >
                {{ orderForm.side === 'buy' ? '买入' : '卖出' }}
              </el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 账户信息 -->
        <div class="card mt-4">
          <div class="card-header">
            <h3>账户信息</h3>
          </div>
          <el-descriptions :column="1" size="small">
            <el-descriptions-item label="总资产">¥{{ formatNumber(totalAssets) }}</el-descriptions-item>
            <el-descriptions-item label="可用资金">¥{{ formatNumber(availableCash) }}</el-descriptions-item>
            <el-descriptions-item label="持仓市值">¥{{ formatNumber(marketValue) }}</el-descriptions-item>
            <el-descriptions-item label="总盈亏">
              <span :class="totalPnl >= 0 ? 'stock-up' : 'stock-down'">
                {{ totalPnl >= 0 ? '+' : '' }}¥{{ formatNumber(totalPnl) }}
              </span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>
    
    <!-- 订单列表 -->
    <div class="card mt-4">
      <div class="card-header">
        <h3>我的订单</h3>
        <el-button @click="refreshOrders" size="small">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      
      <el-table :data="orders" v-loading="ordersLoading">
        <el-table-column prop="symbol" label="股票代码" width="100" />
        <el-table-column prop="side" label="方向" width="80">
          <template #default="{ row }">
            <el-tag :type="row.side === 'buy' ? 'danger' : 'success'" size="small">
              {{ row.side === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="order_type" label="类型" width="80">
          <template #default="{ row }">
            {{ row.order_type === 'market' ? '市价' : '限价' }}
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="100" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">
            {{ row.price ? `¥${row.price.toFixed(2)}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="filled_quantity" label="成交数量" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getOrderStatusType(row.status)" size="small">
              {{ getOrderStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              @click="handleCancelOrder(row.order_id)"
              size="small"
              type="danger"
              text
            >
              撤单
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useTradingStore } from '@/stores/trading'
import { dataApi } from '@/api/data'
import { formatNumber, formatPercent, formatDateTime } from '@/utils/format'
import type { StockInfo, StockSearch } from '@/types/data'
import type { PlaceOrderRequest } from '@/types/trading'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CandlestickChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  LegendComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

// 注册ECharts组件
use([
  CanvasRenderer,
  CandlestickChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  LegendComponent
])

const tradingStore = useTradingStore()

// 响应式数据
const searchKeyword = ref('')
const searchResults = ref<StockSearch[]>([])
const selectedStock = ref<StockInfo | null>(null)
const orderLoading = ref(false)
const ordersLoading = ref(false)
const klineLoading = ref(false)
const orderFormRef = ref<FormInstance>()
const klineData = ref<any[]>([])

// 订单表单
const orderForm = reactive<PlaceOrderRequest>({
  symbol: '',
  side: 'buy',
  order_type: 'limit',
  quantity: 100,
  price: 0
})

// 表单验证规则
const orderRules: FormRules = {
  symbol: [{ required: true, message: '请选择股票', trigger: 'blur' }],
  side: [{ required: true, message: '请选择交易方向', trigger: 'change' }],
  order_type: [{ required: true, message: '请选择订单类型', trigger: 'change' }],
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' },
    { type: 'number', min: 100, message: '最小数量为100股', trigger: 'blur' }
  ],
  price: [
    { required: true, message: '请输入价格', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '价格必须大于0.01', trigger: 'blur' }
  ]
}

// 计算属性
const totalAssets = computed(() => tradingStore.totalAssets)
const availableCash = computed(() => tradingStore.availableCash)
const marketValue = computed(() => tradingStore.marketValue)
const totalPnl = computed(() => tradingStore.totalPnl)
const orders = computed(() => tradingStore.orders)

const estimatedAmount = computed(() => {
  if (orderForm.order_type === 'market' && selectedStock.value) {
    return (selectedStock.value.current_price || 0) * orderForm.quantity
  } else if (orderForm.order_type === 'limit') {
    return orderForm.price * orderForm.quantity
  }
  return 0
})

const canPlaceOrder = computed(() => {
  return orderForm.symbol && 
         orderForm.quantity >= 100 && 
         (orderForm.order_type === 'market' || orderForm.price > 0) &&
         (orderForm.side === 'sell' || estimatedAmount.value <= availableCash.value)
})

// K线图配置
const klineChartOption = computed(() => {
  if (klineData.value.length === 0) {
    return {}
  }

  // 准备数据
  const dates = klineData.value.map((item: any) => {
    const date = new Date(item.date)
    return `${date.getMonth() + 1}/${date.getDate()}`
  })
  
  const candlestickData = klineData.value.map((item: any) => [
    item.open_price,
    item.close_price,
    item.low_price,
    item.high_price
  ])

  // 计算MA5
  const ma5Data: number[] = []
  for (let i = 0; i < klineData.value.length; i++) {
    if (i < 4) {
      ma5Data.push(NaN)
    } else {
      let sum = 0
      for (let j = 0; j < 5; j++) {
        sum += klineData.value[i - j].close_price
      }
      ma5Data.push(sum / 5)
    }
  }

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        const dataIndex = params[0].dataIndex
        const item = klineData.value[dataIndex]
        return `
          日期: ${dates[dataIndex]}<br/>
          开盘: ${item.open_price.toFixed(2)}<br/>
          收盘: ${item.close_price.toFixed(2)}<br/>
          最高: ${item.high_price.toFixed(2)}<br/>
          最低: ${item.low_price.toFixed(2)}<br/>
          涨跌幅: ${(item.change_percent * 100).toFixed(2)}%
        `
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: dates,
      scale: true,
      boundaryGap: true,
      axisLine: { onZero: false },
      splitLine: { show: false },
      axisLabel: {
        fontSize: 10
      }
    },
    yAxis: {
      scale: true,
      splitArea: {
        show: true
      },
      axisLabel: {
        fontSize: 10
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 50,
        end: 100
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: candlestickData,
        itemStyle: {
          color: '#ef232a',
          color0: '#14b143',
          borderColor: '#ef232a',
          borderColor0: '#14b143'
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5Data,
        smooth: true,
        lineStyle: {
          opacity: 0.7,
          width: 1
        },
        showSymbol: false
      }
    ]
  }
})

// 方法
const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }
  
  try {
    const response = await dataApi.searchStocks({
      keyword: searchKeyword.value,
      limit: 10
    })
    searchResults.value = response.data
  } catch (error) {
    console.error('Search failed:', error)
  }
}

const selectStock = async (stock: StockSearch) => {
  try {
    const response = await dataApi.getStockInfo(stock.symbol)
    selectedStock.value = response.data
    orderForm.symbol = stock.symbol
    
    if (orderForm.order_type === 'limit' && selectedStock.value.current_price) {
      orderForm.price = selectedStock.value.current_price
    }
    
    // 加载K线数据
    await loadKlineData(stock.symbol)
  } catch (error) {
    ElMessage.error('获取股票信息失败')
  }
}

const loadKlineData = async (symbol: string) => {
  klineLoading.value = true
  try {
    const response = await dataApi.getStockQuotes(symbol, {
      limit: 30  // 获取最近30天的数据
    })
    klineData.value = response.data.quotes || []
  } catch (error) {
    console.error('加载K线数据失败:', error)
    klineData.value = []
  } finally {
    klineLoading.value = false
  }
}

const addToWatchlist = async () => {
  if (!selectedStock.value) return
  
  try {
    await dataApi.addToWatchlist(selectedStock.value.symbol)
    ElMessage.success('已添加到自选股')
  } catch (error) {
    ElMessage.error('添加自选股失败')
  }
}

const handlePlaceOrder = async () => {
  if (!orderFormRef.value) return
  
  try {
    await orderFormRef.value.validate()
    
    const confirmText = `确认${orderForm.side === 'buy' ? '买入' : '卖出'} ${orderForm.symbol} ${orderForm.quantity}股？`
    await ElMessageBox.confirm(confirmText, '确认下单', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    orderLoading.value = true
    
    const orderData = { ...orderForm }
    if (orderForm.order_type === 'market') {
      delete orderData.price
    }
    
    await tradingStore.placeOrder(orderData)
    ElMessage.success('下单成功')
    
    // 重置表单
    orderForm.quantity = 100
    if (selectedStock.value?.current_price) {
      orderForm.price = selectedStock.value.current_price
    }
    
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '下单失败')
    }
  } finally {
    orderLoading.value = false
  }
}

const handleCancelOrder = async (orderId: string) => {
  try {
    await ElMessageBox.confirm('确认撤销该订单？', '确认撤单', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await tradingStore.cancelOrder(orderId)
    ElMessage.success('撤单成功')
    
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '撤单失败')
    }
  }
}

const refreshOrders = async () => {
  ordersLoading.value = true
  try {
    await tradingStore.fetchOrders()
  } finally {
    ordersLoading.value = false
  }
}

const getChangeClass = (value: number) => {
  if (value > 0) return 'stock-up'
  if (value < 0) return 'stock-down'
  return 'stock-flat'
}

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

// 监听订单类型变化
watch(() => orderForm.order_type, (newType) => {
  if (newType === 'market') {
    orderForm.price = 0
  } else if (selectedStock.value?.current_price) {
    orderForm.price = selectedStock.value.current_price
  }
})

// 组件挂载
onMounted(() => {
  tradingStore.initialize()
})
</script>

<style lang="scss" scoped>
.trading-container {
  padding: 24px;
}

.search-results {
  margin-top: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.stock-info {
  .price-info {
    margin-bottom: 16px;
    
    .current-price {
      font-size: 24px;
      font-weight: 600;
      font-family: 'Courier New', monospace;
      margin-right: 12px;
    }
  }
}

.kline-chart-container {
  height: 200px;
  border-radius: 4px;
  overflow: hidden;
}

.chart-placeholder {
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  color: var(--el-text-color-placeholder);
  
  .el-icon {
    font-size: 48px;
    margin-bottom: 8px;
  }
}

.order-summary {
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  font-size: 14px;
  
  p {
    margin: 4px 0;
    display: flex;
    justify-content: space-between;
  }
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

@media (max-width: 768px) {
  .trading-container {
    padding: 16px;
  }
  
  .card {
    padding: 16px;
  }
  
  .stock-info .price-info .current-price {
    font-size: 20px;
  }
}
</style>