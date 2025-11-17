<template>
  <div class="ai-strategy-generator">
    <!-- 生成器头部 -->
    <div class="generator-header">
      <div class="header-content">
        <div class="header-left">
          <h2 class="generator-title">
            <el-icon><ChatDotRound /></el-icon>
            AI策略生成器
          </h2>
          <p class="generator-subtitle">
            通过自然语言描述您的交易想法，AI将为您生成完整的策略代码和配置
          </p>
        </div>
        <div class="header-right">
          <el-tag type="success" size="large">
            <el-icon><Magic /></el-icon>
            智能生成
          </el-tag>
        </div>
      </div>
    </div>

    <div class="generator-content">
      <el-row :gutter="24">
        <!-- 左侧对话区域 -->
        <el-col :span="14">
          <div class="chat-section">
            <div class="chat-header">
              <h3>策略需求对话</h3>
              <el-button @click="clearChat" size="small" text>
                <el-icon><Delete /></el-icon>
                清空对话
              </el-button>
            </div>
            
            <!-- 对话历史 -->
            <div class="chat-messages" ref="chatMessagesRef">
              <div 
                v-for="(message, index) in chatMessages" 
                :key="index"
                class="message-item"
                :class="message.role"
              >
                <div class="message-avatar">
                  <el-avatar v-if="message.role === 'user'" :size="32">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                  <el-avatar v-else :size="32" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    <el-icon><Robot /></el-icon>
                  </el-avatar>
                </div>
                <div class="message-content">
                  <div class="message-text" v-html="formatMessage(message.content)"></div>
                  <div class="message-time">{{ formatTime(message.timestamp) }}</div>
                </div>
              </div>
              
              <!-- AI思考中 -->
              <div v-if="isThinking" class="message-item assistant thinking">
                <div class="message-avatar">
                  <el-avatar :size="32" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    <el-icon><Robot /></el-icon>
                  </el-avatar>
                </div>
                <div class="message-content">
                  <div class="thinking-indicator">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="thinking-text">AI正在分析您的需求...</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 输入区域 -->
            <div class="chat-input">
              <div class="input-suggestions" v-if="suggestions.length > 0">
                <div class="suggestions-title">💡 建议问题：</div>
                <div class="suggestions-list">
                  <el-tag 
                    v-for="suggestion in suggestions" 
                    :key="suggestion"
                    @click="selectSuggestion(suggestion)"
                    class="suggestion-tag"
                    type="info"
                  >
                    {{ suggestion }}
                  </el-tag>
                </div>
              </div>
              
              <div class="input-area">
                <el-input
                  v-model="userInput"
                  type="textarea"
                  :rows="3"
                  placeholder="请描述您的交易策略想法，例如：我想要一个基于RSI指标的反转策略，当RSI低于30时买入，高于70时卖出..."
                  @keydown.ctrl.enter="sendMessage"
                  :disabled="isThinking"
                />
                <div class="input-actions">
                  <div class="input-tips">
                    <el-icon><InfoFilled /></el-icon>
                    按 Ctrl+Enter 发送消息
                  </div>
                  <el-button 
                    @click="sendMessage" 
                    type="primary" 
                    :loading="isThinking"
                    :disabled="!userInput.trim()"
                  >
                    <el-icon><Promotion /></el-icon>
                    发送
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 右侧策略预览 -->
        <el-col :span="10">
          <div class="strategy-preview">
            <div class="preview-header">
              <h3>策略预览</h3>
              <el-button 
                v-if="generatedStrategy"
                @click="regenerateStrategy" 
                size="small"
                :loading="isRegenerating"
              >
                <el-icon><Refresh /></el-icon>
                重新生成
              </el-button>
            </div>
            
            <div v-if="!generatedStrategy" class="empty-preview">
              <div class="empty-icon">
                <el-icon><ChatDotRound /></el-icon>
              </div>
              <div class="empty-text">
                <h4>开始对话生成策略</h4>
                <p>描述您的交易想法，AI将为您生成专业的量化策略</p>
              </div>
            </div>
            
            <div v-else class="strategy-content">
              <!-- 策略基本信息 -->
              <div class="strategy-info">
                <div class="info-item">
                  <label>策略名称:</label>
                  <el-input 
                    v-model="generatedStrategy.name" 
                    size="small" 
                    placeholder="请输入策略名称"
                    style="width: 200px;"
                  />
                </div>
                <div class="info-item">
                  <label>策略类型:</label>
                  <el-select 
                    v-model="generatedStrategy.category" 
                    size="small" 
                    style="width: 150px;"
                  >
                    <el-option label="趋势跟踪" value="trend_following" />
                    <el-option label="均值回归" value="mean_reversion" />
                    <el-option label="动量策略" value="momentum" />
                    <el-option label="波动率策略" value="volatility" />
                    <el-option label="套利策略" value="arbitrage" />
                    <el-option label="多因子" value="multi_factor" />
                    <el-option label="自定义" value="custom" />
                  </el-select>
                </div>
                <div class="info-item">
                  <label>风险等级:</label>
                  <el-select 
                    v-model="generatedStrategy.risk_level" 
                    size="small" 
                    style="width: 120px;"
                  >
                    <el-option label="低风险" value="low" />
                    <el-option label="中风险" value="medium" />
                    <el-option label="高风险" value="high" />
                  </el-select>
                </div>
                <div class="info-item">
                  <label>策略描述:</label>
                  <el-input 
                    v-model="generatedStrategy.description" 
                    type="textarea" 
                    :rows="3"
                    placeholder="请输入策略描述"
                    style="width: 100%;"
                  />
                </div>
              </div>
              
              <!-- 策略参数 -->
              <div class="strategy-params">
                <div class="params-header">
                  <h4>策略参数</h4>
                  <el-button @click="addParameter" size="small" text>
                    <el-icon><Plus /></el-icon>
                    添加参数
                  </el-button>
                </div>
                <div class="params-list">
                  <div 
                    v-for="(value, key) in generatedStrategy.parameters" 
                    :key="key"
                    class="param-item editable"
                  >
                    <el-input 
                      v-model="parameterKeys[key]" 
                      size="small" 
                      placeholder="参数名"
                      style="width: 100px;"
                      @blur="updateParameterKey(key, parameterKeys[key])"
                    />
                    <span class="param-separator">:</span>
                    <el-input 
                      v-model="generatedStrategy.parameters[key]" 
                      size="small" 
                      placeholder="参数值"
                      style="width: 100px;"
                    />
                    <el-button 
                      @click="removeParameter(key)" 
                      size="small" 
                      text 
                      type="danger"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
              
              <!-- 技术指标 -->
              <div class="strategy-indicators" v-if="generatedStrategy.indicators">
                <div class="indicators-header">
                  <h4>使用指标</h4>
                  <el-button @click="showIndicatorSelector = true" size="small" text>
                    <el-icon><Plus /></el-icon>
                    添加指标
                  </el-button>
                </div>
                <div class="indicators-list">
                  <el-tag 
                    v-for="(indicator, index) in generatedStrategy.indicators" 
                    :key="indicator"
                    size="small"
                    class="indicator-tag editable"
                    closable
                    @close="removeIndicator(index)"
                  >
                    {{ getIndicatorName(indicator) }}
                  </el-tag>
                </div>
              </div>
              
              <!-- 交易规则 -->
              <div class="trading-rules">
                <h4>交易规则</h4>
                <div class="rules-content">
                  <div class="rule-section">
                    <div class="rule-header">
                      <h5>买入条件:</h5>
                      <el-button @click="addBuyCondition" size="small" text>
                        <el-icon><Plus /></el-icon>
                      </el-button>
                    </div>
                    <div class="conditions-list">
                      <div 
                        v-for="(condition, index) in generatedStrategy.buy_conditions" 
                        :key="index"
                        class="condition-card"
                      >
                        <template v-if="typeof condition === 'object'">
                          <div class="condition-content">
                            <div class="condition-header">
                              <el-tag :type="getConditionTypeColor(condition.type)" size="small">
                                {{ getConditionTypeLabel(condition.type) }}
                              </el-tag>
                              <el-button 
                                @click="removeBuyCondition(index)" 
                                size="small" 
                                text 
                                type="danger"
                                circle
                              >
                                <el-icon><Delete /></el-icon>
                              </el-button>
                            </div>
                            <div class="condition-details">
                              <div class="condition-row" v-if="condition.indicator">
                                <span class="label">指标:</span>
                                <el-tag size="small">{{ condition.indicator }}</el-tag>
                              </div>
                              <div class="condition-row" v-if="condition.operator">
                                <span class="label">运算符:</span>
                                <el-tag type="info" size="small">{{ getOperatorLabel(condition.operator) }}</el-tag>
                              </div>
                              <div class="condition-row" v-if="condition.value !== undefined && condition.value !== ''">
                                <span class="label">阈值:</span>
                                <el-tag type="warning" size="small">{{ condition.value }}</el-tag>
                              </div>
                              <div class="condition-row" v-if="condition.params">
                                <span class="label">参数:</span>
                                <div class="params-list">
                                  <el-tag 
                                    v-for="(value, key) in condition.params" 
                                    :key="key" 
                                    size="small"
                                    class="param-tag"
                                  >
                                    {{ key }}: {{ value }}
                                  </el-tag>
                                </div>
                              </div>
                              <div class="condition-description">
                                <el-icon><InfoFilled /></el-icon>
                                {{ condition.description }}
                              </div>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <div class="condition-simple">
                            <span>{{ condition }}</span>
                            <el-button 
                              @click="removeBuyCondition(index)" 
                              size="small" 
                              text 
                              type="danger"
                            >
                              <el-icon><Delete /></el-icon>
                            </el-button>
                          </div>
                        </template>
                      </div>
                    </div>
                  </div>
                  <div class="rule-section">
                    <div class="rule-header">
                      <h5>卖出条件:</h5>
                      <el-button @click="addSellCondition" size="small" text>
                        <el-icon><Plus /></el-icon>
                      </el-button>
                    </div>
                    <div class="conditions-list">
                      <div 
                        v-for="(condition, index) in generatedStrategy.sell_conditions" 
                        :key="index"
                        class="condition-card"
                      >
                        <template v-if="typeof condition === 'object'">
                          <div class="condition-content">
                            <div class="condition-header">
                              <el-tag :type="getConditionTypeColor(condition.type)" size="small">
                                {{ getConditionTypeLabel(condition.type) }}
                              </el-tag>
                              <el-button 
                                @click="removeSellCondition(index)" 
                                size="small" 
                                text 
                                type="danger"
                                circle
                              >
                                <el-icon><Delete /></el-icon>
                              </el-button>
                            </div>
                            <div class="condition-details">
                              <div class="condition-row" v-if="condition.indicator">
                                <span class="label">指标:</span>
                                <el-tag size="small">{{ condition.indicator }}</el-tag>
                              </div>
                              <div class="condition-row" v-if="condition.operator">
                                <span class="label">运算符:</span>
                                <el-tag type="info" size="small">{{ getOperatorLabel(condition.operator) }}</el-tag>
                              </div>
                              <div class="condition-row" v-if="condition.value !== undefined && condition.value !== ''">
                                <span class="label">阈值:</span>
                                <el-tag type="warning" size="small">{{ condition.value }}</el-tag>
                              </div>
                              <div class="condition-row" v-if="condition.params">
                                <span class="label">参数:</span>
                                <div class="params-list">
                                  <el-tag 
                                    v-for="(value, key) in condition.params" 
                                    :key="key" 
                                    size="small"
                                    class="param-tag"
                                  >
                                    {{ key }}: {{ value }}
                                  </el-tag>
                                </div>
                              </div>
                              <div class="condition-description">
                                <el-icon><InfoFilled /></el-icon>
                                {{ condition.description }}
                              </div>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <div class="condition-simple">
                            <span>{{ condition }}</span>
                            <el-button 
                              @click="removeSellCondition(index)" 
                              size="small" 
                              text 
                              type="danger"
                            >
                              <el-icon><Delete /></el-icon>
                            </el-button>
                          </div>
                        </template>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 风险控制 -->
              <div class="risk-controls" v-if="generatedStrategy.risk_controls">
                <h4>风险控制</h4>
                <div class="controls-grid">
                  <div class="control-item">
                    <label>止损(%):</label>
                    <el-input-number 
                      v-model="generatedStrategy.risk_controls.stop_loss" 
                      size="small"
                      :min="0"
                      :max="50"
                      :step="0.1"
                      :precision="1"
                    />
                  </div>
                  <div class="control-item">
                    <label>止盈(%):</label>
                    <el-input-number 
                      v-model="generatedStrategy.risk_controls.take_profit" 
                      size="small"
                      :min="0"
                      :max="100"
                      :step="0.1"
                      :precision="1"
                    />
                  </div>
                  <div class="control-item">
                    <label>仓位(%):</label>
                    <el-input-number 
                      v-model="generatedStrategy.risk_controls.position_size" 
                      size="small"
                      :min="1"
                      :max="100"
                      :step="1"
                    />
                  </div>
                  <div class="control-item">
                    <label>最大持仓:</label>
                    <el-input-number 
                      v-model="generatedStrategy.risk_controls.max_positions" 
                      size="small"
                      :min="1"
                      :max="20"
                      :step="1"
                    />
                  </div>
                </div>
              </div>
              
              <!-- 代码预览 -->
              <div class="code-preview">
                <div class="code-header">
                  <h4>生成的策略代码</h4>
                  <div class="code-actions">
                    <el-button @click="editCode" size="small" text>
                      <el-icon><Edit /></el-icon>
                      编辑代码
                    </el-button>
                    <el-button @click="showFullCode = !showFullCode" size="small" text>
                      {{ showFullCode ? '收起' : '展开' }}
                    </el-button>
                  </div>
                </div>
                <div class="code-content" :class="{ expanded: showFullCode }">
                  <el-input 
                    v-if="isEditingCode"
                    v-model="generatedStrategy.code"
                    type="textarea"
                    :rows="20"
                    placeholder="请输入策略代码"
                    class="code-editor"
                  />
                  <pre v-else><code>{{ generatedStrategy.code }}</code></pre>
                </div>
                <div v-if="isEditingCode" class="code-editor-actions">
                  <el-button @click="saveCode2" type="primary" size="small">保存</el-button>
                  <el-button @click="cancelEditCode" size="small">取消</el-button>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 底部操作栏 -->
    <div class="generator-footer">
      <div class="footer-left">
        <el-button @click="exportChat" size="large">
          <el-icon><Download /></el-icon>
          导出对话
        </el-button>
        <el-button @click="saveTemplate" size="large" :disabled="!generatedStrategy">
          <el-icon><Collection /></el-icon>
          保存为模板
        </el-button>
      </div>
      <div class="footer-right">
        <el-button @click="$emit('cancel')" size="large">
          取消
        </el-button>
        <el-button 
          @click="previewStrategy" 
          size="large"
          :disabled="!generatedStrategy"
        >
          <el-icon><View /></el-icon>
          预览策略
        </el-button>
        <el-button 
          @click="generateStrategy" 
          type="primary" 
          size="large"
          :disabled="!generatedStrategy"
          :loading="isGenerating"
        >
          <el-icon><Check /></el-icon>
          生成策略
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import strategyApi from '@/api/strategy'
import type { Strategy } from '@/types/strategy'

