<template>
  <div class="ai-decision">
    <div class="page-header">
      <h2>AI决策中心</h2>
      <p>查看多Agent分析生成的交易建议</p>
    </div>

    <div class="actions">
      <el-button @click="loadDecisions">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 决策列表 -->
    <el-table :data="decisions" v-loading="loading" stripe>
      <el-table-column prop="stock_code" label="股票代码" width="100" />
      <el-table-column prop="stock_name" label="股票名称" width="120" />
      <el-table-column prop="final_score" label="综合评分" width="100">
        <template #default="{ row }">
          <el-tag :type="getScoreType(row.final_score)">
            {{ row.final_score?.toFixed(1) || '-' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="recommendation" label="操作建议" width="100">
        <template #default="{ row }">
          <el-tag :type="getRecommendationType(row.recommendation)">
            {{ getRecommendationText(row.recommendation) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="entry_price" label="建议买入价" width="110">
        <template #default="{ row }">
          {{ row.entry_price ? `¥${row.entry_price.toFixed(2)}` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="target_price" label="目标止盈价" width="110">
        <template #default="{ row }">
          {{ row.target_price ? `¥${row.target_price.toFixed(2)}` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="stop_loss_price" label="止损价" width="100">
        <template #default="{ row }">
          {{ row.stop_loss_price ? `¥${row.stop_loss_price.toFixed(2)}` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="expected_return" label="预期收益" width="100">
        <template #default="{ row }">
          <span v-if="row.expected_return" :class="row.expected_return > 0 ? 'profit' : 'loss'">
            {{ row.expected_return.toFixed(2) }}%
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="holding_period" label="持仓周期" width="100">
        <template #default="{ row }">
          {{ row.holding_period ? `${row.holding_period}天` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="risk_level" label="风险等级" width="100">
        <template #default="{ row }">
          <el-tag :type="getRiskType(row.risk_level)">
            {{ getRiskText(row.risk_level) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="分析时间" width="160" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetail" title="分析详情" width="800px">
      <div v-if="currentDecision">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="股票代码">{{ currentDecision.stock_code }}</el-descriptions-item>
          <el-descriptions-item label="股票名称">{{ currentDecision.stock_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="综合评分">{{ currentDecision.final_score?.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="共识度">{{ (currentDecision.consensus_level * 100).toFixed(1) }}%</el-descriptions-item>
          <el-descriptions-item label="操作建议">
            <el-tag :type="getRecommendationType(currentDecision.recommendation)">
              {{ getRecommendationText(currentDecision.recommendation) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <el-tag :type="getRiskType(currentDecision.risk_level)">
              {{ getRiskText(currentDecision.risk_level) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <h4>交易建议</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="建议买入价">¥{{ currentDecision.entry_price?.toFixed(2) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="目标止盈价">¥{{ currentDecision.target_price?.toFixed(2) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="止损价">¥{{ currentDecision.stop_loss_price?.toFixed(2) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预期收益">{{ currentDecision.expected_return?.toFixed(2) || '-' }}%</el-descriptions-item>
          <el-descriptions-item label="建议持仓">{{ currentDecision.holding_period || '-' }}天</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <h4>交易理由</h4>
        <p>{{ currentDecision.trade_reason || '暂无' }}</p>

        <h4>综合分析</h4>
        <p>{{ currentDecision.summary }}</p>

        <el-row :gutter="20">
          <el-col :span="12">
            <h4>优势</h4>
            <ul v-if="currentDecision.strengths && currentDecision.strengths.length">
              <li v-for="(item, index) in currentDecision.strengths" :key="index">{{ item }}</li>
            </ul>
            <p v-else>暂无</p>
          </el-col>
          <el-col :span="12">
            <h4>劣势</h4>
            <ul v-if="currentDecision.weaknesses && currentDecision.weaknesses.length">
              <li v-for="(item, index) in currentDecision.weaknesses" :key="index">{{ item }}</li>
            </ul>
            <p v-else>暂无</p>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

interface Decision {
  result_id: string
  stock_code: string
  stock_name?: string
  final_score?: number
  recommendation?: string
  consensus_level?: number
  risk_level?: string
  summary?: string
  entry_price?: number
  target_price?: number
  stop_loss_price?: number
  expected_return?: number
  holding_period?: number
  trade_reason?: string
  strengths?: string[]
  weaknesses?: string[]
  created_at?: string
}

const loading = ref(false)
const decisions = ref<Decision[]>([])
const showDetail = ref(false)
const currentDecision = ref<Decision | null>(null)

const loadDecisions = async () => {
  loading.value = true
  try {
    // 获取最近的分析会话
    const sessionsResponse = await axios.get('/api/agent/sessions', {
      params: { page: 1, page_size: 10 }
    })
    
    if (sessionsResponse.data.code === 200 && sessionsResponse.data.data.items.length > 0) {
      // 获取最新会话的结果
      const latestSession = sessionsResponse.data.data.items[0]
      const resultsResponse = await axios.get(`/api/agent/sessions/${latestSession.session_id}/results`)
      
      if (resultsResponse.data.code === 200) {
        decisions.value = resultsResponse.data.data
      }
    } else {
      decisions.value = []
    }
  } catch (error) {
    console.error('加载决策失败:', error)
    ElMessage.error('加载决策失败')
  } finally {
    loading.value = false
  }
}

const viewDetail = (decision: Decision) => {
  currentDecision.value = decision
  showDetail.value = true
}

const getScoreType = (score?: number) => {
  if (!score) return ''
  if (score >= 80) return 'success'
  if (score >= 65) return 'warning'
  return 'danger'
}

const getRecommendationType = (rec?: string) => {
  if (!rec) return ''
  if (rec === 'strong_buy' || rec === 'buy') return 'success'
  if (rec === 'hold') return 'warning'
  return 'danger'
}

const getRecommendationText = (rec?: string) => {
  const map: Record<string, string> = {
    strong_buy: '强烈买入',
    buy: '买入',
    hold: '持有',
    sell: '卖出',
    strong_sell: '强烈卖出'
  }
  return map[rec || ''] || '-'
}

const getRiskType = (risk?: string) => {
  if (!risk) return ''
  if (risk === 'low') return 'success'
  if (risk === 'medium') return 'warning'
  return 'danger'
}

const getRiskText = (risk?: string) => {
  const map: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    very_high: '极高'
  }
  return map[risk || ''] || '-'
}

onMounted(() => {
  loadDecisions()
})
</script>

<style lang="scss" scoped>
.ai-decision {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
  
  h2 {
    margin: 0 0 8px 0;
    font-size: 24px;
  }
  
  p {
    margin: 0;
    color: #666;
  }
}

.actions {
  margin-bottom: 16px;
}

.profit {
  color: #67C23A;
  font-weight: 600;
}

.loss {
  color: #F56C6C;
  font-weight: 600;
}

h4 {
  margin: 16px 0 8px 0;
  font-size: 14px;
  font-weight: 600;
}

ul {
  margin: 8px 0;
  padding-left: 20px;
}
</style>