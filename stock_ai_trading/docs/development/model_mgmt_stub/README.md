# 模型管理占位接口（临时方案）

目的：在 `app/models/model_management.py` 存在编码损坏导致无法导入的情况下，提供基本的模型管理端点以保证前端预检与页面加载不报错。

当前改动：
- 前端：`src/api/model-management.ts` 去除本地 `'/api'` 前缀，避免与全局 `baseURL('/api')` 重复产生 `'/api/api'`。
- 后端：新增 `app/api/model_management_stub.py`，提供以下端点（只返回空数据/默认统计）：
  - `GET /api/models`
  - `GET /api/ensembles`
  - `GET /api/dashboard/stats`
  - `GET /api/dashboard/performance`
  - `GET /api/models/health`
- 后端：`run_flask.py` 中对模型管理蓝图的加载增加回退逻辑，真实模块失败时加载占位蓝图。

影响与限制：
- 以上端点为占位返回，数据为空或默认值，仅用于保证路由存在和 CORS 预检（OPTIONS）通过。
- 实际业务（创建/编辑模型、组合、测试记录等）不可用，需修复模型定义文件后恢复。

后续修复计划：
1. 修复 `app/models/model_management.py` 的文件编码与损坏字符（移除所有 `U+FFFD`），确保可被 Python 正常解析。
2. 恢复真实蓝图 `app/api/model_management_flask.py` 的导入与注册，移除占位蓝图。
3. 完整回归测试：
   - 模型/组合 CRUD
   - 仪表盘统计与性能指标
   - 认证与权限校验

验收标准（临时方案）：
- 前端不再出现 `OPTIONS /api/api/... 404` 日志。
- `OPTIONS /api/models`、`/api/ensembles`、`/api/dashboard/stats` 返回 `200`。
- 后端启动日志显示“已加载模型管理占位接口，提供基本端点”。