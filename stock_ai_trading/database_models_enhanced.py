"""
增强数据模型 - 新增表结构
"""
from sqlalchemy import Column, String, Date, Integer, Float, Text, DateTime, Boolean, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class IndustryClassification(Base):
    """行业分类表"""
    __tablename__ = 'industry_classification'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False)
    industry_code = Column(String(20), nullable=False)
    industry_name = Column(String(100), nullable=False)
    level = Column(Integer, default=1)
    classification_type = Column(String(20), default='sw')
    in_date = Column(Date)
    out_date = Column(Date)
    is_new = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_ts_code_type', 'ts_code', 'classification_type'),
        Index('idx_industry_code', 'industry_code'),
    )


class LimitPrice(Base):
    """涨跌停价格表"""
    __tablename__ = 'limit_prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False)
    trade_date = Column(Date, nullable=False)
    up_limit = Column(Float)
    down_limit = Column(Float)
    close = Column(Float)
    pct_chg = Column(Float)
    is_limit_up = Column(Boolean, default=False)
    is_limit_down = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_ts_code_date', 'ts_code', 'trade_date', unique=True),
        Index('idx_trade_date', 'trade_date'),
    )


class SuspendInfo(Base):
    """停复牌信息表"""
    __tablename__ = 'suspend_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False)
    suspend_date = Column(Date, nullable=False)
    resume_date = Column(Date)
    suspend_timing = Column(String(10))
    suspend_type = Column(String(50))
    suspend_reason = Column(Text)
    is_suspended = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_ts_code_suspend', 'ts_code', 'suspend_date'),
        Index('idx_is_suspended', 'is_suspended'),
    )


class AuditOpinion(Base):
    """审计意见表"""
    __tablename__ = 'audit_opinions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False)
    ann_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    audit_result = Column(String(50))
    audit_fees = Column(Float)
    audit_agency = Column(String(200))
    audit_sign = Column(String(100))
    opinion_type = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_ts_code_end', 'ts_code', 'end_date', unique=True),
    )