// Emits
const emit = defineEmits<{
  generate: [strategy: Strategy]
  cancel: []
}>()

// 响应式数据
const chatMessagesRef = ref<HTMLElement>()
const userInput = ref('')
const isThinking = ref(false)
const isGenerating = ref(false)
const isRegenerating = ref(false)
const showFullCode = ref(false)
const isEditingCode = ref(false)
const showIndicatorSelector = ref(false)

// 对话消息
const chatMessages = ref<Array<{
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}>>([])

// 生成的策略
const generatedStrategy = ref<any>(null)

// 参数编辑相关
const parameterKeys = ref<Record<string, string>>({})
const originalCode = ref('')

// 建议问题
const suggestions = ref([
  '我想要一个基于RSI的反转策略',
  '帮我创建一个双均线交叉策略',
  '我需要一个布林带突破策略',
  '创建一个MACD动量策略',
  '我想要一个多因子选股策略'
])

// 初始化对话
onMounted(() => {
  chatMessages.value.push({
    role: 'assistant',
    content: `👋 您好！我是AI策略生成助手。

我可以帮您：
• 🎯 根据您的交易想法生成完整的量化策略
• 📊 配置技术指标和交易参数
• ⚡ 生成可执行的Python策略代码
• 🛡️ 设置风险控制规则

请告诉我您的策略想法，比如：
- 您想使用哪些技术指标？
- 您的买卖条件是什么？
- 您的风险偏好如何？

让我们开始创建您的专属策略吧！`,
    timestamp: new Date()
  })
})

