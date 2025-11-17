# 数据库表与Tushare接口映射关系

根据数据库表结构和代码分析，统计实际使用的Tushare接口及数据写入情况。

## 📊 总体统计

| 类别 | 数据库表数量 | Tushare接口数量 | 同步状态 |
|-----|------------|----------------|---------|
| 基础数据 | 3 | 2 | ✅ 完成 |
| 行情数据 | 6 | 5 | ✅ 完成 |
| 财务数据 | 2 | 4 | ✅ 完成 |
| 行业分类 | 1 | 2 | ✅ 完成 |
| 审计意见 | 1 | 1 | 🔄 进行中 |
| 停复牌 | 1 | 1 | ✅ 完成 |
| 涨跌停 | 1 | 1 | ✅ 完成 |
| 资金流向 | 1 | 1 | ⚠️ 未同步 |
| 业务表 | 30+ | - | - |
| **总计** | **52** | **23** | - |

---

## 1️⃣ 基础数据表 (3个)

### 1.1 stock_basic - 股票基础信息
- **Tushare接口**: `pro.stock_basic()`
- **同步脚本**: 
  - `app/services/tushare_daily_service.py` - `sync_stock_basic()`
  - `sync_stock_basic_simple.py`
  - `full_import.py`
- **字段映射**:
  ```
  ts_code → ts_code
  symbol → symbol
  name → name
  area → area
  industry → industry
  market → market
  list_date → list_date
  ```
- **同步状态**: ✅ 已完成 (5,582条)
- **更新频率**: 每日
- **使用场景**: 
  - 选股服务基础数据
  - 回测引擎股票列表
  - 数据同步股票范围

### 1.2 trade_cal - 交易日历
- **Tushare接口**: `pro.trade_cal()`
- **同步脚本**: `app/services/tushare_daily_service.py` - `sync_trade_calendar()`
- **字段映射**:
  ```
  exchange → exchange
  cal_date → cal_date
  is_open → is_open
  pretrade_date → pretrade_date
  ```
- **同步状态**: ✅ 已完成
- **更新频率**: 每日
- **使用场景**: 
  - 回测引擎交易日判断
  - 数据同步日期范围

### 1.3 stock_quotes - 股票行情（未使用）
- **说明**: 表存在但未使用，数据存储在daily_history和daily_basic中

---

## 2️⃣ 行情数据表 (6个)

### 2.1 daily_history - 日线行情
- **Tushare接口**: `pro.daily()`
- **同步脚本**: `app/services/tushare_daily_service.py` - `sync_daily_data()`
- **字段映射**:
  ```
  ts_code → ts_code
  trade_date → trade_date
  open → open
  high → high
  low → low
  close → close
  pre_close → pre_close
  change → change
  pct_chg → pct_chg
  vol → vol
  amount → amount
  ```
- **同步状态**: ✅ 已完成 (数百万条)
- **更新频率**: 每日
- **使用场景**: 
  - 回测引擎价格数据
  - 选股服务价格筛选
  - 技术指标计算

### 2.2 daily_basic - 每日指标
- **Tushare接口**: `pro.daily_basic()`
- **同步脚本**: `app/services/tushare_daily_service.py` - `sync_daily_basic()`
- **字段映射**:
  ```
  ts_code → ts_code
  trade_date → trade_date
  close → close
  turnover_rate → turnover_rate
  turnover_rate_f → turnover_rate_f
  volume_ratio → volume_ratio
  pe → pe
  pe_ttm → pe_ttm
  pb → pb
  ps → ps
  ps_ttm → ps_ttm
  dv_ratio → dv_ratio
  dv_ttm → dv_ttm
  total_share → total_share
  float_share → float_share
  free_share → free_share
  total_mv → total_mv
  circ_mv → circ_mv
  ```
- **同步状态**: ✅ 已完成 (数百万条)
- **更新频率**: 每日
- **使用场景**: 
  - 选股服务估值筛选
  - 回测引擎市值数据

### 2.3 adj_factor - 复权因子
- **Tushare接口**: `pro.adj_factor()`
- **同步脚本**: `app/services/tushare_daily_service.py` - `sync_adj_factor()`
- **字段映射**:
  ```
  ts_code → ts_code
  trade_date → trade_date
  adj_factor → adj_factor
  ```
- **同步状态**: ✅ 已完成
- **更新频率**: 每日
- **使用场景**: 
  - 回测引擎复权价格计算

