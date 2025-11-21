-- =====================================================
-- 模型管理系统数据库设计
-- 创建时间: 2024-01-01
-- 版本: 1.0
-- 描述: 完整的AI模型管理系统数据库架构
-- =====================================================

-- 设置字符集和排序规则
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- 1. ai_models 模型主表
-- =====================================================
DROP TABLE IF EXISTS `ai_models`;
CREATE TABLE `ai_models` (
  `model_id` varchar(50) NOT NULL COMMENT '模型唯一标识',
  `name` varchar(100) NOT NULL COMMENT '模型名称',
  `display_name` varchar(150) DEFAULT NULL COMMENT '显示名称',
  `description` text COMMENT '模型描述',
  
  -- 模型类型和提供商信息
  `model_type` enum('DeepSeek','ChatGPT','Claude','Llama','Custom','Ensemble') NOT NULL COMMENT '模型类型',
  `provider` varchar(50) NOT NULL COMMENT '提供商(openai/anthropic/deepseek/local等)',
  `model_version` varchar(50) DEFAULT NULL COMMENT '模型版本',
  
  -- API配置信息
  `api_key_encrypted` text COMMENT 'API密钥(AES加密存储)',
  `base_url` varchar(500) DEFAULT NULL COMMENT 'API基础URL',
  `api_endpoint` varchar(200) DEFAULT NULL COMMENT 'API端点',
  
  -- 模型参数配置
  `max_tokens` int(11) DEFAULT 4096 COMMENT '最大token数',
  `temperature` decimal(3,2) DEFAULT 0.70 COMMENT '温度参数(0.0-2.0)',
  `top_p` decimal(3,2) DEFAULT 1.00 COMMENT 'Top-p参数',
  `frequency_penalty` decimal(3,2) DEFAULT 0.00 COMMENT '频率惩罚',
  `presence_penalty` decimal(3,2) DEFAULT 0.00 COMMENT '存在惩罚',
  
  -- 性能指标
  `accuracy_rate` decimal(5,4) DEFAULT 0.0000 COMMENT '准确率(0.0000-1.0000)',
  `weight` decimal(5,4) DEFAULT 1.0000 COMMENT '权重(0.0000-1.0000)',
  `avg_response_time` int(11) DEFAULT 0 COMMENT '平均响应时间(毫秒)',
  `success_rate` decimal(5,4) DEFAULT 0.0000 COMMENT '成功率',
  
  -- 状态管理
  `status` enum('active','inactive','training','error','maintenance') NOT NULL DEFAULT 'inactive' COMMENT '运行状态',
  `enabled` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否启用(0:禁用,1:启用)',
  `health_status` enum('healthy','warning','error','unknown') DEFAULT 'unknown' COMMENT '健康状态',
  
  -- 使用统计
  `total_requests` bigint(20) DEFAULT 0 COMMENT '总请求次数',
  `total_tokens_used` bigint(20) DEFAULT 0 COMMENT '总使用token数',
  `last_used_at` timestamp NULL DEFAULT NULL COMMENT '最后使用时间',
  
  -- 训练信息
  `last_trained_at` timestamp NULL DEFAULT NULL COMMENT '最后训练时间',
  `training_data_version` varchar(50) DEFAULT NULL COMMENT '训练数据版本',
  `training_status` enum('not_trained','training','completed','failed') DEFAULT 'not_trained' COMMENT '训练状态',
  
  -- 扩展配置
  `config_json` json DEFAULT NULL COMMENT '扩展配置(JSON格式)',
  `tags` json DEFAULT NULL COMMENT '标签数组',
  
  -- 审计字段
  `created_by` varchar(50) DEFAULT NULL COMMENT '创建者',
  `updated_by` varchar(50) DEFAULT NULL COMMENT '更新者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`model_id`),
  UNIQUE KEY `uk_models_name` (`name`),
  KEY `idx_models_type` (`model_type`),
  KEY `idx_models_provider` (`provider`),
  KEY `idx_models_status` (`status`),
  KEY `idx_models_enabled` (`enabled`),
  KEY `idx_models_created_at` (`created_at`),
  KEY `idx_models_accuracy` (`accuracy_rate`),
  KEY `idx_models_last_used` (`last_used_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI模型主表';

-- =====================================================
-- 2. model_ensembles 模型组合表
-- =====================================================
DROP TABLE IF EXISTS `model_ensembles`;
CREATE TABLE `model_ensembles` (
  `ensemble_id` varchar(50) NOT NULL COMMENT '组合唯一标识',
  `name` varchar(100) NOT NULL COMMENT '组合名称',
  `display_name` varchar(150) DEFAULT NULL COMMENT '显示名称',
  `description` text COMMENT '组合描述',
  
  -- 组合策略配置
  `weight_strategy` enum('equal_weight','accuracy_weight','manual_weight','dynamic_weight','performance_weight') NOT NULL DEFAULT 'equal_weight' COMMENT '权重策略',
  `voting_method` enum('majority','weighted','confidence','threshold') DEFAULT 'weighted' COMMENT '投票方法',
  `confidence_threshold` decimal(3,2) DEFAULT 0.50 COMMENT '置信度阈值',
  
  -- 性能指标
  `overall_accuracy` decimal(5,4) DEFAULT 0.0000 COMMENT '综合准确率',
  `model_count` int(11) DEFAULT 0 COMMENT '包含模型数量',
  `active_model_count` int(11) DEFAULT 0 COMMENT '活跃模型数量',
  `avg_response_time` int(11) DEFAULT 0 COMMENT '平均响应时间(毫秒)',
  
  -- 状态管理
  `status` enum('active','inactive','configuring','error') NOT NULL DEFAULT 'inactive' COMMENT '组合状态',
  `enabled` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否启用',
  `health_status` enum('healthy','warning','error','unknown') DEFAULT 'unknown' COMMENT '健康状态',
  
  -- 使用统计
  `total_requests` bigint(20) DEFAULT 0 COMMENT '总请求次数',
  `success_requests` bigint(20) DEFAULT 0 COMMENT '成功请求次数',
  `last_used_at` timestamp NULL DEFAULT NULL COMMENT '最后使用时间',
  
  -- 配置信息
  `config_json` json DEFAULT NULL COMMENT '组合配置(JSON格式)',
  `tags` json DEFAULT NULL COMMENT '标签数组',
  
  -- 审计字段
  `created_by` varchar(50) DEFAULT NULL COMMENT '创建者',
  `updated_by` varchar(50) DEFAULT NULL COMMENT '更新者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`ensemble_id`),
  UNIQUE KEY `uk_ensembles_name` (`name`),
  KEY `idx_ensembles_strategy` (`weight_strategy`),
  KEY `idx_ensembles_status` (`status`),
  KEY `idx_ensembles_enabled` (`enabled`),
  KEY `idx_ensembles_accuracy` (`overall_accuracy`),
  KEY `idx_ensembles_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型组合表';

-- =====================================================
-- 3. ensemble_model_mapping 组合模型关联表
-- =====================================================
DROP TABLE IF EXISTS `ensemble_model_mapping`;
CREATE TABLE `ensemble_model_mapping` (
  `mapping_id` varchar(50) NOT NULL COMMENT '关联唯一标识',
  `ensemble_id` varchar(50) NOT NULL COMMENT '组合ID',
  `model_id` varchar(50) NOT NULL COMMENT '模型ID',
  
  -- 权重和优先级
  `weight` decimal(5,4) NOT NULL DEFAULT 1.0000 COMMENT '权重(0.0000-1.0000)',
  `priority` int(11) DEFAULT 1 COMMENT '优先级(数字越小优先级越高)',
  `order_index` int(11) DEFAULT 0 COMMENT '排序索引',
  
  -- 状态管理
  `enabled` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用此关联',
  `status` enum('active','inactive','error') DEFAULT 'active' COMMENT '关联状态',
  
  -- 性能统计
  `contribution_score` decimal(5,4) DEFAULT 0.0000 COMMENT '贡献度评分',
  `usage_count` bigint(20) DEFAULT 0 COMMENT '使用次数',
  `last_used_at` timestamp NULL DEFAULT NULL COMMENT '最后使用时间',
  
  -- 配置信息
  `config_json` json DEFAULT NULL COMMENT '关联配置(JSON格式)',
  
  -- 审计字段
  `created_by` varchar(50) DEFAULT NULL COMMENT '创建者',
  `updated_by` varchar(50) DEFAULT NULL COMMENT '更新者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`mapping_id`),
  UNIQUE KEY `uk_ensemble_model` (`ensemble_id`, `model_id`),
  KEY `idx_mapping_ensemble` (`ensemble_id`),
  KEY `idx_mapping_model` (`model_id`),
  KEY `idx_mapping_weight` (`weight`),
  KEY `idx_mapping_priority` (`priority`),
  KEY `idx_mapping_enabled` (`enabled`),
  
  CONSTRAINT `fk_mapping_ensemble` FOREIGN KEY (`ensemble_id`) REFERENCES `model_ensembles` (`ensemble_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_mapping_model` FOREIGN KEY (`model_id`) REFERENCES `ai_models` (`model_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组合模型关联表';

-- =====================================================
-- 4. model_test_records 模型测试记录表
-- =====================================================
DROP TABLE IF EXISTS `model_test_records`;
CREATE TABLE `model_test_records` (
  `test_id` varchar(50) NOT NULL COMMENT '测试记录唯一标识',
  `model_id` varchar(50) NOT NULL COMMENT '模型ID',
  `ensemble_id` varchar(50) DEFAULT NULL COMMENT '组合ID(如果是组合测试)',
  
  -- 测试基本信息
  `test_type` enum('unit','integration','performance','accuracy','stress') NOT NULL COMMENT '测试类型',
  `test_name` varchar(200) DEFAULT NULL COMMENT '测试名称',
  `test_description` text COMMENT '测试描述',
  
  -- 测试输入输出
  `input_data` json NOT NULL COMMENT '测试输入数据(JSON格式)',
  `expected_output` json DEFAULT NULL COMMENT '期望输出(JSON格式)',
  `actual_output` json DEFAULT NULL COMMENT '实际输出(JSON格式)',
  
  -- 性能指标
  `response_time_ms` int(11) DEFAULT NULL COMMENT '响应时间(毫秒)',
  `token_count` int(11) DEFAULT NULL COMMENT 'Token使用数量',
  `success` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否成功(0:失败,1:成功)',
  `accuracy_score` decimal(5,4) DEFAULT NULL COMMENT '准确率得分',
  
  -- 错误信息
  `error_code` varchar(50) DEFAULT NULL COMMENT '错误代码',
  `error_message` text COMMENT '错误信息',
  `error_details` json DEFAULT NULL COMMENT '错误详情(JSON格式)',
  
  -- 测试环境信息
  `test_environment` varchar(100) DEFAULT NULL COMMENT '测试环境',
  `test_version` varchar(50) DEFAULT NULL COMMENT '测试版本',
  `batch_id` varchar(50) DEFAULT NULL COMMENT '批次ID(用于批量测试)',
  
  -- 审计字段
  `tested_by` varchar(50) DEFAULT NULL COMMENT '测试者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  PRIMARY KEY (`test_id`),
  KEY `idx_test_model` (`model_id`),
  KEY `idx_test_ensemble` (`ensemble_id`),
  KEY `idx_test_type` (`test_type`),
  KEY `idx_test_success` (`success`),
  KEY `idx_test_created_at` (`created_at`),
  KEY `idx_test_batch` (`batch_id`),
  KEY `idx_test_response_time` (`response_time_ms`),
  
  CONSTRAINT `fk_test_model` FOREIGN KEY (`model_id`) REFERENCES `ai_models` (`model_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_test_ensemble` FOREIGN KEY (`ensemble_id`) REFERENCES `model_ensembles` (`ensemble_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型测试记录表';

-- =====================================================
-- 5. model_metrics 模型性能指标表
-- =====================================================
DROP TABLE IF EXISTS `model_metrics`;
CREATE TABLE `model_metrics` (
  `metric_id` varchar(50) NOT NULL COMMENT '指标记录唯一标识',
  `model_id` varchar(50) NOT NULL COMMENT '模型ID',
  `ensemble_id` varchar(50) DEFAULT NULL COMMENT '组合ID(如果是组合指标)',
  
  -- 时间维度
  `metric_date` date NOT NULL COMMENT '指标日期',
  `metric_hour` tinyint(4) DEFAULT NULL COMMENT '指标小时(0-23,用于小时级统计)',
  `time_period` enum('hourly','daily','weekly','monthly') NOT NULL DEFAULT 'daily' COMMENT '时间周期',
  
  -- 性能指标
  `accuracy_rate` decimal(5,4) DEFAULT 0.0000 COMMENT '准确率',
  `avg_response_time_ms` int(11) DEFAULT 0 COMMENT '平均响应时间(毫秒)',
  `success_rate` decimal(5,4) DEFAULT 0.0000 COMMENT '成功率',
  `error_rate` decimal(5,4) DEFAULT 0.0000 COMMENT '错误率',
  
  -- 使用统计
  `total_requests` bigint(20) DEFAULT 0 COMMENT '总请求次数',
  `successful_requests` bigint(20) DEFAULT 0 COMMENT '成功请求次数',
  `failed_requests` bigint(20) DEFAULT 0 COMMENT '失败请求次数',
  `total_tokens_used` bigint(20) DEFAULT 0 COMMENT '总使用token数',
  
  -- 响应时间分布
  `response_time_p50` int(11) DEFAULT NULL COMMENT '响应时间50分位数',
  `response_time_p90` int(11) DEFAULT NULL COMMENT '响应时间90分位数',
  `response_time_p95` int(11) DEFAULT NULL COMMENT '响应时间95分位数',
  `response_time_p99` int(11) DEFAULT NULL COMMENT '响应时间99分位数',
  
  -- 成本统计
  `estimated_cost` decimal(10,4) DEFAULT 0.0000 COMMENT '预估成本',
  `cost_per_request` decimal(8,6) DEFAULT 0.000000 COMMENT '每请求成本',
  
  -- 质量指标
  `confidence_score` decimal(5,4) DEFAULT NULL COMMENT '置信度得分',
  `consistency_score` decimal(5,4) DEFAULT NULL COMMENT '一致性得分',
  `relevance_score` decimal(5,4) DEFAULT NULL COMMENT '相关性得分',
  
  -- 扩展指标
  `custom_metrics` json DEFAULT NULL COMMENT '自定义指标(JSON格式)',
  
  -- 审计字段
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`metric_id`),
  UNIQUE KEY `uk_metrics_model_date_period` (`model_id`, `metric_date`, `time_period`, `metric_hour`),
  KEY `idx_metrics_model` (`model_id`),
  KEY `idx_metrics_ensemble` (`ensemble_id`),
  KEY `idx_metrics_date` (`metric_date`),
  KEY `idx_metrics_period` (`time_period`),
  KEY `idx_metrics_accuracy` (`accuracy_rate`),
  KEY `idx_metrics_response_time` (`avg_response_time_ms`),
  KEY `idx_metrics_success_rate` (`success_rate`),
  KEY `idx_metrics_created_at` (`created_at`),
  
  CONSTRAINT `fk_metrics_model` FOREIGN KEY (`model_id`) REFERENCES `ai_models` (`model_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_metrics_ensemble` FOREIGN KEY (`ensemble_id`) REFERENCES `model_ensembles` (`ensemble_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型性能指标表';

-- =====================================================
-- 6. model_api_keys 模型API密钥表 (独立存储,增强安全性)
-- =====================================================
DROP TABLE IF EXISTS `model_api_keys`;
CREATE TABLE `model_api_keys` (
  `key_id` varchar(50) NOT NULL COMMENT '密钥唯一标识',
  `model_id` varchar(50) NOT NULL COMMENT '模型ID',
  
  -- 密钥信息
  `key_name` varchar(100) NOT NULL COMMENT '密钥名称',
  `encrypted_key` text NOT NULL COMMENT '加密后的API密钥',
  `key_hash` varchar(64) NOT NULL COMMENT '密钥哈希值(用于验证)',
  `encryption_method` varchar(50) DEFAULT 'AES-256-GCM' COMMENT '加密方法',
  
  -- 使用限制
  `rate_limit_per_minute` int(11) DEFAULT NULL COMMENT '每分钟请求限制',
  `rate_limit_per_day` int(11) DEFAULT NULL COMMENT '每日请求限制',
  `monthly_quota` bigint(20) DEFAULT NULL COMMENT '月度配额',
  `used_quota` bigint(20) DEFAULT 0 COMMENT '已使用配额',
  
  -- 状态管理
  `status` enum('active','inactive','expired','revoked') NOT NULL DEFAULT 'active' COMMENT '密钥状态',
  `expires_at` timestamp NULL DEFAULT NULL COMMENT '过期时间',
  `last_used_at` timestamp NULL DEFAULT NULL COMMENT '最后使用时间',
  
  -- 审计字段
  `created_by` varchar(50) DEFAULT NULL COMMENT '创建者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`key_id`),
  UNIQUE KEY `uk_api_keys_model_name` (`model_id`, `key_name`),
  KEY `idx_api_keys_model` (`model_id`),
  KEY `idx_api_keys_status` (`status`),
  KEY `idx_api_keys_expires` (`expires_at`),
  
  CONSTRAINT `fk_api_keys_model` FOREIGN KEY (`model_id`) REFERENCES `ai_models` (`model_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型API密钥表';

-- =====================================================
-- 7. model_usage_logs 模型使用日志表
-- =====================================================
DROP TABLE IF EXISTS `model_usage_logs`;
CREATE TABLE `model_usage_logs` (
  `log_id` varchar(50) NOT NULL COMMENT '日志唯一标识',
  `model_id` varchar(50) NOT NULL COMMENT '模型ID',
  `ensemble_id` varchar(50) DEFAULT NULL COMMENT '组合ID',
  
  -- 请求信息
  `request_id` varchar(50) DEFAULT NULL COMMENT '请求ID',
  `user_id` varchar(50) DEFAULT NULL COMMENT '用户ID',
  `session_id` varchar(100) DEFAULT NULL COMMENT '会话ID',
  
  -- 使用详情
  `input_tokens` int(11) DEFAULT 0 COMMENT '输入token数',
  `output_tokens` int(11) DEFAULT 0 COMMENT '输出token数',
  `total_tokens` int(11) DEFAULT 0 COMMENT '总token数',
  `response_time_ms` int(11) DEFAULT NULL COMMENT '响应时间(毫秒)',
  
  -- 结果信息
  `success` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否成功',
  `error_code` varchar(50) DEFAULT NULL COMMENT '错误代码',
  `error_message` text COMMENT '错误信息',
  
  -- 成本信息
  `estimated_cost` decimal(8,6) DEFAULT 0.000000 COMMENT '预估成本',
  
  -- 审计字段
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  PRIMARY KEY (`log_id`),
  KEY `idx_usage_logs_model` (`model_id`),
  KEY `idx_usage_logs_ensemble` (`ensemble_id`),
  KEY `idx_usage_logs_user` (`user_id`),
  KEY `idx_usage_logs_success` (`success`),
  KEY `idx_usage_logs_created_at` (`created_at`),
  KEY `idx_usage_logs_request` (`request_id`),
  
  CONSTRAINT `fk_usage_logs_model` FOREIGN KEY (`model_id`) REFERENCES `ai_models` (`model_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_usage_logs_ensemble` FOREIGN KEY (`ensemble_id`) REFERENCES `model_ensembles` (`ensemble_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型使用日志表';

-- =====================================================
-- 创建视图 - 模型性能概览
-- =====================================================
CREATE OR REPLACE VIEW `v_model_performance_overview` AS
SELECT 
    m.model_id,
    m.name,
    m.model_type,
    m.provider,
    m.status,
    m.enabled,
    m.accuracy_rate,
    m.weight,
    m.avg_response_time,
    m.success_rate,
    m.total_requests,
    m.last_used_at,
    COALESCE(mt.daily_accuracy, 0) as today_accuracy,
    COALESCE(mt.daily_requests, 0) as today_requests,
    COALESCE(mt.daily_avg_response_time, 0) as today_avg_response_time
FROM ai_models m
LEFT JOIN (
    SELECT 
        model_id,
        accuracy_rate as daily_accuracy,
        total_requests as daily_requests,
        avg_response_time_ms as daily_avg_response_time
    FROM model_metrics 
    WHERE metric_date = CURDATE() 
    AND time_period = 'daily'
) mt ON m.model_id = mt.model_id;

-- =====================================================
-- 创建视图 - 组合性能概览
-- =====================================================
CREATE OR REPLACE VIEW `v_ensemble_performance_overview` AS
SELECT 
    e.ensemble_id,
    e.name,
    e.weight_strategy,
    e.status,
    e.enabled,
    e.overall_accuracy,
    e.model_count,
    e.active_model_count,
    e.avg_response_time,
    e.total_requests,
    e.last_used_at,
    GROUP_CONCAT(CONCAT(m.name, '(', emm.weight, ')') ORDER BY emm.priority) as model_details
FROM model_ensembles e
LEFT JOIN ensemble_model_mapping emm ON e.ensemble_id = emm.ensemble_id AND emm.enabled = 1
LEFT JOIN ai_models m ON emm.model_id = m.model_id
GROUP BY e.ensemble_id;

-- =====================================================
-- 插入初始数据示例
-- =====================================================

-- 插入示例模型数据
INSERT INTO `ai_models` (
    `model_id`, `name`, `display_name`, `description`, `model_type`, `provider`, 
    `model_version`, `max_tokens`, `temperature`, `accuracy_rate`, `weight`, 
    `status`, `enabled`, `created_by`
) VALUES 
('deepseek_chat_001', 'DeepSeek Chat', 'DeepSeek 对话模型', '高性能对话生成模型', 'DeepSeek', 'deepseek', 'v1.0', 4096, 0.7, 0.8500, 1.0000, 'active', 1, 'system'),
('gpt4_turbo_001', 'GPT-4 Turbo', 'OpenAI GPT-4 Turbo', '最新的GPT-4 Turbo模型', 'ChatGPT', 'openai', 'gpt-4-turbo', 8192, 0.7, 0.9200, 1.0000, 'active', 1, 'system'),
('claude3_opus_001', 'Claude-3 Opus', 'Anthropic Claude-3 Opus', '高质量推理模型', 'Claude', 'anthropic', 'claude-3-opus', 4096, 0.7, 0.9000, 1.0000, 'active', 1, 'system'),
('llama2_70b_001', 'Llama-2 70B', 'Meta Llama-2 70B', '开源大语言模型', 'Llama', 'meta', 'llama-2-70b', 4096, 0.7, 0.8200, 1.0000, 'inactive', 0, 'system');

-- 插入示例组合数据
INSERT INTO `model_ensembles` (
    `ensemble_id`, `name`, `display_name`, `description`, `weight_strategy`, 
    `overall_accuracy`, `model_count`, `status`, `enabled`, `created_by`
) VALUES 
('ensemble_premium_001', 'Premium Ensemble', '高级模型组合', '包含最优秀模型的组合', 'accuracy_weight', 0.9100, 3, 'active', 1, 'system'),
('ensemble_balanced_001', 'Balanced Ensemble', '平衡模型组合', '性能与成本平衡的组合', 'equal_weight', 0.8700, 2, 'active', 1, 'system');

-- 插入组合关联关系
INSERT INTO `ensemble_model_mapping` (
    `mapping_id`, `ensemble_id`, `model_id`, `weight`, `priority`, `enabled`, `created_by`
) VALUES 
('mapping_001', 'ensemble_premium_001', 'gpt4_turbo_001', 0.4000, 1, 1, 'system'),
('mapping_002', 'ensemble_premium_001', 'claude3_opus_001', 0.3500, 2, 1, 'system'),
('mapping_003', 'ensemble_premium_001', 'deepseek_chat_001', 0.2500, 3, 1, 'system'),
('mapping_004', 'ensemble_balanced_001', 'deepseek_chat_001', 0.5000, 1, 1, 'system'),
('mapping_005', 'ensemble_balanced_001', 'gpt4_turbo_001', 0.5000, 2, 1, 'system');

-- =====================================================
-- 创建存储过程 - 更新模型指标
-- =====================================================
DELIMITER $$

CREATE PROCEDURE `sp_update_model_metrics`(
    IN p_model_id VARCHAR(50),
    IN p_metric_date DATE,
    IN p_accuracy_rate DECIMAL(5,4),
    IN p_avg_response_time INT,
    IN p_success_rate DECIMAL(5,4),
    IN p_total_requests BIGINT,
    IN p_successful_requests BIGINT,
    IN p_failed_requests BIGINT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    INSERT INTO model_metrics (
        metric_id, model_id, metric_date, time_period,
        accuracy_rate, avg_response_time_ms, success_rate,
        total_requests, successful_requests, failed_requests
    ) VALUES (
        CONCAT('metric_', p_model_id, '_', DATE_FORMAT(p_metric_date, '%Y%m%d')),
        p_model_id, p_metric_date, 'daily',
        p_accuracy_rate, p_avg_response_time, p_success_rate,
        p_total_requests, p_successful_requests, p_failed_requests
    ) ON DUPLICATE KEY UPDATE
        accuracy_rate = p_accuracy_rate,
        avg_response_time_ms = p_avg_response_time,
        success_rate = p_success_rate,
        total_requests = p_total_requests,
        successful_requests = p_successful_requests,
        failed_requests = p_failed_requests,
        updated_at = CURRENT_TIMESTAMP;
    
    -- 更新模型主表的统计信息
    UPDATE ai_models SET
        accuracy_rate = p_accuracy_rate,
        avg_response_time = p_avg_response_time,
        success_rate = p_success_rate,
        total_requests = p_total_requests,
        updated_at = CURRENT_TIMESTAMP
    WHERE model_id = p_model_id;
    
    COMMIT;
END$$

DELIMITER ;

-- =====================================================
-- 创建触发器 - 自动更新组合统计
-- =====================================================
DELIMITER $$

CREATE TRIGGER `tr_update_ensemble_stats_after_mapping_change`
AFTER INSERT ON `ensemble_model_mapping`
FOR EACH ROW
BEGIN
    UPDATE model_ensembles SET
        model_count = (
            SELECT COUNT(*) 
            FROM ensemble_model_mapping 
            WHERE ensemble_id = NEW.ensemble_id
        ),
        active_model_count = (
            SELECT COUNT(*) 
            FROM ensemble_model_mapping emm
            JOIN ai_models m ON emm.model_id = m.model_id
            WHERE emm.ensemble_id = NEW.ensemble_id 
            AND emm.enabled = 1 
            AND m.enabled = 1 
            AND m.status = 'active'
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE ensemble_id = NEW.ensemble_id;
END$$

DELIMITER ;

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- 数据库设计说明
-- =====================================================
/*
1. 安全性设计:
   - API密钥采用AES加密存储
   - 独立的密钥管理表
   - 完整的审计字段

2. 性能优化:
   - 合理的索引设计
   - 分区表支持(可按日期分区)
   - 视图简化查询

3. 扩展性:
   - JSON字段支持灵活配置
   - 枚举类型易于扩展
   - 模块化表设计

4. 数据完整性:
   - 外键约束
   - 唯一性约束
   - 触发器自动维护统计

5. 监控和分析:
   - 详细的性能指标
   - 使用日志记录
   - 测试记录追踪
*/