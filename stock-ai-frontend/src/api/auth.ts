import { http } from '@/utils/request'
import type { LoginRequest, LoginResponse, User } from '@/types/auth'

export const authApi = {
  // 登录
  login(data: LoginRequest): Promise<LoginResponse> {
    return http.post('/auth/login', data)
  },

  // 登出
  logout(): Promise<void> {
    return http.post('/auth/logout')
  },

  // 验证token
  validateToken(): Promise<{ data: { user: User } }> {
    return http.get('/auth/validate')
  },

  // 刷新token
  refreshToken(): Promise<{ data: { token: string } }> {
    return http.post('/auth/refresh')
  },

  // 注册
  register(data: {
    username: string
    email: string
    password: string
    confirmPassword: string
  }): Promise<LoginResponse> {
    return http.post('/auth/register', data)
  },

  // 获取用户信息
  getUserInfo(): Promise<{ data: User }> {
    return http.get('/auth/user')
  },

  // 更新用户信息
  updateUserInfo(data: Partial<User>): Promise<{ data: User }> {
    return http.put('/auth/user', data)
  },

  // 修改密码
  changePassword(data: {
    oldPassword: string
    newPassword: string
    confirmPassword: string
  }): Promise<void> {
    return http.post('/auth/change-password', data)
  },

  // 忘记密码
  forgotPassword(email: string): Promise<void> {
    return http.post('/auth/forgot-password', { email })
  },

  // 重置密码
  resetPassword(data: {
    token: string
    password: string
    confirmPassword: string
  }): Promise<void> {
    return http.post('/auth/reset-password', data)
  }
}