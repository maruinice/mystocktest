<template>
  <div class="strategy-importer">
    <div class="importer-content">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 文件导入 -->
        <el-tab-pane label="文件导入" name="file">
          <div class="file-import">
            <div class="upload-area">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :show-file-list="false"
                accept=".json,.py,.txt"
                @change="handleFileChange"
                drag
              >
                <div class="upload-content">
                  <el-icon class="upload-icon"><UploadFilled /></el-icon>
                  <div class="upload-text">
                    <p>将策略文件拖拽到此处，或<em>点击上传</em></p>
                    <p class="upload-hint">支持 JSON、Python、TXT 格式</p>
                  </div>
                </div>
              </el-upload>
            </div>
            
            <div v-if="selectedFile" class="file-info">
              <div class="file-details">
                <el-icon><Document /></el-icon>
                <span class="file-name">{{ selectedFile.name }}</span>
                <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
              </div>
              <el-button @click="clearFile" size="small" text type="danger">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            
            <div v-if="fileContent" class="file-preview">
              <div class="preview-header">
                <h4>文件预览</h4>
                <el-button @click="parseFile" size="small" type="primary">
                  <el-icon><Magic /></el-icon>
                  解析策略
                </el-button>
              </div>
              <div class="preview-content">
                <pre><code>{{ fileContent }}</code></pre>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <!-- URL导入 -->
        <el-tab-pane label="URL导入" name="url">
          <div class="url-import">
            <el-form :model="urlForm" label-width="100px">
              <el-form-item label="策略URL">
                <el-input
                  v-model="urlForm.url"
                  placeholder="请输入策略文件的URL地址"
                  clearable
                >
                  <template #append>
                    <el-button @click="fetchFromUrl" :loading="urlLoading">
                      获取
                    </el-button>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item label="认证信息" v-if="urlForm.requireAuth">
                <el-input
                  v-model="urlForm.token"
                  placeholder="请输入访问令牌（如需要）"
                  type="password"
                  show-password
                />
              </el-form-item>
              
              <el-form-item>
                <el-checkbox v-model="urlForm.requireAuth">需要认证</el-checkbox>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
        
        <!-- 代码导入 -->
        <el-tab-pane label="代码导入" name="code">
          <div class="code-import">
            <div class="code-editor">
              <div class="editor-header">
                <h4>粘贴策略代码</h4>
                <div class="editor-actions">
                  <el-button @click="clearCode" size="small">清空</el-button>
                  <el-button @click="formatCode" size="small">格式化</el-button>
                </div>
              </div>
              <el-input
                v-model="codeContent"
                type="textarea"
                :rows="15"
                placeholder="请粘贴策略代码..."
                class="code-textarea"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      
      <!-- 解析结果 -->
      <div v-if="parsedStrategies.length > 0" class="parsed-strategies">
        <div class="strategies-header">
          <h3>解析到的策略 ({{ parsedStrategies.length }})</h3>
          <el-button @click="selectAll" size="small">
            {{ allSelected ? '取消全选' : '全选' }}
          </el-button>
        </div>
        
        <div class="strategies-list">
          <div 
            v-for="(strategy, index) in parsedStrategies" 
            :key="index"
            class="strategy-item"
            :class="{ selected: strategy.selected }"
            @click="toggleStrategy(index)"
          >
            <div class="strategy-checkbox">
              <el-checkbox v-model="strategy.selected" />
            </div>
            <div class="strategy-info">
              <div class="strategy-header">
                <h4>{{ strategy.name }}</h4>
                <el-tag :type="getStrategyTypeColor(strategy.category)" size="small">
                  {{ getStrategyTypeText(strategy.category) }}
                </el-tag>
              </div>
              <p class="strategy-description">{{ strategy.description }}</p>
              <div class="strategy-meta">
                <span class="meta-item">
                  <el-icon><User /></el-icon>
                  {{ strategy.author || '未知' }}
                </span>
                <span class="meta-item">
                  <el-icon><Calendar /></el-icon>
                  {{ strategy.created_at ? formatDate(strategy.created_at) : '未知' }}
                </span>
                <span class="meta-item">
                  <el-icon><TrendCharts /></el-icon>
                  {{ getRiskLevelText(strategy.risk_level) }}
                </span>
              </div>
            </div>
            <div class="strategy-actions">
              <el-button @click.stop="previewStrategy(strategy)" size="small" text>
                <el-icon><View /></el-icon>
                预览
              </el-button>
              <el-button @click.stop="editStrategy(strategy)" size="small" text>
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 底部操作 -->
    <div class="importer-footer">
      <div class="footer-left">
        <el-button @click="$emit('cancel')">取消</el-button>
      </div>
      <div class="footer-right">
        <el-button 
          @click="importStrategies" 
          type="primary"
          :disabled="selectedStrategies.length === 0"
          :loading="importing"
        >
          <el-icon><Upload /></el-icon>
          导入策略 ({{ selectedStrategies.length }})
        </el-button>
      </div>
    </div>
    
    <!-- 策略预览对话框 -->
    <el-dialog
      v-model="showPreview"
      title="策略预览"
      width="80%"
      :close-on-click-modal="false"
    >
      <StrategyPreview
        v-if="showPreview && previewingStrategy"
        :strategy="previewingStrategy"
        @close="showPreview = false"
      />
    </el-dialog>
    
    <!-- 策略编辑对话框 -->
    <el-dialog
      v-model="showEdit"
      title="编辑策略"
      width="90%"
      :close-on-click-modal="false"
    >
      <StrategyEditor
        v-if="showEdit && editingStrategy"
        :strategy="editingStrategy"
        @save="handleStrategySave"
        @cancel="showEdit = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import type { UploadFile } from 'element-plus'
