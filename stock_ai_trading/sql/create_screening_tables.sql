-- =====================================================
-- 股票选股功能相关数据表
-- =====================================================

-- 1. 日线行情数据表
CREATE TABLE IF NOT EXISTS daily_quotes (
    id BIGINT NOT NULL AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,3) DEFAULT NULL COMMENT '开盘价',
    high_price DECIMAL(10,3) DEFAULT NULL COMMENT '最高价',
    low_price DECIMAL(10,3) DEFAULT NULL COMMENT '最低价',
    close_price DECIMAL(10,3) DEFAULT NULL COMMENT '收盘价',
    pre_close DECIMAL(10,3) DEFAULT NULL COMMENT '昨收价',
    change_amount DECIMAL(10,3) DEFAULT NULL COMMENT '涨跌额',
    change_pct DECIMAL(8,4) DEFAULT NULL COMMENT '涨跌幅(%)',
    volume BIGINT DEFAULT NULL COMMENT '成交量(手)',
    amount DECIMAL(20,2) DEFAULT NULL COMMENT '成交额(千元)',
    turnover_rate DECIMAL(8,4) DEFAULT NULL COMMENT '换手率(%)',
    volume_ratio DECIMAL(8,4) DEFAULT NULL COMMENT '量比',
    pe DECIMAL(10,4) DEFAULT NULL COMMENT '市盈率',
    pb DECIMAL(10,4) DEFAULT NULL COMMENT '市净率',
    ps DECIMAL(10,4) DEFAULT NULL COMMENT '市销率',
    pcf DECIMAL(10,4) DEFAULT NULL COMMENT '市现率',
    market_cap DECIMAL(20,2) DEFAULT NULL COMMENT '总市值(万元)',
    circ_mv DECIMAL(20,2) DEFAULT NULL COMMENT '流通市值(万元)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id, trade_date),
    UNIQUE KEY uk_ts_code_date (ts_code, trade_date),
    KEY idx_ts_code (ts_code),
    KEY idx_trade_date (trade_date),
    KEY idx_change_pct (change_pct),
    KEY idx_turnover_rate (turnover_rate),
    KEY idx_market_cap (market_cap),
    KEY idx_pe (pe),
    KEY idx_pb (pb)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='日线行情数据表'
