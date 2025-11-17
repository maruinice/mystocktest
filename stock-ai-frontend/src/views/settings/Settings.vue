<template>
  <div class="settings-container">
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
      <p class="page-description">个性化配置您的交易系统</p>
    </div>
    
    <el-row :gutter="24">
      <!-- 设置菜单 -->
      <el-col :xs="24" :md="6">
        <div class="settings-menu">
          <el-menu
            :default-active="activeTab"
            @select="handleMenuSelect"
            class="settings-nav"
          >
            <el-menu-item index="profile">
              <el-icon><User /></el-icon>
              <span>个人资料</span>
            </el-menu-item>
            <el-menu-item index="security">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
            </el-menu-item>
            <el-menu-item index="trading">
              <el-icon><TrendCharts /></el-icon>
              <span>交易设置</span>
            </el-menu-item>
            <el-menu-item index="notification">
              <el-icon><Bell /></el-icon>
              <span>通知设置</span>
            </el-menu-item>
            <el-menu-item index="appearance">
              <el-icon><Monitor /></el-icon>
              <span>外观设置</span>
            </el-menu-item>
            <el-menu-item index="system">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-col>
      
      <!-- 设置内容 -->
      <el-col :xs="24" :md="18">
        <div class="settings-content">
          <!-- 个人资料 -->
          <div v-show="activeTab === 'profile'" class="settings-panel">
            <div class="panel-header">
              <h3>个人资料</h3>
              <p>管理您的个人信息</p>
            </div>
            
            <el-form :model="profileForm" :rules="profileRules" ref="profileFormRef" label-width="100px">
              <el-form-item label="头像">
                <div class="avatar-upload">
                  <el-avatar :size="80" :src="profileForm.avatar" />
                  <el-button size="small" style="margin-left: 16px;">
                    <el-icon><Upload /></el-icon>
                    上传头像
                  </el-button>
                </div>
              </el-form-item>
              
              <el-form-item label="用户名" prop="username">
                <el-input v-model="profileForm.username" style="width: 300px;" />
              </el-form-item>
              
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="profileForm.email" style="width: 300px;" />
              </el-form-item>
              
              <el-form-item label="手机号" prop="phone">
                <el-input v-model="profileForm.phone" style="width: 300px;" />
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="saveProfile" :loading="profileLoading">
                  保存
                </el-button>
              </el-form-item>
            </el-form>
          </div>
          
          <!-- 安全设置 -->
          <div v-show="activeTab === 'security'" class="settings-panel">
            <div class="panel-header">
              <h3>安全设置</h3>
              <p>保护您的账户安全</p>
            </div>
            
            <div class="security-items">
              <div class="security-item">
                <div class="security-info">
                  <div class="security-title">登录密码</div>
                  <div class="security-desc">定期更新密码有助于保护账户安全</div>
                </div>
                <el-button @click="showChangePassword = true">修改密码</el-button>
              </div>
              
              <div class="security-item">
                <div class="security-info">
                  <div class="security-title">两步验证</div>
                  <div class="security-desc">开启两步验证提高账户安全性</div>
                </div>
                <el-switch v-model="securitySettings.twoFactorAuth" />
              </div>
              
              <div class="security-item">
                <div class="security-info">
                  <div class="security-title">登录通知</div>
                  <div class="security-desc">新设备登录时发送通知</div>
                </div>
                <el-switch v-model="securitySettings.loginNotification" />
              </div>
            </div>
          </div>
          
          <!-- 交易设置 -->
          <div v-show="activeTab === 'trading'" class="settings-panel">
            <div class="panel-header">
              <h3>交易设置</h3>
              <p>配置您的交易偏好</p>
            </div>
            
            <el-form :model="tradingSettings" label-width="120px">
              <el-form-item label="默认交易数量">
                <el-input-number
                  v-model="tradingSettings.defaultQuantity"
                  :min="100"
                  :step="100"
                  style="width: 200px;"
                />
                <span style="margin-left: 8px; color: var(--el-text-color-regular);">股</span>
              </el-form-item>
              
              <el-form-item label="风险控制">
                <el-switch v-model="tradingSettings.riskControl" />
                <span style="margin-left: 8px; color: var(--el-text-color-regular);">
                  开启后将自动进行风险检查
                </span>
              </el-form-item>
              
              <el-form-item label="最大持仓比例">
                <el-slider
                  v-model="tradingSettings.maxPositionRatio"
                  :min="10"
                  :max="100"
                  :step="5"
                  show-input
                  style="width: 300px;"
                />
                <span style="margin-left: 8px; color: var(--el-text-color-regular);">%</span>
              </el-form-item>
              
              <el-form-item label="止损比例">
                <el-input-number
                  v-model="tradingSettings.stopLossRatio"
                  :min="1"
                  :max="20"
                  :precision="1"
                  style="width: 200px;"
                />
                <span style="margin-left: 8px; color: var(--el-text-color-regular);">%</span>
              </el-form-item>
              
              <el-form-item label="交易确认">
                <el-switch v-model="tradingSettings.confirmBeforeTrade" />
                <span style="margin-left: 8px; color: var(--el-text-color-regular);">
                  下单前需要确认
                </span>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="saveTradingSettings" :loading="tradingLoading">
                  保存设置
                </el-button>
              </el-form-item>
            </el-form>
          </div>
          
          <!-- 通知设置 -->
          <div v-show="activeTab === 'notification'" class="settings-panel">
            <div class="panel-header">
              <h3>通知设置</h3>
              <p>管理您的通知偏好</p>
            </div>
            
            <div class="notification-groups">
              <div class="notification-group">
                <h4>交易通知</h4>
                <div class="notification-items">
                  <div class="notification-item">
                    <div class="notification-info">
                      <div class="notification-title">订单成交</div>
                      <div class="notification-desc">订单成交时发送通知</div>
                    </div>
                    <el-switch v-model="notificationSettings.orderFilled" />
                  </div>
                  
                  <div class="notification-item">
                    <div class="notification-info">
                      <div class="notification-title">价格提醒</div>
                      <div class="notification-desc">股价达到设定价格时提醒</div>
                    </div>
                    <el-switch v-model="notificationSettings.priceAlert" />
                  </div>
                  
                  <div class="notification-item">
                    <div class="notification-info">
                      <div class="notification-title">策略信号</div>
                      <div class="notification-desc">策略产生交易信号时通知</div>
                    </div>
                    <el-switch v-model="notificationSettings.strategySignal" />
                  </div>
                </div>
              </div>
              
              <div class="notification-group">
                <h4>系统通知</h4>
                <div class="notification-items">
                  <div class="notification-item">
                    <div class="notification-info">
                      <div class="notification-title">系统维护</div>
                      <div class="notification-desc">系统维护时发送通知</div>
                    </div>
                    <el-switch v-model="notificationSettings.systemMaintenance" />
                  </div>
                  
                  <div class="notification-item">
                    <div class="notification-info">
                      <div class="notification-title">功能更新</div>
                      <div class="notification-desc">新功能发布时通知</div>
                    </div>
                    <el-switch v-model="notificationSettings.featureUpdate" />
                  </div>
                </div>
              </div>
            </div>
            
            <el-button type="primary" @click="saveNotificationSettings" :loading="notificationLoading">
              保存设置
            </el-button>
          </div>
          
          <!-- 外观设置 -->
          <div v-show="activeTab === 'appearance'" class="settings-panel">
            <div class="panel-header">
              <h3>外观设置</h3>
              <p>个性化您的界面外观</p>
            </div>
            
            <el-form label-width="120px">
              <el-form-item label="主题模式">
                <el-radio-group v-model="themeMode" @change="handleThemeChange">
                  <el-radio label="light">浅色模式</el-radio>
                  <el-radio label="dark">深色模式</el-radio>
                  <el-radio label="auto">跟随系统</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="语言">
                <el-select v-model="appearanceSettings.language" style="width: 200px;">
                  <el-option label="简体中文" value="zh-CN" />
                  <el-option label="English" value="en-US" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="字体大小">
                <el-radio-group v-model="appearanceSettings.fontSize">
                  <el-radio label="small">小</el-radio>
                  <el-radio label="medium">中</el-radio>
                  <el-radio label="large">大</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="紧凑模式">
                <el-switch v-model="appearanceSettings.compactMode" />
                <span style="margin-left: 8px; color: var(--el-text-color-regular);">
                  减少界面间距
                </span>
              </el-form-item>
            </el-form>
          </div>
          
          <!-- 系统设置 -->
          <div v-show="activeTab === 'system'" class="settings-panel">
            <div class="panel-header">
              <h3>系统设置</h3>
              <p>系统相关配置</p>
            </div>
            
            <div class="system-info">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
                <el-descriptions-item label="最后更新">2023-12-01</el-descriptions-item>
                <el-descriptions-item label="API版本">v1.0</el-descriptions-item>
                <el-descriptions-item label="数据库版本">PostgreSQL 14</el-descriptions-item>
              </el-descriptions>
            </div>
            
            <div class="system-actions">
              <el-button @click="clearCache">清除缓存</el-button>
              <el-button @click="exportData">导出数据</el-button>
              <el-button type="danger" @click="resetSettings">重置设置</el-button>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 修改密码对话框 -->
    <el-dialog v-model="showChangePassword" title="修改密码" width="400px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="当前密码" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showChangePassword = false">取消</el-button>
        <el-button type="primary" @click="changePassword" :loading="passwordLoading">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useThemeStore } from '@/stores/theme'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const themeStore = useThemeStore()

