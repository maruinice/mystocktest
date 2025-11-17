def initialize(context):
    # 设置股票池
    context.stocks = ['000001.XSHE', '600000.XSHG', '000858.XSHE', '600036.XSHG']
    
    # 设置均线参数
    context.ma_short = 5    # 短期均线周期
    context.ma_long = 20    # 长期均线周期
    context.position_size = 0.8  # 单只股票最大仓位比例

def handle_data(context, data):
    """
    数据处理函数，每个交易日执行
    策略逻辑：MA5上穿MA20买入，MA5下穿MA20卖出
    """
    for stock in context.stocks:
        # 获取足够的历史数据用于计算均线
        prices = data.history(stock, 'close', context.ma_long + 1)
        
        # 计算短期均线和长期均线
        ma_short = prices[-context.ma_short:].mean()
        ma_long = prices.mean()
        
        # 获取前一天的均线值用于判断交叉
        if len(prices) >= context.ma_long + 2:
            prev_ma_short = prices[-context.ma_short-1:-1].mean()
            prev_ma_long = prices[:-1].mean()
        else:
            # 数据不足时跳过
            continue
        
        # 获取当前持仓
        current_position = context.portfolio.positions[stock].amount
        
        # 买入条件：MA5上穿MA20（金叉）且当前无持仓
        if (prev_ma_short <= prev_ma_long and 
            ma_short > ma_long and 
            current_position == 0):
            
            # 计算可用资金
            available_cash = context.portfolio.cash
            if available_cash > 0:
                # 按设定仓位比例买入
                order_target_percent(stock, context.position_size)
                print(f"买入信号：{stock} MA5上穿MA20，买入仓位{context.position_size}")
        
        # 卖出条件：MA5下穿MA20（死叉）且当前有持仓
        elif (prev_ma_short >= prev_ma_long and 
              ma_short < ma_long and 
              current_position > 0):
            
            # 清仓卖出
            order_target_percent(stock, 0)
            print(f"卖出信号：{stock} MA5下穿MA20，清仓")
        
        # 止损控制：如果当前有持仓，检查是否需要止损
        if current_position > 0:
            current_price = data.current(stock, 'close')
            # 这里可以添加更复杂的止损逻辑
            # 例如基于持仓成本价的止损