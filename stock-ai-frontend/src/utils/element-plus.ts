// Element Plus 组件类型工具函数

// Tag 组件的 type 属性类型
export type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

// 确保返回值符合 Element Plus Tag 组件的 type 属性要求
export function getTagType(value: string): TagType {
  const validTypes: TagType[] = ['primary', 'success', 'warning', 'info', 'danger']
  return validTypes.includes(value as TagType) ? (value as TagType) : 'info'
}

// 常用的状态颜色映射
export const statusColorMap = {
  active: 'success',
  inactive: 'info',
  pending: 'warning',
  error: 'danger',
  success: 'success',
  failed: 'danger',
  running: 'primary',
  stopped: 'info',
  completed: 'success',
  cancelled: 'warning'
} as const

// 获取状态对应的标签类型
export function getStatusTagType(status: string): TagType {
  return getTagType(statusColorMap[status as keyof typeof statusColorMap] || 'info')
}