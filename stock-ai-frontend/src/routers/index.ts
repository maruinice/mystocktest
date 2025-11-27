import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/admin/dashboard'
  },
  {
    path: '/test',
    name: 'Test',
    component: () => import('../views/test/Test.vue'),
    meta: {
      title: '测试页面',
      requiresAuth: false
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  // 管理后台路由 - 使用统一布局
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'),
    redirect: '/admin/dashboard',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/Dashboard.vue'),
        meta: {
          title: '仪表盘',
          requiresAuth: true
        }
      },
      {
        path: 'trading',
        name: 'Trading',
        component: () => import('../views/trading/Trading.vue'),
        meta: {
          title: '交易中心',
          requiresAuth: true
        }
      },
      {
        path: 'portfolio',
        name: 'Portfolio',
        component: () => import('../views/portfolio/Portfolio.vue'),
        meta: {
          title: '投资组合',
          requiresAuth: true
        }
      },
      {
        path: 'strategy',
        name: 'Strategy',
        component: () => import('../views/strategy/Strategy.vue'),
        meta: {
          title: '策略管理',
          requiresAuth: true
        }
      },
      {
        path: 'analysis',
        name: 'Analysis',
        component: () => import('../views/analysis/Analysis.vue'),
        meta: {
          title: '数据分析',
          requiresAuth: true
        }
      },
      {
        path: 'screening',
        name: 'Screening',
        component: () => import('../views/screening/Screening.vue'),
        meta: {
          title: '智能选股',
          requiresAuth: true
        }
      },
      {
        path: 'ai/decision',
        name: 'AIDecision',
        component: () => import('../views/ai/Decision.vue'),
        meta: {
          title: 'AI决策',
          requiresAuth: true
        }
      },
      {
        path: 'ai/risk',
        name: 'AIRisk',
        component: () => import('../views/ai/Risk.vue'),
        meta: {
          title: '风险控制',
          requiresAuth: true
        }
      },
      {
        path: 'ai/models',
        name: 'AIModels',
        component: () => import('../views/ai/Models.vue'),
        meta: {
          title: 'LLM模型配置',
          requiresAuth: true
        }
      },
      {
        path: 'ai/agents/workbench',
        name: 'AgentWorkbench',
        component: () => import('../views/ai/agents/AgentWorkbench.vue'),
        meta: {
          title: 'Agent工作台',
          requiresAuth: true
        }
      },
      {
        path: 'ai/agents/analysis',
        name: 'MultiAgentAnalysis',
        component: () => import('../views/ai/agents/MultiAgentAnalysis.vue'),
        meta: {
          title: '多Agent分析',
          requiresAuth: true
        }
      },
      // 数据管理路由
      {
        path: 'data-management/data-sources',
        name: 'DataSourceManagement',
        component: () => import('../views/data-management/DataSourceManagement.vue'),
        meta: {
          title: '数据源管理',
          requiresAuth: true
        }
      },
      {
        path: 'data-management/api-management',
        name: 'ApiManagement',
        component: () => import('../views/data-management/ApiManagement.vue'),
        meta: {
          title: 'API管理',
          requiresAuth: true
        }
      },
      {
        path: 'data-management/data-sync',
        name: 'DataSync',
        component: () => import('../views/data-management/DataSync.vue'),
        meta: {
          title: '数据同步',
          requiresAuth: true
        }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/settings/Settings.vue'),
        meta: {
          title: '系统设置',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/error/NotFound.vue'),
    meta: {
      title: '页面未找到',
      requiresAuth: false
    }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫 - 启用认证检查
router.beforeEach(async (to, _from, next) => {
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 迅龙AI股票交易系统`
  }

  const requiresAuth = to.meta?.requiresAuth === true
  if (!requiresAuth) {
    return next()
  }

  try {
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()

    // 已登录直接放行
    if (authStore.isAuthenticated) {
      return next()
    }
    // 本地有缓存但未验证，尝试初始化/验证
    await authStore.initialize()
    if (authStore.isAuthenticated) {
      return next()
    }
  } catch (e) {
    // ignore
  }

  next({ path: '/login', query: { redirect: to.fullPath } })
})

export default router