-- 交易系统核心表定义
-- 添加到数据库中：orders(订单表)、positions(持仓表)、accounts(账户表)

USE stock_trading;

-- 1. 账户表(accounts) - 用户资金账户
CREATE TABLE IF NOT EXISTS accounts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL UNIQUE COMMENT '用户ID',
    total_assets DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '总资产',
    available_cash DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '可用资金',
    frozen_cash DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '冻结资金',
    market_value DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '持仓市值',
    profit_loss DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '浮动盈亏',
    profit_loss_pct DECIMAL(10,4) NOT NULL DEFAULT 0.0000 COMMENT '盈亏比例(%)',
    buying_power DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '购买力',
    margin_used DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '已用保证金',
    margin_available DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '可用保证金',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_user_id (user_id),
    INDEX idx_updated_at (updated_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账户资金表';

-- 2. 持仓表(positions) - 当前持仓
CREATE TABLE IF NOT EXISTS positions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    quantity INT NOT NULL DEFAULT 0 COMMENT '持仓数量',
    available_quantity INT NOT NULL DEFAULT 0 COMMENT '可用数量',
    frozen_quantity INT NOT NULL DEFAULT 0 COMMENT '冻结数量',
    avg_cost DECIMAL(10,3) NOT NULL COMMENT '平均成本',
    last_price DECIMAL(10,3) NOT NULL DEFAULT 0.000 COMMENT '最新价格',
    market_value DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '市值',
    cost_basis DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '成本基础',
    profit_loss DECIMAL(20,2) NOT NULL DEFAULT 0.00 COMMENT '浮动盈亏',
    profit_loss_pct DECIMAL(10,4) NOT NULL DEFAULT 0.0000 COMMENT '盈亏比例(%)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '建仓时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_user_stock (user_id, stock_code),
    INDEX idx_user_id (user_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_updated_at (updated_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='持仓表';

-- 3. 订单表(orders) - 交易订单
CREATE TABLE IF NOT EXISTS orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(50) NOT NULL UNIQUE COMMENT '订单号',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    side ENUM('buy','sell') NOT NULL COMMENT '买卖方向',
    order_type ENUM('market','limit','stop','stop_limit') NOT NULL DEFAULT 'limit' COMMENT '订单类型',
    quantity INT NOT NULL COMMENT '委托数量',
    price DECIMAL(10,3) NOT NULL DEFAULT 0.000 COMMENT '委托价格',
    stop_price DECIMAL(10,3) DEFAULT 0.000 COMMENT '止损价格',
    filled_quantity INT NOT NULL DEFAULT 0 COMMENT '已成交数量',
    avg_price DECIMAL(10,3) NOT NULL DEFAULT 0.000 COMMENT '成交均价',
    status ENUM('pending','partial','filled','cancelled','rejected') NOT NULL DEFAULT 'pending' COMMENT '订单状态',
    time_in_force VARCHAR(10) DEFAULT 'day' COMMENT '有效期(day/gtc/ioc/fok)',
    commission DECIMAL(10,2) DEFAULT 0.00 COMMENT '手续费',
    notes TEXT COMMENT '备注',
    strategy_id BIGINT COMMENT '策略ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    filled_at TIMESTAMP NULL COMMENT '成交时间',
    
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_status (status),
    INDEX idx_side (side),
    INDEX idx_user_status (user_id, status),
    INDEX idx_user_stock (user_id, stock_code),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- 4. 创建默认管理员账户（如果不存在）
INSERT INTO accounts (user_id, total_assets, available_cash, buying_power) 
SELECT id, 100000.00, 100000.00, 100000.00 
FROM users 
WHERE id = 1 AND NOT EXISTS (SELECT 1 FROM accounts WHERE user_id = 1);

-- 5. 添加索引优化（如果不存在）
-- MySQL不支持 IF NOT EXISTS 在ALTER TABLE中，使用存储过程
DELIMITER $$

CREATE PROCEDURE AddIndexIfNotExists()
BEGIN
    -- 检查并添加 trade_records.idx_order_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = 'stock_trading' 
        AND table_name = 'trade_records' 
        AND index_name = 'idx_order_id'
    ) THEN
        ALTER TABLE trade_records ADD INDEX idx_order_id (order_id);
    END IF;
    
    -- 检查并添加 portfolios.idx_updated_at  
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = 'stock_trading' 
        AND table_name = 'portfolios' 
        AND index_name = 'idx_updated_at'
    ) THEN
        ALTER TABLE portfolios ADD INDEX idx_updated_at (last_updated);
    END IF;
END$$

DELIMITER ;

CALL AddIndexIfNotExists();
DROP PROCEDURE IF EXISTS AddIndexIfNotExists;

