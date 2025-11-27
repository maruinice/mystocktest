# 迅龙AI股票交易系统 - 前端

基于 Vue 3 + TypeScript 的现代化股票交易系统前端应用。

## 技术栈

- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **UI组件库**: Element Plus
- **图表库**: ECharts + Vue-ECharts
- **HTTP客户端**: Axios
- **样式**: SCSS

## 项目结构

```
stock-ai-frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 公共组件
│   ├── views/             # 页面组件
│   │   ├── auth/          # 认证相关页面
│   │   ├── dashboard/     # 仪表盘
│   │   ├── trading/       # 交易中心
│   │   ├── portfolio/     # 投资组合
│   │   ├── strategy/      # 策略管理
│   │   ├── analysis/      # 数据分析
│   │   ├── settings/      # 系统设置
│   │   └── error/         # 错误页面
│   ├── stores/            # Pinia状态管理
│   │   ├── auth.ts        # 认证状态
│   │   ├── theme.ts       # 主题状态
│   │   └── trading.ts     # 交易状态
│   ├── routers/           # 路由配置
│   ├── api/              # API接口
│   │   ├── auth.ts        # 认证接口
│   │   ├── trading.ts     # 交易接口
│   │   └── data.ts        # 数据接口
│   ├── types/            # TypeScript类型定义
│   │   ├── auth.ts        # 认证类型
│   │   ├── trading.ts     # 交易类型
│   │   └── data.ts        # 数据类型
│   ├── utils/            # 工具函数
│   │   ├── request.ts     # HTTP请求工具
│   │   └── format.ts      # 格式化工具
│   ├── assets/           # 静态资源
│   └── styles/           # 样式文件
│       ├── variables.scss # SCSS变量
│       └── index.scss     # 全局样式
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

## 功能特性

### 🔐 用户认证
- 用户登录/注册
- JWT Token 认证
- 路由守卫
- 权限控制

### 📊 仪表盘
- 资产概览
- 实时数据展示
- 图表可视化
- 快速操作入口

### 💹 交易功能
- 股票搜索
- 实时行情
- 下单交易
- 订单管理
- 持仓查看

### 📈 数据分析
- K线图表
- 技术指标
- 财务数据
- 市场分析

### ⚙️ 系统设置
- 主题切换
- 个人设置
- 系统配置

## 开发环境要求

- Node.js >= 18.0.0
- npm >= 8.0.0

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产版本

```bash
npm run preview
```

## 开发脚本

```bash
# 开发服务器
npm run dev

# 类型检查
npm run type-check

# 构建
npm run build

# 预览
npm run preview

# 代码检查
npm run lint

# 代码格式化
npm run format
```

## 环境变量

创建 `.env.local` 文件配置环境变量：

```env
# API基础URL
VITE_API_BASE_URL=http://127.0.0.1:5000/api

# 应用标题
VITE_APP_TITLE=迅龙AI股票交易系统

# 应用版本
VITE_APP_VERSION=1.0.0
```

## API接口

后端API服务运行在 `http://127.0.0.1:5000`，主要接口包括：

- `/api/auth/*` - 认证相关
- `/api/trade/*` - 交易相关
- `/api/data/*` - 数据相关
- `/api/strategy/*` - 策略相关
- `/api/system/*` - 系统相关

## 主要依赖

### 生产依赖
- `vue`: Vue 3 框架
- `vue-router`: 路由管理
- `pinia`: 状态管理
- `element-plus`: UI组件库
- `echarts`: 图表库
- `axios`: HTTP客户端

### 开发依赖
- `vite`: 构建工具
- `typescript`: TypeScript支持
- `vue-tsc`: Vue TypeScript编译器
- `sass`: SCSS预处理器
- `eslint`: 代码检查
- `prettier`: 代码格式化

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。