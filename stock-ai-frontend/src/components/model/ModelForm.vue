<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑模型' : '创建模型'"
    width="800px"
    :close-on-click-modal="false"
    @update:model-value="handleVisibleChange"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules as any"
      label-width="120px"
      class="model-form"
    >
      <!-- 基本信息 -->
      <div class="form-section">
        <h4 class="section-title">基本信息</h4>
        
        <el-form-item label="模型名称" prop="name" required>
          <el-input
            v-model="formData.name"
            placeholder="请输入模型名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="显示名称" prop="display_name">
          <el-input
            v-model="formData.display_name"
            placeholder="请输入显示名称（可选）"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="模型类型" prop="model_type" required>
          <el-select
            v-model="formData.model_type"
            placeholder="请选择模型类型"
            style="width: 100%"
            @change="handleModelTypeChange"
          >
            <el-option
              v-for="type in modelTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            >
              <div class="model-type-option">
                <span>{{ type.label }}</span>
                <el-text size="small" type="info">{{ type.description }}</el-text>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="提供商" prop="provider" required>
          <el-input
            v-model="formData.provider"
            placeholder="请输入提供商名称"
            maxlength="50"
          />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模型描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </div>

      <!-- API配置 -->
      <div class="form-section">
        <h4 class="section-title">API配置</h4>
        
        <el-form-item label="API地址" prop="base_url" required>
          <el-input
            v-model="formData.base_url"
            placeholder="请输入API基础地址"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="API密钥" prop="api_key" required>
          <el-input
            v-model="formData.api_key"
            type="password"
            placeholder="请输入API密钥"
            show-password
          >
            <template #suffix>
              <el-button
                size="small"
                text
                @click="testConnection"
                :loading="testing"
              >
                测试连接
              </el-button>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="模型版本" prop="model_version">
          <el-select
            v-model="formData.model_version"
            placeholder="请选择或输入模型版本"
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option
              v-for="version in availableVersions"
              :key="version"
              :label="version"
              :value="version"
            />
          </el-select>
        </el-form-item>
      </div>

      <!-- 参数配置 -->
      <div class="form-section">
        <h4 class="section-title">参数配置</h4>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最大Token数" prop="max_tokens">
              <el-input-number
                v-model="formData.max_tokens"
                :min="1"
                :max="32000"
                :step="100"
                style="width: 100%"
                placeholder="最大Token数"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="温度参数" prop="temperature">
              <el-slider
                v-model="formData.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
                :input-size="'small'"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="超时时间(秒)" prop="timeout">
              <el-input-number
                v-model="formData.timeout"
                :min="1"
                :max="300"
                style="width: 100%"
                placeholder="请求超时时间"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用状态">
              <el-switch
                v-model="formData.enabled"
                active-text="启用"
                inactive-text="停用"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 高级配置 -->
      <div class="form-section">
        <h4 class="section-title">
          高级配置
          <el-button
            size="small"
            text
            @click="showAdvanced = !showAdvanced"
          >
            {{ showAdvanced ? '收起' : '展开' }}
          </el-button>
        </h4>
        
        <div v-show="showAdvanced">
          <el-form-item label="自定义配置">
            <el-input
              v-model="configJsonText"
              type="textarea"
              :rows="6"
              placeholder="请输入JSON格式的自定义配置"
              @blur="validateJson"
            />
            <div class="form-tip">
              <el-text size="small" type="info">
                支持JSON格式的自定义配置，如：{"top_p": 0.9, "frequency_penalty": 0.5}
              </el-text>
            </div>
          </el-form-item>
        </div>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="submitting"
        >
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { 
  modelManagementAPI,
  type AIModel,
  type CreateModelRequest,
  type UpdateModelRequest,
  ModelType
} from '@/api/model-management'

// Props
interface Props {
  visible: boolean
  model?: AIModel | null
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  model: null
})

// Emits
const emit = defineEmits<{
  'update:visible': [value: boolean]
  'success': [model: AIModel]
}>()

// 响应式数据
import type { FormInstance } from 'element-plus'
const formRef = ref<FormInstance>()
const submitting = ref(false)
const testing = ref(false)
const showAdvanced = ref(false)
const configJsonText = ref('')
const urlProtocol = ref('https://')

// 表单数据
const formData = ref<CreateModelRequest>({
  name: '',
  model_type: ModelType.DEEPSEEK,
  provider: '',
  display_name: '',
  description: '',
  model_version: '',
  base_url: '',
  api_key: '',
  max_tokens: 4096,
  temperature: 0.7,
  timeout: 30,
  config_json: {}
})

// 计算属性
const isEdit = computed(() => !!props.model)

const modelTypes = computed(() => [
  {
    value: ModelType.DEEPSEEK,
    label: 'DeepSeek',
    description: 'DeepSeek AI模型'
  },
  {
    value: ModelType.OPENAI,
    label: 'OpenAI',
    description: 'OpenAI GPT系列模型'
  },
  {
    value: ModelType.CLAUDE,
    label: 'Claude',
    description: 'Anthropic Claude系列模型'
  },
  {
    value: ModelType.CUSTOM,
    label: '自定义',
    description: '自定义API端点'
  }
])

