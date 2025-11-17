<template>
  <el-dialog
    v-model="visible"
    title="创建自定义策略"
    width="800px"
    :close-on-click-modal="false"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="策略名称" prop="strategy_name">
        <el-input v-model="form.strategy_name" placeholder="请输入策略名称" />
      </el-form-item>
      
      <el-form-item label="策略类型" prop="strategy_type">
        <el-select v-model="form.strategy_type" placeholder="请选择策略类型">
          <el-option label="基本面策略" value="fundamental" />
          <el-option label="技术面策略" value="technical" />
          <el-option label="综合策略" value="mixed" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="策略描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入策略描述"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        创建策略
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

interface Props {
  modelValue: boolean
  indicators: any
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'strategy-created': []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = ref({
  strategy_name: '',
  strategy_type: '',
  description: '',
  conditions: {},
  config: {}
})

const rules: FormRules = {
  strategy_name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' }
  ],
  strategy_type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    // TODO: 调用创建策略API
    await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟API调用
    
    ElMessage.success('策略创建成功')
    emit('strategy-created')
    visible.value = false
    
    // 重置表单
    form.value = {
      strategy_name: '',
      strategy_type: '',
      description: '',
      conditions: {},
      config: {}
    }
  } catch (error) {
    console.error('创建策略失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>