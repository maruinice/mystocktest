<template>
  <div class="strategy-selector">
    <el-loading v-if="loading" element-loading-text="加载策略中...">
      <div style="height: 200px;"></div>
    </el-loading>
    
    <div v-else class="strategy-content">
      <!-- 策略分类标签 -->
      <el-tabs v-model="activeTab" class="strategy-tabs">
        <el-tab-pane label="系统策略" name="system">
          <div class="strategy-list">
            <div
              v-for="strategy in allSystemStrategies"
              :key="strategy.id"
              class="strategy-item"
              :class="{ active: modelValue === strategy.id }"
              @click="selectStrategy(strategy.id)"
            >
              <div class="strategy-header">
                <h4 class="strategy-name">{{ strategy.name }}</h4>
                <el-tag :type="getStrategyTypeTag(strategy.type)" size="small">
                  {{ getStrategyTypeText(strategy.type) }}
                </el-tag>
              </div>
              <p class="strategy-description">{{ strategy.description }}</p>
              <div class="strategy-stats">
                <span class="stat-item">
                  <el-icon><User /></el-icon>
                  使用 {{ strategy.usage_count }} 次
                </span>
                <span v-if="strategy.success_rate" class="stat-item">
                  <el-icon><TrendCharts /></el-icon>
                  成功率 {{ strategy.success_rate }}%
                </span>
                <span v-if="strategy.avg_return" class="stat-item">
                  <el-icon><Money /></el-icon>
                  平均收益 {{ strategy.avg_return }}%
                </span>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="自定义策略" name="custom">
          <div class="strategy-list">
            <div
              v-for="strategy in strategies.custom"
              :key="strategy.id"
              class="strategy-item custom-strategy"
              :class="{ active: modelValue === strategy.id }"
              @click="selectStrategy(strategy.id)"
            >
              <div class="strategy-header">
                <h4 class="strategy-name">{{ strategy.name }}</h4>
                <div class="strategy-actions">
                  <el-tag :type="getStrategyTypeTag(strategy.type)" size="small">
                    {{ getStrategyTypeText(strategy.type) }}
                  </el-tag>
                  <el-dropdown @command="handleStrategyAction">
                    <el-button type="text" size="small">
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="{ action: 'edit', id: strategy.id }">
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'copy', id: strategy.id }">
                          复制
                        </el-dropdown-item>
                        <el-dropdown-item 
                          :command="{ action: 'delete', id: strategy.id }"
                          divided
                        >
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
              <p class="strategy-description">{{ strategy.description }}</p>
              <div class="strategy-stats">
                <span class="stat-item">
                  <el-icon><Calendar /></el-icon>
                  创建于 {{ formatDate(strategy.created_at) }}
                </span>
                <span class="stat-item">
                  <el-icon><User /></el-icon>
                  使用 {{ strategy.usage_count }} 次
                </span>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-if="strategies.custom.length === 0" class="empty-state">
              <el-empty description="暂无自定义策略">
                <el-button type="primary" @click="$emit('create-strategy')">
                  创建策略
                </el-button>
              </el-empty>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, TrendCharts, Money, Calendar, MoreFilled } from '@element-plus/icons-vue'
import type { ScreeningStrategy } from '@/types/screening'

// Props
interface Props {
  modelValue?: number
  strategies: {
    system: ScreeningStrategy[]
    fundamental: ScreeningStrategy[]
    technical: ScreeningStrategy[]
    mixed: ScreeningStrategy[]
    custom: ScreeningStrategy[]
  }
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: number | undefined]
  'strategy-selected': [strategyId: number]
  'create-strategy': []
  'edit-strategy': [strategyId: number]
  'delete-strategy': [strategyId: number]
}>()

// 响应式数据
const activeTab = ref('system')

// 计算属性
const allSystemStrategies = computed(() => [
  ...props.strategies.fundamental,
  ...props.strategies.technical,
  ...props.strategies.mixed
])

const allCustomStrategies = computed(() => [
  ...props.strategies.custom
])

// 方法
const selectStrategy = (strategyId: number) => {
  emit('update:modelValue', strategyId)
  emit('strategy-selected', strategyId)
}

const getStrategyTypeTag = (type: string) => {
  const tagMap: Record<string, string> = {
    fundamental: 'success',
    technical: 'warning',
    mixed: 'info',
    custom: 'primary'
  }
  return tagMap[type] || 'info'
}

const getStrategyTypeText = (type: string) => {
  const textMap: Record<string, string> = {
    fundamental: '基本面',
    technical: '技术面',
    mixed: '综合',
    custom: '自定义'
  }
  return textMap[type] || type
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const handleStrategyAction = async (command: { action: string; id: number }) => {
  const { action, id } = command
  
  switch (action) {
    case 'edit':
      emit('edit-strategy', id)
      break
      
    case 'copy':
      // TODO: 实现策略复制功能
      ElMessage.info('策略复制功能开发中')
      break
      
    case 'delete':
      try {
        await ElMessageBox.confirm(
          '确定要删除这个策略吗？删除后无法恢复。',
          '确认删除',
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        emit('delete-strategy', id)
      } catch {
        // 用户取消
      }
      break
  }
}
</script>

<style scoped lang="scss">
.strategy-selector {
  .strategy-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 16px;
    }
    
    :deep(.el-tabs__nav-wrap::after) {
      display: none;
    }
  }
}

.strategy-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.strategy-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  
  &:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  }
  
  &.active {
    border-color: #409eff;
    background: #f0f9ff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
  }
  
  .strategy-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    
    .strategy-name {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
    
    .strategy-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
  .strategy-description {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: #606266;
    line-height: 1.4;
  }
  
  .strategy-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: #909399;
      
      .el-icon {
        font-size: 14px;
      }
    }
  }
}

.custom-strategy {
  border-left: 4px solid #409eff;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

// 滚动条样式
.strategy-list::-webkit-scrollbar {
  width: 6px;
}

.strategy-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.strategy-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
  
  &:hover {
    background: #a8a8a8;
  }
}
</style>