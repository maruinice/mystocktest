<template>
  <div class="ensemble-manager">
    <!-- 组合列表 -->
    <div class="ensemble-list">
      <div class="list-header">
        <h3>模型组合列表</h3>
        <div class="header-actions">
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建组合
          </el-button>
          <el-button @click="refreshEnsembles" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <el-table :data="ensembles" v-loading="loading" stripe>
        <el-table-column prop="ensemble_id" label="组合ID" width="140">
          <template #default="{ row }">
            <el-text class="ensemble-id" truncated>{{ row.ensemble_id }}</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="name" label="组合名称" width="180">
          <template #default="{ row }">
            <div class="ensemble-name-cell">
              <div class="ensemble-name">{{ row.name }}</div>
              <div class="ensemble-display-name" v-if="row.display_name">
                {{ row.display_name }}
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="weight_strategy" label="权重策略" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getWeightStrategyColor(row.weight_strategy)">
              {{ getWeightStrategyText(row.weight_strategy) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="model_count" label="模型数量" width="100">
          <template #default="{ row }">
            <el-text>{{ row.model_count || 0 }}</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="accuracy" label="综合准确率" width="120">
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
        
        <el-table-column prop="enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <el-text size="small">{{ formatDateTime(row.created_at) }}</el-text>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" @click="viewEnsemble(row)">
                详情
              </el-button>
              <el-button size="small" type="primary" @click="editEnsemble(row)">
                编辑
              </el-button>
              <el-button
                size="small"
                :type="row.enabled ? 'warning' : 'success'"
                @click="toggleEnsemble(row)"
                :loading="row._toggling"
              >
                {{ row.enabled ? '停用' : '启用' }}
              </el-button>
              <el-popconfirm
                title="确定要删除这个组合吗？"
                @confirm="deleteEnsemble(row)"
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
    </div>

    <!-- 创建/编辑组合对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingEnsemble ? '编辑组合' : '创建组合'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="ensembleFormRef"
        :model="ensembleForm"
        :rules="ensembleRules"
        label-width="120px"
      >
        <el-form-item label="组合名称" prop="name" required>
          <el-input
            v-model="ensembleForm.name"
            placeholder="请输入组合名称"
            maxlength="100"
          />
        </el-form-item>
        
        <el-form-item label="显示名称" prop="display_name">
          <el-input
            v-model="ensembleForm.display_name"
            placeholder="请输入显示名称（可选）"
            maxlength="100"
          />
        </el-form-item>
        
        <el-form-item label="权重策略" prop="weight_strategy" required>
          <el-select
            v-model="ensembleForm.weight_strategy"
            placeholder="请选择权重策略"
            style="width: 100%"
          >
            <el-option
              v-for="strategy in weightStrategies"
              :key="strategy.value"
              :label="strategy.label"
              :value="strategy.value"
            >
              <div class="strategy-option">
                <span>{{ strategy.label }}</span>
                <el-text size="small" type="info">{{ strategy.description }}</el-text>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="融合策略" prop="fusion_strategy">
          <el-select
            v-model="ensembleForm.fusion_strategy"
            placeholder="请选择融合策略"
            style="width: 100%"
          >
            <el-option
              v-for="strategy in fusionStrategies"
              :key="strategy.value"
              :label="strategy.label"
              :value="strategy.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="置信度阈值" prop="confidence_threshold">
          <el-slider
            v-model="ensembleForm.confidence_threshold"
            :min="0"
            :max="1"
            :step="0.1"
            show-input
            :input-size="'small'"
          />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="ensembleForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入组合描述"
            maxlength="500"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitEnsemble"
          :loading="submitting"
        >
          {{ editingEnsemble ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 组合详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="组合详情"
      width="900px"
    >
      <div v-if="selectedEnsemble" class="ensemble-detail">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h4>基本信息</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="组合ID">
              {{ selectedEnsemble.ensemble_id }}
            </el-descriptions-item>
            <el-descriptions-item label="组合名称">
              {{ selectedEnsemble.name }}
            </el-descriptions-item>
            <el-descriptions-item label="权重策略">
              <el-tag :type="getWeightStrategyColor(selectedEnsemble.weight_strategy)">
                {{ getWeightStrategyText(selectedEnsemble.weight_strategy) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="selectedEnsemble.enabled ? 'success' : 'info'">
                {{ selectedEnsemble.enabled ? '启用' : '停用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDateTime(selectedEnsemble.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatDateTime(selectedEnsemble.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 包含的模型 -->
        <div class="detail-section">
          <div class="section-header">
            <h4>包含的模型</h4>
            <el-button size="small" @click="showAddModelDialog = true">
              <el-icon><Plus /></el-icon>
              添加模型
            </el-button>
          </div>
          
          <el-table :data="ensembleModels" v-loading="loadingModels">
            <el-table-column prop="model_id" label="模型ID" width="140" />
            <el-table-column prop="model_name" label="模型名称" width="180" />
            <el-table-column prop="weight" label="权重" width="120">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.weight"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  :precision="2"
                  size="small"
                  @change="updateModelWeight(row)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="100">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.priority"
                  :min="1"
                  :max="10"
                  size="small"
                  @change="updateModelWeight(row)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="enabled" label="状态" width="100">
              <template #default="{ row }">
                <el-switch
                  v-model="row.enabled"
                  @change="updateModelWeight(row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-popconfirm
                  title="确定要移除这个模型吗？"
                  @confirm="removeModelFromEnsemble(row)"
                >
                  <template #reference>
                    <el-button size="small" type="danger">
                      移除
                    </el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>

    <!-- 添加模型到组合对话框 -->
    <el-dialog
      v-model="showAddModelDialog"
      title="添加模型到组合"
      width="600px"
    >
      <el-form :model="addModelForm" label-width="100px">
        <el-form-item label="选择模型" required>
          <el-select
            v-model="addModelForm.model_id"
            placeholder="请选择要添加的模型"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="model in availableModels"
              :key="model.model_id"
              :label="`${model.name} (${model.model_id})`"
              :value="model.model_id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="权重" required>
          <el-input-number
            v-model="addModelForm.weight"
            :min="0"
            :max="1"
            :step="0.1"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-input-number
            v-model="addModelForm.priority"
            :min="1"
            :max="10"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddModelDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="addModelToEnsemble"
          :loading="addingModel"
        >
          添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted  } from 'vue'
import { formatDateTime } from '../../utils/format'
import { getTagType } from '../../utils/element-plus'
import {
  modelManagementAPI,
  WeightStrategy,
  FusionStrategy
} from '../../api/model-management'

// 响应式数据
const loading = ref(false)
const loadingModels = ref(false)
const submitting = ref(false)
const addingModel = ref(false)

const ensembles = ref<ModelEnsemble[]>([])
const ensembleModels = ref<EnsembleModelMapping[]>([])
const availableModels = ref<AIModel[]>([])

const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showAddModelDialog = ref(false)

const editingEnsemble = ref<ModelEnsemble | null>(null)
const selectedEnsemble = ref<ModelEnsemble | null>(null)

const ensembleFormRef = ref<FormInstance>()

// 表单数据
const ensembleForm = ref<CreateEnsembleRequest>({
  name: '',
  display_name: '',
  description: '',
  weight_strategy: WeightStrategy.EQUAL,
  fusion_strategy: FusionStrategy.WEIGHTED_VOTING,
  confidence_threshold: 0.7
})

const addModelForm = ref({
  model_id: '',
  weight: 0.5,
  priority: 5
})

// 选项数据
const weightStrategies = computed(() => [
  {
    value: WeightStrategy.EQUAL,
    label: '等权重',
    description: '所有模型权重相等'
  },
  {
    value: WeightStrategy.ACCURACY_BASED,
    label: '基于准确率',
    description: '根据模型准确率分配权重'
  },
  {
    value: WeightStrategy.PERFORMANCE_BASED,
    label: '基于性能',
    description: '综合考虑准确率和响应时间'
  },
  {
    value: WeightStrategy.DYNAMIC,
    label: '动态权重',
    description: '根据实时性能动态调整'
  },
  {
    value: WeightStrategy.MANUAL,
    label: '手动设置',
    description: '手动设置每个模型的权重'
  }
])

const fusionStrategies = computed(() => [
  { value: FusionStrategy.WEIGHTED_VOTING, label: '权重投票' },
  { value: FusionStrategy.MAJORITY_VOTING, label: '多数投票' },
  { value: FusionStrategy.CONFIDENCE_BASED, label: '基于置信度' },
  { value: FusionStrategy.BEST_RESPONSE, label: '最佳响应' },
  { value: FusionStrategy.CONSENSUS, label: '共识算法' },
  { value: FusionStrategy.ENSEMBLE_AVERAGE, label: '集成平均' }
])

// 表单验证规则
const ensembleRules: FormRules = {
  name: [
    { required: true, message: '请输入组合名称', trigger: 'blur' },
    { min: 2, max: 100, message: '组合名称长度在2到100个字符', trigger: 'blur' }
  ],
  weight_strategy: [
    { required: true, message: '请选择权重策略', trigger: 'change' }
  ]
}

// 方法
const getWeightStrategyText = (strategy: WeightStrategy) => {
  const strategyMap = {
    [WeightStrategy.EQUAL]: '等权重',
    [WeightStrategy.ACCURACY_BASED]: '基于准确率',
    [WeightStrategy.PERFORMANCE_BASED]: '基于性能',
    [WeightStrategy.DYNAMIC]: '动态权重',
    [WeightStrategy.MANUAL]: '手动设置'
  }
  return strategyMap[strategy] || strategy
}

const getWeightStrategyColor = (strategy: WeightStrategy): TagType => {
  const colorMap = {
    [WeightStrategy.EQUAL]: 'info',
    [WeightStrategy.ACCURACY_BASED]: 'success',
    [WeightStrategy.PERFORMANCE_BASED]: 'primary',
    [WeightStrategy.DYNAMIC]: 'warning',
    [WeightStrategy.MANUAL]: 'danger'
  }
  return getTagType(colorMap[strategy] || 'info')
}

const getAccuracyColor = (accuracy: number) => {
  if (accuracy >= 0.9) return '#67C23A'
  if (accuracy >= 0.8) return '#E6A23C'
  if (accuracy >= 0.7) return '#F56C6C'
  return '#909399'
}

// 加载组合列表
const loadEnsembles = async () => {
  loading.value = true
  try {
    const response = await modelManagementAPI.getEnsembles()
    
    if (response.success && response.data) {
      ensembles.value = response.data.items
    } else {
      ElMessage.error(response.message || '加载组合列表失败')
    }
  } catch (error) {
    console.error('加载组合列表失败:', error)
    ElMessage.error('加载组合列表失败')
  } finally {
    loading.value = false
  }
}

// 加载可用模型
const loadAvailableModels = async () => {
  try {
    const response = await modelManagementAPI.getModels({ per_page: 100 })
    
    if (response.success && response.data) {
      availableModels.value = response.data.items.filter(model => model.enabled)
    }
  } catch (error) {
    console.error('加载可用模型失败:', error)
  }
}

// 刷新组合列表
const refreshEnsembles = () => {
  loadEnsembles()
}

// 查看组合详情
const viewEnsemble = async (ensemble: ModelEnsemble) => {
  selectedEnsemble.value = ensemble
  showDetailDialog.value = true
  
  // 加载组合中的模型
  await loadEnsembleModels(ensemble.ensemble_id)
}

// 编辑组合
const editEnsemble = (ensemble: ModelEnsemble) => {
  editingEnsemble.value = ensemble
  ensembleForm.value = {
    name: ensemble.name,
    display_name: ensemble.display_name || '',
    description: ensemble.description || '',
    weight_strategy: ensemble.weight_strategy,
    fusion_strategy: ensemble.fusion_strategy || FusionStrategy.WEIGHTED_VOTING,
    confidence_threshold: ensemble.confidence_threshold || 0.7
  }
  showCreateDialog.value = true
}

// 切换组合状态
const toggleEnsemble = async (ensemble: ModelEnsemble) => {
  const action = ensemble.enabled ? '停用' : '启用'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}组合 "${ensemble.name}" 吗？`,
      `确认${action}`,
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    ;(ensemble as any)._toggling = true
    
    // 这里应该调用切换状态的API
    // const response = await modelManagementAPI.toggleEnsemble(ensemble.ensemble_id, !ensemble.enabled)
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    ensemble.enabled = !ensemble.enabled
    
    ElMessage.success(`组合${action}成功`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error(`组合${action}失败:`, error)
      ElMessage.error(`组合${action}失败`)
    }
  } finally {
    ;(ensemble as any)._toggling = false
  }
}

// 删除组合
const deleteEnsemble = async (ensemble: ModelEnsemble) => {
  try {
    ;(ensemble as any)._deleting = true
    
    const response = await modelManagementAPI.deleteEnsemble(ensemble.ensemble_id)
    
    if (response.success) {
      ElMessage.success('组合删除成功')
      await loadEnsembles()
    } else {
      ElMessage.error(response.message || '组合删除失败')
    }
  } catch (error) {
    console.error('组合删除失败:', error)
    ElMessage.error('组合删除失败')
  } finally {
    ;(ensemble as any)._deleting = false
  }
}

// 提交组合表单
const submitEnsemble = async () => {
  if (!ensembleFormRef.value) return

  try {
    await ensembleFormRef.value.validate()
  } catch (error) {
    return
  }

  submitting.value = true
  try {
    let response
    if (editingEnsemble.value) {
      response = await modelManagementAPI.updateEnsemble(
        editingEnsemble.value.ensemble_id,
        ensembleForm.value
      )
    } else {
      response = await modelManagementAPI.createEnsemble(ensembleForm.value)
    }

    if (response.success) {
      ElMessage.success(editingEnsemble.value ? '组合更新成功' : '组合创建成功')
      showCreateDialog.value = false
      resetEnsembleForm()
      await loadEnsembles()
    } else {
      ElMessage.error(response.message || (editingEnsemble.value ? '组合更新失败' : '组合创建失败'))
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(editingEnsemble.value ? '组合更新失败' : '组合创建失败')
  } finally {
    submitting.value = false
  }
}

// 重置组合表单
const resetEnsembleForm = () => {
  editingEnsemble.value = null
  ensembleForm.value = {
    name: '',
    display_name: '',
    description: '',
    weight_strategy: WeightStrategy.EQUAL,
    fusion_strategy: FusionStrategy.WEIGHTED_VOTING,
    confidence_threshold: 0.7
  }
}

// 加载组合中的模型
const loadEnsembleModels = async (ensembleId: string) => {
  loadingModels.value = true
  try {
    const response = await modelManagementAPI.getEnsembleModels(ensembleId)
    
    if (response.success && response.data) {
      ensembleModels.value = response.data
    } else {
      ElMessage.error(response.message || '加载组合模型失败')
    }
  } catch (error) {
    console.error('加载组合模型失败:', error)
    ElMessage.error('加载组合模型失败')
  } finally {
    loadingModels.value = false
  }
}

// 更新模型权重
const updateModelWeight = async (modelMapping: EnsembleModelMapping) => {
  if (!selectedEnsemble.value) return

  try {
    const response = await modelManagementAPI.updateEnsembleModelWeight(
      selectedEnsemble.value.ensemble_id,
      modelMapping.model_id,
      modelMapping.weight
    )
    
    if (response.success) {
      ElMessage.success('权重更新成功')
    } else {
      ElMessage.error(response.message || '权重更新失败')
    }
  } catch (error) {
    console.error('权重更新失败:', error)
    ElMessage.error('权重更新失败')
  }
}

// 添加模型到组合
const addModelToEnsemble = async () => {
  if (!selectedEnsemble.value || !addModelForm.value.model_id) {
    ElMessage.warning('请选择要添加的模型')
    return
  }

  addingModel.value = true
  try {
    const response = await modelManagementAPI.addModelToEnsemble(
      selectedEnsemble.value.ensemble_id,
      addModelForm.value
    )
    
    if (response.success) {
      ElMessage.success('模型添加成功')
      showAddModelDialog.value = false
      resetAddModelForm()
      await loadEnsembleModels(selectedEnsemble.value.ensemble_id)
    } else {
      ElMessage.error(response.message || '模型添加失败')
    }
  } catch (error) {
    console.error('模型添加失败:', error)
    ElMessage.error('模型添加失败')
  } finally {
    addingModel.value = false
  }
}

// 从组合中移除模型
const removeModelFromEnsemble = async (modelMapping: EnsembleModelMapping) => {
  if (!selectedEnsemble.value) return

  try {
    const response = await modelManagementAPI.removeModelFromEnsemble(
      selectedEnsemble.value.ensemble_id,
      modelMapping.model_id
    )
    
    if (response.success) {
      ElMessage.success('模型移除成功')
      await loadEnsembleModels(selectedEnsemble.value.ensemble_id)
    } else {
      ElMessage.error(response.message || '模型移除失败')
    }
  } catch (error) {
    console.error('模型移除失败:', error)
    ElMessage.error('模型移除失败')
  }
}

// 重置添加模型表单
const resetAddModelForm = () => {
  addModelForm.value = {
    model_id: '',
    weight: 0.5,
    priority: 5
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  await Promise.all([
    loadEnsembles(),
    loadAvailableModels()
  ])
})
</script>

<style lang="scss" scoped>
.ensemble-manager {
  .ensemble-list {
    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
      
      .header-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
  
  .ensemble-id {
    font-family: 'Courier New', monospace;
    font-size: 12px;
  }
  
  .ensemble-name-cell {
    .ensemble-name {
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
    
    .ensemble-display-name {
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
  
  .strategy-option {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .ensemble-detail {
    .detail-section {
      margin-bottom: 24px;
      
      h4 {
        margin: 0 0 12px 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
      
      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }
    }
  }
}
</style>