import type { Strategy } from '@/types/strategy'

// 导入子组件
import StrategyPreview from './StrategyPreview.vue'
import StrategyEditor from './StrategyEditor.vue'

// Emits
const emit = defineEmits<{
  import: [strategies: Strategy[]]
  cancel: []
}>()

// 响应式数据
const activeTab = ref('file')
const selectedFile = ref<File | null>(null)
const fileContent = ref('')
const codeContent = ref('')
const urlLoading = ref(false)
const importing = ref(false)
const showPreview = ref(false)
const showEdit = ref(false)
const previewingStrategy = ref<Strategy | null>(null)
const editingStrategy = ref<Strategy | null>(null)

// URL导入表单
const urlForm = reactive({
  url: '',
  token: '',
  requireAuth: false
})

// 解析的策略列表
const parsedStrategies = ref<Array<Strategy & { selected: boolean }>>([])

// 计算属性
const selectedStrategies = computed(() => 
  parsedStrategies.value.filter(s => s.selected)
)

const allSelected = computed(() => 
  parsedStrategies.value.length > 0 && parsedStrategies.value.every(s => s.selected)
)

// 方法
const handleFileChange = (file: UploadFile) => {
  if (!file.raw) return
  
  selectedFile.value = file.raw
  
  const reader = new FileReader()
  reader.onload = (e) => {
    fileContent.value = e.target?.result as string
  }
  reader.readAsText(file.raw)
}

const clearFile = () => {
  selectedFile.value = null
  fileContent.value = ''
  parsedStrategies.value = []
}

const fetchFromUrl = async () => {
  if (!urlForm.url.trim()) {
    ElMessage.warning('请输入URL地址')
    return
  }
  
  urlLoading.value = true
  
  try {
    // 模拟从URL获取策略文件
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟获取到的内容
    const mockContent = `{
  "name": "从URL导入的策略",
  "description": "这是一个从URL导入的示例策略",
  "category": "trend_following",
  "risk_level": "medium",
  "code": "def initialize(context):\\n    pass\\n\\ndef handle_data(context, data):\\n    pass"
}`
    
    fileContent.value = mockContent
    ElMessage.success('策略文件获取成功')
    
    // 自动解析
    parseFile()
    
  } catch (error) {
    ElMessage.error('获取策略文件失败')
  } finally {
    urlLoading.value = false
  }
}

const clearCode = () => {
  codeContent.value = ''
}

