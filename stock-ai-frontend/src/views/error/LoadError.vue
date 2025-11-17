<template>
  <div class="load-error">
    <div class="error-content">
      <div class="error-icon">
        <el-icon :size="64" color="#f56c6c">
          <Warning />
        </el-icon>
      </div>
      <h3>组件加载失败</h3>
      <p>抱歉，页面组件加载时出现了问题</p>
      <div class="error-actions">
        <el-button type="primary" @click="retry">重试</el-button>
        <el-button @click="goHome">返回首页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Warning } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const retry = () => {
  window.location.reload()
}

const goHome = () => {
  router.push('/admin/dashboard')
}
</script>

<style scoped>
.load-error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 20px;
}

.error-content {
  text-align: center;
  max-width: 400px;
}

.error-icon {
  margin-bottom: 20px;
}

.error-content h3 {
  margin: 20px 0 10px;
  color: #303133;
  font-size: 20px;
}

.error-content p {
  margin-bottom: 30px;
  color: #606266;
  line-height: 1.5;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>