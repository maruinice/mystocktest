/**
 * 格式化数字，添加千分位分隔符
 */
export function formatNumber(num: number, decimals: number = 2): string {
  if (isNaN(num)) return '0'
  
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * 格式化货币
 */
export function formatCurrency(amount: number, currency: string = '¥'): string {
  return `${currency}${formatNumber(amount)}`
}

/**
 * 格式化百分比
 */
export function formatPercent(value: number, decimals: number = 2): string {
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * 格式化大数字（K, M, B）
 */
export function formatLargeNumber(num: number): string {
  if (num >= 1e9) {
    return (num / 1e9).toFixed(1) + 'B'
  }
  if (num >= 1e6) {
    return (num / 1e6).toFixed(1) + 'M'
  }
  if (num >= 1e3) {
    return (num / 1e3).toFixed(1) + 'K'
  }
  return num.toString()
}

/**
 * 格式化日期时间
 */
export function formatDateTime(date: string | Date | undefined, format: string = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!date) return '-'
  
  const d = new Date(date)
  
  // 检查日期是否有效
  if (isNaN(d.getTime())) return '-'
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', year.toString())
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化日期
 */
export function formatDate(date: string | Date): string {
  return formatDateTime(date, 'YYYY-MM-DD')
}

/**
 * 格式化时间
 */
export function formatTime(date: string | Date): string {
  return formatDateTime(date, 'HH:mm:ss')
}

/**
 * 相对时间格式化
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date()
  const target = new Date(date)
  const diff = now.getTime() - target.getTime()
  
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const week = 7 * day
  const month = 30 * day
  const year = 365 * day
  
  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`
  } else if (diff < week) {
    return `${Math.floor(diff / day)}天前`
  } else if (diff < month) {
    return `${Math.floor(diff / week)}周前`
  } else if (diff < year) {
    return `${Math.floor(diff / month)}个月前`
  } else {
    return `${Math.floor(diff / year)}年前`
  }
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化股票代码
 */
export function formatStockCode(code: string): string {
  if (!code) return ''
  
  // 添加市场后缀
  if (code.length === 6) {
    if (code.startsWith('6')) {
      return `${code}.SH`
    } else if (code.startsWith('0') || code.startsWith('3')) {
      return `${code}.SZ`
    }
  }
  
  return code
}

/**
 * 格式化涨跌幅
 */
export function formatChange(change: number, changePercent: number): {
  text: string
  class: string
} {
  const changeText = change >= 0 ? `+${formatNumber(change)}` : formatNumber(change)
  const percentText = changePercent >= 0 ? `+${formatPercent(changePercent)}` : formatPercent(changePercent)
  
  let className = 'stock-flat'
  if (change > 0) {
    className = 'stock-up'
  } else if (change < 0) {
    className = 'stock-down'
  }
  
  return {
    text: `${changeText} (${percentText})`,
    class: className
  }
}