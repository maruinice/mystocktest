<template>
  <el-dialog
    v-model="visible"
    :title="`${stockInfo?.name || ''} (${stockInfo?.code || ''})`"
    width="800px"
    @close="handleClose"
  >
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading"><Loading /></el-icon>
      <p>加载中...</p>
    </div>
    
    <div v-else-if="stockInfo" class="stock-detail-content">
      <!-- 基本信息 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="股票代码">{{ stockInfo.code }}</el-descriptions-item>
          <el-descriptions-item label="股票名称">{{ stockInfo.name }}</el-descriptions-item>
          <el-descriptions-item label="市场">{{ stockInfo.market }}</el-descriptions-item>
          <el-descriptions-item label="行业">{{ stockInfo.industry || '-' }}</el-descriptions-item>
          <el-descriptions-item label="上市日期">{{ stockInfo.list_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="交易所">{{ stockInfo.exchange || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 实时行情 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>实时行情</span>
            <el-tag :type="(stockInfo.change_percent || 0) >= 0 ? 'danger' : 'success'" size="small">
              {{ (stockInfo.change_percent || 0) >= 0 ? '+' : '' }}{{ ((stockInfo.change_percent || 0) * 100).toFixed(2) }}%
            </el-tag>
          </div>
        </template>
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="quote-item">
              <div class="quote-label">现价</div>
              <div class="quote-value" :class="(stockInfo.change_percent || 0) >= 0 ? 'price-up' : 'price-down'">
                ¥{{ (stockInfo.current_price || 0).toFixed(2) }}
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="quote-item">
              <div class="quote-label">涨跌额</div>
              <div class="quote-value" :class="(stockInfo.change || 0) >= 0 ? 'price-up' : 'price-down'">
                {{ (stockInfo.change || 0) >= 0 ? '+' : '' }}¥{{ (stockInfo.change || 0).toFixed(2) }}
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="quote-item">
              <div class="quote-label">成交量</div>
              <div class="quote-value">{{ formatVolume(stockInfo.volume || 0) }}</div>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="16" style="margin-top: 16px;">
          <el-col :span="6">
            <div class="quote-item">
              <div class="quote-label">开盘价</div>
              <div class="quote-value">¥{{ (stockInfo.open_price || 0).toFixed(2) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="quote-item">
              <div class="quote-label">最高价</div>
              <div class="quote-value price-up">¥{{ (stockInfo.high_price || 0).toFixed(2) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="quote-item">
              <div class="quote-label">最低价</div>
              <div class="quote-value price-down">¥{{ (stockInfo.low_price || 0).toFixed(2) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="quote-item">
              <div class="quote-label">昨收价</div>
              <div class="quote-value">¥{{ (stockInfo.pre_close || 0).toFixed(2) }}</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 持仓信息（如果有） -->
      <el-card v-if="positionInfo" class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>持仓信息</span>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="持仓数量">{{ positionInfo.quantity }}</el-descriptions-item>
          <el-descriptions-item label="可用数量">{{ positionInfo.available_quantity }}</el-descriptions-item>
          <el-descriptions-item label="成本价">¥{{ positionInfo.avg_cost.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="市值">¥{{ formatNumber(positionInfo.market_value) }}</el-descriptions-item>
          <el-descriptions-item label="浮动盈亏">
            <span :class="(positionInfo.profit_loss || 0) >= 0 ? 'stock-up' : 'stock-down'">
              {{ (positionInfo.profit_loss || 0) >= 0 ? '+' : '' }}¥{{ formatNumber(Math.abs(positionInfo.profit_loss || 0)) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="盈亏比例">
            <span :class="(positionInfo.profit_loss_pct || 0) >= 0 ? 'stock-up' : 'stock-down'">
              {{ (positionInfo.profit_loss_pct || 0) >= 0 ? '+' : '' }}{{ (positionInfo.profit_loss_pct || 0).toFixed(2) }}%
            </span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="goToTrading">前往交易</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { dataApi } from '@/api/data'
import { useTradingStore } from '@/stores/trading'
import { formatNumber } from '@/utils/format'
import type { StockInfo } from '@/types/data'

const props = defineProps<{
  modelValue: boolean
  symbol: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const router = useRouter()
const tradingStore = useTradingStore()

const visible = ref(props.modelValue)
const loading = ref(false)
const stockInfo = ref<StockInfo | null>(null)
const positionInfo = ref<any>(null)

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal && props.symbol) {
    loadStockDetail()
  }
})

// 监听 visible 变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

const loadStockDetail = async () => {
  if (!props.symbol) return
  
  loading.value = true
  try {
    // 加载股票信息
    const response = await dataApi.getStockInfo(props.symbol)
    stockInfo.value = response.data
    
    // 加载持仓信息
    const positions = tradingStore.positions || []
    positionInfo.value = positions.find((p: any) => 
      p.symbol === props.symbol || p.code === props.symbol
    )
  } catch (error) {
    console.error('加载股票详情失败:', error)
    ElMessage.error('加载股票详情失败')
  } finally {
    loading.value = false
  }
}

const formatVolume = (volume: number) => {
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万'
  }
  return volume.toString()
}

const handleClose = () => {
  visible.value = false
}

const goToTrading = () => {
  handleClose()
  router.push({
    path: '/admin/trading',
    query: { symbol: props.symbol }
  })
}
</script>

<style lang="scss" scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  
  .el-icon {
    font-size: 48px;
    margin-bottom: 16px;
    color: var(--el-color-primary);
  }
  
  p {
    color: var(--el-text-color-secondary);
  }
}

.stock-detail-content {
  .info-card {
    margin-bottom: 16px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
  }
  
  .quote-item {
    text-align: center;
    padding: 12px;
    background: var(--el-fill-color-light);
    border-radius: 8px;
    
    .quote-label {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-bottom: 8px;
    }
    
    .quote-value {
      font-size: 18px;
      font-weight: 600;
      font-family: 'Courier New', monospace;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.stock-up {
  color: #f56c6c;
}

.stock-down {
  color: #67c23a;
}
</style>