const formatCode = () => {
  // 简单的代码格式化
  const lines = codeContent.value.split('\n')
  const formatted = lines.map(line => line.trim()).join('\n')
  codeContent.value = formatted
  ElMessage.success('代码格式化完成')
}

const parseFile = () => {
  let content = ''
  
  if (activeTab.value === 'file') {
    content = fileContent.value
  } else if (activeTab.value === 'code') {
    content = codeContent.value
  }
  
  if (!content.trim()) {
    ElMessage.warning('没有内容可解析')
    return
  }
  
  try {
    const strategies = parseStrategyContent(content)
    parsedStrategies.value = strategies.map(strategy => ({
      ...strategy,
      selected: true
    }))
    
    ElMessage.success(`成功解析 ${strategies.length} 个策略`)
  } catch (error) {
    ElMessage.error('策略解析失败，请检查文件格式')
  }
}

const parseStrategyContent = (content: string): Strategy[] => {
  const strategies: Strategy[] = []
  
  try {
    // 尝试解析JSON格式
    const jsonData = JSON.parse(content)
    
    if (Array.isArray(jsonData)) {
      // 多个策略
      jsonData.forEach((item, index) => {
        strategies.push(createStrategyFromData(item, index))
      })
    } else {
      // 单个策略
      strategies.push(createStrategyFromData(jsonData, 0))
    }
  } catch {
    // 如果不是JSON，尝试解析Python代码
    const strategy = parseStrategyFromCode(content)
    strategies.push(strategy)
  }
  
  return strategies
}

const createStrategyFromData = (data: any, index: number): Strategy => {
  return {
    strategy_id: `IMPORT_${Date.now()}_${index}`,
    name: data.name || `导入策略_${index + 1}`,
    display_name: data.display_name || data.name || `导入策略_${index + 1}`,
    description: data.description || '从文件导入的策略',
    category: data.category || 'custom',
    risk_level: data.risk_level || 'medium',
    author: data.author || '未知',
    parameters: data.parameters || {},
    code: data.code || '',
    status: 'draft',
    created_at: data.created_at || new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
}

const parseStrategyFromCode = (code: string): Strategy => {
  // 从Python代码中提取策略信息
  const lines = code.split('\n')
  let name = '代码导入策略'
  let description = '从Python代码导入的策略'
  
  // 尝试从注释中提取信息
  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('#')) {
      const comment = trimmed.substring(1).trim()
      if (comment && !name.includes('导入')) {
        name = comment
        break
      }
    }
  }
  
  return {
    strategy_id: `CODE_IMPORT_${Date.now()}`,
    name: name,
    display_name: name,
    description: description,
    category: 'custom',
    risk_level: 'medium',
    code: code,
    status: 'draft',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
}

const toggleStrategy = (index: number) => {
  parsedStrategies.value[index].selected = !parsedStrategies.value[index].selected
}

const selectAll = () => {
  const newValue = !allSelected.value
  parsedStrategies.value.forEach(strategy => {
    strategy.selected = newValue
  })
}

const previewStrategy = (strategy: Strategy) => {
  previewingStrategy.value = strategy
  showPreview.value = true
}

const editStrategy = (strategy: Strategy) => {
  editingStrategy.value = strategy
  showEdit.value = true
}

const handleStrategySave = (updatedStrategy: Strategy) => {
  const index = parsedStrategies.value.findIndex(s => s.strategy_id === updatedStrategy.strategy_id)
  if (index > -1) {
    parsedStrategies.value[index] = { ...updatedStrategy, selected: true }
  }
  showEdit.value = false
  ElMessage.success('策略更新成功')
}

const importStrategies = async () => {
  if (selectedStrategies.value.length === 0) {
    ElMessage.warning('请选择要导入的策略')
    return
  }
  
  importing.value = true
  
  try {
    // 模拟导入过程
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    const strategies = selectedStrategies.value.map(({ selected, ...strategy }) => strategy)
    
    emit('import', strategies)
    
    ElNotification({
      title: '导入成功',
      message: `成功导入 ${strategies.length} 个策略`,
      type: 'success'
    })
    
  } catch (error) {
    ElMessage.error('策略导入失败')
  } finally {
    importing.value = false
  }
}

