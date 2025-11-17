-- 添加核心字段到 trading_strategies 表
-- 只添加回测必需的3个字段

USE stock_trading;

-- 1. 添加买入条件字段
ALTER TABLE trading_strategies 
ADD COLUMN buy_conditions JSON COMMENT '买入条件(JSON格式)';

-- 2. 添加卖出条件字段
ALTER TABLE trading_strategies 
ADD COLUMN sell_conditions JSON COMMENT '卖出条件(JSON格式)';

-- 3. 添加风险控制字段
ALTER TABLE trading_strategies 
ADD COLUMN risk_controls JSON COMMENT '风险控制参数(JSON格式)';

-- 验证
SELECT 'Core fields added successfully!' AS status;
DESCRIBE trading_strategies;
