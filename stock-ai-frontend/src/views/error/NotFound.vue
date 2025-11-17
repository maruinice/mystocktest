<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <div class="error-message">页面未找到</div>
      <div class="error-description">
        抱歉，您访问的页面不存在或已被移除
      </div>
      <div class="error-actions">
        <el-button type="primary" @click="goHome">
          返回首页
        </el-button>
        <el-button @click="goBack">
          返回上页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/admin/dashboard')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style lang="scss" scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-bg-color-page);
}

.not-found-content {
  text-align: center;
  padding: 40px;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  color: var(--el-color-primary);
  line-height: 1;
  margin-bottom: 20px;
}

.error-message {
  font-size: 32px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
}

.error-description {
  font-size: 16px;
  color: var(--el-text-color-regular);
  margin-bottom: 40px;
}

.error-actions {
  .el-button {
    margin: 0 8px;
  }
}

@media (max-width: 768px) {
  .error-code {
    font-size: 80px;
  }
  
  .error-message {
    font-size: 24px;
  }
  
  .error-description {
    font-size: 14px;
  }
}
</style>