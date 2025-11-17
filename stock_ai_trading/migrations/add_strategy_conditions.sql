-- 添加策略条件字段到 trading_strategies 表
-- 执行日期: 2024-11-05

USE stock_trading;

-- 添加买入条件字段
ALTER TABLE trading_strategies 
ADD COLUMN buy_conditions JSON COMMENT '买入条件(JSON格式)' AFTER indicator_params;

-- 添加卖出条件字段
ALTER TABLE trading_strategies 
ADD COLUMN sell_conditions JSON COMMENT '卖出条件(JSON格式)' AFTER buy_conditions;

-- 添加风险控制字段
ALTER TABLE trading_strategies 
ADD COLUMN risk_controls JSON COMMENT '风险控制参数(JSON格式)' AFTER sell_conditions;

-- 添加策略代码字段
ALTER TABLE trading_strategies 
ADD COLUMN code TEXT COMMENT '策略代码' AFTER risk_controls;

-- 添加显示名称字段
ALTER TABLE trading_strategies 
ADD COLUMN display_name VARCHAR(100) COMMENT '显示名称' AFTER strategy_name;

-- 添加分类字段
ALTER TABLE trading_strategies 
ADD COLUMN category VARCHAR(50) COMMENT '策略分类' AFTER strategy_type;

-- 添加作者字段
ALTER TABLE trading_strategies 
ADD COLUMN author VARCHAR(100) COMMENT '策略作者' AFTER description;

-- 添加最小资金字段
ALTER TABLE trading_strategies 
ADD COLUMN min_capital DECIMAL(15,2) COMMENT '最小资金要求' AFTER author;

-- 添加指标字段
ALTER TABLE trading_strategies 
ADD COLUMN indicators JSON COMMENT '使用的技术指标' AFTER parameters;

-- 添加指标参数字段
ALTER TABLE trading_strategies 
ADD COLUMN indicator_params JSON COMMENT '指标参数配置' AFTER indicators;

-- 添加绩效指标字段
ALTER TABLE trading_strategies 
ADD COLUMN performance DECIMAL(10,4) COMMENT '策略绩效' AFTER code;

ALTER TABLE trading_strategies 
ADD COLUMN sharpe_ratio DECIMAL(10,4) COMMENT '夏普比率' AFTER performance;

ALTER TABLE trading_strategies 
ADD COLUMN max_drawdown DECIMAL(10,4) COMMENT '最大回撤' AFTER sharpe_ratio;

ALTER TABLE trading_strategies 
ADD COLUMN win_rate DECIMAL(10,4) COMMENT '胜率' AFTER max_drawdown;

ALTER TABLE trading_strategies 
ADD COLUMN total_trades INT COMMENT '总交易次数' AFTER win_rate;

-- 添加回测相关字段
ALTER TABLE trading_strategies 
ADD COLUMN backtest_count INT DEFAULT 0 COMMENT '回测次数' AFTER total_trades;

ALTER TABLE trading_strategies 
ADD COLUMN last_backtest_date DATE COMMENT '最后回测日期' AFTER backtest_count;

-- 添加AI生成标记
ALTER TABLE trading_strategies 
ADD COLUMN ai_generated BOOLEAN DEFAULT FALSE COMMENT '是否AI生成' AFTER last_backtest_date;

ALTER TABLE trading_strategies 
ADD COLUMN original_prompt TEXT COMMENT '原始提示词' AFTER ai_generated;

-- 添加最后运行时间
ALTER TABLE trading_strategies 
ADD COLUMN last_run_at TIMESTAMP NULL COMMENT '最后运行时间' AFTER updated_at;

-- 显示表结构
DESCRIBE trading_strategies;

-- 显示成功消息
SELECT 'Migration completed successfully!' AS status;
