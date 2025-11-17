<template>
  <div class="model-tester">
    <el-row :gutter="20">
      <!-- 测试配置面板 -->
      <el-col :span="8">
        <div class="test-config-panel">
          <div class="panel-header">
            <h3>测试配置</h3>
          </div>
          
          <el-form :model="testConfig" label-width="100px" class="test-form">
            <!-- 测试类型 -->
            <el-form-item label="测试类型">
              <el-radio-group v-model="testConfig.testType" @change="handleTestTypeChange">
                <el-radio-button label="single">单模型测试</el-radio-button>
                <el-radio-button label="ensemble">组合测试</el-radio-button>
              </el-radio-group>
            </el-form-item>
            
            <!-- 模型选择 -->
            <el-form-item v-if="testConfig.testType === 'single'" label="选择模型">
              <el-select
                v-model="testConfig.modelId"
                placeholder="请选择要测试的模型"
                style="width: 100%"
                filterable
                @change="handleModelChange"
              >
                <el-option
                  v-for="model in availableModels"
                  :key="model.model_id"
                  :label="`${model.name} (${model.model_id})`"
                  :value="model.model_id"
                >
                  <div class="model-option">
                    <span>{{ model.name }}</span>
                    <el-tag size="small" :type="getModelTypeColor(model.model_type)">
                      {{ getModelTypeText(model.model_type) }}
                    </el-tag>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <!-- 组合选择 -->
            <el-form-item v-if="testConfig.testType === 'ensemble'" label="选择组合">
              <el-select
                v-model="testConfig.ensembleId"
                placeholder="请选择要测试的组合"
                style="width: 100%"
                filterable
                @change="handleEnsembleChange"
              >
                <el-option
                  v-for="ensemble in availableEnsembles"
                  :key="ensemble.ensemble_id"
                  :label="`${ensemble.name} (${ensemble.ensemble_id})`"
                  :value="ensemble.ensemble_id"
                >
                  <div class="ensemble-option">
                    <span>{{ ensemble.name }}</span>
                    <el-text size="small" type="info">
                      {{ ensemble.model_count }}个模型
                    </el-text>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <!-- 测试名称 -->
            <el-form-item label="测试名称">
              <el-input
                v-model="testConfig.testName"
                placeholder="请输入测试名称（可选）"
                maxlength="100"
              />
            </el-form-item>
            
            <!-- 期望输出 -->
            <el-form-item label="期望输出">
              <el-input
                v-model="testConfig.expectedOutput"
                type="textarea"
                :rows="3"
                placeholder="请输入期望的输出结果（用于准确率计算）"
                maxlength="1000"
              />
            </el-form-item>
            
            <!-- 测试描述 -->
            <el-form-item label="测试描述">
              <el-input
                v-model="testConfig.testDescription"
                type="textarea"
                :rows="2"
                placeholder="请输入测试描述（可选）"
                maxlength="500"
              />
            </el-form-item>
            
            <!-- 流式显示开关 -->
            <el-form-item label="显示效果">
              <el-switch
                v-model="testConfig.enableStreaming"
                active-text="流式显示"
                inactive-text="直接显示"
                size="small"
              />
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 历史测试记录 -->
        <div class="test-history-panel">
          <div class="panel-header">
            <h4>测试历史</h4>
            <el-button size="small" @click="loadTestHistory" :loading="loadingHistory">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          
          <div class="history-list">
            <div
              v-for="record in testHistory"
              :key="record.test_id"
              class="history-item"
              @click="loadHistoryTest(record)"
            >
              <div class="history-header">
                <el-text class="test-name" truncated>
                  {{ record.test_name || '未命名测试' }}
                </el-text>
                <el-tag
                  size="small"
                  :type="record.success ? 'success' : 'danger'"
                >
                  {{ record.success ? '成功' : '失败' }}
                </el-tag>
              </div>
              <div class="history-info">
                <el-text size="small" type="info">
                  {{ formatDateTime(record.timestamp) }}
                </el-text>
                <el-text size="small" v-if="record.response_time">
                  {{ record.response_time.toFixed(2) }}s
                </el-text>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      
      <!-- 对话测试区域 -->
      <el-col :span="16">
        <div class="chat-test-panel">
          <div class="panel-header">
            <h3>对话测试</h3>
            <div class="header-actions">
              <el-button @click="clearChat">
                <el-icon><Delete /></el-icon>
                清空对话
              </el-button>
              <el-button
                type="primary"
                @click="runTest"
                :loading="testing"
                :disabled="!canTest"
              >
                <el-icon><ChatDotRound /></el-icon>
                {{ testing ? '测试中...' : '开始测试' }}
              </el-button>
            </div>
          </div>
          
          <!-- 对话区域 -->
          <div class="chat-area" ref="chatAreaRef">
            <div
              v-for="(message, index) in chatMessages"
              :key="index"
              class="chat-message"
              :class="message.type"
            >
              <div class="message-header">
                <div class="message-sender">
                  <el-icon v-if="message.type === 'user'">
                    <User />
                  </el-icon>
                  <el-icon v-else>
                    <ChatDotRound />
                  </el-icon>
                  <span>{{ message.type === 'user' ? '用户' : '模型' }}</span>
                </div>
                <div class="message-meta">
                  <el-text size="small" type="info">
                    {{ formatDateTime(message.timestamp) }}
                  </el-text>
                  <el-text v-if="message.responseTime" size="small" type="info">
                    {{ message.responseTime.toFixed(2) }}s
                  </el-text>
                </div>
              </div>
              
              <div class="message-content">
                <div class="message-text">{{ message.content }}</div>
                
                <!-- 测试结果信息 -->
                <div v-if="message.testResult" class="test-result-info">
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="测试状态">
                      <el-tag
                        size="small"
                        :type="message.testResult.success ? 'success' : 'danger'"
                      >
                        {{ message.testResult.success ? '成功' : '失败' }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="响应时间">
                      {{ message.testResult.response_time ? message.testResult.response_time.toFixed(2) : '0.00' }}s
                    </el-descriptions-item>
                    <el-descriptions-item
                      v-if="message.testResult.accuracy_score !== undefined"
                      label="准确率"
                    >
                      {{ (message.testResult.accuracy_score * 100).toFixed(1) }}%
                    </el-descriptions-item>
                    <el-descriptions-item
                      v-if="message.testResult.similarity_score !== undefined"
                      label="相似度"
                    >
                      {{ (message.testResult.similarity_score * 100).toFixed(1) }}%
                    </el-descriptions-item>
                    <el-descriptions-item
                      v-if="message.testResult.token_count"
                      label="Token数"
                    >
                      {{ message.testResult.token_count }}
                    </el-descriptions-item>
                    <el-descriptions-item
                      v-if="message.testResult.error_message"
                      label="错误信息"
                      :span="2"
                    >
                      <el-text type="danger" size="small">
                        {{ message.testResult.error_message }}
                      </el-text>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-if="chatMessages.length === 0" class="empty-chat">
              <el-empty description="开始您的模型测试对话">
                <el-button type="primary" @click="focusInput">
                  开始测试
                </el-button>
              </el-empty>
            </div>
          </div>
          
          <!-- 输入区域 -->
          <div class="input-area">
            <el-input
              ref="inputRef"
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="请输入要测试的消息..."
              maxlength="2000"
              show-word-limit
              @keydown.ctrl.enter="runTest"
            />
            <div class="input-actions">
              <el-text size="small" type="info">
                Ctrl + Enter 快速发送
              </el-text>
              <el-button
                type="primary"
                @click="runTest"
                :loading="testing"
                :disabled="!canTest"
              >
                发送测试
              </el-button>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { formatDateTime } from '../../utils/format'
import {
  modelManagementAPI,
  type AIModel,
  type ModelEnsemble,
  type TestResult,
  ModelType
} from '../../api/model-management'

// 响应式数据
const testing = ref(false)
const loadingHistory = ref(false)

const availableModels = ref<AIModel[]>([])
const availableEnsembles = ref<ModelEnsemble[]>([])
const testHistory = ref<TestResult[]>([])

const chatAreaRef = ref<HTMLElement>()
const inputRef = ref()

const inputMessage = ref('')

// 测试配置
const testConfig = ref({
  testType: 'single' as 'single' | 'ensemble',
  modelId: '',
  ensembleId: '',
  testName: '',
  expectedOutput: '',
  testDescription: '',
  enableStreaming: false // 添加流式显示开关
})

// 聊天消息
interface ChatMessage {
  type: 'user' | 'assistant'
  content: string
  timestamp: string
  responseTime?: number
  testResult?: TestResult
  isStreaming?: boolean
  fullContent?: string
}

const chatMessages = ref<ChatMessage[]>([])

// 计算属性
const canTest = computed(() => {
  const hasInput = inputMessage.value.trim().length > 0
  const hasTarget = testConfig.value.testType === 'single' 
    ? testConfig.value.modelId 
    : testConfig.value.ensembleId
  
  return hasInput && hasTarget && !testing.value
})

// 方法
const getModelTypeText = (type: ModelType) => {
  const typeMap = {
    [ModelType.DEEPSEEK]: 'DeepSeek',
    [ModelType.OPENAI]: 'OpenAI',
    [ModelType.CLAUDE]: 'Claude',
    [ModelType.CUSTOM]: '自定义'
  }
  return typeMap[type] || type
}

const getModelTypeColor = (type: ModelType) => {
  const colorMap = {
    [ModelType.DEEPSEEK]: 'primary',
    [ModelType.OPENAI]: 'success',
    [ModelType.CLAUDE]: 'warning',
    [ModelType.CUSTOM]: 'info'
  }
  return colorMap[type] || 'info'
}

// 加载可用模型
const loadAvailableModels = async () => {
  try {
    const response = await modelManagementAPI.getModels({ per_page: 100 })
    
    if (response.success && response.data) {
      availableModels.value = response.data.items.filter(model => model.enabled)
    }
  } catch (error) {
    console.error('加载可用模型失败:', error)
  }
}

// 加载可用组合
const loadAvailableEnsembles = async () => {
  try {
    const response = await modelManagementAPI.getEnsembles({ per_page: 100 })
    
    if (response.success && response.data) {
      availableEnsembles.value = response.data.items.filter(ensemble => ensemble.enabled)
    }
  } catch (error) {
    console.error('加载可用组合失败:', error)
  }
}

// 加载测试历史
const loadTestHistory = async () => {
  loadingHistory.value = true
  try {
    // 获取所有模型的测试记录，不限制特定模型
    console.log('正在加载所有测试历史记录...')
    
    // 如果有选择的模型，优先显示该模型的记录
    const targetId = testConfig.value.testType === 'single' 
      ? testConfig.value.modelId 
      : testConfig.value.ensembleId

    if (targetId) {
      console.log('加载指定模型/组合的测试历史，ID:', targetId)
      const response = await modelManagementAPI.getTestRecords(targetId, {
        per_page: 20
      })
      
      console.log('测试历史响应:', response)
      
      if (response.success && response.data) {
        testHistory.value = response.data.items || []
        console.log('加载到测试历史记录数量:', testHistory.value.length)
      } else {
        console.warn('获取测试历史失败:', response.message)
        testHistory.value = []
      }
    } else {
      // 没有选择模型时，尝试加载第一个可用模型的记录
      if (availableModels.value.length > 0) {
        const firstModelId = availableModels.value[0].model_id
        console.log('没有选择模型，加载第一个模型的测试历史:', firstModelId)
        
        const response = await modelManagementAPI.getTestRecords(firstModelId, {
          per_page: 20
        })
        
        if (response.success && response.data) {
          testHistory.value = response.data.items || []
          console.log('加载到测试历史记录数量:', testHistory.value.length)
        } else {
          testHistory.value = []
        }
      } else {
        console.log('没有可用模型，清空测试历史')
        testHistory.value = []
      }
    }
  } catch (error) {
    console.error('加载测试历史失败:', error)
    testHistory.value = []
  } finally {
    loadingHistory.value = false
  }
}

// 处理测试类型变化
const handleTestTypeChange = () => {
  testConfig.value.modelId = ''
  testConfig.value.ensembleId = ''
  testHistory.value = []
}

// 处理模型选择变化
const handleModelChange = () => {
  loadTestHistory()
}

// 处理组合选择变化
const handleEnsembleChange = () => {
  loadTestHistory()
}

// 流式显示文本的方法
const typewriterEffect = async (message: ChatMessage, fullText: string, speed?: number) => {
  message.isStreaming = true
  message.fullContent = fullText
  message.content = ''
  
  let actualSpeed = 15 // 默认速度
  
  if (speed !== undefined) {
    // 如果明确指定了速度，就使用指定的速度
    actualSpeed = speed
  } else {
    // 否则根据文本长度智能调整速度
    const textLength = fullText.length
    
    if (textLength > 500) {
      actualSpeed = 8  // 长文本更快
    } else if (textLength > 200) {
      actualSpeed = 12 // 中等文本中等速度
    } else {
      actualSpeed = 20 // 短文本稍慢，让用户能看清
    }
  }
  
  for (let i = 0; i <= fullText.length; i++) {
    message.content = fullText.substring(0, i)
    await new Promise(resolve => setTimeout(resolve, actualSpeed))
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  }
  
  message.isStreaming = false
}

// 运行测试
const runTest = async () => {
  if (!canTest.value) return

  const userMessage = inputMessage.value.trim()
  
  // 添加用户消息
  const userChatMessage: ChatMessage = {
    type: 'user',
    content: userMessage,
    timestamp: new Date().toISOString()
  }
  
  chatMessages.value.push(userChatMessage)
  inputMessage.value = ''
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()

  testing.value = true
  
  // 先添加一个空的助手消息，用于流式显示
  const assistantMessage: ChatMessage = {
    type: 'assistant',
    content: '正在思考中...',
    timestamp: new Date().toISOString(),
    isStreaming: true
  }
  chatMessages.value.push(assistantMessage)
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  try {
    let response: any
    
    if (testConfig.value.testType === 'single') {
      response = await modelManagementAPI.testSingleModel({
        model_id: testConfig.value.modelId,
        input: userMessage,
        expected_output: testConfig.value.expectedOutput || undefined,
        test_name: testConfig.value.testName || undefined,
        test_description: testConfig.value.testDescription || undefined
      })
    } else {
      response = await modelManagementAPI.testEnsemble({
        ensemble_id: testConfig.value.ensembleId,
        input: userMessage,
        expected_output: testConfig.value.expectedOutput || undefined,
        test_name: testConfig.value.testName || undefined,
        test_description: testConfig.value.testDescription || undefined
      })
    }
    
    console.log('API响应:', response)
    
    if (response.success && response.data) {
      const testResult = response.data.test_result || response.data
      const outputText = testResult.output || testResult.content || '无响应内容'
      
      // 更新助手消息的测试结果信息
      assistantMessage.responseTime = testResult.response_time_ms ? testResult.response_time_ms / 1000 : testResult.response_time
      assistantMessage.testResult = testResult
      
      // 根据用户设置选择显示方式
      if (testConfig.value.enableStreaming) {
        // 使用流式显示
        await typewriterEffect(assistantMessage, outputText)
      } else {
        // 直接显示完整内容
        assistantMessage.content = outputText
        assistantMessage.isStreaming = false
      }
      
      // 刷新测试历史
      await loadTestHistory()
      
      ElMessage.success('测试完成')
    } else {
      // 处理失败情况
      assistantMessage.isStreaming = false
      assistantMessage.content = `测试失败: ${response.message || '未知错误'}`
      assistantMessage.testResult = {
        test_id: '',
        success: false,
        response_time: 0,
        error_message: response.message || '未知错误',
        timestamp: new Date().toISOString()
      }
      
      ElMessage.error(response.message || '测试失败')
    }
  } catch (error) {
    console.error('测试失败:', error)
    ElMessage.error('测试失败')
    
    // 处理异常情况
    assistantMessage.isStreaming = false
    assistantMessage.content = `测试异常: ${error}`
    assistantMessage.testResult = {
      test_id: '',
      success: false,
      response_time: 0,
      error_message: String(error),
      timestamp: new Date().toISOString()
    }
  } finally {
    testing.value = false
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  }
}

// 清空对话
const clearChat = () => {
  chatMessages.value = []
}

// 聚焦输入框
const focusInput = () => {
  if (inputRef.value) {
    inputRef.value.focus()
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (chatAreaRef.value) {
    chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
  }
}

// 加载历史测试 - 重构版本
const loadHistoryTest = async (record: TestResult) => {
  try {
    // 清空当前对话
    chatMessages.value = []
    
    // 从测试记录中提取输入和输出
    const inputData = record.input_data || {}
    const actualOutput = record.actual_output || {}
    
    const inputText = inputData.input || '无输入数据'
    const outputText = actualOutput.output || '无输出数据'
    
    // 添加用户输入消息
    const userMessage: ChatMessage = {
      type: 'user',
      content: inputText,
      timestamp: record.created_at || record.timestamp || new Date().toISOString()
    }
    chatMessages.value.push(userMessage)
    
    // 添加AI回复消息 - 直接显示完整内容，不使用流式显示
    const assistantMessage: ChatMessage = {
      type: 'assistant',
      content: outputText,
      timestamp: record.created_at || record.timestamp || new Date().toISOString(),
      responseTime: record.response_time_ms ? record.response_time_ms / 1000 : record.response_time,
      isStreaming: false,
      testResult: {
        test_id: record.test_id,
        success: record.success,
        response_time: record.response_time_ms || record.response_time || 0,
        accuracy_score: record.accuracy_score,
        token_count: record.token_count,
        error_message: record.error_message,
        timestamp: record.created_at || record.timestamp || new Date().toISOString()
      }
    }
    chatMessages.value.push(assistantMessage)
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
    
    ElMessage.success(`已加载测试记录: ${record.test_name || record.test_id}`)
  } catch (error) {
    console.error('加载历史测试失败:', error)
    ElMessage.error('加载历史测试失败')
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  await Promise.all([
    loadAvailableModels(),
    loadAvailableEnsembles()
  ])
  
  // 加载模型后自动加载测试历史
  await loadTestHistory()
})
</script>

<style lang="scss" scoped>
.model-tester {
  height: calc(100vh - 200px);
  
  .test-config-panel,
  .test-history-panel,
  .chat-test-panel {
    background: var(--el-bg-color-overlay);
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    padding: 16px;
    height: 75%;
    display: flex;
    flex-direction: column;
  }
  
  .test-config-panel {
    height: 35%;
    margin-bottom: 16px;
  }
  
  .test-history-panel {
    height: calc(40% - 16px);
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--el-border-color-light);
    
    h3, h4 {
      margin: 0;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
    
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .test-form {
    flex: 1;
    overflow-y: auto;
  }
  
  .model-option,
  .ensemble-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }
  
  .history-list {
    flex: 1;
    overflow-y: auto;
    
    .history-item {
      padding: 8px;
      border: 1px solid var(--el-border-color-lighter);
      border-radius: 4px;
      margin-bottom: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: var(--el-color-primary);
        background: var(--el-color-primary-light-9);
      }
      
      .history-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
        
        .test-name {
          font-weight: 500;
        }
      }
      
      .history-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    }
  }
  
  .chat-test-panel {
    .chat-area {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: var(--el-bg-color-page);
      border-radius: 6px;
      margin-bottom: 16px;
      
      .chat-message {
        margin-bottom: 16px;
        
        &.user {
          .message-content {
            background: var(--el-color-primary-light-8);
            margin-left: 40px;
          }
        }
        
        &.assistant {
          .message-content {
            background: var(--el-bg-color-overlay);
            margin-right: 40px;
          }
        }
        
        .message-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
          
          .message-sender {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 500;
            color: var(--el-text-color-primary);
          }
          
          .message-meta {
            display: flex;
            gap: 12px;
          }
        }
        
        .message-content {
          padding: 12px 16px;
          border-radius: 8px;
          border: 1px solid var(--el-border-color-lighter);
          
          .message-text {
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.6;
            margin-bottom: 12px;
          }
          
          .test-result-info {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--el-border-color-lighter);
          }
        }
      }
      
      .empty-chat {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
    
    .input-area {
      .input-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 8px;
      }
    }
  }
}

// 滚动条样式
:deep(.el-scrollbar__wrap) {
  scrollbar-width: thin;
  scrollbar-color: var(--el-border-color) transparent;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar) {
  width: 6px;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar-thumb) {
  background-color: var(--el-border-color);
  border-radius: 3px;
}
</style>