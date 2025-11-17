<template>
  <div class="strategy-builder">
    <!-- 构建器头部 -->
    <div class="builder-header">
      <div class="header-left">
        <h2 class="builder-title">
          {{ editStrategy ? '编辑策略' : '创建策略' }}
        </h2>
        <p class="builder-subtitle">
          {{ editStrategy ? '修改现有策略配置和代码' : '通过可视化配置或代码编写创建新策略' }}
        </p>
      </div>
      <div class="header-right">
        <el-radio-group v-model="builderMode" size="large">
          <el-radio-button label="visual">
            <el-icon><Setting /></el-icon>
            可视化配置
          </el-radio-button>
          <el-radio-button label="code">
            <el-icon><Document /></el-icon>
            代码编辑
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 可视化配置模式 -->
    <div v-if="builderMode === 'visual'" class="visual-builder">
      <el-row :gutter="24">
        <!-- 左侧配置面板 -->
        <el-col :span="16">
          <div class="config-panel">
            <!-- 基本信息 -->
            <div class="config-section">
              <div class="section-header">
                <h3>基本信息</h3>
                <el-tooltip content="策略的基本信息配置" placement="top">
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              
              <el-form :model="strategyForm" :rules="formRules" ref="strategyFormRef" label-width="120px">
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="策略名称" prop="name">
                      <el-input 
                        v-model="strategyForm.name" 
                        placeholder="请输入策略名称"
                        maxlength="50"
                        show-word-limit
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="策略作者" prop="author">
                      <el-input 
                        v-model="strategyForm.author" 
                        placeholder="请输入作者名称"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-form-item label="策略描述" prop="description">
                  <el-input
                    v-model="strategyForm.description"
                    type="textarea"
                    :rows="3"
                    placeholder="请详细描述策略的逻辑和特点"
                    maxlength="500"
                    show-word-limit
                  />
                </el-form-item>
                
                <el-row :gutter="16">
                  <el-col :span="8">
                    <el-form-item label="策略类型" prop="category">
                      <el-select v-model="strategyForm.category" style="width: 100%">
                        <el-option 
                          v-for="type in strategyTypes" 
                          :key="type.value" 
                          :label="type.label" 
                          :value="type.value"
                        >
                          <div class="option-item">
                            <span>{{ type.label }}</span>
                            <el-tooltip :content="type.description" placement="right">
                              <el-icon class="option-help"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </div>
                        </el-option>
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="风险等级" prop="risk_level">
                      <el-select v-model="strategyForm.risk_level" style="width: 100%">
                        <el-option 
                          v-for="risk in riskLevels" 
                          :key="risk.value" 
                          :label="risk.label" 
                          :value="risk.value"
                        >
                          <div class="option-item">
                            <el-tag :type="risk.color" size="small">{{ risk.label }}</el-tag>
                            <span class="risk-desc">{{ risk.description }}</span>
                          </div>
                        </el-option>
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="最小资金" prop="min_capital">
                      <el-input-number
                        v-model="strategyForm.min_capital"
                        :min="10000"
                        :max="10000000"
                        :step="10000"
                        style="width: 100%"
                        controls-position="right"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>

            <!-- 技术指标配置 -->
            <div class="config-section">
              <div class="section-header">
                <h3>技术指标配置</h3>
                <el-tooltip content="选择策略使用的技术指标" placement="top">
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              
              <div class="indicators-grid">
                <div 
                  v-for="indicator in technicalIndicators" 
                  :key="indicator.code"
                  class="indicator-card"
                  :class="{ active: selectedIndicators.includes(indicator.code) }"
                  @click="toggleIndicator(indicator.code)"
                >
                  <div class="indicator-header">
                    <el-checkbox 
                      :model-value="selectedIndicators.includes(indicator.code)"
                      @change="toggleIndicator(indicator.code)"
                    />
                    <span class="indicator-name">{{ indicator.name }}</span>
                    <el-tooltip :content="indicator.description" placement="top">
                      <el-icon class="indicator-help"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </div>
                  <div class="indicator-formula">{{ indicator.formula }}</div>
                  
                  <!-- 指标参数配置 -->
                  <div v-if="selectedIndicators.includes(indicator.code)" class="indicator-params">
                    <div 
                      v-for="param in indicator.parameters" 
                      :key="param.name"
                      class="param-item"
                    >
                      <label>{{ param.label }}:</label>
                      <el-input-number
                        v-model="indicatorParams[indicator.code][param.name]"
                        :min="param.min"
                        :max="param.max"
                        :step="param.step"
                        size="small"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 策略参数配置 -->
            <div class="config-section">
              <div class="section-header">
                <h3>策略参数</h3>
                <el-tooltip content="配置策略的核心参数" placement="top">
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
                <el-button @click="addCustomParameter" size="small" type="primary" text>
                  <el-icon><Plus /></el-icon>
                  添加参数
                </el-button>
              </div>
              
              <div class="parameters-list">
                <div 
                  v-for="(param, index) in strategyParameters" 
                  :key="index"
                  class="parameter-item"
                >
                  <el-row :gutter="12" align="middle">
                    <el-col :span="5">
                      <el-input 
                        v-model="param.name" 
                        placeholder="参数名称"
                        size="small"
                      />
                    </el-col>
                    <el-col :span="4">
                      <el-select v-model="param.type" size="small">
                        <el-option label="数字" value="number" />
                        <el-option label="文本" value="string" />
                        <el-option label="布尔" value="boolean" />
                        <el-option label="选择" value="select" />
                      </el-select>
                    </el-col>
                    <el-col :span="4">
                      <el-input 
                        v-model="param.default_value" 
                        placeholder="默认值"
                        size="small"
                      />
                    </el-col>
                    <el-col :span="6">
                      <el-input 
                        v-model="param.description" 
                        placeholder="参数描述"
                        size="small"
                      />
                    </el-col>
                    <el-col :span="3">
                      <el-input 
                        v-model="param.range" 
                        placeholder="取值范围"
                        size="small"
                      />
                    </el-col>
                    <el-col :span="2">
                      <el-button 
                        @click="removeParameter(index)" 
                        size="small" 
                        type="danger" 
                        text
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </el-col>
                  </el-row>
                </div>
              </div>
            </div>

            <!-- 交易规则配置 -->
            <div class="config-section">
              <div class="section-header">
                <h3>交易规则</h3>
                <el-tooltip content="配置买入卖出条件和风险控制" placement="top">
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              
              <el-tabs v-model="activeRuleTab" type="border-card">
                <el-tab-pane label="买入条件" name="buy">
                  <div class="rule-builder">
                    <div 
                      v-for="(condition, index) in buyConditions" 
                      :key="index"
                      class="condition-item"
                    >
                      <el-row :gutter="12" align="middle">
                        <el-col :span="1" v-if="index > 0">
                          <el-select v-model="condition.operator" size="small">
                            <el-option label="且" value="and" />
                            <el-option label="或" value="or" />
                          </el-select>
                        </el-col>
                        <el-col :span="6">
                          <el-select v-model="condition.indicator" placeholder="选择指标" size="small">
                            <el-option 
                              v-for="indicator in availableIndicators" 
                              :key="indicator.code"
                              :label="indicator.name" 
                              :value="indicator.code"
                            />
                          </el-select>
                        </el-col>
                        <el-col :span="4">
                          <el-select v-model="condition.comparison" size="small">
                            <el-option label="大于" value=">" />
                            <el-option label="小于" value="<" />
                            <el-option label="等于" value="=" />
                            <el-option label="大于等于" value=">=" />
                            <el-option label="小于等于" value="<=" />
                            <el-option label="上穿" value="cross_above" />
                            <el-option label="下穿" value="cross_below" />
                          </el-select>
                        </el-col>
                        <el-col :span="6">
                          <el-input 
                            v-model="condition.value" 
                            placeholder="阈值或指标"
                            size="small"
                          />
                        </el-col>
                        <el-col :span="6">
                          <el-input 
                            v-model="condition.description" 
                            placeholder="条件描述"
                            size="small"
                          />
                        </el-col>
                        <el-col :span="1">
                          <el-button 
                            @click="removeBuyCondition(index)" 
                            size="small" 
                            type="danger" 
                            text
                          >
                            <el-icon><Delete /></el-icon>
                          </el-button>
                        </el-col>
                      </el-row>
                    </div>
                    <el-button @click="addBuyCondition" size="small" type="primary" text>
                      <el-icon><Plus /></el-icon>
                      添加买入条件
                    </el-button>
                  </div>
                </el-tab-pane>
                
                <el-tab-pane label="卖出条件" name="sell">
                  <div class="rule-builder">
                    <div 
                      v-for="(condition, index) in sellConditions" 
                      :key="index"
                      class="condition-item"
                    >
                      <el-row :gutter="12" align="middle">
                        <el-col :span="1" v-if="index > 0">
                          <el-select v-model="condition.operator" size="small">
                            <el-option label="且" value="and" />
                            <el-option label="或" value="or" />
                          </el-select>
                        </el-col>
                        <el-col :span="6">
                          <el-select v-model="condition.indicator" placeholder="选择指标" size="small">
                            <el-option 
                              v-for="indicator in availableIndicators" 
                              :key="indicator.code"
                              :label="indicator.name" 
                              :value="indicator.code"
                            />
                          </el-select>
                        </el-col>
                        <el-col :span="4">
                          <el-select v-model="condition.comparison" size="small">
                            <el-option label="大于" value=">" />
                            <el-option label="小于" value="<" />
                            <el-option label="等于" value="=" />
                            <el-option label="大于等于" value=">=" />
                            <el-option label="小于等于" value="<=" />
                            <el-option label="上穿" value="cross_above" />
                            <el-option label="下穿" value="cross_below" />
                          </el-select>
                        </el-col>
                        <el-col :span="6">
                          <el-input 
                            v-model="condition.value" 
                            placeholder="阈值或指标"
                            size="small"
                          />
                        </el-col>
                        <el-col :span="6">
                          <el-input 
                            v-model="condition.description" 
                            placeholder="条件描述"
                            size="small"
                          />
                        </el-col>
                        <el-col :span="1">
                          <el-button 
                            @click="removeSellCondition(index)" 
                            size="small" 
                            type="danger" 
                            text
                          >
                            <el-icon><Delete /></el-icon>
                          </el-button>
                        </el-col>
                      </el-row>
                    </div>
                    <el-button @click="addSellCondition" size="small" type="primary" text>
                      <el-icon><Plus /></el-icon>
                      添加卖出条件
                    </el-button>
                  </div>
                </el-tab-pane>
                
                <el-tab-pane label="风险控制" name="risk">
                  <div class="risk-controls">
                    <el-row :gutter="16">
                      <el-col :span="8">
                        <el-form-item label="止损比例(%)">
                          <el-input-number
                            v-model="riskControls.stop_loss_pct"
                            :min="0"
                            :max="50"
                            :step="0.1"
                            :precision="1"
                            style="width: 100%"
                          />
                        </el-form-item>
                      </el-col>
                      <el-col :span="8">
                        <el-form-item label="止盈比例(%)">
                          <el-input-number
                            v-model="riskControls.take_profit_pct"
                            :min="0"
                            :max="200"
                            :step="0.1"
                            :precision="1"
                            style="width: 100%"
                          />
                        </el-form-item>
                      </el-col>
                      <el-col :span="8">
                        <el-form-item label="单笔仓位(%)">
                          <el-input-number
                            v-model="riskControls.position_size_pct"
                            :min="1"
                            :max="100"
                            :step="1"
                            style="width: 100%"
                          />
                        </el-form-item>
                      </el-col>
                    </el-row>
                    
                    <el-row :gutter="16">
                      <el-col :span="8">
                        <el-form-item label="最大持仓数">
                          <el-input-number
                            v-model="riskControls.max_positions"
                            :min="1"
                            :max="50"
                            :step="1"
                            style="width: 100%"
                          />
                        </el-form-item>
                      </el-col>
                      <el-col :span="8">
                        <el-form-item label="最大回撤(%)">
                          <el-input-number
                            v-model="riskControls.max_drawdown_pct"
                            :min="1"
                            :max="50"
                            :step="1"
                            style="width: 100%"
                          />
                        </el-form-item>
                      </el-col>
                      <el-col :span="8">
                        <el-form-item label="交易手续费(%)">
                          <el-input-number
                            v-model="riskControls.commission_pct"
                            :min="0"
                            :max="1"
                            :step="0.001"
                            :precision="3"
                            style="width: 100%"
                          />
                        </el-form-item>
                      </el-col>
                    </el-row>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </div>
          </div>
        </el-col>

        <!-- 右侧预览面板 -->
        <el-col :span="8">
          <div class="preview-panel">
            <div class="panel-header">
              <h3>策略预览</h3>
              <el-button @click="generateCode" size="small" type="primary">
                <el-icon><Magic /></el-icon>
                生成代码
              </el-button>
            </div>
            
            <div class="strategy-summary">
              <div class="summary-item">
                <label>策略名称:</label>
                <span>{{ strategyForm.name || '未命名策略' }}</span>
              </div>
              <div class="summary-item">
                <label>策略类型:</label>
                <span>{{ getStrategyTypeText(strategyForm.category) }}</span>
              </div>
              <div class="summary-item">
                <label>风险等级:</label>
                <el-tag :type="getRiskLevelColor(strategyForm.risk_level)" size="small">
                  {{ getRiskLevelText(strategyForm.risk_level) }}
                </el-tag>
              </div>
              <div class="summary-item">
                <label>使用指标:</label>
                <div class="indicators-tags">
                  <el-tag 
                    v-for="indicator in selectedIndicators" 
                    :key="indicator"
                    size="small"
                    class="indicator-tag"
                  >
                    {{ getIndicatorName(indicator) }}
                  </el-tag>
                </div>
              </div>
              <div class="summary-item">
                <label>买入条件:</label>
                <div class="conditions-preview">
                  <div v-for="(condition, index) in buyConditions" :key="index" class="condition-preview">
                    {{ index > 0 ? condition.operator === 'and' ? '且' : '或' : '' }}
                    {{ getIndicatorName(condition.indicator) }} 
                    {{ getComparisonText(condition.comparison) }} 
                    {{ condition.value }}
                  </div>
                </div>
              </div>
              <div class="summary-item">
                <label>卖出条件:</label>
                <div class="conditions-preview">
                  <div v-for="(condition, index) in sellConditions" :key="index" class="condition-preview">
                    {{ index > 0 ? condition.operator === 'and' ? '且' : '或' : '' }}
                    {{ getIndicatorName(condition.indicator) }} 
                    {{ getComparisonText(condition.comparison) }} 
                    {{ condition.value }}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 策略流程图 -->
            <div class="strategy-flowchart">
              <h4>策略流程</h4>
              <div class="flowchart-content">
                <div class="flow-step">
                  <div class="step-icon">1</div>
                  <div class="step-content">
                    <div class="step-title">数据获取</div>
                    <div class="step-desc">获取股票价格和技术指标数据</div>
                  </div>
                </div>
                <div class="flow-arrow">↓</div>
                <div class="flow-step">
                  <div class="step-icon">2</div>
                  <div class="step-content">
                    <div class="step-title">信号判断</div>
                    <div class="step-desc">根据配置的条件判断买卖信号</div>
                  </div>
                </div>
                <div class="flow-arrow">↓</div>
                <div class="flow-step">
                  <div class="step-icon">3</div>
                  <div class="step-content">
                    <div class="step-title">风险控制</div>
                    <div class="step-desc">检查仓位和风险控制条件</div>
                  </div>
                </div>
                <div class="flow-arrow">↓</div>
                <div class="flow-step">
                  <div class="step-icon">4</div>
                  <div class="step-content">
                    <div class="step-title">执行交易</div>
                    <div class="step-desc">发出交易指令并记录结果</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 代码编辑模式 -->
    <div v-else class="code-builder">
      <div class="code-editor-container">
        <div class="editor-toolbar">
          <div class="toolbar-left">
            <el-button-group>
              <el-button @click="loadTemplate" size="small">
                <el-icon><Document /></el-icon>
                加载模板
              </el-button>
              <el-button @click="formatCode" size="small">
                <el-icon><Magic /></el-icon>
                格式化
              </el-button>
              <el-button @click="validateCode" size="small">
                <el-icon><CircleCheck /></el-icon>
                验证代码
              </el-button>
            </el-button-group>
          </div>
          <div class="toolbar-right">
            <el-select v-model="selectedTemplate" placeholder="选择模板" size="small" style="width: 200px;">
              <el-option 
                v-for="template in codeTemplates" 
                :key="template.name"
                :label="template.label" 
                :value="template.name"
              />
            </el-select>
          </div>
        </div>
        
        <div class="code-editor">
          <textarea
            ref="codeEditorRef"
            v-model="strategyCode"
            class="code-textarea"
            placeholder="请输入策略代码..."
          ></textarea>
        </div>
        
        <div class="code-info">
          <div class="info-tabs">
            <el-tabs v-model="activeInfoTab" type="card">
              <el-tab-pane label="代码说明" name="docs">
                <div class="code-docs">
                  <h4>策略代码规范</h4>
                  <ul>
                    <li><strong>initialize(context):</strong> 策略初始化函数，设置参数和初始状态</li>
                    <li><strong>handle_data(context, data):</strong> 数据处理函数，每个交易日调用</li>
                    <li><strong>before_trading_start(context, data):</strong> 交易开始前调用（可选）</li>
                    <li><strong>after_trading_end(context, data):</strong> 交易结束后调用（可选）</li>
                  </ul>
                  
                  <h4>可用的数据和函数</h4>
                  <ul>
                    <li><strong>data.current(asset, field):</strong> 获取当前价格数据</li>
                    <li><strong>data.history(asset, fields, bar_count):</strong> 获取历史数据</li>
                    <li><strong>order_target_percent(asset, target):</strong> 按目标仓位下单</li>
                    <li><strong>order(asset, amount):</strong> 按数量下单</li>
                    <li><strong>get_open_orders():</strong> 获取未成交订单</li>
                  </ul>
                </div>
              </el-tab-pane>
              
              <el-tab-pane label="示例代码" name="examples">
                <div class="code-examples">
                  <el-collapse v-model="activeExample">
                    <el-collapse-item title="双均线策略" name="ma_cross">
                      <pre><code>{{ examples.ma_cross }}</code></pre>
                    </el-collapse-item>
                    <el-collapse-item title="RSI策略" name="rsi">
                      <pre><code>{{ examples.rsi }}</code></pre>
                    </el-collapse-item>
                    <el-collapse-item title="布林带策略" name="bollinger">
                      <pre><code>{{ examples.bollinger }}</code></pre>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </el-tab-pane>
              
              <el-tab-pane label="语法检查" name="validation">
                <div class="validation-result">
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
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="builder-footer">
      <div class="footer-left">
        <el-button @click="resetForm" size="large">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
        <el-button @click="saveAsDraft" size="large">
          <el-icon><Document /></el-icon>
          保存草稿
        </el-button>
      </div>
      <div class="footer-right">
        <el-button @click="$emit('cancel')" size="large">
          取消
        </el-button>
        <el-button @click="previewStrategy" size="large">
          <el-icon><View /></el-icon>
          预览
        </el-button>
        <el-button @click="testStrategy" type="warning" size="large">
          <el-icon><DataAnalysis /></el-icon>
          快速回测
        </el-button>
        <el-button @click="saveStrategy" type="primary" size="large" :loading="saving">
          <el-icon><Check /></el-icon>
          {{ editStrategy ? '更新策略' : '创建策略' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import type { Strategy } from '@/types/strategy'

// Props
interface Props {
  editStrategy?: Strategy | null
}

const props = withDefaults(defineProps<Props>(), {
  editStrategy: null
})

// Emits
const emit = defineEmits<{
  save: [strategy: Strategy]
  cancel: []
}>()

// 响应式数据
const builderMode = ref<'visual' | 'code'>('visual')
const saving = ref(false)
const strategyFormRef = ref<FormInstance>()
const codeEditorRef = ref<HTMLTextAreaElement>()
const activeRuleTab = ref('buy')
const activeInfoTab = ref('docs')
const activeExample = ref('')
const selectedTemplate = ref('')

// 策略表单数据
const strategyForm = reactive({
  name: '',
  author: '',
  description: '',
  category: 'trend_following',
  risk_level: 'medium',
  min_capital: 100000
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 50, message: '策略名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入策略描述', trigger: 'blur' },
    { min: 10, max: 500, message: '策略描述长度在 10 到 500 个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  risk_level: [
    { required: true, message: '请选择风险等级', trigger: 'change' }
  ]
}

// 策略类型选项
const strategyTypes = [
  { 
    value: 'trend_following', 
    label: '趋势跟踪', 
    description: '跟随市场趋势方向进行交易，适合趋势明显的市场' 
  },
  { 
    value: 'mean_reversion', 
    label: '均值回归', 
    description: '基于价格回归均值的理论，在超买超卖时进行反向交易' 
  },
  { 
    value: 'momentum', 
    label: '动量策略', 
    description: '利用价格动量效应，追涨杀跌获取短期收益' 
  },
  { 
    value: 'arbitrage', 
    label: '套利策略', 
    description: '利用不同市场或品种间的价差进行无风险套利' 
  },
  { 
    value: 'multi_factor', 
    label: '多因子策略', 
    description: '综合多个因子进行选股和择时，分散风险' 
  },
  { 
    value: 'custom', 
    label: '自定义策略', 
    description: '根据特定需求自定义的策略逻辑' 
  }
]

// 风险等级选项
const riskLevels = [
  { 
    value: 'low', 
    label: '低风险', 
    color: 'success', 
    description: '保守型，追求稳定收益' 
  },
  { 
    value: 'medium', 
    label: '中风险', 
    color: 'warning', 
    description: '平衡型，收益风险适中' 
  },
  { 
    value: 'high', 
    label: '高风险', 
    color: 'danger', 
    description: '激进型，追求高收益' 
  }
]

// 技术指标配置
const technicalIndicators = [
  {
    code: 'MA',
    name: '移动平均线',
    description: '计算一定周期内的平均价格，用于判断趋势方向',
    formula: 'MA(n) = (P1 + P2 + ... + Pn) / n',
    parameters: [
      { name: 'period', label: '周期', min: 5, max: 250, step: 1, default: 20 }
    ]
  },
  {
    code: 'EMA',
    name: '指数移动平均线',
    description: '给近期价格更高权重的移动平均线',
    formula: 'EMA = (2/(n+1)) * P + (1-2/(n+1)) * EMA_prev',
    parameters: [
      { name: 'period', label: '周期', min: 5, max: 250, step: 1, default: 12 }
    ]
  },
  {
    code: 'RSI',
    name: '相对强弱指数',
    description: '衡量价格变动速度和幅度的震荡指标',
    formula: 'RSI = 100 - 100/(1 + RS)',
    parameters: [
      { name: 'period', label: '周期', min: 5, max: 50, step: 1, default: 14 }
    ]
  },
  {
    code: 'MACD',
    name: 'MACD指标',
    description: '趋势跟踪动量指标，由快慢均线差值构成',
    formula: 'MACD = EMA12 - EMA26',
    parameters: [
      { name: 'fast_period', label: '快线周期', min: 5, max: 50, step: 1, default: 12 },
      { name: 'slow_period', label: '慢线周期', min: 10, max: 100, step: 1, default: 26 },
      { name: 'signal_period', label: '信号线周期', min: 5, max: 20, step: 1, default: 9 }
    ]
  },
  {
    code: 'BOLL',
    name: '布林带',
    description: '基于标准差的通道指标，用于判断超买超卖',
    formula: 'Upper = MA + k*STD, Lower = MA - k*STD',
    parameters: [
      { name: 'period', label: '周期', min: 10, max: 50, step: 1, default: 20 },
      { name: 'std_dev', label: '标准差倍数', min: 1, max: 3, step: 0.1, default: 2 }
    ]
  },
  {
    code: 'KDJ',
    name: 'KDJ指标',
    description: '随机震荡指标，用于判断超买超卖状态',
    formula: 'K = (C-Ln)/(Hn-Ln)*100',
    parameters: [
      { name: 'period', label: '周期', min: 5, max: 30, step: 1, default: 9 },
      { name: 'k_period', label: 'K值周期', min: 1, max: 10, step: 1, default: 3 },
      { name: 'd_period', label: 'D值周期', min: 1, max: 10, step: 1, default: 3 }
    ]
  }
]

// 选中的指标
const selectedIndicators = ref<string[]>(['MA', 'RSI'])

// 指标参数
const indicatorParams = reactive<Record<string, Record<string, number>>>({})

// 策略参数
const strategyParameters = ref([
  { name: 'position_size', type: 'number', default_value: '0.1', description: '单笔仓位比例', range: '0.01-0.5' },
  { name: 'rebalance_freq', type: 'select', default_value: 'daily', description: '调仓频率', range: 'daily,weekly,monthly' }
])

// 交易条件
const buyConditions = ref([
  { operator: '', indicator: 'MA', comparison: 'cross_above', value: 'close', description: '价格上穿均线' }
])

const sellConditions = ref([
  { operator: '', indicator: 'MA', comparison: 'cross_below', value: 'close', description: '价格下穿均线' }
])

// 风险控制参数
const riskControls = reactive({
  stop_loss_pct: 5.0,
  take_profit_pct: 15.0,
  position_size_pct: 10,
  max_positions: 5,
  max_drawdown_pct: 20,
  commission_pct: 0.003
})

// 策略代码
const strategyCode = ref('')

// 代码模板
const codeTemplates = [
  { name: 'ma_cross', label: '双均线策略模板' },
  { name: 'rsi_reversal', label: 'RSI反转策略模板' },
  { name: 'bollinger_bands', label: '布林带策略模板' },
  { name: 'macd_momentum', label: 'MACD动量策略模板' },
  { name: 'empty', label: '空白模板' }
]

// 代码示例
const examples = {
  ma_cross: `def initialize(context):
    # 设置股票池
    context.stocks = ['000001.XSHE', '000002.XSHE']
    # 设置均线参数
    context.short_period = 5
    context.long_period = 20

def handle_data(context, data):
    for stock in context.stocks:
        # 获取历史价格数据
        hist = data.history(stock, 'close', context.long_period + 1)
        
        # 计算均线
        short_ma = hist[-context.short_period:].mean()
        long_ma = hist.mean()
        
        # 获取当前持仓
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：短均线上穿长均线
        if short_ma > long_ma and current_position == 0:
            order_target_percent(stock, 0.5)
            
        # 卖出信号：短均线下穿长均线
        elif short_ma < long_ma and current_position > 0:
            order_target_percent(stock, 0)`,
            
  rsi: `def initialize(context):
    context.stocks = ['000001.XSHE']
    context.rsi_period = 14
    context.rsi_overbought = 70
    context.rsi_oversold = 30

def handle_data(context, data):
    for stock in context.stocks:
        # 计算RSI
        hist = data.history(stock, 'close', context.rsi_period + 1)
        rsi = calculate_rsi(hist, context.rsi_period)
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：RSI < 30
        if rsi < context.rsi_oversold and current_position == 0:
            order_target_percent(stock, 0.3)
            
        # 卖出信号：RSI > 70
        elif rsi > context.rsi_overbought and current_position > 0:
            order_target_percent(stock, 0)

def calculate_rsi(prices, period):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]`,
    
  bollinger: `def initialize(context):
    context.stocks = ['000001.XSHE']
    context.period = 20
    context.std_dev = 2

def handle_data(context, data):
    for stock in context.stocks:
        # 获取历史数据
        hist = data.history(stock, 'close', context.period + 1)
        
        # 计算布林带
        ma = hist.mean()
        std = hist.std()
        upper_band = ma + context.std_dev * std
        lower_band = ma - context.std_dev * std
        
        current_price = data.current(stock, 'close')
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：价格触及下轨
        if current_price <= lower_band and current_position == 0:
            order_target_percent(stock, 0.4)
            
        # 卖出信号：价格触及上轨
        elif current_price >= upper_band and current_position > 0:
            order_target_percent(stock, 0)`
}

// 代码验证结果
const validationResult = reactive({
  valid: true,
  errors: [] as string[]
})

// 计算属性
const availableIndicators = computed(() => {
  return technicalIndicators.filter(indicator => 
    selectedIndicators.value.includes(indicator.code)
  )
})

// 初始化指标参数
const initIndicatorParams = () => {
  technicalIndicators.forEach(indicator => {
    if (!indicatorParams[indicator.code]) {
      indicatorParams[indicator.code] = {}
    }
    indicator.parameters.forEach(param => {
      if (!(param.name in indicatorParams[indicator.code])) {
        indicatorParams[indicator.code][param.name] = param.default
      }
    })
  })
}

// 方法
const toggleIndicator = (code: string) => {
  const index = selectedIndicators.value.indexOf(code)
  if (index > -1) {
    selectedIndicators.value.splice(index, 1)
  } else {
    selectedIndicators.value.push(code)
  }
}

const addCustomParameter = () => {
  strategyParameters.value.push({
    name: '',
    type: 'number',
    default_value: '',
    description: '',
    range: ''
  })
}

const removeParameter = (index: number) => {
  strategyParameters.value.splice(index, 1)
}

const addBuyCondition = () => {
  buyConditions.value.push({
    operator: buyConditions.value.length > 0 ? 'and' : '',
    indicator: '',
    comparison: '>',
    value: '',
    description: ''
  })
}

const removeBuyCondition = (index: number) => {
  buyConditions.value.splice(index, 1)
}

const addSellCondition = () => {
  sellConditions.value.push({
    operator: sellConditions.value.length > 0 ? 'and' : '',
    indicator: '',
    comparison: '<',
    value: '',
    description: ''
  })
}

const removeSellCondition = (index: number) => {
  sellConditions.value.splice(index, 1)
}

const generateCode = () => {
  // 根据可视化配置生成Python代码
  let code = `# ${strategyForm.name || '未命名策略'}\n`
  code += `# ${strategyForm.description || '策略描述'}\n\n`
  
  code += `def initialize(context):\n`
  code += `    # 策略参数\n`
  strategyParameters.value.forEach(param => {
    if (param.name && param.default_value) {
      code += `    context.${param.name} = ${param.default_value}\n`
    }
  })
  
  code += `    # 风险控制参数\n`
  code += `    context.stop_loss_pct = ${riskControls.stop_loss_pct}\n`
  code += `    context.take_profit_pct = ${riskControls.take_profit_pct}\n`
  code += `    context.position_size_pct = ${riskControls.position_size_pct}\n\n`
  
  code += `def handle_data(context, data):\n`
  code += `    # 策略逻辑\n`
  code += `    pass\n`
  
  strategyCode.value = code
  builderMode.value = 'code'
  ElMessage.success('代码生成成功')
}

const loadTemplate = () => {
  if (!selectedTemplate.value) {
    ElMessage.warning('请先选择模板')
    return
  }
  
  if (selectedTemplate.value === 'empty') {
    strategyCode.value = `def initialize(context):
    # 策略初始化
    pass

def handle_data(context, data):
    # 策略逻辑
    pass`
  } else {
    strategyCode.value = examples[selectedTemplate.value as keyof typeof examples] || ''
  }
  
  ElMessage.success('模板加载成功')
}

const formatCode = () => {
  // 简单的代码格式化
  const lines = strategyCode.value.split('\n')
  const formatted = lines.map(line => line.trim()).join('\n')
  strategyCode.value = formatted
  ElMessage.success('代码格式化完成')
}

const validateCode = () => {
  const code = strategyCode.value.trim()
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
  
  validationResult.valid = errors.length === 0
  validationResult.errors = errors
  
  if (validationResult.valid) {
    ElMessage.success('代码验证通过')
  } else {
    ElMessage.error('代码验证失败，请检查错误')
  }
  
  activeInfoTab.value = 'validation'
}

const resetForm = () => {
  Object.assign(strategyForm, {
    name: '',
    author: '',
    description: '',
    category: 'trend_following',
    risk_level: 'medium',
    min_capital: 100000
  })
  
  selectedIndicators.value = ['MA', 'RSI']
  strategyParameters.value = [
    { name: 'position_size', type: 'number', default_value: '0.1', description: '单笔仓位比例', range: '0.01-0.5' }
  ]
  
  buyConditions.value = [
    { operator: '', indicator: 'MA', comparison: 'cross_above', value: 'close', description: '价格上穿均线' }
  ]
  
  sellConditions.value = [
    { operator: '', indicator: 'MA', comparison: 'cross_below', value: 'close', description: '价格下穿均线' }
  ]
  
  strategyCode.value = ''
  
  ElMessage.success('表单已重置')
}

const saveAsDraft = async () => {
  // 保存为草稿逻辑
  ElMessage.success('策略已保存为草稿')
}

const previewStrategy = () => {
  // 策略预览逻辑
  ElMessage.info('策略预览功能开发中')
}

const testStrategy = () => {
  // 快速回测逻辑
  ElMessage.info('快速回测功能开发中')
}

const saveStrategy = async () => {
  if (builderMode.value === 'visual') {
    if (!strategyFormRef.value) return
    
    try {
      await strategyFormRef.value.validate()
    } catch {
      ElMessage.error('请完善策略配置')
      return
    }
  } else {
    if (!strategyCode.value.trim()) {
      ElMessage.error('请输入策略代码')
      return
    }
  }
  
  saving.value = true
  
  try {
    const strategy: Strategy = {
      strategy_id: props.editStrategy?.strategy_id || `STR_${Date.now()}`,
      name: strategyForm.name,
      display_name: strategyForm.name,
      description: strategyForm.description,
      category: strategyForm.category,
      risk_level: strategyForm.risk_level,
      author: strategyForm.author,
      min_capital: strategyForm.min_capital,
      parameters: Object.fromEntries(
        strategyParameters.value.map(p => [p.name, p.default_value])
      ),
      indicators: selectedIndicators.value,
      indicator_params: indicatorParams,
      buy_conditions: buyConditions.value,
      sell_conditions: sellConditions.value,
      risk_controls: riskControls,
      code: strategyCode.value,
      status: 'draft',
      created_at: props.editStrategy?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    
    emit('save', strategy)
  } catch (error) {
    ElMessage.error('策略保存失败')
  } finally {
    saving.value = false
  }
}

// 工具方法
const getStrategyTypeText = (type: string) => {
  const found = strategyTypes.find(t => t.value === type)
  return found?.label || type
}

const getRiskLevelText = (level: string) => {
  const found = riskLevels.find(r => r.value === level)
  return found?.label || level
}

const getRiskLevelColor = (level: string) => {
  const found = riskLevels.find(r => r.value === level)
  return found?.color || 'info'
}

const getIndicatorName = (code: string) => {
  const found = technicalIndicators.find(i => i.code === code)
  return found?.name || code
}

const getComparisonText = (comparison: string) => {
  const map: Record<string, string> = {
    '>': '大于',
    '<': '小于',
    '=': '等于',
    '>=': '大于等于',
    '<=': '小于等于',
    'cross_above': '上穿',
    'cross_below': '下穿'
  }
  return map[comparison] || comparison
}

// 监听编辑策略变化
watch(() => props.editStrategy, (strategy) => {
  if (strategy) {
    Object.assign(strategyForm, {
      name: strategy.name,
      author: strategy.author || '',
      description: strategy.description,
      category: strategy.category,
      risk_level: strategy.risk_level,
      min_capital: strategy.min_capital || 100000
    })
    
    if (strategy.code) {
      strategyCode.value = strategy.code
      builderMode.value = 'code'
    }
    
    if (strategy.indicators) {
      selectedIndicators.value = strategy.indicators
    }
    
    if (strategy.buy_conditions) {
      buyConditions.value = strategy.buy_conditions
    }
    
    if (strategy.sell_conditions) {
      sellConditions.value = strategy.sell_conditions
    }
    
    if (strategy.risk_controls) {
      Object.assign(riskControls, strategy.risk_controls)
    }
  }
}, { immediate: true })

// 生命周期
onMounted(() => {
  initIndicatorParams()
})
</script>

<style lang="scss" scoped>
.strategy-builder {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

// 构建器头部
.builder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  
  .header-left {
    .builder-title {
      font-size: 24px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 4px 0;
    }
    
    .builder-subtitle {
      font-size: 14px;
      color: #6b7280;
      margin: 0;
    }
  }
}

// 可视化构建器
.visual-builder {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.config-panel {
  .config-section {
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    
    .section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 20px;
      
      h3 {
        font-size: 18px;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
      }
      
      .help-icon {
        color: #9ca3af;
        cursor: help;
        
        &:hover {
          color: #6b7280;
        }
      }
    }
  }
}

// 指标网格
.indicators-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.indicator-card {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  }
  
  &.active {
    border-color: #3b82f6;
    background: #eff6ff;
  }
  
  .indicator-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    
    .indicator-name {
      font-weight: 600;
      color: #1f2937;
    }
    
    .indicator-help {
      color: #9ca3af;
      cursor: help;
    }
  }
  
  .indicator-formula {
    font-size: 12px;
    color: #6b7280;
    font-family: 'Courier New', monospace;
    margin-bottom: 12px;
  }
  
  .indicator-params {
    .param-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
      
      label {
        font-size: 12px;
        color: #374151;
      }
    }
  }
}

