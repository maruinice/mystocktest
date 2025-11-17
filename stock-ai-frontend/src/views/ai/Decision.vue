<template>
  <div class="ai-decision-container">
    <div class="page-header">
      <h2>AI决策引擎</h2>
      <p>基于多模型融合的智能投资决策系统</p>
    </div>

    <!-- 决策概览 -->
    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <div class="overview-card">
          <div class="card-icon active-decisions">
            <el-icon><MagicStick /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">活跃决策</div>
            <div class="card-value">{{ activeDecisions }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="overview-card">
          <div class="card-icon success-rate">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">成功率</div>
            <div class="card-value">{{ successRate }}%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="overview-card">
          <div class="card-icon total-profit">
            <el-icon><Money /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">总收益</div>
            <div class="card-value">{{ totalProfit }}%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="overview-card">
          <div class="card-icon model-count">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-title">模型数量</div>
            <div class="card-value">{{ modelCount }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 决策操作 -->
    <div class="decision-actions">
      <el-button type="primary" @click="generateDecision" :loading="generating">
        <el-icon><MagicStick /></el-icon>
        生成新决策
      </el-button>
      <el-button @click="refreshDecisions" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索决策..."
        style="width: 200px; margin-left: 12px;"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 决策列表 -->
    <div class="card">
      <div class="card-header">
        <h3>决策记录</h3>
      </div>
      
      <el-table :data="filteredDecisions" v-loading="loading" stripe>
        <el-table-column prop="decision_id" label="决策ID" width="120" />
        <el-table-column prop="symbol" label="股票代码" width="100" />
        <el-table-column prop="action" label="决策动作" width="100">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)">
              {{ getActionText(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="100">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.round(row.confidence * 100)"
              :color="getConfidenceColor(row.confidence)"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="expected_return" label="预期收益" width="100">
          <template #default="{ row }">
            <span :class="row.expected_return >= 0 ? 'profit' : 'loss'">
              {{ (row.expected_return * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="risk_score" label="风险评分" width="100">
          <template #default="{ row }">
            <el-rate
              v-model="row.risk_score"
              disabled
              :max="5"
              :colors="['#67C23A', '#E6A23C', '#F56C6C']"
            />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDecision(row)">详情</el-button>
            <el-button
              size="small"
              type="primary"
              @click="executeDecision(row)"
              :disabled="row.status !== 'pending'"
            >
              执行
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { formatDateTime } from '@/utils/format'
import { getTagType, type TagType } from '@/utils/element-plus'
import { aiDecisionApi } from '@/api/ai'
import {
  MagicStick,
  TrendCharts,
  Money,
  DataAnalysis,
  Refresh,
  Search
} from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const generating = ref(false)
const searchKeyword = ref('')

// 模拟数据
const activeDecisions = ref(12)
const successRate = ref(78.5)
const totalProfit = ref(15.6)
const modelCount = ref(5)

const decisions = ref([
  {
    decision_id: 'DEC_001',
    symbol: '000001',
    action: 'buy',
    confidence: 0.85,
    expected_return: 0.12,
    risk_score: 2,
    status: 'pending',
    created_at: '2023-12-01T10:00:00Z'
  },
  {
    decision_id: 'DEC_002',
    symbol: '000002',
    action: 'sell',
    confidence: 0.92,
    expected_return: 0.08,
    risk_score: 1,
    status: 'executed',
    created_at: '2023-12-01T09:30:00Z'
  },
  {
    decision_id: 'DEC_003',
    symbol: '600036',
    action: 'hold',
    confidence: 0.67,
    expected_return: -0.03,
    risk_score: 3,
    status: 'cancelled',
    created_at: '2023-12-01T09:00:00Z'
  }
])

// 计算属性
const filteredDecisions = computed(() => {
  if (!searchKeyword.value) return decisions.value
  
  return decisions.value.filter(decision =>
    decision.symbol.includes(searchKeyword.value) ||
    decision.decision_id.includes(searchKeyword.value)
  )
})

// 方法
const getActionText = (action: string) => {
  const actionMap: Record<string, string> = {
    buy: '买入',
    sell: '卖出',
    hold: '持有'
  }
  return actionMap[action] || action
}

const getActionType = (action: string): TagType => {
  const typeMap: Record<string, string> = {
    buy: 'success',
    sell: 'danger',
    hold: 'warning'
  }
  return getTagType(typeMap[action] || 'info')
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待执行',
    executed: '已执行',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const getStatusType = (status: string): TagType => {
  const typeMap: Record<string, string> = {
    pending: 'warning',
    executed: 'success',
    cancelled: 'info'
  }
  return getTagType(typeMap[status] || 'info')
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return '#67C23A'
  if (confidence >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

const refreshDecisions = async () => {
  loading.value = true
  try {
    const response = await aiDecisionApi.getDecisions({
      page: 1,
      page_size: 50
    })
    
    if (response.data?.decisions) {
      decisions.value = response.data.decisions
    }
    
    ElMessage.success('刷新成功')
  } catch (error) {
    console.error('刷新决策失败:', error)
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const generateDecision = async () => {
  generating.value = true
  try {
    const response = await aiDecisionApi.generateDecision({
      strategy_type: 'auto',
      force_analysis: true
    })
    
    if (response.data) {
      // 刷新决策列表
      await refreshDecisions()
      ElMessage.success('决策生成成功')
    }
  } catch (error) {
    console.error('决策生成失败:', error)
    ElMessage.error('决策生成失败')
  } finally {
    generating.value = false
  }
}

const viewDecision = (decision: any) => {
  ElMessage.info(`查看决策详情: ${decision.decision_id}`)
}

const executeDecision = async (decision: any) => {
  try {
    const response = await aiDecisionApi.executeDecision(decision.decision_id)
    
    if (response.data) {
      decision.status = 'executed'
      ElMessage.success('决策执行成功')
    }
  } catch (error) {
    console.error('决策执行失败:', error)
    ElMessage.error('决策执行失败')
  }
}

onMounted(async () => {
  // 初始化时加载决策列表
  await refreshDecisions()
})
</script>

<style lang="scss" scoped>
.ai-decision-container {
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
  
  &.active-decisions {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  &.success-rate {
    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  }
  
  &.total-profit {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  }
  
  &.model-count {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
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

.decision-actions {
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

.profit {
  color: var(--el-color-success);
  font-weight: 600;
}

.loss {
  color: var(--el-color-danger);
  font-weight: 600;
}
</style>