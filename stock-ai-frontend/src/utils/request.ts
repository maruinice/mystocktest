import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/routers'

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore()
    // 添加认证token（从计算属性tokenStr读取字符串）
    if (authStore.tokenStr) {
      const token = typeof authStore.tokenStr === 'string' ? authStore.tokenStr : (authStore.tokenStr as any).value
      if (token) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    
    // 如果返回的状态码为200，说明接口请求成功，可以正常拿到数据
    if (response.status === 200) {
      return data
    }
    
    // 其他状态码都当作错误处理
    ElMessage.error(data.message || '请求失败')
    return Promise.reject(new Error(data.message || '请求失败'))
  },
  async (error) => {
    const { response } = error
    const authStore = useAuthStore()
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          // 避免在logout请求失败时再次调用logout造成循环
          if (!error.config?.url?.includes('/auth/logout')) {
            ElMessage.error('登录已过期，请重新登录')
            await authStore.logout()
            router.push('/login')
          }
          break
          
        case 403:
          ElMessage.error('没有权限访问该资源')
          break
          
        case 404:
          ElMessage.error('请求的资源不存在')
          break
          
        case 422:
          // 参数验证错误
          if (data.errors) {
            const errorMessages = Object.values(data.errors).flat()
            ElMessage.error(errorMessages.join(', '))
          } else {
            ElMessage.error(data.message || '参数验证失败')
          }
          break
          
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试')
          break
          
        case 500:
          ElMessage.error('服务器内部错误')
          break
          
        default:
          ElMessage.error(data?.message || `请求失败 (${status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else if (error.message === 'Network Error') {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error('请求失败，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

// 封装常用的请求方法
export const http = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return request.get(url, config)
  },
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return request.post(url, data, config)
  },
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return request.put(url, data, config)
  },
  
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return request.delete(url, config)
  },
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return request.patch(url, data, config)
  }
}

export default request