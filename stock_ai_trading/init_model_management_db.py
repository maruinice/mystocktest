#!/usr/bin/env python3
"""
模型管理系统数据库初始化脚本
用于创建数据库表结构和插入初始数据
"""

import os
import sys
import logging
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.model_management import (
    Base, AIModel, ModelEnsemble, EnsembleModelMapping, 
    ModelTestRecord, ModelMetric, ModelAPIKey, ModelUsageLog,
    ModelType, ModelStatus, HealthStatus, WeightStrategy, VotingMethod
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/stock_ai_trading?charset=utf8mb4"

def create_database_engine():
    """创建数据库引擎"""
    try:
        engine = create_engine(
            DATABASE_URL,
            echo=True,  # 打印SQL语句
            pool_pre_ping=True,  # 连接池预检查
            pool_recycle=3600,   # 连接回收时间
            encoding='utf-8'
        )
        return engine
    except Exception as e:
        logger.error(f"创建数据库引擎失败: {e}")
        raise

def create_tables(engine):
    """创建数据库表"""
    try:
        logger.info("开始创建数据库表...")
        Base.metadata.create_all(engine)
        logger.info("数据库表创建成功")
    except SQLAlchemyError as e:
        logger.error(f"创建数据库表失败: {e}")
        raise

def insert_sample_data(session):
    """插入示例数据"""
    try:
        logger.info("开始插入示例数据...")
        
        # 1. 插入AI模型数据
        models = [
            AIModel(
                model_id='deepseek_chat_001',
                name='DeepSeek Chat',
                display_name='DeepSeek 对话模型',
                description='高性能对话生成模型，支持中英文对话',
                model_type=ModelType.DEEPSEEK,
                provider='deepseek',
                model_version='v1.0',
                base_url='https://api.deepseek.com',
                max_tokens=4096,
                temperature=Decimal('0.70'),
                accuracy_rate=Decimal('0.8500'),
                weight=Decimal('1.0000'),
                status=ModelStatus.ACTIVE,
                enabled=True,
                health_status=HealthStatus.HEALTHY,
                created_by='system'
            ),
            AIModel(
                model_id='gpt4_turbo_001',
                name='GPT-4 Turbo',
                display_name='OpenAI GPT-4 Turbo',
                description='最新的GPT-4 Turbo模型，具有更强的推理能力',
                model_type=ModelType.CHATGPT,
                provider='openai',
                model_version='gpt-4-turbo',
                base_url='https://api.openai.com',
                max_tokens=8192,
                temperature=Decimal('0.70'),
                accuracy_rate=Decimal('0.9200'),
                weight=Decimal('1.0000'),
                status=ModelStatus.ACTIVE,
                enabled=True,
                health_status=HealthStatus.HEALTHY,
                created_by='system'
            ),
            AIModel(
                model_id='claude3_opus_001',
                name='Claude-3 Opus',
                display_name='Anthropic Claude-3 Opus',
                description='高质量推理模型，擅长复杂任务处理',
                model_type=ModelType.CLAUDE,
                provider='anthropic',
                model_version='claude-3-opus',
                base_url='https://api.anthropic.com',
                max_tokens=4096,
                temperature=Decimal('0.70'),
                accuracy_rate=Decimal('0.9000'),
                weight=Decimal('1.0000'),
                status=ModelStatus.ACTIVE,
                enabled=True,
                health_status=HealthStatus.HEALTHY,
                created_by='system'
            ),
            AIModel(
                model_id='llama2_70b_001',
                name='Llama-2 70B',
                display_name='Meta Llama-2 70B',
                description='开源大语言模型，适合本地部署',
                model_type=ModelType.LLAMA,
                provider='meta',
                model_version='llama-2-70b',
                base_url='http://localhost:8080',
                max_tokens=4096,
                temperature=Decimal('0.70'),
                accuracy_rate=Decimal('0.8200'),
                weight=Decimal('1.0000'),
                status=ModelStatus.INACTIVE,
                enabled=False,
                health_status=HealthStatus.UNKNOWN,
                created_by='system'
            ),
            AIModel(
                model_id='custom_model_001',
                name='Custom Finance Model',
                display_name='自定义金融模型',
                description='专门针对金融领域优化的自定义模型',
                model_type=ModelType.CUSTOM,
                provider='custom',
                model_version='v1.0',
                base_url='http://localhost:9000',
                max_tokens=2048,
                temperature=Decimal('0.50'),
                accuracy_rate=Decimal('0.8800'),
                weight=Decimal('1.0000'),
                status=ModelStatus.TRAINING,
                enabled=False,
                health_status=HealthStatus.WARNING,
                created_by='system'
            )
        ]
        
        for model in models:
            session.add(model)
        
        # 2. 插入模型组合数据
        ensembles = [
            ModelEnsemble(
                ensemble_id='ensemble_premium_001',
                name='Premium Ensemble',
                display_name='高级模型组合',
                description='包含最优秀模型的组合，适合高质量任务',
                weight_strategy=WeightStrategy.ACCURACY_WEIGHT,
                voting_method=VotingMethod.WEIGHTED,
                confidence_threshold=Decimal('0.80'),
                overall_accuracy=Decimal('0.9100'),
                model_count=3,
                active_model_count=3,
                status='active',
                enabled=True,
                health_status=HealthStatus.HEALTHY,
                created_by='system'
            ),
            ModelEnsemble(
                ensemble_id='ensemble_balanced_001',
                name='Balanced Ensemble',
                display_name='平衡模型组合',
                description='性能与成本平衡的组合，适合日常使用',
                weight_strategy=WeightStrategy.EQUAL_WEIGHT,
                voting_method=VotingMethod.MAJORITY,
                confidence_threshold=Decimal('0.60'),
                overall_accuracy=Decimal('0.8700'),
                model_count=2,
                active_model_count=2,
                status='active',
                enabled=True,
                health_status=HealthStatus.HEALTHY,
                created_by='system'
            ),
            ModelEnsemble(
                ensemble_id='ensemble_experimental_001',
                name='Experimental Ensemble',
                display_name='实验性组合',
                description='用于测试新模型和策略的实验性组合',
                weight_strategy=WeightStrategy.DYNAMIC_WEIGHT,
                voting_method=VotingMethod.CONFIDENCE,
                confidence_threshold=Decimal('0.70'),
                overall_accuracy=Decimal('0.8300'),
                model_count=4,
                active_model_count=2,
                status='configuring',
                enabled=False,
                health_status=HealthStatus.WARNING,
                created_by='system'
            )
        ]
        
        for ensemble in ensembles:
            session.add(ensemble)
        
        # 提交模型和组合数据
        session.commit()
        
        # 3. 插入组合模型关联数据
        mappings = [
            # Premium Ensemble 的模型关联
            EnsembleModelMapping(
                mapping_id='mapping_001',
                ensemble_id='ensemble_premium_001',
                model_id='gpt4_turbo_001',
                weight=Decimal('0.4000'),
                priority=1,
                order_index=1,
                enabled=True,
                status='active',
                created_by='system'
            ),
            EnsembleModelMapping(
                mapping_id='mapping_002',
                ensemble_id='ensemble_premium_001',
                model_id='claude3_opus_001',
                weight=Decimal('0.3500'),
                priority=2,
                order_index=2,
                enabled=True,
                status='active',
                created_by='system'
            ),
            EnsembleModelMapping(
                mapping_id='mapping_003',
                ensemble_id='ensemble_premium_001',
                model_id='deepseek_chat_001',
                weight=Decimal('0.2500'),
                priority=3,
                order_index=3,
                enabled=True,
                status='active',
                created_by='system'
            ),
            # Balanced Ensemble 的模型关联
            EnsembleModelMapping(
                mapping_id='mapping_004',
                ensemble_id='ensemble_balanced_001',
                model_id='deepseek_chat_001',
                weight=Decimal('0.5000'),
                priority=1,
                order_index=1,
                enabled=True,
                status='active',
                created_by='system'
            ),
            EnsembleModelMapping(
                mapping_id='mapping_005',
                ensemble_id='ensemble_balanced_001',
                model_id='gpt4_turbo_001',
                weight=Decimal('0.5000'),
                priority=2,
                order_index=2,
                enabled=True,
                status='active',
                created_by='system'
            ),
            # Experimental Ensemble 的模型关联
            EnsembleModelMapping(
                mapping_id='mapping_006',
                ensemble_id='ensemble_experimental_001',
                model_id='custom_model_001',
                weight=Decimal('0.3000'),
                priority=1,
                order_index=1,
                enabled=True,
                status='active',
                created_by='system'
            ),
            EnsembleModelMapping(
                mapping_id='mapping_007',
                ensemble_id='ensemble_experimental_001',
                model_id='llama2_70b_001',
                weight=Decimal('0.2000'),
                priority=2,
                order_index=2,
                enabled=False,
                status='inactive',
                created_by='system'
            )
        ]
        
        for mapping in mappings:
            session.add(mapping)
        
        # 4. 插入性能指标数据
        today = date.today()
        metrics = [
            ModelMetric(
                metric_id=f'metric_deepseek_chat_001_{today.strftime("%Y%m%d")}',
                model_id='deepseek_chat_001',
                metric_date=today,
                time_period='daily',
                accuracy_rate=Decimal('0.8500'),
                avg_response_time_ms=1200,
                success_rate=Decimal('0.9800'),
                error_rate=Decimal('0.0200'),
                total_requests=1500,
                successful_requests=1470,
                failed_requests=30,
                total_tokens_used=45000,
                response_time_p50=1000,
                response_time_p90=1800,
                response_time_p95=2200,
                response_time_p99=3000,
                estimated_cost=Decimal('12.5000'),
                cost_per_request=Decimal('0.008333')
            ),
            ModelMetric(
                metric_id=f'metric_gpt4_turbo_001_{today.strftime("%Y%m%d")}',
                model_id='gpt4_turbo_001',
                metric_date=today,
                time_period='daily',
                accuracy_rate=Decimal('0.9200'),
                avg_response_time_ms=2000,
                success_rate=Decimal('0.9900'),
                error_rate=Decimal('0.0100'),
                total_requests=800,
                successful_requests=792,
                failed_requests=8,
                total_tokens_used=32000,
                response_time_p50=1800,
                response_time_p90=2800,
                response_time_p95=3200,
                response_time_p99=4000,
                estimated_cost=Decimal('48.0000'),
                cost_per_request=Decimal('0.060000')
            ),
            ModelMetric(
                metric_id=f'metric_claude3_opus_001_{today.strftime("%Y%m%d")}',
                model_id='claude3_opus_001',
                metric_date=today,
                time_period='daily',
                accuracy_rate=Decimal('0.9000'),
                avg_response_time_ms=1800,
                success_rate=Decimal('0.9850'),
                error_rate=Decimal('0.0150'),
                total_requests=600,
                successful_requests=591,
                failed_requests=9,
                total_tokens_used=24000,
                response_time_p50=1600,
                response_time_p90=2400,
                response_time_p95=2800,
                response_time_p99=3500,
                estimated_cost=Decimal('36.0000'),
                cost_per_request=Decimal('0.060000')
            )
        ]
        
        for metric in metrics:
            session.add(metric)
        
        # 5. 插入API密钥数据 (示例，实际使用时需要加密)
        api_keys = [
            ModelAPIKey(
                key_id='key_deepseek_001',
                model_id='deepseek_chat_001',
                key_name='DeepSeek Primary Key',
                encrypted_key='encrypted_key_placeholder_1',
                key_hash='hash_placeholder_1',
                rate_limit_per_minute=60,
                rate_limit_per_day=10000,
                monthly_quota=300000,
                used_quota=45000,
                status='active',
                created_by='system'
            ),
            ModelAPIKey(
                key_id='key_openai_001',
                model_id='gpt4_turbo_001',
                key_name='OpenAI Primary Key',
                encrypted_key='encrypted_key_placeholder_2',
                key_hash='hash_placeholder_2',
                rate_limit_per_minute=30,
                rate_limit_per_day=5000,
                monthly_quota=150000,
                used_quota=32000,
                status='active',
                created_by='system'
            )
        ]
        
        for api_key in api_keys:
            session.add(api_key)
        
        # 提交所有数据
        session.commit()
        logger.info("示例数据插入成功")
        
    except SQLAlchemyError as e:
        logger.error(f"插入示例数据失败: {e}")
        session.rollback()
        raise

def verify_data(session):
    """验证数据插入"""
    try:
        logger.info("开始验证数据...")
        
        # 验证模型数据
        model_count = session.query(AIModel).count()
        logger.info(f"AI模型数量: {model_count}")
        
        # 验证组合数据
        ensemble_count = session.query(ModelEnsemble).count()
        logger.info(f"模型组合数量: {ensemble_count}")
        
        # 验证关联数据
        mapping_count = session.query(EnsembleModelMapping).count()
        logger.info(f"组合关联数量: {mapping_count}")
        
        # 验证指标数据
        metric_count = session.query(ModelMetric).count()
        logger.info(f"性能指标数量: {metric_count}")
        
        # 验证API密钥数据
        key_count = session.query(ModelAPIKey).count()
        logger.info(f"API密钥数量: {key_count}")
        
        # 查询一些示例数据
        active_models = session.query(AIModel).filter(AIModel.status == ModelStatus.ACTIVE).all()
        logger.info(f"活跃模型: {[model.name for model in active_models]}")
        
        active_ensembles = session.query(ModelEnsemble).filter(ModelEnsemble.enabled == True).all()
        logger.info(f"启用的组合: {[ensemble.name for ensemble in active_ensembles]}")
        
        logger.info("数据验证完成")
        
    except SQLAlchemyError as e:
        logger.error(f"数据验证失败: {e}")
        raise

def main():
    """主函数"""
    try:
        logger.info("开始初始化模型管理系统数据库...")
        
        # 创建数据库引擎
        engine = create_database_engine()
        
        # 创建数据库表
        create_tables(engine)
        
        # 创建会话
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # 插入示例数据
            insert_sample_data(session)
            
            # 验证数据
            verify_data(session)
            
            logger.info("模型管理系统数据库初始化完成！")
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()