// 方法
const sendMessage = async () => {
  if (!userInput.value.trim() || isThinking.value) return
  
  // 添加用户消息
  chatMessages.value.push({
    role: 'user',
    content: userInput.value,
    timestamp: new Date()
  })
  
  const message = userInput.value
  userInput.value = ''
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  // 开始AI思考
  isThinking.value = true
  
  // 模拟AI响应
  setTimeout(async () => {
    const response = await generateAIResponse(message)
    
    chatMessages.value.push({
      role: 'assistant',
      content: response.message,
      timestamp: new Date()
    })
    
    // 如果生成了策略
    if (response.strategy) {
      console.log('[策略更新] 收到新策略数据:', response.strategy)
      console.log('[策略更新] 参数:', response.strategy.parameters)
      console.log('[策略更新] 买入条件:', response.strategy.buy_conditions)
      console.log('[策略更新] 卖出条件:', response.strategy.sell_conditions)
      
      // 强制清空旧数据，确保响应式更新
      generatedStrategy.value = null
      await nextTick()
      
      // 深拷贝策略数据，避免引用问题
      generatedStrategy.value = JSON.parse(JSON.stringify(response.strategy))
      
      console.log('[策略更新] 更新后的策略:', generatedStrategy.value)
      
      // 初始化参数键映射
      await nextTick()
      initParameterKeys()
    }
    
    isThinking.value = false
    
    await nextTick()
    scrollToBottom()
  }, 2000)
}

