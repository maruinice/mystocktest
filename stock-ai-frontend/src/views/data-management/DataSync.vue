<template>
  <div class="data-sync">
    <div class="page-header">
      <h2>数据同步管理</h2>
      <p class="page-description">管理增强数据源的同步任务</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="syncAllData" :loading="syncingAll">
        <el-icon><Download /></el-icon>
        同步所有数据
      </el-button>
      <el-button @click="refreshStatus">
        <el-icon><Refresh /></el-icon>
        刷新状态
      </el-button>
      <el-button @click="showScheduleDialog">
        <el-icon><Timer /></el-icon>
        定时任务
      </el-button>
    </div>

    <!-- 数据源卡片 -->
    <el-row :gutter="20">
      <el-col 
        v-for="source in dataSources" 
        :key="source.id" 
        :xs="24" 
        :sm="12" 
        :md="12" 
        :lg="6"
      >
        <el-card class="data-source-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="source-name">{{ source.name }}</span>
              <el-tag 
                :type="getPriorityType(source.priority)" 
                size="small"
              >
                {{ source.priority }}
              </el-tag>
            </div>
          </template>
          
          <div class="card-content">
            <div class="source-info">
              <p class="description">{{ source.description }}</p>
              
              <!-- 同步进度条 -->
              <div v-if="source.syncing" class="sync-progress">
                <el-progress 
                  :percentage="source.progress" 
                  :status="source.progress === 100 ? 'success' : undefined"
                />
                <div class="progress-info">
                  <span class="progress-text">{{ source.message }}</span>
                  <span class="progress-count">{{ source.current }} / {{ source.total }}</span>
                </div>
              </div>
              
              <div class="stats">
                <div class="stat-item">
                  <span class="label">数据条数:</span>
                  <span class="value">{{ source.count || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">最后更新:</span>
                  <span class="value">{{ formatDate(source.last_date) }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">同步频率:</span>
                  <span class="value">{{ getScheduleText(source.schedule) }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">实现状态:</span>
                  <el-tag :type="source.implemented ? 'success' : 'info'" size="small">
                    {{ source.implemented ? '已实现' : '未实现' }}
                  </el-tag>
                </div>
              </div>
            </div>
            
            <div class="card-actions">
              <el-button 
                type="primary" 
                size="small" 
                @click="syncSingleSource(source)"
                :loading="source.syncing"
                :disabled="!source.implemented"
              >
                {{ source.syncing ? '同步中...' : '立即同步' }}
              </el-button>
              <el-button 
                size="small" 
                @click="showSyncHistory(source)"
              >
                同步历史
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 同步历史对话框 -->
    <el-dialog
      v-model="historyDialogVisible"
      title="同步历史"
      width="900px"
    >
      <div v-if="selectedSource" class="sync-history">
        <div class="history-header">
          <h4>{{ selectedSource.name }}</h4>
          <p>{{ selectedSource.description }}</p>
        </div>
        
        <el-table 
          :data="syncHistory" 
          v-loading="historyLoading"
          size="small"
        >
          <el-table-column prop="sync_time" label="同步时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.sync_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag 
                :type="getSyncStatusType(row.status)" 
                size="small"
              >
                {{ getSyncStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="count" label="同步数量" width="100" />
          <el-table-column prop="duration" label="耗时" width="100">
            <template #default="{ row }">
              {{ row.duration }}s
            </template>
          </el-table-column>
          <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" @click="showHistoryDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination">
          <el-pagination
            v-model:current-page="historyPagination.page"
            v-model:page-size="historyPagination.size"
            :page-sizes="[10, 20, 50]"
            :total="historyPagination.total"
            layout="total, sizes, prev, pager, next"
            @size-change="loadSyncHistory"
            @current-change="loadSyncHistory"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="historyDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 定时任务对话框 -->
    <el-dialog
      v-model="scheduleDialogVisible"
      title="定时同步任务"
      width="700px"
    >
      <div class="schedule-config">
        <el-alert
          title="定时任务说明"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        >
          <p>系统支持为每个数据源配置定时同步任务，建议配置如下：</p>
          <ul>
            <li>行业分类：每周一次</li>
            <li>涨跌停价格：每日收盘后</li>
            <li>停复牌信息：每日收盘后</li>
            <li>审计意见：每月一次</li>
          </ul>
        </el-alert>
        
        <el-table :data="dataSources" size="small">
          <el-table-column prop="name" label="数据源" width="150" />
          <el-table-column prop="schedule" label="同步频率" width="100">
            <template #default="{ row }">
              {{ getScheduleText(row.schedule) }}
            </template>
          </el-table-column>
          <el-table-column label="下次同步时间" width="160">
            <template #default="{ row }">
              {{ getNextSyncTime(row.schedule) }}
            </template>
          </el-table-column>
          <el-table-column label="启用状态" width="100">
            <template #default="{ row }">
              <el-switch 
                v-model="row.enabled" 
                @change="toggleSchedule(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" @click="editSchedule(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="saveScheduleConfig">保存配置</el-button>
      </template>
    </el-dialog>

    <!-- 同步参数对话框 -->
    <el-dialog
      v-model="paramsDialogVisible"
      :title="`同步 ${selectedSource?.name}`"
      width="600px"
    >
      <div v-if="selectedSource" class="sync-params">
        <el-form :model="syncParams" label-width="120px">
          <el-form-item 
            v-for="param in getSyncParams(selectedSource)"
            :key="param.name"
            :label="param.label"
          >
            <el-input 
              v-if="param.type === 'text'"
              v-model="syncParams[param.name]" 
              :placeholder="param.placeholder"
            />
            <el-date-picker
              v-else-if="param.type === 'date'"
              v-model="syncParams[param.name]"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYYMMDD"
            />
            <el-date-picker
              v-else-if="param.type === 'daterange'"
              v-model="syncParams[param.name]"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYYMMDD"
            />
          </el-form-item>
        </el-form>
        
        <el-alert
          title="提示"
          type="info"
          :closable="false"
        >
          如果不填写日期参数，系统将自动从最新数据日期开始同步到当前日期
        </el-alert>
      </div>
      <template #footer>
        <el-button @click="paramsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="executeSyncWithParams" :loading="syncing">
          开始同步
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Refresh, Timer } from '@element-plus/icons-vue'
import { dataManagementApi } from '@/api/data-management'

// 响应式数据
const syncingAll = ref(false)
const syncing = ref(false)
const historyLoading = ref(false)

const dataSources = ref([])

const syncHistory = ref([])
const selectedSource = ref(null)

const historyDialogVisible = ref(false)
const scheduleDialogVisible = ref(false)
const paramsDialogVisible = ref(false)

const syncParams = reactive({})

const historyPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 加载同步服务列表
const loadSyncServices = async () => {
  try {
    const response = await fetch('/api/data-sync/services')
    const result = await response.json()
    
    if (result.success) {
      dataSources.value = result.data.map(service => ({
        id: service.key,
        key: service.key,
        name: service.name,
        description: service.description,
        table: service.table,
        frequency: service.frequency,
        api: service.api,
        implemented: service.implemented,
        schedule: service.frequency === '每日' ? 'daily' : service.frequency === '每周' ? 'weekly' : 'monthly',
        priority: service.frequency === '每日' ? 'high' : 'medium',
        count: 0,
        last_date: null,
        syncing: false,
        enabled: true,
        progress: 0,
        current: 0,
        total: 0,
        message: ''
      }))
      
      // 加载统计信息
      await refreshStatistics()
    }
  } catch (error) {
    console.error('加载同步服务失败:', error)
    ElMessage.error('加载同步服务失败')
  }
}

// 刷新统计信息
const refreshStatistics = async () => {
  for (const source of dataSources.value) {
    if (!source.implemented) continue
    
    try {
      const response = await fetch(`/api/data-sync/services/${source.key}/statistics`)
      const result = await response.json()
      
      if (result.success) {
        source.count = result.data.total_count || 0
        source.last_date = result.data.last_sync_date || null
      }
    } catch (error) {
      console.error(`获取${source.name}统计失败:`, error)
    }
  }
}

// 方法
const refreshStatus = async () => {
  try {
    await refreshStatistics()
    
    // 刷新所有服务的同步状态
    const serviceKeys = dataSources.value.filter(s => s.implemented).map(s => s.key)
    const response = await fetch('/api/data-sync/services/batch-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ service_keys: serviceKeys })
    })
    const result = await response.json()
    
    if (result.success) {
      dataSources.value.forEach(source => {
        const status = result.data[source.key]
        if (status) {
          source.syncing = status.is_running
          source.progress = status.progress || 0
          source.current = status.current || 0
          source.total = status.total || 0
          source.message = status.message || ''
        }
      })
    }
    
    ElMessage.success('状态刷新成功')
  } catch (error) {
    console.error('获取同步状态失败:', error)
    ElMessage.error('获取同步状态失败')
  }
}

const syncAllData = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要同步所有数据源吗？这可能需要几分钟时间。',
      '确认同步',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    syncingAll.value = true
    const response = await dataManagementApi.syncAllData()
    
    if (response.success) {
      ElMessage.success(response.message || '批量同步成功')
      refreshStatus()
    } else {
      ElMessage.error(response.message || '批量同步失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量同步失败:', error)
      ElMessage.error('批量同步失败')
    }
  } finally {
    syncingAll.value = false
  }
}

const syncSingleSource = (source: any) => {
  selectedSource.value = source
  
  // 如果需要参数，显示参数对话框
  const needsParams = ['limit_prices', 'suspend', 'audit'].includes(source.id)
  
  if (needsParams) {
    // 重置参数
    Object.keys(syncParams).forEach(key => {
      delete syncParams[key]
    })
    paramsDialogVisible.value = true
  } else {
    // 直接同步
    executeSyncWithParams()
  }
}

const executeSyncWithParams = async () => {
  if (!selectedSource.value) return
  
  if (!selectedSource.value.implemented) {
    ElMessage.warning('该同步服务尚未实现')
    return
  }
  
  try {
    selectedSource.value.syncing = true
    syncing.value = true
    
    const params = { ...syncParams }
    
    // 启动同步任务
    const response = await fetch(`/api/data-sync/services/${selectedSource.value.key}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
    const result = await response.json()
    
    if (result.success) {
      ElMessage.success(`${selectedSource.value.name}同步任务已启动`)
      paramsDialogVisible.value = false
      
      // 开始轮询状态
      startStatusPolling(selectedSource.value.key)
    } else {
      ElMessage.error(result.message || '启动同步失败')
      selectedSource.value.syncing = false
    }
  } catch (error) {
    console.error('启动同步失败:', error)
    ElMessage.error('启动同步失败')
    selectedSource.value.syncing = false
  } finally {
    syncing.value = false
  }
}

// 状态轮询
const pollingTimers = new Map()

const startStatusPolling = (serviceKey: string) => {
  // 清除已有的轮询
  if (pollingTimers.has(serviceKey)) {
    clearInterval(pollingTimers.get(serviceKey))
  }
  
  // 开始新的轮询
  const timer = setInterval(async () => {
    try {
      const response = await fetch(`/api/data-sync/services/${serviceKey}/status`)
      const result = await response.json()
      
      if (result.success) {
        const source = dataSources.value.find(s => s.key === serviceKey)
        if (source) {
          source.syncing = result.data.is_running
          source.progress = result.data.progress || 0
          source.current = result.data.current || 0
          source.total = result.data.total || 0
          source.message = result.data.message || ''
          
          // 如果同步完成，停止轮询
          if (!result.data.is_running) {
            clearInterval(timer)
            pollingTimers.delete(serviceKey)
            
            // 刷新统计信息
            refreshStatistics()
            
            if (result.data.error) {
              ElMessage.error(`${source.name}同步失败: ${result.data.error}`)
            } else {
              ElMessage.success(`${source.name}同步完成`)
            }
          }
        }
      }
    } catch (error) {
      console.error('轮询状态失败:', error)
    }
  }, 1000) // 每秒轮询一次
  
  pollingTimers.set(serviceKey, timer)
}

const showSyncHistory = (source: any) => {
  selectedSource.value = source
  historyPagination.page = 1
  historyDialogVisible.value = true
  loadSyncHistory()
}

const loadSyncHistory = async () => {
  historyLoading.value = true
  try {
    if (!selectedSource.value) {
      syncHistory.value = []
      historyPagination.total = 0
      return
    }
    const statsResp = await fetch(`/api/data-sync/services/${selectedSource.value.key}/statistics`)
    const stats = await statsResp.json()
    const row = {
      sync_time: stats?.data?.last_sync_date || new Date().toISOString(),
      status: 'success',
      count: stats?.data?.total_count || 0,
      duration: stats?.data?.last_duration || 0,
      message: '统计信息'
    }
    syncHistory.value = [row]
    historyPagination.total = syncHistory.value.length
  } catch (e) {
    syncHistory.value = []
    historyPagination.total = 0
  } finally {
    historyLoading.value = false
  }
}

const showHistoryDetail = (row: any) => {
  ElMessageBox.alert(
    `<pre>${JSON.stringify(row, null, 2)}</pre>`,
    '同步详情',
    {
      dangerouslyUseHTMLString: true
    }
  )
}

const showScheduleDialog = () => {
  scheduleDialogVisible.value = true
}

const toggleSchedule = (source: any) => {
  ElMessage.success(`${source.name}定时任务已${source.enabled ? '启用' : '禁用'}`)
}

const editSchedule = (source: any) => {
  ElMessage.info('编辑定时任务功能开发中')
}

const saveScheduleConfig = () => {
  ElMessage.success('定时任务配置已保存')
  scheduleDialogVisible.value = false
}

const getSyncParams = (source: any) => {
  const paramsMap = {
    industry: [
      { name: 'src', label: '分类标准', type: 'text', placeholder: 'SW2021' },
      { name: 'level', label: '行业级别', type: 'text', placeholder: 'L1' }
    ],
    limit_prices: [
      { name: 'start_date', label: '开始日期', type: 'date', placeholder: '' },
      { name: 'end_date', label: '结束日期', type: 'date', placeholder: '' }
    ],
    suspend: [
      { name: 'start_date', label: '开始日期', type: 'date', placeholder: '' },
      { name: 'end_date', label: '结束日期', type: 'date', placeholder: '' }
    ],
    audit: [
      { name: 'start_date', label: '开始日期', type: 'date', placeholder: '' },
      { name: 'end_date', label: '结束日期', type: 'date', placeholder: '' }
    ]
  }
  return paramsMap[source.id] || []
}

// 辅助方法
const getPriorityType = (priority: string) => {
  const typeMap = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return typeMap[priority] || 'info'
}

const getScheduleText = (schedule: string) => {
  const textMap = {
    daily: '每日',
    weekly: '每周',
    monthly: '每月'
  }
  return textMap[schedule] || schedule
}

const getSyncStatusType = (status: string) => {
  const typeMap = {
    success: 'success',
    failed: 'danger',
    running: 'warning'
  }
  return typeMap[status] || 'info'
}

const getSyncStatusText = (status: string) => {
  const textMap = {
    success: '成功',
    failed: '失败',
    running: '运行中'
  }
  return textMap[status] || status
}

const formatDate = (date: string) => {
  if (!date) return '暂无数据'
  return new Date(date).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

const getNextSyncTime = (schedule: string) => {
  const now = new Date()
  let next = new Date(now)
  
  switch (schedule) {
    case 'daily':
      next.setDate(now.getDate() + 1)
      next.setHours(16, 0, 0, 0)
      break
    case 'weekly':
      next.setDate(now.getDate() + (7 - now.getDay() + 1))
      next.setHours(9, 0, 0, 0)
      break
    case 'monthly':
      next.setMonth(now.getMonth() + 1)
      next.setDate(1)
      next.setHours(1, 0, 0, 0)
      break
  }
  
  return next.toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadSyncServices()
})

// 组件卸载时清除所有轮询
import { onUnmounted } from 'vue'
onUnmounted(() => {
  pollingTimers.forEach(timer => clearInterval(timer))
  pollingTimers.clear()
})
</script>

<style scoped>
.data-sync {
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
  margin-bottom: 20px;
}

.data-source-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.data-source-card:hover {
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.source-name {
  font-weight: 600;
  font-size: 16px;
}

.card-content {
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.source-info {
  flex: 1;
}

.description {
  color: #606266;
  font-size: 14px;
  margin-bottom: 16px;
}

.stats {
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-item .label {
  color: #909399;
  font-size: 13px;
}

.stat-item .value {
  color: #303133;
  font-weight: 500;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-actions .el-button {
  flex: 1;
}

.sync-history {
  padding: 20px 0;
}

.history-header {
  margin-bottom: 20px;
}

.history-header h4 {
  margin: 0 0 8px 0;
}

.history-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.schedule-config ul {
  margin: 8px 0;
  padding-left: 20px;
}

.schedule-config li {
  margin: 4px 0;
}

.sync-params {
  padding: 20px 0;
}

.sync-progress {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
}

.progress-text {
  color: #606266;
  flex: 1;
}

.progress-count {
  color: #909399;
  font-weight: 500;
}
</style>
