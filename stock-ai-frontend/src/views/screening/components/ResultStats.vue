<template>
  <div class="result-stats">
    <el-loading v-if="loading" element-loading-text="统计中...">
      <div style="height: 200px;"></div>
    </el-loading>
    
    <div v-else-if="resultDetail" class="stats-content">
      <!-- 基础统计 -->
      <div class="basic-stats">
        <div class="stat-row">
          <div class="stat-item">
            <div class="stat-label">筛选股票</div>
            <div class="stat-value primary">{{ resultDetail.filtered_stocks }}</div>
            <div class="stat-unit">只</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">总股票数</div>
            <div class="stat-value">{{ resultDetail.total_stocks }}</div>
            <div class="stat-unit">只</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">筛选率</div>
            <div class="stat-value success">{{ filterRate }}%</div>
            <div class="stat-unit"></div>
          </div>
          <div class="stat-item">
            <div class="stat-label">执行时间</div>
            <div class="stat-value">{{ resultDetail.execution_time }}</div>
            <div class="stat-unit">ms</div>
          </div>
        </div>
      </div>
      
      <!-- 评分分布 -->
      <div v-if="resultDetail.summary?.score_distribution" class="score-distribution">
        <h4 class="section-title">评分分布</h4>
        <div class="score-chart">
          <div class="score-bars">
            <div
              v-for="(count, level) in resultDetail.summary.score_distribution"
              :key="level"
              class="score-bar"
            >
              <div class="bar-container">
                <div
                  class="bar-fill"
                  :class="`bar-${level}`"
                  :style="{ height: getBarHeight(count, resultDetail.filtered_stocks) }"
                ></div>
              </div>
              <div class="bar-label">{{ getScoreLevelText(level) }}</div>
              <div class="bar-count">{{ count }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 行业分布 -->
      <div v-if="resultDetail.summary?.industry_distribution" class="industry-distribution">
        <h4 class="section-title">行业分布 (前5名)</h4>
        <div class="industry-list">
          <div
            v-for="(count, industry) in topIndustries"
            :key="industry"
            class="industry-item"
          >
            <div class="industry-name">{{ industry }}</div>
            <div class="industry-bar">
              <div
                class="industry-fill"
                :style="{ width: getIndustryBarWidth(count, maxIndustryCount) }"
              ></div>
            </div>
            <div class="industry-count">{{ count }}</div>
          </div>
        </div>
      </div>
      
      <!-- 关键指标 -->
      <div class="key-indicators">
        <h4 class="section-title">关键指标平均值</h4>
        <div class="indicator-grid">
          <div v-if="resultDetail.summary?.avg_roe" class="indicator-item">
            <div class="indicator-label">平均ROE</div>
            <div class="indicator-value">{{ formatPercent(resultDetail.summary.avg_roe) }}</div>
          </div>
          <div v-if="resultDetail.summary?.avg_pe" class="indicator-item">
            <div class="indicator-label">平均PE</div>
            <div class="indicator-value">{{ formatNumber(resultDetail.summary.avg_pe) }}</div>
          </div>
          <div v-if="resultDetail.summary?.avg_market_cap" class="indicator-item">
            <div class="indicator-label">平均市值</div>
            <div class="indicator-value">{{ formatMarketCap(resultDetail.summary.avg_market_cap) }}</div>
          </div>
          <div class="indicator-item">
            <div class="indicator-label">平均评分</div>
            <div class="indicator-value">{{ formatNumber(resultDetail.summary?.avg_score || 0) }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-stats">
      <el-empty description="暂无统计数据" :image-size="60">
        <p class="empty-tip">执行选股后将显示详细统计信息</p>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ScreeningDetailResult } from '@/types/screening'

// Props
interface Props {
  resultDetail?: ScreeningDetailResult
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// 计算属性
const filterRate = computed(() => {
  if (!props.resultDetail) return 0
  const rate = (props.resultDetail.filtered_stocks / props.resultDetail.total_stocks) * 100
  return rate.toFixed(2)
})

const topIndustries = computed(() => {
  if (!props.resultDetail?.summary?.industry_distribution) return {}
  
  const industries = props.resultDetail.summary.industry_distribution
  const sorted = Object.entries(industries)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
  
  return Object.fromEntries(sorted)
})

const maxIndustryCount = computed(() => {
  if (!props.resultDetail?.summary?.industry_distribution) return 0
  return Math.max(...Object.values(props.resultDetail.summary.industry_distribution))
})

// 方法
const getBarHeight = (count: number, total: number) => {
  if (total === 0) return '0%'
  const percentage = (count / total) * 100
  return `${Math.max(percentage, 5)}%` // 最小高度5%
}

const getIndustryBarWidth = (count: number, max: number) => {
  if (max === 0) return '0%'
  const percentage = (count / max) * 100
  return `${percentage}%`
}

const getScoreLevelText = (level: string) => {
  const textMap: Record<string, string> = {
    excellent: '优秀',
    good: '良好',
    average: '一般',
    poor: '较差'
  }
  return textMap[level] || level
}

const formatPercent = (value: number) => {
  return `${value.toFixed(2)}%`
}

const formatNumber = (value: number, decimals = 2) => {
  return value.toFixed(decimals)
}

const formatMarketCap = (value: number) => {
  if (value >= 10000) {
    return `${(value / 10000).toFixed(1)}万亿`
  } else if (value >= 100) {
    return `${(value / 100).toFixed(1)}百亿`
  } else {
    return `${value.toFixed(1)}亿`
  }
}
</script>

<style scoped lang="scss">
.result-stats {
  .stats-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .section-title {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: #303133;
    border-bottom: 1px solid #e4e7ed;
    padding-bottom: 8px;
  }
}

.basic-stats {
  .stat-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }
  
  .stat-item {
    text-align: center;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 6px;
    
    .stat-label {
      font-size: 12px;
      color: #909399;
      margin-bottom: 4px;
    }
    
    .stat-value {
      font-size: 20px;
      font-weight: 600;
      color: #303133;
      
      &.primary {
        color: #409eff;
      }
      
      &.success {
        color: #67c23a;
      }
    }
    
    .stat-unit {
      font-size: 12px;
      color: #909399;
      margin-top: 2px;
    }
  }
}

.score-distribution {
  .score-chart {
    .score-bars {
      display: flex;
      align-items: end;
      gap: 12px;
      height: 100px;
      padding: 0 8px;
    }
    
    .score-bar {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      
      .bar-container {
        width: 100%;
        height: 80px;
        display: flex;
        align-items: end;
        justify-content: center;
        
        .bar-fill {
          width: 24px;
          border-radius: 2px 2px 0 0;
          transition: height 0.3s ease;
          
          &.bar-excellent {
            background: linear-gradient(to top, #67c23a, #85ce61);
          }
          
          &.bar-good {
            background: linear-gradient(to top, #409eff, #66b1ff);
          }
          
          &.bar-average {
            background: linear-gradient(to top, #e6a23c, #ebb563);
          }
          
          &.bar-poor {
            background: linear-gradient(to top, #f56c6c, #f78989);
          }
        }
      }
      
      .bar-label {
        font-size: 12px;
        color: #606266;
        margin-top: 4px;
      }
      
      .bar-count {
        font-size: 12px;
        font-weight: 600;
        color: #303133;
        margin-top: 2px;
      }
    }
  }
}

.industry-distribution {
  .industry-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .industry-item {
    display: grid;
    grid-template-columns: 80px 1fr 40px;
    align-items: center;
    gap: 12px;
    
    .industry-name {
      font-size: 12px;
      color: #606266;
      text-align: right;
    }
    
    .industry-bar {
      height: 16px;
      background: #f0f2f5;
      border-radius: 8px;
      overflow: hidden;
      
      .industry-fill {
        height: 100%;
        background: linear-gradient(to right, #409eff, #66b1ff);
        transition: width 0.3s ease;
      }
    }
    
    .industry-count {
      font-size: 12px;
      font-weight: 600;
      color: #303133;
      text-align: center;
    }
  }
}

.key-indicators {
  .indicator-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .indicator-item {
    padding: 12px;
    background: #f8f9fa;
    border-radius: 6px;
    text-align: center;
    
    .indicator-label {
      font-size: 12px;
      color: #909399;
      margin-bottom: 4px;
    }
    
    .indicator-value {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
}

.empty-stats {
  padding: 40px 20px;
  text-align: center;
  
  .empty-tip {
    margin-top: 16px;
    color: #909399;
    font-size: 14px;
  }
}
</style>