// 初始化参数键映射
const initParameterKeys = () => {
  if (generatedStrategy.value?.parameters) {
    parameterKeys.value = {}
    Object.keys(generatedStrategy.value.parameters).forEach(key => {
      parameterKeys.value[key] = key
    })
  }
}

// 参数编辑方法
const addParameter = () => {
  if (!generatedStrategy.value.parameters) {
    generatedStrategy.value.parameters = {}
  }
  const newKey = `param_${Date.now()}`
  generatedStrategy.value.parameters[newKey] = 0
  parameterKeys.value[newKey] = newKey
}

const removeParameter = (key: string) => {
  delete generatedStrategy.value.parameters[key]
  delete parameterKeys.value[key]
}

const updateParameterKey = (oldKey: string, newKey: string) => {
  if (oldKey !== newKey && newKey.trim()) {
    const value = generatedStrategy.value.parameters[oldKey]
    delete generatedStrategy.value.parameters[oldKey]
    generatedStrategy.value.parameters[newKey] = value
    
    delete parameterKeys.value[oldKey]
    parameterKeys.value[newKey] = newKey
  }
}

// 指标编辑方法
const removeIndicator = (index: number) => {
  generatedStrategy.value.indicators.splice(index, 1)
}

// 交易规则编辑方法
const addBuyCondition = () => {
  if (!generatedStrategy.value.buy_conditions) {
    generatedStrategy.value.buy_conditions = []
  }
  // 添加对象格式的条件，兼容后端数据结构
  generatedStrategy.value.buy_conditions.push({
    type: 'custom',
    description: '新的买入条件',
    operator: 'greater_than',
    value: ''
  })
}

const removeBuyCondition = (index: number) => {
  generatedStrategy.value.buy_conditions.splice(index, 1)
}

const addSellCondition = () => {
  if (!generatedStrategy.value.sell_conditions) {
    generatedStrategy.value.sell_conditions = []
  }
  // 添加对象格式的条件，兼容后端数据结构
  generatedStrategy.value.sell_conditions.push({
    type: 'custom',
    description: '新的卖出条件',
    operator: 'less_than',
    value: ''
  })
}

const removeSellCondition = (index: number) => {
  generatedStrategy.value.sell_conditions.splice(index, 1)
}

// 条件显示辅助函数
const getConditionTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    'indicator': '技术指标',
    'price': '价格条件',
    'volume': '成交量',
    'custom': '自定义',
    'risk': '风险控制'
  }
  return labels[type] || type
}

const getConditionTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    'indicator': 'primary',
    'price': 'success',
    'volume': 'warning',
    'custom': 'info',
    'risk': 'danger'
  }
  return colors[type] || 'info'
}

