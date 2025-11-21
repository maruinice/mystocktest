import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './routers'
import '@/styles/index.scss'
import { initWebSocket } from './utils/websocket'

// 性能监控
const startTime = performance.now()

// 创建应用实例
const app = createApp(App)

// 注册Element Plus图标（按需注册，减少初始化时间）
const iconComponents = [
  'ArrowDown', 'ArrowUp', 'Check', 'Close', 'Delete', 'Edit', 'Plus', 
  'Refresh', 'Search', 'Setting', 'User', 'Warning', 'Loading',
  'VideoStop', 'VideoPause', 'VideoPlay', 'MagicStick', 'CircleClose',
  'ChatDotRound', 'Document', 'TrendCharts', 'QuestionFilled', 'View',
  'DataAnalysis', 'CopyDocument', 'Clock', 'Download'
]

iconComponents.forEach(name => {
  if ((ElementPlusIconsVue as any)[name]) {
    app.component(name, (ElementPlusIconsVue as any)[name])
  }
})

// 注册 Magic 作为 MagicStick 的别名（Element Plus 图标库中没有 Magic，只有 MagicStick）
if ((ElementPlusIconsVue as any)['MagicStick']) {
  app.component('Magic', (ElementPlusIconsVue as any)['MagicStick'])
}

// 延迟注册其他图标
setTimeout(() => {
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    if (!iconComponents.includes(key)) {
      app.component(key, component)
    }
  }
}, 100)

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

// 初始化认证状态（确保拦截器与路由守卫能拿到token与用户信息）
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore(pinia)

// 异步初始化，不阻塞应用启动
const initializeApp = async () => {
  try {
    await authStore.initialize()
    
    // 如果用户已登录，延迟初始化WebSocket连接
    if (authStore.isAuthenticated) {
      setTimeout(() => {
        initWebSocket().catch(console.error)
      }, 1000)
    }
  } catch (error) {
    console.error('应用初始化失败:', error)
  }
}

// 挂载应用
app.mount('#app')

// 移除加载动画
const loadingElement = document.getElementById('loading')
if (loadingElement) {
  setTimeout(() => {
    loadingElement.style.opacity = '0'
    setTimeout(() => {
      loadingElement.remove()
    }, 300)
  }, 500)
}

// 异步初始化
initializeApp()

// 性能监控
const endTime = performance.now()
console.log(`应用启动耗时: ${(endTime - startTime).toFixed(2)}ms`)

// 预加载关键路由组件
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => {
    // 预加载登录页面
    import('@/views/auth/Login.vue').catch(() => {})
    // 预加载仪表盘
    import('@/views/dashboard/Dashboard.vue').catch(() => {})
  })
}