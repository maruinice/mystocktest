-- Stock AI Trading System Database Schema
-- 创建数据库
CREATE DATABASE IF NOT EXISTS stock_trading CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE stock_trading;

-- 1. 用户表(users)
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    full_name VARCHAR(100) COMMENT '真实姓名',
    phone VARCHAR(20) COMMENT '手机号',
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active' COMMENT '用户状态',
    role ENUM('admin', 'trader', 'viewer') DEFAULT 'trader' COMMENT '用户角色',
    initial_capital DECIMAL(15,2) DEFAULT 0.00 COMMENT '初始资金',
    current_capital DECIMAL(15,2) DEFAULT 0.00 COMMENT '当前资金',
    risk_level ENUM('conservative', 'moderate', 'aggressive') DEFAULT 'moderate' COMMENT '风险偏好',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_login_at TIMESTAMP NULL COMMENT '最后登录时间',
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_status_role (status, role),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB COMMENT='用户表';

-- 2. 股票基础数据(stock_basic)
CREATE TABLE stock_basic (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL UNIQUE COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    market VARCHAR(10) NOT NULL COMMENT '市场(SH/SZ)',
    industry VARCHAR(50) COMMENT '所属行业',
    sector VARCHAR(50) COMMENT '所属板块',
    list_date DATE COMMENT '上市日期',
    delist_date DATE NULL COMMENT '退市日期',
    total_share BIGINT COMMENT '总股本',
    float_share BIGINT COMMENT '流通股本',
    market_cap DECIMAL(20,2) COMMENT '总市值',
    status ENUM('active', 'suspended', 'delisted') DEFAULT 'active' COMMENT '股票状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_stock_code (stock_code),
    INDEX idx_market_status (market, status),
    INDEX idx_industry (industry),
    INDEX idx_sector (sector),
    INDEX idx_list_date (list_date)
) ENGINE=InnoDB COMMENT='股票基础数据表';

