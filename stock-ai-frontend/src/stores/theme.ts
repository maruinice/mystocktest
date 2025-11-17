import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'auto'

export const useThemeStore = defineStore('theme', () => {
  // 状态
  const mode = ref<ThemeMode>('auto')
  const isDark = ref(false)

  // 初始化主题
  const initTheme = () => {
    const savedMode = localStorage.getItem('theme-mode') as ThemeMode
    if (savedMode) {
      mode.value = savedMode
    }
    applyTheme()
  }

  // 应用主题
  const applyTheme = () => {
    const html = document.documentElement
    
    if (mode.value === 'auto') {
      // 自动模式：根据系统偏好设置
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      isDark.value = mediaQuery.matches
    } else {
      isDark.value = mode.value === 'dark'
    }

    if (isDark.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  // 切换主题模式
  const setThemeMode = (newMode: ThemeMode) => {
    mode.value = newMode
    localStorage.setItem('theme-mode', newMode)
    applyTheme()
  }

  // 监听系统主题变化
  const watchSystemTheme = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', () => {
      if (mode.value === 'auto') {
        applyTheme()
      }
    })
  }

  return {
    // 状态
    mode: readonly(mode),
    isDark: readonly(isDark),
    
    // 方法
    initTheme,
    setThemeMode,
    watchSystemTheme
  }
})