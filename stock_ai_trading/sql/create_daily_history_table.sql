-- 创建每日历史行情表
-- 用于存储从Tushare /daily接口获取的历史行情数据

DROP TABLE IF EXISTS daily_history;

CREATE TABLE daily_history (
    id BIGINT AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,4) DEFAULT NULL COMMENT '开盘价',
    high_price DECIMAL(10,4) DEFAULT NULL COMMENT '最高价',
    low_price DECIMAL(10,4) DEFAULT NULL COMMENT '最低价',
    close_price DECIMAL(10,4) DEFAULT NULL COMMENT '收盘价',
    pre_close DECIMAL(10,4) DEFAULT NULL COMMENT '昨收价',
    change_amount DECIMAL(10,4) DEFAULT NULL COMMENT '涨跌额',
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
    
    -- 主键必须包含分区字段
    PRIMARY KEY (id, trade_date),
    
    -- 索引
    UNIQUE KEY uk_ts_code_date (ts_code, trade_date),
    KEY idx_trade_date (trade_date),
    KEY idx_ts_code (ts_code),
    KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日历史行情数据表'
PARTITION BY RANGE (YEAR(trade_date)) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);