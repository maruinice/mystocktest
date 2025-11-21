/**
 * 日期工具函数
 */

/**
 * 获取最近N天的日期范围
 * @param days 天数，默认30天（一个月）
 * @returns [开始日期, 结束日期] 格式：YYYY-MM-DD
 */
export function getRecentDateRange(days: number = 30): [string, string] {
  const end = new Date()
  const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000)
  
  return [formatDate(start), formatDate(end)]
}

/**
 * 格式化日期为 YYYY-MM-DD
 * @param date 日期对象
 * @returns 格式化后的日期字符串
 */
export function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  
  return `${year}-${month}-${day}`
}

/**
 * 获取今天的日期
 * @returns 格式化后的日期字符串 YYYY-MM-DD
 */
export function getToday(): string {
  return formatDate(new Date())
}

/**
 * 获取最近一周的日期范围
 * @returns [开始日期, 结束日期]
 */
export function getLastWeekRange(): [string, string] {
  return getRecentDateRange(7)
}

/**
 * 获取最近一个月的日期范围
 * @returns [开始日期, 结束日期]
 */
export function getLastMonthRange(): [string, string] {
  return getRecentDateRange(30)
}

/**
 * 获取最近一年的日期范围
 * @returns [开始日期, 结束日期]
 */
export function getLastYearRange(): [string, string] {
  return getRecentDateRange(365)
}