// 响应式数据
const activeTab = ref('profile')
const profileLoading = ref(false)
const tradingLoading = ref(false)
const notificationLoading = ref(false)
const passwordLoading = ref(false)
const showChangePassword = ref(false)

const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

// 表单数据
const profileForm = reactive({
  username: '',
  email: '',
  phone: '',
  avatar: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const securitySettings = reactive({
  twoFactorAuth: false,
  loginNotification: true
})

const tradingSettings = reactive({
  defaultQuantity: 100,
  riskControl: true,
  maxPositionRatio: 50,
  stopLossRatio: 5.0,
  confirmBeforeTrade: true
})

const notificationSettings = reactive({
  orderFilled: true,
  priceAlert: true,
  strategySignal: true,
  systemMaintenance: true,
  featureUpdate: false
})

const appearanceSettings = reactive({
  language: 'zh-CN',
  fontSize: 'medium',
  compactMode: false
})

const themeMode = ref(themeStore.mode)

// 表单验证规则
const profileRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const passwordRules: FormRules = {
  oldPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 方法
const handleMenuSelect = (index: string) => {
  activeTab.value = index
}

const saveProfile = async () => {
  if (!profileFormRef.value) return
  try {
    await profileFormRef.value.validate()
    profileLoading.value = true
    const payload: any = { username: profileForm.username, email: profileForm.email }
    if (profileForm.avatar) payload.avatar = profileForm.avatar
    const resp = await authApi.updateUserInfo(payload)
    if (resp.data) {
      const authStore = useAuthStore()
      const updated = resp.data
      localStorage.setItem('user', JSON.stringify(updated))
      ElMessage.success('个人资料保存成功')
    }
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    profileLoading.value = false
  }
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  try {
    await passwordFormRef.value.validate()
    passwordLoading.value = true
    await authApi.changePassword({
      oldPassword: passwordForm.oldPassword,
      newPassword: passwordForm.newPassword,
      confirmPassword: passwordForm.confirmPassword
    })
    ElMessage.success('密码修改成功')
    showChangePassword.value = false
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (error) {
    ElMessage.error('密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

const saveTradingSettings = async () => {
  tradingLoading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('交易设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    tradingLoading.value = false
  }
}

const saveNotificationSettings = async () => {
  notificationLoading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('通知设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    notificationLoading.value = false
  }
}

const handleThemeChange = (mode: string) => {
  themeStore.setThemeMode(mode as any)
}

const clearCache = async () => {
  try {
    await ElMessageBox.confirm('确认清除所有缓存数据？', '清除缓存', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    ElMessage.success('缓存清除成功')
  } catch (error) {
    // 用户取消
  }
}

const exportData = () => {
  ElMessage.success('数据导出成功')
}

const resetSettings = async () => {
  try {
    await ElMessageBox.confirm('确认重置所有设置？此操作不可恢复。', '重置设置', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    ElMessage.success('设置重置成功')
  } catch (error) {
    // 用户取消
  }
}

onMounted(async () => {
  try {
    const resp = await authApi.getUserInfo()
    if (resp.data) {
      profileForm.username = resp.data.username || ''
      profileForm.email = resp.data.email || ''
      profileForm.avatar = resp.data.avatar || ''
    }
  } catch {}
})
</script>

<style lang="scss" scoped>
.settings-container {
  padding: 24px;
}

.settings-menu {
  .settings-nav {
    border-right: none;
    background: var(--el-bg-color-overlay);
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
  }
}

.settings-content {
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 24px;
}

.settings-panel {
  .panel-header {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    h3 {
      margin: 0 0 8px 0;
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
    
    p {
      margin: 0;
      color: var(--el-text-color-regular);
      font-size: 14px;
    }
  }
}

.avatar-upload {
  display: flex;
  align-items: center;
}

.security-items {
  .security-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    &:last-child {
      border-bottom: none;
    }
    
    .security-info {
      flex: 1;
      
      .security-title {
        font-size: 16px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .security-desc {
        font-size: 14px;
        color: var(--el-text-color-regular);
      }
    }
  }
}

.notification-groups {
  .notification-group {
    margin-bottom: 32px;
    
    h4 {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
    
    .notification-items {
      .notification-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid var(--el-border-color-lighter);
        
        &:last-child {
          border-bottom: none;
        }
        
        .notification-info {
          flex: 1;
          
          .notification-title {
            font-size: 14px;
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 2px;
          }
          
          .notification-desc {
            font-size: 12px;
            color: var(--el-text-color-regular);
          }
        }
      }
    }
  }
}

.system-info {
  margin-bottom: 24px;
}

.system-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .settings-container {
    padding: 16px;
  }
  
  .settings-content {
    padding: 16px;
    margin-top: 16px;
  }
  
  .security-item,
  .notification-item {
    flex-direction: column;
    align-items: flex-start !important;
    
    .security-info,
    .notification-info {
      margin-bottom: 12px;
    }
  }
  
  .system-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}
</style>
