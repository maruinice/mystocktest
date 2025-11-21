/**
 * WebSocket客户端管理器
 * 提供实时数据通信功能
 */

import { ElMessage, ElNotification } from 'element-plus'

// WebSocket消息类型
export enum WebSocketMessageType {
  QUOTE_UPDATE = 'quote_update',
  ORDER_UPDATE = 'order_update',
  POSITION_UPDATE = 'position_update',
  RISK_ALERT = 'risk_alert',
  SYSTEM_STATUS = 'system_status',
  STRATEGY_UPDATE = 'strategy_update',
  AI_DECISION = 'ai_decision',
  CONNECTION_ESTABLISHED = 'connection_established',
  PING = 'ping',
  PONG = 'pong'
}

// WebSocket连接状态
export enum WebSocketStatus {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

// 消息处理器类型
export type MessageHandler = (data: any) => void

// WebSocket配置
interface WebSocketConfig {
  url?: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  debug?: boolean
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private status: WebSocketStatus = WebSocketStatus.DISCONNECTED
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000
  private heartbeatInterval = 30000
  private heartbeatTimer: number | null = null
  private reconnectTimer: number | null = null
  private debug = false
  
  // 消息处理器映射
  private messageHandlers: Map<WebSocketMessageType, Set<MessageHandler>> = new Map()
  
  // 状态变化回调
  private statusChangeCallbacks: Set<(status: WebSocketStatus) => void> = new Set()
  
  constructor(config: WebSocketConfig = {}) {
    this.maxReconnectAttempts = config.maxReconnectAttempts || 5
    this.reconnectInterval = config.reconnectInterval || 1000
    this.heartbeatInterval = config.heartbeatInterval || 30000
    this.debug = config.debug || false
  }
  
  /**
   * 连接WebSocket服务器
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          reject(new Error('未找到认证token'))
          return
        }
        
        // 构建WebSocket URL
        const wsUrl = this.getWebSocketUrl(token)
        
        this.log('正在连接WebSocket服务器...', wsUrl)
        this.setStatus(WebSocketStatus.CONNECTING)
        
        this.ws = new WebSocket(wsUrl)
        
        this.ws.onopen = () => {
          this.log('WebSocket连接已建立')
          this.setStatus(WebSocketStatus.CONNECTED)
          this.reconnectAttempts = 0
          this.startHeartbeat()
          resolve()
        }
        
        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }
        
        this.ws.onclose = (event) => {
          this.log('WebSocket连接已关闭', event.code, event.reason)
          this.setStatus(WebSocketStatus.DISCONNECTED)
          this.stopHeartbeat()
          
          // 认证错误（4001, 4002, 4003）不应该重连
          if (event.code === 4001 || event.code === 4002 || event.code === 4003) {
            this.log('WebSocket认证失败，停止重连', event.reason)
            // 检查token是否过期
            const token = localStorage.getItem('token')
            if (!token) {
              this.log('Token不存在，停止重连')
              return
            }
            // 尝试解析token检查是否过期
            try {
              const payload = JSON.parse(atob(token.split('.')[1]))
              const exp = payload.exp * 1000 // 转换为毫秒
              if (Date.now() >= exp) {
                this.log('Token已过期，停止重连')
                return
              }
            } catch (e) {
              // token格式错误，停止重连
              this.log('Token格式错误，停止重连')
              return
            }
            // token有效但认证失败，可能是服务器问题，停止重连避免无限循环
            this.log('Token有效但认证失败，停止重连以避免无限循环')
            return
          }
          
          // 如果不是主动关闭，尝试重连
          if (event.code !== 1000) {
            this.handleReconnect()
          }
        }
        
        this.ws.onerror = (error) => {
          this.log('WebSocket连接错误', error)
          this.setStatus(WebSocketStatus.ERROR)
          reject(error)
        }
        
      } catch (error) {
        this.log('创建WebSocket连接失败', error)
        reject(error)
      }
    })
  }
  
  /**
   * 断开WebSocket连接
   */
  disconnect(): void {
    this.log('主动断开WebSocket连接')
    
    this.stopHeartbeat()
    this.stopReconnect()
    
    if (this.ws) {
      this.ws.close(1000, '主动断开')
      this.ws = null
    }
    
    this.setStatus(WebSocketStatus.DISCONNECTED)
  }
  
  /**
   * 发送消息
   */
  send(type: WebSocketMessageType, data: any = {}): boolean {
    if (!this.isConnected()) {
      this.log('WebSocket未连接，无法发送消息')
      return false
    }
    
    try {
      const message = {
        type,
        data,
        timestamp: new Date().toISOString()
      }
      
      this.ws!.send(JSON.stringify(message))
      this.log('发送消息', message)
      return true
      
    } catch (error) {
      this.log('发送消息失败', error)
      return false
    }
  }
  
  /**
   * 订阅消息类型
   */
  subscribe(type: WebSocketMessageType, handler: MessageHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set())
    }
    