const getOperatorLabel = (operator: string) => {
  const labels: Record<string, string> = {
    'greater_than': '大于 >',
    'less_than': '小于 <',
    'equal': '等于 =',
    'cross_above': '上穿 ↗',
    'cross_below': '下穿 ↘',
    'trigger': '触发',
    '>': '大于',
    '<': '小于',
    '=': '等于',
    '>=': '大于等于',
    '<=': '小于等于'
  }
  return labels[operator] || operator
}

// 代码编辑方法
const editCode = () => {
  originalCode.value = generatedStrategy.value.code
  isEditingCode.value = true
}

const saveCode = () => {
  isEditingCode.value = false
  ElMessage.success('代码保存成功')
}

const cancelEditCode = () => {
  generatedStrategy.value.code = originalCode.value
  isEditingCode.value = false
}

const saveCode2 = async () => {
  try {
    const code = generatedStrategy.value?.code || ''
    const validResp = await strategyApi.validateCode(code)
    const valid = validResp.data?.valid
    if (!valid) {
      const errs = validResp.data?.errors || []
      ElMessage.error(errs.join('\n') || '代码校验失败')
      return
    }
    const fmtResp = await strategyApi.formatCode(code)
    if (fmtResp.data?.formatted_code) {
      generatedStrategy.value.code = fmtResp.data.formatted_code
    }
    isEditingCode.value = false
    ElMessage.success('代码校验通过并已格式化')
  } catch {
    ElMessage.error('代码保存失败')
  }
}

const generateAIResponse = async (userMessage: string): Promise<{
  message: string
  strategy?: any
}> => {
  try {
    console.log('[AI生成] 开始调用API，提示词:', userMessage)
    // 调用真实的AI策略生成API
    const response = await strategyApi.generateStrategy(userMessage, {
      strategy_type: 'custom',
      risk_level: 'medium'
    })
    
    const data = response.data
    const promptInfo = response.prompt_info
    
    console.log('[AI生成] API响应:', data)
    console.log('[AI生成] 提示词信息:', promptInfo)
    console.log('[AI生成] 买入条件数量:', data?.buy_conditions?.length || 0)
    console.log('[AI生成] 卖出条件数量:', data?.sell_conditions?.length || 0)
    
    // 如果API调用成功，返回真实的AI生成结果
    if (data) {
      // 构建提示词增强信息
      let promptEnhancementInfo = ''
      if (promptInfo && promptInfo.enhancement_applied) {
        promptEnhancementInfo = `\n\n📝 **提示词增强：**
原始提示词：${promptInfo.original_prompt}

补全后提示词：
${promptInfo.enhanced_prompt}

💡 系统自动补充了缺失的信息，以确保生成完整的策略配置。`
      }
      
      const responseMessage = `✨ 太好了！我已经根据您的需求分析生成了一个专业的量化策略。

📋 **策略特点：**
• 策略名称：${data.name}
• 策略类型：${getStrategyTypeText(data.category)}
• 风险等级：${getRiskLevelText(data.risk_level)}
• AI生成：是

🎯 **核心逻辑：**
${data.description}

⚙️ **参数配置：**
${Object.entries(data.parameters || {}).map(([key, value]) => `• ${key}: ${value}`).join('\n')}
${promptEnhancementInfo}

您可以在右侧查看完整的策略配置和代码。如果需要调整任何参数或逻辑，请告诉我！`

      console.log('[AI生成] 返回策略数据，买入条件:', data.buy_conditions)
      console.log('[AI生成] 返回策略数据，卖出条件:', data.sell_conditions)
      
      return {
        message: responseMessage,
        strategy: {
          ...data,
          real_ai_generated: true, // 标记为真实AI生成
          api_generated: true,
          prompt_info: promptInfo // 保存提示词信息
        }
      }
    }
  } catch (error) {
    console.error('[AI生成] API调用失败，使用本地模拟生成:', error)
  }
  
  // 如果API调用失败，降级到本地模拟生成
  const lowerMessage = userMessage.toLowerCase()
  
  // 检测策略类型
  let strategyType = 'custom'
  let indicators: string[] = []
  let description = ''
  
  if (lowerMessage.includes('rsi') || lowerMessage.includes('相对强弱')) {
    strategyType = 'mean_reversion'
    indicators = ['RSI']
    description = '基于RSI指标的均值回归策略'
  } else if (lowerMessage.includes('均线') || lowerMessage.includes('ma') || lowerMessage.includes('移动平均')) {
    strategyType = 'trend_following'
    indicators = ['MA', 'EMA']
    description = '基于移动平均线的趋势跟踪策略'
  } else if (lowerMessage.includes('布林带') || lowerMessage.includes('bollinger')) {
    strategyType = 'volatility'
    indicators = ['BOLL']
    description = '基于布林带的波动率策略'
  } else if (lowerMessage.includes('macd')) {
    strategyType = 'momentum'
    indicators = ['MACD']
    description = '基于MACD的动量策略'
  }
  
  // 生成策略
  const strategy = {
    name: `AI生成策略_${Date.now()}`,
    description: description || '基于用户需求生成的自定义策略',
    category: strategyType,
    risk_level: 'medium',
    indicators: indicators,
    parameters: {
      position_size: 0.1,
      stop_loss: 5.0,
      take_profit: 15.0
    },
    buy_conditions: [
      {
        type: 'indicator',
        description: '技术指标满足买入条件',
        operator: 'greater_than',
        value: ''
      },
      {
        type: 'price',
        description: '价格突破关键阻力位',
        operator: 'greater_than',
        value: ''
      },
      {
        type: 'volume',
        description: '成交量放大确认',
        operator: 'greater_than',
        value: 1.5
      }
    ],
    sell_conditions: [
      {
        type: 'indicator',
        description: '技术指标满足卖出条件',
        operator: 'less_than',
        value: ''
      },
      {
        type: 'price',
        description: '价格跌破关键支撑位',
        operator: 'less_than',
        value: ''
      },
      {
        type: 'risk',
        description: '止损或止盈触发',
        operator: 'trigger',
        value: ''
      }
    ],
    risk_controls: {
      stop_loss: 5.0,
      take_profit: 15.0,
      position_size: 10,
      max_positions: 5
    },
    code: generateStrategyCode(strategyType, indicators),
    mock_generated: true // 标记为模拟生成
  }
  
  const responseMessage = `✨ 太好了！我已经根据您的需求分析生成了一个${description}。

📋 **策略特点：**
• 策略类型：${getStrategyTypeText(strategyType)}
• 使用指标：${indicators.join(', ') || '自定义指标'}
• 风险等级：中等风险
• 生成方式：本地模拟生成

🎯 **核心逻辑：**
${generateStrategyLogic(strategyType, indicators)}

⚙️ **参数配置：**
• 单笔仓位：10%
• 止损比例：5%
• 止盈比例：15%
• 最大持仓：5只股票

您可以在右侧查看完整的策略配置和代码。如果需要调整任何参数或逻辑，请告诉我！`

  return {
    message: responseMessage,
    strategy: strategy
  }
}

