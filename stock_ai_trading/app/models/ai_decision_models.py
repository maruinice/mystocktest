"""
AI决策执行引擎相关数据模型
定义交易决策、指令解析、置信度评估等相关的数据结构
"""
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Text, Boolean, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

# 枚举类型定义
class TradingAction(str, Enum):
    """交易动作枚举"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class InstructionType(str, Enum):
    """指令类型枚举"""
    MARKET_ORDER = "MARKET_ORDER"
    LIMIT_ORDER = "LIMIT_ORDER"
    STOP_ORDER = "STOP_ORDER"
    CONDITIONAL_ORDER = "CONDITIONAL_ORDER"

class ConfidenceLevel(str, Enum):
    """置信度等级枚举"""
    VERY_LOW = "VERY_LOW"      # 0.0-0.2
    LOW = "LOW"                # 0.2-0.4
    MEDIUM = "MEDIUM"          # 0.4-0.6
    HIGH = "HIGH"              # 0.6-0.8
    VERY_HIGH = "VERY_HIGH"    # 0.8-1.0

class ExecutionStrategy(str, Enum):
    """执行策略枚举"""
    IMMEDIATE = "IMMEDIATE"
    TWAP = "TWAP"              # 时间加权平均价格
    VWAP = "VWAP"              # 成交量加权平均价格
    ICEBERG = "ICEBERG"        # 冰山订单
    SMART_ROUTING = "SMART_ROUTING"

# Pydantic模型 - 用于API请求/响应
class TradingDecision(BaseModel):
    """交易决策数据结构"""
    action: TradingAction = Field(..., description="交易动作")
    symbol: str = Field(..., description="股票代码")
    quantity: int = Field(..., gt=0, description="交易数量")
    price: Optional[float] = Field(None, gt=0, description="交易价格")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    reasoning: str = Field(..., description="决策理由")
    model_id: str = Field(..., description="模型ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="决策时间")
    
    # 扩展字段
    instruction_type: InstructionType = Field(default=InstructionType.MARKET_ORDER, description="指令类型")
    execution_strategy: ExecutionStrategy = Field(default=ExecutionStrategy.IMMEDIATE, description="执行策略")
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="风险评分")
    expected_return: Optional[float] = Field(None, description="预期收益率")
    stop_loss: Optional[float] = Field(None, gt=0, description="止损价格")
    take_profit: Optional[float] = Field(None, gt=0, description="止盈价格")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('置信度必须在0.0到1.0之间')
        return v
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """获取置信度等级"""
        if self.confidence < 0.2:
            return ConfidenceLevel.VERY_LOW
        elif self.confidence < 0.4:
            return ConfidenceLevel.LOW
        elif self.confidence < 0.6:
            return ConfidenceLevel.MEDIUM
        elif self.confidence < 0.8:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH

class InstructionParseResult(BaseModel):
    """指令解析结果"""
    original_instruction: str = Field(..., description="原始指令")
    parsed_instruction: str = Field(..., description="解析后的标准指令")
    standardized_instructions: List[str] = Field(default_factory=list, description="标准化指令列表")
    instruction_type: InstructionType = Field(..., description="指令类型")
    confidence: float = Field(..., ge=0.0, le=1.0, description="解析置信度")
    ambiguity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="模糊度评分")
    conflicts: List[str] = Field(default_factory=list, description="冲突列表")
    suggestions: List[str] = Field(default_factory=list, description="建议列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="解析时间")

class ConfidenceAssessment(BaseModel):
    """置信度评估结果"""
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="总体置信度")
    logic_score: float = Field(..., ge=0.0, le=1.0, description="逻辑合理性评分")
    market_match_score: float = Field(..., ge=0.0, le=1.0, description="市场环境匹配度")
    risk_reward_score: float = Field(..., ge=0.0, le=1.0, description="风险收益评分")
    historical_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="历史准确率")
    market_conditions: Dict[str, Any] = Field(default_factory=dict, description="市场条件")
    risk_factors: List[str] = Field(default_factory=list, description="风险因素")
    timestamp: datetime = Field(default_factory=datetime.now, description="评估时间")

class ModelVote(BaseModel):
    """模型投票结果"""
    model_id: str = Field(..., description="模型ID")
    decision: TradingDecision = Field(..., description="决策结果")
    weight: float = Field(..., ge=0.0, le=1.0, description="模型权重")
    performance_score: float = Field(..., ge=0.0, le=1.0, description="性能评分")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="一致性评分")

class ModelFusionResult(BaseModel):
    """多模型融合结果"""
    final_decision: TradingDecision = Field(..., description="最终决策")
    model_votes: List[ModelVote] = Field(..., description="模型投票列表")
    consensus_score: float = Field(..., ge=0.0, le=1.0, description="共识度评分")
    disagreement_factors: List[str] = Field(default_factory=list, description="分歧因素")
    fusion_method: str = Field(..., description="融合方法")
    timestamp: datetime = Field(default_factory=datetime.now, description="融合时间")

# SQLAlchemy模型 - 用于数据库存储
class AIDecisionRecords(Base):
    """AI决策记录表"""
    __tablename__ = 'ai_decision_records'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    decision_id = Column(String(50), unique=True, nullable=False, comment='决策ID')
    portfolio_id = Column(BigInteger, ForeignKey('portfolios.id'), comment='组合ID')
    symbol = Column(String(20), nullable=False, comment='股票代码')
    action = Column(String(10), nullable=False, comment='交易动作')
    quantity = Column(Integer, nullable=False, comment='交易数量')
    price = Column(Float, comment='交易价格')
    confidence = Column(Float, nullable=False, comment='置信度')
    reasoning = Column(Text, comment='决策理由')
    model_id = Column(String(50), nullable=False, comment='模型ID')
    
    # 扩展字段
    instruction_type = Column(String(20), comment='指令类型')
    execution_strategy = Column(String(20), comment='执行策略')
    risk_score = Column(Float, comment='风险评分')
    expected_return = Column(Float, comment='预期收益率')
    stop_loss = Column(Float, comment='止损价格')
    take_profit = Column(Float, comment='止盈价格')
    
    # 状态字段
    status = Column(String(20), default='pending', comment='决策状态')
    execution_result = Column(JSON, comment='执行结果')
    actual_return = Column(Float, comment='实际收益率')
    
    # 时间字段
    decision_time = Column(DateTime, nullable=False, comment='决策时间')
    execution_time = Column(DateTime, comment='执行时间')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    portfolio = relationship("Portfolios")
    
    # 索引
    __table_args__ = (
        Index('idx_ai_decision_portfolio_time', 'portfolio_id', 'decision_time'),
        Index('idx_ai_decision_symbol_time', 'symbol', 'decision_time'),
        Index('idx_ai_decision_model', 'model_id'),
        Index('idx_ai_decision_status', 'status'),
    )

class InstructionParseHistory(Base):
    """指令解析历史表"""
    __tablename__ = 'instruction_parse_history'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=False, comment='会话ID')
    original_instruction = Column(Text, nullable=False, comment='原始指令')
    parsed_instruction = Column(Text, comment='解析后指令')
    instruction_type = Column(String(20), comment='指令类型')
    parse_confidence = Column(Float, comment='解析置信度')
    ambiguity_score = Column(Float, comment='模糊度评分')
    conflicts = Column(JSON, comment='冲突列表')
    suggestions = Column(JSON, comment='建议列表')
    parse_time = Column(DateTime, nullable=False, comment='解析时间')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_parse_session_time', 'session_id', 'parse_time'),
        Index('idx_parse_type', 'instruction_type'),
    )

class ConfidenceAssessmentHistory(Base):
    """置信度评估历史表"""
    __tablename__ = 'confidence_assessment_history'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    decision_id = Column(String(50), ForeignKey('ai_decision_records.decision_id'), comment='决策ID')
    overall_confidence = Column(Float, nullable=False, comment='总体置信度')
    logic_score = Column(Float, comment='逻辑合理性评分')
    market_match_score = Column(Float, comment='市场环境匹配度')
    risk_reward_score = Column(Float, comment='风险收益评分')
    historical_accuracy = Column(Float, comment='历史准确率')
    market_conditions = Column(JSON, comment='市场条件')
    risk_factors = Column(JSON, comment='风险因素')
    assessment_time = Column(DateTime, nullable=False, comment='评估时间')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    
    # 关系
    decision_record = relationship("AIDecisionRecords")
    
    # 索引
    __table_args__ = (
        Index('idx_confidence_decision', 'decision_id'),
        Index('idx_confidence_time', 'assessment_time'),
    )

class ModelFusionHistory(Base):
    """模型融合历史表"""
    __tablename__ = 'model_fusion_history'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fusion_id = Column(String(50), unique=True, nullable=False, comment='融合ID')
    decision_id = Column(String(50), ForeignKey('ai_decision_records.decision_id'), comment='决策ID')
    model_votes = Column(JSON, nullable=False, comment='模型投票结果')
    consensus_score = Column(Float, comment='共识度评分')
    disagreement_factors = Column(JSON, comment='分歧因素')
    fusion_method = Column(String(50), comment='融合方法')
    final_weights = Column(JSON, comment='最终权重')
    fusion_time = Column(DateTime, nullable=False, comment='融合时间')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    
    # 关系
    decision_record = relationship("AIDecisionRecords")
    
    # 索引
    __table_args__ = (
        Index('idx_fusion_decision', 'decision_id'),
        Index('idx_fusion_time', 'fusion_time'),
        Index('idx_fusion_method', 'fusion_method'),
    )

class ModelPerformanceMetrics(Base):
    """模型性能指标表"""
    __tablename__ = 'model_performance_metrics'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    model_id = Column(String(50), nullable=False, comment='模型ID')
    metric_date = Column(String(8), nullable=False, comment='指标日期')
    total_decisions = Column(Integer, default=0, comment='总决策数')
    correct_decisions = Column(Integer, default=0, comment='正确决策数')
    accuracy_rate = Column(Float, comment='准确率')
    avg_confidence = Column(Float, comment='平均置信度')
    avg_return = Column(Float, comment='平均收益率')
    sharpe_ratio = Column(Float, comment='夏普比率')
    max_drawdown = Column(Float, comment='最大回撤')
    win_rate = Column(Float, comment='胜率')
    profit_factor = Column(Float, comment='盈利因子')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_model_perf_model_date', 'model_id', 'metric_date'),
        Index('idx_model_perf_date', 'metric_date'),
    )