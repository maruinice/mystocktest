"""
AI Agent 数据模型
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Enum, Boolean, Index
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum as PyEnum

from ..core.database import Base


class AgentType(str, PyEnum):
    """Agent类型枚举"""
    MARKET_ANALYST = "market_analyst"
    FUNDAMENTAL_ANALYST = "fundamental_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    NEWS_ANALYST = "news_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    RISK_ANALYST = "risk_analyst"


class Recommendation(str, PyEnum):
    """推荐操作枚举"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class AnalysisStatus(str, PyEnum):
    """分析状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(str, PyEnum):
    """会话状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionType(str, PyEnum):
    """会话类型枚举"""
    SINGLE_STOCK = "single_stock"
    BATCH_ANALYSIS = "batch_analysis"
    SCHEME_RUN = "scheme_run"


class RiskLevel(str, PyEnum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AIAgent(Base):
    """AI Agent配置表"""
    __tablename__ = 'ai_agents'
    
    agent_id = Column(String(50), primary_key=True, comment='Agent唯一标识')
    name = Column(String(100), nullable=False, unique=True, comment='Agent名称')
    display_name = Column(String(150), comment='显示名称')
    description = Column(Text, comment='Agent描述')
    agent_type = Column(String(50), nullable=False, comment='Agent类型')
    model_id = Column(String(50), comment='绑定的模型ID')
    system_prompt = Column(Text, comment='系统提示词')
    enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    priority = Column(Integer, default=1, comment='优先级')
    weight = Column(Float, default=1.0, comment='权重')
    config_json = Column(JSON, comment='扩展配置')
    total_analyses = Column(Integer, default=0, comment='总分析次数')
    success_analyses = Column(Integer, default=0, comment='成功分析次数')
    avg_score = Column(Float, comment='平均评分')
    created_by = Column(String(50), comment='创建者')
    updated_by = Column(String(50), comment='更新者')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')
    
    __table_args__ = (
        Index('idx_agents_type', 'agent_type'),
        Index('idx_agents_enabled', 'enabled'),
        Index('idx_agents_model', 'model_id'),
    )


class AgentAnalysisRecord(Base):
    """Agent分析记录表"""
    __tablename__ = 'agent_analysis_records'
    
    record_id = Column(String(50), primary_key=True, comment='记录ID')
    session_id = Column(String(50), nullable=False, comment='会话ID')
    stock_code = Column(String(20), nullable=False, comment='股票代码')
    agent_id = Column(String(50), nullable=False, comment='Agent ID')
    agent_type = Column(String(50), nullable=False, comment='Agent类型')
    analysis_content = Column(Text, comment='分析内容')
    score = Column(Float, comment='评分(0-100)')
    confidence = Column(Float, comment='置信度(0-1)')
    recommendation = Column(String(20), comment='推荐操作')
    key_points = Column(JSON, comment='关键要点')
    risk_factors = Column(JSON, comment='风险因素')
    opportunities = Column(JSON, comment='机会因素')
    market_data = Column(JSON, comment='分析时的市场数据')
    model_used = Column(String(50), comment='使用的模型')
    tokens_used = Column(Integer, comment='使用的token数')
    response_time = Column(Integer, comment='响应时间(毫秒)')
    status = Column(String(20), default='pending', nullable=False, comment='状态')
    error_message = Column(Text, comment='错误信息')
    analysis_time = Column(DateTime, nullable=False, comment='分析时间')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    
    __table_args__ = (
        Index('idx_analysis_session', 'session_id'),
        Index('idx_analysis_stock', 'stock_code'),
        Index('idx_analysis_agent', 'agent_id'),
        Index('idx_analysis_time', 'analysis_time'),
        Index('idx_analysis_stock_agent', 'stock_code', 'agent_id'),
    )


class StockSelectionScheme(Base):
    """选股方案表"""
    __tablename__ = 'stock_selection_schemes'
    
    scheme_id = Column(String(50), primary_key=True, comment='方案ID')
    name = Column(String(100), nullable=False, unique=True, comment='方案名称')
    description = Column(Text, comment='方案描述')
    filter_conditions = Column(JSON, comment='筛选条件')
    agent_config = Column(JSON, comment='Agent配置')
    stock_pool = Column(JSON, comment='股票池')
    enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    total_runs = Column(Integer, default=0, comment='总运行次数')
    last_run_at = Column(DateTime, comment='最后运行时间')
    created_by = Column(String(50), comment='创建者')
    updated_by = Column(String(50), comment='更新者')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')
    
    __table_args__ = (
        Index('idx_schemes_enabled', 'enabled'),
        Index('idx_schemes_created_by', 'created_by'),
    )


class StockSelectionResult(Base):
    """选股结果表"""
    __tablename__ = 'stock_selection_results'
    
    result_id = Column(String(50), primary_key=True, comment='结果ID')
    session_id = Column(String(50), nullable=False, comment='会话ID')
    scheme_id = Column(String(50), nullable=True, comment='方案ID')
    stock_code = Column(String(20), nullable=False, comment='股票代码')
    stock_name = Column(String(100), comment='股票名称')
    final_score = Column(Float, comment='综合评分(0-100)')
    agent_scores = Column(JSON, comment='各Agent评分')
    recommendation = Column(String(20), comment='综合推荐')
    consensus_level = Column(Float, comment='共识度(0-1)')
    risk_level = Column(String(20), comment='风险等级')
    summary = Column(Text, comment='综合分析摘要')
    strengths = Column(JSON, comment='优势')
    weaknesses = Column(JSON, comment='劣势')
    market_data_snapshot = Column(JSON, comment='市场数据快照')
    rank = Column(Integer, comment='排名')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    
    __table_args__ = (
        Index('idx_results_session', 'session_id'),
        Index('idx_results_scheme', 'scheme_id'),
        Index('idx_results_stock', 'stock_code'),
        Index('idx_results_score', 'final_score'),
        Index('idx_results_scheme_score', 'scheme_id', 'final_score'),
        Index('idx_results_session_rank', 'session_id', 'rank'),
    )


class AgentAnalysisSession(Base):
    """Agent分析会话表"""
    __tablename__ = 'agent_analysis_sessions'
    
    session_id = Column(String(50), primary_key=True, comment='会话ID')
    session_type = Column(String(20), nullable=False, comment='会话类型')
    scheme_id = Column(String(50), comment='关联的方案ID')
    stock_codes = Column(JSON, comment='分析的股票代码列表')
    agent_ids = Column(JSON, comment='使用的Agent ID列表')
    total_stocks = Column(Integer, default=0, comment='总股票数')
    completed_stocks = Column(Integer, default=0, comment='已完成股票数')
    total_agents = Column(Integer, default=0, comment='总Agent数')
    status = Column(String(20), default='pending', nullable=False, comment='状态')
    progress = Column(Integer, default=0, comment='进度百分比')
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    error_message = Column(Text, comment='错误信息')
    created_by = Column(String(50), comment='创建者')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    
    __table_args__ = (
        Index('idx_sessions_type', 'session_type'),
        Index('idx_sessions_scheme', 'scheme_id'),
        Index('idx_sessions_status', 'status'),
        Index('idx_sessions_created_at', 'created_at'),
    )
