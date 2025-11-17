<template>
  <div class="result-table">
    <el-table
      :data="results"
      v-loading="loading"
      element-loading-text="选股中..."
      height="100%"
      stripe
      @row-click="handleRowClick"
      class="screening-table"
    >
      <el-table-column type="index" label="排名" width="60" align="center" />
      
      <el-table-column prop="symbol" label="股票代码" width="100" align="center">
        <template #default="{ row }">
          <el-button type="text" @click.stop="viewStockDetail(row)">
            {{ row.symbol }}
          </el-button>
        </template>
      </el-table-column>
      
      <el-table-column prop="name" label="股票名称" width="120" show-overflow-tooltip />
      
      <el-table-column prop="industry" label="行业" width="100" show-overflow-tooltip />
      
      <el-table-column prop="market" label="市场" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="getMarketTagType(row.market)" size="small">
            {{ getMarketText(row.market) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="close_price" label="收盘价" width="90" align="right">
        <template #default="{ row }">
          <span v-if="row.close_price">{{ formatPrice(row.close_price) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="change_pct" label="涨跌幅" width="90" align="right">
        <template #default="{ row }">
          <span
            v-if="row.change_pct !== null && row.change_pct !== undefined"
            :class="getPriceChangeClass(row.change_pct)"
          >
            {{ formatPercent(row.change_pct) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="turnover_rate" label="换手率" width="90" align="right">
        <template #default="{ row }">
          <span v-if="row.turnover_rate">{{ formatPercent(row.turnover_rate) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="pe" label="市盈率" width="80" align="right">
        <template #default="{ row }">
          <span v-if="row.pe">{{ formatNumber(row.pe, 2) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="pb" label="市净率" width="80" align="right">
        <template #default="{ row }">
          <span v-if="row.pb">{{ formatNumber(row.pb, 2) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="market_cap" label="市值" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.market_cap">{{ formatMarketCap(row.market_cap) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="roe" label="ROE" width="80" align="right">
        <template #default="{ row }">
          <span v-if="row.roe">{{ formatPercent(row.roe) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="revenue_growth" label="营收增长" width="100" align="right">
        <template #default="{ row }">
          <span
            v-if="row.revenue_growth !== null && row.revenue_growth !== undefined"
            :class="getGrowthClass(row.revenue_growth)"
          >
            {{ formatPercent(row.revenue_growth) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="profit_growth" label="利润增长" width="100" align="right">
        <template #default="{ row }">
          <span
            v-if="row.profit_growth !== null && row.profit_growth !== undefined"
            :class="getGrowthClass(row.profit_growth)"
          >
            {{ formatPercent(row.profit_growth) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="debt_ratio" label="资产负债率" width="110" align="right">
        <template #default="{ row }">
          <span v-if="row.debt_ratio">{{ formatPercent(row.debt_ratio) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="current_ratio" label="流动比率" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.current_ratio">{{ formatNumber(row.current_ratio, 2) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="quick_ratio" label="速动比率" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.quick_ratio">{{ formatNumber(row.quick_ratio, 2) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="gross_margin" label="毛利率" width="80" align="right">
        <template #default="{ row }">
          <span v-if="row.gross_margin">{{ formatPercent(row.gross_margin) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="net_margin" label="净利率" width="80" align="right">
        <template #default="{ row }">
          <span v-if="row.net_margin">{{ formatPercent(row.net_margin) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="roa" label="ROA" width="80" align="right">
        <template #default="{ row }">
          <span v-if="row.roa">{{ formatPercent(row.roa) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="composite_score" label="综合评分" width="100" align="center" fixed="right">
        <template #default="{ row }">
          <div class="score-cell">
            <el-progress
              :percentage="Math.min(row.composite_score, 100)"
              :color="getScoreColor(row.composite_score)"
              :stroke-width="8"
              text-inside
              :format="() => formatScore(row.composite_score)"
            />
          </div>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="120" align="center" fixed="right">
        <template #default="{ row }">
          <el-button-group>
            <el-button type="primary" size="small" @click.stop="viewStockDetail(row)">
              详情
            </el-button>
            <el-button type="success" size="small" @click.stop="addToPortfolio(row)">
              加入
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 空状态 -->
    <div v-if="!loading && results.length === 0" class="empty-result">
      <el-empty description="暂无选股结果">
        <template #image>
          <el-icon size="60" color="#c0c4cc">
            <TrendCharts />
          </el-icon>
        </template>
        <p class="empty-tip">请选择策略并设置筛选条件后执行选股</p>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { TrendCharts } from '@element-plus/icons-vue'
import type { ScreeningResult } from '@/types/screening'

// Props
interface Props {
  results: ScreeningResult[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  'row-click': [result: ScreeningResult]
  'view-detail': [result: ScreeningResult]
  'add-to-portfolio': [result: ScreeningResult]
}>()

// 方法
const handleRowClick = (row: ScreeningResult) => {
  emit('row-click', row)
}

const viewStockDetail = (row: ScreeningResult) => {
  emit('view-detail', row)
}

const addToPortfolio = (row: ScreeningResult) => {
  emit('add-to-portfolio', row)
  ElMessage.success(`已将 ${row.name} 加入投资组合`)
}

const getMarketTagType = (market: string) => {
  const typeMap: Record<string, string> = {
    '主板': 'primary',
    '创业板': 'success',
    '科创板': 'warning',
    '北交所': 'info'
  }
  return typeMap[market] || 'info'
}

const getMarketText = (market: string) => {
  const textMap: Record<string, string> = {
    'main': '主板',
    'gem': '创业板',
    'star': '科创板',
    'bse': '北交所'
  }
  return textMap[market] || market
}

const getPriceChangeClass = (change: number) => {
  if (change > 0) return 'price-up'
  if (change < 0) return 'price-down'
  return 'price-flat'
}

const getGrowthClass = (growth: number) => {
  if (growth > 0) return 'growth-positive'
  if (growth < 0) return 'growth-negative'
  return 'growth-flat'
}

const getScoreColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#409eff'
  if (score >= 40) return '#e6a23c'
  return '#f56c6c'
}

const formatPrice = (price: number) => {
  return `¥${price.toFixed(2)}`
}

const formatPercent = (value: number) => {
  return `${value.toFixed(2)}%`
}

const formatNumber = (value: number, decimals = 2) => {
  return value.toFixed(decimals)
}

const formatMarketCap = (value: number) => {
  if (value >= 10000) {
    return `${(value / 10000).toFixed(1)}万亿`
  } else if (value >= 100) {
    return `${(value / 100).toFixed(1)}百亿`
  } else {
    return `${value.toFixed(1)}亿`
  }
}

const formatScore = (score: number) => {
  return score.toFixed(0)
}
</script>

<style scoped lang="scss">
.result-table {
  height: 300px;
  
  .screening-table {
    :deep(.el-table__header) {
      background-color: #fafafa;
      
      th {
        background-color: #fafafa !important;
        color: #303133;
        font-weight: 600;
      }
    }
    
    :deep(.el-table__row) {
      cursor: pointer;
      
      &:hover {
        background-color: #f5f7fa;
      }
    }
  }
  
  .no-data {
    color: #c0c4cc;
  }
  
  .price-up {
    color: #f56c6c;
    font-weight: 600;
  }
  
  .price-down {
    color: #67c23a;
    font-weight: 600;
  }
  
  .price-flat {
    color: #909399;
  }
  
  .growth-positive {
    color: #f56c6c;
    font-weight: 600;
  }
  
  .growth-negative {
    color: #67c23a;
    font-weight: 600;
  }
  
  .growth-flat {
    color: #909399;
  }
  
  .score-cell {
    padding: 4px 0;
    
    :deep(.el-progress__text) {
      font-size: 12px !important;
      font-weight: 600;
    }
  }
}

.empty-result {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .empty-tip {
    margin-top: 16px;
    color: #909399;
    font-size: 14px;
  }
}
</style>