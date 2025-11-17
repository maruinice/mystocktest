-- =====================================================
-- stock_basic表结构和数据同步SQL脚本
-- 将stock_basic表结构更新为与stock_basic一致，并导入数据
-- =====================================================

-- 1. 备份原stock_basic表（如果有数据的话）
CREATE TABLE stock_basic_backup_manual AS SELECT * FROM stock_basic;

-- 2. 删除原stock_basic表
DROP TABLE IF EXISTS stock_basic;

-- 3. 创建新的stock_basic表（结构与stock_basic一致）
CREATE TABLE stock_basic (
    id BIGINT NOT NULL AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS股票代码',
    symbol VARCHAR(10) NOT NULL COMMENT '股票代码',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    area VARCHAR(50) DEFAULT NULL COMMENT '地域',
    industry VARCHAR(100) DEFAULT NULL COMMENT '所属行业',
    fullname VARCHAR(200) DEFAULT NULL COMMENT '股票全称',
    enname VARCHAR(200) DEFAULT NULL COMMENT '英文全称',
    cnspell VARCHAR(50) DEFAULT NULL COMMENT '拼音缩写',
    market VARCHAR(50) DEFAULT NULL COMMENT '市场类型',
    exchange VARCHAR(10) DEFAULT NULL COMMENT '交易所代码',
    curr_type VARCHAR(10) DEFAULT NULL COMMENT '交易货币',
    list_status VARCHAR(10) DEFAULT NULL COMMENT '上市状态',
    list_date DATE DEFAULT NULL COMMENT '上市日期',
    delist_date DATE DEFAULT NULL COMMENT '退市日期',
    is_hs VARCHAR(10) DEFAULT NULL COMMENT '是否沪深港通标的',
    act_name VARCHAR(200) DEFAULT NULL COMMENT '实控人名称',
    act_ent_type VARCHAR(100) DEFAULT NULL COMMENT '实控人企业性质',
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    data_source VARCHAR(50) DEFAULT 'tushare' COMMENT '数据来源',
    sync_status VARCHAR(20) DEFAULT 'active' COMMENT '同步状态',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_ts_code (ts_code),
    KEY idx_symbol (symbol),
    KEY idx_name (name),
    KEY idx_industry (industry),
    KEY idx_market (market),
    KEY idx_exchange (exchange),
    KEY idx_list_status (list_status),
    KEY idx_list_date (list_date),
    KEY idx_is_hs (is_hs),
    KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基础信息表 (Tushare数据源)';

-- 4. 从stock_basic复制数据到stock_basic
INSERT INTO stock_basic (
    ts_code, symbol, name, area, industry, fullname, enname, cnspell,
    market, exchange, curr_type, list_status, list_date, delist_date,
    is_hs, act_name, act_ent_type, created_at, updated_at, data_source, sync_status
)
SELECT 
    ts_code, symbol, name, area, industry, fullname, enname, cnspell,
    market, exchange, curr_type, list_status, list_date, delist_date,
    is_hs, act_name, act_ent_type, created_at, updated_at, data_source, sync_status
FROM stock_basic;

-- 5. 验证数据复制结果
SELECT 
    'stock_basic' as table_name, 
    COUNT(*) as row_count 
FROM stock_basic
UNION ALL
SELECT 
    'stock_basic' as table_name, 
    COUNT(*) as row_count 
FROM stock_basic;

-- 6. 检查前5条数据
SELECT 
    ts_code, symbol, name, market, list_status, data_source
FROM stock_basic 
ORDER BY ts_code 
LIMIT 5;

-- 7. 更新外键引用（如果需要）
-- 注意：如果有其他表引用stock_basic，需要检查外键约束
-- 可以运行以下查询来检查外键引用：
/*
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE REFERENCED_TABLE_SCHEMA = 'stock_trading'
AND REFERENCED_TABLE_NAME = 'stock_basic';
*/

-- 8. 清理备份表（可选，建议保留一段时间）
-- DROP TABLE IF EXISTS stock_basic_backup_manual;