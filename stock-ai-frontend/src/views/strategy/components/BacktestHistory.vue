<template>
  <div class="backtest-history">
    <div class="history-header">
      <h3>回测历史</h3>
      <div class="header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索策略名称..."
          style="width: 200px; margin-right: 12px;"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button @click="refreshHistory" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="history-content">
      <el-table
        :data="filteredHistory"
        v-loading="loading"
        @row-click="viewBacktestDetail"
        style="cursor: pointer;"
      >
        <el-table-column prop="strategy_name" label="策略名称" width="200">
          <template #default="{ row }">
            <div class="strategy-info">
              <div class="strategy-name">{{ row.strategy_name }}</div>
              <div class="strategy-id">{{ row.strategy_id }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="start_date" label="回测期间" width="180">
          <template #default="{ row }">
            {{ row.start_date }} ~ {{ row.end_date }}
          </template>
        </el-table-column>
        
        <el-table-column prop="initial_capital" label="初始资金" width="120" align="right">
          <template #default="{ row }">
            ¥{{ formatNumber(row.initial_capital) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="total_return" label="总收益率" width="120" align="right">
          <template #default="{ row }">
            <span :class="row.total_return >= 0 ? 'positive' : 'negative'">
              {{ row.total_return >= 0 ? '+' : '' }}{{ (Number(row.total_return) * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="sharpe_ratio" label="夏普比率" width="100" align="right">
          <template #default="{ row }">
            {{ row.sharpe_ratio ? Number(row.sharpe_ratio).toFixed(2) : '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="max_drawdown" label="最大回撤" width="100" align="right">
          <template #default="{ row }">
            <span class="negative">
              -{{ (Number(row.max_drawdown) * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="win_rate" label="胜率" width="80" align="right">
          <template #default="{ row }">
            {{ (Number(row.win_rate) * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        
        <el-table-column prop="total_trades" label="交易次数" width="100" align="right" />
        
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click.stop="viewBacktestDetail(row)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 回测详情弹窗 -->
    <el-dialog
      v-model="showDetailDialog"
      title="回测详情"
      width="90%"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <BacktestResult
        v-if="selectedBacktest"
        :result="selectedBacktest"
        @close="showDetailDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import BacktestResult from './BacktestResult.vue'
import { strategyApi } from '@/api/strategy'

// Props
interface Props {
  strategyId?: string
}

const props = defineProps<Props>()

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const historyList = ref<any[]>([])
const showDetailDialog = ref(false)
const selectedBacktest = ref<any>(null)

// 计算属性
const filteredHistory = computed(() => {
  if (!searchKeyword.value) {
    return historyList.value
  }
  return historyList.value.filter(item =>
    item.strategy_name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// 方法
const formatNumber = (num: number | string) => {
  const numValue = typeof num === 'string' ? parseFloat(num) : num
  return new Intl.NumberFormat('zh-CN').format(numValue)
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'running': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'running': return '运行中'
    case 'failed': return '失败'
    default: return '未知'
  }
}

const loadHistory = async () => {
  loading.value = true
  try {
    const response = await strategyApi.getBacktestHistory({
      strategy_id: props.strategyId,
      page: currentPage.value,
      size: pageSize.value
    })
    
    console.log('回测历史响应:', response)
    
    // 兼容两种返回格式
    if (response.success && response.data) {
      // 格式1: { success: true, data: { results: [], total: 17, ... } }
      historyList.value = response.data.results || []
      total.value = response.data.total || 0
    } else if (response.data?.success && response.data?.data) {
      // 格式2: { data: { success: true, data: { results: [], total: 17 } } }
      historyList.value = response.data.data.results || []
      total.value = response.data.data.total || 0
    } else {
      ElMessage.error(response.message || response.data?.message || '获取回测历史失败')
    }
  } catch (error: any) {
    console.error('获取回测历史失败:', error)
    ElMessage.error('获取回测历史失败')
  } finally {
    loading.value = false
  }
}

const refreshHistory = () => {
  currentPage.value = 1
  loadHistory()
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  loadHistory()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  loadHistory()
}

const viewBacktestDetail = async (row: any) => {
  try {
    loading.value = true
    const response = await strategyApi.getBacktestDetail(row.backtest_id)
    
    console.log('回测详情响应:', response)
    
    // 兼容两种返回格式
    if (response.success && response.data) {
      selectedBacktest.value = response.data
      showDetailDialog.value = true
    } else if (response.data?.success && response.data?.data) {
      selectedBacktest.value = response.data.data
      showDetailDialog.value = true
    } else {
      ElMessage.error(response.message || response.data?.message || '获取回测详情失败')
    }
  } catch (error: any) {
    console.error('获取回测详情失败:', error)
    ElMessage.error('获取回测详情失败')
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadHistory()
})

// 暴露方法给父组件
defineExpose({
  refreshHistory
})
</script>

<style lang="scss" scoped>
.backtest-history {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
  }
}

.history-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  
  .el-table {
    flex: 1;
  }
}

.strategy-info {
  .strategy-name {
    font-weight: 500;
    color: #303133;
  }
  
  .strategy-id {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
  }
}

.positive {
  color: #67c23a;
  font-weight: 500;
}

.negative {
  color: #f56c6c;
  font-weight: 500;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  padding: 16px 0;
}

:deep(.el-table__row) {
  cursor: pointer;
  
  &:hover {
    background-color: #f5f7fa;
  }
}
</style>
