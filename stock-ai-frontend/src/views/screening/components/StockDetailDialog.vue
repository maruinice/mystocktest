<template>
  <el-dialog
    v-model="visible"
    :title="stock ? `${stock.name} (${stock.symbol})` : '股票详情'"
    width="600px"
  >
    <div v-if="stock" class="stock-detail">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="股票代码">{{ stock.symbol }}</el-descriptions-item>
        <el-descriptions-item label="股票名称">{{ stock.name }}</el-descriptions-item>
        <el-descriptions-item label="所属行业">{{ stock.industry }}</el-descriptions-item>
        <el-descriptions-item label="交易市场">{{ stock.market }}</el-descriptions-item>
        <el-descriptions-item label="收盘价">
          {{ stock.close_price ? `¥${stock.close_price.toFixed(2)}` : '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="涨跌幅">
          <span :class="getPriceChangeClass(stock.change_pct)">
            {{ stock.change_pct ? `${stock.change_pct.toFixed(2)}%` : '--' }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="市盈率">
          {{ stock.pe ? stock.pe.toFixed(2) : '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="市净率">
          {{ stock.pb ? stock.pb.toFixed(2) : '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="ROE">
          {{ stock.roe ? `${stock.roe.toFixed(2)}%` : '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="综合评分">
          <el-tag :type="getScoreTagType(stock.composite_score)">
            {{ stock.composite_score.toFixed(1) }}分
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </div>
    
    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button type="primary" @click="addToPortfolio">加入投资组合</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { ScreeningResult } from '@/types/screening'

interface Props {
  modelValue: boolean
  stock?: ScreeningResult
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const getPriceChangeClass = (change?: number) => {
  if (!change) return ''
  if (change > 0) return 'price-up'
  if (change < 0) return 'price-down'
  return 'price-flat'
}

const getScoreTagType = (score: number) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'primary'
  if (score >= 40) return 'warning'
  return 'danger'
}

const addToPortfolio = () => {
  if (props.stock) {
    ElMessage.success(`已将 ${props.stock.name} 加入投资组合`)
    visible.value = false
  }
}
</script>

<style scoped lang="scss">
.stock-detail {
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
}
</style>