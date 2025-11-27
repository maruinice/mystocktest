<template>
  <div class="multi-agent-analysis">
    <div class="page-header">
      <h2>多Agent分析</h2>
      <p>使用多个AI Agent对股票进行综合分析</p>
    </div>

    <!-- 分析配置 -->
    <el-card class="config-card">
      <template #header>
        <span>分析配置</span>
      </template>
      
      <el-form :model="analysisConfig" label-width="100px">
        <el-form-item label="股票代码">
          <el-input
            v-model="analysisConfig.stock_codes"
            placeholder="输入股票代码，多个用逗号分隔，例如: 000001.SZ,600036.SH"
          />
        </el-form-item>
        
        <el-form-item label="选择Agent">
          <el-checkbox-group v-model="analysisConfig.agent_ids">
            <el-checkbox
              v-for="agent in availableAgents"
              :key="agent.agent_id"
              :label="agent.agent_id"
            >
              {{ agent.display_name }} ({{ getAgentTypeName(agent.agent_type) }})
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="startAnalysis" :loading="analyzing">
            <el-icon><MagicStick /></el-icon>
            开始分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 分析结果 -->
    <el-card v-if="analysisResults.length > 0" class="results-card">
      <template #header>
        <span>分析结果</span>
      </template>
      
      <el-table :data="analysisResults" stripe>
        <el-table-column prop="stock_code" label="股票代码" width="120" />
        <el-table-column prop="stock_name" label="股票名称" width="120" />
        <el-table-column prop="final_score" label="综合评分" width="100">
          <template #default="{ row }">
            <el-progress
              :percentage="row.final_score"
              :color="getScoreColor(row.final_score)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="recommendation" label="推荐操作" width="120">
          <template #default="{ row }">
            <el-tag :type="getRecommendationColor(row.recommendation)">
              {{ getRecommendationText(row.recommendation) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="consensus_level" label="共识度" width="100">
          <template #default="{ row }">
            {{ (row.consensus_level * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getRiskLevelColor(row.risk_level)">
              {{ getRiskLevelText(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="分析摘要" min-width="200" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="分析详情" width="800px">
      <div v-if="selectedResult">
        <h3>{{ selectedResult.stock_code }} - {{ selectedResult.stock_name }}</h3>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="综合评分">
            {{ selectedResult.final_score }}
          </el-descriptions-item>
          <el-descriptions-item label="推荐操作">
            {{ getRecommendationText(selectedResult.recommendation) }}
          </el-descriptions-item>
          <el-descriptions-item label="共识度">
            {{ (selectedResult.consensus_level * 100).toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="风险等级">
            {{ getRiskLevelText(selectedResult.risk_level) }}
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top: 20px;">各Agent评分</h4>
        <el-table :data="getAgentScoresArray(selectedResult.agent_scores)" size="small">
          <el-table-column prop="agent_name" label="Agent" />
          <el-table-column prop="score" label="评分" width="100" />
          <el-table-column prop="recommendation" label="推荐" width="100" />
        </el-table>

        <div v-if="selectedResult.strengths && selectedResult.strengths.length > 0">
          <h4>优势</h4>
          <ul>
            <li v-for="(item, index) in selectedResult.strengths" :key="index">{{ item }}</li>
          </ul>
        </div>

        <div v-if="selectedResult.weaknesses && selectedResult.weaknesses.length > 0">
          <h4>劣势</h4>
          <ul>
            <li v-for="(item, index) in selectedResult.weaknesses" :key="index">{{ item }}</li>
          </ul>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import axios from 'axios'

const analysisConfig = ref({
  stock_codes: '',
  agent_ids: []
})

const availableAgents = ref<any[]>([])
const analyzing = ref(false)
const analysisResults = ref<any[]>([])
const showDetailDialog = ref(false)
const selectedResult = ref<any>(null)

const getAgentTypeName = (type: string) => {
  const map: Record<string, string> = {
    market_analyst: '市场分析师',
    fundamental_analyst: '基本面分析师',
    technical_analyst: '技术分析师',
    news_analyst: '新闻分析师',
    sentiment_analyst: '情绪分析师'
  }
  return map[type] || type
}

const getScoreColor = (score: number) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getRecommendationText = (rec: string) => {
  const map: Record<string, string> = {
    strong_buy: '强烈买入',
    buy: '买入',
    hold: '持有',
    sell: '卖出',
    strong_sell: '强烈卖出'
  }
  return map[rec] || rec
}

const getRecommendationColor = (rec: string) => {
  const map: Record<string, string> = {
    strong_buy: 'success',
    buy: 'success',
    hold: 'info',
    sell: 'warning',
    strong_sell: 'danger'
  }
  return map[rec] || 'info'
}

const getRiskLevelText = (level: string) => {
  const map: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    very_high: '极高'
  }
  return map[level] || level
}

const getRiskLevelColor = (level: string) => {
  const map: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
    very_high: 'danger'
  }
  return map[level] || 'info'
}

const loadAgents = async () => {
  try {
    const response = await axios.get('/api/agent/agents', {
      params: { enabled: true }
    })
    if (response.data.code === 200) {
      availableAgents.value = response.data.data.items
      // 默认选中所有Agent
      analysisConfig.value.agent_ids = availableAgents.value.map(a => a.agent_id)
    }
  } catch (error) {
    ElMessage.error('加载Agent列表失败')
  }
}

const startAnalysis = async () => {
  if (!analysisConfig.value.stock_codes) {
    ElMessage.warning('请输入股票代码')
    return
  }
  
  if (analysisConfig.value.agent_ids.length === 0) {
    ElMessage.warning('请至少选择一个Agent')
    return
  }

  analyzing.value = true
  try {
    const stockCodes = analysisConfig.value.stock_codes.split(',').map(s => s.trim())
    
    const response = await axios.post('/api/agent/analyze/batch', {
      stock_codes: stockCodes,
      agent_ids: analysisConfig.value.agent_ids
    })
    
    if (response.data.code === 200) {
      analysisResults.value = response.data.data.results || []
      ElMessage.success('分析完成')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '分析失败')
  } finally {
    analyzing.value = false
  }
}

const viewDetail = (result: any) => {
  selectedResult.value = result
  showDetailDialog.value = true
}

const getAgentScoresArray = (agentScores: any) => {
  if (!agentScores) return []
  return Object.values(agentScores)
}

onMounted(() => {
  loadAgents()
})
</script>

<style lang="scss" scoped>
.multi-agent-analysis {
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

.config-card,
.results-card {
  margin-bottom: 20px;
}

h4 {
  margin-top: 16px;
  margin-bottom: 8px;
}

ul {
  margin: 0;
  padding-left: 20px;
}
</style>