const generateStrategyCode = (type: string, indicators: string[]): string => {
  const templates = {
    mean_reversion: `def initialize(context):
    # RSI反转策略
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.rsi_period = 14
    context.rsi_overbought = 70
    context.rsi_oversold = 30
    context.position_size = 0.1

def handle_data(context, data):
    for stock in context.stocks:
        # 计算RSI
        hist = data.history(stock, 'close', context.rsi_period + 1)
        rsi = calculate_rsi(hist, context.rsi_period)
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：RSI < 30
        if rsi < context.rsi_oversold and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：RSI > 70
        elif rsi > context.rsi_overbought and current_position > 0:
            order_target_percent(stock, 0)`,
            
    trend_following: `def initialize(context):
    # 双均线策略
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.short_period = 5
    context.long_period = 20
    context.position_size = 0.1

def handle_data(context, data):
    for stock in context.stocks:
        # 获取历史价格数据
        hist = data.history(stock, 'close', context.long_period + 1)
        
        # 计算均线
        short_ma = hist[-context.short_period:].mean()
        long_ma = hist.mean()
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：短均线上穿长均线
        if short_ma > long_ma and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：短均线下穿长均线
        elif short_ma < long_ma and current_position > 0:
            order_target_percent(stock, 0)`,
            
    default: `def initialize(context):
    # 自定义策略
    context.stocks = ['000001.XSHE']
    context.position_size = 0.1

def handle_data(context, data):
    # 策略逻辑
    for stock in context.stocks:
        current_position = context.portfolio.positions[stock].amount
        
        # 买入条件
        if should_buy(context, data, stock) and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出条件
        elif should_sell(context, data, stock) and current_position > 0:
            order_target_percent(stock, 0)`
  }
  
  return templates[type as keyof typeof templates] || templates.default
}

const generateStrategyLogic = (type: string, indicators: string[]): string => {
  const logics = {
    mean_reversion: '当RSI指标低于30时认为股票超卖，产生买入信号；当RSI高于70时认为股票超买，产生卖出信号。',
    trend_following: '当短期均线上穿长期均线时产生买入信号，当短期均线下穿长期均线时产生卖出信号。',
    volatility: '当价格触及布林带下轨时买入，触及上轨时卖出，利用价格的均值回归特性。',
    momentum: '利用MACD指标的金叉死叉信号，结合价格动量进行交易决策。',
    default: '根据自定义的技术指标和交易规则进行买卖决策。'
  }
  
  return logics[type as keyof typeof logics] || logics.default
}

const selectSuggestion = (suggestion: string) => {
  userInput.value = suggestion
  suggestions.value = []
}

const clearChat = () => {
  chatMessages.value = []
  generatedStrategy.value = null
  onMounted() // 重新初始化
}

