<template>
  <div class="data-source-management">
    <div class="page-header">
      <h2>数据源管理</h2>
      <p class="page-description">管理行情数据源和交易数据源配置</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新增数据源
      </el-button>
      <el-button @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 筛选器 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item label="数据源类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable>
            <el-option label="行情数据源" value="market_data" />
            <el-option label="交易数据源" value="trading_data" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
            <el-option label="测试中" value="testing" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadDataSources">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据表格 -->
    <el-table 
      :data="dataSources" 
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="name" label="数据源名称" width="150" />
      <el-table-column prop="type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="row.type === 'market_data' ? 'primary' : 'warning'">
            {{ row.type === 'market_data' ? '行情数据源' : '交易数据源' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="provider" label="提供商" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag 
            :type="getStatusType(row.status)"
            size="small"
          >
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="base_url" label="基础URL" width="200" show-overflow-tooltip />
      <el-table-column label="API密钥" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.has_api_key" type="success" size="small">已配置</el-tag>
          <el-tag v-else type="danger" size="small">未配置</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="调用统计" width="150">
        <template #default="{ row }">
          <div class="stats">
            <div>总调用: {{ row.total_calls }}</div>
            <div>成功率: {{ row.success_rate }}%</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="last_call_time" label="最后调用" width="150">
        <template #default="{ row }">
          {{ formatDateTime(row.last_call_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="testConnection(row)">测试</el-button>
          <el-button size="small" @click="editDataSource(row)">编辑</el-button>
          <el-button 
            size="small" 
            type="danger" 
            @click="deleteDataSource(row)"
            :disabled="row.provider === 'tushare'"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadDataSources"
        @current-change="loadDataSources"
      />
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑数据源' : '新增数据源'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="数据源名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入数据源名称" />
        </el-form-item>
        <el-form-item label="数据源类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择数据源类型">
            <el-option label="行情数据源" value="market_data" />
            <el-option label="交易数据源" value="trading_data" />
          </el-select>
        </el-form-item>
        <el-form-item label="提供商" prop="provider">
          <el-input v-model="form.provider" placeholder="请输入提供商名称" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" placeholder="请选择状态">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
            <el-option label="测试中" value="testing" />
          </el-select>
        </el-form-item>
        <el-form-item label="基础URL">
          <el-input v-model="form.base_url" placeholder="请输入基础URL" />
        </el-form-item>
        <el-form-item label="API密钥">
          <el-input 
            v-model="form.api_key" 
            type="password" 
            placeholder="请输入API密钥"
            show-password
          />
        </el-form-item>
        <el-form-item label="API密钥">
          <el-input 
            v-model="form.api_secret" 
            type="password" 
            placeholder="请输入API密钥（可选）"
            show-password
          />
        </el-form-item>
        <el-form-item label="超时时间(秒)">
          <el-input-number v-model="form.timeout" :min="1" :max="300" />
        </el-form-item>
        <el-form-item label="速率限制">
          <el-input-number v-model="form.rate_limit" :min="1" :max="1000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 测试结果对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="连接测试结果"
      width="500px"
    >
      <div class="test-result">
        <div class="result-header">
          <el-icon v-if="testResult.success" color="green" size="24">
            <SuccessFilled />
          </el-icon>
          <el-icon v-else color="red" size="24">
            <CircleCloseFilled />
          </el-icon>
          <span class="result-text">
            {{ testResult.success ? '连接成功' : '连接失败' }}
          </span>
        </div>
        <div class="result-message">
          {{ testResult.message }}
        </div>
        <div v-if="testResult.data" class="result-data">
          <h4>测试数据:</h4>
          <pre>{{ JSON.stringify(testResult.data, null, 2) }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { dataManagementApi } from '@/api/data-management'

// 响应式数据
const loading = ref(false)
const dataSources = ref([])
const dialogVisible = ref(false)
const testDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 筛选器
const filters = reactive({
  type: '',
  status: ''
})

// 表单数据
const form = reactive({
  name: '',
  type: '',
  provider: '',
  status: 'inactive',
  base_url: '',
  api_key: '',
  api_secret: '',
  timeout: 30,
  rate_limit: 200
})

// 测试结果
const testResult = reactive({
  success: false,
  message: '',
  data: null
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入数据源名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择数据源类型', trigger: 'change' }
  ],
  provider: [
    { required: true, message: '请输入提供商名称', trigger: 'blur' }
  ]
}

// 方法
const loadDataSources = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filters
    }
    const response = await dataManagementApi.getDataSources(params)
    if (response.success) {
      dataSources.value = response.data.items
      pagination.total = response.data.total
    } else {
      ElMessage.error(response.error || '获取数据源列表失败')
    }
  } catch (error) {
    ElMessage.error('获取数据源列表失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadDataSources()
}

const resetFilters = () => {
  filters.type = ''
  filters.status = ''
  pagination.page = 1
  loadDataSources()
}

const showCreateDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
}

const editDataSource = (row: any) => {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    name: row.name,
    type: row.type,
    provider: row.provider,
    status: row.status,
    base_url: row.base_url || '',
    api_key: '',
    api_secret: '',
    timeout: row.timeout || 30,
    rate_limit: row.rate_limit || 200
  })
  dialogVisible.value = true
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    type: '',
    provider: '',
    status: 'inactive',
    base_url: '',
    api_key: '',
    api_secret: '',
    timeout: 30,
    rate_limit: 200
  })
  formRef.value?.resetFields()
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    let response
    if (isEdit.value) {
      response = await dataManagementApi.updateDataSource(form.id, form)
    } else {
      response = await dataManagementApi.createDataSource(form)
    }
    
    if (response.success) {
      ElMessage.success(isEdit.value ? '数据源更新成功' : '数据源创建成功')
      dialogVisible.value = false
      loadDataSources()
    } else {
      ElMessage.error(response.error || '操作失败')
    }
  } catch (error) {
    // 表单验证失败
  } finally {
    submitting.value = false
  }
}

const deleteDataSource = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据源 "${row.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await dataManagementApi.deleteDataSource(row.id)
    if (response.success) {
      ElMessage.success('数据源删除成功')
      loadDataSources()
    } else {
      ElMessage.error(response.error || '删除失败')
    }
  } catch (error) {
    // 用户取消删除
  }
}

const testConnection = async (row: any) => {
  try {
    ElMessage.info('正在测试连接...')
    const response = await dataManagementApi.testDataSource(row.id)
    
    testResult.success = response.success
    testResult.message = response.message
    testResult.data = response.data
    testDialogVisible.value = true
    
    // 刷新数据以更新统计信息
    loadDataSources()
  } catch (error) {
    ElMessage.error('测试连接失败')
  }
}

const getStatusType = (status: string) => {
  const statusMap = {
    active: 'success',
    inactive: 'danger',
    testing: 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap = {
    active: '启用',
    inactive: '禁用',
    testing: '测试中'
  }
  return statusMap[status] || status
}

const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadDataSources()
})
</script>

<style scoped>
.data-source-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.action-bar {
  margin-bottom: 16px;
}

.filter-bar {
  margin-bottom: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.stats {
  font-size: 12px;
  line-height: 1.4;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.test-result {
  padding: 20px 0;
}

.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.result-text {
  margin-left: 8px;
  font-size: 16px;
  font-weight: 500;
}

.result-message {
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
}

.result-data {
  margin-top: 16px;
}

.result-data h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.result-data pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}
</style>