### 2.4 daily_quotes - 日线报价（未使用）
- **说明**: 表存在但未使用

### 2.5 limit_prices - 涨跌停价格
- **Tushare接口**: `pro.stk_limit()`
- **同步脚本**: `app/services/tushare_enhanced_service.py` - `get_stk_limit()`
- **字段映射**:
  ```
  trade_date → trade_date
  ts_code → ts_code
  up_limit → up_limit
  down_limit → down_limit
  ```
- **同步状态**: ✅ 已完成
- **更新频率**: 每日
- **使用场景**: 
  - 回测引擎涨跌停判断
  - 选股服务过滤涨跌停

### 2.6 suspend_info - 停复牌信息
- **Tushare接口**: `pro.suspend_d()`
- **同步脚本**: `app/services/tushare_enhanced_service.py` - `get_suspend_data()`
- **字段映射**:
  ```
  ts_code → ts_code
  trade_date → trade_date
  suspend_type → suspend_type
  suspend_timing → suspend_timing
  ```
- **同步状态**: ✅ 已完成
- **更新频率**: 每日
- **使用场景**: 
  - 回测引擎停牌判断
  - 选股服务过滤停牌股

---

## 3️⃣ 财务数据表 (2个)

### 3.1 financial_indicators - 财务指标
- **Tushare接口**: `pro.fina_indicator()`
- **同步脚本**: `sync_financial_indicators.py`
- **字段映射**:
  ```
  ts_code → ts_code
  ann_date → ann_date
  end_date → end_date
  eps → eps
  dt_eps → dt_eps
  total_revenue_ps → total_revenue_ps
  revenue_ps → revenue_ps
  capital_rese_ps → capital_rese_ps
  surplus_rese_ps → surplus_rese_ps
  undist_profit_ps → undist_profit_ps
  extra_item → extra_item
  profit_dedt → profit_dedt
  gross_margin → gross_margin
  current_ratio → current_ratio
  quick_ratio → quick_ratio
  cash_ratio → cash_ratio
  invturn_days → invturn_days
  arturn_days → arturn_days
  inv_turn → inv_turn
  ar_turn → ar_turn
  ca_turn → ca_turn
  fa_turn → fa_turn
  assets_turn → assets_turn
  op_income → op_income
  valuechange_income → valuechange_income
  interst_income → interst_income
  daa → daa
  ebit → ebit
  ebitda → ebitda
  fcff → fcff
  fcfe → fcfe
  current_exint → current_exint
  noncurrent_exint → noncurrent_exint
  interestdebt → interestdebt
  netdebt → netdebt
  tangible_asset → tangible_asset
  working_capital → working_capital
  networking_capital → networking_capital
  invest_capital → invest_capital
  retained_earnings → retained_earnings
  diluted2_eps → diluted2_eps
  bps → bps
  ocfps → ocfps
  retainedps → retainedps
  cfps → cfps
  ebit_ps → ebit_ps
  fcff_ps → fcff_ps
  fcfe_ps → fcfe_ps
  netprofit_margin → netprofit_margin
  grossprofit_margin → grossprofit_margin
  cogs_of_sales → cogs_of_sales
  expense_of_sales → expense_of_sales
  profit_to_gr → profit_to_gr
  saleexp_to_gr → saleexp_to_gr
  adminexp_of_gr → adminexp_of_gr
  finaexp_of_gr → finaexp_of_gr
  impai_ttm → impai_ttm
  gc_of_gr → gc_of_gr
  op_of_gr → op_of_gr
  ebit_of_gr → ebit_of_gr
  roe → roe
  roe_waa → roe_waa
  roe_dt → roe_dt
  roa → roa
  npta → npta
  roic → roic
  roe_yearly → roe_yearly
  roa_yearly → roa_yearly
  roe_avg → roe_avg
  opincome_of_ebt → opincome_of_ebt
  investincome_of_ebt → investincome_of_ebt
  n_op_profit_of_ebt → n_op_profit_of_ebt
  tax_to_ebt → tax_to_ebt
  dtprofit_to_profit → dtprofit_to_profit
  salescash_to_or → salescash_to_or
  ocf_to_or → ocf_to_or
  ocf_to_opincome → ocf_to_opincome
  capitalized_to_da → capitalized_to_da
  debt_to_assets → debt_to_assets
  assets_to_eqt → assets_to_eqt
  dp_assets_to_eqt → dp_assets_to_eqt
  ca_to_assets → ca_to_assets
  nca_to_assets → nca_to_assets
  tbassets_to_totalassets → tbassets_to_totalassets
  int_to_talcap → int_to_talcap
  eqt_to_talcapital → eqt_to_talcapital
  currentdebt_to_debt → currentdebt_to_debt
  longdeb_to_debt → longdeb_to_debt
  ocf_to_shortdebt → ocf_to_shortdebt
  debt_to_eqt → debt_to_eqt
  eqt_to_debt → eqt_to_debt
  eqt_to_interestdebt → eqt_to_interestdebt
  tangibleasset_to_debt → tangibleasset_to_debt
  tangasset_to_intdebt → tangasset_to_intdebt
  tangibleasset_to_netdebt → tangibleasset_to_netdebt
  ocf_to_debt → ocf_to_debt
  ocf_to_interestdebt → ocf_to_interestdebt
  ocf_to_netdebt → ocf_to_netdebt
  ebit_to_interest → ebit_to_interest
  longdebt_to_workingcapital → longdebt_to_workingcapital
  ebitda_to_debt → ebitda_to_debt
  turn_days → turn_days
  roa_yearly → roa_yearly
  roa_dp → roa_dp
  fixed_assets → fixed_assets
  profit_prefin_exp → profit_prefin_exp
  non_op_profit → non_op_profit
  op_to_ebt → op_to_ebt
  nop_to_ebt → nop_to_ebt
  ocf_to_profit → ocf_to_profit
  cash_to_liqdebt → cash_to_liqdebt
  cash_to_liqdebt_withinterest → cash_to_liqdebt_withinterest
  op_to_liqdebt → op_to_liqdebt
  op_to_debt → op_to_debt
  roic_yearly → roic_yearly
  total_fa_trun → total_fa_trun
  profit_to_op → profit_to_op
  q_opincome → q_opincome
  q_investincome → q_investincome
  q_dtprofit → q_dtprofit
  q_eps → q_eps
  q_netprofit_margin → q_netprofit_margin
  q_gsprofit_margin → q_gsprofit_margin
  q_exp_to_sales → q_exp_to_sales
  q_profit_to_gr → q_profit_to_gr
  q_saleexp_to_gr → q_saleexp_to_gr
  q_adminexp_to_gr → q_adminexp_to_gr
  q_finaexp_to_gr → q_finaexp_to_gr
  q_impair_to_gr_ttm → q_impair_to_gr_ttm
  q_gc_to_gr → q_gc_to_gr
  q_op_to_gr → q_op_to_gr
  q_roe → q_roe
  q_dt_roe → q_dt_roe
  q_npta → q_npta
  q_opincome_to_ebt → q_opincome_to_ebt
  q_investincome_to_ebt → q_investincome_to_ebt
  q_dtprofit_to_profit → q_dtprofit_to_profit
  q_salescash_to_or → q_salescash_to_or
  q_ocf_to_sales → q_ocf_to_sales
  q_ocf_to_or → q_ocf_to_or
  basic_eps_yoy → basic_eps_yoy
  dt_eps_yoy → dt_eps_yoy
  cfps_yoy → cfps_yoy
  op_yoy → op_yoy
  ebt_yoy → ebt_yoy
  netprofit_yoy → netprofit_yoy
  dt_netprofit_yoy → dt_netprofit_yoy
  ocf_yoy → ocf_yoy
  roe_yoy → roe_yoy
  bps_yoy → bps_yoy
  assets_yoy → assets_yoy
  eqt_yoy → eqt_yoy
  tr_yoy → tr_yoy
  or_yoy → or_yoy
  q_gr_yoy → q_gr_yoy
  q_gr_qoq → q_gr_qoq
  q_sales_yoy → q_sales_yoy
  q_sales_qoq → q_sales_qoq
  q_op_yoy → q_op_yoy
  q_op_qoq → q_op_qoq
  q_profit_yoy → q_profit_yoy
  q_profit_qoq → q_profit_qoq
  q_netprofit_yoy → q_netprofit_yoy
  q_netprofit_qoq → q_netprofit_qoq
  equity_yoy → equity_yoy
  rd_exp → rd_exp
  update_flag → update_flag
  ```
