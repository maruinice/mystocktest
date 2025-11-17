<template>
  <div class="condition-editor">
    <el-loading v-if="loading" element-loading-text="加载指标中...">
      <div style="height: 200px;"></div>
    </el-loading>
    
    <div v-else class="editor-content">
      <!-- 添加条件按钮 -->
      <div class="add-condition">
        <el-button type="primary" @click="showAddDialog = true" :icon="Plus">
          添加筛选条件
        </el-button>
      </div>
      
      <!-- 条件列表 -->
      <div v-if="modelValue.length > 0" class="condition-list">
        <div
          v-for="(item, index) in modelValue"
          :key="index"
          class="condition-item"
          :class="{ disabled: !item.enabled }"
        >
          <div class="condition-header">
            <el-switch
              v-model="item.enabled"
              @change="updateCondition(index, item)"
            />
            <span class="condition-name">{{ getIndicatorName(item.indicator) }}</span>
            <el-button
              type="text"
              size="small"
              @click="removeCondition(index)"
              :icon="Delete"
            />
          </div>
          
          <div class="condition-content">
            <!-- 范围条件 -->
            <div v-if="item.operator === 'range'" class="range-condition">
              <el-input-number
                v-model="item.value.min"
                :precision="2"
                :min="getIndicatorRange(item.indicator)[0]"
                :max="getIndicatorRange(item.indicator)[1]"
                :step="getStep(item.indicator)"
                placeholder="最小值"
                size="small"
                @change="updateCondition(index, item)"
              />
              <span class="range-separator">至</span>
              <el-input-number
                v-model="item.value.max"
                :precision="2"
                :min="getIndicatorRange(item.indicator)[0]"
                :max="getIndicatorRange(item.indicator)[1]"
                :step="getStep(item.indicator)"
                placeholder="最大值"
                size="small"
                @change="updateCondition(index, item)"
              />
              <span class="unit">{{ getIndicatorUnit(item.indicator) }}</span>
            </div>
            
            <!-- 枚举条件 -->
            <div v-else-if="item.operator === 'in'" class="enum-condition">
              <el-select
                v-model="item.value"
                multiple
                placeholder="请选择"
                size="small"
                @change="updateCondition(index, item)"
              >
                <el-option
                  v-for="option in getEnumOptions(item.indicator)"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </div>
            
            <!-- 布尔条件 -->
            <div v-else-if="item.operator === 'boolean'" class="boolean-condition">
              <el-radio-group
                v-model="item.value"
                size="small"
                @change="updateCondition(index, item)"
              >
                <el-radio :label="true">是</el-radio>
                <el-radio :label="false">否</el-radio>
              </el-radio-group>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-empty description="暂无筛选条件" :image-size="80">
          <el-button type="primary" @click="showAddDialog = true">
            添加第一个条件
          </el-button>
        </el-empty>
      </div>
    </div>
    
    <!-- 添加条件对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加筛选条件"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="add-dialog-content">
        <!-- 指标分类 -->
        <el-tabs v-model="activeIndicatorTab" class="indicator-tabs">
          <el-tab-pane label="基本面指标" name="fundamental">
            <div class="indicator-groups">
              <div
                v-for="(group, groupName) in indicators.fundamental"
                :key="groupName"
                class="indicator-group"
              >
                <h4 class="group-title">{{ getGroupTitle(groupName) }}</h4>
                <div class="indicator-grid">
                  <div
                    v-for="indicator in group"
                    :key="indicator.code"
                    class="indicator-card"
                    @click="selectIndicator(indicator)"
                  >
                    <div class="indicator-name">{{ indicator.name }}</div>
                    <div class="indicator-unit">{{ indicator.unit }}</div>
                    <div class="indicator-range">范围：{{ indicator.range?.[0] }} ~ {{ indicator.range?.[1] }}</div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="技术面指标" name="technical">
            <div class="indicator-groups">
              <div
                v-for="(group, groupName) in indicators.technical"
                :key="groupName"
                class="indicator-group"
              >
                <h4 class="group-title">{{ getGroupTitle(groupName) }}</h4>
                <div class="indicator-grid">
                  <div
                    v-for="indicator in group"
                    :key="indicator.code"
                    class="indicator-card"
                    @click="selectIndicator(indicator)"
                  >
                    <div class="indicator-name">{{ indicator.name }}</div>
                    <div class="indicator-unit">{{ indicator.unit }}</div>
                    <div class="indicator-range">范围：{{ indicator.range?.[0] }} ~ {{ indicator.range?.[1] }}</div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="市场指标" name="market">
            <div class="indicator-groups">
              <div
                v-for="(group, groupName) in indicators.market"
                :key="groupName"
                class="indicator-group"
              >
                <h4 class="group-title">{{ getGroupTitle(groupName) }}</h4>
                <div class="indicator-grid">
                  <div
                    v-for="indicator in group"
                    :key="indicator.code"
                    class="indicator-card"
                    @click="selectIndicator(indicator)"
                  >
                    <div class="indicator-name">{{ indicator.name }}</div>
                    <div class="indicator-unit">{{ indicator.unit }}</div>
                    <div class="indicator-range">范围：{{ indicator.range?.[0] }} ~ {{ indicator.range?.[1] }}</div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import type { ConditionItem, ScreeningIndicator, IndicatorGroup } from '@/types/screening'

