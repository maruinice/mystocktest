-- 股票基础信息表
-- 基于Tushare stock_basic接口设计
-- 文档: https://tushare.pro/document/2?doc_id=25

CREATE TABLE IF NOT EXISTS stock_basic (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '自增主键',
    ts_code VARCHAR(20) NOT NULL UNIQUE COMMENT 'TS代码（如000001.SZ）',
    symbol VARCHAR(10) NOT NULL COMMENT '股票代码（如000001）',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    area VARCHAR(50) COMMENT '地域',
    industry VARCHAR(100) COMMENT '所属行业',
    fullname VARCHAR(200) COMMENT '股票全称',
    enname VARCHAR(200) COMMENT '英文全称',
    cnspell VARCHAR(50) COMMENT '拼音缩写',
    market VARCHAR(50) COMMENT '市场类型（主板/创业板/科创板/CDR/北交所）',
    exchange VARCHAR(10) COMMENT '交易所代码（SSE/SZSE/BSE）',
    curr_type VARCHAR(10) COMMENT '交易货币',
    list_status VARCHAR(10) COMMENT '上市状态（L上市/D退市/P暂停上市）',
    list_date DATE COMMENT '上市日期',
    delist_date DATE COMMENT '退市日期',
    is_hs VARCHAR(10) COMMENT '是否沪深港通标的（N否/H沪股通/S深股通）',
    act_name VARCHAR(200) COMMENT '实控人名称',
    act_ent_type VARCHAR(100) COMMENT '实控人企业性质',
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    data_source VARCHAR(50) DEFAULT 'tushare' COMMENT '数据来源',
    sync_status VARCHAR(20) DEFAULT 'active' COMMENT '同步状态（active/inactive）',
    
    -- 索引
    INDEX idx_symbol (symbol),
    INDEX idx_name (name),
    INDEX idx_industry (industry),
    INDEX idx_market (market),
    INDEX idx_exchange (exchange),
    INDEX idx_list_status (list_status),
    INDEX idx_list_date (list_date),
    INDEX idx_is_hs (is_hs),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基础信息表（Tushare数据源）';

-- 创建视图：仅显示正常上市的股票
CREATE OR REPLACE VIEW v_stock_basicctive AS
SELECT 
    ts_code,
    symbol,
    name,
    area,
    industry,
    fullname,
    market,
    exchange,
    list_date,
    is_hs,
    act_name,
    created_at,
    updated_at
FROM stock_basic 
WHERE list_status = 'L' 
  AND sync_status = 'active'
ORDER BY symbol;

-- 创建视图：按行业分组统计
CREATE OR REPLACE VIEW v_stock_basic_industry_stats AS
SELECT 
    industry,
    COUNT(*) as stock_count,
    COUNT(CASE WHEN is_hs IN ('H', 'S') THEN 1 END) as hs_count,
    MIN(list_date) as earliest_list_date,
    MAX(list_date) as latest_list_date
FROM stock_basic 
WHERE list_status = 'L' 
  AND sync_status = 'active'
  AND industry IS NOT NULL
GROUP BY industry
ORDER BY stock_count DESC;