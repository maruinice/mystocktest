-- 修复 suspend_info 表结构
-- 问题：suspend_timing 字段长度不够，导致数据插入失败

-- 1. 检查当前表结构
DESCRIBE suspend_info;

-- 2. 修改 suspend_timing 字段长度
-- 从 VARCHAR(50) 或更小改为 VARCHAR(100)
ALTER TABLE suspend_info 
MODIFY COLUMN suspend_timing VARCHAR(100) DEFAULT NULL COMMENT '停牌时间';

-- 3. 确保其他字段也足够
ALTER TABLE suspend_info 
MODIFY COLUMN suspend_type VARCHAR(50) DEFAULT NULL COMMENT '停牌类型';

-- 4. 验证修改
DESCRIBE suspend_info;

-- 5. 查看现有数据
SELECT COUNT(*) as total_count FROM suspend_info;
SELECT * FROM suspend_info LIMIT 5;