// Props
interface Props {
  modelValue: ConditionItem[]
  indicators: {
    fundamental: IndicatorGroup
    technical: IndicatorGroup
    market: IndicatorGroup
  }
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: ConditionItem[]]
  'conditions-changed': [items: ConditionItem[]]
}>()

// 响应式数据
const showAddDialog = ref(false)
const activeIndicatorTab = ref('fundamental')

// 计算属性
const allIndicators = computed(() => {
  const indicators: Record<string, ScreeningIndicator> = {}
  
  Object.values(props.indicators.fundamental).flat().forEach(indicator => {
    indicators[indicator.code] = indicator
  })
  Object.values(props.indicators.technical).flat().forEach(indicator => {
    indicators[indicator.code] = indicator
  })
  Object.values(props.indicators.market).flat().forEach(indicator => {
    indicators[indicator.code] = indicator
  })
  
  return indicators
})

// 方法
const getIndicatorName = (code: string) => {
  return allIndicators.value[code]?.name || code
}

const getIndicatorUnit = (code: string) => {
  return allIndicators.value[code]?.unit || ''
}

const getIndicatorRange = (code: string): [number, number] => {
  return allIndicators.value[code]?.range || [Number.NEGATIVE_INFINITY, Number.POSITIVE_INFINITY]
}

  const getStep = (code: string) => {
    const unit = getIndicatorUnit(code)
    // 百分比和比率用0.1步长，金额/价格用1步长
    if (unit === '%' || unit === '倍') return 0.1
    if (unit === '元') return 0.01
    if (unit === '万元') return 10000
    return 1
  }

const getGroupTitle = (groupName: string) => {
  const titleMap: Record<string, string> = {
    profitability: '盈利能力',
    growth: '成长性',
    valuation: '估值指标',
    financial_health: '财务健康',
    trend: '趋势指标',
    momentum: '动量指标',
    volume: '成交量指标',
    basic: '基础指标'
  }
  return titleMap[groupName] || groupName
}

const getEnumOptions = (code: string) => {
  // 根据指标代码返回枚举选项
  const optionsMap: Record<string, Array<{ label: string; value: string }>> = {
    industry: [
      { label: '银行', value: 'bank' },
      { label: '证券', value: 'securities' },
      { label: '保险', value: 'insurance' },
      // ... 更多行业选项
    ],
    market: [
      { label: '主板', value: 'main' },
      { label: '创业板', value: 'gem' },
      { label: '科创板', value: 'star' }
    ]
  }
  return optionsMap[code] || []
}

