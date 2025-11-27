-- 为stock_selection_results表添加交易建议字段
ALTER TABLE stock_selection_results 
ADD COLUMN entry_price DECIMAL(10, 2) COMMENT '建议买入价' AFTER market_data_snapshot,
ADD COLUMN target_price DECIMAL(10, 2) COMMENT '目标止盈价' AFTER entry_price,
ADD COLUMN stop_loss_price DECIMAL(10, 2) COMMENT '止损价' AFTER target_price,
ADD COLUMN expected_return DECIMAL(6, 2) COMMENT '预期收益率(%)' AFTER stop_loss_price,
ADD COLUMN holding_period INT COMMENT '建议持仓天数' AFTER expected_return,
ADD COLUMN trade_reason TEXT COMMENT '交易理由' AFTER holding_period;