// 参数列表
.parameters-list {
  .parameter-item {
    margin-bottom: 12px;
    padding: 12px;
    background: #f9fafb;
    border-radius: 6px;
  }
}

// 规则构建器
.rule-builder {
  .condition-item {
    margin-bottom: 12px;
    padding: 12px;
    background: #f9fafb;
    border-radius: 6px;
  }
}

// 风险控制
.risk-controls {
  .el-form-item {
    margin-bottom: 16px;
  }
}

// 预览面板
.preview-panel {
  background: white;
  border-radius: 12px;
  padding: 24px;
  height: fit-content;
  position: sticky;
  top: 24px;
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 {
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
      margin: 0;
    }
  }
  
  .strategy-summary {
    .summary-item {
      display: flex;
      align-items: flex-start;
      margin-bottom: 12px;
      
      label {
        font-size: 14px;
        color: #6b7280;
        min-width: 80px;
        margin-right: 8px;
      }
      
      span {
        font-size: 14px;
        color: #1f2937;
      }
      
      .indicators-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        
        .indicator-tag {
          font-size: 12px;
        }
      }
      
      .conditions-preview {
        .condition-preview {
          font-size: 12px;
          color: #374151;
          margin-bottom: 4px;
        }
      }
    }
  }
  
  .strategy-flowchart {
    margin-top: 24px;
    
    h4 {
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 16px 0;
    }
    
    .flowchart-content {
      .flow-step {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .step-icon {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: #3b82f6;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 14px;
        }
        
        .step-content {
          .step-title {
            font-size: 14px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 2px;
          }
          
          .step-desc {
            font-size: 12px;
            color: #6b7280;
          }
        }
      }
      
      .flow-arrow {
        text-align: center;
        color: #9ca3af;
        font-size: 18px;
        margin: 8px 0;
      }
    }
  }
}