- **同步状态**: ✅ 已完成 (数万条)
- **更新频率**: 每季度
- **使用场景**: 
  - 选股服务财务筛选
  - 回测引擎基本面数据

### 3.2 financial_data - 财务数据（未完全使用）
- **Tushare接口**: 
  - `pro.income()` - 利润表
  - `pro.balancesheet()` - 资产负债表
  - `pro.cashflow()` - 现金流量表
- **说明**: 接口已实现但未建立完整同步脚本
- **同步状态**: ⚠️ 部分实现
- **使用场景**: 预留扩展

---

## 4️⃣ 行业分类表 (1个)

### 4.1 industry_classification - 申万行业分类
- **Tushare接口**: 
  - `pro.index_classify()` - 获取行业列表
  - `pro.index_member()` - 获取行业成分股
- **同步脚本**: `sync_industry_classification.py`
- **字段映射**:
  ```
  ts_code → con_code (成分股代码)
  industry_code → industry_code
  industry_name → industry_name
  level → level (1/2/3)
  classification_type → 'SW2021'
  ```
- **同步状态**: ✅ 已完成 (23,049条)
  - 一级行业: 7,589条
  - 二级行业: 8,013条
  - 三级行业: 7,447条
- **更新频率**: 每季度
- **使用场景**: 
  - 选股服务行业筛选
  - 回测引擎行业分散
  - 风控行业限制

