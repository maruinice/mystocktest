-- 更新trading_strategies表结构以支持完整的策略管理功能
-- 执行时间: 2025-01-30

-- 1. 添加新字段（使用存储过程来处理IF NOT EXISTS）
DELIMITER $$

CREATE PROCEDURE AddColumnIfNotExists()
BEGIN
    -- 检查并添加display_name字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'display_name') THEN
        ALTER TABLE trading_strategies ADD COLUMN display_name VARCHAR(200) COMMENT '策略显示名称' AFTER strategy_name;
    END IF;
    
    -- 检查并添加author字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'author') THEN
        ALTER TABLE trading_strategies ADD COLUMN author VARCHAR(100) COMMENT '策略作者' AFTER description;
    END IF;
    
    -- 检查并添加min_capital字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'min_capital') THEN
        ALTER TABLE trading_strategies ADD COLUMN min_capital DECIMAL(15,2) DEFAULT 100000 COMMENT '最小资金要求' AFTER author;
    END IF;
    
    -- 检查并添加category字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'category') THEN
        ALTER TABLE trading_strategies ADD COLUMN category ENUM('trend_following', 'mean_reversion', 'momentum', 'arbitrage', 'multi_factor', 'volatility', 'custom') DEFAULT 'custom' COMMENT '策略分类' AFTER strategy_type;
    END IF;
    
    -- 检查并添加indicators字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'indicators') THEN
        ALTER TABLE trading_strategies ADD COLUMN indicators JSON COMMENT '使用的技术指标列表' AFTER parameters;
    END IF;
    
    -- 检查并添加indicator_params字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'indicator_params') THEN
        ALTER TABLE trading_strategies ADD COLUMN indicator_params JSON COMMENT '指标参数配置' AFTER indicators;
    END IF;
    
    -- 检查并添加buy_conditions字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'buy_conditions') THEN
        ALTER TABLE trading_strategies ADD COLUMN buy_conditions JSON COMMENT '买入条件' AFTER indicator_params;
    END IF;
    
    -- 检查并添加sell_conditions字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'sell_conditions') THEN
        ALTER TABLE trading_strategies ADD COLUMN sell_conditions JSON COMMENT '卖出条件' AFTER buy_conditions;
    END IF;
    
    -- 检查并添加code字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'code') THEN
        ALTER TABLE trading_strategies ADD COLUMN code TEXT COMMENT '策略代码' AFTER sell_conditions;
    END IF;
    
    -- 检查并添加performance字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'performance') THEN
        ALTER TABLE trading_strategies ADD COLUMN performance DECIMAL(8,4) COMMENT '策略表现' AFTER code;
    END IF;
    
    -- 检查并添加sharpe_ratio字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'sharpe_ratio') THEN
        ALTER TABLE trading_strategies ADD COLUMN sharpe_ratio DECIMAL(8,4) COMMENT '夏普比率' AFTER performance;
    END IF;
    
    -- 检查并添加max_drawdown字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'max_drawdown') THEN
        ALTER TABLE trading_strategies ADD COLUMN max_drawdown DECIMAL(8,4) COMMENT '最大回撤' AFTER sharpe_ratio;
    END IF;
    
    -- 检查并添加win_rate字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'win_rate') THEN
        ALTER TABLE trading_strategies ADD COLUMN win_rate DECIMAL(8,4) COMMENT '胜率' AFTER max_drawdown;
    END IF;
    
    -- 检查并添加total_trades字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'total_trades') THEN
        ALTER TABLE trading_strategies ADD COLUMN total_trades INT DEFAULT 0 COMMENT '总交易次数' AFTER win_rate;
    END IF;
    
    -- 检查并添加backtest_count字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'backtest_count') THEN
        ALTER TABLE trading_strategies ADD COLUMN backtest_count INT DEFAULT 0 COMMENT '回测次数' AFTER total_trades;
    END IF;
    
    -- 检查并添加last_backtest_date字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'last_backtest_date') THEN
        ALTER TABLE trading_strategies ADD COLUMN last_backtest_date DATE COMMENT '最后回测日期' AFTER backtest_count;
    END IF;
    
    -- 检查并添加ai_generated字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'ai_generated') THEN
        ALTER TABLE trading_strategies ADD COLUMN ai_generated BOOLEAN DEFAULT FALSE COMMENT '是否AI生成' AFTER last_backtest_date;
    END IF;
    
    -- 检查并添加original_prompt字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'original_prompt') THEN
        ALTER TABLE trading_strategies ADD COLUMN original_prompt TEXT COMMENT '原始提示词(AI生成时)' AFTER ai_generated;
    END IF;
    
    -- 检查并添加last_run_at字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND COLUMN_NAME = 'last_run_at') THEN
        ALTER TABLE trading_strategies ADD COLUMN last_run_at TIMESTAMP NULL COMMENT '最后运行时间' AFTER updated_at;
    END IF;