PARTITION BY RANGE (YEAR(trade_date)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 2. 财务指标数据表
CREATE TABLE IF NOT EXISTS financial_indicators (
    id BIGINT NOT NULL AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS股票代码',
    ann_date DATE NOT NULL COMMENT '公告日期',
    end_date DATE NOT NULL COMMENT '报告期',
    report_type VARCHAR(20) DEFAULT NULL COMMENT '报告类型(1季报/中报/3季报/年报)',
    
    -- 盈利能力指标
    roe DECIMAL(8,4) DEFAULT NULL COMMENT '净资产收益率(%)',
    roa DECIMAL(8,4) DEFAULT NULL COMMENT '总资产收益率(%)',
    roic DECIMAL(8,4) DEFAULT NULL COMMENT '投入资本回报率(%)',
    gross_margin DECIMAL(8,4) DEFAULT NULL COMMENT '毛利率(%)',
    net_margin DECIMAL(8,4) DEFAULT NULL COMMENT '净利率(%)',
    
    -- 成长性指标
    revenue_growth DECIMAL(8,4) DEFAULT NULL COMMENT '营收增长率(%)',
    profit_growth DECIMAL(8,4) DEFAULT NULL COMMENT '净利润增长率(%)',
    eps_growth DECIMAL(8,4) DEFAULT NULL COMMENT 'EPS增长率(%)',
    
    -- 财务健康指标
    debt_ratio DECIMAL(8,4) DEFAULT NULL COMMENT '资产负债率(%)',
    current_ratio DECIMAL(8,4) DEFAULT NULL COMMENT '流动比率',
    quick_ratio DECIMAL(8,4) DEFAULT NULL COMMENT '速动比率',
    
    -- 估值指标
    pe_ttm DECIMAL(10,4) DEFAULT NULL COMMENT '市盈率TTM',
    pb_mrq DECIMAL(10,4) DEFAULT NULL COMMENT '市净率MRQ',
    ps_ttm DECIMAL(10,4) DEFAULT NULL COMMENT '市销率TTM',
    peg DECIMAL(10,4) DEFAULT NULL COMMENT 'PEG比率',
    
    -- 每股指标
    eps DECIMAL(10,4) DEFAULT NULL COMMENT '每股收益',
    bps DECIMAL(10,4) DEFAULT NULL COMMENT '每股净资产',
    revenue_per_share DECIMAL(10,4) DEFAULT NULL COMMENT '每股营收',
    cash_per_share DECIMAL(10,4) DEFAULT NULL COMMENT '每股现金流',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id, end_date),
    UNIQUE KEY uk_ts_code_end_date (ts_code, end_date),
    KEY idx_ts_code (ts_code),
    KEY idx_ann_date (ann_date),
    KEY idx_end_date (end_date),
    KEY idx_roe (roe),
    KEY idx_roa (roa),
    KEY idx_revenue_growth (revenue_growth),
    KEY idx_profit_growth (profit_growth),
    KEY idx_pe_ttm (pe_ttm),
    KEY idx_pb_mrq (pb_mrq)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='财务指标数据表'
PARTITION BY RANGE (YEAR(end_date)) (
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 3. 技术指标数据表
CREATE TABLE IF NOT EXISTS technical_indicators (
    id BIGINT NOT NULL AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    
    -- 移动平均线
    ma5 DECIMAL(10,3) DEFAULT NULL COMMENT '5日均线',
    ma10 DECIMAL(10,3) DEFAULT NULL COMMENT '10日均线',
    ma20 DECIMAL(10,3) DEFAULT NULL COMMENT '20日均线',
    ma60 DECIMAL(10,3) DEFAULT NULL COMMENT '60日均线',
    ma120 DECIMAL(10,3) DEFAULT NULL COMMENT '120日均线',
    ma250 DECIMAL(10,3) DEFAULT NULL COMMENT '250日均线',
    
    -- RSI指标
    rsi6 DECIMAL(8,4) DEFAULT NULL COMMENT '6日RSI',
    rsi12 DECIMAL(8,4) DEFAULT NULL COMMENT '12日RSI',
    rsi24 DECIMAL(8,4) DEFAULT NULL COMMENT '24日RSI',
    
    -- MACD指标
    macd_dif DECIMAL(10,6) DEFAULT NULL COMMENT 'MACD DIF',
    macd_dea DECIMAL(10,6) DEFAULT NULL COMMENT 'MACD DEA',
    macd_bar DECIMAL(10,6) DEFAULT NULL COMMENT 'MACD BAR',
    
    -- KDJ指标
    kdj_k DECIMAL(8,4) DEFAULT NULL COMMENT 'KDJ K值',
    kdj_d DECIMAL(8,4) DEFAULT NULL COMMENT 'KDJ D值',
    kdj_j DECIMAL(8,4) DEFAULT NULL COMMENT 'KDJ J值',
    
    -- 布林带指标
    boll_upper DECIMAL(10,3) DEFAULT NULL COMMENT '布林带上轨',
    boll_mid DECIMAL(10,3) DEFAULT NULL COMMENT '布林带中轨',
    boll_lower DECIMAL(10,3) DEFAULT NULL COMMENT '布林带下轨',
    
    -- 威廉指标
    wr10 DECIMAL(8,4) DEFAULT NULL COMMENT '10日威廉指标',
    wr6 DECIMAL(8,4) DEFAULT NULL COMMENT '6日威廉指标',
    
    -- 成交量指标
    vol_ma5 BIGINT DEFAULT NULL COMMENT '5日成交量均线',
    vol_ma10 BIGINT DEFAULT NULL COMMENT '10日成交量均线',
    vol_ratio DECIMAL(8,4) DEFAULT NULL COMMENT '量比',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id, trade_date),
    UNIQUE KEY uk_ts_code_date (ts_code, trade_date),
    KEY idx_ts_code (ts_code),
    KEY idx_trade_date (trade_date),
    KEY idx_rsi12 (rsi12),
    KEY idx_kdj_k (kdj_k),
    KEY idx_macd_dif (macd_dif)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技术指标数据表'
PARTITION BY RANGE (YEAR(trade_date)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 4. 资金流向数据表
CREATE TABLE IF NOT EXISTS money_flow (
    id BIGINT NOT NULL AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    
    -- 主力资金
    main_net_inflow DECIMAL(20,2) DEFAULT NULL COMMENT '主力净流入(万元)',
    main_net_inflow_rate DECIMAL(8,4) DEFAULT NULL COMMENT '主力净流入率(%)',
    super_net_inflow DECIMAL(20,2) DEFAULT NULL COMMENT '超大单净流入(万元)',
    super_net_inflow_rate DECIMAL(8,4) DEFAULT NULL COMMENT '超大单净流入率(%)',
    large_net_inflow DECIMAL(20,2) DEFAULT NULL COMMENT '大单净流入(万元)',
    large_net_inflow_rate DECIMAL(8,4) DEFAULT NULL COMMENT '大单净流入率(%)',
    
    -- 散户资金
    medium_net_inflow DECIMAL(20,2) DEFAULT NULL COMMENT '中单净流入(万元)',
    medium_net_inflow_rate DECIMAL(8,4) DEFAULT NULL COMMENT '中单净流入率(%)',
    small_net_inflow DECIMAL(20,2) DEFAULT NULL COMMENT '小单净流入(万元)',
    small_net_inflow_rate DECIMAL(8,4) DEFAULT NULL COMMENT '小单净流入率(%)',
    
    -- 北向资金
    north_net_inflow DECIMAL(20,2) DEFAULT NULL COMMENT '北向资金净流入(万元)',
    north_net_inflow_rate DECIMAL(8,4) DEFAULT NULL COMMENT '北向资金净流入率(%)',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id, trade_date),
    UNIQUE KEY uk_ts_code_date (ts_code, trade_date),
    KEY idx_ts_code (ts_code),
    KEY idx_trade_date (trade_date),
    KEY idx_main_net_inflow (main_net_inflow),
    KEY idx_main_net_inflow_rate (main_net_inflow_rate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资金流向数据表'
PARTITION BY RANGE (YEAR(trade_date)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 5. 选股策略配置表
CREATE TABLE IF NOT EXISTS screening_strategies (
    id BIGINT NOT NULL AUTO_INCREMENT,
    strategy_name VARCHAR(100) NOT NULL COMMENT '策略名称',
    strategy_code VARCHAR(50) NOT NULL COMMENT '策略代码',
    strategy_type ENUM('fundamental', 'technical', 'mixed', 'custom') DEFAULT 'mixed' COMMENT '策略类型',
    description TEXT COMMENT '策略描述',
    
    -- 策略配置
    config JSON COMMENT '策略配置参数',
    conditions JSON COMMENT '筛选条件',
    sort_rules JSON COMMENT '排序规则',
    
    -- 策略属性
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统预设策略',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    creator_id BIGINT DEFAULT NULL COMMENT '创建者ID',
    
    -- 统计信息
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    success_rate DECIMAL(5,2) DEFAULT NULL COMMENT '成功率(%)',
    avg_return DECIMAL(8,4) DEFAULT NULL COMMENT '平均收益率(%)',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_strategy_code (strategy_code),
    KEY idx_strategy_type (strategy_type),
    KEY idx_creator_id (creator_id),
    KEY idx_is_system (is_system),
    KEY idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='选股策略配置表';

-- 6. 选股结果表
CREATE TABLE IF NOT EXISTS screening_results (
    id BIGINT NOT NULL AUTO_INCREMENT,
    task_id VARCHAR(50) NOT NULL COMMENT '任务ID',
    strategy_id BIGINT NOT NULL COMMENT '策略ID',
    user_id BIGINT DEFAULT NULL COMMENT '用户ID',
    
    -- 筛选参数
    screening_date DATE NOT NULL COMMENT '筛选日期',
    total_stocks INT DEFAULT 0 COMMENT '总股票数',
    filtered_stocks INT DEFAULT 0 COMMENT '筛选后股票数',
    
    -- 结果数据
    result_data JSON COMMENT '筛选结果数据',
    summary_stats JSON COMMENT '汇总统计信息',
    
    -- 执行信息
    execution_time INT DEFAULT NULL COMMENT '执行时间(毫秒)',
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending' COMMENT '执行状态',
    error_message TEXT COMMENT '错误信息',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_task_id (task_id),
    KEY idx_strategy_id (strategy_id),
    KEY idx_user_id (user_id),
    KEY idx_screening_date (screening_date),
    KEY idx_status (status),
    
    FOREIGN KEY (strategy_id) REFERENCES screening_strategies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='选股结果表';

-- 7. 选股历史表
CREATE TABLE IF NOT EXISTS screening_history (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    strategy_id BIGINT NOT NULL COMMENT '策略ID',
    result_id BIGINT NOT NULL COMMENT '结果ID',
    
    -- 历史信息
    screening_date DATE NOT NULL COMMENT '筛选日期',
    selected_stocks JSON COMMENT '选中的股票列表',
    performance_data JSON COMMENT '后续表现数据',
    
    -- 评价指标
    hit_rate DECIMAL(5,2) DEFAULT NULL COMMENT '命中率(%)',
    avg_return_1d DECIMAL(8,4) DEFAULT NULL COMMENT '1日平均收益率(%)',
    avg_return_5d DECIMAL(8,4) DEFAULT NULL COMMENT '5日平均收益率(%)',
    avg_return_10d DECIMAL(8,4) DEFAULT NULL COMMENT '10日平均收益率(%)',
    max_drawdown DECIMAL(8,4) DEFAULT NULL COMMENT '最大回撤(%)',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    KEY idx_user_id (user_id),
    KEY idx_strategy_id (strategy_id),
    KEY idx_result_id (result_id),
    KEY idx_screening_date (screening_date),
    
    FOREIGN KEY (strategy_id) REFERENCES screening_strategies(id) ON DELETE CASCADE,
    FOREIGN KEY (result_id) REFERENCES screening_results(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='选股历史表';

-- 8. 用户选股偏好表
CREATE TABLE IF NOT EXISTS user_screening_preferences (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    
    -- 偏好设置
    preferred_strategies JSON COMMENT '偏好策略列表',
    default_conditions JSON COMMENT '默认筛选条件',
    notification_settings JSON COMMENT '通知设置',
    
    -- 风险偏好
    risk_level ENUM('conservative', 'moderate', 'aggressive') DEFAULT 'moderate' COMMENT '风险偏好',
    max_position_size DECIMAL(5,2) DEFAULT 10.00 COMMENT '最大仓位比例(%)',
    stop_loss_rate DECIMAL(5,2) DEFAULT 10.00 COMMENT '止损比例(%)',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_id (user_id),
    KEY idx_risk_level (risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户选股偏好表';

-- 插入系统预设选股策略
INSERT INTO screening_strategies (strategy_name, strategy_code, strategy_type, description, config, conditions, is_system, is_active) VALUES
('价值投资策略', 'value_investing', 'fundamental', '基于低估值、高分红、稳定盈利的价值投资理念', 
 '{"weight_pe": 0.3, "weight_pb": 0.2, "weight_roe": 0.3, "weight_dividend": 0.2}',
 '{"pe": {"min": 0, "max": 15}, "pb": {"min": 0, "max": 2}, "roe": {"min": 10, "max": null}, "dividend_yield": {"min": 3, "max": null}}',
 TRUE, TRUE),

('成长股策略', 'growth_stocks', 'fundamental', '寻找高成长性、盈利能力强的成长型股票',
 '{"weight_revenue_growth": 0.4, "weight_profit_growth": 0.4, "weight_roe": 0.2}',
 '{"revenue_growth": {"min": 20, "max": null}, "profit_growth": {"min": 25, "max": null}, "roe": {"min": 15, "max": null}}',
 TRUE, TRUE),

('技术突破策略', 'technical_breakout', 'technical', '基于技术指标的突破信号选股',
 '{"ma_period": 20, "volume_threshold": 1.5, "rsi_range": [30, 70]}',
 '{"price_above_ma20": true, "volume_ratio": {"min": 1.5, "max": null}, "rsi": {"min": 30, "max": 70}}',
 TRUE, TRUE),

('低位反弹策略', 'oversold_rebound', 'technical', '寻找超跌后可能反弹的股票',
 '{"rsi_oversold": 30, "decline_threshold": -20, "volume_confirm": true}',
 '{"rsi": {"min": 0, "max": 30}, "change_pct_5d": {"min": null, "max": -15}, "volume_ratio": {"min": 1.2, "max": null}}',
 TRUE, TRUE),

('均衡配置策略', 'balanced_allocation', 'mixed', '基本面和技术面相结合的均衡选股策略',
 '{"fundamental_weight": 0.6, "technical_weight": 0.4}',
 '{"pe": {"min": 0, "max": 25}, "roe": {"min": 8, "max": null}, "rsi": {"min": 25, "max": 75}, "ma_trend": "up"}',
 TRUE, TRUE);

-- 创建视图：最新行情数据
CREATE OR REPLACE VIEW v_latest_quotes AS
SELECT 
    dq.*,
    sb.symbol,
    sb.name,
    sb.industry,
    sb.market
FROM daily_quotes dq
INNER JOIN stock_basic sb ON dq.ts_code = sb.ts_code
INNER JOIN (
    SELECT ts_code, MAX(trade_date) as latest_date
    FROM daily_quotes
    GROUP BY ts_code
) latest ON dq.ts_code = latest.ts_code AND dq.trade_date = latest.latest_date;

-- 创建视图：最新财务指标
CREATE OR REPLACE VIEW v_latest_financial AS
SELECT 
    fi.*,
    sb.symbol,
    sb.name,
    sb.industry,
    sb.market
FROM financial_indicators fi
INNER JOIN stock_basic sb ON fi.ts_code = sb.ts_code
INNER JOIN (
    SELECT ts_code, MAX(end_date) as latest_date
    FROM financial_indicators
    GROUP BY ts_code
) latest ON fi.ts_code = latest.ts_code AND fi.end_date = latest.latest_date;

-- 创建视图：最新技术指标
CREATE OR REPLACE VIEW v_latest_technical AS
SELECT 
    ti.*,
    sb.symbol,
    sb.name,
    sb.industry,
    sb.market
FROM technical_indicators ti
INNER JOIN stock_basic sb ON ti.ts_code = sb.ts_code
INNER JOIN (
    SELECT ts_code, MAX(trade_date) as latest_date
    FROM technical_indicators
    GROUP BY ts_code
) latest ON ti.ts_code = latest.ts_code AND ti.trade_date = latest.latest_date;