---

## 5️⃣ 审计意见表 (1个)

### 5.1 audit_opinions - 财务审计意见
- **Tushare接口**: `pro.fina_audit()`
- **同步脚本**: `sync_audit_opinions.py`
- **字段映射**:
  ```
  ts_code → ts_code
  ann_date → ann_date
  end_date → end_date
  audit_result → audit_result
  audit_fees → audit_fees
  audit_agency → audit_agency
  audit_sign → audit_sign
  ```
- **同步状态**: 🔄 进行中 (2,234条, 12.72%)
- **更新频率**: 每年
- **使用场景**: 
  - 选股服务风控筛选
  - 过滤非标审计意见股票

---

## 6️⃣ 资金流向表 (1个)

### 6.1 money_flow - 资金流向
- **Tushare接口**: `pro.moneyflow()`
- **同步脚本**: `app/services/tushare_service.py` - `get_moneyflow()` (已实现接口)
- **同步状态**: ⚠️ 接口已实现但未建立同步脚本
- **权限要求**: 2000积分
- **使用场景**: 
  - 选股服务资金面筛选
  - 回测引擎资金流分析

---

## 7️⃣ 技术指标表 (1个)

### 7.1 technical_indicators - 技术指标
- **Tushare接口**: ❌ 无（需自行计算）
- **数据来源**: 基于daily_history计算
- **同步状态**: ❌ 未实现
- **使用场景**: 
  - 选股服务技术面筛选
  - 回测引擎技术指标

---

## 8️⃣ 业务功能表 (30+个)

### 回测相关 (6个)
- **backtest_results** - 回测结果
- **trade_records** - 交易记录
- **portfolios** - 投资组合
- **trading_strategies** - 交易策略
- **strategy_templates** - 策略模板
- **system_metrics** - 系统指标

### 选股相关 (4个)
- **screening_results** - 选股结果
- **screening_history** - 选股历史
- **screening_strategies** - 选股策略
- **user_screening_preferences** - 用户选股偏好

### AI模型相关 (10个)
- **ai_models** - AI模型
- **ai_decision_records** - AI决策记录
- **model_ensembles** - 模型集成
- **model_fusion_history** - 模型融合历史
- **model_metrics** - 模型指标
- **model_performance_metrics** - 模型性能指标
- **model_test_records** - 模型测试记录
- **model_usage_logs** - 模型使用日志
- **model_api_keys** - 模型API密钥
- **ensemble_model_mapping** - 集成模型映射

### 风控相关 (2个)
- **risk_rules** - 风控规则
- **confidence_assessment_history** - 置信度评估历史

### 系统相关 (8个)
- **api_call_logs** - API调用日志
- **api_interfaces** - API接口
- **api_sync_tasks** - API同步任务
- **data_sources** - 数据源
- **instruction_parse_history** - 指令解析历史
- **llm_decisions** - LLM决策
- **users** - 用户
- **trading_users** - 交易用户

---

## 📊 Tushare接口使用情况汇总

### ✅ 已同步到数据库的接口 (11个)

