<template>
  <div class="realtime-quote">
    <el-card class="quote-card" :class="quoteClass">
      <template #header>
        <div class="card-header">
          <span class="stock-code">{{ stockCode }}</span>
          <span class="stock-name">{{ quoteData?.name || '加载中...' }}</span>
          <el-tag v-if="quoteData" :type="tagType" size="small">
            {{ quoteData.source }}
          </el-tag>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      
      <div v-else-if="error" class="error-container">
        <el-icon><WarningFilled /></el-icon>
        <span>{{ error }}</span>
      </div>
      
      <div v-else-if="quoteData" class="quote-content">
        <!-- 当前价格 -->
        <div class="price-section">
          <div class="current-price" :class="priceClass">
            ¥{{ quoteData.current.toFixed(2) }}
          </div>
          <div class="price-change" :class="priceClass">
            <span>{{ changeText }}</span>
            <span class="change-pct">{{ changePctText }}</span>
          </div>
        </div>
        
        <!-- 详细信息 -->
        <div class="detail-section">
          <div class="detail-row">
            <span class="label">今开</span>
            <span class="value">¥{{ quoteData.open.toFixed(2) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">昨收</span>
            <span class="value">¥{{ quoteData.close.toFixed(2) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">最高</span>
            <span class="value price-up">¥{{ quoteData.high.toFixed(2) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">最低</span>
            <span class="value price-down">¥{{ quoteData.low.toFixed(2) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">成交量</span>
            <span class="value">{{ formatVolume(quoteData.volume) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">更新时间</span>
            <span class="value">{{ formatTime(quoteData.time) }}</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, WarningFilled } from '@element-plus/icons-vue'
import axios from 'axios'

interface QuoteData {
  code: string
  name: string
  current: number
  open: number
  close: number
  high: number
  low: number
  volume: number
  amount: number
  change: number
  change_pct: number
  time: string
  source: string
}

const props = defineProps<{
  stockCode: string
  autoRefresh?: boolean
  refreshInterval?: number // 刷新间隔（毫秒）
}>()

const quoteData = ref<QuoteData | null>(null)
const loading = ref(false)
const error = ref('')
let refreshTimer: number | null = null

// 计算属性
const priceClass = computed(() => {
  if (!quoteData.value) return ''
  return quoteData.value.change >= 0 ? 'price-up' : 'price-down'
})

const quoteClass = computed(() => {
  if (!quoteData.value) return ''
  return quoteData.value.change >= 0 ? 'quote-up' : 'quote-down'
})

const tagType = computed(() => {
  if (!quoteData.value) return 'info'
  const source = quoteData.value.source
  if (source === 'tencent') return 'success'
  if (source === 'eastmoney') return 'warning'
  return 'info'
})

const changeText = computed(() => {
  if (!quoteData.value) return ''
  const change = quoteData.value.change
  return change >= 0 ? `+${change.toFixed(2)}` : change.toFixed(2)
})

const changePctText = computed(() => {
  if (!quoteData.value) return ''
  const pct = quoteData.value.change_pct
  return pct >= 0 ? `+${pct.toFixed(2)}%` : `${pct.toFixed(2)}%`
})

// 获取实时行情
const fetchQuote = async () => {
  if (!props.stockCode) return
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.get(`/api/quote/realtime/${props.stockCode}`)
    if (response.data.success) {
      quoteData.value = response.data.data
    } else {
      error.value = response.data.message || '获取行情失败'
    }
  } catch (err: any) {
    error.value = err.response?.data?.message || '网络错误'
    console.error('获取实时行情失败:', err)
  } finally {
    loading.value = false
  }
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

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return ''
  // 格式：20251126104951 -> 10:49:51
  if (time.length >= 14) {
    const hour = time.substring(8, 10)
    const minute = time.substring(10, 12)
    const second = time.substring(12, 14)
    return `${hour}:${minute}:${second}`
  }
  return time
}

// 启动自动刷新
const startAutoRefresh = () => {
  if (props.autoRefresh && props.refreshInterval) {
    refreshTimer = window.setInterval(() => {
      fetchQuote()
    }, props.refreshInterval)
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 监听股票代码变化
watch(() => props.stockCode, () => {
  fetchQuote()
})

// 生命周期
onMounted(() => {
  fetchQuote()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

// 暴露方法供父组件调用
defineExpose({
  refresh: fetchQuote
})
</script>

<style scoped lang="scss">
.realtime-quote {
  .quote-card {
    border-radius: 8px;
    transition: all 0.3s;
    
    &.quote-up {
      border-left: 4px solid #f56c6c;
    }
    
    &.quote-down {
      border-left: 4px solid #67c23a;
    }
    
    .card-header {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .stock-code {
        font-size: 18px;
        font-weight: bold;
        color: #303133;
      }
      
      .stock-name {
        font-size: 14px;
        color: #606266;
      }
    }
  }
  
  .loading-container,
  .error-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 40px 0;
    color: #909399;
  }
  
  .error-container {
    color: #f56c6c;
  }
  
  .quote-content {
    .price-section {
      text-align: center;
      padding: 20px 0;
      border-bottom: 1px solid #ebeef5;
      
      .current-price {
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 8px;
        
        &.price-up {
          color: #f56c6c;
        }
        
        &.price-down {
          color: #67c23a;
        }
      }
      
      .price-change {
        font-size: 16px;
        
        &.price-up {
          color: #f56c6c;
        }
        
        &.price-down {
          color: #67c23a;
        }
        
        .change-pct {
          margin-left: 8px;
        }
      }
    }
    
    .detail-section {
      padding: 20px 0;
      
      .detail-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        
        .label {
          color: #909399;
          font-size: 14px;
        }
        
        .value {
          color: #303133;
          font-size: 14px;
          font-weight: 500;
          
          &.price-up {
            color: #f56c6c;
          }
          
          &.price-down {
            color: #67c23a;
          }
        }
      }
    }
  }
}
</style>
