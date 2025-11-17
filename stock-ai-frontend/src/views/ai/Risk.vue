<template>
  <div class="risk-control-container">
    <div class="page-header">
      <h2>风险控制中心</h2>
      <p>实时监控和管理投资风险</p>
    </div>

    <!-- 风险概览 -->
    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <div class="overview-card">
          <div class="card-icon risk-level">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">风险等级</div>
            <div class="card-value">{{ riskLevel }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="overview-card">
          <div class="card-icon var-value">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">VaR值</div>
            <div class="card-value">{{ varValue }}%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="overview-card">
          <div class="card-icon max-drawdown">
            <el-icon><Bottom /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">最大回撤</div>
            <div class="card-value">{{ maxDrawdown }}%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="overview-card">
          <div class="card-icon active-alerts">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">活跃警报</div>
            <div class="card-value">{{ activeAlerts }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 风险控制操作 -->
    <div class="risk-actions">
      <el-button type="primary" @click="runRiskCheck" :loading="checking">
        <el-icon><Search /></el-icon>
        风险检查
      </el-button>
      <el-button @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
      <el-button type="warning" @click="showRiskSettings">
        <el-icon><Setting /></el-icon>
        风险设置
      </el-button>
    </div>

    <el-row :gutter="20">
      <!-- 风险警报 -->
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <h3>风险警报</h3>
            <el-button size="small" @click="clearAlerts">清除已读</el-button>
          </div>
          
          <div class="alert-list">
            <div
              v-for="alert in riskAlerts"
              :key="alert.id"
              class="alert-item"
              :class="alert.level"
            >
              <div class="alert-icon">
                <el-icon v-if="alert.level === 'high'"><WarningFilled /></el-icon>
                <el-icon v-else-if="alert.level === 'medium'"><Warning /></el-icon>
                <el-icon v-else><InfoFilled /></el-icon>
              </div>
              <div class="alert-content">
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-message">{{ alert.message }}</div>
                <div class="alert-time">{{ formatDateTime(alert.created_at) }}</div>
              </div>
              <div class="alert-actions">
                <el-button size="small" text @click="handleAlert(alert)">处理</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 风险指标 -->
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <h3>风险指标</h3>
          </div>
          
          <div class="risk-metrics">
            <div class="metric-item">
              <div class="metric-label">夏普比率</div>
              <div class="metric-value">{{ sharpeRatio }}</div>
              <el-progress
                :percentage="Math.min(sharpeRatio * 50, 100)"
                :color="getSharpeColor(sharpeRatio)"
                :stroke-width="6"
              />
            </div>
            
            <div class="metric-item">
              <div class="metric-label">波动率</div>
              <div class="metric-value">{{ volatility }}%</div>
              <el-progress
                :percentage="Math.min(volatility * 5, 100)"
                :color="getVolatilityColor(volatility)"
                :stroke-width="6"
              />
            </div>
            
            <div class="metric-item">
              <div class="metric-label">贝塔系数</div>
              <div class="metric-value">{{ beta }}</div>
              <el-progress
                :percentage="Math.min(Math.abs(beta) * 100, 100)"
                :color="getBetaColor(beta)"
                :stroke-width="6"
              />
            </div>
            
            <div class="metric-item">
              <div class="metric-label">信息比率</div>
              <div class="metric-value">{{ informationRatio }}</div>
              <el-progress
                :percentage="Math.min(Math.abs(informationRatio) * 50, 100)"
                :color="getInfoRatioColor(informationRatio)"
                :stroke-width="6"
              />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 风险设置对话框 -->
    <el-dialog v-model="showSettings" title="风险控制设置" width="600px">
      <el-form :model="riskSettings" label-width="120px">
        <el-form-item label="最大仓位">
          <el-slider
            v-model="riskSettings.maxPosition"
            :min="0"
            :max="100"
            :step="5"
            show-stops
            show-input
          />
        </el-form-item>
        
        <el-form-item label="止损比例">
          <el-slider
            v-model="riskSettings.stopLoss"
            :min="1"
            :max="20"
            :step="0.5"
            show-stops
            show-input
          />
        </el-form-item>
        
        <el-form-item label="VaR阈值">
          <el-slider
            v-model="riskSettings.varThreshold"
            :min="1"
            :max="10"
            :step="0.1"
            show-stops
            show-input
          />
        </el-form-item>
        
        <el-form-item label="启用自动止损">
          <el-switch v-model="riskSettings.autoStopLoss" />
        </el-form-item>
        
        <el-form-item label="启用风险预警">
          <el-switch v-model="riskSettings.riskAlert" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveRiskSettings">保存设置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '@/utils/format'
import { riskControlApi } from '@/api/ai'
import {
  Warning,
  WarningFilled,
  InfoFilled,
  TrendCharts,
  Bottom,
  Bell,
  Search,
  Refresh,
  Setting
} from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const checking = ref(false)
const showSettings = ref(false)

// 风险概览数据
const riskLevel = ref('中等')
const varValue = ref(2.5)
const maxDrawdown = ref(8.3)
const activeAlerts = ref(3)

// 风险指标
const sharpeRatio = ref(1.25)
const volatility = ref(18.5)
const beta = ref(1.08)
const informationRatio = ref(0.85)

// 风险警报
const riskAlerts = ref([
  {
    id: 1,
    level: 'high',
    title: '持仓集中度过高',
    message: '单一股票持仓超过20%，建议分散投资',
    created_at: '2023-12-01T10:30:00Z'
  },
  {
    id: 2,
    level: 'medium',
    title: 'VaR值超过阈值',
    message: '当前VaR值为2.5%，超过设定阈值2.0%',
    created_at: '2023-12-01T09:45:00Z'
  },
  {
    id: 3,
    level: 'low',
    title: '市场波动加剧',
    message: '市场波动率上升，建议关注风险',
    created_at: '2023-12-01T09:00:00Z'
  }
])

// 风险设置
const riskSettings = reactive({
  maxPosition: 20,
  stopLoss: 5,
  varThreshold: 2.0,
  autoStopLoss: true,
  riskAlert: true
})

// 方法
const getSharpeColor = (value: number) => {
  if (value >= 1.5) return '#67C23A'
  if (value >= 1.0) return '#E6A23C'
  return '#F56C6C'
}

const getVolatilityColor = (value: number) => {
  if (value <= 15) return '#67C23A'
  if (value <= 25) return '#E6A23C'
  return '#F56C6C'
}

const getBetaColor = (value: number) => {
  if (Math.abs(value - 1) <= 0.2) return '#67C23A'
  if (Math.abs(value - 1) <= 0.5) return '#E6A23C'
  return '#F56C6C'
}

const getInfoRatioColor = (value: number) => {
  if (value >= 0.5) return '#67C23A'
  if (value >= 0) return '#E6A23C'
  return '#F56C6C'
}

const refreshData = async () => {
  loading.value = true
  try {
    // 获取风险概览
    const overviewResponse = await riskControlApi.getRiskOverview()
    if (overviewResponse.data) {
      riskLevel.value = overviewResponse.data.risk_level
      varValue.value = overviewResponse.data.var_value
      maxDrawdown.value = overviewResponse.data.max_drawdown
      activeAlerts.value = overviewResponse.data.active_alerts
    }

    // 获取风险指标
    const metricsResponse = await riskControlApi.getRiskMetrics()
    if (metricsResponse.data) {
      sharpeRatio.value = metricsResponse.data.sharpe_ratio
      volatility.value = metricsResponse.data.volatility
      beta.value = metricsResponse.data.beta
      informationRatio.value = metricsResponse.data.information_ratio
    }

    // 获取风险警报
    const alertsResponse = await riskControlApi.getRiskAlerts()
    if (alertsResponse.data?.alerts) {
      riskAlerts.value = alertsResponse.data.alerts
    }

    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('数据刷新失败:', error)
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const runRiskCheck = async () => {
  checking.value = true
  try {
    const response = await riskControlApi.runRiskCheck()
    
    if (response.data) {
      // 检查完成后刷新数据
      await refreshData()
      ElMessage.success('风险检查完成')
    }
  } catch (error) {
    console.error('风险检查失败:', error)
    ElMessage.error('风险检查失败')
  } finally {
    checking.value = false
  }
}

const showRiskSettings = () => {
  showSettings.value = true
}

const saveRiskSettings = async () => {
  try {
    const response = await riskControlApi.updateRiskSettings({
      max_position: riskSettings.maxPosition,
      stop_loss: riskSettings.stopLoss,
      var_threshold: riskSettings.varThreshold,
      auto_stop_loss: riskSettings.autoStopLoss,
      risk_alert: riskSettings.riskAlert
    })
    
    if (response.data) {
      showSettings.value = false
      ElMessage.success('风险设置保存成功')
    }
  } catch (error) {
    console.error('风险设置保存失败:', error)
    ElMessage.error('风险设置保存失败')
  }
}

const clearAlerts = async () => {
  try {
    await ElMessageBox.confirm('确认清除所有已读警报？', '确认操作', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    riskAlerts.value = riskAlerts.value.filter(alert => alert.level === 'high')
    ElMessage.success('已清除已读警报')
  } catch (error) {
    // 用户取消
  }
}

const handleAlert = (alert: any) => {
  ElMessage.info(`处理警报: ${alert.title}`)
}

onMounted(async () => {
  // 初始化时加载风险数据
  await refreshData()
})
</script>

<style lang="scss" scoped>
.risk-control-container {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
  
  h2 {
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  p {
    margin: 0;
    color: var(--el-text-color-regular);
  }
}

.overview-cards {
  margin-bottom: 24px;
}

.overview-card {
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  
  .el-icon {
    font-size: 24px;
    color: white;
  }
  
  &.risk-level {
    background: linear-gradient(135deg, #F56C6C 0%, #E6A23C 100%);
  }
  
  &.var-value {
    background: linear-gradient(135deg, #409EFF 0%, #667eea 100%);
  }
  
  &.max-drawdown {
    background: linear-gradient(135deg, #909399 0%, #606266 100%);
  }
  
  &.active-alerts {
    background: linear-gradient(135deg, #E6A23C 0%, #F56C6C 100%);
  }
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-family: 'Courier New', monospace;
}

.risk-actions {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}

.card {
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

.alert-list {
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  border-left: 4px solid;
  
  &.high {
    background: rgba(245, 108, 108, 0.1);
    border-left-color: #F56C6C;
  }
  
  &.medium {
    background: rgba(230, 162, 60, 0.1);
    border-left-color: #E6A23C;
  }
  
  &.low {
    background: rgba(64, 158, 255, 0.1);
    border-left-color: #409EFF;
  }
}

.alert-icon {
  margin-right: 12px;
  margin-top: 2px;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.alert-message {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}

.alert-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.alert-actions {
  margin-left: 12px;
}

.risk-metrics {
  .metric-item {
    margin-bottom: 20px;
    
    .metric-label {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 14px;
      color: var(--el-text-color-regular);
    }
    
    .metric-value {
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
}
</style>