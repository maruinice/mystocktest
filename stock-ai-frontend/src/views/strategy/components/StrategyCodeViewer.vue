<template>
  <div class="strategy-code-viewer">
    <div class="viewer-header">
      <div class="header-info">
        <h2>{{ strategy.name }} - 策略代码</h2>
        <div class="strategy-meta">
          <el-tag :type="getStrategyTypeColor(strategy.category)" size="small">
            {{ getStrategyTypeText(strategy.category) }}
          </el-tag>
          <el-tag :type="getRiskLevelColor(strategy.risk_level)" size="small">
            {{ getRiskLevelText(strategy.risk_level) }}
          </el-tag>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="copyCode" size="large">
          <el-icon><CopyDocument /></el-icon>
          复制代码
        </el-button>
        <el-button @click="downloadCode" size="large">
          <el-icon><Download /></el-icon>
          下载代码
        </el-button>
        <el-button @click="$emit('edit', strategy)" type="primary" size="large">
          <el-icon><Edit /></el-icon>
          编辑策略
        </el-button>
      </div>
    </div>

    <div class="viewer-content">
      <el-row :gutter="24">
        <!-- 左侧代码区域 -->
        <el-col :span="16">
          <div class="code-section">
            <div class="code-header">
              <div class="header-left">
                <h3>策略代码</h3>
                <div class="code-stats">
                  <span>{{ codeStats.lines }} 行</span>
                  <span>{{ codeStats.functions }} 个函数</span>
                  <span>{{ codeStats.size }} 字符</span>
                </div>
              </div>
              <div class="header-right">
                <el-button-group>
                  <el-button 
                    @click="formatCode" 
                    size="small"
                    :loading="formatting"
                  >
                    <el-icon><Magic /></el-icon>
                    格式化
                  </el-button>
                  <el-button @click="validateCode" size="small">
                    <el-icon><CircleCheck /></el-icon>
                    验证语法
                  </el-button>
                  <el-button @click="showDocs = !showDocs" size="small">
                    <el-icon><Document /></el-icon>
                    {{ showDocs ? '隐藏' : '显示' }}文档
                  </el-button>
                </el-button-group>
              </div>
            </div>
            
            <div class="code-container">
              <div class="code-editor">
                <pre class="code-content"><code class="python">{{ strategy.code || defaultCode }}</code></pre>
              </div>
              
              <!-- 语法验证结果 -->
              <div v-if="validationResult" class="validation-result">
                <div v-if="validationResult.valid" class="validation-success">
                  <el-icon><CircleCheck /></el-icon>
                  代码语法正确
                </div>
                <div v-else class="validation-error">
                  <el-icon><CircleClose /></el-icon>
                  发现语法错误:
                  <ul>
                    <li v-for="error in validationResult.errors" :key="error">{{ error }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 右侧信息面板 -->
        <el-col :span="8">
          <div class="info-panel">
            <!-- 策略信息 -->
            <div class="info-section">
              <h3>策略信息</h3>
              <div class="info-content">
                <div class="info-item">
                  <label>策略名称:</label>
                  <span>{{ strategy.name }}</span>
                </div>
                <div class="info-item">
                  <label>策略描述:</label>
                  <p>{{ strategy.description }}</p>
                </div>
                <div class="info-item">
                  <label>创建时间:</label>
                  <span>{{ formatDateTime(strategy.created_at) }}</span>
                </div>
                <div class="info-item">
                  <label>更新时间:</label>
                  <span>{{ formatDateTime(strategy.updated_at) }}</span>
                </div>
                <div class="info-item" v-if="strategy.author">
                  <label>作者:</label>
                  <span>{{ strategy.author }}</span>
                </div>
              </div>
            </div>

            <!-- 策略参数 -->
            <div class="info-section" v-if="strategy.parameters && Object.keys(strategy.parameters).length > 0">
              <h3>策略参数</h3>
              <div class="params-list">
                <div 
                  v-for="(value, key) in strategy.parameters" 
                  :key="key"
                  class="param-item"
                >
                  <span class="param-name">{{ key }}:</span>
                  <span class="param-value">{{ value }}</span>
                </div>
              </div>
            </div>

            <!-- 技术指标 -->
            <div class="info-section" v-if="strategy.indicators && strategy.indicators.length > 0">
              <h3>使用指标</h3>
              <div class="indicators-list">
                <el-tag 
                  v-for="indicator in strategy.indicators" 
                  :key="indicator"
                  size="small"
                  class="indicator-tag"
                >
                  {{ getIndicatorName(indicator) }}
                </el-tag>
              </div>
            </div>

            <!-- 风险控制 -->
            <div class="info-section" v-if="strategy.risk_controls">
              <h3>风险控制</h3>
              <div class="risk-controls">
                <div class="control-item" v-if="strategy.risk_controls.stop_loss">
                  <label>止损:</label>
                  <span>{{ strategy.risk_controls.stop_loss }}%</span>
                </div>
                <div class="control-item" v-if="strategy.risk_controls.take_profit">
                  <label>止盈:</label>
                  <span>{{ strategy.risk_controls.take_profit }}%</span>
                </div>
                <div class="control-item" v-if="strategy.risk_controls.position_size">
                  <label>仓位:</label>
                  <span>{{ strategy.risk_controls.position_size }}%</span>
                </div>
                <div class="control-item" v-if="strategy.risk_controls.max_positions">
                  <label>最大持仓:</label>
                  <span>{{ strategy.risk_controls.max_positions }}只</span>
                </div>
              </div>
            </div>

            <!-- 代码文档 -->
            <div class="info-section" v-if="showDocs">
              <h3>代码文档</h3>
              <div class="docs-content">
                <el-collapse v-model="activeDocs">
                  <el-collapse-item title="函数说明" name="functions">
                    <div class="doc-section">
                      <h4>initialize(context)</h4>
                      <p>策略初始化函数，在策略开始运行前调用一次。</p>
                      <ul>
                        <li><strong>context:</strong> 策略上下文对象</li>
                      </ul>
                      
                      <h4>handle_data(context, data)</h4>
                      <p>数据处理函数，每个交易日调用一次。</p>
                      <ul>
                        <li><strong>context:</strong> 策略上下文对象</li>
                        <li><strong>data:</strong> 当日数据对象</li>
                      </ul>
                    </div>
                  </el-collapse-item>
                  
                  <el-collapse-item title="可用API" name="api">
                    <div class="doc-section">
                      <h4>数据获取</h4>
                      <ul>
                        <li><code>data.current(asset, field)</code> - 获取当前价格</li>
                        <li><code>data.history(asset, fields, bar_count)</code> - 获取历史数据</li>
                      </ul>
                      
                      <h4>交易下单</h4>
                      <ul>
                        <li><code>order(asset, amount)</code> - 按数量下单</li>
                        <li><code>order_target_percent(asset, target)</code> - 按目标仓位下单</li>
                      </ul>
                      
                      <h4>持仓查询</h4>
                      <ul>
                        <li><code>context.portfolio.positions</code> - 当前持仓</li>
                        <li><code>get_open_orders()</code> - 未成交订单</li>
                      </ul>
                    </div>
                  </el-collapse-item>
                  
                  <el-collapse-item title="示例代码" name="examples">
                    <div class="doc-section">
                      <h4>获取股票价格</h4>
                      <pre><code>current_price = data.current(stock, 'close')
hist_prices = data.history(stock, 'close', 20)</code></pre>
                      
                      <h4>计算技术指标</h4>
                      <pre><code>ma_short = hist_prices[-5:].mean()
ma_long = hist_prices.mean()</code></pre>
                      
                      <h4>下单交易</h4>
                      <pre><code>if ma_short > ma_long:
    order_target_percent(stock, 0.1)
else:
    order_target_percent(stock, 0)</code></pre>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="viewer-footer">
      <div class="footer-left">
        <el-button @click="$emit('close')">关闭</el-button>
      </div>
      <div class="footer-right">
        <el-button @click="runBacktest" type="warning">
          <el-icon><DataAnalysis /></el-icon>
          运行回测
        </el-button>
        <el-button @click="$emit('edit', strategy)" type="primary">
          <el-icon><Edit /></el-icon>
          编辑策略
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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
  edit: [strategy: Strategy]
}>()

