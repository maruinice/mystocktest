<template>
  <div class="model-list">
    <!-- 搜索和筛选 -->
    <div class="list-header">
      <div class="search-filters">
        <el-input
          v-model="searchQuery"
          placeholder="搜索模型名称或ID..."
          style="width: 300px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select
          v-model="filterType"
          placeholder="模型类型"
          style="width: 150px; margin-left: 12px"
          clearable
          @change="handleFilter"
        >
          <el-option
            v-for="type in modelTypes"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>
        
        <el-select
          v-model="filterStatus"
          placeholder="状态"
          style="width: 120px; margin-left: 12px"
          clearable
          @change="handleFilter"
        >
          <el-option
            v-for="status in statusOptions"
            :key="status.value"
            :label="status.label"
            :value="status.value"
          />
        </el-select>
        
        <el-button @click="resetFilters" style="margin-left: 12px">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
      </div>
      
      <div class="list-actions">
        <el-button type="primary" @click="$emit('create-model')">
          <el-icon><Plus /></el-icon>
          添加模型
        </el-button>
        <el-button @click="refreshList" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 模型表格 -->
    <el-table
      :data="models"
      v-loading="loading"
      stripe
      style="width: 100%"
      @sort-change="handleSortChange"
    >
      <el-table-column prop="model_id" label="模型ID" width="140" sortable="custom">
        <template #default="{ row }">
          <el-text class="model-id" truncated>{{ row.model_id }}</el-text>
        </template>
      </el-table-column>
      
      <el-table-column prop="name" label="模型名称" width="180" sortable="custom">
        <template #default="{ row }">
          <div class="model-name-cell">
            <div class="model-name">{{ row.name }}</div>
            <div class="model-display-name" v-if="row.display_name">
              {{ row.display_name }}
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="model_type" label="模型类型" width="120" sortable="custom">
        <template #default="{ row }">
          <el-tag>
            {{ getModelTypeText(row.model_type) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="provider" label="提供商" width="100" sortable="custom">
        <template #default="{ row }">
          <el-text size="small">{{ row.provider }}</el-text>
        </template>
      </el-table-column>
      
      <el-table-column prop="accuracy" label="准确率" width="120" sortable="custom">
        <template #default="{ row }">
          <div class="accuracy-cell" v-if="row.accuracy !== undefined">
            <el-progress
              :percentage="Math.round(row.accuracy * 100)"
              :color="getAccuracyColor(row.accuracy)"
              :stroke-width="6"
              :show-text="false"
            />
            <span class="accuracy-text">{{ (row.accuracy * 100).toFixed(1) }}%</span>
          </div>
          <el-text v-else type="info" size="small">未知</el-text>
        </template>
      </el-table-column>
      
      <el-table-column prop="response_time" label="响应时间" width="100" sortable="custom">
        <template #default="{ row }">
          <el-text v-if="row.response_time" size="small">
            {{ row.response_time.toFixed(2) }}s
          </el-text>
          <el-text v-else type="info" size="small">-</el-text>
        </template>
      </el-table-column>
      
      <el-table-column prop="status" label="状态" width="100" sortable="custom">
        <template #default="{ row }">
          <el-tag>
            <el-icon v-if="row.status === 'training'" class="is-loading">
              <Loading />
            </el-icon>
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="usage_count" label="使用次数" width="100" sortable="custom">
        <template #default="{ row }">
          <el-text size="small">{{ row.usage_count || 0 }}</el-text>
        </template>
      </el-table-column>
      
      <el-table-column prop="updated_at" label="最后更新" width="160" sortable="custom">
        <template #default="{ row }">
          <el-text size="small">{{ formatDateTime(row.updated_at) }}</el-text>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button size="small" @click="viewModel(row)">
              详情
            </el-button>
            <el-button
              size="small"
              type="primary"
              @click="editModel(row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              :type="row.enabled ? 'warning' : 'success'"
              @click="toggleModel(row)"
              :loading="row._toggling"
            >
              {{ row.enabled ? '停用' : '启用' }}
            </el-button>
            <el-popconfirm
              title="确定要删除这个模型吗？"
              @confirm="deleteModel(row)"
            >
              <template #reference>
                <el-button
                  size="small"
                  type="danger"
                  :loading="row._deleting"
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Search, RefreshLeft, Plus, Refresh, Loading } from '@element-plus/icons-vue'
import { formatDateTime } from '../../utils/format'
import { 
  modelManagementAPI, 
  type AIModel, 
  ModelType, 
  ModelStatus 
} from '../../api/model-management'

// Props
interface Props {
  refreshTrigger?: number
}

const props = withDefaults(defineProps<Props>(), {
  refreshTrigger: 0
})

// Emits
const emit = defineEmits<{
  'create-model': []
  'edit-model': [model: AIModel]
  'view-model': [model: AIModel]
}>()

// 响应式数据
const loading = ref(false)
const models = ref<AIModel[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 搜索和筛选
const searchQuery = ref('')
const filterType = ref<ModelType | ''>('')
const filterStatus = ref<ModelStatus | ''>('')
const sortField = ref('')
const sortOrder = ref('')

// 模型类型选项
const modelTypes = computed(() => [
  { label: 'DeepSeek', value: ModelType.DEEPSEEK },
  { label: 'OpenAI', value: ModelType.OPENAI },
  { label: 'Claude', value: ModelType.CLAUDE },
  { label: '自定义', value: ModelType.CUSTOM }
])

// 状态选项
const statusOptions = computed(() => [
  { label: '活跃', value: ModelStatus.ACTIVE },
  { label: '停用', value: ModelStatus.INACTIVE },
  { label: '训练中', value: ModelStatus.TRAINING },
  { label: '错误', value: ModelStatus.ERROR }
])

// 方法
const getModelTypeText = (type: ModelType) => {
  const typeMap = {
    [ModelType.DEEPSEEK]: 'DeepSeek',
    [ModelType.OPENAI]: 'OpenAI',
    [ModelType.CLAUDE]: 'Claude',
    [ModelType.CUSTOM]: '自定义'
  }
  return typeMap[type] || type
}

const getModelTypeColor = (type: ModelType) => {
  const colorMap = {
    [ModelType.DEEPSEEK]: 'primary',
    [ModelType.OPENAI]: 'success',
    [ModelType.CLAUDE]: 'warning',
    [ModelType.CUSTOM]: 'info'
  }
  return colorMap[type] || 'info'
}

const getStatusText = (status: ModelStatus) => {
  const statusMap = {
    [ModelStatus.ACTIVE]: '活跃',
    [ModelStatus.INACTIVE]: '停用',
    [ModelStatus.TRAINING]: '训练中',
    [ModelStatus.ERROR]: '错误'
  }
  return statusMap[status] || status
}

const getStatusColor = (status: ModelStatus) => {
  const colorMap = {
    [ModelStatus.ACTIVE]: 'success',
    [ModelStatus.INACTIVE]: 'info',
    [ModelStatus.TRAINING]: 'warning',
    [ModelStatus.ERROR]: 'danger'
  }
  return colorMap[status] || 'info'
}

const getAccuracyColor = (accuracy: number) => {
  if (accuracy >= 0.9) return '#67C23A'
  if (accuracy >= 0.8) return '#E6A23C'
  if (accuracy >= 0.7) return '#F56C6C'
  return '#909399'
}

// 加载模型列表
const loadModels = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      search: searchQuery.value || undefined,
      model_type: filterType.value || undefined,
      status: filterStatus.value || undefined
    }

    const response = await modelManagementAPI.getModels(params)
    
    if (response.success && response.data) {
      models.value = response.data.items
      total.value = response.data.total
    } else {
      ElMessage.error(response.message || '加载模型列表失败')
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
    ElMessage.error('加载模型列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  loadModels()
}

// 筛选处理
const handleFilter = () => {
  currentPage.value = 1
  loadModels()
}

// 重置筛选
const resetFilters = () => {
  searchQuery.value = ''
  filterType.value = ''
  filterStatus.value = ''
  currentPage.value = 1
  loadModels()
}

// 排序处理
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  sortField.value = prop
  sortOrder.value = order
  loadModels()
}

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadModels()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadModels()
}

