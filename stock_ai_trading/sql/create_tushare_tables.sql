-- 创建Tushare相关数据表
-- 包括复权因子、每日指标、交易日历等

-- 1. 复权因子表 (adj_factor)
DROP TABLE IF EXISTS adj_factor;
CREATE TABLE adj_factor (
    id BIGINT AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    adj_factor DECIMAL(12,6) DEFAULT NULL COMMENT '复权因子',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id, trade_date),
    UNIQUE KEY uk_ts_code_date (ts_code, trade_date),
    KEY idx_trade_date (trade_date),
    KEY idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='复权因子表'
PARTITION BY RANGE (YEAR(trade_date)) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 2. 每日指标表 (daily_basic)
DROP TABLE IF EXISTS daily_basic;
CREATE TABLE daily_basic (
    id BIGINT AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    close DECIMAL(10,4) DEFAULT NULL COMMENT '当日收盘价',
    turnover_rate DECIMAL(8,4) DEFAULT NULL COMMENT '换手率（%）',
    turnover_rate_f DECIMAL(8,4) DEFAULT NULL COMMENT '换手率（自由流通股）',
    volume_ratio DECIMAL(8,4) DEFAULT NULL COMMENT '量比',
    pe DECIMAL(10,4) DEFAULT NULL COMMENT '市盈率（总市值/净利润，亏损的PE为空）',
    pe_ttm DECIMAL(10,4) DEFAULT NULL COMMENT '市盈率（TTM，亏损的PE为空）',
    pb DECIMAL(10,4) DEFAULT NULL COMMENT '市净率（总市值/净资产）',
    ps DECIMAL(10,4) DEFAULT NULL COMMENT '市销率',
    ps_ttm DECIMAL(10,4) DEFAULT NULL COMMENT '市销率（TTM）',
    dv_ratio DECIMAL(8,4) DEFAULT NULL COMMENT '股息率（%）',
    dv_ttm DECIMAL(8,4) DEFAULT NULL COMMENT '股息率（TTM）（%）',
    total_share DECIMAL(20,2) DEFAULT NULL COMMENT '总股本（万股）',
    float_share DECIMAL(20,2) DEFAULT NULL COMMENT '流通股本（万股）',
    free_share DECIMAL(20,2) DEFAULT NULL COMMENT '自由流通股本（万）',
    total_mv DECIMAL(20,2) DEFAULT NULL COMMENT '总市值（万元）',
    circ_mv DECIMAL(20,2) DEFAULT NULL COMMENT '流通市值（万元）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id, trade_date),
    UNIQUE KEY uk_ts_code_date (ts_code, trade_date),
    KEY idx_trade_date (trade_date),
    KEY idx_ts_code (ts_code),
    KEY idx_pe (pe),
    KEY idx_pb (pb)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日指标表'
PARTITION BY RANGE (YEAR(trade_date)) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 3. 交易日历表 (trade_cal)
DROP TABLE IF EXISTS trade_cal;
CREATE TABLE trade_cal (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    exchange VARCHAR(10) NOT NULL COMMENT '交易所 SSE上交所 SZSE深交所',
    cal_date DATE NOT NULL COMMENT '日历日期',
    is_open TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否交易 0休市 1交易',
    pretrade_date DATE DEFAULT NULL COMMENT '上一个交易日',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_exchange_date (exchange, cal_date),
    KEY idx_cal_date (cal_date),
    KEY idx_is_open (is_open)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易日历表';

-- 4. 创建视图：最新每日指标
CREATE OR REPLACE VIEW v_latest_daily_basic AS
SELECT 
    db.ts_code,
    db.trade_date,
    db.close,
    db.turnover_rate,
    db.volume_ratio,
    db.pe,
    db.pe_ttm,
    db.pb,
    db.ps,
    db.ps_ttm,
    db.total_mv,
    db.circ_mv
FROM daily_basic db
INNER JOIN (
    SELECT ts_code, MAX(trade_date) as max_date
    FROM daily_basic
    GROUP BY ts_code
) latest ON db.ts_code = latest.ts_code AND db.trade_date = latest.max_date;