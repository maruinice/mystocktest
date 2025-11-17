<template>
  <div class="history-table">
    <el-table :data="history" v-loading="loading" stripe>
      <el-table-column prop="strategy_name" label="策略名称" width="150" />
      <el-table-column prop="screening_date" label="选股日期" width="120" />
      <el-table-column prop="filtered_stocks" label="筛选结果" width="100" align="center">
        <template #default="{ row }">
          <el-tag type="primary">{{ row.filtered_stocks }}只</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="execution_time" label="执行时间" width="100" align="center">
        <template #default="{ row }">{{ row.execution_time }}ms</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="viewResult(row.task_id)">
            查看结果
          </el-button>
          <el-button type="success" size="small" @click="rerunScreening(row.task_id)" style="margin-left: 8px;">
            重新执行
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div v-if="pagination.total > 0" class="pagination">
      <el-pagination
        :current-page="pagination.page"
        :page-size="pagination.limit"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ScreeningHistory, Pagination } from '@/types/screening'

interface Props {
  history: ScreeningHistory[]
  pagination: Pagination
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  'page-change': [page: number]
  'view-result': [taskId: string]
  'rerun-screening': [taskId: string]
}>()

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    completed: 'success',
    running: 'warning',
    failed: 'danger',
    pending: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    completed: '已完成',
    running: '运行中',
    failed: '失败',
    pending: '等待中'
  }
  return textMap[status] || status
}

const handlePageChange = (page: number) => {
  emit('page-change', page)
}

const viewResult = (taskId: string) => {
  emit('view-result', taskId)
}

const rerunScreening = (taskId: string) => {
  emit('rerun-screening', taskId)
}
</script>

<style scoped lang="scss">
.history-table {
  .pagination {
    margin-top: 16px;
    text-align: center;
  }
}
</style>