// 刷新列表
const refreshList = () => {
  loadModels()
}

// 查看模型详情
const viewModel = (model: AIModel) => {
  emit('view-model', model)
}

// 编辑模型
const editModel = (model: AIModel) => {
  emit('edit-model', model)
}

// 切换模型状态
const toggleModel = async (model: AIModel) => {
  const action = model.enabled ? '停用' : '启用'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}模型 "${model.name}" 吗？`,
      `确认${action}`,
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    model._toggling = true
    
    const response = await modelManagementAPI.toggleModelStatus(
      model.model_id,
      !model.enabled
    )
    
    if (response.success && response.data) {
      model.enabled = response.data.enabled
      model.status = response.data.status
      ElMessage.success(`模型${action}成功`)
    } else {
      ElMessage.error(response.message || `模型${action}失败`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error(`模型${action}失败:`, error)
      ElMessage.error(`模型${action}失败`)
    }
  } finally {
    model._toggling = false
  }
}

// 删除模型
const deleteModel = async (model: AIModel) => {
  try {
    model._deleting = true
    
    const response = await modelManagementAPI.deleteModel(model.model_id)
    
    if (response.success) {
      ElMessage.success('模型删除成功')
      await loadModels()
    } else {
      ElMessage.error(response.message || '模型删除失败')
    }
  } catch (error) {
    console.error('模型删除失败:', error)
    ElMessage.error('模型删除失败')
  } finally {
    model._deleting = false
  }
}

// 监听刷新触发器
watch(() => props.refreshTrigger, () => {
  if (props.refreshTrigger > 0) {
    loadModels()
  }
})

// 组件挂载时加载数据
onMounted(() => {
  loadModels()
})
</script>

<style lang="scss" scoped>
.model-list {
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .search-filters {
      display: flex;
      align-items: center;
    }
    
    .list-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .model-id {
    font-family: 'Courier New', monospace;
    font-size: 12px;
  }
  
  .model-name-cell {
    .model-name {
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
    
    .model-display-name {
      font-size: 12px;
      color: var(--el-text-color-regular);
      margin-top: 2px;
    }
  }
  
  .accuracy-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-progress {
      flex: 1;
    }
    
    .accuracy-text {
      font-size: 12px;
      font-weight: 500;
      min-width: 40px;
    }
  }
  
  .action-buttons {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }
  
  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }
}

// 加载动画
.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>