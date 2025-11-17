<template>
  <div class="test-container">
    <h1>🎉 Vue3 应用启动成功！</h1>
    <p>如果你能看到这个页面，说明前端应用已经正常运行。</p>
    
    <div class="status-info">
      <div class="status-item">
        <span class="label">Vue版本:</span>
        <span class="value">{{ vueVersion }}</span>
      </div>
      <div class="status-item">
        <span class="label">当前路由:</span>
        <span class="value">{{ $route.path }}</span>
      </div>
      <div class="status-item">
        <span class="label">时间:</span>
        <span class="value">{{ currentTime }}</span>
      </div>
    </div>
    
    <div class="navigation">
      <h2>🧭 页面导航测试</h2>
      <div class="nav-buttons">
        <button @click="$router.push('/login')" class="nav-btn primary">登录页面</button>
        <button @click="$router.push('/dashboard')" class="nav-btn success">仪表盘</button>
        <button @click="$router.push('/trading')" class="nav-btn warning">交易中心</button>
        <button @click="$router.push('/portfolio')" class="nav-btn info">投资组合</button>
        <button @click="$router.push('/strategy')" class="nav-btn danger">策略管理</button>
        <button @click="$router.push('/analysis')" class="nav-btn">数据分析</button>
        <button @click="$router.push('/settings')" class="nav-btn">系统设置</button>
      </div>
    </div>
    
    <div class="element-test">
      <h2>🎨 Element Plus 测试</h2>
      <div class="alert-success">
        ✅ Element Plus 组件库加载成功！
      </div>
      <div class="button-group">
        <button class="btn primary">主要按钮</button>
        <button class="btn success">成功按钮</button>
        <button class="btn warning">警告按钮</button>
        <button class="btn danger">危险按钮</button>
      </div>
    </div>
    
    <div class="api-test">
      <h2>🔗 API 连接测试</h2>
      <button @click="testApi" class="btn primary" :disabled="apiTesting">
        {{ apiTesting ? '测试中...' : '测试后端连接' }}
      </button>
      <div v-if="apiResult" class="api-result" :class="apiResult.success ? 'success' : 'error'">
        {{ apiResult.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { version } from 'vue'

const vueVersion = version
const currentTime = ref('')
const apiTesting = ref(false)
const apiResult = ref<{success: boolean, message: string} | null>(null)

const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

const testApi = async () => {
  apiTesting.value = true
  apiResult.value = null
  
  try {
    const response = await fetch('/api/system/health')
    if (response.ok) {
      apiResult.value = {
        success: true,
        message: '✅ 后端API连接成功！'
      }
    } else {
      apiResult.value = {
        success: false,
        message: `❌ API响应错误: ${response.status}`
      }
    }
  } catch (error) {
    apiResult.value = {
      success: false,
      message: `❌ 无法连接到后端API: ${error}`
    }
  } finally {
    apiTesting.value = false
  }
}

onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
})
</script>

<style lang="scss" scoped>
.test-container {
  padding: 40px;
  max-width: 900px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  
  h1 {
    color: #409eff;
    margin-bottom: 20px;
    text-align: center;
    font-size: 2.5em;
  }
  
  h2 {
    margin: 40px 0 20px 0;
    color: #303133;
    font-size: 1.5em;
  }
  
  p {
    font-size: 18px;
    color: #606266;
    margin-bottom: 30px;
    text-align: center;
  }
}

.status-info {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
  
  .status-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .label {
      font-weight: 600;
      color: #909399;
    }
    
    .value {
      color: #303133;
      font-family: 'Courier New', monospace;
    }
  }
}

.navigation {
  margin-bottom: 40px;
  
  .nav-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .nav-btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    &.primary {
      background: #409eff;
      color: white;
    }
    
    &.success {
      background: #67c23a;
      color: white;
    }
    
    &.warning {
      background: #e6a23c;
      color: white;
    }
    
    &.info {
      background: #909399;
      color: white;
    }
    
    &.danger {
      background: #f56c6c;
      color: white;
    }
    
    &:not(.primary):not(.success):not(.warning):not(.info):not(.danger) {
      background: #dcdfe6;
      color: #606266;
    }
  }
}

.element-test {
  margin-bottom: 40px;
  
  .alert-success {
    background: #f0f9ff;
    border: 1px solid #67c23a;
    color: #67c23a;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 20px;
    font-weight: 500;
  }
  
  .button-group {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
    
    &:hover {
      opacity: 0.8;
    }
    
    &.primary {
      background: #409eff;
      color: white;
    }
    
    &.success {
      background: #67c23a;
      color: white;
    }
    
    &.warning {
      background: #e6a23c;
      color: white;
    }
    
    &.danger {
      background: #f56c6c;
      color: white;
    }
  }
}

.api-test {
  .btn {
    padding: 12px 24px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    background: #409eff;
    color: white;
    transition: all 0.3s ease;
    
    &:hover:not(:disabled) {
      background: #337ecc;
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
  
  .api-result {
    margin-top: 15px;
    padding: 12px;
    border-radius: 6px;
    font-weight: 500;
    
    &.success {
      background: #f0f9ff;
      border: 1px solid #67c23a;
      color: #67c23a;
    }
    
    &.error {
      background: #fef0f0;
      border: 1px solid #f56c6c;
      color: #f56c6c;
    }
  }
}

@media (max-width: 768px) {
  .test-container {
    padding: 20px;
  }
  
  h1 {
    font-size: 2em;
  }
  
  .nav-buttons,
  .button-group {
    flex-direction: column;
  }
  
  .nav-btn,
  .btn {
    width: 100%;
  }
}
</style>