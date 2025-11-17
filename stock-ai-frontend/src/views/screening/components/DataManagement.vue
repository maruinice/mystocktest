<template>
  <div class="data-management">
    <div class="sync-actions">
      <el-card class="sync-card">
        <template #header>
          <span>数据同步</span>
        </template>
        <div class="sync-buttons">
          <el-button type="info" @click="syncData('stock-basic')" :loading="loading.stockBasic">
            同步股票基础信息
          </el-button>
          <el-button type="primary" @click="syncData('quotes')" :loading="loading.quotes">
            同步行情数据
          </el-button>
          <el-button type="success" @click="syncData('financial')" :loading="loading.financial">
            同步财务数据
          </el-button>
          <el-button type="warning" @click="syncData('technical')" :loading="loading.technical">
            计算技术指标
          </el-button>
        </div>
        <div class="sync-tips">
          <el-alert
            title="数据同步说明"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>1. 首次使用请先同步股票基础信息</p>
              <p>2. 然后依次同步行情数据和财务数据</p>
              <p>3. 最后计算技术指标完成数据准备</p>
            </template>
          </el-alert>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits<{
  'sync-data': [type: string, params?: any]
}>()

const loading = ref({
  stockBasic: false,
  quotes: false,
  financial: false,
  technical: false
})

const syncData = async (type: string) => {
  const loadingKey = type === 'stock-basic' ? 'stockBasic' : type as keyof typeof loading.value
  loading.value[loadingKey] = true
  try {
    await emit('sync-data', type)
  } finally {
    loading.value[loadingKey] = false
  }
}
</script>

<style scoped lang="scss">
.data-management {
  .sync-card {
    .sync-buttons {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }
    
    .sync-tips {
      :deep(.el-alert__content) {
        p {
          margin: 4px 0;
          font-size: 13px;
        }
      }
    }
  }
}
</style>