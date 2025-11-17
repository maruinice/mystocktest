"""
模型服务管理器
提供统一的服务层接口，整合所有模型相关服务
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .model_connection_service import (
    ModelConnectionService, ModelConfig, ModelType, ModelResponse,
    model_connection_service
)
from .weight_management_service import (
    WeightManagementService, WeightStrategy, ModelWeight, ModelPerformance,
    weight_management_service
)
from .model_testing_service import (
    ModelTestingService, TestCase, TestType, TestSession,
    create_model_testing_service
)
from .performance_monitoring_service import (
    PerformanceMonitoringService, AlertLevel, MetricType,
    performance_monitoring_service
)
from .model_fusion import (
    ModelFusionService, EnsembleConfig, FusionStrategy, FailureStrategy,
    create_model_fusion_service
)
from .encryption_service import encryption_service

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """服务状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class ServiceHealth:
    """服务健康状态"""
    service_name: str
    status: ServiceStatus
    last_check: datetime
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None

class ModelServiceManager:
    """模型服务管理器"""
    
    def __init__(self):
        # 核心服务实例
        self.connection_service = model_connection_service
        self.weight_service = weight_management_service
        self.monitoring_service = performance_monitoring_service
        
        # 依赖注入的服务
        self.testing_service: Optional[ModelTestingService] = None
        self.fusion_service: Optional[ModelFusionService] = None
        
        # 服务状态
        self.status = ServiceStatus.INITIALIZING
        self.initialized = False
        
        # 配置
        self.config = {
            "auto_monitoring": True,
            "default_timeout": 30.0,
            "max_concurrent_requests": 10,
            "enable_fallback": True,
            "log_level": "INFO"
        }
    
    async def initialize(self) -> bool:
        """初始化服务管理器"""
        try:
            logger.info("Initializing Model Service Manager...")
            
            # 创建依赖注入的服务
            self.testing_service = create_model_testing_service(
                self.connection_service, 
                self.weight_service
            )
            
            self.fusion_service = create_model_fusion_service(
                self.connection_service,
                self.weight_service,
                self.monitoring_service
            )
            
            # 启用监控
            if self.config["auto_monitoring"]:
                self.monitoring_service.set_monitoring_enabled(True)
            
            self.status = ServiceStatus.RUNNING
            self.initialized = True
            
            logger.info("Model Service Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Model Service Manager: {e}")
            self.status = ServiceStatus.ERROR
            return False
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self.initialized and self.status == ServiceStatus.RUNNING
    
    # =====================================================
    # 模型连接管理接口
    # =====================================================
    
    def register_model(
        self,
        model_id: str,
        model_type: Union[ModelType, str],
        name: str,
        api_key: str,
        base_url: str,
        **kwargs
    ) -> bool:
        """注册模型"""
        try:
            # 类型转换
            if isinstance(model_type, str):
                model_type = ModelType(model_type)
            
            # 加密API密钥
            encrypted_key = encryption_service.encrypt(api_key)
            
            # 创建配置
            config = ModelConfig(
                model_id=model_id,
                model_type=model_type,
                name=name,
                api_key=encrypted_key,
                base_url=base_url,
                **kwargs
            )
            
            return self.connection_service.register_model(config)
            
        except Exception as e:
            logger.error(f"Failed to register model {model_id}: {e}")
            return False
    
    def unregister_model(self, model_id: str) -> bool:
        """注销模型"""
        success = self.connection_service.unregister_model(model_id)
        if success:
            # 清理相关数据
            self.monitoring_service.reset_model_stats(model_id)
        return success
    
    def list_models(self) -> List[str]:
        """列出所有模型"""
        return self.connection_service.list_models()
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        return self.connection_service.get_model_info(model_id)
    
    async def test_model_connection(self, model_id: str) -> bool:
        """测试模型连接"""
        return await self.connection_service.test_connection(model_id)
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """测试所有模型连接"""
        return await self.connection_service.test_all_connections()
    
    # =====================================================
    # 模型请求接口
    # =====================================================
    
    async def send_message(
        self, 
        model_id: str, 
        message: str,
        **kwargs
    ) -> ModelResponse:
        """发送消息到单个模型"""
        if not self.is_initialized():
            return ModelResponse(
                success=False,
                error_message="Service not initialized",
                error_code="SERVICE_NOT_READY"
            )
        
        return await self.connection_service.send_message(model_id, message, **kwargs)
    
    async def send_ensemble_message(
        self,
        ensemble_id: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送消息到模型集成"""
        if not self.is_initialized() or not self.fusion_service:
            return {
                "success": False,
                "error": "Service not initialized or fusion service unavailable"
            }
        
        result = await self.fusion_service.process_ensemble_request(
            ensemble_id, message, **kwargs
        )
        
        return {
            "success": result.success,
            "content": result.content,
            "confidence": result.confidence,
            "fusion_strategy": result.fusion_strategy.value,
            "total_response_time": result.total_response_time,
            "individual_results": [
                {
                    "model_id": r.model_id,
                    "success": r.response.success,
                    "response_time": r.response_time,
                    "weight": r.weight
                }
                for r in result.individual_results
            ],
            "metadata": result.metadata
        }
    
    # =====================================================
    # 集成管理接口
    # =====================================================
    
    def create_ensemble(
        self,
        ensemble_id: str,
        name: str,
        model_ids: List[str],
        fusion_strategy: Union[FusionStrategy, str] = FusionStrategy.WEIGHTED_VOTING,
        weight_strategy: Union[WeightStrategy, str] = WeightStrategy.EQUAL,
        **kwargs
    ) -> bool:
        """创建模型集成"""
        if not self.is_initialized() or not self.fusion_service:
            return False
        
        try:
            # 类型转换
            if isinstance(fusion_strategy, str):
                fusion_strategy = FusionStrategy(fusion_strategy)
            if isinstance(weight_strategy, str):
                weight_strategy = WeightStrategy(weight_strategy)
            
            config = EnsembleConfig(
                ensemble_id=ensemble_id,
                name=name,
                model_ids=model_ids,
                fusion_strategy=fusion_strategy,
                weight_strategy=weight_strategy,
                **kwargs
            )
            
            return self.fusion_service.register_ensemble(config)
            
        except Exception as e:
            logger.error(f"Failed to create ensemble {ensemble_id}: {e}")
            return False
    
    def delete_ensemble(self, ensemble_id: str) -> bool:
        """删除模型集成"""
        if not self.fusion_service:
            return False
        return self.fusion_service.unregister_ensemble(ensemble_id)
    
    def list_ensembles(self) -> List[str]:
        """列出所有集成"""
        if not self.fusion_service:
            return []
        return self.fusion_service.list_ensembles()
    
    def get_ensemble_config(self, ensemble_id: str) -> Optional[Dict[str, Any]]:
        """获取集成配置"""
        if not self.fusion_service:
            return None
        
        config = self.fusion_service.get_ensemble_config(ensemble_id)
        if not config:
            return None
        
        return {
            "ensemble_id": config.ensemble_id,
            "name": config.name,
            "model_ids": config.model_ids,
            "fusion_strategy": config.fusion_strategy.value,
            "weight_strategy": config.weight_strategy.value,
            "failure_strategy": config.failure_strategy.value,
            "confidence_threshold": config.confidence_threshold,
            "timeout": config.timeout,
            "max_retries": config.max_retries,
            "enable_fallback": config.enable_fallback,
            "metadata": config.metadata
        }
    
    def update_ensemble_config(self, ensemble_id: str, **updates) -> bool:
        """更新集成配置"""
        if not self.fusion_service:
            return False
        return self.fusion_service.update_ensemble_config(ensemble_id, **updates)
    
    # =====================================================
    # 权重管理接口
    # =====================================================
    
    def calculate_model_weights(
        self,
        strategy: Union[WeightStrategy, str],
        model_ids: List[str],
        ensemble_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """计算模型权重"""
        try:
            if isinstance(strategy, str):
                strategy = WeightStrategy(strategy)
            
            # 获取性能数据
            performances = {}
            for model_id in model_ids:
                perf_data = self.monitoring_service.get_model_performance(model_id)
                if perf_data:
                    perf = ModelPerformance(
                        model_id=model_id,
                        accuracy=perf_data.get("avg_accuracy", 0.0),
                        response_time=perf_data.get("avg_response_time", 1.0),
                        success_rate=perf_data.get("success_rate", 0.0),
                        usage_count=perf_data.get("total_requests", 0),
                        error_rate=1.0 - perf_data.get("success_rate", 0.0)
                    )
                    performances[model_id] = perf
            
            weights = self.weight_service.calculate_weights(
                strategy, model_ids, performances, ensemble_id
            )
            
            # 转换为字典格式
            result = {}
            for model_id, weight in weights.items():
                result[model_id] = {
                    "weight": weight.weight,
                    "confidence": weight.confidence,
                    "metadata": weight.metadata
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate weights: {e}")
            return {}
    
    def set_manual_weights(self, ensemble_id: str, weights: Dict[str, float]) -> bool:
        """设置手动权重"""
        return self.weight_service.set_manual_weights(ensemble_id, weights)
    
    def get_weight_explanation(self, ensemble_id: str) -> Dict[str, str]:
        """获取权重解释"""
        weights = self.weight_service.get_manual_weights(ensemble_id)
        if not weights:
            return {}
        return self.weight_service.get_weight_explanation(weights)
    
    # =====================================================
    # 测试接口
    # =====================================================
    
    async def test_single_model(
        self,
        model_id: str,
        input_text: str,
        expected_output: Optional[str] = None,
        test_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """测试单个模型"""
        if not self.testing_service:
            return {"success": False, "error": "Testing service not available"}
        
        test_case = TestCase(
            test_id="",
            name=test_name or f"Test_{model_id}_{datetime.now().strftime('%H%M%S')}",
            input_text=input_text,
            expected_output=expected_output
        )
        
        result = await self.testing_service.test_single_model(model_id, test_case)
        
        return {
            "success": result.response.success,
            "content": result.response.content,
            "response_time": result.test_duration,
            "accuracy_score": result.accuracy_score,
            "similarity_score": result.similarity_score,
            "error_message": result.response.error_message if not result.response.success else None
        }
    
    async def test_ensemble(
        self,
        ensemble_id: str,
        input_text: str,
        expected_output: Optional[str] = None,
        test_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """测试模型集成"""
        if not self.testing_service or not self.fusion_service:
            return {"success": False, "error": "Testing or fusion service not available"}
        
        config = self.fusion_service.get_ensemble_config(ensemble_id)
        if not config:
            return {"success": False, "error": f"Ensemble {ensemble_id} not found"}
        
        test_case = TestCase(
            test_id="",
            name=test_name or f"EnsembleTest_{ensemble_id}_{datetime.now().strftime('%H%M%S')}",
            input_text=input_text,
            expected_output=expected_output
        )
        
        result = await self.testing_service.test_multiple_models(
            config.model_ids,
            test_case,
            config.weight_strategy,
            config.fusion_strategy.value
        )
        
        return {
            "success": len([r for r in result.individual_results if r.response.success]) > 0,
            "combined_response": result.combined_response,
            "overall_accuracy": result.overall_accuracy,
            "test_duration": result.test_duration,
            "fusion_strategy": result.fusion_strategy,
            "individual_results": [
                {
                    "model_id": r.model_id,
                    "success": r.response.success,
                    "response_time": r.test_duration,
                    "accuracy_score": r.accuracy_score
                }
                for r in result.individual_results
            ]
        }
    
    async def benchmark_models(
        self,
        model_ids: List[str],
        test_cases: List[Dict[str, str]],
        iterations: int = 1
    ) -> Dict[str, Dict[str, float]]:
        """基准测试模型"""
        if not self.testing_service:
            return {}
        
        # 转换测试用例
        cases = []
        for i, case in enumerate(test_cases):
            test_case = TestCase(
                test_id=f"benchmark_{i}",
                name=case.get("name", f"Benchmark_{i}"),
                input_text=case["input"],
                expected_output=case.get("expected_output")
            )
            cases.append(test_case)
        
        return await self.testing_service.benchmark_models(model_ids, cases, iterations)
    
    # =====================================================
    # 性能监控接口
    # =====================================================
    
    def get_model_performance(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取模型性能信息"""
        return self.monitoring_service.get_model_performance(model_id)
    
    def get_all_performance(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型性能信息"""
        return self.monitoring_service.get_all_models_performance()
    
    def get_alerts(
        self,
        model_id: Optional[str] = None,
        level: Optional[Union[AlertLevel, str]] = None
    ) -> List[Dict[str, Any]]:
        """获取告警信息"""
        if isinstance(level, str):
            level = AlertLevel(level)
        
        alerts = self.monitoring_service.get_alerts(model_id, level, acknowledged=False)
        
        return [
            {
                "alert_id": alert.alert_id,
                "model_id": alert.model_id,
                "level": alert.level.value,
                "message": alert.message,
                "metric_type": alert.metric_type.value,
                "threshold_value": alert.threshold_value,
                "actual_value": alert.actual_value,
                "timestamp": alert.timestamp.isoformat(),
                "acknowledged": alert.acknowledged
            }
            for alert in alerts
        ]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        return self.monitoring_service.acknowledge_alert(alert_id)
    
    def generate_performance_report(self, model_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """生成性能报告"""
        return self.monitoring_service.generate_performance_report(model_ids)
    
    # =====================================================
    # 服务健康检查
    # =====================================================
    
    def get_service_health(self) -> Dict[str, ServiceHealth]:
        """获取服务健康状态"""
        health_status = {}
        
        # 检查连接服务
        try:
            models = self.connection_service.list_models()
            health_status["connection_service"] = ServiceHealth(
                service_name="connection_service",
                status=ServiceStatus.RUNNING,
                last_check=datetime.now(),
                metrics={"registered_models": len(models)}
            )
        except Exception as e:
            health_status["connection_service"] = ServiceHealth(
                service_name="connection_service",
                status=ServiceStatus.ERROR,
                last_check=datetime.now(),
                error_message=str(e)
            )
        
        # 检查权重服务
        try:
            health_status["weight_service"] = ServiceHealth(
                service_name="weight_service",
                status=ServiceStatus.RUNNING,
                last_check=datetime.now()
            )
        except Exception as e:
            health_status["weight_service"] = ServiceHealth(
                service_name="weight_service",
                status=ServiceStatus.ERROR,
                last_check=datetime.now(),
                error_message=str(e)
            )
        
        # 检查监控服务
        try:
            all_perf = self.monitoring_service.get_all_models_performance()
            health_status["monitoring_service"] = ServiceHealth(
                service_name="monitoring_service",
                status=ServiceStatus.RUNNING,
                last_check=datetime.now(),
                metrics={"monitored_models": len(all_perf)}
            )
        except Exception as e:
            health_status["monitoring_service"] = ServiceHealth(
                service_name="monitoring_service",
                status=ServiceStatus.ERROR,
                last_check=datetime.now(),
                error_message=str(e)
            )
        
        # 检查测试服务
        if self.testing_service:
            try:
                health_status["testing_service"] = ServiceHealth(
                    service_name="testing_service",
                    status=ServiceStatus.RUNNING,
                    last_check=datetime.now()
                )
            except Exception as e:
                health_status["testing_service"] = ServiceHealth(
                    service_name="testing_service",
                    status=ServiceStatus.ERROR,
                    last_check=datetime.now(),
                    error_message=str(e)
                )
        else:
            health_status["testing_service"] = ServiceHealth(
                service_name="testing_service",
                status=ServiceStatus.STOPPED,
                last_check=datetime.now(),
                error_message="Service not initialized"
            )
        
        # 检查融合服务
        if self.fusion_service:
            try:
                ensembles = self.fusion_service.list_ensembles()
                health_status["fusion_service"] = ServiceHealth(
                    service_name="fusion_service",
                    status=ServiceStatus.RUNNING,
                    last_check=datetime.now(),
                    metrics={"registered_ensembles": len(ensembles)}
                )
            except Exception as e:
                health_status["fusion_service"] = ServiceHealth(
                    service_name="fusion_service",
                    status=ServiceStatus.ERROR,
                    last_check=datetime.now(),
                    error_message=str(e)
                )
        else:
            health_status["fusion_service"] = ServiceHealth(
                service_name="fusion_service",
                status=ServiceStatus.STOPPED,
                last_check=datetime.now(),
                error_message="Service not initialized"
            )
        
        return health_status
    
    def get_overall_health(self) -> Dict[str, Any]:
        """获取整体健康状态"""
        health_status = self.get_service_health()
        
        total_services = len(health_status)
        running_services = sum(1 for h in health_status.values() if h.status == ServiceStatus.RUNNING)
        error_services = sum(1 for h in health_status.values() if h.status == ServiceStatus.ERROR)
        
        overall_status = ServiceStatus.RUNNING
        if error_services > 0:
            overall_status = ServiceStatus.ERROR
        elif running_services < total_services:
            overall_status = ServiceStatus.INITIALIZING
        
        return {
            "overall_status": overall_status.value,
            "total_services": total_services,
            "running_services": running_services,
            "error_services": error_services,
            "health_score": running_services / total_services if total_services > 0 else 0.0,
            "last_check": datetime.now().isoformat(),
            "services": {name: {
                "status": health.status.value,
                "error_message": health.error_message,
                "metrics": health.metrics
            } for name, health in health_status.items()}
        }
    
    # =====================================================
    # 配置管理
    # =====================================================
    
    def update_config(self, **config_updates) -> bool:
        """更新配置"""
        try:
            for key, value in config_updates.items():
                if key in self.config:
                    self.config[key] = value
                    
                    # 应用特定配置
                    if key == "auto_monitoring":
                        self.monitoring_service.set_monitoring_enabled(value)
                    elif key == "log_level":
                        logging.getLogger().setLevel(getattr(logging, value.upper()))
            
            logger.info(f"Configuration updated: {config_updates}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()
    
    # =====================================================
    # 清理和关闭
    # =====================================================
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理监控数据
            self.monitoring_service.clear_old_alerts(days=1)
            
            # 重置状态
            self.status = ServiceStatus.STOPPED
            self.initialized = False
            
            logger.info("Model Service Manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# 全局服务管理器实例
model_service_manager = ModelServiceManager()