END$$

DELIMITER ;

-- 调用存储过程
CALL AddColumnIfNotExists();

-- 删除存储过程
DROP PROCEDURE AddColumnIfNotExists;

-- 2. 修改现有字段
ALTER TABLE trading_strategies 
MODIFY COLUMN strategy_type ENUM('technical', 'fundamental', 'quantitative', 'ai_driven', 'trend_following', 'mean_reversion', 'momentum', 'arbitrage', 'multi_factor', 'volatility', 'custom') NOT NULL COMMENT '策略类型',
MODIFY COLUMN status ENUM('draft', 'active', 'inactive', 'testing', 'paused', 'stopped', 'error') DEFAULT 'draft' COMMENT '策略状态';

-- 3. 添加新索引（使用存储过程处理）
DELIMITER $$

CREATE PROCEDURE AddIndexIfNotExists()
BEGIN
    -- 检查并添加category索引
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND INDEX_NAME = 'idx_category') THEN
        ALTER TABLE trading_strategies ADD INDEX idx_category (category);
    END IF;
    
    -- 检查并添加author索引
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND INDEX_NAME = 'idx_author') THEN
        ALTER TABLE trading_strategies ADD INDEX idx_author (author);
    END IF;
    
    -- 检查并添加ai_generated索引
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND INDEX_NAME = 'idx_ai_generated') THEN
        ALTER TABLE trading_strategies ADD INDEX idx_ai_generated (ai_generated);
    END IF;
    
    -- 检查并添加performance索引
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND INDEX_NAME = 'idx_performance') THEN
        ALTER TABLE trading_strategies ADD INDEX idx_performance (performance);
    END IF;
    
    -- 检查并添加last_backtest_date索引
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'trading_strategies' AND INDEX_NAME = 'idx_last_backtest_date') THEN
        ALTER TABLE trading_strategies ADD INDEX idx_last_backtest_date (last_backtest_date);
    END IF;
END$$

DELIMITER ;

-- 调用存储过程
CALL AddIndexIfNotExists();

-- 删除存储过程
DROP PROCEDURE AddIndexIfNotExists;

-- 4. 创建回测结果表
CREATE TABLE IF NOT EXISTS backtest_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    backtest_id VARCHAR(50) UNIQUE NOT NULL COMMENT '回测ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    strategy_id BIGINT COMMENT '策略ID',
    strategy_name VARCHAR(200) NOT NULL COMMENT '策略名称',
    
    -- 回测配置
    start_date DATE NOT NULL COMMENT '回测开始日期',
    end_date DATE NOT NULL COMMENT '回测结束日期',
    initial_capital DECIMAL(15,2) NOT NULL COMMENT '初始资金',
    final_capital DECIMAL(15,2) COMMENT '最终资金',
    parameters JSON COMMENT '回测参数',
    stock_pool JSON COMMENT '股票池',
    benchmark VARCHAR(20) DEFAULT '000300.SH' COMMENT '基准指数',
    
    -- 收益指标
    total_return DECIMAL(10,6) COMMENT '总收益率',
    annualized_return DECIMAL(10,6) COMMENT '年化收益率',
    benchmark_return DECIMAL(10,6) COMMENT '基准收益率',
    alpha DECIMAL(10,6) COMMENT 'Alpha',
    beta DECIMAL(10,6) COMMENT 'Beta',
    
    -- 风险指标
    sharpe_ratio DECIMAL(8,4) COMMENT '夏普比率',
    sortino_ratio DECIMAL(8,4) COMMENT 'Sortino比率',
    max_drawdown DECIMAL(8,4) COMMENT '最大回撤',
    volatility DECIMAL(8,4) COMMENT '波动率',
    
    -- 交易指标
    win_rate DECIMAL(8,4) COMMENT '胜率',
    profit_factor DECIMAL(8,4) COMMENT '盈利因子',
    total_trades INT DEFAULT 0 COMMENT '总交易次数',
    winning_trades INT DEFAULT 0 COMMENT '盈利交易次数',
    losing_trades INT DEFAULT 0 COMMENT '亏损交易次数',
    avg_win DECIMAL(10,6) COMMENT '平均盈利',
    avg_loss DECIMAL(10,6) COMMENT '平均亏损',
    largest_win DECIMAL(10,6) COMMENT '最大盈利',
    largest_loss DECIMAL(10,6) COMMENT '最大亏损',
    
    -- 详细数据
    equity_curve JSON COMMENT '净值曲线数据',
    trades JSON COMMENT '交易记录',
    
    -- 状态和时间
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending' COMMENT '回测状态',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_strategy_id (strategy_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_user_strategy (user_id, strategy_id),
    
    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='回测结果表';