// 工具方法
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const getStrategyTypeText = (type: string): string => {
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

const getStrategyTypeColor = (type: string): string => {
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

const getRiskLevelText = (level: string): string => {
  const levelMap: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险'
  }
  return levelMap[level] || level
}

// 监听代码内容变化，自动解析
watch(() => codeContent.value, (newValue) => {
  if (newValue.trim() && activeTab.value === 'code') {
    // 延迟解析，避免频繁触发
    clearTimeout(parseTimer)
    parseTimer = setTimeout(() => {
      parseFile()
    }, 1000)
  }
})

let parseTimer: NodeJS.Timeout
</script>

<style lang="scss" scoped>
.strategy-importer {
  display: flex;
  flex-direction: column;
  height: 70vh;
}

.importer-content {
  flex: 1;
  overflow: hidden;
  
  .el-tabs {
    height: 100%;
    display: flex;
    flex-direction: column;
    
    :deep(.el-tabs__content) {
      flex: 1;
      overflow: auto;
    }
  }
}

// 文件导入
.file-import {
  padding: 20px;
  
  .upload-area {
    margin-bottom: 20px;
    
    .upload-content {
      padding: 40px;
      text-align: center;
      
      .upload-icon {
        font-size: 48px;
        color: #c0c4cc;
        margin-bottom: 16px;
      }
      
      .upload-text {
        p {
          margin: 0 0 8px 0;
          color: #606266;
          
          em {
            color: #409eff;
            font-style: normal;
          }
        }
        
        .upload-hint {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }
  
  .file-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #f5f7fa;
    border-radius: 6px;
    margin-bottom: 20px;
    
    .file-details {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .file-name {
        font-weight: 500;
        color: #303133;
      }
      
      .file-size {
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .file-preview {
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      
      h4 {
        margin: 0;
        font-size: 16px;
        color: #303133;
      }
    }
    
    .preview-content {
      background: #1e1e1e;
      border-radius: 6px;
      overflow: hidden;
      
      pre {
        margin: 0;
        padding: 16px;
        overflow: auto;
        max-height: 300px;
        
        code {
          color: #d4d4d4;
          font-family: 'Courier New', monospace;
          font-size: 12px;
          line-height: 1.5;
        }
      }
    }
  }
}

// URL导入
.url-import {
  padding: 20px;
}

// 代码导入
.code-import {
  padding: 20px;
  
  .code-editor {
    .editor-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      
      h4 {
        margin: 0;
        font-size: 16px;
        color: #303133;
      }
      
      .editor-actions {
        display: flex;
        gap: 8px;
      }
    }
    
    .code-textarea {
      :deep(.el-textarea__inner) {
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.6;
        background: #1e1e1e;
        color: #d4d4d4;
        border: 1px solid #404040;
        
        &:focus {
          border-color: #409eff;
        }
      }
    }
  }
}

// 解析结果
.parsed-strategies {
  border-top: 1px solid #e4e7ed;
  padding: 20px;
  
  .strategies-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      margin: 0;
      font-size: 18px;
      color: #303133;
    }
  }
  
  .strategies-list {
    .strategy-item {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: #409eff;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
      }
      
      &.selected {
        border-color: #409eff;
        background: #f0f9ff;
      }
      
      .strategy-checkbox {
        flex-shrink: 0;
      }
      
      .strategy-info {
        flex: 1;
        
        .strategy-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;
          
          h4 {
            margin: 0;
            font-size: 16px;
            color: #303133;
          }
        }
        
        .strategy-description {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: #606266;
          line-height: 1.4;
        }
        
        .strategy-meta {
          display: flex;
          gap: 16px;
          
          .meta-item {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            color: #909399;
          }
        }
      }
      
      .strategy-actions {
        flex-shrink: 0;
        display: flex;
        gap: 8px;
      }
    }
  }
}

// 底部操作
.importer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}

// 响应式设计
@media (max-width: 768px) {
  .strategy-item {
    flex-direction: column;
    align-items: flex-start !important;
    
    .strategy-actions {
      width: 100%;
      justify-content: flex-end;
    }
  }
  
  .importer-footer {
    flex-direction: column;
    gap: 12px;
  }
}
</style>