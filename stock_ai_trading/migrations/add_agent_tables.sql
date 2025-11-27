-- ====================================================
-- AI Agent 系统数据表
-- 创建时间: 2025-11-27
-- 说明: 支持多智能体选股系统的数据表
-- ====================================================

SET NAMES utf8mb4;

-- ----------------------------
-- Table structure for ai_agents
-- ----------------------------
DROP TABLE IF EXISTS `ai_agents`;
CREATE TABLE `ai_agents` (
  `agent_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Agent唯一标识',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Agent名称',
  `display_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '显示名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'Agent描述',
  `agent_type` enum('market_analyst','fundamental_analyst','technical_analyst','news_analyst','sentiment_analyst','risk_analyst') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Agent类型',
  `model_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '绑定的模型ID',
  `system_prompt` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '系统提示词',
  `enabled` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用(0:禁用,1:启用)',
  `priority` int NULL DEFAULT 1 COMMENT '优先级(数字越小优先级越高)',
  `weight` decimal(5, 4) NULL DEFAULT 1.0000 COMMENT '权重(0.0000-1.0000)',
  `config_json` json NULL COMMENT '扩展配置(JSON格式)',
  `total_analyses` bigint NULL DEFAULT 0 COMMENT '总分析次数',
  `success_analyses` bigint NULL DEFAULT 0 COMMENT '成功分析次数',
  `avg_score` decimal(5, 2) NULL DEFAULT NULL COMMENT '平均评分',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '创建者',
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`agent_id`) USING BTREE,
  UNIQUE INDEX `uk_agents_name`(`name` ASC) USING BTREE,
  INDEX `idx_agents_type`(`agent_type` ASC) USING BTREE,
  INDEX `idx_agents_enabled`(`enabled` ASC) USING BTREE,
  INDEX `idx_agents_model`(`model_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'AI Agent配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for agent_analysis_records
-- ----------------------------
DROP TABLE IF EXISTS `agent_analysis_records`;
CREATE TABLE `agent_analysis_records` (
  `record_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '记录ID',
  `session_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话ID(同一次分析的多个Agent共享)',
  `stock_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `agent_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Agent ID',
  `agent_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Agent类型',
  `analysis_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '分析内容',
  `score` decimal(5, 2) NULL DEFAULT NULL COMMENT '评分(0-100)',
  `confidence` decimal(5, 4) NULL DEFAULT NULL COMMENT '置信度(0-1)',
  `recommendation` enum('strong_buy','buy','hold','sell','strong_sell') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '推荐操作',
  `key_points` json NULL COMMENT '关键要点(JSON数组)',
  `risk_factors` json NULL COMMENT '风险因素(JSON数组)',
  `opportunities` json NULL COMMENT '机会因素(JSON数组)',
  `market_data` json NULL COMMENT '分析时的市场数据',
  `model_used` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '使用的模型',
  `tokens_used` int NULL DEFAULT NULL COMMENT '使用的token数',
  `response_time` int NULL DEFAULT NULL COMMENT '响应时间(毫秒)',
  `status` enum('pending','processing','completed','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '状态',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `analysis_time` datetime NOT NULL COMMENT '分析时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`record_id`) USING BTREE,
  INDEX `idx_analysis_session`(`session_id` ASC) USING BTREE,
  INDEX `idx_analysis_stock`(`stock_code` ASC) USING BTREE,
  INDEX `idx_analysis_agent`(`agent_id` ASC) USING BTREE,
  INDEX `idx_analysis_time`(`analysis_time` ASC) USING BTREE,
  INDEX `idx_analysis_stock_agent`(`stock_code` ASC, `agent_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'Agent分析记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for stock_selection_schemes
-- ----------------------------
DROP TABLE IF EXISTS `stock_selection_schemes`;
CREATE TABLE `stock_selection_schemes` (
  `scheme_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '方案ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '方案名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '方案描述',
  `filter_conditions` json NULL COMMENT '筛选条件(JSON格式)',
  `agent_config` json NULL COMMENT 'Agent配置(包含使用的Agent列表和权重)',
  `stock_pool` json NULL COMMENT '股票池(股票代码列表)',
  `enabled` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `total_runs` int NULL DEFAULT 0 COMMENT '总运行次数',
  `last_run_at` timestamp NULL DEFAULT NULL COMMENT '最后运行时间',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '创建者',
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`scheme_id`) USING BTREE,
  UNIQUE INDEX `uk_schemes_name`(`name` ASC) USING BTREE,
  INDEX `idx_schemes_enabled`(`enabled` ASC) USING BTREE,
  INDEX `idx_schemes_created_by`(`created_by` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '选股方案表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for stock_selection_results
-- ----------------------------
DROP TABLE IF EXISTS `stock_selection_results`;
CREATE TABLE `stock_selection_results` (
  `result_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '结果ID',
  `session_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话ID',
  `scheme_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '方案ID',
  `stock_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `stock_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '股票名称',
  `final_score` decimal(5, 2) NULL DEFAULT NULL COMMENT '综合评分(0-100)',
  `agent_scores` json NULL COMMENT '各Agent评分(JSON格式)',
  `recommendation` enum('strong_buy','buy','hold','sell','strong_sell') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '综合推荐',
  `consensus_level` decimal(5, 4) NULL DEFAULT NULL COMMENT '共识度(0-1)',
  `risk_level` enum('low','medium','high','very_high') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '风险等级',
  `summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '综合分析摘要',
  `strengths` json NULL COMMENT '优势(JSON数组)',
  `weaknesses` json NULL COMMENT '劣势(JSON数组)',
  `market_data_snapshot` json NULL COMMENT '市场数据快照',
  `rank` int NULL DEFAULT NULL COMMENT '排名',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`result_id`) USING BTREE,
  INDEX `idx_results_session`(`session_id` ASC) USING BTREE,
  INDEX `idx_results_scheme`(`scheme_id` ASC) USING BTREE,
  INDEX `idx_results_stock`(`stock_code` ASC) USING BTREE,
  INDEX `idx_results_score`(`final_score` DESC) USING BTREE,
  INDEX `idx_results_scheme_score`(`scheme_id` ASC, `final_score` DESC) USING BTREE,
  INDEX `idx_results_session_rank`(`session_id` ASC, `rank` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '选股结果表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for agent_analysis_sessions
-- ----------------------------
DROP TABLE IF EXISTS `agent_analysis_sessions`;
CREATE TABLE `agent_analysis_sessions` (
  `session_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话ID',
  `session_type` enum('single_stock','batch_analysis','scheme_run') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话类型',
  `scheme_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '关联的方案ID',
  `stock_codes` json NULL COMMENT '分析的股票代码列表',
  `agent_ids` json NULL COMMENT '使用的Agent ID列表',
  `total_stocks` int NULL DEFAULT 0 COMMENT '总股票数',
  `completed_stocks` int NULL DEFAULT 0 COMMENT '已完成股票数',
  `total_agents` int NULL DEFAULT 0 COMMENT '总Agent数',
  `status` enum('pending','running','completed','failed','cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '状态',
  `progress` int NULL DEFAULT 0 COMMENT '进度百分比(0-100)',
  `started_at` timestamp NULL DEFAULT NULL COMMENT '开始时间',
  `completed_at` timestamp NULL DEFAULT NULL COMMENT '完成时间',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '创建者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`session_id`) USING BTREE,
  INDEX `idx_sessions_type`(`session_type` ASC) USING BTREE,
  INDEX `idx_sessions_scheme`(`scheme_id` ASC) USING BTREE,
  INDEX `idx_sessions_status`(`status` ASC) USING BTREE,
  INDEX `idx_sessions_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'Agent分析会话表' ROW_FORMAT = Dynamic;

-- 插入默认的Agent配置
INSERT INTO `ai_agents` (`agent_id`, `name`, `display_name`, `description`, `agent_type`, `system_prompt`, `enabled`, `priority`, `weight`) VALUES
('agent_market_001', 'market_analyst', '市场分析师', '分析宏观经济环境、市场趋势、行业动态', 'market_analyst', 
'你是一位资深的市场分析师，擅长分析宏观经济环境、市场整体趋势和行业动态。请从以下角度分析股票：
1. 当前市场环境和趋势
2. 所属行业的发展前景
3. 市场情绪和资金流向
4. 政策影响和宏观因素
请给出0-100的评分，并说明关键要点、风险因素和机会。', 1, 1, 0.2500),

('agent_fundamental_001', 'fundamental_analyst', '基本面分析师', '分析财务数据、估值水平、盈利能力', 'fundamental_analyst',
'你是一位资深的基本面分析师，擅长分析公司财务数据和估值。请从以下角度分析股票：
1. 财务健康状况（资产负债率、流动比率等）
2. 盈利能力（ROE、净利率、营收增长等）
3. 估值水平（PE、PB、PS等）
4. 成长性和可持续性
请给出0-100的评分，并说明关键要点、风险因素和机会。', 1, 2, 0.3000),

('agent_technical_001', 'technical_analyst', '技术分析师', '分析K线形态、技术指标、支撑阻力', 'technical_analyst',
'你是一位资深的技术分析师，擅长分析K线形态和技术指标。请从以下角度分析股票：
1. 价格趋势和形态（上升/下降趋势、突破/支撑等）
2. 技术指标（MACD、KDJ、RSI、均线等）
3. 成交量分析
4. 支撑位和阻力位
请给出0-100的评分，并说明关键要点、风险因素和机会。', 1, 3, 0.2500),

('agent_sentiment_001', 'sentiment_analyst', '情绪分析师', '分析市场情绪、投资者行为、舆情', 'sentiment_analyst',
'你是一位资深的市场情绪分析师，擅长分析投资者情绪和市场舆情。请从以下角度分析股票：
1. 市场情绪指标（换手率、振幅等）
2. 投资者行为（主力资金、散户情绪等）
3. 新闻舆情和热度
4. 市场关注度和讨论度
请给出0-100的评分，并说明关键要点、风险因素和机会。', 1, 4, 0.2000);
