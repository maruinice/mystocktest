# -*- coding: utf-8 -*-
"""
Model Management SQLAlchemy models (cleaned ASCII version).
This file removes corrupted docstrings/comments and preserves schema used by APIs.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, BigInteger, DECIMAL, Text, JSON,
    DateTime, Date, Boolean, Enum, ForeignKey, Index, UniqueConstraint, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

Base = declarative_base()

# =============================
# Enums
# =============================

class ModelType(PyEnum):
    DeepSeek = "DeepSeek"
    ChatGPT = "ChatGPT"
    Claude = "Claude"
    Llama = "Llama"
    Custom = "Custom"
    Ensemble = "Ensemble"

class ModelStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class HealthStatus(PyEnum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"

class WeightStrategy(PyEnum):
    EQUAL_WEIGHT = "equal_weight"
    ACCURACY_WEIGHT = "accuracy_weight"
    MANUAL_WEIGHT = "manual_weight"
    DYNAMIC_WEIGHT = "dynamic_weight"
    PERFORMANCE_WEIGHT = "performance_weight"

class VotingMethod(PyEnum):
    MAJORITY = "majority"
    WEIGHTED = "weighted"
    CONFIDENCE = "confidence"
    THRESHOLD = "threshold"

class TestType(PyEnum):
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    ACCURACY = "accuracy"
    STRESS = "stress"

class TimePeriod(PyEnum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

# =============================
# Core Tables
# =============================

class AIModel(Base):
    __tablename__ = 'ai_models'

    # Basic info
    model_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(150))
    description = Column(Text)

    # Type and provider
    model_type = Column(Enum(ModelType), nullable=False)
    provider = Column(String(50), nullable=False)
    model_version = Column(String(50))

    # API config
    api_key_encrypted = Column(Text)
    base_url = Column(String(500))
    api_endpoint = Column(String(200))

    # Parameters
    max_tokens = Column(Integer, default=4096)
    temperature = Column(DECIMAL(3, 2), default=Decimal('0.70'))
    top_p = Column(DECIMAL(3, 2), default=Decimal('1.00'))
    frequency_penalty = Column(DECIMAL(3, 2), default=Decimal('0.00'))
    presence_penalty = Column(DECIMAL(3, 2), default=Decimal('0.00'))

    # Metrics
    accuracy_rate = Column(DECIMAL(5, 4), default=Decimal('0.0000'))
    weight = Column(DECIMAL(5, 4), default=Decimal('1.0000'))
    avg_response_time = Column(Integer, default=0)
    success_rate = Column(DECIMAL(5, 4), default=Decimal('0.0000'))

    # Status
    # 直接使用字符串枚举值，匹配数据库中的小写枚举值
    status = Column(
        Enum('active', 'inactive', 'training', 'error', 'maintenance', name='model_status_enum'),
        nullable=False,
        default='inactive'
    )
    enabled = Column(Boolean, nullable=False, default=False)
    health_status = Column(
        Enum(
            HealthStatus,
            values_callable=lambda enum: [e.value for e in enum],
            name='healthstatus'
        ),
        default=HealthStatus.UNKNOWN
    )

    # Usage stats
    total_requests = Column(BigInteger, default=0)
    total_tokens_used = Column(BigInteger, default=0)
    last_used_at = Column(DateTime)

    # Training info
    last_trained_at = Column(DateTime)
    training_data_version = Column(String(50))
    training_status = Column(Enum('not_trained', 'training', 'completed', 'failed', name='training_status_enum'), default='not_trained')

    # Ext config
    config_json = Column(JSON)
    tags = Column(JSON)

    # Audit
    created_by = Column(String(50))
    updated_by = Column(String(50))
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    api_keys = relationship("ModelAPIKey", back_populates="model", cascade="all, delete-orphan")
    test_records = relationship("ModelTestRecord", back_populates="model", cascade="all, delete-orphan")
    metrics = relationship("ModelMetric", back_populates="model", cascade="all, delete-orphan")
    usage_logs = relationship("ModelUsageLog", back_populates="model", cascade="all, delete-orphan")
    ensemble_mappings = relationship("EnsembleModelMapping", back_populates="model", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_models_type', 'model_type'),
        Index('idx_models_provider', 'provider'),
        Index('idx_models_status', 'status'),
        Index('idx_models_enabled', 'enabled'),
        Index('idx_models_created_at', 'created_at'),
        Index('idx_models_accuracy', 'accuracy_rate'),
        Index('idx_models_last_used', 'last_used_at'),
    )


class ModelEnsemble(Base):
    __tablename__ = 'model_ensembles'

    ensemble_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(150))
    description = Column(Text)

    weight_strategy = Column(
        Enum(WeightStrategy, values_callable=lambda enum: [e.value for e in enum], name='weightstrategy'),
        nullable=False,
        default=WeightStrategy.EQUAL_WEIGHT
    )
    voting_method = Column(
        Enum(VotingMethod, values_callable=lambda enum: [e.value for e in enum], name='votingmethod'),
        default=VotingMethod.WEIGHTED
    )
    confidence_threshold = Column(DECIMAL(3, 2), default=Decimal('0.50'))

    overall_accuracy = Column(DECIMAL(5, 4), default=Decimal('0.0000'))
    model_count = Column(Integer, default=0)
    active_model_count = Column(Integer, default=0)
    avg_response_time = Column(Integer, default=0)

    status = Column(Enum('active', 'inactive', 'configuring', 'error', name='ensemble_status_enum'), nullable=False, default='inactive')
    enabled = Column(Boolean, nullable=False, default=False)
    health_status = Column(
        Enum(HealthStatus, values_callable=lambda enum: [e.value for e in enum], name='healthstatus'),
        default=HealthStatus.UNKNOWN
    )

    total_requests = Column(BigInteger, default=0)
    success_requests = Column(BigInteger, default=0)
    last_used_at = Column(DateTime)

    config_json = Column(JSON)
    tags = Column(JSON)

    created_by = Column(String(50))
    updated_by = Column(String(50))
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    model_mappings = relationship("EnsembleModelMapping", back_populates="ensemble", cascade="all, delete-orphan")
    test_records = relationship("ModelTestRecord", back_populates="ensemble", cascade="all, delete-orphan")
    metrics = relationship("ModelMetric", back_populates="ensemble", cascade="all, delete-orphan")
    usage_logs = relationship("ModelUsageLog", back_populates="ensemble", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_ensembles_strategy', 'weight_strategy'),
        Index('idx_ensembles_status', 'status'),
        Index('idx_ensembles_enabled', 'enabled'),
        Index('idx_ensembles_accuracy', 'overall_accuracy'),
        Index('idx_ensembles_created_at', 'created_at'),
    )


class EnsembleModelMapping(Base):
    __tablename__ = 'ensemble_model_mapping'

    mapping_id = Column(String(50), primary_key=True)
    ensemble_id = Column(String(50), ForeignKey('model_ensembles.ensemble_id', ondelete='CASCADE'), nullable=False)
    model_id = Column(String(50), ForeignKey('ai_models.model_id', ondelete='CASCADE'), nullable=False)

    weight = Column(DECIMAL(5, 4), nullable=False, default=Decimal('1.0000'))
    priority = Column(Integer, default=1)
    order_index = Column(Integer, default=0)

    enabled = Column(Boolean, nullable=False, default=True)
    status = Column(Enum('active', 'inactive', 'error', name='mapping_status_enum'), default='active')

    contribution_score = Column(DECIMAL(5, 4), default=Decimal('0.0000'))
    usage_count = Column(BigInteger, default=0)
    last_used_at = Column(DateTime)

    config_json = Column(JSON)

    created_by = Column(String(50))
    updated_by = Column(String(50))
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    ensemble = relationship("ModelEnsemble", back_populates="model_mappings")
    model = relationship("AIModel", back_populates="ensemble_mappings")

    __table_args__ = (
        UniqueConstraint('ensemble_id', 'model_id', name='uk_ensemble_model'),
        Index('idx_mapping_ensemble', 'ensemble_id'),
        Index('idx_mapping_model', 'model_id'),
        Index('idx_mapping_weight', 'weight'),
        Index('idx_mapping_priority', 'priority'),
        Index('idx_mapping_enabled', 'enabled'),
    )


class ModelTestRecord(Base):
    __tablename__ = 'model_test_records'

    test_id = Column(String(50), primary_key=True)
    model_id = Column(String(50), ForeignKey('ai_models.model_id', ondelete='CASCADE'), nullable=False)
    ensemble_id = Column(String(50), ForeignKey('model_ensembles.ensemble_id', ondelete='CASCADE'))

    # 统一枚举值存储为小写字符串
    test_type = Column(
        Enum(TestType, values_callable=lambda enum: [e.value for e in enum], name='testtype')
        , nullable=False
    )
    test_name = Column(String(200))
    test_description = Column(Text)

    input_data = Column(JSON, nullable=False)
    expected_output = Column(JSON)
    actual_output = Column(JSON)

    response_time_ms = Column(Integer)
    token_count = Column(Integer)
    success = Column(Boolean, nullable=False, default=False)
    accuracy_score = Column(DECIMAL(5, 4))

    error_code = Column(String(50))
    error_message = Column(Text)
    error_details = Column(JSON)

    test_environment = Column(String(100))
    test_version = Column(String(50))
    batch_id = Column(String(50))

    tested_by = Column(String(50))
    created_at = Column(DateTime, nullable=False, default=func.now())

    model = relationship("AIModel", back_populates="test_records")
    ensemble = relationship("ModelEnsemble", back_populates="test_records")

    __table_args__ = (
        Index('idx_test_model', 'model_id'),
        Index('idx_test_ensemble', 'ensemble_id'),
        Index('idx_test_type', 'test_type'),
        Index('idx_test_success', 'success'),
        Index('idx_test_created_at', 'created_at'),
        Index('idx_test_batch', 'batch_id'),
        Index('idx_test_response_time', 'response_time_ms'),
    )


class ModelMetric(Base):
    __tablename__ = 'model_metrics'

    metric_id = Column(String(50), primary_key=True)
    model_id = Column(String(50), ForeignKey('ai_models.model_id', ondelete='CASCADE'), nullable=False)
    ensemble_id = Column(String(50), ForeignKey('model_ensembles.ensemble_id', ondelete='CASCADE'))

    metric_date = Column(Date, nullable=False)
    metric_hour = Column(Integer)
    time_period = Column(
        Enum(TimePeriod, values_callable=lambda enum: [e.value for e in enum], name='timeperiod'),
        nullable=False,
        default=TimePeriod.DAILY
    )

    accuracy_rate = Column(DECIMAL(5, 4), default=Decimal('0.0000'))
    avg_response_time_ms = Column(Integer, default=0)
    success_rate = Column(DECIMAL(5, 4), default=Decimal('0.0000'))
    error_rate = Column(DECIMAL(5, 4), default=Decimal('0.0000'))

    total_requests = Column(BigInteger, default=0)
    successful_requests = Column(BigInteger, default=0)
    failed_requests = Column(BigInteger, default=0)
    total_tokens_used = Column(BigInteger, default=0)

    response_time_p50 = Column(Integer)
    response_time_p90 = Column(Integer)
    response_time_p95 = Column(Integer)
    response_time_p99 = Column(Integer)

    estimated_cost = Column(DECIMAL(10, 4), default=Decimal('0.0000'))
    cost_per_request = Column(DECIMAL(8, 6), default=Decimal('0.000000'))

    confidence_score = Column(DECIMAL(5, 4))
    consistency_score = Column(DECIMAL(5, 4))
    relevance_score = Column(DECIMAL(5, 4))

    custom_metrics = Column(JSON)

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    model = relationship("AIModel", back_populates="metrics")
    ensemble = relationship("ModelEnsemble", back_populates="metrics")

    __table_args__ = (
        UniqueConstraint('model_id', 'metric_date', 'time_period', 'metric_hour', name='uk_metrics_model_date_period'),
        Index('idx_metrics_model', 'model_id'),
        Index('idx_metrics_ensemble', 'ensemble_id'),
        Index('idx_metrics_date', 'metric_date'),
        Index('idx_metrics_period', 'time_period'),
        Index('idx_metrics_accuracy', 'accuracy_rate'),
        Index('idx_metrics_response_time', 'avg_response_time_ms'),
        Index('idx_metrics_success_rate', 'success_rate'),
        Index('idx_metrics_created_at', 'created_at'),
    )


class ModelAPIKey(Base):
    __tablename__ = 'model_api_keys'

    key_id = Column(String(50), primary_key=True)
    model_id = Column(String(50), ForeignKey('ai_models.model_id', ondelete='CASCADE'), nullable=False)

    key_name = Column(String(100), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    key_hash = Column(String(64), nullable=False)
    encryption_method = Column(String(50), default='AES-256-GCM')

    rate_limit_per_minute = Column(Integer)
    rate_limit_per_day = Column(Integer)
    monthly_quota = Column(BigInteger)
    used_quota = Column(BigInteger, default=0)

    status = Column(Enum('active', 'inactive', 'expired', 'revoked', name='key_status_enum'), nullable=False, default='active')
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)

    created_by = Column(String(50))
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    model = relationship("AIModel", back_populates="api_keys")

    __table_args__ = (
        UniqueConstraint('model_id', 'key_name', name='uk_api_keys_model_name'),
        Index('idx_api_keys_model', 'model_id'),
        Index('idx_api_keys_status', 'status'),
        Index('idx_api_keys_expires', 'expires_at'),
    )


class ModelUsageLog(Base):
    __tablename__ = 'model_usage_logs'

    log_id = Column(String(50), primary_key=True)
    model_id = Column(String(50), ForeignKey('ai_models.model_id', ondelete='CASCADE'), nullable=False)
    ensemble_id = Column(String(50), ForeignKey('model_ensembles.ensemble_id', ondelete='CASCADE'))

    request_id = Column(String(50))
    user_id = Column(String(50))
    session_id = Column(String(100))

    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    response_time_ms = Column(Integer)

    success = Column(Boolean, nullable=False, default=False)
    error_code = Column(String(50))
    error_message = Column(Text)

    estimated_cost = Column(DECIMAL(8, 6), default=Decimal('0.000000'))

    created_at = Column(DateTime, nullable=False, default=func.now())

    model = relationship("AIModel", back_populates="usage_logs")
    ensemble = relationship("ModelEnsemble", back_populates="usage_logs")

    __table_args__ = (
        Index('idx_usage_logs_model', 'model_id'),
        Index('idx_usage_logs_ensemble', 'ensemble_id'),
        Index('idx_usage_logs_user', 'user_id'),
        Index('idx_usage_logs_success', 'success'),
        Index('idx_usage_logs_created_at', 'created_at'),
        Index('idx_usage_logs_request', 'request_id'),
    )