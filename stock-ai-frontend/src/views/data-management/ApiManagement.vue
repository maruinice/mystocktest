<template>
  <div class="api-management">
    <div class="page-header">
      <h2>API管理</h2>
      <p class="page-description">管理和测试数据源API接口</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="syncApis" :loading="syncing">
        <el-icon><Download /></el-icon>
        同步API
      </el-button>
      <el-button @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-button @click="showSyncTasks">
        <el-icon><List /></el-icon>
        同步任务
      </el-button>
    </div>

    <!-- 筛选器 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item label="数据源">
          <el-select v-model="filters.data_source_id" placeholder="全部数据源" clearable>
            <el-option 
              v-for="source in dataSources" 
              :key="source.id" 
              :label="source.name" 
              :value="source.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="API分类">
          <el-select v-model="filters.category" placeholder="全部分类" clearable>
            <el-option 
              v-for="category in categories" 
              :key="category.category" 
              :label="`${category.category} (${category.api_count})`" 
              :value="category.category" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
            <el-option label="已废弃" value="deprecated" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadApiInterfaces">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据表格 -->
    <el-table 
      :data="apiInterfaces" 
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="api_code" label="API代码" width="120" />
      <el-table-column prop="api_name" label="API名称" width="150" />
      <el-table-column prop="api_category" label="分类" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.api_category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="data_source_name" label="数据源" width="120" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="required_points" label="所需积分" width="100" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag 
            :type="getStatusType(row.status)"
            size="small"
          >
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="调用统计" width="120">
        <template #default="{ row }">
          <div class="stats">
            <div>总调用: {{ row.total_calls }}</div>
            <div>成功率: {{ row.success_rate }}%</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="avg_response_time" label="平均响应时间" width="120">
        <template #default="{ row }">
          {{ row.avg_response_time ? `${row.avg_response_time}s` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="last_call_time" label="最后调用" width="150">
        <template #default="{ row }">
          {{ formatDateTime(row.last_call_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showApiDetail(row)">详情</el-button>
          <el-button size="small" type="primary" @click="testApi(row)">测试</el-button>
          <el-button size="small" type="success" @click="viewApiData(row)">查看数据</el-button>
          <el-button size="small" @click="showCallLogs(row)">日志</el-button>
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
        @size-change="loadApiInterfaces"
        @current-change="loadApiInterfaces"
      />
    </div>

    <!-- API详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="API接口详情"
      width="800px"
    >
      <div v-if="selectedApi" class="api-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="API代码">{{ selectedApi.api_code }}</el-descriptions-item>
          <el-descriptions-item label="API名称">{{ selectedApi.api_name }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ selectedApi.api_category }}</el-descriptions-item>
          <el-descriptions-item label="数据源">{{ selectedApi.data_source_name }}</el-descriptions-item>
          <el-descriptions-item label="请求方法">{{ selectedApi.method }}</el-descriptions-item>
          <el-descriptions-item label="端点">{{ selectedApi.endpoint }}</el-descriptions-item>
          <el-descriptions-item label="所需积分">{{ selectedApi.required_points }}</el-descriptions-item>
          <el-descriptions-item label="速率限制">{{ selectedApi.rate_limit }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="api-description">
          <h4>描述</h4>
          <p>{{ selectedApi.description }}</p>
        </div>

        <div class="api-params">
          <h4>必需参数</h4>
          <el-table :data="selectedApi.required_params" size="small">
            <el-table-column prop="name" label="参数名" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>

        <div class="api-params">
          <h4>可选参数</h4>
          <el-table :data="selectedApi.optional_params" size="small">
            <el-table-column prop="name" label="参数名" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>

        <div class="api-params">
          <h4>响应字段</h4>
          <el-table :data="selectedApi.response_fields" size="small">
            <el-table-column prop="name" label="字段名" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- API测试对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="API测试"
      width="700px"
    >
      <div v-if="selectedApi" class="api-test">
        <div class="test-form">
          <h4>测试参数</h4>
          <el-form :model="testParams" label-width="120px">
            <el-form-item 
              v-for="param in [...selectedApi.required_params, ...selectedApi.optional_params]"
              :key="param.name"
              :label="param.name"
            >
              <el-input 
                v-model="testParams[param.name]" 
                :placeholder="param.description"
              />
              <div class="param-info">
                <span class="param-type">{{ param.type }}</span>
                <span class="param-desc">{{ param.description }}</span>
              </div>
            </el-form-item>
          </el-form>
        </div>
        
        <div class="test-result" v-if="testResult.tested">
          <h4>测试结果</h4>
          <div class="result-header">
            <el-icon v-if="testResult.success" color="green" size="20">
              <SuccessFilled />
            </el-icon>
            <el-icon v-else color="red" size="20">
              <CircleCloseFilled />
            </el-icon>
            <span class="result-text">
              {{ testResult.success ? '调用成功' : '调用失败' }}
            </span>
            <span class="response-time">
              响应时间: {{ testResult.response_time }}s
            </span>
          </div>
          <div v-if="testResult.error_message" class="error-message">
            <strong>错误信息:</strong> {{ testResult.error_message }}
          </div>
          <div v-if="testResult.response_data" class="response-data">
            <strong>响应数据:</strong>
            <pre>{{ JSON.stringify(testResult.response_data, null, 2) }}</pre>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="executeApiTest" :loading="testing">
          执行测试
        </el-button>
      </template>
    </el-dialog>

    <!-- 调用日志对话框 -->
    <el-dialog
      v-model="logsDialogVisible"
      title="API调用日志"
      width="900px"
    >
      <el-table :data="callLogs" v-loading="logsLoading" size="small">
        <el-table-column prop="call_type" label="调用类型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getCallTypeColor(row.call_type)">
              {{ getCallTypeText(row.call_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="success" label="结果" width="60">
          <template #default="{ row }">
            <el-icon v-if="row.success" color="green">
              <SuccessFilled />
            </el-icon>
            <el-icon v-else color="red">
              <CircleCloseFilled />
            </el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="response_time" label="响应时间" width="100">
          <template #default="{ row }">
            {{ row.response_time ? `${row.response_time}s` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="called_at" label="调用时间" width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.called_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="showLogDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination
          v-model:current-page="logsPagination.page"
          v-model:page-size="logsPagination.size"
          :page-sizes="[10, 20, 50]"
          :total="logsPagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="loadCallLogs"
          @current-change="loadCallLogs"
        />
      </div>
      <template #footer>
        <el-button @click="logsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 同步任务对话框 -->
    <el-dialog
      v-model="syncTasksDialogVisible"
      title="API同步任务"
      width="800px"
    >
      <el-table :data="syncTasks" v-loading="syncTasksLoading" size="small">
        <el-table-column prop="task_name" label="任务名称" min-width="200" />
        <el-table-column prop="task_type" label="任务类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getSyncStatusType(row.status)" size="small">
              {{ getSyncStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="100">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :show-text="false" />
            <span>{{ row.progress }}%</span>
          </template>
        </el-table-column>
        <el-table-column label="API统计" width="150">
          <template #default="{ row }">
            <div class="sync-stats">
              <div>总数: {{ row.total_apis }}</div>
              <div>新增: {{ row.new_apis }} 更新: {{ row.updated_apis }}</div>
              <div v-if="row.failed_apis > 0" class="failed">失败: {{ row.failed_apis }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="syncTasksDialogVisible = false">关闭</el-button>
        <el-button @click="loadSyncTasks">刷新</el-button>
      </template>
    </el-dialog>

    <!-- 查看数据对话框 -->
    <el-dialog
      v-model="viewDataDialogVisible"
      title="API数据查看"
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedApi" class="api-data-viewer">
        <div class="data-header">
          <h4>{{ selectedApi.api_name }} ({{ selectedApi.api_code }})</h4>
          <p class="api-description">{{ selectedApi.description }}</p>
        </div>
        
        <!-- 参数设置 -->
        <div class="data-params">
          <h5>查询参数</h5>
          <el-form :model="viewDataParams" inline size="small">
            <el-form-item 
              v-for="param in getViewDataParams(selectedApi)"
              :key="param.name"
              :label="param.name"
            >
              <el-input 
                v-model="viewDataParams[param.name]" 
                :placeholder="param.description"
                style="width: 150px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="executeViewData" :loading="viewDataLoading">
                查询数据
              </el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 数据展示 -->
        <div class="data-result" v-if="viewDataResult.executed">
          <div class="result-header">
            <h5>查询结果</h5>
            <div class="result-info">
              <el-tag v-if="viewDataResult.success" type="success" size="small">
                查询成功
              </el-tag>
              <el-tag v-else type="danger" size="small">
                查询失败
              </el-tag>
              <span class="response-time">
                响应时间: {{ viewDataResult.response_time }}s
              </span>
              <span v-if="viewDataResult.data_count" class="data-count">
                数据条数: {{ viewDataResult.data_count }}
              </span>
            </div>
          </div>
          
          <div v-if="viewDataResult.error_message" class="error-message">
            <strong>错误信息:</strong> {{ viewDataResult.error_message }}
          </div>
          
          <div v-if="viewDataResult.response_data" class="response-data">
            <!-- 表格展示 -->
            <div v-if="Array.isArray(viewDataResult.response_data) && viewDataResult.response_data.length > 0" class="data-table">
              <el-table 
                :data="viewDataResult.response_data.slice(0, 100)" 
                size="small" 
                max-height="400"
                stripe
              >
                <el-table-column 
                  v-for="(value, key) in viewDataResult.response_data[0]" 
                  :key="key"
                  :prop="key" 
                  :label="key"
                  :width="getColumnWidth(key)"
                  show-overflow-tooltip
                />
              </el-table>
              <div v-if="viewDataResult.response_data.length > 100" class="data-limit-notice">
                <el-alert 
                  title="数据显示限制" 
                  :description="`共 ${viewDataResult.response_data.length} 条数据，仅显示前 100 条`"
                  type="info" 
                  :closable="false"
                />
              </div>
            </div>
            
            <!-- JSON展示 -->
            <div v-else class="json-data">
              <pre>{{ JSON.stringify(viewDataResult.response_data, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="viewDataDialogVisible = false">关闭</el-button>
        <el-button v-if="viewDataResult.response_data" @click="exportData">导出数据</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Download, 
  Refresh, 
  List, 
  SuccessFilled, 
  CircleCloseFilled 
} from '@element-plus/icons-vue'
import { dataManagementApi } from '@/api/data-management'

// 响应式数据
const loading = ref(false)
const syncing = ref(false)
const testing = ref(false)
const logsLoading = ref(false)
const syncTasksLoading = ref(false)
const viewDataLoading = ref(false)

const apiInterfaces = ref([])
const dataSources = ref([])
const categories = ref([])
const callLogs = ref([])
const syncTasks = ref([])

const detailDialogVisible = ref(false)
const testDialogVisible = ref(false)
const logsDialogVisible = ref(false)
const syncTasksDialogVisible = ref(false)
const viewDataDialogVisible = ref(false)

const selectedApi = ref(null)

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const logsPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 筛选器
const filters = reactive({
  data_source_id: '',
  category: '',
  status: ''
})

// 测试参数
const testParams = reactive({})

// 测试结果
const testResult = reactive({
  tested: false,
  success: false,
  response_time: 0,
  error_message: '',
  response_data: null
})

// 查看数据参数
const viewDataParams = reactive({})

// 查看数据结果
const viewDataResult = reactive({
  executed: false,
  success: false,
  response_time: 0,
  error_message: '',
  response_data: null,
  data_count: 0
})

// 方法
const loadApiInterfaces = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filters
    }
    const response = await dataManagementApi.getApiInterfaces(params)
    if (response.success) {
      apiInterfaces.value = response.data.items
      pagination.total = response.data.total
    } else {
      ElMessage.error(response.error || '获取API接口列表失败')
    }
  } catch (error) {
    ElMessage.error('获取API接口列表失败')
  } finally {
    loading.value = false
  }
}

const loadDataSources = async () => {
  try {
    const response = await dataManagementApi.getDataSources({ size: 100 })
    if (response.success) {
      dataSources.value = response.data.items
    }
  } catch (error) {
    console.error('获取数据源列表失败', error)
  }
}

const loadCategories = async () => {
  try {
    const response = await dataManagementApi.getApiCategories(filters.data_source_id ? { data_source_id: filters.data_source_id } : {})
    if (response.success) {
      categories.value = response.data
    }
  } catch (error) {
    console.error('获取API分类失败', error)
  }
}

const refreshData = () => {
  loadApiInterfaces()
  loadCategories()
}

const resetFilters = () => {
  filters.data_source_id = ''
  filters.category = ''
  filters.status = ''
  pagination.page = 1
  loadApiInterfaces()
  loadCategories()
}

const syncApis = async () => {
  if (!filters.data_source_id) {
    ElMessage.warning('请先选择要同步的数据源')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要同步选中数据源的API接口吗？',
      '确认同步',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    syncing.value = true
    const response = await dataManagementApi.syncApis(filters.data_source_id)
    
    if (response.success) {
      ElMessage.success(`API同步成功！新增 ${response.data.new_apis} 个，更新 ${response.data.updated_apis} 个`)
      loadApiInterfaces()
    } else {
      ElMessage.error(response.error || 'API同步失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('API同步失败')
    }
  } finally {
    syncing.value = false
  }
}

const showApiDetail = (row: any) => {
  selectedApi.value = row
  detailDialogVisible.value = true
}

const testApi = (row: any) => {
  selectedApi.value = row
  // 重置测试参数
  Object.keys(testParams).forEach(key => {
    delete testParams[key]
  })
  // 重置测试结果
  testResult.tested = false
  testResult.success = false
  testResult.response_time = 0
  testResult.error_message = ''
  testResult.response_data = null
  
  testDialogVisible.value = true
}

const executeApiTest = async () => {
  testing.value = true
  try {
    const response = await dataManagementApi.testApiInterface(selectedApi.value.id, {
      params: testParams
    })
    
    testResult.tested = true
    testResult.success = response.success
    testResult.response_time = response.data?.response_time || 0
    testResult.error_message = response.data?.error_message || ''
    testResult.response_data = response.data?.response_data || null
    
    if (response.success) {
      ElMessage.success('API测试完成')
    } else {
      ElMessage.warning('API测试失败，请查看错误信息')
    }
    
    // 刷新数据以更新统计信息
    loadApiInterfaces()
  } catch (error) {
    ElMessage.error('API测试失败')
  } finally {
    testing.value = false
  }
}

const showCallLogs = async (row: any) => {
  selectedApi.value = row
  logsPagination.page = 1
  logsDialogVisible.value = true
  await loadCallLogs()
}

const loadCallLogs = async () => {
  if (!selectedApi.value) return
  
  logsLoading.value = true
  try {
    const params = {
      page: logsPagination.page,
      size: logsPagination.size
    }
    const response = await dataManagementApi.getApiCallLogs(selectedApi.value.id, params)
    if (response.success) {
      callLogs.value = response.data.items
      logsPagination.total = response.data.total
    } else {
      ElMessage.error(response.error || '获取调用日志失败')
    }
  } catch (error) {
    ElMessage.error('获取调用日志失败')
  } finally {
    logsLoading.value = false
  }
}

const showSyncTasks = async () => {
  syncTasksDialogVisible.value = true
  await loadSyncTasks()
}

const loadSyncTasks = async () => {
  syncTasksLoading.value = true
  try {
    const response = await dataManagementApi.getSyncTasks()
    if (response.success) {
      syncTasks.value = response.data.items
    } else {
      ElMessage.error(response.error || '获取同步任务失败')
    }
  } catch (error) {
    ElMessage.error('获取同步任务失败')
  } finally {
    syncTasksLoading.value = false
  }
}

const showLogDetail = (row: any) => {
  // 显示日志详情的逻辑
  ElMessageBox.alert(
    `<pre>${JSON.stringify(row, null, 2)}</pre>`,
    '调用日志详情',
    {
      dangerouslyUseHTMLString: true
    }
  )
}

// 辅助方法
const getStatusType = (status: string) => {
  const statusMap = {
    active: 'success',
    inactive: 'danger',
    deprecated: 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap = {
    active: '启用',
    inactive: '禁用',
    deprecated: '已废弃'
  }
  return statusMap[status] || status
}

const getCallTypeColor = (type: string) => {
  const typeMap = {
    test: 'primary',
    sync: 'success',
    manual: 'warning'
  }
  return typeMap[type] || 'info'
}

const getCallTypeText = (type: string) => {
  const typeMap = {
    test: '测试',
    sync: '同步',
    manual: '手动'
  }
  return typeMap[type] || type
}

const getSyncStatusType = (status: string) => {
  const statusMap = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return statusMap[status] || 'info'
}

const getSyncStatusText = (status: string) => {
  const statusMap = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 查看数据功能
const viewApiData = (row: any) => {
  selectedApi.value = row
  // 重置查看数据参数
  Object.keys(viewDataParams).forEach(key => {
    delete viewDataParams[key]
  })
  // 重置查看数据结果
  viewDataResult.executed = false
  viewDataResult.success = false
  viewDataResult.response_time = 0
  viewDataResult.error_message = ''
  viewDataResult.response_data = null
  viewDataResult.data_count = 0
  
  viewDataDialogVisible.value = true
}

const getViewDataParams = (api: any) => {
  if (!api) return []
  // 合并必需参数和可选参数，但只显示常用的查询参数
  const allParams = [...(api.required_params || []), ...(api.optional_params || [])]
  // 过滤出常用的查询参数
  const commonParams = ['ts_code', 'symbol', 'trade_date', 'start_date', 'end_date', 'limit', 'offset']
  return allParams.filter(param => commonParams.includes(param.name))
}

const executeViewData = async () => {
  viewDataLoading.value = true
  try {
    const response = await dataManagementApi.testApiInterface(selectedApi.value.id, {
      params: viewDataParams
    })
    
    viewDataResult.executed = true
    viewDataResult.success = response.success
    viewDataResult.response_time = response.data?.response_time || 0
    viewDataResult.error_message = response.data?.error_message || ''
    viewDataResult.response_data = response.data?.response_data || null
    
    // 计算数据条数
    if (Array.isArray(viewDataResult.response_data)) {
      viewDataResult.data_count = viewDataResult.response_data.length
    } else if (viewDataResult.response_data) {
      viewDataResult.data_count = 1
    } else {
      viewDataResult.data_count = 0
    }
    
    if (response.success) {
      ElMessage.success('数据查询完成')
    } else {
      ElMessage.warning('数据查询失败，请查看错误信息')
    }
    
    // 刷新数据以更新统计信息
    loadApiInterfaces()
  } catch (error) {
    ElMessage.error('数据查询失败')
  } finally {
    viewDataLoading.value = false
  }
}

const getColumnWidth = (key: string) => {
  // 根据字段名设置合适的列宽
  const widthMap: Record<string, number> = {
    'ts_code': 120,
    'symbol': 100,
    'name': 150,
    'trade_date': 120,
    'list_date': 120,
    'area': 80,
    'industry': 120,
    'market': 80,
    'exchange': 80
  }
  return widthMap[key] || 120
}

const exportData = () => {
  if (!viewDataResult.response_data) return
  
  try {
    let csvContent = ''
    
    if (Array.isArray(viewDataResult.response_data) && viewDataResult.response_data.length > 0) {
      // 表格数据导出为CSV
      const headers = Object.keys(viewDataResult.response_data[0])
      csvContent = headers.join(',') + '\n'
      
      viewDataResult.response_data.forEach(row => {
        const values = headers.map(header => {
          const value = row[header]
          // 处理包含逗号的值
          return typeof value === 'string' && value.includes(',') ? `"${value}"` : value
        })
        csvContent += values.join(',') + '\n'
      })
    } else {
      // JSON数据导出
      csvContent = JSON.stringify(viewDataResult.response_data, null, 2)
    }
    
    // 创建下载链接
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `${selectedApi.value.api_code}_data_${new Date().getTime()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('数据导出成功')
  } catch (error) {
    ElMessage.error('数据导出失败')
  }
}

// 生命周期
onMounted(() => {
  loadDataSources()
  loadCategories()
  loadApiInterfaces()
})
</script>

<style scoped>
.api-management {
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

.api-detail {
  padding: 20px 0;
}

.api-description {
  margin: 20px 0;
}

.api-params {
  margin: 20px 0;
}

.api-params h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.api-test {
  padding: 20px 0;
}

.test-form {
  margin-bottom: 20px;
}

.param-info {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.param-type {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 2px;
  margin-right: 8px;
}

.test-result {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
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

.response-time {
  margin-left: auto;
  font-size: 14px;
  color: #909399;
}

.error-message {
  margin-bottom: 16px;
  padding: 12px;
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 4px;
  color: #f56c6c;
}

.response-data {
  margin-top: 16px;
}

.response-data pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.sync-stats {
  font-size: 12px;
  line-height: 1.4;
}

.sync-stats .failed {
  color: #f56c6c;
}

/* 查看数据对话框样式 */
.api-data-viewer {
  padding: 20px 0;
}

.data-header h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 18px;
}

.api-description {
  margin: 0 0 20px 0;
  color: #606266;
  font-size: 14px;
}

.data-params {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.data-params h5 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.data-result {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.result-header h5 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.result-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.response-time,
.data-count {
  color: #909399;
}

.error-message {
  margin-bottom: 16px;
  padding: 12px;
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 4px;
  color: #f56c6c;
  font-size: 14px;
}

.data-table {
  margin-bottom: 16px;
}

.data-limit-notice {
  margin-top: 12px;
}

.json-data {
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.json-data pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #303133;
}
</style>