-- 5. 创建策略模板表
CREATE TABLE IF NOT EXISTS strategy_templates (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    template_name VARCHAR(100) NOT NULL COMMENT '模板名称',
    display_name VARCHAR(200) NOT NULL COMMENT '显示名称',
    description TEXT COMMENT '模板描述',
    category ENUM('trend_following', 'mean_reversion', 'momentum', 'arbitrage', 'multi_factor', 'volatility', 'custom') NOT NULL COMMENT '策略分类',
    risk_level ENUM('low', 'medium', 'high') DEFAULT 'medium' COMMENT '风险等级',
    
    -- 模板配置
    parameter_schema JSON COMMENT '参数结构定义',
    default_parameters JSON COMMENT '默认参数值',
    min_capital DECIMAL(15,2) DEFAULT 100000 COMMENT '最小资金要求',
    supported_markets JSON COMMENT '支持的市场',
    indicators JSON COMMENT '使用的技术指标',
    
    -- 代码模板
    code_template TEXT NOT NULL COMMENT '代码模板',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    UNIQUE KEY uk_template_name (template_name),
    INDEX idx_category (category),
    INDEX idx_risk_level (risk_level),
    INDEX idx_is_active (is_active),
    INDEX idx_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='策略模板表';

-- 6. 插入默认策略模板
INSERT IGNORE INTO strategy_templates (template_name, display_name, description, category, risk_level, parameter_schema, default_parameters, indicators, code_template) VALUES
('ma_cross', '双均线交叉策略', '基于短期和长期移动平均线交叉的经典趋势跟踪策略', 'trend_following', 'medium', 
 '{"short_period": {"type": "integer", "min": 3, "max": 20, "default": 5}, "long_period": {"type": "integer", "min": 10, "max": 60, "default": 20}, "position_size": {"type": "number", "min": 0.01, "max": 1.0, "default": 0.1}}',
 '{"short_period": 5, "long_period": 20, "position_size": 0.1}',
 '["MA"]',
 'def initialize(context):\n    context.stocks = [\"000001.XSHE\", \"000002.XSHE\"]\n    context.short_period = {short_period}\n    context.long_period = {long_period}\n    context.position_size = {position_size}\n\ndef handle_data(context, data):\n    for stock in context.stocks:\n        hist = data.history(stock, \"close\", context.long_period + 1)\n        short_ma = hist[-context.short_period:].mean()\n        long_ma = hist.mean()\n        current_position = context.portfolio.positions[stock].amount\n        \n        if short_ma > long_ma and current_position == 0:\n            order_target_percent(stock, context.position_size)\n        elif short_ma < long_ma and current_position > 0:\n            order_target_percent(stock, 0)'),

('rsi_reversal', 'RSI反转策略', '基于RSI指标的均值回归策略，在超买超卖区域进行反向交易', 'mean_reversion', 'medium',
 '{"rsi_period": {"type": "integer", "min": 5, "max": 30, "default": 14}, "rsi_overbought": {"type": "number", "min": 60, "max": 90, "default": 70}, "rsi_oversold": {"type": "number", "min": 10, "max": 40, "default": 30}, "position_size": {"type": "number", "min": 0.01, "max": 1.0, "default": 0.15}}',
 '{"rsi_period": 14, "rsi_overbought": 70, "rsi_oversold": 30, "position_size": 0.15}',
 '["RSI"]',
 'def initialize(context):\n    context.stocks = [\"000001.XSHE\", \"000002.XSHE\"]\n    context.rsi_period = {rsi_period}\n    context.rsi_overbought = {rsi_overbought}\n    context.rsi_oversold = {rsi_oversold}\n    context.position_size = {position_size}\n\ndef handle_data(context, data):\n    for stock in context.stocks:\n        hist = data.history(stock, \"close\", context.rsi_period + 1)\n        rsi = calculate_rsi(hist, context.rsi_period)\n        current_position = context.portfolio.positions[stock].amount\n        \n        if rsi < context.rsi_oversold and current_position == 0:\n            order_target_percent(stock, context.position_size)\n        elif rsi > context.rsi_overbought and current_position > 0:\n            order_target_percent(stock, 0)\n\ndef calculate_rsi(prices, period):\n    delta = prices.diff()\n    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()\n    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()\n    rs = gain / loss\n    return 100 - (100 / (1 + rs)).iloc[-1]'),

('bollinger_bands', '布林带策略', '基于布林带的突破和回归策略', 'volatility', 'medium',
 '{"period": {"type": "integer", "min": 10, "max": 50, "default": 20}, "std_dev": {"type": "number", "min": 1.0, "max": 3.0, "default": 2.0}, "position_size": {"type": "number", "min": 0.01, "max": 1.0, "default": 0.12}}',
 '{"period": 20, "std_dev": 2.0, "position_size": 0.12}',
 '["BOLL"]',
 'def initialize(context):\n    context.stocks = [\"000001.XSHE\"]\n    context.period = {period}\n    context.std_dev = {std_dev}\n    context.position_size = {position_size}\n\ndef handle_data(context, data):\n    for stock in context.stocks:\n        hist = data.history(stock, \"close\", context.period + 1)\n        ma = hist.mean()\n        std = hist.std()\n        upper_band = ma + context.std_dev * std\n        lower_band = ma - context.std_dev * std\n        \n        current_price = data.current(stock, \"close\")\n        current_position = context.portfolio.positions[stock].amount\n        \n        if current_price <= lower_band and current_position == 0:\n            order_target_percent(stock, context.position_size)\n        elif current_price >= upper_band and current_position > 0:\n            order_target_percent(stock, 0)');

-- 7. 更新现有数据的默认值
UPDATE trading_strategies 
SET 
    display_name = COALESCE(display_name, strategy_name),
    category = CASE 
        WHEN strategy_type = 'technical' THEN 'custom'
        WHEN strategy_type = 'fundamental' THEN 'multi_factor'
        WHEN strategy_type = 'quantitative' THEN 'custom'
        WHEN strategy_type = 'ai_driven' THEN 'custom'
        ELSE 'custom'
    END,
    status = CASE 
        WHEN status = 'inactive' THEN 'draft'
        WHEN status = 'testing' THEN 'draft'
        ELSE status
    END
WHERE display_name IS NULL OR category IS NULL;

-- 8. 创建视图：策略统计
CREATE OR REPLACE VIEW strategy_statistics AS
SELECT 
    category,
    COUNT(*) as total_strategies,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_strategies,
    COUNT(CASE WHEN ai_generated = TRUE THEN 1 END) as ai_generated_strategies,
    AVG(performance) as avg_performance,
    AVG(sharpe_ratio) as avg_sharpe_ratio,
    AVG(max_drawdown) as avg_max_drawdown,
    SUM(backtest_count) as total_backtests
FROM trading_strategies 
GROUP BY category;

-- 9. 创建视图：用户策略概览
CREATE OR REPLACE VIEW user_strategy_overview AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(ts.id) as total_strategies,
    COUNT(CASE WHEN ts.status = 'active' THEN 1 END) as active_strategies,
    COUNT(CASE WHEN ts.ai_generated = TRUE THEN 1 END) as ai_strategies,
    AVG(ts.performance) as avg_performance,
    MAX(ts.last_backtest_date) as last_backtest_date,
    SUM(ts.backtest_count) as total_backtests
FROM users u
LEFT JOIN trading_strategies ts ON u.id = ts.user_id
GROUP BY u.id, u.username;

-- 10. 添加触发器：更新策略统计
DELIMITER $$

CREATE TRIGGER IF NOT EXISTS update_strategy_stats_after_backtest
AFTER INSERT ON backtest_results
FOR EACH ROW
BEGIN
    IF NEW.status = 'completed' AND NEW.strategy_id IS NOT NULL THEN
        UPDATE trading_strategies 
        SET 
            backtest_count = backtest_count + 1,
            last_backtest_date = CURDATE(),
            performance = NEW.total_return,
            sharpe_ratio = NEW.sharpe_ratio,
            max_drawdown = NEW.max_drawdown,
            win_rate = NEW.win_rate,
            total_trades = NEW.total_trades,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.strategy_id;
    END IF;
END$$

DELIMITER ;

-- 执行完成提示
SELECT 'trading_strategies表结构更新完成！' as message;
SELECT 'backtest_results表创建完成！' as message;
SELECT 'strategy_templates表创建完成并插入默认模板！' as message;
SELECT '相关视图和触发器创建完成！' as message;