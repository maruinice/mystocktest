# 回测无交易信号 - 快速修复指南

## 问题原因

回测结果显示一条直线且交易记录为空，原因是：

**数据库表 `trading_strategies` 缺少 `buy_conditions`、`sell_conditions`、`risk_controls` 字段！**

## 🚀 快速修复（3步）

### 步骤1: 执行数据库迁移

打开MySQL客户端（MySQL Workbench / Navicat / 命令行），执行以下SQL：

```sql
USE stock_trading;

-- 添加买入条件
ALTER TABLE trading_strategies 
ADD COLUMN IF NOT EXISTS buy_conditions JSON COMMENT '买入条件';

-- 添加卖出条件
ALTER TABLE trading_strategies 
ADD COLUMN IF NOT EXISTS sell_conditions JSON COMMENT '卖出条件';

-- 添加风险控制
ALTER TABLE trading_strategies 
ADD COLUMN IF NOT EXISTS risk_controls JSON COMMENT '风险控制';

-- 验证
DESCRIBE trading_strategies;
```

### 步骤2: 重启Flask服务器

关闭Flask窗口，重新运行：
```bash
python run_flask.py --port 5000 --debug
```

### 步骤3: 重新生成策略并回测

1. 在前端删除旧策略
2. 使用AI生成新策略（会自动包含买卖条件）
3. 执行回测
4. 查看交易记录 ✅

## 📊 验证修复成功

回测完成后，你应该看到：

✅ **净值曲线有波动**（不再是直线）
✅ **交易记录有数据**（显示买入/卖出信号）
✅ **交易统计有数值**（买入次数、卖出次数等）

## 🔍 调试信息

如果修复后仍然没有交易信号，查看Flask控制台输出：

```
[DEBUG] 策略信息:
  - 策略ID: xxx
  - 策略名称: xxx
  - 买入条件: [...]  ← 应该有内容
  - 卖出条件: [...]  ← 应该有内容
  - 风险控制: {...}  ← 应该有内容

[DEBUG] 回测配置:
  - 买入条件数量: 1  ← 应该 > 0
  - 卖出条件数量: 1  ← 应该 > 0
  - 风险控制: {...}

[INFO] [2024-01-01] 使用条件评估器，买入条件数: 1, 卖出条件数: 1
[INFO] [2024-01-15] 生成 1 笔交易  ← 应该看到这样的日志
```

## ⚠️ 常见问题

### Q: 执行SQL时提示 "Duplicate column name"
**A:** 字段已存在，可以忽略。直接进行步骤2。

### Q: 仍然没有交易信号
**A:** 检查：
1. 是否重启了Flask服务器
2. 是否使用AI重新生成了策略（旧策略没有买卖条件）
3. 查看Flask控制台的[DEBUG]日志

### Q: 如何手动添加买卖条件到现有策略
**A:** 执行SQL：

```sql
UPDATE trading_strategies 
SET 
    buy_conditions = '[{
        "type": "price",
        "operator": "greater_than",
        "value": "MA20",
        "description": "价格高于20日均线"
    }]',
    sell_conditions = '[{
        "type": "price",
        "operator": "less_than",
        "value": "MA20",
        "description": "价格低于20日均线"
    }]',
    risk_controls = '{
        "max_position_size": 0.1,
        "max_total_position": 0.6,
        "stop_loss": 5.0,
        "take_profit": 15.0
    }'
WHERE strategy_id = '你的策略ID';
```

## 📝 完整示例

### 示例1: MA交叉策略

```sql
UPDATE trading_strategies 
SET 
    buy_conditions = '[{
        "type": "indicator",
        "indicator": "MA",
        "operator": "cross_above",
        "params": {"short_period": 5, "long_period": 20},
        "description": "5日均线上穿20日均线"
