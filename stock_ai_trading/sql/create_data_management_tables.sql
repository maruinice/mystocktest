-- 数据管理功能相关表结构
-- 包含数据源配置表和API管理表

-- 1. 数据源配置表
CREATE TABLE IF NOT EXISTS data_sources (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    name VARCHAR(100) NOT NULL COMMENT '数据源名称',
    type ENUM('market_data', 'trading_data') NOT NULL COMMENT '数据源类型：market_data-行情数据源，trading_data-交易数据源',
    provider VARCHAR(50) NOT NULL COMMENT '数据提供商（如tushare、同花顺等）',
    status ENUM('active', 'inactive', 'testing') DEFAULT 'inactive' COMMENT '状态：active-启用，inactive-禁用，testing-测试中',
    
    -- 连接配置
    api_key VARCHAR(500) COMMENT 'API密钥（加密存储）',
    api_secret VARCHAR(500) COMMENT 'API密钥（加密存储）',
    base_url VARCHAR(200) COMMENT '基础URL',
    timeout INT DEFAULT 30 COMMENT '超时时间（秒）',
    rate_limit INT DEFAULT 200 COMMENT '速率限制（每分钟请求数）',
    
    -- 配置参数（JSON格式存储其他配置）
    config_params JSON COMMENT '其他配置参数',
    
    -- 统计信息
    total_calls BIGINT DEFAULT 0 COMMENT '总调用次数',
    success_calls BIGINT DEFAULT 0 COMMENT '成功调用次数',
    last_call_time TIMESTAMP NULL COMMENT '最后调用时间',
    last_success_time TIMESTAMP NULL COMMENT '最后成功时间',
    
    -- 系统字段
    created_by BIGINT COMMENT '创建人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by BIGINT COMMENT '更新人ID',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_type (type),
    INDEX idx_provider (provider),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据源配置表';

-- 2. API接口管理表
CREATE TABLE IF NOT EXISTS api_interfaces (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    data_source_id BIGINT NOT NULL COMMENT '数据源ID',
    
    -- API基本信息
    api_code VARCHAR(100) NOT NULL COMMENT 'API代码（如stock_basic）',
    api_name VARCHAR(200) NOT NULL COMMENT 'API名称',
    api_category VARCHAR(100) COMMENT 'API分类（如基础数据、行情数据等）',
    description TEXT COMMENT 'API描述',
    
    -- API配置
    endpoint VARCHAR(200) COMMENT 'API端点',
    method ENUM('GET', 'POST', 'PUT', 'DELETE') DEFAULT 'GET' COMMENT 'HTTP方法',
    required_params JSON COMMENT '必需参数配置',
    optional_params JSON COMMENT '可选参数配置',
    response_fields JSON COMMENT '响应字段配置',
    
    -- 权限和限制
    required_points INT DEFAULT 0 COMMENT '所需积分',
    rate_limit INT COMMENT 'API速率限制',
    data_limit INT COMMENT '数据量限制',
    
    -- 状态和统计
    status ENUM('active', 'inactive', 'deprecated') DEFAULT 'active' COMMENT '状态',
    total_calls BIGINT DEFAULT 0 COMMENT '总调用次数',
    success_calls BIGINT DEFAULT 0 COMMENT '成功调用次数',
    last_call_time TIMESTAMP NULL COMMENT '最后调用时间',
    last_success_time TIMESTAMP NULL COMMENT '最后成功时间',
    avg_response_time DECIMAL(10,3) COMMENT '平均响应时间（秒）',
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    synced_at TIMESTAMP NULL COMMENT '最后同步时间',
    
    -- 外键约束
    FOREIGN KEY (data_source_id) REFERENCES data_sources(id) ON DELETE CASCADE,
    
    -- 索引
    UNIQUE KEY uk_datasource_apicode (data_source_id, api_code),
    INDEX idx_api_category (api_category),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_synced_at (synced_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API接口管理表';

-- 3. API调用记录表
CREATE TABLE IF NOT EXISTS api_call_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    api_interface_id BIGINT NOT NULL COMMENT 'API接口ID',
    
    -- 调用信息
    call_type ENUM('test', 'sync', 'manual') NOT NULL COMMENT '调用类型：test-测试，sync-同步，manual-手动',
    request_params JSON COMMENT '请求参数',
    
    -- 响应信息
    status_code INT COMMENT 'HTTP状态码',
    success BOOLEAN DEFAULT FALSE COMMENT '是否成功',
    response_data JSON COMMENT '响应数据（限制大小）',
    response_size INT COMMENT '响应数据大小（字节）',
    response_time DECIMAL(10,3) COMMENT '响应时间（秒）',
    
    -- 错误信息
    error_code VARCHAR(50) COMMENT '错误代码',
    error_message TEXT COMMENT '错误信息',
    
    -- 系统字段
    called_by BIGINT COMMENT '调用人ID',
    called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '调用时间',
    
    -- 外键约束
    FOREIGN KEY (api_interface_id) REFERENCES api_interfaces(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_api_interface (api_interface_id),
    INDEX idx_call_type (call_type),
    INDEX idx_success (success),
    INDEX idx_called_at (called_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API调用记录表';

-- 4. API同步任务表
CREATE TABLE IF NOT EXISTS api_sync_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    data_source_id BIGINT NOT NULL COMMENT '数据源ID',
    
    -- 任务信息
    task_name VARCHAR(200) NOT NULL COMMENT '任务名称',
    task_type ENUM('full_sync', 'incremental_sync', 'api_discovery') NOT NULL COMMENT '任务类型',
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending' COMMENT '任务状态',
    
    -- 执行信息
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    progress INT DEFAULT 0 COMMENT '进度百分比',
    
    -- 结果统计
    total_apis INT DEFAULT 0 COMMENT '总API数量',
    new_apis INT DEFAULT 0 COMMENT '新增API数量',
    updated_apis INT DEFAULT 0 COMMENT '更新API数量',
    failed_apis INT DEFAULT 0 COMMENT '失败API数量',
    
    -- 错误信息
    error_message TEXT COMMENT '错误信息',
    log_data JSON COMMENT '日志数据',
    
    -- 系统字段
    created_by BIGINT COMMENT '创建人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 外键约束
    FOREIGN KEY (data_source_id) REFERENCES data_sources(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_data_source (data_source_id),
    INDEX idx_status (status),
    INDEX idx_task_type (task_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API同步任务表';

-- 插入默认的Tushare数据源配置
INSERT INTO data_sources (name, type, provider, status, base_url, rate_limit, config_params, created_at) VALUES
('Tushare Pro', 'market_data', 'tushare', 'active', 'http://api.tushare.pro', 200, 
 JSON_OBJECT('version', 'pro', 'format', 'json', 'timeout', 30), NOW())
ON DUPLICATE KEY UPDATE updated_at = NOW();

-- 插入预留的交易数据源配置
INSERT INTO data_sources (name, type, provider, status, config_params, created_at) VALUES
('交易接口', 'trading_data', 'reserved', 'inactive', 
 JSON_OBJECT('note', '预留交易数据源，暂未实现'), NOW())
ON DUPLICATE KEY UPDATE updated_at = NOW();

-- 创建视图：数据源统计
CREATE OR REPLACE VIEW v_data_source_stats AS
SELECT 
    ds.id,
    ds.name,
    ds.type,
    ds.provider,
    ds.status,
    ds.total_calls,
    ds.success_calls,
    CASE 
        WHEN ds.total_calls > 0 THEN ROUND((ds.success_calls / ds.total_calls) * 100, 2)
        ELSE 0 
    END as success_rate,
    COUNT(ai.id) as api_count,
    COUNT(CASE WHEN ai.status = 'active' THEN 1 END) as active_api_count,
    ds.last_call_time,
    ds.created_at
FROM data_sources ds
LEFT JOIN api_interfaces ai ON ds.id = ai.data_source_id
GROUP BY ds.id, ds.name, ds.type, ds.provider, ds.status, ds.total_calls, ds.success_calls, ds.last_call_time, ds.created_at;

-- 创建视图：API接口统计
CREATE OR REPLACE VIEW v_api_interface_stats AS
SELECT 
    ai.id,
    ai.api_code,
    ai.api_name,
    ai.api_category,
    ai.status,
    ds.name as data_source_name,
    ds.provider,
    ai.total_calls,
    ai.success_calls,
    CASE 
        WHEN ai.total_calls > 0 THEN ROUND((ai.success_calls / ai.total_calls) * 100, 2)
        ELSE 0 
    END as success_rate,
    ai.avg_response_time,
    ai.last_call_time,
    ai.synced_at,
    ai.created_at
FROM api_interfaces ai
JOIN data_sources ds ON ai.data_source_id = ds.id;