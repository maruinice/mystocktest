<template>
  <div class="models-container">
    <div class="page-header">
      <h2>模型管理中心</h2>
      <p>管理AI模型和多模型组合策略</p>
    </div>

    <!-- 简化的内容 -->
    <el-card>
      <h3>模型管理功能</h3>
      <p>这里将显示模型管理的各种功能...</p>
      
      <el-button type="primary" @click="testFunction">测试按钮</el-button>
      
      <div v-if="showMessage" style="margin-top: 20px;">
        <el-alert title="测试成功" type="success" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ElMessage from 'element-plus'

// 响应式数据
const showMessage = ref(false)

// 方法
const testFunction = () => {
  showMessage.value = true
  ElMessage.success('功能测试成功！')
  
  setTimeout(() => {
    showMessage.value = false
  }, 3000)
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
</style>