-- 3. 行情数据(stock_quotes) - 按日期分区
CREATE TABLE stock_quotes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,3) NOT NULL COMMENT '开盘价',
    high_price DECIMAL(10,3) NOT NULL COMMENT '最高价',
    low_price DECIMAL(10,3) NOT NULL COMMENT '最低价',
    close_price DECIMAL(10,3) NOT NULL COMMENT '收盘价',
    pre_close DECIMAL(10,3) COMMENT '前收盘价',
    change_amount DECIMAL(10,3) COMMENT '涨跌额',
    change_pct DECIMAL(8,4) COMMENT '涨跌幅(%)',
    volume BIGINT COMMENT '成交量(股)',
    amount DECIMAL(20,2) COMMENT '成交额(元)',
    turnover_rate DECIMAL(8,4) COMMENT '换手率(%)',
    pe_ratio DECIMAL(10,4) COMMENT '市盈率',
    pb_ratio DECIMAL(10,4) COMMENT '市净率',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_stock_date (stock_code, trade_date),
    INDEX idx_stock_code (stock_code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_close_price (close_price),
    INDEX idx_volume (volume),
    INDEX idx_change_pct (change_pct)
) ENGINE=InnoDB COMMENT='股票行情数据表'
PARTITION BY RANGE (YEAR(trade_date)) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 4. 财务数据(financial_data) - 按年度分区
CREATE TABLE financial_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    report_date DATE NOT NULL COMMENT '报告期',
    report_type ENUM('Q1', 'Q2', 'Q3', 'annual') NOT NULL COMMENT '报告类型',
    revenue DECIMAL(20,2) COMMENT '营业收入',
    net_profit DECIMAL(20,2) COMMENT '净利润',
    total_assets DECIMAL(20,2) COMMENT '总资产',
    total_equity DECIMAL(20,2) COMMENT '股东权益',
    roe DECIMAL(8,4) COMMENT '净资产收益率(%)',
    roa DECIMAL(8,4) COMMENT '总资产收益率(%)',
    gross_margin DECIMAL(8,4) COMMENT '毛利率(%)',
    net_margin DECIMAL(8,4) COMMENT '净利率(%)',
    debt_ratio DECIMAL(8,4) COMMENT '资产负债率(%)',
    current_ratio DECIMAL(8,4) COMMENT '流动比率',
    quick_ratio DECIMAL(8,4) COMMENT '速动比率',
    eps DECIMAL(10,4) COMMENT '每股收益',
    bvps DECIMAL(10,4) COMMENT '每股净资产',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_stock_report (stock_code, report_date, report_type),
    INDEX idx_stock_code (stock_code),
    INDEX idx_report_date (report_date),
    INDEX idx_report_type (report_type),
    INDEX idx_roe (roe),
    INDEX idx_eps (eps),
    FOREIGN KEY (stock_code) REFERENCES stock_basic(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='财务数据表'
PARTITION BY RANGE (YEAR(report_date)) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 5. 策略配置(trading_strategies)
CREATE TABLE trading_strategies (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    strategy_name VARCHAR(100) NOT NULL COMMENT '策略名称',
    strategy_type ENUM('technical', 'fundamental', 'quantitative', 'ai_driven') NOT NULL COMMENT '策略类型',
    description TEXT COMMENT '策略描述',
    parameters JSON COMMENT '策略参数(JSON格式)',
    risk_level ENUM('low', 'medium', 'high') DEFAULT 'medium' COMMENT '风险等级',
    max_position_size DECIMAL(15,2) COMMENT '最大仓位',
    stop_loss_pct DECIMAL(8,4) COMMENT '止损百分比',
    take_profit_pct DECIMAL(8,4) COMMENT '止盈百分比',
    status ENUM('active', 'inactive', 'testing') DEFAULT 'inactive' COMMENT '策略状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_strategy_type (strategy_type),
    INDEX idx_status (status),
    INDEX idx_user_status (user_id, status),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='交易策略配置表';

-- 6. 资产组合(portfolios)
CREATE TABLE portfolios (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    portfolio_name VARCHAR(100) NOT NULL COMMENT '组合名称',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    quantity BIGINT NOT NULL DEFAULT 0 COMMENT '持仓数量',
    avg_cost DECIMAL(10,3) NOT NULL DEFAULT 0.000 COMMENT '平均成本',
    current_price DECIMAL(10,3) COMMENT '当前价格',
    market_value DECIMAL(15,2) COMMENT '市值',
    unrealized_pnl DECIMAL(15,2) COMMENT '浮动盈亏',
    unrealized_pnl_pct DECIMAL(8,4) COMMENT '浮动盈亏比例(%)',
    weight DECIMAL(8,4) COMMENT '组合权重(%)',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_user_portfolio_stock (user_id, portfolio_name, stock_code),
    INDEX idx_user_id (user_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_portfolio_name (portfolio_name),
    INDEX idx_user_portfolio (user_id, portfolio_name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_code) REFERENCES stock_basic(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='资产组合表';

-- 7. 交易记录(trade_records) - 按月分区
CREATE TABLE trade_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    strategy_id BIGINT COMMENT '策略ID',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    trade_type ENUM('buy', 'sell') NOT NULL COMMENT '交易类型',
    order_type ENUM('market', 'limit', 'stop') DEFAULT 'market' COMMENT '订单类型',
    quantity BIGINT NOT NULL COMMENT '交易数量',
    price DECIMAL(10,3) NOT NULL COMMENT '交易价格',
    amount DECIMAL(15,2) NOT NULL COMMENT '交易金额',
    commission DECIMAL(10,2) DEFAULT 0.00 COMMENT '手续费',
    tax DECIMAL(10,2) DEFAULT 0.00 COMMENT '印花税',
    net_amount DECIMAL(15,2) NOT NULL COMMENT '净交易金额',
    trade_time TIMESTAMP NOT NULL COMMENT '交易时间',
    status ENUM('pending', 'filled', 'cancelled', 'failed') DEFAULT 'pending' COMMENT '交易状态',
    order_id VARCHAR(50) COMMENT '订单号',
    reason TEXT COMMENT '交易原因/备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_strategy_id (strategy_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_trade_type (trade_type),
    INDEX idx_trade_time (trade_time),
    INDEX idx_status (status),
    INDEX idx_user_time (user_id, trade_time),
    INDEX idx_stock_time (stock_code, trade_time),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies(id) ON DELETE SET NULL,
    FOREIGN KEY (stock_code) REFERENCES stock_basic(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='交易记录表'
PARTITION BY RANGE (YEAR(trade_time) * 100 + MONTH(trade_time)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    PARTITION p202403 VALUES LESS THAN (202404),
    PARTITION p202404 VALUES LESS THAN (202405),
    PARTITION p202405 VALUES LESS THAN (202406),
    PARTITION p202406 VALUES LESS THAN (202407),
    PARTITION p202407 VALUES LESS THAN (202408),
    PARTITION p202408 VALUES LESS THAN (202409),
    PARTITION p202409 VALUES LESS THAN (202410),
    PARTITION p202410 VALUES LESS THAN (202411),
    PARTITION p202411 VALUES LESS THAN (202412),
    PARTITION p202412 VALUES LESS THAN (202501),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 8. 风控规则(risk_rules)
CREATE TABLE risk_rules (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT COMMENT '用户ID(NULL表示全局规则)',
    rule_name VARCHAR(100) NOT NULL COMMENT '规则名称',
    rule_type ENUM('position_limit', 'loss_limit', 'concentration', 'volatility', 'custom') NOT NULL COMMENT '规则类型',
    rule_config JSON NOT NULL COMMENT '规则配置(JSON格式)',
    threshold_value DECIMAL(15,4) COMMENT '阈值',
    action ENUM('alert', 'block', 'force_close') DEFAULT 'alert' COMMENT '触发动作',
    priority INT DEFAULT 1 COMMENT '优先级(1-10)',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '规则状态',
    description TEXT COMMENT '规则描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_rule_type (rule_type),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_user_type_status (user_id, rule_type, status),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='风控规则表';

-- 9. LLM决策记录(llm_decisions) - 按日期分区
CREATE TABLE llm_decisions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    strategy_id BIGINT COMMENT '策略ID',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    decision_type ENUM('buy', 'sell', 'hold', 'analysis') NOT NULL COMMENT '决策类型',
    prompt_text TEXT NOT NULL COMMENT '输入提示词',
    llm_response TEXT NOT NULL COMMENT 'LLM响应内容',
    confidence_score DECIMAL(5,4) COMMENT '置信度分数(0-1)',
    reasoning TEXT COMMENT '决策推理过程',
    market_data JSON COMMENT '决策时的市场数据',
    decision_result JSON COMMENT '决策结果详情',
    execution_status ENUM('pending', 'executed', 'rejected', 'expired') DEFAULT 'pending' COMMENT '执行状态',
    model_name VARCHAR(50) COMMENT '使用的模型名称',
    model_version VARCHAR(20) COMMENT '模型版本',
    processing_time_ms INT COMMENT '处理时间(毫秒)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_strategy_id (strategy_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_decision_type (decision_type),
    INDEX idx_execution_status (execution_status),
    INDEX idx_created_at (created_at),
    INDEX idx_user_stock_time (user_id, stock_code, created_at),
    INDEX idx_confidence_score (confidence_score),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies(id) ON DELETE SET NULL,
    FOREIGN KEY (stock_code) REFERENCES stock_basic(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='LLM决策记录表'
PARTITION BY RANGE (TO_DAYS(created_at)) (
    PARTITION p20240101 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p20240201 VALUES LESS THAN (TO_DAYS('2024-03-01')),
    PARTITION p20240301 VALUES LESS THAN (TO_DAYS('2024-04-01')),
    PARTITION p20240401 VALUES LESS THAN (TO_DAYS('2024-05-01')),
    PARTITION p20240501 VALUES LESS THAN (TO_DAYS('2024-06-01')),
    PARTITION p20240601 VALUES LESS THAN (TO_DAYS('2024-07-01')),
    PARTITION p20240701 VALUES LESS THAN (TO_DAYS('2024-08-01')),
    PARTITION p20240801 VALUES LESS THAN (TO_DAYS('2024-09-01')),
    PARTITION p20240901 VALUES LESS THAN (TO_DAYS('2024-10-01')),
    PARTITION p20241001 VALUES LESS THAN (TO_DAYS('2024-11-01')),
    PARTITION p20241101 VALUES LESS THAN (TO_DAYS('2024-12-01')),
    PARTITION p20241201 VALUES LESS THAN (TO_DAYS('2025-01-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 10. 系统监控(system_metrics) - 按日期分区
CREATE TABLE system_metrics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    metric_type ENUM('performance', 'business', 'system', 'error') NOT NULL COMMENT '指标类型',
    metric_value DECIMAL(20,6) NOT NULL COMMENT '指标值',
    metric_unit VARCHAR(20) COMMENT '指标单位',
    tags JSON COMMENT '标签信息',
    description TEXT COMMENT '指标描述',
    recorded_at TIMESTAMP NOT NULL COMMENT '记录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_metric_name (metric_name),
    INDEX idx_metric_type (metric_type),
    INDEX idx_recorded_at (recorded_at),
    INDEX idx_name_time (metric_name, recorded_at),
    INDEX idx_type_time (metric_type, recorded_at)
) ENGINE=InnoDB COMMENT='系统监控指标表'
PARTITION BY RANGE (TO_DAYS(recorded_at)) (
    PARTITION p20240101 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p20240201 VALUES LESS THAN (TO_DAYS('2024-03-01')),
    PARTITION p20240301 VALUES LESS THAN (TO_DAYS('2024-04-01')),
    PARTITION p20240401 VALUES LESS THAN (TO_DAYS('2024-05-01')),
    PARTITION p20240501 VALUES LESS THAN (TO_DAYS('2024-06-01')),
    PARTITION p20240601 VALUES LESS THAN (TO_DAYS('2024-07-01')),
    PARTITION p20240701 VALUES LESS THAN (TO_DAYS('2024-08-01')),
    PARTITION p20240801 VALUES LESS THAN (TO_DAYS('2024-09-01')),
    PARTITION p20240901 VALUES LESS THAN (TO_DAYS('2024-10-01')),
    PARTITION p20241001 VALUES LESS THAN (TO_DAYS('2024-11-01')),
    PARTITION p20241101 VALUES LESS THAN (TO_DAYS('2024-12-01')),
    PARTITION p20241201 VALUES LESS THAN (TO_DAYS('2025-01-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 创建视图：用户交易统计
CREATE VIEW user_trading_stats AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(tr.id) as total_trades,
    SUM(CASE WHEN tr.trade_type = 'buy' THEN tr.quantity ELSE 0 END) as total_buy_quantity,
    SUM(CASE WHEN tr.trade_type = 'sell' THEN tr.quantity ELSE 0 END) as total_sell_quantity,
    SUM(CASE WHEN tr.trade_type = 'buy' THEN tr.net_amount ELSE -tr.net_amount END) as net_investment,
    AVG(tr.price) as avg_trade_price,
    MAX(tr.trade_time) as last_trade_time
FROM users u
LEFT JOIN trade_records tr ON u.id = tr.user_id AND tr.status = 'filled'
GROUP BY u.id, u.username;

-- 创建视图：股票表现统计
CREATE VIEW stock_performance_stats AS
SELECT 
    sb.stock_code,
    sb.stock_name,
    sq.close_price as current_price,
    sq.change_pct as daily_change_pct,
    COUNT(tr.id) as trade_count,
    SUM(tr.quantity) as total_volume,
    AVG(tr.price) as avg_trade_price,
    MAX(tr.trade_time) as last_trade_time
FROM stock_basic sb
LEFT JOIN stock_quotes sq ON sb.stock_code = sq.stock_code 
    AND sq.trade_date = (SELECT MAX(trade_date) FROM stock_quotes WHERE stock_code = sb.stock_code)
LEFT JOIN trade_records tr ON sb.stock_code = tr.stock_code AND tr.status = 'filled'
WHERE sb.list_status = 'L'
GROUP BY sb.stock_code, sb.stock_name, sq.close_price, sq.change_pct;

-- 插入初始数据
INSERT INTO users (username, email, password_hash, full_name, role, initial_capital, current_capital) VALUES
('admin', 'admin@example.com', '$2b$12$example_hash', '系统管理员', 'admin', 1000000.00, 1000000.00),
('demo_trader', 'trader@example.com', '$2b$12$example_hash', '演示交易员', 'trader', 100000.00, 100000.00);

-- 插入风控规则示例
INSERT INTO risk_rules (rule_name, rule_type, rule_config, threshold_value, action, description) VALUES
('全局单日亏损限制', 'loss_limit', '{"period": "daily", "type": "absolute"}', 10000.00, 'block', '单日最大亏损不超过1万元'),
('单只股票最大仓位', 'position_limit', '{"type": "single_stock"}', 0.20, 'alert', '单只股票仓位不超过总资产20%'),
('总仓位限制', 'position_limit', '{"type": "total_position"}', 0.80, 'block', '总仓位不超过80%');

COMMIT;