    this.messageHandlers.get(type)!.add(handler)
    this.log(`订阅消息类型: ${type}`)
  }
  
  /**
   * 取消订阅消息类型
   */
  unsubscribe(type: WebSocketMessageType, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      handlers.delete(handler)
      if (handlers.size === 0) {
        this.messageHandlers.delete(type)
      }
    }
    
    this.log(`取消订阅消息类型: ${type}`)
  }
  
  /**
   * 监听状态变化
   */
  onStatusChange(callback: (status: WebSocketStatus) => void): void {
    this.statusChangeCallbacks.add(callback)
  }
  
  /**
   * 移除状态变化监听
   */
  offStatusChange(callback: (status: WebSocketStatus) => void): void {
    this.statusChangeCallbacks.delete(callback)
  }
  
  /**
   * 获取当前状态
   */
  getStatus(): WebSocketStatus {
    return this.status
  }
  
  /**
   * 检查是否已连接
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
  
  /**
   * 处理收到的消息
   */
  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data)
      const { type, data: payload } = message
      
      this.log('收到消息', message)
      
      // 处理特殊消息类型
      if (type === WebSocketMessageType.PONG) {
        this.log('收到心跳响应')
        return
      }
      
      if (type === WebSocketMessageType.CONNECTION_ESTABLISHED) {
        this.log('连接建立确认', payload)
        ElMessage.success('实时连接已建立')
        return
      }
      
      // 分发消息给处理器
      const handlers = this.messageHandlers.get(type as WebSocketMessageType)
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(payload)
          } catch (error) {
            this.log('消息处理器执行失败', error)
          }
        })
      }
      
      // 处理特定消息类型的默认行为
      this.handleDefaultMessage(type, payload)
      
    } catch (error) {
      this.log('解析消息失败', error)
    }
  }
  
  /**
   * 处理默认消息行为
   */
  private handleDefaultMessage(type: string, payload: any): void {
    switch (type) {
      case WebSocketMessageType.RISK_ALERT:
        // 显示风险警报通知
        ElNotification({
          title: '风险警报',
          message: payload.message || '检测到风险事件',
          type: 'warning',
          duration: 0 // 不自动关闭
        })
        break
        
      case WebSocketMessageType.SYSTEM_STATUS:
        // 处理系统状态更新
        if (payload.status === 'maintenance') {
          ElNotification({
            title: '系统维护',
            message: payload.message || '系统正在维护中',
            type: 'info'
          })
        }
        break
        
      case WebSocketMessageType.AI_DECISION:
        // 显示AI决策通知
        ElNotification({
          title: 'AI决策',
          message: `新的AI决策: ${payload.action || '未知操作'}`,
          type: 'info'
        })
        break
    }
  }
  
  /**
   * 处理重连
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.log('达到最大重连次数，停止重连')
      ElMessage.error('连接已断开，请刷新页面重试')
      return
    }
    
    this.setStatus(WebSocketStatus.RECONNECTING)
    this.reconnectAttempts++
    
    const delay = this.reconnectInterval * this.reconnectAttempts
    this.log(`${delay}ms后尝试第${this.reconnectAttempts}次重连`)
    
    this.reconnectTimer = window.setTimeout(() => {
      this.connect().catch(error => {
        this.log('重连失败', error)
      })
    }, delay)
  }
  
  /**
   * 开始心跳检测
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    
    this.heartbeatTimer = window.setInterval(() => {
      if (this.isConnected()) {
        this.send(WebSocketMessageType.PING)
      }
    }, this.heartbeatInterval)
  }
  
  /**
   * 停止心跳检测
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
  
  /**
   * 停止重连
   */
  private stopReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
  
  /**
   * 设置状态
   */
  private setStatus(status: WebSocketStatus): void {
    if (this.status !== status) {
      this.status = status
      this.statusChangeCallbacks.forEach(callback => {
        try {
          callback(status)
        } catch (error) {
          this.log('状态变化回调执行失败', error)
        }
      })
    }
  }
  
  /**
   * 获取WebSocket URL
   */
  private getWebSocketUrl(token: string): string {
    // 从环境变量获取WebSocket URL，如果没有则使用默认值
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8765'
    return `${wsUrl}?token=${encodeURIComponent(token)}`
  }
  
  /**
   * 日志输出
   */
  private log(message: string, ...args: any[]): void {
    if (this.debug) {
      console.log(`[WebSocket] ${message}`, ...args)
    }
  }
}

// 全局WebSocket客户端实例
export const websocketClient = new WebSocketClient({
  debug: import.meta.env.DEV
})

// 自动连接和断开
let isInitialized = false

export function initWebSocket(): Promise<void> {
  if (isInitialized) {
    return Promise.resolve()
  }
  
  isInitialized = true
  
  // 监听页面可见性变化
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // 页面隐藏时断开连接
      websocketClient.disconnect()
    } else {
      // 页面显示时重新连接
      const token = localStorage.getItem('token')
      if (token) {
        websocketClient.connect().catch(console.error)
      }
    }
  })
  
  // 监听窗口关闭
  window.addEventListener('beforeunload', () => {
    websocketClient.disconnect()
  })
  
  return websocketClient.connect()
}

export function destroyWebSocket(): void {
  websocketClient.disconnect()
  isInitialized = false
}