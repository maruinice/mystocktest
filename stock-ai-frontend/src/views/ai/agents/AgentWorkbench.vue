<template>
  <div class="agent-workbench">
    <div class="page-header">
      <h2>Agent工作台</h2>
      <p>配置和管理AI分析Agent</p>
    </div>

    <div class="actions">
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建Agent
      </el-button>
      <el-button @click="loadAgents">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- Agent列表 -->
    <el-table :data="agents" v-loading="loading" stripe>
      <el-table-column prop="display_name" label="名称" width="150" />
      <el-table-column prop="agent_type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getAgentTypeColor(row.agent_type)">
            {{ getAgentTypeName(row.agent_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="model_id" label="绑定模型" width="150" />
      <el-table-column prop="priority" label="优先级" width="80" />
      <el-table-column prop="weight" label="权重" width="80" />
      <el-table-column prop="total_analyses" label="分析次数" width="100" />
      <el-table-column prop="avg_score" label="平均评分" width="100">
        <template #default="{ row }">
          {{ row.avg_score ? row.avg_score.toFixed(2) : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="enabled" label="状态" width="80">
        <template #default="{ row }">
          <el-switch
            v-model="row.enabled"
            @change="toggleAgentStatus(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="editAgent(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteAgent(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingAgent ? '编辑Agent' : '创建Agent'"
      width="600px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="Agent名称">
          <el-input v-model="formData.name" placeholder="例如: market_analyst_01" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="formData.display_name" placeholder="例如: 市场分析师" />
        </el-form-item>
        <el-form-item label="Agent类型">
          <el-select v-model="formData.agent_type" placeholder="请选择">
            <el-option label="市场分析师" value="market_analyst" />
            <el-option label="基本面分析师" value="fundamental_analyst" />
            <el-option label="技术分析师" value="technical_analyst" />
            <el-option label="新闻分析师" value="news_analyst" />
            <el-option label="情绪分析师" value="sentiment_analyst" />
          </el-select>
        </el-form-item>
        <el-form-item label="绑定模型">
          <el-select v-model="formData.model_id" placeholder="请选择模型">
            <el-option
              v-for="model in availableModels"
              :key="model.model_id"
              :label="model.display_name || model.name"
              :value="model.model_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="formData.priority" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="权重">
          <el-input-number v-model="formData.weight" :min="0" :max="1" :step="0.1" />
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input
            v-model="formData.system_prompt"
            type="textarea"
            :rows="6"
            placeholder="输入Agent的系统提示词..."
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="Agent描述..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAgent">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

interface Agent {
  agent_id: string
  name: string
  display_name: string
  agent_type: string
  model_id: string
  priority: number
  weight: number
  enabled: boolean
  total_analyses: number
  avg_score: number
  description?: string
  system_prompt?: string
}

interface Model {
  model_id: string
  name: string
  display_name?: string
}

const agents = ref<Agent[]>([])
const availableModels = ref<Model[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const editingAgent = ref<Agent | null>(null)

const formData = ref({
  name: '',
  display_name: '',
  agent_type: '',
  model_id: '',
  priority: 1,
  weight: 1.0,
  system_prompt: '',
  description: ''
})

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

const getAgentTypeColor = (type: string) => {
  const map: Record<string, string> = {
    market_analyst: 'primary',
    fundamental_analyst: 'success',
    technical_analyst: 'warning',
    news_analyst: 'info',
    sentiment_analyst: 'danger'
  }
  return map[type] || ''
}

const loadAgents = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/agent/agents')
    if (response.data.code === 200) {
      agents.value = response.data.data.items
    }
  } catch (error) {
    ElMessage.error('加载Agent列表失败')
  } finally {
    loading.value = false
  }
}

const loadModels = async () => {
  try {
    const response = await axios.get('/api/model-management/models')
    if (response.data.code === 200) {
      availableModels.value = response.data.data.items.filter((m: any) => m.enabled)
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

const editAgent = (agent: Agent) => {
  editingAgent.value = agent
  formData.value = {
    name: agent.name,
    display_name: agent.display_name,
    agent_type: agent.agent_type,
    model_id: agent.model_id,
    priority: agent.priority,
    weight: agent.weight,
    system_prompt: agent.system_prompt || '',
    description: agent.description || ''
  }
  showCreateDialog.value = true
}

const saveAgent = async () => {
  try {
    if (editingAgent.value) {
      // 更新
      await axios.put(`/api/agent/agents/${editingAgent.value.agent_id}`, formData.value)
      ElMessage.success('Agent更新成功')
    } else {
      // 创建
      await axios.post('/api/agent/agents', formData.value)
      ElMessage.success('Agent创建成功')
    }
    showCreateDialog.value = false
    editingAgent.value = null
    loadAgents()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '保存失败')
  }
}

const deleteAgent = async (agent: Agent) => {
  try {
    await ElMessageBox.confirm(`确定删除Agent "${agent.display_name}"?`, '确认删除', {
      type: 'warning'
    })
    await axios.delete(`/api/agent/agents/${agent.agent_id}`)
    ElMessage.success('删除成功')
    loadAgents()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const toggleAgentStatus = async (agent: Agent) => {
  try {
    await axios.post(`/api/agent/agents/${agent.agent_id}/toggle`, {
      enabled: agent.enabled
    })
    ElMessage.success(`Agent已${agent.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    agent.enabled = !agent.enabled
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  loadAgents()
  loadModels()
})
</script>

<style lang="scss" scoped>
.agent-workbench {
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
</style>
