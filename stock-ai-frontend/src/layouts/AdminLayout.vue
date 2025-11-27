<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
      <div class="logo">
        <el-icon v-if="isCollapse" size="24"><TrendCharts /></el-icon>
        <span v-else class="logo-text">迅龙AI股票交易</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :unique-opened="true"
        @select="handleMenuSelect"
        class="sidebar-menu"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/trading">
          <el-icon><TrendCharts /></el-icon>
          <template #title>交易中心</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/portfolio">
          <el-icon><PieChart /></el-icon>
          <template #title>投资组合</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/strategy">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>策略管理</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/screening">
          <el-icon><Search /></el-icon>
          <template #title>智能选股</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/analysis">
          <el-icon><DataLine /></el-icon>
          <template #title>数据分析</template>
        </el-menu-item>
        
        <el-sub-menu index="ai">
          <template #title>
            <el-icon><MagicStick /></el-icon>
            <span>AI功能</span>
          </template>
          <el-menu-item index="/admin/ai/models">LLM模型配置</el-menu-item>
          <el-menu-item index="/admin/ai/agents/workbench">Agent工作台</el-menu-item>
          <el-menu-item index="/admin/ai/agents/analysis">多Agent分析</el-menu-item>
          <el-menu-item index="/admin/ai/decision">AI决策</el-menu-item>
          <!-- <el-menu-item index="/admin/ai/risk">风险控制</el-menu-item> -->
        </el-sub-menu>
        
        <el-sub-menu index="data-management">
          <template #title>
            <el-icon><DataAnalysis /></el-icon>
            <span>数据管理</span>
          </template>
          <el-menu-item index="/admin/data-management/data-sources">数据源管理</el-menu-item>
          <el-menu-item index="/admin/data-management/api-management">API管理</el-menu-item>
          <el-menu-item index="/admin/data-management/data-sync">数据同步</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/admin/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区域 -->
    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <el-button
            text
            @click="toggleCollapse"
            class="collapse-btn"
          >
            <el-icon size="20">
              <Expand v-if="isCollapse" />
              <Fold v-else />
            </el-icon>
          </el-button>
          
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 通知 -->
          <el-badge :value="12" class="notification">
            <el-button text>
              <el-icon size="18"><Bell /></el-icon>
            </el-button>
          </el-badge>
          
          <!-- 用户菜单 -->
          <el-dropdown @command="handleUserCommand">
            <div class="user-info">
              <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
              <span class="username">{{ userStore.user && userStore.user.username ? userStore.user.username : 'Admin' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                <el-dropdown-item command="settings">账户设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 页面内容 -->
      <el-main class="main-content">
        <router-view :key="$route.fullPath" />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const userStore = useAuthStore()

const isCollapse = ref(false)

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  const breadcrumbItems = matched.map(item => ({
    path: item.path,
    title: item.meta?.title as string
  }))
  
  // 添加首页
  if (breadcrumbItems.length > 0 && breadcrumbItems[0].path !== '/admin/dashboard') {
    breadcrumbItems.unshift({ path: '/admin/dashboard', title: '首页' })
  }
  
  return breadcrumbItems
})

// 切换侧边栏折叠状态
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 处理菜单选择
const handleMenuSelect = (index: string) => {
  console.log('菜单选择:', index)
  
  // 直接进行路由跳转
  if (route.path !== index) {
    router.push(index).catch((error) => {
      console.error('路由跳转失败:', error)
    })
  }
}

// 处理用户菜单命令
const handleUserCommand = async (command: string) => {
  const { ElMessage, ElMessageBox } = await import('element-plus')
  switch (command) {
    case 'profile':
      ElMessage.info('个人资料功能开发中')
      break
    case 'settings':
      router.push('/admin/settings')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确认退出登录？', '提示', {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await userStore.logout()
        ElMessage.success('已退出登录')
        router.push('/login')
      } catch (error) {
        // 用户取消
      }
      break
  }
}

// 监听路由变化，确保页面正确更新
watch(
  () => route.path,
  (newPath, oldPath) => {
    // 强制更新菜单激活状态
    nextTick(() => {
      // 确保菜单项正确高亮
      const menuEl = document.querySelector('.sidebar-menu')
      if (menuEl) {
        // 触发菜单重新渲染
        menuEl.dispatchEvent(new Event('resize'))
      }
    })
    
    // 调试信息
    console.log('路由变化:', { from: oldPath, to: newPath })
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
.admin-layout {
  height: 100vh;
  display: flex;
}

.sidebar {
  background: var(--el-bg-color-overlay);
  border-right: 1px solid var(--el-border-color-light);
  transition: width 0.3s ease;
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid var(--el-border-color-light);
    
    .logo-text {
      font-size: 18px;
      font-weight: 600;
      color: var(--el-color-primary);
    }
  }
  
  .sidebar-menu {
    border: none;
    height: calc(100vh - 60px);
    
    .el-menu-item,
    .el-sub-menu__title {
      height: 48px;
      line-height: 48px;
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.header {
  background: var(--el-bg-color-overlay);
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .collapse-btn {
      padding: 8px;
    }
    
    .breadcrumb {
      font-size: 14px;
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .notification {
      .el-button {
        padding: 8px;
      }
    }
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 6px;
      transition: background-color 0.3s ease;
      
      &:hover {
        background: var(--el-fill-color-light);
      }
      
      .username {
        font-size: 14px;
        color: var(--el-text-color-primary);
      }
    }
  }
}

.main-content {
  background: var(--el-bg-color-page);
  padding: 20px;
  overflow-y: auto;
}

// 响应式设计
@media (max-width: 768px) {
  .admin-layout {
    .sidebar {
      position: fixed;
      left: 0;
      top: 0;
      z-index: 1000;
      height: 100vh;
    }
    
    .main-container {
      margin-left: 0;
    }
    
    .header {
      .breadcrumb {
        display: none;
      }
    }
  }
}
</style>