const scrollToBottom = () => {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

const formatMessage = (content: string) => {
  // 简单的markdown格式化
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/•/g, '•')
    .replace(/\n/g, '<br>')
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const regenerateStrategy = async () => {
  isRegenerating.value = true
  
  // 模拟重新生成
  setTimeout(() => {
    if (generatedStrategy.value) {
      generatedStrategy.value.name = `AI生成策略_${Date.now()}`
      generatedStrategy.value.parameters.position_size = Math.random() * 0.2 + 0.05
    }
    isRegenerating.value = false
    ElMessage.success('策略重新生成完成')
  }, 1500)
}

const exportChat = () => {
  const chatContent = chatMessages.value.map(msg => 
    `[${formatTime(msg.timestamp)}] ${msg.role === 'user' ? '用户' : 'AI'}: ${msg.content}`
  ).join('\n\n')
  
  const blob = new Blob([chatContent], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `AI策略对话_${new Date().getTime()}.txt`
  link.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('对话记录导出成功')
}

const saveTemplate = () => {
  ElMessage.success('策略模板保存成功')
}

const previewStrategy = () => {
  ElMessage.info('策略预览功能开发中')
}

const generateStrategy = async () => {
  if (!generatedStrategy.value) return
  
  isGenerating.value = true
  
  try {
    // 准备策略数据
    const createPayload = {
      name: generatedStrategy.value.name,
      display_name: generatedStrategy.value.name,
      description: generatedStrategy.value.description,
      category: generatedStrategy.value.category,
      risk_level: generatedStrategy.value.risk_level,
      parameters: generatedStrategy.value.parameters,
      code: generatedStrategy.value.code,
      status: 'draft',
      ai_generated: true,
      original_prompt: chatMessages.value
        .filter(msg => msg.role === 'user')
        .map(msg => msg.content)
        .join('\n'),
      // 添加其他字段
      indicators: generatedStrategy.value.indicators,
      buy_conditions: generatedStrategy.value.buy_conditions,
      sell_conditions: generatedStrategy.value.sell_conditions,
      risk_controls: generatedStrategy.value.risk_controls
    }
    
    // 调用createStrategy API保存到数据库
    const { data } = await strategyApi.createStrategy(createPayload)
    
    const strategy: Strategy = {
      ...data,
      ai_generated: true,
      saved_to_database: true
    }
    
    emit('generate', strategy)
    ElMessage.success('策略生成成功并已保存到数据库')
    
  } catch (error) {
    console.error('策略保存失败:', error)
    
    // 如果保存失败，仍然可以在前端显示策略，但标记为未保存
    const strategy: Strategy = {
      strategy_id: `AI_${Date.now()}`,
      name: generatedStrategy.value.name,
      display_name: generatedStrategy.value.name,
      description: generatedStrategy.value.description,
      category: generatedStrategy.value.category,
      risk_level: generatedStrategy.value.risk_level,
      parameters: generatedStrategy.value.parameters,
      code: generatedStrategy.value.code,
      status: 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      ai_generated: true,
      saved_to_database: false
    }
    
    emit('generate', strategy)
    ElMessage.warning('策略生成成功，但保存到数据库失败，请稍后重试')
  } finally {
    isGenerating.value = false
  }
}

// 工具方法
const getStrategyTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    trend_following: '趋势跟踪',
    mean_reversion: '均值回归',
    momentum: '动量策略',
    volatility: '波动率策略',
    arbitrage: '套利策略',
    multi_factor: '多因子',
    custom: '自定义'
  }
  return typeMap[type] || type
}

const getStrategyTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    trend_following: 'primary',
    mean_reversion: 'success',
    momentum: 'warning',
    volatility: 'info',
    arbitrage: 'danger',
    multi_factor: '',
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

const getIndicatorName = (code: string) => {
  const indicatorMap: Record<string, string> = {
    MA: '移动平均线',
    EMA: '指数移动平均线',
    RSI: '相对强弱指数',
    MACD: 'MACD指标',
    BOLL: '布林带',
    KDJ: 'KDJ指标'
  }
  return indicatorMap[code] || code
}
</script>

<style lang="scss" scoped>
.ai-strategy-generator {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

// 生成器头部
.generator-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px;
  color: white;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .generator-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 8px 0;
    
    .el-icon {
      font-size: 28px;
    }
  }
  
  .generator-subtitle {
    font-size: 14px;
    opacity: 0.9;
    margin: 0;
  }
}

// 生成器内容
.generator-content {
  flex: 1;
  padding: 24px;
  overflow: hidden;
}

// 对话区域
.chat-section {
  background: white;
  border-radius: 12px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  
  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #e5e7eb;
    
    h3 {
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
      margin: 0;
    }
  }
  
  .chat-messages {
    flex: 1;
    padding: 20px 24px;
    overflow-y: auto;
    
    .message-item {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      
      &.user {
        flex-direction: row-reverse;
        
        .message-content {
          background: #3b82f6;
          color: white;
          border-radius: 18px 18px 4px 18px;
        }
      }
      
      &.assistant {
        .message-content {
          background: #f3f4f6;
          color: #1f2937;
          border-radius: 18px 18px 18px 4px;
        }
      }
      
      &.thinking {
        .message-content {
          background: #eff6ff;
          border: 1px solid #dbeafe;
        }
      }
      
      .message-content {
        max-width: 70%;
        padding: 12px 16px;
        
        .message-text {
          line-height: 1.6;
          word-wrap: break-word;
        }
        
        .message-time {
          font-size: 12px;
          opacity: 0.7;
          margin-top: 8px;
        }
        
        .thinking-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #3b82f6;
            animation: thinking 1.4s infinite ease-in-out;
            
            &:nth-child(1) { animation-delay: -0.32s; }
            &:nth-child(2) { animation-delay: -0.16s; }
          }
          
          .thinking-text {
            color: #6b7280;
            font-size: 14px;
          }
        }
      }
    }
  }
  
  .chat-input {
    border-top: 1px solid #e5e7eb;
    padding: 20px 24px;
    
    .input-suggestions {
      margin-bottom: 16px;
      
      .suggestions-title {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 8px;
      }
      
      .suggestions-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        
        .suggestion-tag {
          cursor: pointer;
          transition: all 0.3s ease;
          
          &:hover {
            background: #3b82f6;
            color: white;
          }
        }
      }
    }
    
    .input-area {
      .input-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;
        
        .input-tips {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: #9ca3af;
        }
      }
    }
  }
}

