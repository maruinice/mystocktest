"""
股票相关数据模型
定义数据库表结构对应的SQLAlchemy模型
"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base

class StockBasic(Base):
    """股票基础信息表"""
    __tablename__ = 'stock_basic'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), unique=True, nullable=False, comment='股票代码')
    symbol = Column(String(10), nullable=False, comment='股票简称')
    name = Column(String(50), nullable=False, comment='股票名称')
    area = Column(String(20), comment='地域')
    industry = Column(String(50), comment='所属行业')
    fullname = Column(String(100), comment='股票全称')
    enname = Column(String(100), comment='英文全称')
    cnspell = Column(String(50), comment='拼音缩写')
    market = Column(String(10), comment='市场类型')
    exchange = Column(String(10), comment='交易所代码')
    curr_type = Column(String(10), comment='交易货币')
    list_status = Column(String(1), comment='上市状态')
    list_date = Column(String(8), comment='上市日期')
    delist_date = Column(String(8), comment='退市日期')
    is_hs = Column(String(1), comment='是否沪深港通标的')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_stock_basic_symbol', 'symbol'),
        Index('idx_stock_basic_industry', 'industry'),
        Index('idx_stock_basic_market', 'market'),
        Index('idx_stock_basic_list_status', 'list_status'),
    )

class StockQuotes(Base):
    """股票行情数据表"""
    __tablename__ = 'stock_quotes'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment='股票代码')
    trade_date = Column(String(8), nullable=False, comment='交易日期')
    open = Column(Float, comment='开盘价')
    high = Column(Float, comment='最高价')
    low = Column(Float, comment='最低价')
    close = Column(Float, comment='收盘价')
    pre_close = Column(Float, comment='昨收价')
    change = Column(Float, comment='涨跌额')
    pct_chg = Column(Float, comment='涨跌幅')
    vol = Column(Float, comment='成交量(手)')
    amount = Column(Float, comment='成交额(千元)')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    
    # 复合索引
    __table_args__ = (
        Index('idx_quotes_code_date', 'ts_code', 'trade_date'),
        Index('idx_quotes_date', 'trade_date'),
        Index('idx_quotes_code', 'ts_code'),
        # 分区配置在init.sql中定义
    )

class FinancialData(Base):
    """财务数据表"""
    __tablename__ = 'financial_data'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment='股票代码')
    ann_date = Column(String(8), comment='公告日期')
    f_ann_date = Column(String(8), comment='实际公告日期')
    end_date = Column(String(8), nullable=False, comment='报告期')
    report_type = Column(String(20), comment='报告类型')
    comp_type = Column(String(1), comment='公司类型')
    basic_eps = Column(Float, comment='基本每股收益')
    diluted_eps = Column(Float, comment='稀释每股收益')
    total_revenue = Column(Float, comment='营业总收入')
    revenue = Column(Float, comment='营业收入')
    int_income = Column(Float, comment='利息收入')
    prem_earned = Column(Float, comment='已赚保费')
    comm_income = Column(Float, comment='手续费及佣金收入')
    n_commis_income = Column(Float, comment='手续费及佣金净收入')
    n_oth_income = Column(Float, comment='其他经营净收益')
    n_oth_b_income = Column(Float, comment='加:其他业务净收益')
    prem_income = Column(Float, comment='保险业务收入')
    out_prem = Column(Float, comment='减:分出保费')
    une_prem_reser = Column(Float, comment='提取未到期责任准备金')
    reins_income = Column(Float, comment='其中:分保费收入')
    n_sec_tb_income = Column(Float, comment='代理买卖证券业务净收入')
    n_sec_uw_income = Column(Float, comment='证券承销业务净收入')
    n_asset_mg_income = Column(Float, comment='受托客户资产管理业务净收入')
    oth_b_income = Column(Float, comment='其他业务收入')
    fv_value_chg_gain = Column(Float, comment='加:公允价值变动净收益')
    invest_income = Column(Float, comment='加:投资净收益')
    ass_invest_income = Column(Float, comment='其中:对联营企业和合营企业的投资收益')
    forex_gain = Column(Float, comment='加:汇兑净收益')
    total_cogs = Column(Float, comment='营业总成本')
    oper_cost = Column(Float, comment='减:营业成本')
    int_exp = Column(Float, comment='减:利息支出')
    comm_exp = Column(Float, comment='减:手续费及佣金支出')
    biz_tax_surchg = Column(Float, comment='减:营业税金及附加')
    sell_exp = Column(Float, comment='减:销售费用')
    admin_exp = Column(Float, comment='减:管理费用')
    fin_exp = Column(Float, comment='减:财务费用')
    assets_impair_loss = Column(Float, comment='减:资产减值损失')
    prem_refund = Column(Float, comment='退保金')
    compens_payout = Column(Float, comment='赔付总支出')
    reser_insur_liab = Column(Float, comment='提取保险责任准备金')
    div_payt = Column(Float, comment='保户红利支出')
    reins_exp = Column(Float, comment='分保费用')
    oper_exp = Column(Float, comment='营业支出')
    compens_payout_refu = Column(Float, comment='减:摊回赔付支出')
    insur_reser_refu = Column(Float, comment='减:摊回保险责任准备金')
    reins_cost_refund = Column(Float, comment='减:摊回分保费用')
    other_bus_cost = Column(Float, comment='其他业务成本')
    operate_profit = Column(Float, comment='营业利润')
    non_oper_income = Column(Float, comment='加:营业外收入')
    non_oper_exp = Column(Float, comment='减:营业外支出')
    nca_disploss = Column(Float, comment='其中:减:非流动资产处置净损失')
    total_profit = Column(Float, comment='利润总额')
    income_tax = Column(Float, comment='所得税费用')
    n_income = Column(Float, comment='净利润')
    n_income_attr_p = Column(Float, comment='归属于母公司所有者的净利润')
    minority_gain = Column(Float, comment='少数股东损益')
    oth_compr_income = Column(Float, comment='其他综合收益')
    t_compr_income = Column(Float, comment='综合收益总额')
    compr_inc_attr_p = Column(Float, comment='归属于母公司所有者的综合收益总额')
    compr_inc_attr_m_s = Column(Float, comment='归属于少数股东的综合收益总额')
    ebit = Column(Float, comment='息税前利润')
    ebitda = Column(Float, comment='息税折旧摊销前利润')
    insurance_exp = Column(Float, comment='保险业务支出')
    undist_profit = Column(Float, comment='年初未分配利润')
    distable_profit = Column(Float, comment='可分配利润')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    
    # 复合索引
    __table_args__ = (
        Index('idx_financial_code_date', 'ts_code', 'end_date'),
        Index('idx_financial_ann_date', 'ann_date'),
        Index('idx_financial_end_date', 'end_date'),
        # 分区配置在init.sql中定义
    )

class TradingStrategies(Base):
    """交易策略表"""
    __tablename__ = 'trading_strategies'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    strategy_name = Column(String(100), nullable=False, comment='策略名称')
    strategy_type = Column(String(50), nullable=False, comment='策略类型')
    description = Column(Text, comment='策略描述')
    parameters = Column(Text, comment='策略参数(JSON格式)')
    risk_level = Column(String(20), comment='风险等级')
    expected_return = Column(Float, comment='预期收益率')
    max_drawdown = Column(Float, comment='最大回撤')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建者ID')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    creator = relationship("Users", back_populates="strategies")
    
    # 索引
    __table_args__ = (
        Index('idx_strategy_type', 'strategy_type'),
        Index('idx_strategy_active', 'is_active'),
        Index('idx_strategy_creator', 'created_by'),
    )

class Portfolios(Base):
    """投资组合表"""
    __tablename__ = 'portfolios'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    portfolio_name = Column(String(100), nullable=False, comment='组合名称')
    total_value = Column(Float, default=0.0, comment='总市值')
    available_cash = Column(Float, default=0.0, comment='可用资金')
    frozen_cash = Column(Float, default=0.0, comment='冻结资金')
    total_profit = Column(Float, default=0.0, comment='总盈亏')
    total_return_rate = Column(Float, default=0.0, comment='总收益率')
    risk_level = Column(String(20), comment='风险等级')
    strategy_id = Column(Integer, ForeignKey('trading_strategies.id'), comment='关联策略ID')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    user = relationship("Users", back_populates="portfolios")
    strategy = relationship("TradingStrategies")
    trades = relationship("TradeRecords", back_populates="portfolio")
    
    # 索引
    __table_args__ = (
        Index('idx_portfolio_user', 'user_id'),
        Index('idx_portfolio_strategy', 'strategy_id'),
        Index('idx_portfolio_active', 'is_active'),
    )

class TradeRecords(Base):
    """交易记录表"""
    __tablename__ = 'trade_records'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False, comment='组合ID')
    ts_code = Column(String(20), nullable=False, comment='股票代码')
    trade_type = Column(String(10), nullable=False, comment='交易类型(buy/sell)')
    quantity = Column(Integer, nullable=False, comment='交易数量')
    price = Column(Float, nullable=False, comment='交易价格')
    amount = Column(Float, nullable=False, comment='交易金额')
    commission = Column(Float, default=0.0, comment='手续费')
    tax = Column(Float, default=0.0, comment='印花税')
    net_amount = Column(Float, nullable=False, comment='净交易金额')
    trade_time = Column(DateTime, nullable=False, comment='交易时间')
    order_id = Column(String(50), comment='订单ID')
    strategy_signal = Column(String(100), comment='策略信号')
    profit_loss = Column(Float, comment='盈亏金额')
    return_rate = Column(Float, comment='收益率')
    status = Column(String(20), default='completed', comment='交易状态')
    remark = Column(Text, comment='备注')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    
    # 关系
    portfolio = relationship("Portfolios", back_populates="trades")
    
    # 索引
    __table_args__ = (
        Index('idx_trade_portfolio_code_time', 'portfolio_id', 'ts_code', 'trade_time'),
        Index('idx_trade_time', 'trade_time'),
        Index('idx_trade_code', 'ts_code'),
        Index('idx_trade_type', 'trade_type'),
        # 分区配置在init.sql中定义
    )

class RiskRules(Base):
    """风控规则表"""
    __tablename__ = 'risk_rules'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    rule_type = Column(String(50), nullable=False, comment='规则类型')
    rule_condition = Column(Text, nullable=False, comment='规则条件(JSON格式)')
    action_type = Column(String(50), nullable=False, comment='触发动作')
    priority = Column(Integer, default=1, comment='优先级')
    is_active = Column(Boolean, default=True, comment='是否启用')
    description = Column(Text, comment='规则描述')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建者ID')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    creator = relationship("Users")
    
    # 索引
    __table_args__ = (
        Index('idx_risk_rule_type', 'rule_type'),
        Index('idx_risk_rule_active', 'is_active'),
        Index('idx_risk_rule_priority', 'priority'),
    )

class LLMDecisions(Base):
    """LLM决策记录表"""
    __tablename__ = 'llm_decisions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    decision_id = Column(String(50), unique=True, nullable=False, comment='决策ID')
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), comment='组合ID')
    ts_code = Column(String(20), comment='股票代码')
    decision_type = Column(String(50), nullable=False, comment='决策类型')
    input_data = Column(Text, comment='输入数据(JSON格式)')
    llm_model = Column(String(50), comment='使用的LLM模型')
    prompt_template = Column(Text, comment='提示词模板')
    llm_response = Column(Text, comment='LLM原始响应')
    parsed_decision = Column(Text, comment='解析后的决策(JSON格式)')
    confidence_score = Column(Float, comment='置信度分数')
    decision_time = Column(DateTime, nullable=False, comment='决策时间')
    execution_status = Column(String(20), default='pending', comment='执行状态')
    execution_result = Column(Text, comment='执行结果')
    feedback_score = Column(Float, comment='反馈评分')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    
    # 关系
    portfolio = relationship("Portfolios")
    
    # 索引
    __table_args__ = (
        Index('idx_llm_decision_portfolio_time', 'portfolio_id', 'decision_time'),
        Index('idx_llm_decision_code_time', 'ts_code', 'decision_time'),
        Index('idx_llm_decision_type', 'decision_type'),
        Index('idx_llm_decision_status', 'execution_status'),
        # 分区配置在init.sql中定义
    )

class SystemMetrics(Base):
    """系统指标表"""
    __tablename__ = 'system_metrics'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False, comment='指标名称')
    metric_type = Column(String(50), nullable=False, comment='指标类型')
    metric_value = Column(Float, nullable=False, comment='指标值')
    metric_unit = Column(String(20), comment='指标单位')
    metric_time = Column(DateTime, nullable=False, comment='指标时间')
    source_system = Column(String(50), comment='来源系统')
    additional_info = Column(Text, comment='附加信息(JSON格式)')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_metrics_name_time', 'metric_name', 'metric_time'),
        Index('idx_metrics_type_time', 'metric_type', 'metric_time'),
        Index('idx_metrics_time', 'metric_time'),
        # 分区配置在init.sql中定义
    )

class Users(Base):
    """用户表"""
    __tablename__ = 'trading_users'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, comment='邮箱')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    full_name = Column(String(100), comment='全名')
    phone = Column(String(20), comment='电话')
    user_type = Column(String(20), default='individual', comment='用户类型')
    risk_preference = Column(String(20), comment='风险偏好')
    is_active = Column(Boolean, default=True, comment='是否激活')
    last_login = Column(DateTime, comment='最后登录时间')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    portfolios = relationship("Portfolios", back_populates="user")
    strategies = relationship("TradingStrategies", back_populates="creator")
    
    # 索引
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_type', 'user_type'),
        Index('idx_user_active', 'is_active'),
    )