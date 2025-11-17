export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  role: string
  permissions: string[]
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
  remember?: boolean
}

export interface LoginResponse {
  success: boolean
  message: string
  data: {
    token: string
    user: User
    expires_in: number
  }
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirmPassword: string
}

export interface ChangePasswordRequest {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  password: string
  confirmPassword: string
}