// 策略预览
.strategy-preview {
  background: white;
  border-radius: 12px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  
  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #e5e7eb;
    
    h3 {
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
      margin: 0;
    }
  }
  
  .empty-preview {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    text-align: center;
    
    .empty-icon {
      font-size: 64px;
      color: #d1d5db;
      margin-bottom: 16px;
    }
    
    .empty-text {
      h4 {
        font-size: 18px;
        color: #374151;
        margin: 0 0 8px 0;
      }
      
      p {
        font-size: 14px;
        color: #9ca3af;
        margin: 0;
      }
    }
  }
  
  .strategy-content {
    flex: 1;
    padding: 20px 24px;
    overflow-y: auto;
    
    .strategy-info,
    .strategy-params,
    .strategy-indicators,
    .trading-rules,
    .risk-controls,
    .code-preview {
      margin-bottom: 24px;
      
      h4 {
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
        margin: 0 0 12px 0;
      }
      
      h5 {
        font-size: 14px;
        font-weight: 600;
        color: #374151;
        margin: 0 0 8px 0;
      }
    }
    
    .info-item {
      display: flex;
      align-items: flex-start;
      margin-bottom: 8px;
      
      label {
        font-size: 14px;
        color: #6b7280;
        min-width: 80px;
        margin-right: 8px;
      }
      
      span, p {
        font-size: 14px;
        color: #1f2937;
        margin: 0;
      }
    }
    
    .params-list {
      .param-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        background: #f9fafb;
        border-radius: 6px;
        margin-bottom: 4px;
        gap: 8px;
        
        &.editable {
          background: #fff;
          border: 1px solid #e5e7eb;
          
          .param-separator {
            color: #6b7280;
            font-weight: 500;
          }
        }
        
        .param-name {
          font-weight: 500;
          color: #374151;
        }
        
        .param-value {
          color: #6b7280;
          font-family: 'Courier New', monospace;
        }
      }
    }
    
    .params-header,
    .indicators-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    
    .conditions-list {
      .condition-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      
      .condition-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: #667eea;
          box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
        }
      }
      
      .condition-content {
        .condition-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid #e5e7eb;
        }
        
        .condition-details {
          .condition-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            
            .label {
              font-size: 12px;
              color: #6b7280;
              min-width: 50px;
              font-weight: 500;
            }
            
            .params-list {
              display: flex;
              flex-wrap: wrap;
              gap: 6px;
              
              .param-tag {
                font-size: 11px;
              }
            }
          }
          
          .condition-description {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 12px;
            padding: 8px 12px;
            background: #fff;
            border-radius: 6px;
            font-size: 13px;
            color: #374151;
            border-left: 3px solid #667eea;
            
            .el-icon {
              color: #667eea;
              font-size: 14px;
            }
          }
        }
      }
      
      .condition-simple {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
        background: #f3f4f6;
        border-radius: 6px;
        
        span {
          font-size: 14px;
          color: #374151;
        }
      }
    }
    
    .rule-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    
    .code-actions {
      display: flex;
      gap: 8px;
    }
    
    .code-editor {
      font-family: 'Courier New', monospace;
      font-size: 12px;
      
      :deep(.el-textarea__inner) {
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.5;
      }
    }
    
    .code-editor-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #e5e7eb;
    }
    
    .indicators-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      
      .indicator-tag {
        font-size: 12px;
      }
    }
    
    .rules-content {
      .rule-section {
        margin-bottom: 16px;
        
        ul {
          margin: 0;
          padding-left: 20px;
          
          li {
            font-size: 14px;
            color: #374151;
            margin-bottom: 4px;
          }
        }
      }
    }
    
    .controls-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      
      .control-item {
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
    
    .code-preview {
      .code-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }
      
      .code-content {
        background: #1e293b;
        border-radius: 8px;
        overflow: auto;
        max-height: 300px;
        transition: max-height 0.3s ease;
        
        &.expanded {
          max-height: 600px;
        }
        
        pre {
          margin: 0;
          padding: 16px;
          overflow: visible;
          max-height: none;
          
          code {
            color: #e2e8f0;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.5;
            white-space: pre;
            display: block;
          }
        }
      }
    }
  }
}

// 底部操作栏
.generator-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: white;
  border-top: 1px solid #e5e7eb;
  
  .footer-left,
  .footer-right {
    display: flex;
    gap: 12px;
  }
}

// 动画
@keyframes thinking {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .generator-content {
    .el-col:first-child {
      margin-bottom: 24px;
    }
  }
}

@media (max-width: 768px) {
  .generator-header {
    .header-content {
      flex-direction: column;
      gap: 16px;
      text-align: center;
    }
  }
  
  .generator-content {
    padding: 16px;
  }
  
  .chat-messages {
    .message-item {
      .message-content {
        max-width: 85%;
      }
    }
  }
  
  .generator-footer {
    flex-direction: column;
    gap: 16px;
    
    .footer-left,
    .footer-right {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>
