<template>
  <div class="strategy-editor">
    <div class="editor-header">
      <h3>编辑策略</h3>
      <div class="header-actions">
        <el-button @click="resetForm" size="small">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
        <el-button @click="validateStrategy" size="small">
          <el-icon><CircleCheck /></el-icon>
          验证
        </el-button>
      </div>
    </div>
    
    <div class="editor-content">
      <el-form :model="editForm" :rules="formRules" ref="formRef" label-width="120px">
        <!-- 基本信息 -->
        <div class="form-section">
          <h4>基本信息</h4>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="策略名称" prop="name">
                <el-input 
                  v-model="editForm.name" 
                  placeholder="请输入策略名称"
                  maxlength="50"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="策略作者" prop="author">
                <el-input 
                  v-model="editForm.author" 
                  placeholder="请输入作者名称"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="策略描述" prop="description">
            <el-input
              v-model="editForm.description"
              type="textarea"
              :rows="3"
              placeholder="请详细描述策略的逻辑和特点"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="策略类型" prop="category">
                <el-select v-model="editForm.category" style="width: 100%">
                  <el-option 
                    v-for="type in strategyTypes" 
                    :key="type.value" 
                    :label="type.label" 
                    :value="type.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="风险等级" prop="risk_level">
                <el-select v-model="editForm.risk_level" style="width: 100%">
                  <el-option 
                    v-for="risk in riskLevels" 
                    :key="risk.value" 
                    :label="risk.label" 
                    :value="risk.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="最小资金">
                <el-input-number
                  v-model="editForm.min_capital"
                  :min="10000"
                  :max="10000000"
                  :step="10000"
                  style="width: 100%"
                  controls-position="right"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 策略参数 -->
        <div class="form-section">
          <div class="section-header">
            <h4>策略参数</h4>
            <el-button @click="addParameter" size="small" type="primary" text>
              <el-icon><Plus /></el-icon>
              添加参数
            </el-button>
          </div>
          
          <div class="parameters-list">
            <div 
              v-for="(param, index) in editForm.parameters" 
              :key="index"
              class="parameter-item"
            >
              <el-row :gutter="12" align="middle">
                <el-col :span="6">
                  <el-input 
                    v-model="param.key" 
                    placeholder="参数名称"
                    size="small"
                  />
                </el-col>
                <el-col :span="6">
                  <el-input 
                    v-model="param.value" 
                    placeholder="参数值"
                    size="small"
                  />
                </el-col>
                <el-col :span="4">
                  <el-select v-model="param.type" size="small">
                    <el-option label="数字" value="number" />
                    <el-option label="文本" value="string" />
                    <el-option label="布尔" value="boolean" />
                  </el-select>
                </el-col>
                <el-col :span="6">
                  <el-input 
                    v-model="param.description" 
                    placeholder="参数描述"
                    size="small"
                  />
                </el-col>
                <el-col :span="2">
                  <el-button 
                    @click="removeParameter(index)" 
                    size="small" 
                    type="danger" 
                    text
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </div>
        </div>

        <!-- 风险控制 -->
        <div class="form-section">
          <h4>风险控制</h4>
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="止损比例(%)">
                <el-input-number
                  v-model="editForm.risk_controls.stop_loss"
                  :min="0"
                  :max="50"
                  :step="0.1"
                  :precision="1"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="止盈比例(%)">
                <el-input-number
                  v-model="editForm.risk_controls.take_profit"
                  :min="0"
                  :max="200"
                  :step="0.1"
                  :precision="1"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="单笔仓位(%)">
                <el-input-number
                  v-model="editForm.risk_controls.position_size"
                  :min="1"
                  :max="100"
                  :step="1"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="最大持仓数">
                <el-input-number
                  v-model="editForm.risk_controls.max_positions"
                  :min="1"
                  :max="50"
                  :step="1"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 策略代码 -->
        <div class="form-section">
          <div class="section-header">
            <h4>策略代码</h4>
            <div class="code-actions">
              <el-button @click="formatCode" size="small">
                <el-icon><Magic /></el-icon>
                格式化
              </el-button>
              <el-button @click="validateCode" size="small">
                <el-icon><CircleCheck /></el-icon>
                验证代码
              </el-button>
            </div>
          </div>
          
          <div class="code-editor">
            <el-input
              v-model="editForm.code"
              type="textarea"
              :rows="15"
              placeholder="请输入策略代码..."
              class="code-textarea"
            />
          </div>
          
          <!-- 验证结果 -->
          <div v-if="validationResult" class="validation-result">
            <div v-if="validationResult.valid" class="validation-success">
              <el-icon><CircleCheck /></el-icon>
              代码验证通过
            </div>
            <div v-else class="validation-error">
              <el-icon><CircleClose /></el-icon>
              发现错误:
              <ul>
                <li v-for="error in validationResult.errors" :key="error">{{ error }}</li>
              </ul>
            </div>
          </div>
        </div>
      </el-form>
    </div>
    
    <div class="editor-footer">
      <div class="footer-left">
        <el-button @click="$emit('cancel')">取消</el-button>
      </div>
      <div class="footer-right">
        <el-button @click="previewStrategy">
          <el-icon><View /></el-icon>
          预览
        </el-button>
        <el-button @click="saveStrategy" type="primary" :loading="saving">
          <el-icon><Check /></el-icon>
          保存策略
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { Strategy } from '@/types/strategy'

