-- 创建申万行业分类表
CREATE TABLE IF NOT EXISTS industry_classification (
    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    industry_code VARCHAR(20) NOT NULL COMMENT '行业代码',
    industry_name VARCHAR(100) COMMENT '行业名称',
    level INT NOT NULL COMMENT '行业级别(1:一级/2:二级/3:三级)',
    classification_type VARCHAR(20) NOT NULL DEFAULT 'SW2021' COMMENT '分类标准(SW2021:申万2021/ZJHHY:证监会)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (ts_code, industry_code, level),
    INDEX idx_ts_code (ts_code),
    INDEX idx_industry_code (industry_code),
    INDEX idx_level (level),
    INDEX idx_classification_type (classification_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='申万行业分类表';

-- 查看表结构
DESC industry_classification;

-- 示例数据
-- INSERT INTO industry_classification 
-- (ts_code, industry_code, industry_name, level, classification_type)
-- VALUES 
-- ('000001.SZ', '801780', '银行', 1, 'SW2021'),
-- ('000001.SZ', '801790', '银行II', 2, 'SW2021');