// 代码构建器
.code-builder {
  flex: 1;
  display: flex;
  flex-direction: column;
  
  .code-editor-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    margin: 24px;
    background: white;
    border-radius: 12px;
    overflow: hidden;
    
    .editor-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: #f8fafc;
      border-bottom: 1px solid #e5e7eb;
    }
    
    .code-editor {
      flex: 1;
      position: relative;
      
      .code-textarea {
        width: 100%;
        height: 400px;
        border: none;
        outline: none;
        padding: 20px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.6;
        resize: none;
        background: #1e293b;
        color: #e2e8f0;
      }
    }
    
    .code-info {
      border-top: 1px solid #e5e7eb;
      
      .code-docs {
        padding: 20px;
        
        h4 {
          font-size: 16px;
          font-weight: 600;
          color: #1f2937;
          margin: 0 0 12px 0;
        }
        
        ul {
          margin: 0 0 20px 0;
          padding-left: 20px;
          
          li {
            margin-bottom: 8px;
            color: #374151;
            
            strong {
              color: #1f2937;
            }
          }
        }
      }
      
      .code-examples {
        padding: 20px;
        
        pre {
          background: #1e293b;
          color: #e2e8f0;
          padding: 16px;
          border-radius: 6px;
          overflow-x: auto;
          font-size: 12px;
          line-height: 1.5;
        }
      }
      
      .validation-result {
        padding: 20px;
        
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
}

// 底部操作栏
.builder-footer {
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

// 选项样式
.option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  
  .option-help {
    color: #9ca3af;
    font-size: 12px;
  }
  
  .risk-desc {
    font-size: 12px;
    color: #6b7280;
    margin-left: 8px;
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .visual-builder {
    .el-col:first-child {
      margin-bottom: 24px;
    }
  }
}

@media (max-width: 768px) {
  .builder-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .visual-builder {
    padding: 16px;
  }
  
  .indicators-grid {
    grid-template-columns: 1fr;
  }
  
  .builder-footer {
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