// Props
interface Props {
  strategy: Strategy
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  save: [strategy: Strategy]
  cancel: []
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const saving = ref(false)
const validationResult = ref<{ valid: boolean; errors: string[] } | null>(null)

// 编辑表单
const editForm = reactive({
  name: '',
  author: '',
  description: '',
  category: 'trend_following',
  risk_level: 'medium',
  min_capital: 100000,
  parameters: [] as Array<{ key: string; value: string; type: string; description: string }>,
  risk_controls: {
    stop_loss: 5.0,
    take_profit: 15.0,
    position_size: 10,
    max_positions: 5
  },
  code: ''
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 50, message: '策略名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入策略描述', trigger: 'blur' },
    { min: 10, max: 500, message: '策略描述长度在 10 到 500 个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  risk_level: [
    { required: true, message: '请选择风险等级', trigger: 'change' }
  ]
}

// 策略类型选项
const strategyTypes = [
  { value: 'trend_following', label: '趋势跟踪' },
  { value: 'mean_reversion', label: '均值回归' },
  { value: 'momentum', label: '动量策略' },
  { value: 'arbitrage', label: '套利策略' },
  { value: 'multi_factor', label: '多因子' },
  { value: 'volatility', label: '波动率策略' },
  { value: 'custom', label: '自定义' }
]

// 风险等级选项
const riskLevels = [
  { value: 'low', label: '低风险' },
  { value: 'medium', label: '中风险' },
  { value: 'high', label: '高风险' }
]

// 方法
const initForm = () => {
  if (props.strategy) {
    editForm.name = props.strategy.name
    editForm.author = props.strategy.author || ''
    editForm.description = props.strategy.description
    editForm.category = props.strategy.category
    editForm.risk_level = props.strategy.risk_level
    editForm.min_capital = props.strategy.min_capital || 100000
    editForm.code = props.strategy.code || ''
    
    // 初始化参数
    if (props.strategy.parameters) {
      editForm.parameters = Object.entries(props.strategy.parameters).map(([key, value]) => ({
        key,
        value: String(value),
        type: typeof value,
        description: ''
      }))
    }
    
    // 初始化风险控制
    if (props.strategy.risk_controls) {
      Object.assign(editForm.risk_controls, props.strategy.risk_controls)
    }
  }
}

const resetForm = () => {
  initForm()
  validationResult.value = null
  ElMessage.success('表单已重置')
}

const addParameter = () => {
  editForm.parameters.push({
    key: '',
    value: '',
    type: 'string',
    description: ''
  })
}

const removeParameter = (index: number) => {
  editForm.parameters.splice(index, 1)
}

const formatCode = () => {
  if (!editForm.code.trim()) {
    ElMessage.warning('请先输入代码')
    return
  }
  
  // 简单的代码格式化
  const lines = editForm.code.split('\n')
  const formatted = lines.map(line => line.trim()).join('\n')
  editForm.code = formatted
  ElMessage.success('代码格式化完成')
}

const validateCode = () => {
  const code = editForm.code.trim()
  const errors: string[] = []
  
  if (!code) {
    errors.push('代码不能为空')
  } else {
    // 基本语法检查
    if (!code.includes('def initialize(context):')) {
      errors.push('缺少 initialize 函数')
    }
    
    if (!code.includes('def handle_data(context, data):')) {
      errors.push('缺少 handle_data 函数')
    }
  }
  
  validationResult.value = {
    valid: errors.length === 0,
    errors: errors
  }
  
  if (validationResult.value.valid) {
    ElMessage.success('代码验证通过')
  } else {
    ElMessage.error('代码验证失败')
  }
}

const validateStrategy = async () => {
  if (!formRef.value) return false
  
  try {
    await formRef.value.validate()
    validateCode()
    return validationResult.value?.valid || false
  } catch {
    ElMessage.error('请完善策略配置')
    return false
  }
}

const previewStrategy = () => {
  ElMessage.info('预览功能开发中')
}

const saveStrategy = async () => {
  if (!(await validateStrategy())) {
    return
  }
  
  saving.value = true
  
  try {
    // 构建参数对象
    const parameters: Record<string, any> = {}
    editForm.parameters.forEach(param => {
      if (param.key && param.value) {
        let value: any = param.value
        if (param.type === 'number') {
          value = Number(param.value)
        } else if (param.type === 'boolean') {
          value = param.value === 'true'
        }
        parameters[param.key] = value
      }
    })
    
    const updatedStrategy: Strategy = {
      ...props.strategy,
      name: editForm.name,
      display_name: editForm.name,
      description: editForm.description,
      category: editForm.category as any,
      risk_level: editForm.risk_level as any,
      author: editForm.author,
      min_capital: editForm.min_capital,
      parameters: parameters,
      risk_controls: editForm.risk_controls,
      code: editForm.code,
      updated_at: new Date().toISOString()
    }
    
    emit('save', updatedStrategy)
    
  } catch (error) {
    ElMessage.error('策略保存失败')
  } finally {
    saving.value = false
  }
}

// 监听策略变化
watch(() => props.strategy, () => {
  initForm()
}, { immediate: true })

// 生命周期
onMounted(() => {
  initForm()
})
</script>

<style lang="scss" scoped>
.strategy-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 20px;
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
  }
  
  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.editor-content {
  flex: 1;
  overflow-y: auto;
  
  .form-section {
    margin-bottom: 24px;
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
    
    h4 {
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 16px 0;
    }
    
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      h4 {
        margin: 0;
      }
      
      .code-actions {
        display: flex;
        gap: 8px;
      }
    }
    
    .parameters-list {
      .parameter-item {
        margin-bottom: 12px;
        padding: 12px;
        background: white;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
      }
    }
    
    .code-editor {
      .code-textarea {
        :deep(.el-textarea__inner) {
          font-family: 'Courier New', monospace;
          font-size: 14px;
          line-height: 1.6;
          background: #1e293b;
          color: #e2e8f0;
          border: 1px solid #404040;
          
          &:focus {
            border-color: #409eff;
          }
        }
      }
    }
    
    .validation-result {
      margin-top: 12px;
      padding: 12px;
      border-radius: 6px;
      
      .validation-success {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #059669;
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
      }
      
      .validation-error {
        color: #dc2626;
        background: #fef2f2;
        border: 1px solid #fecaca;
        
        ul {
          margin: 8px 0 0 0;
          padding-left: 20px;
          
          li {
            margin-bottom: 4px;
          }
        }
      }
    }
  }
}

.editor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
  
  .footer-left,
  .footer-right {
    display: flex;
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .strategy-editor {
    .editor-header {
      flex-direction: column;
      gap: 12px;
    }
    
    .editor-footer {
      flex-direction: column;
      gap: 12px;
      
      .footer-left,
      .footer-right {
        width: 100%;
        justify-content: center;
      }
    }
  }
}
</style>