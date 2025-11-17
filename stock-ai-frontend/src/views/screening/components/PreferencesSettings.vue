<template>
  <div class="preferences-settings">
    <el-form :model="form" label-width="120px">
      <el-form-item label="风险偏好">
        <el-radio-group v-model="form.risk_level">
          <el-radio label="conservative">保守型</el-radio>
          <el-radio label="moderate">稳健型</el-radio>
          <el-radio label="aggressive">激进型</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="最大仓位">
        <el-input-number
          v-model="form.max_position_size"
          :min="1"
          :max="100"
          :precision="1"
        />
        <span style="margin-left: 8px;">%</span>
      </el-form-item>
      
      <el-form-item label="止损比例">
        <el-input-number
          v-model="form.stop_loss_rate"
          :min="1"
          :max="50"
          :precision="1"
        />
        <span style="margin-left: 8px;">%</span>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="saveSettings" :loading="loading">
          保存设置
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { UserPreferences } from '@/types/screening'

interface Props {
  preferences: UserPreferences
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  'save-preferences': [preferences: UserPreferences]
}>()

const form = ref<UserPreferences>({ ...props.preferences })

watch(() => props.preferences, (newPrefs) => {
  form.value = { ...newPrefs }
}, { deep: true })

const saveSettings = () => {
  emit('save-preferences', form.value)
}
</script>

<style scoped lang="scss">
.preferences-settings {
  max-width: 500px;
}
</style>