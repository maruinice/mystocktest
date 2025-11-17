import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { compression } from 'vite-plugin-compression2'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vitejs.dev/config/
export default defineConfig({
  root: process.cwd(),
  publicDir: 'public',
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: [
        'vue',
        'vue-router',
        'pinia',
        {
          'element-plus': [
            'ElMessage',
            'ElMessageBox',
            'ElNotification',
            'ElLoading'
          ]
        }
      ],
      dts: true,
      eslintrc: {
        enabled: true
      }
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: true
    }),
    // Gzip压缩
    compression({
      algorithm: 'gzip',
      exclude: [/\.(br)$ /, /\.(gz)$/]
    }),
    // Brotli压缩
    compression({
      algorithm: 'brotliCompress',
      exclude: [/\.(br)$ /, /\.(gz)$/]
    }),
    // 打包分析
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@views': resolve(__dirname, 'src/views'),
      '@stores': resolve(__dirname, 'src/stores'),
      '@api': resolve(__dirname, 'src/api'),
      '@types': resolve(__dirname, 'src/types'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@assets': resolve(__dirname, 'src/assets'),
      '@styles': resolve(__dirname, 'src/styles')
    }
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    open: true,
    cors: true,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    target: 'es2015',
    cssTarget: 'chrome80',
    // 启用CSS代码分割
    cssCodeSplit: true,
    // 减少包大小警告阈值
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          let extType = info[info.length - 1]
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name)) {
            extType = 'media'
          } else if (/\.(png|jpe?g|gif|svg)(\?.*)?$/i.test(assetInfo.name)) {
            extType = 'img'
          } else if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name)) {
            extType = 'fonts'
          }
          return `${extType}/[name]-[hash].[ext]`
        },
        manualChunks: (id) => {
          // 第三方库分包
          if (id.includes('node_modules')) {
            if (id.includes('vue') || id.includes('vue-router') || id.includes('pinia')) {
              return 'vue-vendor'
            }
            if (id.includes('element-plus')) {
              return 'element-plus'
            }
            if (id.includes('echarts')) {
              return 'echarts'
            }
            if (id.includes('axios') || id.includes('dayjs') || id.includes('lodash')) {
              return 'utils'
            }
            return 'vendor'
          }
          // 页面组件分包
          if (id.includes('/views/')) {
            const dirs = id.split('/views/')[1].split('/')
            return `page-${dirs[0]}`
          }
        }
      },
      // 外部化依赖
      external: [],
      // 优化选项
      treeshake: {
        preset: 'recommended',
        manualPureFunctions: ['console.log', 'console.info']
      }
    },
    // Terser压缩选项
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info'],
        passes: 2
      },
      mangle: {
        safari10: true
      },
      format: {
        comments: false
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`,
        charset: false
      }
    },
    postcss: {
      plugins: []
    }
  },
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'element-plus/es',
      'element-plus/es/components/message/style/css',
      'element-plus/es/components/message-box/style/css',
      'element-plus/es/components/notification/style/css',
      'element-plus/es/components/loading/style/css',
      '@element-plus/icons-vue',
      'echarts',
      'vue-echarts',
      'axios',
      'dayjs',
      'lodash-es'
    ],
    // 强制预构建
    force: false,
    // 排除预构建
    exclude: ['@vueuse/core']
  },
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false
  }
})