| 接口 | 数据库表 | 记录数 | 状态 |
|-----|---------|--------|------|
| stock_basic | stock_basic | 5,582 | ✅ |
| trade_cal | trade_cal | 数千 | ✅ |
| daily | daily_history | 数百万 | ✅ |
| daily_basic | daily_basic | 数百万 | ✅ |
| adj_factor | adj_factor | 数十万 | ✅ |
| stk_limit | limit_prices | 数十万 | ✅ |
| suspend_d | suspend_info | 数千 | ✅ |
| fina_indicator | financial_indicators | 数万 | ✅ |
| index_classify | industry_classification | 511 | ✅ |
| index_member | industry_classification | 23,049 | ✅ |
| fina_audit | audit_opinions | 2,234 | 🔄 |

### ⚠️ 已实现但未同步的接口 (9个)

| 接口 | 用途 | 原因 |
|-----|------|------|
| income | 利润表 | 未建立同步脚本 |
| balancesheet | 资产负债表 | 未建立同步脚本 |
| cashflow | 现金流量表 | 未建立同步脚本 |
| dividend | 分红送股 | 未建立同步脚本 |
| share_float | 限售股解禁 | 未建立同步脚本 |
| top10_holders | 十大股东 | 未建立同步脚本 |
| top_list | 龙虎榜 | 未建立同步脚本 |
| moneyflow | 资金流向 | 未建立同步脚本 |
| limit_list | 涨跌停统计 | 未建立同步脚本 |

### 🔧 已实现但低频使用的接口 (3个)

| 接口 | 用途 | 使用场景 |
|-----|------|---------|
| index_basic | 指数信息 | 按需查询 |
| stk_mins | 分钟行情 | 按需查询 |
| index_weight | 指数权重 | 按需查询 |

---

## 🎯 各功能模块使用的接口

### 回测引擎使用的接口 (7个)
1. ✅ **stock_basic** - 股票列表
2. ✅ **trade_cal** - 交易日历
3. ✅ **daily** - 日线行情
4. ✅ **daily_basic** - 每日指标
5. ✅ **adj_factor** - 复权因子
6. ✅ **stk_limit** - 涨跌停价格
7. ✅ **suspend_d** - 停复牌信息

### 选股服务使用的接口 (8个)
1. ✅ **stock_basic** - 股票基础
2. ✅ **daily** - 最新价格
3. ✅ **daily_basic** - 估值指标
4. ✅ **fina_indicator** - 财务指标
5. ✅ **index_classify** - 行业分类
6. ✅ **index_member** - 行业成分
7. 🔄 **fina_audit** - 审计意见
8. ⚠️ **moneyflow** - 资金流向（未同步）

### 数据同步使用的接口 (11个)
1. ✅ **stock_basic** - 每日同步
2. ✅ **trade_cal** - 每日同步
3. ✅ **daily** - 每日同步
4. ✅ **daily_basic** - 每日同步
5. ✅ **adj_factor** - 每日同步
6. ✅ **stk_limit** - 每日同步
7. ✅ **suspend_d** - 每日同步
8. ✅ **fina_indicator** - 每季度同步
9. ✅ **index_classify** - 每季度同步
10. ✅ **index_member** - 每季度同步
11. 🔄 **fina_audit** - 每年同步

---

## 📋 建议优化项

### 高优先级
1. ✅ **完成审计意见同步** - 继续同步剩余87.28%
2. ❌ **实现技术指标计算** - 基于daily_history计算KDJ、MACD等
3. ⚠️ **建立资金流向同步** - 创建moneyflow同步脚本

### 中优先级
4. ⚠️ **建立三张财务报表同步** - income, balancesheet, cashflow
5. ⚠️ **建立分红送股同步** - dividend
6. ⚠️ **建立龙虎榜同步** - top_list

### 低优先级
7. ⚠️ **建立限售股同步** - share_float
8. ⚠️ **建立十大股东同步** - top10_holders
9. ⚠️ **建立涨跌停统计同步** - limit_list

---

## 📈 数据完整性评估

| 功能模块 | 数据完整性 | 评分 | 说明 |
|---------|-----------|------|------|
| 回测引擎 | 100% | ⭐⭐⭐⭐⭐ | 所有必需数据已同步 |
| 选股服务 | 87.5% | ⭐⭐⭐⭐ | 缺少审计意见、资金流向 |
| 数据同步 | 91.7% | ⭐⭐⭐⭐⭐ | 核心数据已完成 |
| 风控系统 | 75% | ⭐⭐⭐ | 缺少审计意见、停牌等 |
| 技术分析 | 0% | ⭐ | 技术指标未实现 |

---

**总结**: 
- 核心功能（回测、选股）的数据已基本完备
- 需要完成审计意见同步和技术指标计算
- 可选扩展财务报表、资金流向等高级数据