// 响应式数据
const formatting = ref(false)
const showDocs = ref(false)
const activeDocs = ref(['functions'])
const validationResult = ref<{ valid: boolean; errors: string[] } | null>(null)

// 默认代码模板
const defaultCode = `def initialize(context):
    # 策略初始化
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.position_size = 0.1

def handle_data(context, data):
    # 策略逻辑
    for stock in context.stocks:
        current_price = data.current(stock, 'close')
        
        # 在这里添加您的交易逻辑
        pass`

// 计算属性
const codeStats = computed(() => {
  const code = props.strategy.code || defaultCode
  const lines = code.split('\n').length
  const functions = (code.match(/def\s+\w+/g) || []).length
  const size = code.length
  
  return { lines, functions, size }
})

// 方法
const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(props.strategy.code || defaultCode)
    ElMessage.success('代码已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const downloadCode = () => {
  const code = props.strategy.code || defaultCode
  const blob = new Blob([code], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.strategy.name}_strategy.py`
  link.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('代码下载成功')
}

const formatCode = async () => {
  formatting.value = true
  
  try {
    // 模拟代码格式化
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('代码格式化完成')
  } catch (error) {
    ElMessage.error('代码格式化失败')
  } finally {
    formatting.value = false
  }
}

const validateCode = () => {
  const code = props.strategy.code || defaultCode
  const errors: string[] = []
  
  // 基本语法检查
  if (!code.includes('def initialize(context):')) {
    errors.push('缺少 initialize 函数')
  }
  
  if (!code.includes('def handle_data(context, data):')) {
    errors.push('缺少 handle_data 函数')
  }
  
  // 检查缩进
  const lines = code.split('\n')
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (line.trim() && !line.startsWith(' ') && !line.startsWith('def') && !line.startsWith('#')) {
      errors.push(`第 ${i + 1} 行缩进错误`)
    }
  }
  
  validationResult.value = {
    valid: errors.length === 0,
    errors: errors
  }
  
  if (validationResult.value.valid) {
    ElMessage.success('代码验证通过')
  } else {
    ElMessage.error('代码验证失败，请检查错误')
  }
}

const runBacktest = () => {
  ElMessage.info('正在启动回测...')
  // 这里应该调用回测API
}

// 工具方法
const getStrategyTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    trend_following: '趋势跟踪',
    mean_reversion: '均值回归',
    momentum: '动量策略',
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
    arbitrage: 'info',
    multi_factor: 'danger',
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

// 生命周期
onMounted(() => {
  // 初始化代码高亮
  // 这里可以集成代码高亮库如Prism.js或highlight.js
})
</script>

<style lang="scss" scoped>
.strategy-code-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

// 查看器头部
.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  
  .header-info {
    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 600;
    }
    
    .strategy-meta {
      display: flex;
      gap: 8px;
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

// 查看器内容
.viewer-content {
  flex: 1;
  padding: 24px;
  overflow: hidden;
}

// 代码区域
.code-section {
  background: white;
  border-radius: 12px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  
  .code-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #e5e7eb;
    
    .header-left {
      h3 {
        margin: 0 0 4px 0;
        font-size: 18px;
        font-weight: 600;
        color: #1f2937;
      }
      
      .code-stats {
        display: flex;
        gap: 16px;
        font-size: 12px;
        color: #9ca3af;
      }
    }
  }
  
  .code-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    
    .code-editor {
      flex: 1;
      overflow: auto;
      
      .code-content {
        margin: 0;
        padding: 24px;
        background: #1e293b;
        color: #e2e8f0;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.6;
        overflow: auto;
        
        code {
          color: inherit;
        }
      }
    }
    
    .validation-result {
      padding: 16px 24px;
      border-top: 1px solid #e5e7eb;
      
      .validation-success {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #059669;
        font-weight: 600;
      }
      
      .validation-error {
        color: #dc2626;
        
        ul {
          margin: 8px 0 0 0;
          padding-left: 20px;
          
          li {
            margin-bottom: 4px;
          }
        }
      }
    }
  }
}

// 信息面板
.info-panel {
  height: 100%;
  overflow-y: auto;
  
  .info-section {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    
    h3 {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
    }
    
    .info-content {
      .info-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 12px;
        
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
    }
    
    .params-list {
      .param-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 12px;
        background: #f9fafb;
        border-radius: 6px;
        margin-bottom: 4px;
        
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
    
    .indicators-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      
      .indicator-tag {
        font-size: 12px;
      }
    }
    
    .risk-controls {
      .control-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 12px;
        background: #f9fafb;
        border-radius: 6px;
        margin-bottom: 4px;
        
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
    
    .docs-content {
      .doc-section {
        h4 {
          font-size: 14px;
          font-weight: 600;
          color: #1f2937;
          margin: 0 0 8px 0;
        }
        
        p {
          font-size: 14px;
          color: #374151;
          margin: 0 0 12px 0;
          line-height: 1.5;
        }
        
        ul {
          margin: 0 0 16px 0;
          padding-left: 20px;
          
          li {
            font-size: 14px;
            color: #374151;
            margin-bottom: 4px;
            
            code {
              background: #f3f4f6;
              padding: 2px 4px;
              border-radius: 3px;
              font-family: 'Courier New', monospace;
              font-size: 12px;
            }
          }
        }
        
        pre {
          background: #1e293b;
          color: #e2e8f0;
          padding: 12px;
          border-radius: 6px;
          overflow-x: auto;
          margin: 0 0 16px 0;
          
          code {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
          }
        }
      }
    }
  }
}

// 底部操作栏
.viewer-footer {
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

// 响应式设计
@media (max-width: 1200px) {
  .viewer-content {
    .el-col:first-child {
      margin-bottom: 24px;
    }
  }
}

@media (max-width: 768px) {
  .viewer-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .viewer-content {
    padding: 16px;
  }
  
  .code-header {
    flex-direction: column;
    gap: 12px;
    
    .header-left,
    .header-right {
      width: 100%;
      text-align: center;
    }
  }
  
  .viewer-footer {
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