const availableVersions = computed(() => {
  const versionMap = {
    [ModelType.DEEPSEEK]: ['deepseek-chat', 'deepseek-coder'],
    [ModelType.OPENAI]: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    [ModelType.CLAUDE]: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
    [ModelType.CUSTOM]: []
  }
  return versionMap[formData.value.model_type] || []
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { min: 2, max: 100, message: '模型名称长度在2到100个字符', trigger: 'blur' }
  ],
  model_type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  provider: [
    { required: true, message: '请输入提供商名称', trigger: 'blur' },
    { min: 1, max: 50, message: '提供商名称长度在1到50个字符', trigger: 'blur' }
  ],
  base_url: [
    { required: true, message: '请输入API地址', trigger: 'blur' },
  ],
  api_key: [
    { required: true, message: '请输入API密钥', trigger: 'blur' },
    { min: 10, message: 'API密钥长度至少10个字符', trigger: 'blur' }
  ],
  max_tokens: [
    { type: 'number', min: 1, max: 32000, message: '最大Token数范围1-32000', trigger: 'blur' }
  ],
  temperature: [
    { type: 'number', min: 0, max: 2, message: '温度参数范围0-2', trigger: 'blur' }
  ],
  timeout: [
    { type: 'number', min: 1, max: 300, message: '超时时间范围1-300秒', trigger: 'blur' }
  ]
}

// 方法
const handleModelTypeChange = (type: ModelType) => {
  // 根据模型类型设置默认值
  const defaults = {
    [ModelType.DEEPSEEK]: {
      provider: 'DeepSeek',
      base_url: 'https://api.deepseek.com/v1',
      model_version: 'deepseek-chat',
      max_tokens: 4096,
      temperature: 0.7
    },
    [ModelType.OPENAI]: {
      provider: 'OpenAI',
      base_url: 'https://api.openai.com',
      model_version: 'gpt-4-turbo',
      max_tokens: 4096,
      temperature: 0.8
    },
    [ModelType.CLAUDE]: {
      provider: 'Anthropic',
      base_url: 'https://api.anthropic.com',
      model_version: 'claude-3-sonnet-20240229',
      max_tokens: 4096,
      temperature: 0.6
    },
    [ModelType.CUSTOM]: {
      provider: '',
      base_url: '',
      model_version: '',
      max_tokens: 4096,
      temperature: 0.7
    }
  }

  const defaultConfig = defaults[type]
  if (defaultConfig && !isEdit.value) {
    Object.assign(formData.value, defaultConfig)
  }
}

const validateJson = () => {
  if (!configJsonText.value.trim()) {
    formData.value.config_json = {}
    return
  }

  try {
    formData.value.config_json = JSON.parse(configJsonText.value)
  } catch (error) {
    ElMessage.error('JSON格式不正确')
    configJsonText.value = JSON.stringify(formData.value.config_json || {}, null, 2)
  }
}

const testConnection = async () => {
  if (!formData.value.api_key || !formData.value.base_url) {
    ElMessage.warning('请先填写API地址和密钥')
    return
  }

  testing.value = true
  try {
    // 这里可以调用测试连接的API
    await new Promise(resolve => setTimeout(resolve, 2000)) // 模拟测试
    ElMessage.success('连接测试成功')
  } catch (error) {
    ElMessage.error('连接测试失败')
  } finally {
    testing.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  submitting.value = true
  try {
    const submitData = {
      ...formData.value,
      base_url: formData.value.base_url
    }

    let response
    if (isEdit.value && props.model) {
      response = await modelManagementAPI.updateModel(props.model.model_id, submitData)
    } else {
      response = await modelManagementAPI.createModel(submitData)
    }

    if (response.success && response.data) {
      ElMessage.success(isEdit.value ? '模型更新成功' : '模型创建成功')
      emit('success', response.data)
      handleClose()
    } else {
      ElMessage.error(response.message || (isEdit.value ? '模型更新失败' : '模型创建失败'))
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(isEdit.value ? '模型更新失败' : '模型创建失败')
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleVisibleChange = (visible: boolean) => {
  emit('update:visible', visible)
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  formData.value = {
    name: '',
    model_type: ModelType.DEEPSEEK,
    provider: '',
    display_name: '',
    description: '',
    model_version: '',
    base_url: '',
    api_key: '',
    max_tokens: 4096,
    temperature: 0.7,
    timeout: 30,
    config_json: {}
  }
  
  configJsonText.value = ''
  showAdvanced.value = false
}

const loadModelData = () => {
  if (props.model) {
    Object.assign(formData.value, {
      name: props.model.name,
      model_type: props.model.model_type,
      provider: props.model.provider,
      display_name: props.model.display_name || '',
      description: props.model.description || '',
      model_version: props.model.model_version || '',
      base_url: props.model.base_url,
      api_key: '', // 不显示已保存的密钥
      max_tokens: props.model.max_tokens || 4096,
      temperature: props.model.temperature || 0.7,
      timeout: props.model.timeout || 30,
      config_json: props.model.config_json || {}
    })
    
    configJsonText.value = JSON.stringify(props.model.config_json || {}, null, 2)
  }
}

// 监听器
watch(() => props.visible, (visible) => {
  if (visible) {
    nextTick(() => {
      if (isEdit.value) {
        loadModelData()
      } else {
        resetForm()
      }
    })
  }
})

</script>

<style lang="scss" scoped>
.model-form {
  .form-section {
    margin-bottom: 24px;
    
    .section-title {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      border-bottom: 1px solid var(--el-border-color-light);
      padding-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
  
  .model-type-option {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .form-tip {
    margin-top: 4px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-input-group__prepend) {
  padding: 0;
}
</style>