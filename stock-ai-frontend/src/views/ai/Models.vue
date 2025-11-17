<template>
  <div class="models-container">
    <div class="page-header">
      <h2>模型管理中心</h2>
      <p>管理AI模型和多模型组合策略</p>
    </div>

    <!-- 标签页导航 -->
    <el-tabs v-model="activeTab" class="model-tabs">
      <!-- 仪表盘 -->
      <el-tab-pane label="仪表盘" name="dashboard">
        <ModelDashboard />
      </el-tab-pane>

      <!-- 模型管理 -->
      <el-tab-pane label="模型管理" name="models">
        <ModelList
          :refresh-trigger="refreshTrigger"
          @create-model="handleCreateModel"
          @edit-model="handleEditModel"
          @view-model="handleViewModel"
        />
      </el-tab-pane>

      <!-- 组合管理 -->
      <el-tab-pane label="组合管理" name="ensembles">
        <EnsembleManager />
      </el-tab-pane>

      <!-- 模型测试 -->
      <el-tab-pane label="模型测试" name="testing">
        <ModelTester />
      </el-tab-pane>
    </el-tabs>

    <!-- 模型表单对话框 -->
    <ModelForm
      v-model:visible="showModelForm"
      :model="selectedModel"
      @success="handleModelFormSuccess"
    />

    <!-- 模型详情对话框 -->
    <el-dialog
      v-model="showModelDetail"
      title="模型详情"
      width="800px"
    >
      <div v-if="selectedModel" class="model-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模型ID">
            {{ selectedModel.model_id }}
          </el-descriptions-item>
          <el-descriptions-item label="模型名称">
            {{ selectedModel.name }}
          </el-descriptions-item>
          <el-descriptions-item label="显示名称">
            {{ selectedModel.display_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="模型类型">
            <el-tag :type="getModelTypeColor(selectedModel.model_type)">
              {{ getModelTypeText(selectedModel.model_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="提供商">
            {{ selectedModel.provider }}
          </el-descriptions-item>
          <el-descriptions-item label="模型版本">
            {{ selectedModel.model_version || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="API地址">
            {{ selectedModel.base_url }}
          </el-descriptions-item>
          <el-descriptions-item label="最大Token数">
            {{ selectedModel.max_tokens || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="温度参数">
            {{ selectedModel.temperature || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="超时时间">
            {{ selectedModel.timeout || '-' }}s
          </el-descriptions-item>
          <el-descriptions-item label="准确率">
            <div v-if="selectedModel.accuracy !== undefined">
              <el-progress
                :percentage="Math.round(selectedModel.accuracy * 100)"
                :color="getAccuracyColor(selectedModel.accuracy)"
                :stroke-width="6"
              />
            </div>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="响应时间">
            {{ selectedModel.response_time ? selectedModel.response_time.toFixed(2) + 's' : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="使用次数">
            {{ selectedModel.usage_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedModel.enabled ? 'success' : 'info'">
              {{ selectedModel.enabled ? '启用' : '停用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(selectedModel.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(selectedModel.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedModel.description || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 配置信息 -->
        <div v-if="selectedModel.config_json" class="config-section">
          <h4>配置信息</h4>
          <el-input
            :model-value="JSON.stringify(selectedModel.config_json, null, 2)"
            type="textarea"
            :rows="6"
            readonly
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { formatDateTime } from '@/utils/format'
import { getTagType, type TagType } from '@/utils/element-plus'
import ModelList from '@/components/model/ModelList.vue'
import ModelForm from '@/components/model/ModelForm.vue'
import EnsembleManager from '@/components/model/EnsembleManager.vue'
import ModelTester from '@/components/model/ModelTester.vue'
import ModelDashboard from '@/components/model/ModelDashboard.vue'
import { type AIModel, ModelType } from '@/api/model-management'

// 响应式数据
const activeTab = ref('dashboard')
const showModelForm = ref(false)
const showModelDetail = ref(false)
const selectedModel = ref<AIModel | null>(null)
const refreshTrigger = ref(0)

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

const getModelTypeColor = (type: ModelType): TagType => {
  const colorMap = {
    [ModelType.DEEPSEEK]: 'primary',
    [ModelType.OPENAI]: 'success',
    [ModelType.CLAUDE]: 'warning',
    [ModelType.CUSTOM]: 'info'
  }
  return getTagType(colorMap[type] || 'info')
}

const getAccuracyColor = (accuracy: number) => {
  if (accuracy >= 0.9) return '#67C23A'
  if (accuracy >= 0.8) return '#E6A23C'
  if (accuracy >= 0.7) return '#F56C6C'
  return '#909399'
}

// 事件处理
const handleCreateModel = () => {
  selectedModel.value = null
  showModelForm.value = true
}

const handleEditModel = (model: AIModel) => {
  selectedModel.value = model
  showModelForm.value = true
}

const handleViewModel = (model: AIModel) => {
  selectedModel.value = model
  showModelDetail.value = true
}

const handleModelFormSuccess = (_model: AIModel) => {
  ElMessage.success(selectedModel.value ? '模型更新成功' : '模型创建成功')
  refreshTrigger.value++
  
  // 如果是在仪表盘页面，也需要刷新仪表盘数据
  if (activeTab.value === 'dashboard') {
    // 这里可以触发仪表盘刷新
  }
}
</script>

<style lang="scss" scoped>
.models-container {
  padding: 24px;
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
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

.model-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  
  :deep(.el-tabs__content) {
    flex: 1;
    overflow: hidden;
    
    .el-tab-pane {
      height: 100%;
      overflow-y: auto;
    }
  }
}

.model-detail {
  .config-section {
    margin-top: 20px;
    
    h4 {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
}
</style>