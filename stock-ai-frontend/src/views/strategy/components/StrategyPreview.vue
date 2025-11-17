<template>
  <div class="strategy-preview">
    <div class="preview-header">
      <h3>策略预览</h3>
      <el-button @click="$emit('close')" size="small" text>
        <el-icon><Close /></el-icon>
      </el-button>
    </div>
    
    <div class="preview-content">
      <!-- 策略基本信息 -->
      <div class="info-section">
        <h4>基本信息</h4>
        <div class="info-grid">
          <div class="info-item">
            <label>策略名称:</label>
            <span>{{ strategy.name }}</span>
          </div>
          <div class="info-item">
            <label>策略类型:</label>
            <el-tag :type="getStrategyTypeColor(strategy.category)" size="small">
              {{ getStrategyTypeText(strategy.category) }}
            </el-tag>
          </div>
          <div class="info-item">
            <label>风险等级:</label>
            <el-tag :type="getRiskLevelColor(strategy.risk_level)" size="small">
              {{ getRiskLevelText(strategy.risk_level) }}
            </el-tag>
          </div>
          <div class="info-item">
            <label>创建时间:</label>
            <span>{{ formatDateTime(strategy.created_at) }}</span>
          </div>
        </div>
        
        <div class="description">
          <label>策略描述:</label>
          <p>{{ strategy.description }}</p>
        </div>
      </div>

      <!-- 策略参数 -->
      <div class="info-section" v-if="strategy.parameters && Object.keys(strategy.parameters).length > 0">
        <h4>策略参数</h4>
        <div class="params-table">
          <el-table :data="parametersList" size="small">
            <el-table-column prop="key" label="参数名" width="150" />
            <el-table-column prop="value" label="参数值" />
            <el-table-column prop="type" label="类型" width="100" />
          </el-table>
        </div>
      </div>

      <!-- 策略代码 -->
      <div class="info-section" v-if="strategy.code">
        <h4>策略代码</h4>
        <div class="code-preview">
          <pre><code>{{ strategy.code }}</code></pre>
        </div>
      </div>

      <!-- 风险控制 -->
      <div class="info-section" v-if="strategy.risk_controls">
        <h4>风险控制</h4>
        <div class="risk-grid">
          <div class="risk-item" v-if="strategy.risk_controls.stop_loss">
            <label>止损比例:</label>
            <span>{{ strategy.risk_controls.stop_loss }}%</span>
          </div>
          <div class="risk-item" v-if="strategy.risk_controls.take_profit">
            <label>止盈比例:</label>
            <span>{{ strategy.risk_controls.take_profit }}%</span>
          </div>
          <div class="risk-item" v-if="strategy.risk_controls.position_size">
            <label>仓位大小:</label>
            <span>{{ strategy.risk_controls.position_size }}%</span>
          </div>
          <div class="risk-item" v-if="strategy.risk_controls.max_positions">
            <label>最大持仓:</label>
            <span>{{ strategy.risk_controls.max_positions }}只</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatDateTime } from '@/utils/format'
import type { Strategy } from '@/types/strategy'

// Props
interface Props {
  strategy: Strategy
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
}>()

// 计算属性
const parametersList = computed(() => {
  if (!props.strategy.parameters) return []
  
  return Object.entries(props.strategy.parameters).map(([key, value]) => ({
    key,
    value: String(value),
    type: typeof value
  }))
})

// 工具方法
const getStrategyTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    trend_following: '趋势跟踪',
    mean_reversion: '均值回归',
    momentum: '动量策略',
    arbitrage: '套利策略',
    multi_factor: '多因子',
    volatility: '波动率策略',
    custom: '自定义'
  }
  return typeMap[type] || type
}

const getStrategyTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    trend_following: 'primary',
    mean_reversion: 'success',
    momentum: 'warning',
    arbitrage: 'info',
    multi_factor: 'danger',
    volatility: '',
    custom: ''
  }
  return colorMap[type] || 'info'
}

const getRiskLevelText = (level: string) => {
  const levelMap: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险'
  }
  return levelMap[level] || level
}

const getRiskLevelColor = (level: string) => {
  const colorMap: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return colorMap[level] || 'info'
}
</script>

<style lang="scss" scoped>
.strategy-preview {
  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 16px;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 20px;
    
    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
    }
  }
  
  .preview-content {
    max-height: 600px;
    overflow-y: auto;
    
    .info-section {
      margin-bottom: 24px;
      
      h4 {
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
        margin: 0 0 12px 0;
      }
      
      .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-bottom: 16px;
        
        .info-item {
          display: flex;
          align-items: center;
          gap: 8px;
          
          label {
            font-size: 14px;
            color: #6b7280;
            min-width: 80px;
          }
          
          span {
            font-size: 14px;
            color: #1f2937;
          }
        }
      }
      
      .description {
        label {
          font-size: 14px;
          color: #6b7280;
          display: block;
          margin-bottom: 8px;
        }
        
        p {
          font-size: 14px;
          color: #1f2937;
          line-height: 1.5;
          margin: 0;
          padding: 12px;
          background: #f9fafb;
          border-radius: 6px;
        }
      }
      
      .params-table {
        .el-table {
          border: 1px solid #e5e7eb;
          border-radius: 6px;
        }
      }
      
      .code-preview {
        background: #1e293b;
        border-radius: 8px;
        overflow: hidden;
        
        pre {
          margin: 0;
          padding: 16px;
          overflow: auto;
          max-height: 300px;
          
          code {
            color: #e2e8f0;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.5;
          }
        }
      }
      
      .risk-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        
        .risk-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 12px;
          background: #f9fafb;
          border-radius: 6px;
          
          label {
            font-size: 14px;
            color: #6b7280;
          }
          
          span {
            font-size: 14px;
            color: #1f2937;
            font-weight: 500;
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .strategy-preview {
    .preview-content {
      .info-section {
        .info-grid,
        .risk-grid {
          grid-template-columns: 1fr;
        }
      }
    }
  }
}
</style>