const isDuplicate = (code: string) => {
  return props.modelValue.some(item => item.indicator === code)
}

const selectIndicator = (indicator: ScreeningIndicator) => {
  // 防止重复添加同一指标
  if (isDuplicate(indicator.code)) {
    ElMessage.warning(`已添加指标：${indicator.name}`)
    return
  }

  const newItem: ConditionItem = {
    indicator: indicator.code,
    operator: 'range', // 默认为范围条件
    // 默认不限制范围（后端会忽略空范围），但UI限定输入边界
    value: { min: undefined, max: undefined },
    enabled: true
  }
  
  // 根据指标类型设置默认操作符和值
  if (['industry', 'market'].includes(indicator.code)) {
    newItem.operator = 'in'
    newItem.value = []
  } else if (indicator.code.includes('is_')) {
    newItem.operator = 'boolean'
    newItem.value = true
  }
  
  const newItems = [...props.modelValue, newItem]
  emit('update:modelValue', newItems)
  emit('conditions-changed', newItems)
  
  showAddDialog.value = false
}

const clampToRange = (code: string, val: number | undefined) => {
  if (val === undefined || val === null) return val
  const [minR, maxR] = getIndicatorRange(code)
  return Math.min(Math.max(val, minR), maxR)
}

const updateCondition = (index: number, item: ConditionItem) => {
  // 规范化范围值：限定在指标可用范围内，且保证min<=max
  if (item.operator === 'range' && item.value) {
    const code = item.indicator
    let minVal = clampToRange(code, item.value.min)
    let maxVal = clampToRange(code, item.value.max)
    if (minVal !== undefined && maxVal !== undefined && minVal > maxVal) {
      // 自动纠正为交换
      const temp = minVal
      minVal = maxVal
      maxVal = temp
    }
    item.value = { min: minVal, max: maxVal }
  }

  const newItems = [...props.modelValue]
  newItems[index] = { ...item }
  emit('update:modelValue', newItems)
  emit('conditions-changed', newItems)
}

const removeCondition = (index: number) => {
  const newItems = props.modelValue.filter((_, i) => i !== index)
  emit('update:modelValue', newItems)
  emit('conditions-changed', newItems)
}
</script>

<style scoped lang="scss">
.condition-editor {
  .add-condition {
    margin-bottom: 16px;
  }
}

.condition-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.condition-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: white;
  transition: all 0.3s ease;
  
  &.disabled {
    opacity: 0.6;
    background: #f5f7fa;
  }
  
  .condition-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    
    .condition-name {
      flex: 1;
      font-weight: 500;
      color: #303133;
    }
  }
  
  .condition-content {
    .range-condition {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .range-separator {
        color: #909399;
        font-size: 12px;
      }
      
      .unit {
        color: #909399;
        font-size: 12px;
      }
    }
    
    .enum-condition {
      .el-select {
        width: 100%;
      }
    }
  }
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.add-dialog-content {
  .indicator-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 16px;
    }
  }
}

.indicator-groups {
  max-height: 400px;
  overflow-y: auto;
}

.indicator-group {
  margin-bottom: 24px;
  
  .group-title {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: #303133;
    border-bottom: 1px solid #e4e7ed;
    padding-bottom: 8px;
  }
}

.indicator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}

.indicator-card {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #409eff;
    background: #f0f9ff;
  }
  
  .indicator-name {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
    margin-bottom: 4px;
  }
  
  .indicator-unit {
    font-size: 12px;
    color: #909399;
  }

  .indicator-range {
    font-size: 12px;
    color: #a0a3a6;
    margin-top: 2px;
  }
}

// 滚动条样式
.indicator-groups::-webkit-scrollbar {
  width: 6px;
}

.indicator-groups::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.indicator-groups::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
  
  &:hover {
    background: #a8a8a8;
  }
}
</style>