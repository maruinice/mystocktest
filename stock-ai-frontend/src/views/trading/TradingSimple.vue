<template>
  <div class="simple-trading">
    <h1>交易中心 - 简单测试页面</h1>
    <p>当前时间: {{ currentTime }}</p>
    <p>路由路径: {{ $route.path }}</p>
    <p>路由参数: {{ JSON.stringify($route.params) }}</p>
    <el-button type="primary" @click="testClick">测试按钮</el-button>
    <div class="test-content">
      <h2>这是一个简单的测试页面</h2>
      <p>如果你能看到这个内容，说明路由系统工作正常。</p>
      <el-card>
        <h3>测试卡片</h3>
        <p>这是一个Element Plus卡片组件</p>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const currentTime = ref('')

const updateTime = () => {
  currentTime.value = new Date().toLocaleString()
}

const testClick = () => {
  ElMessage.success('测试按钮点击成功！')
}

onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
})
</script>

<style scoped>
.simple-trading {
  padding: 20px;
}

.test-content {
  margin-top: 20px;
}

h1 {
  color: #409eff;
}

h2 {
  color: #67c23a;
}
</style>