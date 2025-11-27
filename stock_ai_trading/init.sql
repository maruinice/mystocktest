/*
 Navicat Premium Dump SQL

 Source Server         : 192.168.126.128_3306
 Source Server Type    : MySQL
 Source Server Version : 80042 (8.0.42)
 Source Host           : 192.168.126.128:3306
 Source Schema         : stock_trading

 Target Server Type    : MySQL
 Target Server Version : 80042 (8.0.42)
 File Encoding         : 65001

 Date: 26/11/2025 20:36:16
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for accounts
-- ----------------------------
DROP TABLE IF EXISTS `accounts`;
CREATE TABLE `accounts`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT 'ç”¨æˆ·ID',
  `total_assets` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'æ€»èµ„äº§',
  `available_cash` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'å¯ç”¨èµ„é‡‘',
  `frozen_cash` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'å†»ç»“èµ„é‡‘',
  `market_value` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'æŒä»“å¸‚å€¼',
  `profit_loss` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'æµ®åŠ¨ç›ˆäº',
  `profit_loss_pct` decimal(10, 4) NOT NULL DEFAULT 0.0000 COMMENT 'ç›ˆäºæ¯”ä¾‹(%)',
  `buying_power` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'è´­ä¹°åŠ›',
  `margin_used` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'å·²ç”¨ä¿è¯é‡‘',
  `margin_available` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'å¯ç”¨ä¿è¯é‡‘',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'åˆ›å»ºæ—¶é—´',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'æ›´æ–°æ—¶é—´',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE,
  CONSTRAINT `accounts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'è´¦æˆ·èµ„é‡‘è¡¨' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for adj_factor
-- ----------------------------
DROP TABLE IF EXISTS `adj_factor`;
CREATE TABLE `adj_factor`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `adj_factor` decimal(12, 6) NULL DEFAULT NULL COMMENT '复权因子',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`, `trade_date`) USING BTREE,
  UNIQUE INDEX `uk_ts_code_date`(`ts_code` ASC, `trade_date` ASC) USING BTREE,
  INDEX `idx_trade_date`(`trade_date` ASC) USING BTREE,
  INDEX `idx_ts_code`(`ts_code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 127537 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '复权因子表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for ai_decision_records
-- ----------------------------
DROP TABLE IF EXISTS `ai_decision_records`;
CREATE TABLE `ai_decision_records`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `decision_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '决策ID',
  `portfolio_id` bigint NULL DEFAULT NULL COMMENT '组合ID',
  `symbol` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `action` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易动作',
  `quantity` int NOT NULL COMMENT '交易数量',
  `price` float NULL DEFAULT NULL COMMENT '交易价格',
  `confidence` float NOT NULL COMMENT '置信度',
  `reasoning` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '决策理由',
  `model_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型ID',
  `instruction_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '指令类型',
  `execution_strategy` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '执行策略',
  `risk_score` float NULL DEFAULT NULL COMMENT '风险评分',
  `expected_return` float NULL DEFAULT NULL COMMENT '预期收益率',
  `stop_loss` float NULL DEFAULT NULL COMMENT '止损价格',
  `take_profit` float NULL DEFAULT NULL COMMENT '止盈价格',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '决策状态',
  `execution_result` json NULL COMMENT '执行结果',
  `actual_return` float NULL DEFAULT NULL COMMENT '实际收益率',
  `decision_time` datetime NOT NULL COMMENT '决策时间',
  `execution_time` datetime NULL DEFAULT NULL COMMENT '执行时间',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `decision_id`(`decision_id` ASC) USING BTREE,
  INDEX `idx_ai_decision_model`(`model_id` ASC) USING BTREE,
  INDEX `idx_ai_decision_status`(`status` ASC) USING BTREE,
  INDEX `idx_ai_decision_portfolio_time`(`portfolio_id` ASC, `decision_time` ASC) USING BTREE,
  INDEX `idx_ai_decision_symbol_time`(`symbol` ASC, `decision_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for ai_models
-- ----------------------------
DROP TABLE IF EXISTS `ai_models`;
CREATE TABLE `ai_models`  (
  `model_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型唯一标识',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型名称',
  `display_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '显示名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '模型描述',
  `model_type` enum('DeepSeek','ChatGPT','Claude','Llama','Custom','Ensemble') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型类型',
  `provider` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商(openai/anthropic/deepseek/local等)',
  `model_version` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '模型版本',
  `api_key_encrypted` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'API密钥(AES加密存储)',
  `base_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'API基础URL',
  `api_endpoint` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'API端点',
  `max_tokens` int NULL DEFAULT 4096 COMMENT '最大token数',
  `temperature` decimal(3, 2) NULL DEFAULT 0.70 COMMENT '温度参数(0.0-2.0)',
  `top_p` decimal(3, 2) NULL DEFAULT 1.00 COMMENT 'Top-p参数',
  `frequency_penalty` decimal(3, 2) NULL DEFAULT 0.00 COMMENT '频率惩罚',
  `presence_penalty` decimal(3, 2) NULL DEFAULT 0.00 COMMENT '存在惩罚',
  `accuracy_rate` decimal(5, 4) NULL DEFAULT 0.0000 COMMENT '准确率(0.0000-1.0000)',
  `weight` decimal(5, 4) NULL DEFAULT 1.0000 COMMENT '权重(0.0000-1.0000)',
  `avg_response_time` int NULL DEFAULT 0 COMMENT '平均响应时间(毫秒)',
  `success_rate` decimal(5, 4) NULL DEFAULT 0.0000 COMMENT '成功率',
  `status` enum('active','inactive','training','error','maintenance') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'inactive' COMMENT '运行状态',
  `enabled` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否启用(0:禁用,1:启用)',
  `health_status` enum('healthy','warning','error','unknown') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'unknown' COMMENT '健康状态',
  `total_requests` bigint NULL DEFAULT 0 COMMENT '总请求次数',
  `total_tokens_used` bigint NULL DEFAULT 0 COMMENT '总使用token数',
  `last_used_at` timestamp NULL DEFAULT NULL COMMENT '最后使用时间',
  `last_trained_at` timestamp NULL DEFAULT NULL COMMENT '最后训练时间',
  `training_data_version` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '训练数据版本',
  `training_status` enum('not_trained','training','completed','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'not_trained' COMMENT '训练状态',
  `config_json` json NULL COMMENT '扩展配置(JSON格式)',
  `tags` json NULL COMMENT '标签数组',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '创建者',
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`model_id`) USING BTREE,
  UNIQUE INDEX `uk_models_name`(`name` ASC) USING BTREE,
  INDEX `idx_models_type`(`model_type` ASC) USING BTREE,
  INDEX `idx_models_provider`(`provider` ASC) USING BTREE,
  INDEX `idx_models_status`(`status` ASC) USING BTREE,
  INDEX `idx_models_enabled`(`enabled` ASC) USING BTREE,
  INDEX `idx_models_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_models_accuracy`(`accuracy_rate` ASC) USING BTREE,
  INDEX `idx_models_last_used`(`last_used_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'AI模型主表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_call_logs
-- ----------------------------
DROP TABLE IF EXISTS `api_call_logs`;
CREATE TABLE `api_call_logs`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `api_interface_id` bigint NOT NULL COMMENT 'API接口ID',
  `call_type` enum('test','sync','manual') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '调用类型：test-测试，sync-同步，manual-手动',
  `request_params` json NULL COMMENT '请求参数',
  `status_code` int NULL DEFAULT NULL COMMENT 'HTTP状态码',
  `success` tinyint(1) NULL DEFAULT 0 COMMENT '是否成功',
  `response_data` json NULL COMMENT '响应数据（限制大小）',
  `response_size` int NULL DEFAULT NULL COMMENT '响应数据大小（字节）',
  `response_time` decimal(10, 3) NULL DEFAULT NULL COMMENT '响应时间（秒）',
  `error_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '错误代码',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `called_by` bigint NULL DEFAULT NULL COMMENT '调用人ID',
  `called_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '调用时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_api_interface`(`api_interface_id` ASC) USING BTREE,
  INDEX `idx_call_type`(`call_type` ASC) USING BTREE,
  INDEX `idx_success`(`success` ASC) USING BTREE,
  INDEX `idx_called_at`(`called_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'API调用记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_interfaces
-- ----------------------------
DROP TABLE IF EXISTS `api_interfaces`;
CREATE TABLE `api_interfaces`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `data_source_id` bigint NOT NULL COMMENT '数据源ID',
  `api_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'API代码（如stock_basic）',
  `api_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'API名称',
  `api_category` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'API分类（如基础数据、行情数据等）',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'API描述',
  `endpoint` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'API端点',
  `method` enum('GET','POST','PUT','DELETE') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'GET' COMMENT 'HTTP方法',
  `required_params` json NULL COMMENT '必需参数配置',
  `optional_params` json NULL COMMENT '可选参数配置',
  `response_fields` json NULL COMMENT '响应字段配置',
  `required_points` int NULL DEFAULT 0 COMMENT '所需积分',
  `rate_limit` int NULL DEFAULT NULL COMMENT 'API速率限制',
  `data_limit` int NULL DEFAULT NULL COMMENT '数据量限制',
  `status` enum('active','inactive','deprecated') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'active' COMMENT '状态',
  `total_calls` bigint NULL DEFAULT 0 COMMENT '总调用次数',
  `success_calls` bigint NULL DEFAULT 0 COMMENT '成功调用次数',
  `last_call_time` timestamp NULL DEFAULT NULL COMMENT '最后调用时间',
  `last_success_time` timestamp NULL DEFAULT NULL COMMENT '最后成功时间',
  `avg_response_time` decimal(10, 3) NULL DEFAULT NULL COMMENT '平均响应时间（秒）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `synced_at` timestamp NULL DEFAULT NULL COMMENT '最后同步时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_datasource_apicode`(`data_source_id` ASC, `api_code` ASC) USING BTREE,
  INDEX `idx_api_category`(`api_category` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_synced_at`(`synced_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 20 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'API接口管理表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_sync_tasks
-- ----------------------------
DROP TABLE IF EXISTS `api_sync_tasks`;
CREATE TABLE `api_sync_tasks`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `data_source_id` bigint NOT NULL COMMENT '数据源ID',
  `task_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务名称',
  `task_type` enum('full_sync','incremental_sync','api_discovery') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务类型',
  `status` enum('pending','running','completed','failed','cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'pending' COMMENT '任务状态',
  `started_at` timestamp NULL DEFAULT NULL COMMENT '开始时间',
  `completed_at` timestamp NULL DEFAULT NULL COMMENT '完成时间',
  `progress` int NULL DEFAULT 0 COMMENT '进度百分比',
  `total_apis` int NULL DEFAULT 0 COMMENT '总API数量',
  `new_apis` int NULL DEFAULT 0 COMMENT '新增API数量',
  `updated_apis` int NULL DEFAULT 0 COMMENT '更新API数量',
  `failed_apis` int NULL DEFAULT 0 COMMENT '失败API数量',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `log_data` json NULL COMMENT '日志数据',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_data_source`(`data_source_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_task_type`(`task_type` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'API同步任务表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for audit_opinions
-- ----------------------------
DROP TABLE IF EXISTS `audit_opinions`;
CREATE TABLE `audit_opinions`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ann_date` date NOT NULL,
  `end_date` date NOT NULL,
  `audit_result` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `audit_fees` float NULL DEFAULT NULL,
  `audit_agency` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `audit_sign` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `opinion_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_ts_code_end`(`ts_code` ASC, `end_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11032 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for backtest_results
-- ----------------------------
DROP TABLE IF EXISTS `backtest_results`;
CREATE TABLE `backtest_results`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `backtest_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '回测ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `strategy_id` bigint NULL DEFAULT NULL COMMENT '策略ID',
  `strategy_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '策略名称',
  `start_date` date NOT NULL COMMENT '回测开始日期',
  `end_date` date NOT NULL COMMENT '回测结束日期',
  `initial_capital` decimal(15, 2) NOT NULL COMMENT '初始资金',
  `final_capital` decimal(15, 2) NULL DEFAULT NULL COMMENT '最终资金',
  `parameters` json NULL COMMENT '回测参数',
  `stock_pool` json NULL COMMENT '股票池',
  `benchmark` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '000300.SH' COMMENT '基准指数',
  `total_return` decimal(10, 6) NULL DEFAULT NULL COMMENT '总收益率',
  `annualized_return` decimal(10, 6) NULL DEFAULT NULL COMMENT '年化收益率',
  `benchmark_return` decimal(10, 6) NULL DEFAULT NULL COMMENT '基准收益率',
  `alpha` decimal(10, 6) NULL DEFAULT NULL COMMENT 'Alpha',
  `beta` decimal(10, 6) NULL DEFAULT NULL COMMENT 'Beta',
  `sharpe_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '夏普比率',
  `sortino_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT 'Sortino比率',
  `max_drawdown` decimal(8, 4) NULL DEFAULT NULL COMMENT '最大回撤',
  `volatility` decimal(8, 4) NULL DEFAULT NULL COMMENT '波动率',
  `win_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '胜率',
  `profit_factor` decimal(8, 4) NULL DEFAULT NULL COMMENT '盈利因子',
  `total_trades` int NULL DEFAULT 0 COMMENT '总交易次数',
  `winning_trades` int NULL DEFAULT 0 COMMENT '盈利交易次数',
  `losing_trades` int NULL DEFAULT 0 COMMENT '亏损交易次数',
  `avg_win` decimal(10, 6) NULL DEFAULT NULL COMMENT '平均盈利',
  `avg_loss` decimal(10, 6) NULL DEFAULT NULL COMMENT '平均亏损',
  `largest_win` decimal(10, 6) NULL DEFAULT NULL COMMENT '最大盈利',
  `largest_loss` decimal(10, 6) NULL DEFAULT NULL COMMENT '最大亏损',
  `equity_curve` json NULL COMMENT '净值曲线数据',
  `trades` json NULL COMMENT '交易记录',
  `status` enum('pending','running','completed','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'pending' COMMENT '回测状态',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `completed_at` timestamp NULL DEFAULT NULL COMMENT '完成时间',
  `returns_distribution` json NULL,
  `monthly_returns` json NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `backtest_id`(`backtest_id` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_strategy_id`(`strategy_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_user_strategy`(`user_id` ASC, `strategy_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 23 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '回测结果表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for confidence_assessment_history
-- ----------------------------
DROP TABLE IF EXISTS `confidence_assessment_history`;
CREATE TABLE `confidence_assessment_history`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `decision_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '决策ID',
  `overall_confidence` float NOT NULL COMMENT '总体置信度',
  `logic_score` float NULL DEFAULT NULL COMMENT '逻辑合理性评分',
  `market_match_score` float NULL DEFAULT NULL COMMENT '市场环境匹配度',
  `risk_reward_score` float NULL DEFAULT NULL COMMENT '风险收益评分',
  `historical_accuracy` float NULL DEFAULT NULL COMMENT '历史准确率',
  `market_conditions` json NULL COMMENT '市场条件',
  `risk_factors` json NULL COMMENT '风险因素',
  `assessment_time` datetime NOT NULL COMMENT '评估时间',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_confidence_decision`(`decision_id` ASC) USING BTREE,
  INDEX `idx_confidence_time`(`assessment_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for daily_basic
-- ----------------------------
DROP TABLE IF EXISTS `daily_basic`;
CREATE TABLE `daily_basic`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `close` decimal(10, 4) NULL DEFAULT NULL COMMENT '当日收盘价',
  `turnover_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '换手率（%）',
  `turnover_rate_f` decimal(8, 4) NULL DEFAULT NULL COMMENT '换手率（自由流通股）',
  `volume_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '量比',
  `pe` decimal(10, 4) NULL DEFAULT NULL COMMENT '市盈率（总市值/净利润，亏损的PE为空）',
  `pe_ttm` decimal(10, 4) NULL DEFAULT NULL COMMENT '市盈率（TTM，亏损的PE为空）',
  `pb` decimal(10, 4) NULL DEFAULT NULL COMMENT '市净率（总市值/净资产）',
  `ps` decimal(10, 4) NULL DEFAULT NULL COMMENT '市销率',
  `ps_ttm` decimal(10, 4) NULL DEFAULT NULL COMMENT '市销率（TTM）',
  `dv_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '股息率（%）',
  `dv_ttm` decimal(8, 4) NULL DEFAULT NULL COMMENT '股息率（TTM）（%）',
  `total_share` decimal(20, 2) NULL DEFAULT NULL COMMENT '总股本（万股）',
  `float_share` decimal(20, 2) NULL DEFAULT NULL COMMENT '流通股本（万股）',
  `free_share` decimal(20, 2) NULL DEFAULT NULL COMMENT '自由流通股本（万）',
  `total_mv` decimal(20, 2) NULL DEFAULT NULL COMMENT '总市值（万元）',
  `circ_mv` decimal(20, 2) NULL DEFAULT NULL COMMENT '流通市值（万元）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`, `trade_date`) USING BTREE,
  UNIQUE INDEX `uk_ts_code_date`(`ts_code` ASC, `trade_date` ASC) USING BTREE,
  INDEX `idx_trade_date`(`trade_date` ASC) USING BTREE,
  INDEX `idx_ts_code`(`ts_code` ASC) USING BTREE,
  INDEX `idx_pe`(`pe` ASC) USING BTREE,
  INDEX `idx_pb`(`pb` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 220194 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '每日指标表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for daily_history
-- ----------------------------
DROP TABLE IF EXISTS `daily_history`;
CREATE TABLE `daily_history`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `open_price` decimal(10, 4) NULL DEFAULT NULL COMMENT '开盘价',
  `high_price` decimal(10, 4) NULL DEFAULT NULL COMMENT '最高价',
  `low_price` decimal(10, 4) NULL DEFAULT NULL COMMENT '最低价',
  `close_price` decimal(10, 4) NULL DEFAULT NULL COMMENT '收盘价',
  `pre_close` decimal(10, 4) NULL DEFAULT NULL COMMENT '昨收价',
  `change_amount` decimal(10, 4) NULL DEFAULT NULL COMMENT '涨跌额',
  `change_pct` decimal(8, 4) NULL DEFAULT NULL COMMENT '涨跌幅(%)',
  `volume` bigint NULL DEFAULT NULL COMMENT '成交量(手)',
  `amount` decimal(20, 2) NULL DEFAULT NULL COMMENT '成交额(千元)',
  `turnover_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '换手率(%)',
  `volume_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '量比',
  `pe` decimal(10, 4) NULL DEFAULT NULL COMMENT '市盈率',
  `pb` decimal(10, 4) NULL DEFAULT NULL COMMENT '市净率',
  `ps` decimal(10, 4) NULL DEFAULT NULL COMMENT '市销率',
  `pcf` decimal(10, 4) NULL DEFAULT NULL COMMENT '市现率',
  `market_cap` decimal(20, 2) NULL DEFAULT NULL COMMENT '总市值(万元)',
  `circ_mv` decimal(20, 2) NULL DEFAULT NULL COMMENT '流通市值(万元)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`, `trade_date`) USING BTREE,
  UNIQUE INDEX `uk_ts_code_date`(`ts_code` ASC, `trade_date` ASC) USING BTREE,
  INDEX `idx_trade_date`(`trade_date` ASC) USING BTREE,
  INDEX `idx_ts_code`(`ts_code` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4474985 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '每日历史行情数据表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for daily_quotes
-- ----------------------------
DROP TABLE IF EXISTS `daily_quotes`;
CREATE TABLE `daily_quotes`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'TS股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `open_price` decimal(10, 3) NULL DEFAULT NULL COMMENT '开盘价',
  `high_price` decimal(10, 3) NULL DEFAULT NULL COMMENT '最高价',
  `low_price` decimal(10, 3) NULL DEFAULT NULL COMMENT '最低价',
  `close_price` decimal(10, 3) NULL DEFAULT NULL COMMENT '收盘价',
  `pre_close` decimal(10, 3) NULL DEFAULT NULL COMMENT '昨收价',
  `change_amount` decimal(10, 3) NULL DEFAULT NULL COMMENT '涨跌额',
  `change_pct` decimal(8, 4) NULL DEFAULT NULL COMMENT '涨跌幅(%)',
  `volume` bigint NULL DEFAULT NULL COMMENT '成交量(手)',
  `amount` decimal(20, 2) NULL DEFAULT NULL COMMENT '成交额(千元)',
  `turnover_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '换手率(%)',
  `volume_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '量比',
  `pe` decimal(10, 4) NULL DEFAULT NULL COMMENT '市盈率',
  `pb` decimal(10, 4) NULL DEFAULT NULL COMMENT '市净率',
  `ps` decimal(10, 4) NULL DEFAULT NULL COMMENT '市销率',
  `pcf` decimal(10, 4) NULL DEFAULT NULL COMMENT '市现率',
  `market_cap` decimal(20, 2) NULL DEFAULT NULL COMMENT '总市值(万元)',
  `circ_mv` decimal(20, 2) NULL DEFAULT NULL COMMENT '流通市值(万元)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`, `trade_date`) USING BTREE,
  UNIQUE INDEX `uk_ts_code_date`(`ts_code` ASC, `trade_date` ASC) USING BTREE,
  INDEX `idx_ts_code`(`ts_code` ASC) USING BTREE,
  INDEX `idx_trade_date`(`trade_date` ASC) USING BTREE,
  INDEX `idx_change_pct`(`change_pct` ASC) USING BTREE,
  INDEX `idx_turnover_rate`(`turnover_rate` ASC) USING BTREE,
  INDEX `idx_market_cap`(`market_cap` ASC) USING BTREE,
  INDEX `idx_pe`(`pe` ASC) USING BTREE,
  INDEX `idx_pb`(`pb` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '日线行情数据表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for data_sources
-- ----------------------------
DROP TABLE IF EXISTS `data_sources`;
CREATE TABLE `data_sources`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据源名称',
  `type` enum('market_data','trading_data') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据源类型：market_data-行情数据源，trading_data-交易数据源',
  `provider` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据提供商（如tushare、同花顺等）',
  `status` enum('active','inactive','testing') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'inactive' COMMENT '状态：active-启用，inactive-禁用，testing-测试中',
  `api_key` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'API密钥（加密存储）',
  `api_secret` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'API密钥（加密存储）',
  `base_url` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '基础URL',
  `timeout` int NULL DEFAULT 30 COMMENT '超时时间（秒）',
  `rate_limit` int NULL DEFAULT 200 COMMENT '速率限制（每分钟请求数）',
  `config_params` json NULL COMMENT '其他配置参数',
  `total_calls` bigint NULL DEFAULT 0 COMMENT '总调用次数',
  `success_calls` bigint NULL DEFAULT 0 COMMENT '成功调用次数',
  `last_call_time` timestamp NULL DEFAULT NULL COMMENT '最后调用时间',
  `last_success_time` timestamp NULL DEFAULT NULL COMMENT '最后成功时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_type`(`type` ASC) USING BTREE,
  INDEX `idx_provider`(`provider` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '数据源配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for ensemble_model_mapping
-- ----------------------------
DROP TABLE IF EXISTS `ensemble_model_mapping`;
CREATE TABLE `ensemble_model_mapping`  (
  `mapping_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联唯一标识',
  `ensemble_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '组合ID',
  `model_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型ID',
  `weight` decimal(5, 4) NOT NULL DEFAULT 1.0000 COMMENT '权重(0.0000-1.0000)',
  `priority` int NULL DEFAULT 1 COMMENT '优先级(数字越小优先级越高)',
  `order_index` int NULL DEFAULT 0 COMMENT '排序索引',
  `enabled` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用此关联',
  `status` enum('active','inactive','error') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'active' COMMENT '关联状态',
  `contribution_score` decimal(5, 4) NULL DEFAULT 0.0000 COMMENT '贡献度评分',
  `usage_count` bigint NULL DEFAULT 0 COMMENT '使用次数',
  `last_used_at` timestamp NULL DEFAULT NULL COMMENT '最后使用时间',
  `config_json` json NULL COMMENT '关联配置(JSON格式)',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '创建者',
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`mapping_id`) USING BTREE,
  UNIQUE INDEX `uk_ensemble_model`(`ensemble_id` ASC, `model_id` ASC) USING BTREE,
  INDEX `idx_mapping_ensemble`(`ensemble_id` ASC) USING BTREE,
  INDEX `idx_mapping_model`(`model_id` ASC) USING BTREE,
  INDEX `idx_mapping_weight`(`weight` ASC) USING BTREE,
  INDEX `idx_mapping_priority`(`priority` ASC) USING BTREE,
  INDEX `idx_mapping_enabled`(`enabled` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '组合模型关联表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for financial_data
-- ----------------------------
DROP TABLE IF EXISTS `financial_data`;
CREATE TABLE `financial_data`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `stock_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `report_date` date NOT NULL COMMENT '报告期',
  `report_type` enum('Q1','Q2','Q3','annual') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '报告类型',
  `revenue` decimal(20, 2) NULL DEFAULT NULL COMMENT '营业收入',
  `net_profit` decimal(20, 2) NULL DEFAULT NULL COMMENT '净利润',
  `total_assets` decimal(20, 2) NULL DEFAULT NULL COMMENT '总资产',
  `total_equity` decimal(20, 2) NULL DEFAULT NULL COMMENT '股东权益',
  `roe` decimal(8, 4) NULL DEFAULT NULL COMMENT '净资产收益率(%)',
  `roa` decimal(8, 4) NULL DEFAULT NULL COMMENT '总资产收益率(%)',
  `gross_margin` decimal(8, 4) NULL DEFAULT NULL COMMENT '毛利率(%)',
  `net_margin` decimal(8, 4) NULL DEFAULT NULL COMMENT '净利率(%)',
  `debt_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '资产负债率(%)',
  `current_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '流动比率',
  `quick_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '速动比率',
  `eps` decimal(10, 4) NULL DEFAULT NULL COMMENT '每股收益',
  `bvps` decimal(10, 4) NULL DEFAULT NULL COMMENT '每股净资产',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_stock_report`(`stock_code` ASC, `report_date` ASC, `report_type` ASC) USING BTREE,
  INDEX `idx_stock_code`(`stock_code` ASC) USING BTREE,
  INDEX `idx_report_date`(`report_date` ASC) USING BTREE,
  INDEX `idx_report_type`(`report_type` ASC) USING BTREE,
  INDEX `idx_roe`(`roe` ASC) USING BTREE,
  INDEX `idx_eps`(`eps` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '财务数据表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for financial_indicators
-- ----------------------------
DROP TABLE IF EXISTS `financial_indicators`;
CREATE TABLE `financial_indicators`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'TS股票代码',
  `ann_date` date NOT NULL COMMENT '公告日期',
  `end_date` date NOT NULL COMMENT '报告期',
  `report_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '报告类型(1季报/中报/3季报/年报)',
  `roe` decimal(8, 4) NULL DEFAULT NULL COMMENT '净资产收益率(%)',
  `roa` decimal(8, 4) NULL DEFAULT NULL COMMENT '总资产收益率(%)',
  `roic` decimal(8, 4) NULL DEFAULT NULL COMMENT '投入资本回报率(%)',
  `gross_margin` decimal(8, 4) NULL DEFAULT NULL COMMENT '毛利率(%)',
  `net_margin` decimal(8, 4) NULL DEFAULT NULL COMMENT '净利率(%)',
  `revenue_growth` decimal(8, 4) NULL DEFAULT NULL COMMENT '营收增长率(%)',
  `profit_growth` decimal(8, 4) NULL DEFAULT NULL COMMENT '净利润增长率(%)',
  `eps_growth` decimal(8, 4) NULL DEFAULT NULL COMMENT 'EPS增长率(%)',
  `debt_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '资产负债率(%)',
  `current_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '流动比率',
  `quick_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '速动比率',
  `pe_ttm` decimal(10, 4) NULL DEFAULT NULL COMMENT '市盈率TTM',
  `pb_mrq` decimal(10, 4) NULL DEFAULT NULL COMMENT '市净率MRQ',
  `ps_ttm` decimal(10, 4) NULL DEFAULT NULL COMMENT '市销率TTM',
  `peg` decimal(10, 4) NULL DEFAULT NULL COMMENT 'PEG比率',
  `eps` decimal(10, 4) NULL DEFAULT NULL COMMENT '每股收益',
  `bps` decimal(10, 4) NULL DEFAULT NULL COMMENT '每股净资产',
  `revenue_per_share` decimal(10, 4) NULL DEFAULT NULL COMMENT '每股营收',
  `cash_per_share` decimal(10, 4) NULL DEFAULT NULL COMMENT '每股现金流',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`, `end_date`) USING BTREE,
  UNIQUE INDEX `uk_ts_code_end_date`(`ts_code` ASC, `end_date` ASC) USING BTREE,
  INDEX `idx_ts_code`(`ts_code` ASC) USING BTREE,
  INDEX `idx_ann_date`(`ann_date` ASC) USING BTREE,
  INDEX `idx_end_date`(`end_date` ASC) USING BTREE,
  INDEX `idx_roe`(`roe` ASC) USING BTREE,
  INDEX `idx_roa`(`roa` ASC) USING BTREE,
  INDEX `idx_revenue_growth`(`revenue_growth` ASC) USING BTREE,
  INDEX `idx_profit_growth`(`profit_growth` ASC) USING BTREE,
  INDEX `idx_pe_ttm`(`pe_ttm` ASC) USING BTREE,
  INDEX `idx_pb_mrq`(`pb_mrq` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 61492 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '财务指标数据表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for industry_classification
-- ----------------------------
DROP TABLE IF EXISTS `industry_classification`;
CREATE TABLE `industry_classification`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `industry_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `industry_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` int NULL DEFAULT NULL,
  `classification_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `in_date` date NULL DEFAULT NULL,
  `out_date` date NULL DEFAULT NULL,
  `is_new` tinyint(1) NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `updated_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_ts_code_type`(`ts_code` ASC, `classification_type` ASC) USING BTREE,
  INDEX `idx_industry_code`(`industry_code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 69148 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for instruction_parse_history
-- ----------------------------
DROP TABLE IF EXISTS `instruction_parse_history`;
CREATE TABLE `instruction_parse_history`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话ID',
  `original_instruction` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '原始指令',
  `parsed_instruction` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '解析后指令',
  `instruction_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '指令类型',
  `parse_confidence` float NULL DEFAULT NULL COMMENT '解析置信度',
  `ambiguity_score` float NULL DEFAULT NULL COMMENT '模糊度评分',
  `conflicts` json NULL COMMENT '冲突列表',
  `suggestions` json NULL COMMENT '建议列表',
  `parse_time` datetime NOT NULL COMMENT '解析时间',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_parse_session_time`(`session_id` ASC, `parse_time` ASC) USING BTREE,
  INDEX `idx_parse_type`(`instruction_type` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for limit_prices
-- ----------------------------
DROP TABLE IF EXISTS `limit_prices`;
CREATE TABLE `limit_prices`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `trade_date` date NOT NULL,
  `up_limit` float NULL DEFAULT NULL,
  `down_limit` float NULL DEFAULT NULL,
  `close` float NULL DEFAULT NULL,
  `pct_chg` float NULL DEFAULT NULL,
  `is_limit_up` tinyint(1) NULL DEFAULT NULL,
  `is_limit_down` tinyint(1) NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_ts_code_date`(`ts_code` ASC, `trade_date` ASC) USING BTREE,
  INDEX `idx_trade_date`(`trade_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 249601 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '涨跌停价格' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for llm_decisions
-- ----------------------------
DROP TABLE IF EXISTS `llm_decisions`;
CREATE TABLE `llm_decisions`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `strategy_id` bigint NULL DEFAULT NULL COMMENT '策略ID',
  `stock_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `decision_type` enum('buy','sell','hold','analysis') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '决策类型',
  `prompt_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '输入提示词',
  `llm_response` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'LLM响应内容',
  `confidence_score` decimal(5, 4) NULL DEFAULT NULL COMMENT '置信度分数(0-1)',
  `reasoning` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '决策推理过程',
  `market_data` json NULL COMMENT '决策时的市场数据',
  `decision_result` json NULL COMMENT '决策结果详情',
  `execution_status` enum('pending','executed','rejected','expired') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'pending' COMMENT '执行状态',
  `model_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '使用的模型名称',
  `model_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '模型版本',
  `processing_time_ms` int NULL DEFAULT NULL COMMENT '处理时间(毫秒)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_strategy_id`(`strategy_id` ASC) USING BTREE,
  INDEX `idx_stock_code`(`stock_code` ASC) USING BTREE,
  INDEX `idx_decision_type`(`decision_type` ASC) USING BTREE,
  INDEX `idx_execution_status`(`execution_status` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_user_stock_time`(`user_id` ASC, `stock_code` ASC, `created_at` ASC) USING BTREE,
  INDEX `idx_confidence_score`(`confidence_score` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'LLM决策记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for model_api_keys
-- ----------------------------
DROP TABLE IF EXISTS `model_api_keys`;
CREATE TABLE `model_api_keys`  (
  `key_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密钥唯一标识',
  `model_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型ID',
  `key_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密钥名称',
  `encrypted_key` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '加密后的API密钥',
  `key_hash` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密钥哈希值(用于验证)',
  `encryption_method` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'AES-256-GCM' COMMENT '加密方法',
  `rate_limit_per_minute` int NULL DEFAULT NULL COMMENT '每分钟请求限制',
  `rate_limit_per_day` int NULL DEFAULT NULL COMMENT '每日请求限制',
  `monthly_quota` bigint NULL DEFAULT NULL COMMENT '月度配额',
  `used_quota` bigint NULL DEFAULT 0 COMMENT '已使用配额',
  `status` enum('active','inactive','expired','revoked') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT '密钥状态',
  `expires_at` timestamp NULL DEFAULT NULL COMMENT '过期时间',
  `last_used_at` timestamp NULL DEFAULT NULL COMMENT '最后使用时间',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '创建者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`key_id`) USING BTREE,
  UNIQUE INDEX `uk_api_keys_model_name`(`model_id` ASC, `key_name` ASC) USING BTREE,
  INDEX `idx_api_keys_model`(`model_id` ASC) USING BTREE,
  INDEX `idx_api_keys_status`(`status` ASC) USING BTREE,
  INDEX `idx_api_keys_expires`(`expires_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '模型API密钥表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for model_ensembles
-- ----------------------------
DROP TABLE IF EXISTS `model_ensembles`;
CREATE TABLE `model_ensembles`  (
  `ensemble_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '组合唯一标识',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '组合名称',
  `display_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '显示名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '组合描述',
  `weight_strategy` enum('equal_weight','accuracy_weight','manual_weight','dynamic_weight','performance_weight') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'equal_weight' COMMENT '权重策略',
  `voting_method` enum('majority','weighted','confidence','threshold') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'weighted' COMMENT '投票方法',
  `confidence_threshold` decimal(3, 2) NULL DEFAULT 0.50 COMMENT '置信度阈值',
  `overall_accuracy` decimal(5, 4) NULL DEFAULT 0.0000 COMMENT '综合准确率',
  `model_count` int NULL DEFAULT 0 COMMENT '包含模型数量',
  `active_model_count` int NULL DEFAULT 0 COMMENT '活跃模型数量',
  `avg_response_time` int NULL DEFAULT 0 COMMENT '平均响应时间(毫秒)',
  `status` enum('active','inactive','configuring','error') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'inactive' COMMENT '组合状态',
  `enabled` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否启用',
  `health_status` enum('healthy','warning','error','unknown') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'unknown' COMMENT '健康状态',
  `total_requests` bigint NULL DEFAULT 0 COMMENT '总请求次数',
  `success_requests` bigint NULL DEFAULT 0 COMMENT '成功请求次数',
  `last_used_at` timestamp NULL DEFAULT NULL COMMENT '最后使用时间',
  `config_json` json NULL COMMENT '组合配置(JSON格式)',
  `tags` json NULL COMMENT '标签数组',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '创建者',
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`ensemble_id`) USING BTREE,
  UNIQUE INDEX `uk_ensembles_name`(`name` ASC) USING BTREE,
  INDEX `idx_ensembles_strategy`(`weight_strategy` ASC) USING BTREE,
  INDEX `idx_ensembles_status`(`status` ASC) USING BTREE,
  INDEX `idx_ensembles_enabled`(`enabled` ASC) USING BTREE,
  INDEX `idx_ensembles_accuracy`(`overall_accuracy` ASC) USING BTREE,
  INDEX `idx_ensembles_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '模型组合表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for model_fusion_history
-- ----------------------------
DROP TABLE IF EXISTS `model_fusion_history`;
CREATE TABLE `model_fusion_history`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `fusion_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '融合ID',
  `decision_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '决策ID',
  `model_votes` json NOT NULL COMMENT '模型投票结果',
  `consensus_score` float NULL DEFAULT NULL COMMENT '共识度评分',
  `disagreement_factors` json NULL COMMENT '分歧因素',
  `fusion_method` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '融合方法',
  `final_weights` json NULL COMMENT '最终权重',
  `fusion_time` datetime NOT NULL COMMENT '融合时间',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `fusion_id`(`fusion_id` ASC) USING BTREE,
  INDEX `idx_fusion_method`(`fusion_method` ASC) USING BTREE,
  INDEX `idx_fusion_time`(`fusion_time` ASC) USING BTREE,
  INDEX `idx_fusion_decision`(`decision_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for model_metrics
-- ----------------------------
DROP TABLE IF EXISTS `model_metrics`;
CREATE TABLE `model_metrics`  (
  `metric_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '指标记录唯一标识',
  `model_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型ID',
  `ensemble_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '组合ID(如果是组合指标)',
  `metric_date` date NOT NULL COMMENT '指标日期',
  `metric_hour` tinyint NULL DEFAULT NULL COMMENT '指标小时(0-23,用于小时级统计)',
  `time_period` enum('hourly','daily','weekly','monthly') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'daily' COMMENT '时间周期',
  `accuracy_rate` decimal(5, 4) NULL DEFAULT 0.0000 COMMENT '准确率',
  `avg_response_time_ms` int NULL DEFAULT 0 COMMENT '平均响应时间(毫秒)',
  `success_rate` decimal(5, 4) NULL DEFAULT 0.0000 COMMENT '成功率',
  `error_rate` decimal(5, 4) NULL DEFAULT 0.0000 COMMENT '错误率',
  `total_requests` bigint NULL DEFAULT 0 COMMENT '总请求次数',
  `successful_requests` bigint NULL DEFAULT 0 COMMENT '成功请求次数',
  `failed_requests` bigint NULL DEFAULT 0 COMMENT '失败请求次数',
  `total_tokens_used` bigint NULL DEFAULT 0 COMMENT '总使用token数',
  `response_time_p50` int NULL DEFAULT NULL COMMENT '响应时间50分位数',
  `response_time_p90` int NULL DEFAULT NULL COMMENT '响应时间90分位数',
  `response_time_p95` int NULL DEFAULT NULL COMMENT '响应时间95分位数',
  `response_time_p99` int NULL DEFAULT NULL COMMENT '响应时间99分位数',
  `estimated_cost` decimal(10, 4) NULL DEFAULT 0.0000 COMMENT '预估成本',
  `cost_per_request` decimal(8, 6) NULL DEFAULT 0.000000 COMMENT '每请求成本',
  `confidence_score` decimal(5, 4) NULL DEFAULT NULL COMMENT '置信度得分',
  `consistency_score` decimal(5, 4) NULL DEFAULT NULL COMMENT '一致性得分',
  `relevance_score` decimal(5, 4) NULL DEFAULT NULL COMMENT '相关性得分',
  `custom_metrics` json NULL COMMENT '自定义指标(JSON格式)',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`metric_id`) USING BTREE,
  UNIQUE INDEX `uk_metrics_model_date_period`(`model_id` ASC, `metric_date` ASC, `time_period` ASC, `metric_hour` ASC) USING BTREE,
  INDEX `idx_metrics_model`(`model_id` ASC) USING BTREE,
  INDEX `idx_metrics_ensemble`(`ensemble_id` ASC) USING BTREE,
  INDEX `idx_metrics_date`(`metric_date` ASC) USING BTREE,
  INDEX `idx_metrics_period`(`time_period` ASC) USING BTREE,
  INDEX `idx_metrics_accuracy`(`accuracy_rate` ASC) USING BTREE,
  INDEX `idx_metrics_response_time`(`avg_response_time_ms` ASC) USING BTREE,
  INDEX `idx_metrics_success_rate`(`success_rate` ASC) USING BTREE,
  INDEX `idx_metrics_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '模型性能指标表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for model_performance_metrics
-- ----------------------------
DROP TABLE IF EXISTS `model_performance_metrics`;
CREATE TABLE `model_performance_metrics`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `model_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型ID',
  `metric_date` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '指标日期',
  `total_decisions` int NULL DEFAULT NULL COMMENT '总决策数',
  `correct_decisions` int NULL DEFAULT NULL COMMENT '正确决策数',
  `accuracy_rate` float NULL DEFAULT NULL COMMENT '准确率',
  `avg_confidence` float NULL DEFAULT NULL COMMENT '平均置信度',
  `avg_return` float NULL DEFAULT NULL COMMENT '平均收益率',
  `sharpe_ratio` float NULL DEFAULT NULL COMMENT '夏普比率',
  `max_drawdown` float NULL DEFAULT NULL COMMENT '最大回撤',
  `win_rate` float NULL DEFAULT NULL COMMENT '胜率',
  `profit_factor` float NULL DEFAULT NULL COMMENT '盈利因子',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_model_perf_model_date`(`model_id` ASC, `metric_date` ASC) USING BTREE,
  INDEX `idx_model_perf_date`(`metric_date` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for model_test_records
-- ----------------------------
DROP TABLE IF EXISTS `model_test_records`;
CREATE TABLE `model_test_records`  (
  `test_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '测试记录唯一标识',
  `model_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型ID',
  `ensemble_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '组合ID(如果是组合测试)',
  `test_type` enum('unit','integration','performance','accuracy','stress') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '测试类型',
  `test_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '测试名称',
  `test_description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '测试描述',
  `input_data` json NOT NULL COMMENT '测试输入数据(JSON格式)',
  `expected_output` json NULL COMMENT '期望输出(JSON格式)',
  `actual_output` json NULL COMMENT '实际输出(JSON格式)',
  `response_time_ms` int NULL DEFAULT NULL COMMENT '响应时间(毫秒)',
  `token_count` int NULL DEFAULT NULL COMMENT 'Token使用数量',
  `success` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否成功(0:失败,1:成功)',
  `accuracy_score` decimal(5, 4) NULL DEFAULT NULL COMMENT '准确率得分',
  `error_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '错误代码',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `error_details` json NULL COMMENT '错误详情(JSON格式)',
  `test_environment` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '测试环境',
  `test_version` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '测试版本',
  `batch_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '批次ID(用于批量测试)',
  `tested_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '测试者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`test_id`) USING BTREE,
  INDEX `idx_test_model`(`model_id` ASC) USING BTREE,
  INDEX `idx_test_ensemble`(`ensemble_id` ASC) USING BTREE,
  INDEX `idx_test_type`(`test_type` ASC) USING BTREE,
  INDEX `idx_test_success`(`success` ASC) USING BTREE,
  INDEX `idx_test_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_test_batch`(`batch_id` ASC) USING BTREE,
  INDEX `idx_test_response_time`(`response_time_ms` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '模型测试记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for model_usage_logs
-- ----------------------------
DROP TABLE IF EXISTS `model_usage_logs`;
CREATE TABLE `model_usage_logs`  (
  `log_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志唯一标识',
  `model_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型ID',
  `ensemble_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '组合ID',
  `request_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '请求ID',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户ID',
  `session_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '会话ID',
  `input_tokens` int NULL DEFAULT 0 COMMENT '输入token数',
  `output_tokens` int NULL DEFAULT 0 COMMENT '输出token数',
  `total_tokens` int NULL DEFAULT 0 COMMENT '总token数',
  `response_time_ms` int NULL DEFAULT NULL COMMENT '响应时间(毫秒)',
  `success` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否成功',
  `error_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '错误代码',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `estimated_cost` decimal(8, 6) NULL DEFAULT 0.000000 COMMENT '预估成本',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`log_id`) USING BTREE,
  INDEX `idx_usage_logs_model`(`model_id` ASC) USING BTREE,
  INDEX `idx_usage_logs_ensemble`(`ensemble_id` ASC) USING BTREE,
  INDEX `idx_usage_logs_user`(`user_id` ASC) USING BTREE,
  INDEX `idx_usage_logs_success`(`success` ASC) USING BTREE,
  INDEX `idx_usage_logs_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_usage_logs_request`(`request_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '模型使用日志表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for money_flow
-- ----------------------------
DROP TABLE IF EXISTS `money_flow`;
CREATE TABLE `money_flow`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'TS股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `main_net_inflow` decimal(20, 2) NULL DEFAULT NULL COMMENT '主力净流入(万元)',
  `main_net_inflow_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '主力净流入率(%)',
  `super_net_inflow` decimal(20, 2) NULL DEFAULT NULL COMMENT '超大单净流入(万元)',
  `super_net_inflow_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '超大单净流入率(%)',
  `large_net_inflow` decimal(20, 2) NULL DEFAULT NULL COMMENT '大单净流入(万元)',
  `large_net_inflow_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '大单净流入率(%)',
  `medium_net_inflow` decimal(20, 2) NULL DEFAULT NULL COMMENT '中单净流入(万元)',
  `medium_net_inflow_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '中单净流入率(%)',
  `small_net_inflow` decimal(20, 2) NULL DEFAULT NULL COMMENT '小单净流入(万元)',
  `small_net_inflow_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '小单净流入率(%)',
  `north_net_inflow` decimal(20, 2) NULL DEFAULT NULL COMMENT '北向资金净流入(万元)',
  `north_net_inflow_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '北向资金净流入率(%)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`, `trade_date`) USING BTREE,
  UNIQUE INDEX `uk_ts_code_date`(`ts_code` ASC, `trade_date` ASC) USING BTREE,
  INDEX `idx_ts_code`(`ts_code` ASC) USING BTREE,
  INDEX `idx_trade_date`(`trade_date` ASC) USING BTREE,
  INDEX `idx_main_net_inflow`(`main_net_inflow` ASC) USING BTREE,
  INDEX `idx_main_net_inflow_rate`(`main_net_inflow_rate` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '资金流向数据表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for orders
-- ----------------------------
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'è®¢å•å·',
  `user_id` bigint NOT NULL COMMENT 'ç”¨æˆ·ID',
  `stock_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'è‚¡ç¥¨ä»£ç ',
  `stock_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'è‚¡ç¥¨åç§°',
  `side` enum('buy','sell') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'ä¹°å–æ–¹å‘',
  `order_type` enum('market','limit','stop','stop_limit') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'limit' COMMENT 'è®¢å•ç±»åž‹',
  `quantity` int NOT NULL COMMENT 'å§”æ‰˜æ•°é‡',
  `price` decimal(10, 3) NOT NULL DEFAULT 0.000 COMMENT 'å§”æ‰˜ä»·æ ¼',
  `stop_price` decimal(10, 3) NULL DEFAULT 0.000 COMMENT 'æ­¢æŸä»·æ ¼',
  `filled_quantity` int NOT NULL DEFAULT 0 COMMENT 'å·²æˆäº¤æ•°é‡',
  `avg_price` decimal(10, 3) NOT NULL DEFAULT 0.000 COMMENT 'æˆäº¤å‡ä»·',
  `status` enum('pending','partial','filled','cancelled','rejected') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'pending' COMMENT 'è®¢å•çŠ¶æ€',
  `time_in_force` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'day' COMMENT 'æœ‰æ•ˆæœŸ(day/gtc/ioc/fok)',
  `commission` decimal(10, 2) NULL DEFAULT 0.00 COMMENT 'æ‰‹ç»­è´¹',
  `notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT 'å¤‡æ³¨',
  `strategy_id` bigint NULL DEFAULT NULL COMMENT 'ç­–ç•¥ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'åˆ›å»ºæ—¶é—´',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'æ›´æ–°æ—¶é—´',
  `filled_at` timestamp NULL DEFAULT NULL COMMENT 'æˆäº¤æ—¶é—´',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `order_id`(`order_id` ASC) USING BTREE,
  INDEX `idx_order_id`(`order_id` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_stock_code`(`stock_code` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_side`(`side` ASC) USING BTREE,
  INDEX `idx_user_status`(`user_id` ASC, `status` ASC) USING BTREE,
  INDEX `idx_user_stock`(`user_id` ASC, `stock_code` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `strategy_id`(`strategy_id` ASC) USING BTREE,
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`strategy_id`) REFERENCES `trading_strategies` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'è®¢å•è¡¨' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for portfolios
-- ----------------------------
DROP TABLE IF EXISTS `portfolios`;
CREATE TABLE `portfolios`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `portfolio_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '组合名称',
  `stock_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `quantity` bigint NOT NULL DEFAULT 0 COMMENT '持仓数量',
  `avg_cost` decimal(10, 3) NOT NULL DEFAULT 0.000 COMMENT '平均成本',
  `current_price` decimal(10, 3) NULL DEFAULT NULL COMMENT '当前价格',
  `market_value` decimal(15, 2) NULL DEFAULT NULL COMMENT '市值',
  `unrealized_pnl` decimal(15, 2) NULL DEFAULT NULL COMMENT '浮动盈亏',
  `unrealized_pnl_pct` decimal(8, 4) NULL DEFAULT NULL COMMENT '浮动盈亏比例(%)',
  `weight` decimal(8, 4) NULL DEFAULT NULL COMMENT '组合权重(%)',
  `last_updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_portfolio_stock`(`user_id` ASC, `portfolio_name` ASC, `stock_code` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_stock_code`(`stock_code` ASC) USING BTREE,
  INDEX `idx_portfolio_name`(`portfolio_name` ASC) USING BTREE,
  INDEX `idx_user_portfolio`(`user_id` ASC, `portfolio_name` ASC) USING BTREE,
  INDEX `idx_updated_at`(`last_updated` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '资产组合表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for positions
-- ----------------------------
DROP TABLE IF EXISTS `positions`;
CREATE TABLE `positions`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT 'ç”¨æˆ·ID',
  `stock_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'è‚¡ç¥¨ä»£ç ',
  `stock_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'è‚¡ç¥¨åç§°',
  `quantity` int NOT NULL DEFAULT 0 COMMENT 'æŒä»“æ•°é‡',
  `available_quantity` int NOT NULL DEFAULT 0 COMMENT 'å¯ç”¨æ•°é‡',
  `frozen_quantity` int NOT NULL DEFAULT 0 COMMENT 'å†»ç»“æ•°é‡',
  `avg_cost` decimal(10, 3) NOT NULL COMMENT 'å¹³å‡æˆæœ¬',
  `last_price` decimal(10, 3) NOT NULL DEFAULT 0.000 COMMENT 'æœ€æ–°ä»·æ ¼',
  `market_value` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'å¸‚å€¼',
  `cost_basis` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'æˆæœ¬åŸºç¡€',
  `profit_loss` decimal(20, 2) NOT NULL DEFAULT 0.00 COMMENT 'æµ®åŠ¨ç›ˆäº',
  `profit_loss_pct` decimal(10, 4) NOT NULL DEFAULT 0.0000 COMMENT 'ç›ˆäºæ¯”ä¾‹(%)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'å»ºä»“æ—¶é—´',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'æ›´æ–°æ—¶é—´',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_stock`(`user_id` ASC, `stock_code` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_stock_code`(`stock_code` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE,
  CONSTRAINT `positions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'æŒä»“è¡¨' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for risk_rules
-- ----------------------------
DROP TABLE IF EXISTS `risk_rules`;
CREATE TABLE `risk_rules`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NULL DEFAULT NULL COMMENT '用户ID(NULL表示全局规则)',
  `rule_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '规则名称',
  `rule_type` enum('position_limit','loss_limit','concentration','volatility','custom') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '规则类型',
  `rule_config` json NOT NULL COMMENT '规则配置(JSON格式)',
  `threshold_value` decimal(15, 4) NULL DEFAULT NULL COMMENT '阈值',
  `action` enum('alert','block','force_close') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'alert' COMMENT '触发动作',
  `priority` int NULL DEFAULT 1 COMMENT '优先级(1-10)',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'active' COMMENT '规则状态',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '规则描述',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_rule_type`(`rule_type` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_priority`(`priority` ASC) USING BTREE,
  INDEX `idx_user_type_status`(`user_id` ASC, `rule_type` ASC, `status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '风控规则表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for screening_history
-- ----------------------------
DROP TABLE IF EXISTS `screening_history`;
CREATE TABLE `screening_history`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `strategy_id` bigint NOT NULL COMMENT '策略ID',
  `result_id` bigint NOT NULL COMMENT '结果ID',
  `screening_date` date NOT NULL COMMENT '筛选日期',
  `selected_stocks` json NULL COMMENT '选中的股票列表',
  `performance_data` json NULL COMMENT '后续表现数据',
  `hit_rate` decimal(5, 2) NULL DEFAULT NULL COMMENT '命中率(%)',
  `avg_return_1d` decimal(8, 4) NULL DEFAULT NULL COMMENT '1日平均收益率(%)',
  `avg_return_5d` decimal(8, 4) NULL DEFAULT NULL COMMENT '5日平均收益率(%)',
  `avg_return_10d` decimal(8, 4) NULL DEFAULT NULL COMMENT '10日平均收益率(%)',
  `max_drawdown` decimal(8, 4) NULL DEFAULT NULL COMMENT '最大回撤(%)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_strategy_id`(`strategy_id` ASC) USING BTREE,
  INDEX `idx_result_id`(`result_id` ASC) USING BTREE,
  INDEX `idx_screening_date`(`screening_date` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '选股历史表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for screening_results
-- ----------------------------
DROP TABLE IF EXISTS `screening_results`;
CREATE TABLE `screening_results`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `task_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务ID',
  `strategy_id` bigint NOT NULL COMMENT '策略ID',
  `user_id` bigint NULL DEFAULT NULL COMMENT '用户ID',
  `screening_date` date NOT NULL COMMENT '筛选日期',
  `total_stocks` int NULL DEFAULT 0 COMMENT '总股票数',
  `filtered_stocks` int NULL DEFAULT 0 COMMENT '筛选后股票数',
  `result_data` json NULL COMMENT '筛选结果数据',
  `summary_stats` json NULL COMMENT '汇总统计信息',
  `execution_time` int NULL DEFAULT NULL COMMENT '执行时间(毫秒)',
  `status` enum('pending','running','completed','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'pending' COMMENT '执行状态',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_task_id`(`task_id` ASC) USING BTREE,
  INDEX `idx_strategy_id`(`strategy_id` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_screening_date`(`screening_date` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 156 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '选股结果表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for screening_strategies
-- ----------------------------
DROP TABLE IF EXISTS `screening_strategies`;
CREATE TABLE `screening_strategies`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `strategy_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '策略名称',
  `strategy_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '策略代码',
  `strategy_type` enum('fundamental','technical','mixed','custom') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'mixed' COMMENT '策略类型',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '策略描述',
  `config` json NULL COMMENT '策略配置参数',
  `conditions` json NULL COMMENT '筛选条件',
  `sort_rules` json NULL COMMENT '排序规则',
  `is_system` tinyint(1) NULL DEFAULT 0 COMMENT '是否系统预设策略',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '是否启用',
  `creator_id` bigint NULL DEFAULT NULL COMMENT '创建者ID',
  `usage_count` int NULL DEFAULT 0 COMMENT '使用次数',
  `success_rate` decimal(5, 2) NULL DEFAULT NULL COMMENT '成功率(%)',
  `avg_return` decimal(8, 4) NULL DEFAULT NULL COMMENT '平均收益率(%)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_strategy_code`(`strategy_code` ASC) USING BTREE,
  INDEX `idx_strategy_type`(`strategy_type` ASC) USING BTREE,
  INDEX `idx_creator_id`(`creator_id` ASC) USING BTREE,
  INDEX `idx_is_system`(`is_system` ASC) USING BTREE,
  INDEX `idx_is_active`(`is_active` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '选股策略配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for stock_basic
-- ----------------------------
DROP TABLE IF EXISTS `stock_basic`;
CREATE TABLE `stock_basic`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'TS股票代码',
  `symbol` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票名称',
  `area` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '地域',
  `industry` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '所属行业',
  `fullname` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '股票全称',
  `enname` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '英文全称',
  `cnspell` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '拼音缩写',
  `market` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '市场类型',
  `exchange` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '交易所代码',
  `curr_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '交易货币',
  `list_status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '上市状态',
  `list_date` date NULL DEFAULT NULL COMMENT '上市日期',
  `delist_date` date NULL DEFAULT NULL COMMENT '退市日期',
  `is_hs` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '是否沪深港通标的',
  `act_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '实控人名称',
  `act_ent_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '实控人企业性质',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `data_source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'tushare' COMMENT '数据来源',
  `sync_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'active' COMMENT '同步状态',
  `stock_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci GENERATED ALWAYS AS (`symbol`) VIRTUAL COMMENT '股票代码（兼容字段）' NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_ts_code`(`ts_code` ASC) USING BTREE,
  UNIQUE INDEX `uk_stock_code`(`stock_code` ASC) USING BTREE,
  INDEX `idx_symbol`(`symbol` ASC) USING BTREE,
  INDEX `idx_name`(`name` ASC) USING BTREE,
  INDEX `idx_industry`(`industry` ASC) USING BTREE,
  INDEX `idx_market`(`market` ASC) USING BTREE,
  INDEX `idx_exchange`(`exchange` ASC) USING BTREE,
  INDEX `idx_list_status`(`list_status` ASC) USING BTREE,
  INDEX `idx_list_date`(`list_date` ASC) USING BTREE,
  INDEX `idx_is_hs`(`is_hs` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 52173 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '股票基础信息表 (Tushare数据源)' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for stock_quotes
-- ----------------------------
DROP TABLE IF EXISTS `stock_quotes`;
CREATE TABLE `stock_quotes`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `stock_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `open_price` decimal(10, 3) NOT NULL COMMENT '开盘价',
  `high_price` decimal(10, 3) NOT NULL COMMENT '最高价',
  `low_price` decimal(10, 3) NOT NULL COMMENT '最低价',
  `close_price` decimal(10, 3) NOT NULL COMMENT '收盘价',
  `pre_close` decimal(10, 3) NULL DEFAULT NULL COMMENT '前收盘价',
  `change_amount` decimal(10, 3) NULL DEFAULT NULL COMMENT '涨跌额',
  `change_pct` decimal(8, 4) NULL DEFAULT NULL COMMENT '涨跌幅(%)',
  `volume` bigint NULL DEFAULT NULL COMMENT '成交量(股)',
  `amount` decimal(20, 2) NULL DEFAULT NULL COMMENT '成交额(元)',
  `turnover_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '换手率(%)',
  `pe_ratio` decimal(10, 4) NULL DEFAULT NULL COMMENT '市盈率',
  `pb_ratio` decimal(10, 4) NULL DEFAULT NULL COMMENT '市净率',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_stock_date`(`stock_code` ASC, `trade_date` ASC) USING BTREE,
  INDEX `idx_stock_code`(`stock_code` ASC) USING BTREE,
  INDEX `idx_trade_date`(`trade_date` ASC) USING BTREE,
  INDEX `idx_close_price`(`close_price` ASC) USING BTREE,
  INDEX `idx_volume`(`volume` ASC) USING BTREE,
  INDEX `idx_change_pct`(`change_pct` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '股票行情数据表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for strategy_templates
-- ----------------------------
DROP TABLE IF EXISTS `strategy_templates`;
CREATE TABLE `strategy_templates`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `template_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模板名称',
  `display_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '显示名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '模板描述',
  `category` enum('trend_following','mean_reversion','momentum','arbitrage','multi_factor','volatility','custom') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '策略分类',
  `risk_level` enum('low','medium','high') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'medium' COMMENT '风险等级',
  `parameter_schema` json NULL COMMENT '参数结构定义',
  `default_parameters` json NULL COMMENT '默认参数值',
  `min_capital` decimal(15, 2) NULL DEFAULT 100000.00 COMMENT '最小资金要求',
  `supported_markets` json NULL COMMENT '支持的市场',
  `indicators` json NULL COMMENT '使用的技术指标',
  `code_template` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '代码模板',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '是否启用',
  `sort_order` int NULL DEFAULT 0 COMMENT '排序',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_template_name`(`template_name` ASC) USING BTREE,
  INDEX `idx_category`(`category` ASC) USING BTREE,
  INDEX `idx_risk_level`(`risk_level` ASC) USING BTREE,
  INDEX `idx_is_active`(`is_active` ASC) USING BTREE,
  INDEX `idx_sort_order`(`sort_order` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '策略模板表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for suspend_info
-- ----------------------------
DROP TABLE IF EXISTS `suspend_info`;
CREATE TABLE `suspend_info`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `suspend_date` date NOT NULL,
  `resume_date` date NULL DEFAULT NULL,
  `suspend_timing` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '停牌时间',
  `suspend_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '停牌类型',
  `suspend_reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `is_suspended` tinyint(1) NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `updated_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_is_suspended`(`is_suspended` ASC) USING BTREE,
  INDEX `idx_ts_code_suspend`(`ts_code` ASC, `suspend_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 18541 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for sync_positions
-- ----------------------------
DROP TABLE IF EXISTS `sync_positions`;
CREATE TABLE `sync_positions`  (
  `sync_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `position` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sync_key`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for system_metrics
-- ----------------------------
DROP TABLE IF EXISTS `system_metrics`;
CREATE TABLE `system_metrics`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `metric_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '指标名称',
  `metric_type` enum('performance','business','system','error') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '指标类型',
  `metric_value` decimal(20, 6) NOT NULL COMMENT '指标值',
  `metric_unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '指标单位',
  `tags` json NULL COMMENT '标签信息',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '指标描述',
  `recorded_at` timestamp NOT NULL COMMENT '记录时间',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_metric_name`(`metric_name` ASC) USING BTREE,
  INDEX `idx_metric_type`(`metric_type` ASC) USING BTREE,
  INDEX `idx_recorded_at`(`recorded_at` ASC) USING BTREE,
  INDEX `idx_name_time`(`metric_name` ASC, `recorded_at` ASC) USING BTREE,
  INDEX `idx_type_time`(`metric_type` ASC, `recorded_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统监控指标表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for technical_indicators
-- ----------------------------
DROP TABLE IF EXISTS `technical_indicators`;
CREATE TABLE `technical_indicators`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ts_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'TS股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `ma5` decimal(10, 3) NULL DEFAULT NULL COMMENT '5日均线',
  `ma10` decimal(10, 3) NULL DEFAULT NULL COMMENT '10日均线',
  `ma20` decimal(10, 3) NULL DEFAULT NULL COMMENT '20日均线',
  `ma60` decimal(10, 3) NULL DEFAULT NULL COMMENT '60日均线',
  `ma120` decimal(10, 3) NULL DEFAULT NULL COMMENT '120日均线',
  `ma250` decimal(10, 3) NULL DEFAULT NULL COMMENT '250日均线',
  `rsi6` decimal(8, 4) NULL DEFAULT NULL COMMENT '6日RSI',
  `rsi12` decimal(8, 4) NULL DEFAULT NULL COMMENT '12日RSI',
  `rsi24` decimal(8, 4) NULL DEFAULT NULL COMMENT '24日RSI',
  `macd_dif` decimal(10, 6) NULL DEFAULT NULL COMMENT 'MACD DIF',
  `macd_dea` decimal(10, 6) NULL DEFAULT NULL COMMENT 'MACD DEA',
  `macd_bar` decimal(10, 6) NULL DEFAULT NULL COMMENT 'MACD BAR',
  `kdj_k` decimal(8, 4) NULL DEFAULT NULL COMMENT 'KDJ K值',
  `kdj_d` decimal(8, 4) NULL DEFAULT NULL COMMENT 'KDJ D值',
  `kdj_j` decimal(8, 4) NULL DEFAULT NULL COMMENT 'KDJ J值',
  `boll_upper` decimal(10, 3) NULL DEFAULT NULL COMMENT '布林带上轨',
  `boll_mid` decimal(10, 3) NULL DEFAULT NULL COMMENT '布林带中轨',
  `boll_lower` decimal(10, 3) NULL DEFAULT NULL COMMENT '布林带下轨',
  `wr10` decimal(8, 4) NULL DEFAULT NULL COMMENT '10日威廉指标',
  `wr6` decimal(8, 4) NULL DEFAULT NULL COMMENT '6日威廉指标',
  `vol_ma5` bigint NULL DEFAULT NULL COMMENT '5日成交量均线',
  `vol_ma10` bigint NULL DEFAULT NULL COMMENT '10日成交量均线',
  `vol_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '量比',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`, `trade_date`) USING BTREE,
  UNIQUE INDEX `uk_ts_code_date`(`ts_code` ASC, `trade_date` ASC) USING BTREE,
  INDEX `idx_ts_code`(`ts_code` ASC) USING BTREE,
  INDEX `idx_trade_date`(`trade_date` ASC) USING BTREE,
  INDEX `idx_rsi12`(`rsi12` ASC) USING BTREE,
  INDEX `idx_kdj_k`(`kdj_k` ASC) USING BTREE,
  INDEX `idx_macd_dif`(`macd_dif` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 103 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '技术指标数据表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for trade_cal
-- ----------------------------
DROP TABLE IF EXISTS `trade_cal`;
CREATE TABLE `trade_cal`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `exchange` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易所 SSE上交所 SZSE深交所',
  `cal_date` date NOT NULL COMMENT '日历日期',
  `is_open` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否交易 0休市 1交易',
  `pretrade_date` date NULL DEFAULT NULL COMMENT '上一个交易日',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_exchange_date`(`exchange` ASC, `cal_date` ASC) USING BTREE,
  INDEX `idx_cal_date`(`cal_date` ASC) USING BTREE,
  INDEX `idx_is_open`(`is_open` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 6629 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '交易日历表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for trade_records
-- ----------------------------
DROP TABLE IF EXISTS `trade_records`;
CREATE TABLE `trade_records`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `strategy_id` bigint NULL DEFAULT NULL COMMENT '策略ID',
  `stock_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_type` enum('buy','sell') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易类型',
  `order_type` enum('market','limit','stop') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'market' COMMENT '订单类型',
  `quantity` bigint NOT NULL COMMENT '交易数量',
  `price` decimal(10, 3) NOT NULL COMMENT '交易价格',
  `amount` decimal(15, 2) NOT NULL COMMENT '交易金额',
  `commission` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '手续费',
  `tax` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '印花税',
  `net_amount` decimal(15, 2) NOT NULL COMMENT '净交易金额',
  `trade_time` timestamp NOT NULL COMMENT '交易时间',
  `status` enum('pending','filled','cancelled','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'pending' COMMENT '交易状态',
  `order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '订单号',
  `reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '交易原因/备注',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_strategy_id`(`strategy_id` ASC) USING BTREE,
  INDEX `idx_stock_code`(`stock_code` ASC) USING BTREE,
  INDEX `idx_trade_type`(`trade_type` ASC) USING BTREE,
  INDEX `idx_trade_time`(`trade_time` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_user_time`(`user_id` ASC, `trade_time` ASC) USING BTREE,
  INDEX `idx_stock_time`(`stock_code` ASC, `trade_time` ASC) USING BTREE,
  INDEX `idx_order_id`(`order_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '交易记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for trading_strategies
-- ----------------------------
DROP TABLE IF EXISTS `trading_strategies`;
CREATE TABLE `trading_strategies`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `strategy_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '策略名称',
  `display_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '策略显示名称',
  `strategy_type` enum('technical','fundamental','quantitative','ai_driven','trend_following','mean_reversion','momentum','arbitrage','multi_factor','volatility','custom') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '策略类型',
  `category` enum('trend_following','mean_reversion','momentum','arbitrage','multi_factor','volatility','custom') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'custom' COMMENT '策略分类',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '策略描述',
  `author` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '策略作者',
  `min_capital` decimal(15, 2) NULL DEFAULT 100000.00 COMMENT '最小资金要求',
  `parameters` json NULL COMMENT '策略参数(JSON格式)',
  `indicators` json NULL COMMENT '使用的技术指标列表',
  `indicator_params` json NULL COMMENT '指标参数配置',
  `buy_conditions` json NULL COMMENT '买入条件',
  `sell_conditions` json NULL COMMENT '卖出条件',
  `code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '策略代码',
  `performance` decimal(8, 4) NULL DEFAULT NULL COMMENT '策略表现',
  `sharpe_ratio` decimal(8, 4) NULL DEFAULT NULL COMMENT '夏普比率',
  `max_drawdown` decimal(8, 4) NULL DEFAULT NULL COMMENT '最大回撤',
  `win_rate` decimal(8, 4) NULL DEFAULT NULL COMMENT '胜率',
  `total_trades` int NULL DEFAULT 0 COMMENT '总交易次数',
  `backtest_count` int NULL DEFAULT 0 COMMENT '回测次数',
  `last_backtest_date` date NULL DEFAULT NULL COMMENT '最后回测日期',
  `ai_generated` tinyint(1) NULL DEFAULT 0 COMMENT '是否AI生成',
  `original_prompt` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '原始提示词(AI生成时)',
  `risk_level` enum('low','medium','high') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'medium' COMMENT '风险等级',
  `max_position_size` decimal(15, 2) NULL DEFAULT NULL COMMENT '最大仓位',
  `stop_loss_pct` decimal(8, 4) NULL DEFAULT NULL COMMENT '止损百分比',
  `take_profit_pct` decimal(8, 4) NULL DEFAULT NULL COMMENT '止盈百分比',
  `status` enum('draft','active','inactive','testing','paused','stopped','error') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'draft' COMMENT '策略状态',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_run_at` timestamp NULL DEFAULT NULL COMMENT '最后运行时间',
  `risk_controls` json NULL COMMENT '风险控制参数(JSON格式)',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_strategy_type`(`strategy_type` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_user_status`(`user_id` ASC, `status` ASC) USING BTREE,
  INDEX `idx_category`(`category` ASC) USING BTREE,
  INDEX `idx_author`(`author` ASC) USING BTREE,
  INDEX `idx_ai_generated`(`ai_generated` ASC) USING BTREE,
  INDEX `idx_performance`(`performance` ASC) USING BTREE,
  INDEX `idx_last_backtest_date`(`last_backtest_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 36 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '交易策略配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for trading_users
-- ----------------------------
DROP TABLE IF EXISTS `trading_users`;
CREATE TABLE `trading_users`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱',
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `full_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '全名',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '电话',
  `user_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户类型',
  `risk_preference` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '风险偏好',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否激活',
  `last_login` datetime NULL DEFAULT NULL COMMENT '最后登录时间',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE,
  INDEX `idx_user_email`(`email` ASC) USING BTREE,
  INDEX `idx_user_type`(`user_type` ASC) USING BTREE,
  INDEX `idx_user_active`(`is_active` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for user_screening_preferences
-- ----------------------------
DROP TABLE IF EXISTS `user_screening_preferences`;
CREATE TABLE `user_screening_preferences`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `preferred_strategies` json NULL COMMENT '偏好策略列表',
  `default_conditions` json NULL COMMENT '默认筛选条件',
  `notification_settings` json NULL COMMENT '通知设置',
  `risk_level` enum('conservative','moderate','aggressive') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'moderate' COMMENT '风险偏好',
  `max_position_size` decimal(5, 2) NULL DEFAULT 10.00 COMMENT '最大仓位比例(%)',
  `stop_loss_rate` decimal(5, 2) NULL DEFAULT 10.00 COMMENT '止损比例(%)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_risk_level`(`risk_level` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户选股偏好表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱',
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `full_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '真实姓名',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '手机号',
  `status` enum('active','inactive','suspended') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'active' COMMENT '用户状态',
  `role` enum('admin','trader','viewer') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'trader' COMMENT '用户角色',
  `initial_capital` decimal(15, 2) NULL DEFAULT 0.00 COMMENT '初始资金',
  `current_capital` decimal(15, 2) NULL DEFAULT 0.00 COMMENT '当前资金',
  `risk_level` enum('conservative','moderate','aggressive') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'moderate' COMMENT '风险偏好',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `last_login_at` timestamp NULL DEFAULT NULL COMMENT '最后登录时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE,
  INDEX `idx_username`(`username` ASC) USING BTREE,
  INDEX `idx_email`(`email` ASC) USING BTREE,
  INDEX `idx_status_role`(`status` ASC, `role` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- View structure for user_trading_stats
-- ----------------------------
DROP VIEW IF EXISTS `user_trading_stats`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `user_trading_stats` AS select `u`.`id` AS `user_id`,`u`.`username` AS `username`,count(`tr`.`id`) AS `total_trades`,sum((case when (`tr`.`trade_type` = 'buy') then `tr`.`quantity` else 0 end)) AS `total_buy_quantity`,sum((case when (`tr`.`trade_type` = 'sell') then `tr`.`quantity` else 0 end)) AS `total_sell_quantity`,sum((case when (`tr`.`trade_type` = 'buy') then `tr`.`net_amount` else -(`tr`.`net_amount`) end)) AS `net_investment`,avg(`tr`.`price`) AS `avg_trade_price`,max(`tr`.`trade_time`) AS `last_trade_time` from (`users` `u` left join `trade_records` `tr` on(((`u`.`id` = `tr`.`user_id`) and (`tr`.`status` = 'filled')))) group by `u`.`id`,`u`.`username`;

-- ----------------------------
-- View structure for v_api_interface_stats
-- ----------------------------
DROP VIEW IF EXISTS `v_api_interface_stats`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_api_interface_stats` AS select `ai`.`id` AS `id`,`ai`.`api_code` AS `api_code`,`ai`.`api_name` AS `api_name`,`ai`.`api_category` AS `api_category`,`ai`.`status` AS `status`,`ds`.`name` AS `data_source_name`,`ds`.`provider` AS `provider`,`ai`.`total_calls` AS `total_calls`,`ai`.`success_calls` AS `success_calls`,(case when (`ai`.`total_calls` > 0) then round(((`ai`.`success_calls` / `ai`.`total_calls`) * 100),2) else 0 end) AS `success_rate`,`ai`.`avg_response_time` AS `avg_response_time`,`ai`.`last_call_time` AS `last_call_time`,`ai`.`synced_at` AS `synced_at`,`ai`.`created_at` AS `created_at` from (`api_interfaces` `ai` join `data_sources` `ds` on((`ai`.`data_source_id` = `ds`.`id`)));

-- ----------------------------
-- View structure for v_data_source_stats
-- ----------------------------
DROP VIEW IF EXISTS `v_data_source_stats`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_data_source_stats` AS select `ds`.`id` AS `id`,`ds`.`name` AS `name`,`ds`.`type` AS `type`,`ds`.`provider` AS `provider`,`ds`.`status` AS `status`,`ds`.`total_calls` AS `total_calls`,`ds`.`success_calls` AS `success_calls`,(case when (`ds`.`total_calls` > 0) then round(((`ds`.`success_calls` / `ds`.`total_calls`) * 100),2) else 0 end) AS `success_rate`,count(`ai`.`id`) AS `api_count`,count((case when (`ai`.`status` = 'active') then 1 end)) AS `active_api_count`,`ds`.`last_call_time` AS `last_call_time`,`ds`.`created_at` AS `created_at` from (`data_sources` `ds` left join `api_interfaces` `ai` on((`ds`.`id` = `ai`.`data_source_id`))) group by `ds`.`id`,`ds`.`name`,`ds`.`type`,`ds`.`provider`,`ds`.`status`,`ds`.`total_calls`,`ds`.`success_calls`,`ds`.`last_call_time`,`ds`.`created_at`;

-- ----------------------------
-- View structure for v_ensemble_performance_overview
-- ----------------------------
DROP VIEW IF EXISTS `v_ensemble_performance_overview`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_ensemble_performance_overview` AS select `e`.`ensemble_id` AS `ensemble_id`,`e`.`name` AS `name`,`e`.`weight_strategy` AS `weight_strategy`,`e`.`status` AS `status`,`e`.`enabled` AS `enabled`,`e`.`overall_accuracy` AS `overall_accuracy`,`e`.`model_count` AS `model_count`,`e`.`active_model_count` AS `active_model_count`,`e`.`avg_response_time` AS `avg_response_time`,`e`.`total_requests` AS `total_requests`,`e`.`last_used_at` AS `last_used_at`,group_concat(concat(`m`.`name`,'(',`emm`.`weight`,')') order by `emm`.`priority` ASC separator ',') AS `model_details` from ((`model_ensembles` `e` left join `ensemble_model_mapping` `emm` on(((`e`.`ensemble_id` = `emm`.`ensemble_id`) and (`emm`.`enabled` = 1)))) left join `ai_models` `m` on((`emm`.`model_id` = `m`.`model_id`))) group by `e`.`ensemble_id`;

-- ----------------------------
-- View structure for v_latest_daily_basic
-- ----------------------------
DROP VIEW IF EXISTS `v_latest_daily_basic`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_latest_daily_basic` AS select `db`.`ts_code` AS `ts_code`,`db`.`trade_date` AS `trade_date`,`db`.`close` AS `close`,`db`.`turnover_rate` AS `turnover_rate`,`db`.`volume_ratio` AS `volume_ratio`,`db`.`pe` AS `pe`,`db`.`pe_ttm` AS `pe_ttm`,`db`.`pb` AS `pb`,`db`.`ps` AS `ps`,`db`.`ps_ttm` AS `ps_ttm`,`db`.`total_mv` AS `total_mv`,`db`.`circ_mv` AS `circ_mv` from (`daily_basic` `db` join (select `daily_basic`.`ts_code` AS `ts_code`,max(`daily_basic`.`trade_date`) AS `max_date` from `daily_basic` group by `daily_basic`.`ts_code`) `latest` on(((`db`.`ts_code` = `latest`.`ts_code`) and (`db`.`trade_date` = `latest`.`max_date`))));

-- ----------------------------
-- View structure for v_model_performance_overview
-- ----------------------------
DROP VIEW IF EXISTS `v_model_performance_overview`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_model_performance_overview` AS select `m`.`model_id` AS `model_id`,`m`.`name` AS `name`,`m`.`model_type` AS `model_type`,`m`.`provider` AS `provider`,`m`.`status` AS `status`,`m`.`enabled` AS `enabled`,`m`.`accuracy_rate` AS `accuracy_rate`,`m`.`weight` AS `weight`,`m`.`avg_response_time` AS `avg_response_time`,`m`.`success_rate` AS `success_rate`,`m`.`total_requests` AS `total_requests`,`m`.`last_used_at` AS `last_used_at`,coalesce(`mt`.`daily_accuracy`,0) AS `today_accuracy`,coalesce(`mt`.`daily_requests`,0) AS `today_requests`,coalesce(`mt`.`daily_avg_response_time`,0) AS `today_avg_response_time` from (`ai_models` `m` left join (select `model_metrics`.`model_id` AS `model_id`,`model_metrics`.`accuracy_rate` AS `daily_accuracy`,`model_metrics`.`total_requests` AS `daily_requests`,`model_metrics`.`avg_response_time_ms` AS `daily_avg_response_time` from `model_metrics` where ((`model_metrics`.`metric_date` = curdate()) and (`model_metrics`.`time_period` = 'daily'))) `mt` on((`m`.`model_id` = `mt`.`model_id`)));

-- ----------------------------
-- Triggers structure for table backtest_results
-- ----------------------------
DROP TRIGGER IF EXISTS `update_strategy_stats_after_backtest`;
delimiter ;;
CREATE TRIGGER `update_strategy_stats_after_backtest` AFTER INSERT ON `backtest_results` FOR EACH ROW BEGIN
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
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table ensemble_model_mapping
-- ----------------------------
DROP TRIGGER IF EXISTS `tr_update_ensemble_stats_after_mapping_change`;
delimiter ;;
CREATE TRIGGER `tr_update_ensemble_stats_after_mapping_change` AFTER INSERT ON `ensemble_model_mapping` FOR EACH ROW BEGIN
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
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
