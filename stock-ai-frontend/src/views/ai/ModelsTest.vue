<template>
  <div class="models-test">
    <h1>模型管理测试页面</h1>
    <p>如果您能看到这个页面，说明路由工作正常。</p>
    <el-button type="primary" @click="goBack">返回</el-button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  router.push('/admin/dashboard')
}
</script>

<style scoped>
.models-test {
  padding: 20px;
  text-align: center;
}
</style>