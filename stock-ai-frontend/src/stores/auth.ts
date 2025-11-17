import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { authApi } from '@/api/auth'
import type { LoginRequest, User } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  // 供外部（如axios拦截器）直接读取字符串形式的token
  const tokenStr = computed(() => token.value || '')

  // 登录
  const login = async (credentials: LoginRequest) => {
    loading.value = true
    try {
      const response = await authApi.login(credentials)
      token.value = response.data.token
      user.value = response.data.user
      
      // 保存到本地存储
      localStorage.setItem('token', response.data.token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
      
      // 登录成功后初始化WebSocket连接
      const { initWebSocket } = await import('@/utils/websocket')
      initWebSocket().catch(console.error)
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 断开WebSocket连接
      const { destroyWebSocket } = await import('@/utils/websocket')
      destroyWebSocket()
      
      // 清除状态和本地存储
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }

  // 验证token
  const validateToken = async (): Promise<boolean> => {
    if (!token.value) return false
    
    try {
      const response = await authApi.validateToken()
      user.value = response.data.user
      return true
    } catch (error) {
      // token无效，清除状态
      await logout()
      return false
    }
  }

  // 刷新token
  const refreshToken = async () => {
    try {
      const response = await authApi.refreshToken()
      token.value = response.data.token
      localStorage.setItem('token', response.data.token)
      return response.data.token
    } catch (error) {
      await logout()
      throw error
    }
  }

  // 初始化
  const initialize = async () => {
    const savedUser = localStorage.getItem('user')
    if (savedUser && token.value) {
      try {
        user.value = JSON.parse(savedUser)
        // 验证token是否仍然有效
        await validateToken()
      } catch (error) {
        await logout()
      }
    }
  }

  return {
    // 状态
    token: readonly(token),
    user: readonly(user),
    loading: readonly(loading),
    
    // 计算属性
    isAuthenticated,
    tokenStr,
    
    // 方法
    login,
    logout,
    validateToken,
    refreshToken,
    initialize
  }
})