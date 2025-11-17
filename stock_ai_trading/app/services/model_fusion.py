"""
模型组合策略服务
提供多模型结果融合、权重投票、置信度评估和失败回退策略
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

from .model_connection_service import ModelConnectionService, ModelResponse
from .weight_management_service import WeightManagementService, ModelWeight, WeightStrategy
from .performance_monitoring_service import PerformanceMonitoringService

logger = logging.getLogger(__name__)

class FusionStrategy(Enum):
    """融合策略枚举"""
    WEIGHTED_VOTING = "weighted_voting"  # 权重投票
    MAJORITY_VOTING = "majority_voting"  # 多数投票
    CONFIDENCE_BASED = "confidence_based"  # 基于置信度
    BEST_RESPONSE = "best_response"  # 最佳响应
    CONSENSUS = "consensus"  # 共识算法
    ENSEMBLE_AVERAGE = "ensemble_average"  # 集成平均
    DYNAMIC_SELECTION = "dynamic_selection"  # 动态选择

class FailureStrategy(Enum):
    """失败回退策略"""
    FALLBACK_TO_BEST = "fallback_to_best"  # 回退到最佳模型
    RETRY_WITH_BACKUP = "retry_with_backup"  # 使用备用模型重试
    PARTIAL_RESPONSE = "partial_response"  # 部分响应
    ERROR_RESPONSE = "error_response"  # 错误响应

@dataclass
class ModelResult:
    """模型结果数据类"""
    model_id: str
    response: ModelResponse
    weight: float = 1.0
    confidence: float = 1.0
    response_time: float = 0.0
    accuracy_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FusionResult:
    """融合结果数据类"""
    success: bool
    content: str
    confidence: float
    individual_results: List[ModelResult]
    fusion_strategy: FusionStrategy
    weights_used: Dict[str, float]
    total_response_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnsembleConfig:
    """集成配置"""
    ensemble_id: str
    name: str
    model_ids: List[str]
    fusion_strategy: FusionStrategy = FusionStrategy.WEIGHTED_VOTING
    weight_strategy: WeightStrategy = WeightStrategy.EQUAL
    failure_strategy: FailureStrategy = FailureStrategy.FALLBACK_TO_BEST
    confidence_threshold: float = 0.5
    timeout: float = 30.0
    max_retries: int = 2
    enable_fallback: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseFusionAlgorithm(ABC):
    """融合算法基类"""
    
    @abstractmethod
    def fuse_results(
        self, 
        results: List[ModelResult], 
        config: EnsembleConfig
    ) -> FusionResult:
        """融合多个模型结果"""
        pass
    
    @abstractmethod
    def calculate_confidence(self, results: List[ModelResult]) -> float:
        """计算融合结果的置信度"""
        pass

class WeightedVotingFusion(BaseFusionAlgorithm):
    """权重投票融合算法"""
    
    def fuse_results(self, results: List[ModelResult], config: EnsembleConfig) -> FusionResult:
        """权重投票融合"""
        if not results:
            return self._create_empty_result(config)
        
        # 过滤成功的结果
        successful_results = [r for r in results if r.response.success]
        if not successful_results:
            return self._create_failure_result(results, config)
        
        # 根据权重选择最佳结果
        best_result = max(
            successful_results,
            key=lambda r: r.weight * r.confidence * (r.accuracy_score or 0.5)
        )
        
        confidence = self.calculate_confidence(successful_results)
        total_time = sum(r.response_time for r in results)
        
        return FusionResult(
            success=True,
            content=best_result.response.content,
            confidence=confidence,
            individual_results=results,
            fusion_strategy=FusionStrategy.WEIGHTED_VOTING,
            weights_used={r.model_id: r.weight for r in results},
            total_response_time=total_time,
            metadata={"selected_model": best_result.model_id}
        )
    
    def calculate_confidence(self, results: List[ModelResult]) -> float:
        """计算权重投票的置信度"""
        if not results:
            return 0.0
        
        # 基于权重和个体置信度计算总体置信度
        total_weight = sum(r.weight for r in results)
        if total_weight == 0:
            return 0.0
        
        weighted_confidence = sum(r.weight * r.confidence for r in results) / total_weight
        
        # 考虑结果一致性
        consistency_bonus = min(0.2, len(results) * 0.05)
        
        return min(1.0, weighted_confidence + consistency_bonus)
    
    def _create_empty_result(self, config: EnsembleConfig) -> FusionResult:
        """创建空结果"""
        return FusionResult(
            success=False,
            content="",
            confidence=0.0,
            individual_results=[],
            fusion_strategy=config.fusion_strategy,
            weights_used={},
            total_response_time=0.0,
            metadata={"error": "No results to fuse"}
        )
    
    def _create_failure_result(self, results: List[ModelResult], config: EnsembleConfig) -> FusionResult:
        """创建失败结果"""
        total_time = sum(r.response_time for r in results)
        
        return FusionResult(
            success=False,
            content="所有模型请求都失败了",
            confidence=0.0,
            individual_results=results,
            fusion_strategy=config.fusion_strategy,
            weights_used={r.model_id: r.weight for r in results},
            total_response_time=total_time,
            metadata={"error": "All model requests failed"}
        )

class MajorityVotingFusion(BaseFusionAlgorithm):
    """多数投票融合算法"""
    
    def fuse_results(self, results: List[ModelResult], config: EnsembleConfig) -> FusionResult:
        """多数投票融合"""
        if not results:
            return self._create_empty_result(config)
        
        successful_results = [r for r in results if r.response.success]
        if not successful_results:
            return self._create_failure_result(results, config)
        
        # 简化的多数投票：选择最常见的响应长度范围的结果
        length_groups = {}
        for result in successful_results:
            length_key = len(result.response.content) // 100  # 按100字符分组
            if length_key not in length_groups:
                length_groups[length_key] = []
            length_groups[length_key].append(result)
        
        # 选择最大组中权重最高的结果
        largest_group = max(length_groups.values(), key=len)
        best_result = max(largest_group, key=lambda r: r.weight)
        
        confidence = self.calculate_confidence(successful_results)
        total_time = sum(r.response_time for r in results)
        
        return FusionResult(
            success=True,
            content=best_result.response.content,
            confidence=confidence,
            individual_results=results,
            fusion_strategy=FusionStrategy.MAJORITY_VOTING,
            weights_used={r.model_id: r.weight for r in results},
            total_response_time=total_time,
            metadata={
                "selected_model": best_result.model_id,
                "group_size": len(largest_group),
                "total_groups": len(length_groups)
            }
        )
    
    def calculate_confidence(self, results: List[ModelResult]) -> float:
        """计算多数投票的置信度"""
        if not results:
            return 0.0
        
        # 基于结果数量和一致性
        base_confidence = min(0.8, len(results) * 0.2)
        
        # 考虑平均置信度
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return (base_confidence + avg_confidence) / 2

class ConfidenceBasedFusion(BaseFusionAlgorithm):
    """基于置信度的融合算法"""
    
    def fuse_results(self, results: List[ModelResult], config: EnsembleConfig) -> FusionResult:
        """基于置信度融合"""
        if not results:
            return self._create_empty_result(config)
        
        successful_results = [r for r in results if r.response.success]
        if not successful_results:
            return self._create_failure_result(results, config)
        
        # 过滤低置信度结果
        high_confidence_results = [
            r for r in successful_results 
            if r.confidence >= config.confidence_threshold
        ]
        
        if not high_confidence_results:
            # 如果没有高置信度结果，选择置信度最高的
            best_result = max(successful_results, key=lambda r: r.confidence)
        else:
            # 在高置信度结果中选择权重最高的
            best_result = max(
                high_confidence_results,
                key=lambda r: r.weight * r.confidence
            )
        
        confidence = self.calculate_confidence(successful_results)
        total_time = sum(r.response_time for r in results)
        
        return FusionResult(
            success=True,
            content=best_result.response.content,
            confidence=confidence,
            individual_results=results,
            fusion_strategy=FusionStrategy.CONFIDENCE_BASED,
            weights_used={r.model_id: r.weight for r in results},
            total_response_time=total_time,
            metadata={
                "selected_model": best_result.model_id,
                "selected_confidence": best_result.confidence,
                "high_confidence_count": len(high_confidence_results)
            }
        )
    
    def calculate_confidence(self, results: List[ModelResult]) -> float:
        """计算基于置信度融合的置信度"""
        if not results:
            return 0.0
        
        # 使用最高置信度作为基础
        max_confidence = max(r.confidence for r in results)
        
        # 考虑高置信度结果的比例
        high_conf_ratio = sum(1 for r in results if r.confidence > 0.7) / len(results)
        
        return min(1.0, max_confidence * (0.7 + 0.3 * high_conf_ratio))

class EnsembleAverageFusion(BaseFusionAlgorithm):
    """集成平均融合算法"""
    
    def fuse_results(self, results: List[ModelResult], config: EnsembleConfig) -> FusionResult:
        """集成平均融合"""
        if not results:
            return self._create_empty_result(config)
        
        successful_results = [r for r in results if r.response.success]
        if not successful_results:
            return self._create_failure_result(results, config)
        
        # 简化的平均融合：选择中等长度的响应
        responses = [r.response.content for r in successful_results]
        lengths = [len(content) for content in responses]
        
        if lengths:
            median_length = sorted(lengths)[len(lengths) // 2]
            # 选择长度最接近中位数的响应
            best_result = min(
                successful_results,
                key=lambda r: abs(len(r.response.content) - median_length)
            )
        else:
            best_result = successful_results[0]
        
        confidence = self.calculate_confidence(successful_results)
        total_time = sum(r.response_time for r in results)
        
        return FusionResult(
            success=True,
            content=best_result.response.content,
            confidence=confidence,
            individual_results=results,
            fusion_strategy=FusionStrategy.ENSEMBLE_AVERAGE,
            weights_used={r.model_id: r.weight for r in results},
            total_response_time=total_time,
            metadata={
                "selected_model": best_result.model_id,
                "median_length": median_length if lengths else 0,
                "response_count": len(successful_results)
            }
        )
    
    def calculate_confidence(self, results: List[ModelResult]) -> float:
        """计算集成平均的置信度"""
        if not results:
            return 0.0
        
        # 基于结果一致性和平均置信度
        avg_confidence = sum(r.confidence for r in results) / len(results)
        consistency_factor = 1.0 - (len(set(len(r.response.content) for r in results)) - 1) * 0.1
        
        return min(1.0, avg_confidence * max(0.5, consistency_factor))

class ModelFusionService:
    """模型融合服务"""
    
    def __init__(
        self,
        connection_service: ModelConnectionService,
        weight_service: WeightManagementService,
        monitoring_service: PerformanceMonitoringService
    ):
        self.connection_service = connection_service
        self.weight_service = weight_service
        self.monitoring_service = monitoring_service
        
        # 融合算法映射
        self.fusion_algorithms = {
            FusionStrategy.WEIGHTED_VOTING: WeightedVotingFusion(),
            FusionStrategy.MAJORITY_VOTING: MajorityVotingFusion(),
            FusionStrategy.CONFIDENCE_BASED: ConfidenceBasedFusion(),
            FusionStrategy.BEST_RESPONSE: WeightedVotingFusion(),  # 复用权重投票
            FusionStrategy.CONSENSUS: MajorityVotingFusion(),  # 复用多数投票
            FusionStrategy.ENSEMBLE_AVERAGE: EnsembleAverageFusion(),
            FusionStrategy.DYNAMIC_SELECTION: WeightedVotingFusion()  # 复用权重投票
        }
        
        # 集成配置存储
        self.ensemble_configs: Dict[str, EnsembleConfig] = {}
    
    def register_ensemble(self, config: EnsembleConfig) -> bool:
        """注册集成配置"""
        try:
            # 验证模型是否存在
            available_models = self.connection_service.list_models()
            invalid_models = [m for m in config.model_ids if m not in available_models]
            
            if invalid_models:
                logger.error(f"Invalid models in ensemble {config.ensemble_id}: {invalid_models}")
                return False
            
            self.ensemble_configs[config.ensemble_id] = config
            logger.info(f"Ensemble {config.ensemble_id} registered with {len(config.model_ids)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register ensemble {config.ensemble_id}: {e}")
            return False
    
    def unregister_ensemble(self, ensemble_id: str) -> bool:
        """注销集成配置"""
        if ensemble_id in self.ensemble_configs:
            del self.ensemble_configs[ensemble_id]
            logger.info(f"Ensemble {ensemble_id} unregistered")
            return True
        return False
    
    def get_ensemble_config(self, ensemble_id: str) -> Optional[EnsembleConfig]:
        """获取集成配置"""
        return self.ensemble_configs.get(ensemble_id)
    
    def list_ensembles(self) -> List[str]:
        """列出所有集成"""
        return list(self.ensemble_configs.keys())
    
    async def process_ensemble_request(
        self, 
        ensemble_id: str, 
        message: str,
        **kwargs
    ) -> FusionResult:
        """处理集成请求"""
        config = self.ensemble_configs.get(ensemble_id)
        if not config:
            return FusionResult(
                success=False,
                content=f"Ensemble {ensemble_id} not found",
                confidence=0.0,
                individual_results=[],
                fusion_strategy=FusionStrategy.WEIGHTED_VOTING,
                weights_used={},
                total_response_time=0.0,
                metadata={"error": "Ensemble not found"}
            )
        
        start_time = time.time()
        
        try:
            # 并发请求所有模型
            individual_results = await self._request_all_models(config, message, **kwargs)
            
            # 应用失败回退策略
            if self._should_apply_fallback(individual_results, config):
                fallback_result = await self._apply_failure_strategy(config, message, individual_results, **kwargs)
                if fallback_result:
                    return fallback_result
            
            # 计算权重
            weights = await self._calculate_ensemble_weights(config, individual_results)
            
            # 应用权重到结果
            for result in individual_results:
                weight = weights.get(result.model_id)
                if weight:
                    result.weight = weight.weight
                    result.confidence = weight.confidence
            
            # 融合结果
            fusion_algorithm = self.fusion_algorithms.get(
                config.fusion_strategy, 
                self.fusion_algorithms[FusionStrategy.WEIGHTED_VOTING]
            )
            
            fusion_result = fusion_algorithm.fuse_results(individual_results, config)
            
            # 记录性能指标
            self._record_ensemble_metrics(config, fusion_result, time.time() - start_time)
            
            return fusion_result
            
        except Exception as e:
            logger.error(f"Error processing ensemble request for {ensemble_id}: {e}")
            return FusionResult(
                success=False,
                content=f"Ensemble processing failed: {str(e)}",
                confidence=0.0,
                individual_results=[],
                fusion_strategy=config.fusion_strategy,
                weights_used={},
                total_response_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def _request_all_models(
        self, 
        config: EnsembleConfig, 
        message: str,
        **kwargs
    ) -> List[ModelResult]:
        """并发请求所有模型"""
        tasks = []
        
        for model_id in config.model_ids:
            task = self._request_single_model(model_id, message, **kwargs)
            tasks.append(task)
        
        # 设置超时
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=config.timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Ensemble {config.ensemble_id} request timeout")
            responses = [None] * len(tasks)
        
        # 处理结果
        results = []
        for i, response in enumerate(responses):
            model_id = config.model_ids[i]
            
            if isinstance(response, Exception):
                logger.error(f"Model {model_id} request failed: {response}")
                # 创建失败结果
                error_response = ModelResponse(
                    success=False,
                    error_message=str(response),
                    error_code="REQUEST_EXCEPTION"
                )
                result = ModelResult(model_id=model_id, response=error_response)
            elif response is None:
                # 超时结果
                error_response = ModelResponse(
                    success=False,
                    error_message="Request timeout",
                    error_code="TIMEOUT"
                )
                result = ModelResult(model_id=model_id, response=error_response)
            else:
                result = response
            
            results.append(result)
        
        return results
    
    async def _request_single_model(self, model_id: str, message: str, **kwargs) -> ModelResult:
        """请求单个模型"""
        start_time = time.time()
        
        try:
            response = await self.connection_service.send_message(model_id, message, **kwargs)
            response_time = time.time() - start_time
            
            # 记录性能指标
            self.monitoring_service.record_request(
                model_id=model_id,
                success=response.success,
                response_time=response_time
            )
            
            return ModelResult(
                model_id=model_id,
                response=response,
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Error requesting model {model_id}: {e}")
            
            # 记录失败
            self.monitoring_service.record_request(
                model_id=model_id,
                success=False,
                response_time=response_time
            )
            
            error_response = ModelResponse(
                success=False,
                error_message=str(e),
                error_code="REQUEST_ERROR"
            )
            
            return ModelResult(
                model_id=model_id,
                response=error_response,
                response_time=response_time
            )
    
    async def _calculate_ensemble_weights(
        self, 
        config: EnsembleConfig, 
        results: List[ModelResult]
    ) -> Dict[str, Any]:
        """计算集成权重"""
        # 构建性能数据
        performances = {}
        for result in results:
            from .weight_management_service import ModelPerformance
            perf = ModelPerformance(
                model_id=result.model_id,
                accuracy=result.accuracy_score or 0.0,
                response_time=result.response_time,
                success_rate=1.0 if result.response.success else 0.0
            )
            performances[result.model_id] = perf
        
        # 计算权重
        weights = self.weight_service.calculate_weights(
            config.weight_strategy,
            config.model_ids,
            performances,
            config.ensemble_id
        )
        
        return weights
    
    def _should_apply_fallback(self, results: List[ModelResult], config: EnsembleConfig) -> bool:
        """判断是否应该应用失败回退策略"""
        if not config.enable_fallback:
            return False
        
        successful_count = sum(1 for r in results if r.response.success)
        success_rate = successful_count / len(results) if results else 0.0
        
        # 如果成功率低于50%，应用回退策略
        return success_rate < 0.5
    
    async def _apply_failure_strategy(
        self, 
        config: EnsembleConfig, 
        message: str,
        original_results: List[ModelResult],
        **kwargs
    ) -> Optional[FusionResult]:
        """应用失败回退策略"""
        if config.failure_strategy == FailureStrategy.FALLBACK_TO_BEST:
            return await self._fallback_to_best_model(config, message, original_results, **kwargs)
        elif config.failure_strategy == FailureStrategy.RETRY_WITH_BACKUP:
            return await self._retry_with_backup(config, message, original_results, **kwargs)
        elif config.failure_strategy == FailureStrategy.PARTIAL_RESPONSE:
            return self._create_partial_response(config, original_results)
        else:
            return None
    
    async def _fallback_to_best_model(
        self, 
        config: EnsembleConfig, 
        message: str,
        original_results: List[ModelResult],
        **kwargs
    ) -> Optional[FusionResult]:
        """回退到最佳模型"""
        # 找到最佳模型（基于历史性能）
        best_model_id = None
        best_score = -1
        
        for model_id in config.model_ids:
            perf = self.monitoring_service.get_model_performance(model_id)
            if perf:
                # 计算综合得分
                score = (
                    perf.get("success_rate", 0.0) * 0.4 +
                    perf.get("avg_accuracy", 0.0) * 0.4 +
                    (1.0 / max(perf.get("avg_response_time", 1.0), 0.1)) * 0.2
                )
                if score > best_score:
                    best_score = score
                    best_model_id = model_id
        
        if not best_model_id:
            return None
        
        # 请求最佳模型
        try:
            fallback_result = await self._request_single_model(best_model_id, message, **kwargs)
            
            if fallback_result.response.success:
                return FusionResult(
                    success=True,
                    content=fallback_result.response.content,
                    confidence=0.7,  # 降低置信度表示这是回退结果
                    individual_results=original_results + [fallback_result],
                    fusion_strategy=config.fusion_strategy,
                    weights_used={best_model_id: 1.0},
                    total_response_time=sum(r.response_time for r in original_results) + fallback_result.response_time,
                    metadata={
                        "fallback_used": True,
                        "fallback_model": best_model_id,
                        "fallback_strategy": "best_model"
                    }
                )
        except Exception as e:
            logger.error(f"Fallback to best model failed: {e}")
        
        return None
    
    async def _retry_with_backup(
        self, 
        config: EnsembleConfig, 
        message: str,
        original_results: List[ModelResult],
        **kwargs
    ) -> Optional[FusionResult]:
        """使用备用模型重试"""
        # 找到失败的模型
        failed_models = [r.model_id for r in original_results if not r.response.success]
        
        if not failed_models:
            return None
        
        # 重试失败的模型（最多重试次数）
        retry_results = []
        for model_id in failed_models[:config.max_retries]:
            try:
                retry_result = await self._request_single_model(model_id, message, **kwargs)
                retry_results.append(retry_result)
            except Exception as e:
                logger.error(f"Retry for model {model_id} failed: {e}")
        
        # 合并原始结果和重试结果
        all_results = original_results + retry_results
        successful_results = [r for r in all_results if r.response.success]
        
        if successful_results:
            # 选择最佳结果
            best_result = max(successful_results, key=lambda r: r.confidence)
            
            return FusionResult(
                success=True,
                content=best_result.response.content,
                confidence=best_result.confidence * 0.8,  # 降低置信度
                individual_results=all_results,
                fusion_strategy=config.fusion_strategy,
                weights_used={r.model_id: 1.0/len(successful_results) for r in successful_results},
                total_response_time=sum(r.response_time for r in all_results),
                metadata={
                    "fallback_used": True,
                    "retry_count": len(retry_results),
                    "fallback_strategy": "retry_backup"
                }
            )
        
        return None
    
    def _create_partial_response(
        self, 
        config: EnsembleConfig, 
        results: List[ModelResult]
    ) -> FusionResult:
        """创建部分响应"""
        successful_results = [r for r in results if r.response.success]
        
        if successful_results:
            # 合并所有成功的响应
            combined_content = " | ".join([r.response.content for r in successful_results])
            confidence = len(successful_results) / len(results)
        else:
            combined_content = "部分模型响应失败，无法提供完整结果"
            confidence = 0.1
        
        return FusionResult(
            success=len(successful_results) > 0,
            content=combined_content,
            confidence=confidence,
            individual_results=results,
            fusion_strategy=config.fusion_strategy,
            weights_used={r.model_id: 1.0/len(results) for r in results},
            total_response_time=sum(r.response_time for r in results),
            metadata={
                "fallback_used": True,
                "successful_models": len(successful_results),
                "total_models": len(results),
                "fallback_strategy": "partial_response"
            }
        )
    
    def _record_ensemble_metrics(
        self, 
        config: EnsembleConfig, 
        result: FusionResult, 
        total_time: float
    ):
        """记录集成指标"""
        # 记录集成级别的性能指标
        self.monitoring_service.record_request(
            model_id=f"ensemble_{config.ensemble_id}",
            success=result.success,
            response_time=total_time,
            accuracy=None,  # 集成准确率需要单独计算
            metadata={
                "fusion_strategy": result.fusion_strategy.value,
                "individual_count": len(result.individual_results),
                "confidence": result.confidence
            }
        )
    
    def get_ensemble_performance(self, ensemble_id: str) -> Optional[Dict[str, Any]]:
        """获取集成性能信息"""
        return self.monitoring_service.get_model_performance(f"ensemble_{ensemble_id}")
    
    def update_ensemble_config(self, ensemble_id: str, **updates) -> bool:
        """更新集成配置"""
        config = self.ensemble_configs.get(ensemble_id)
        if not config:
            return False
        
        try:
            # 更新允许的字段
            updatable_fields = [
                'fusion_strategy', 'weight_strategy', 'failure_strategy',
                'confidence_threshold', 'timeout', 'max_retries', 'enable_fallback'
            ]
            
            for field, value in updates.items():
                if field in updatable_fields:
                    if field in ['fusion_strategy', 'weight_strategy', 'failure_strategy']:
                        # 枚举类型需要特殊处理
                        if isinstance(value, str):
                            enum_class = {
                                'fusion_strategy': FusionStrategy,
                                'weight_strategy': WeightStrategy,
                                'failure_strategy': FailureStrategy
                            }[field]
                            value = enum_class(value)
                    
                    setattr(config, field, value)
            
            logger.info(f"Ensemble {ensemble_id} configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update ensemble {ensemble_id} configuration: {e}")
            return False

# 创建全局融合服务实例（需要在使用时注入依赖）
def create_model_fusion_service(connection_service, weight_service, monitoring_service):
    """创建模型融合服务实例"""
    return ModelFusionService(connection_service, weight_service, monitoring_service)
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import json
import statistics

from app.models.ai_decision_models import (
    TradingDecision, 
    ModelVote,
    ModelFusionResult,
    TradingAction,
    ConfidenceLevel
)
from app.services.llm_gateway import LLMGateway, GatewayRequest

logger = logging.getLogger(__name__)

@dataclass
class ModelWeight:
    """模型权重配置"""
    model_id: str
    base_weight: float  # 基础权重
    performance_weight: float  # 基于历史表现的权重
    confidence_weight: float  # 基于置信度的权重
    final_weight: float = field(init=False)  # 最终权重
    
    def __post_init__(self):
        self.final_weight = self.base_weight * self.performance_weight * self.confidence_weight

@dataclass
class ConsistencyMetrics:
    """一致性指标"""
    action_consistency: float  # 动作一致性
    price_consistency: float  # 价格一致性
    quantity_consistency: float  # 数量一致性
    overall_consistency: float  # 总体一致性
    conflicting_models: List[str]  # 冲突的模型

@dataclass
class FusionConfig:
    """融合配置"""
    min_models: int = 2  # 最少模型数量
    consistency_threshold: float = 0.6  # 一致性阈值
    confidence_threshold: float = 0.5  # 置信度阈值
    weight_decay: float = 0.95  # 权重衰减因子
    max_price_deviation: float = 0.1  # 最大价格偏差
    max_quantity_deviation: float = 0.2  # 最大数量偏差

class ModelFusion:
    """多模型融合器"""
    
    def __init__(self, llm_gateway: LLMGateway, config: Optional[FusionConfig] = None):
        self.llm_gateway = llm_gateway
        self.config = config or FusionConfig()
        
        # 模型权重管理
        self.model_weights: Dict[str, ModelWeight] = {}
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        
        # 融合策略配置
        self.fusion_strategies = {
            'weighted_voting': self._weighted_voting_fusion,
            'consensus_based': self._consensus_based_fusion,
            'confidence_weighted': self._confidence_weighted_fusion,
            'ensemble_average': self._ensemble_average_fusion
        }
        
        # 一致性检查权重
        self.consistency_weights = {
            'action': 0.4,
            'price': 0.3,
            'quantity': 0.2,
            'confidence': 0.1
        }

    async def fuse_decisions(
        self,
        model_votes: List[ModelVote],
        strategy: str = 'weighted_voting',
        market_context: Optional[Dict[str, Any]] = None
    ) -> ModelFusionResult:
        """
        融合多个模型的决策结果
        
        Args:
            model_votes: 模型投票列表
            strategy: 融合策略
            market_context: 市场上下文
            
        Returns:
            ModelFusionResult: 融合结果
        """
        try:
            logger.info(f"开始融合{len(model_votes)}个模型决策，策略: {strategy}")
            
            # 1. 验证输入
            if len(model_votes) < self.config.min_models:
                raise ValueError(f"模型数量不足，至少需要{self.config.min_models}个")
            
            # 2. 更新模型权重
            self._update_model_weights(model_votes)
            
            # 3. 一致性检查
            consistency_metrics = self._check_consistency(model_votes)
            
            # 4. 选择融合策略
            if strategy not in self.fusion_strategies:
                strategy = 'weighted_voting'
                logger.warning(f"未知融合策略，使用默认策略: {strategy}")
            
            # 5. 执行融合
            fusion_func = self.fusion_strategies[strategy]
            fused_decision = await fusion_func(model_votes, consistency_metrics, market_context)
            
            # 6. 计算融合置信度
            fusion_confidence = self._calculate_fusion_confidence(
                model_votes, consistency_metrics, fused_decision
            )
            
            # 7. 生成融合解释
            fusion_reasoning = await self._generate_fusion_reasoning(
                model_votes, fused_decision, consistency_metrics
            )
            
            return ModelFusionResult(
                fused_decision=fused_decision,
                model_votes=model_votes,
                fusion_confidence=fusion_confidence,
                consistency_metrics=consistency_metrics.__dict__,
                fusion_strategy=strategy,
                fusion_reasoning=fusion_reasoning,
                model_weights={mv.model_id: self.model_weights.get(mv.model_id, ModelWeight(mv.model_id, 1.0, 1.0, 1.0)).final_weight 
                             for mv in model_votes},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"模型融合失败: {e}")
            # 返回默认结果
            return self._create_fallback_result(model_votes, str(e))

    def _update_model_weights(self, model_votes: List[ModelVote]):
        """更新模型权重"""
        for vote in model_votes:
            model_id = vote.model_id
            
            # 初始化权重（如果不存在）
            if model_id not in self.model_weights:
                self.model_weights[model_id] = ModelWeight(
                    model_id=model_id,
                    base_weight=1.0,
                    performance_weight=1.0,
                    confidence_weight=1.0
                )
            
            # 更新基于置信度的权重
            confidence_weight = max(0.1, min(2.0, vote.confidence * 2))
            self.model_weights[model_id].confidence_weight = confidence_weight
            
            # 更新基于历史表现的权重
            if model_id in self.performance_history:
                recent_performance = self.performance_history[model_id][-10:]  # 最近10次
                if recent_performance:
                    avg_performance = statistics.mean(recent_performance)
                    performance_weight = max(0.1, min(2.0, avg_performance * 2))
                    self.model_weights[model_id].performance_weight = performance_weight
            
            # 重新计算最终权重
            weight = self.model_weights[model_id]
            weight.final_weight = weight.base_weight * weight.performance_weight * weight.confidence_weight

    def _check_consistency(self, model_votes: List[ModelVote]) -> ConsistencyMetrics:
        """检查模型决策一致性"""
        if len(model_votes) < 2:
            return ConsistencyMetrics(1.0, 1.0, 1.0, 1.0, [])
        
        # 提取决策数据
        actions = [vote.decision.action for vote in model_votes]
        prices = [vote.decision.price for vote in model_votes if vote.decision.price]
        quantities = [vote.decision.quantity for vote in model_votes if vote.decision.quantity]
        
        # 1. 动作一致性
        action_counts = Counter(actions)
        most_common_action = action_counts.most_common(1)[0]
        action_consistency = most_common_action[1] / len(actions)
        
        # 2. 价格一致性
        price_consistency = 1.0
        if len(prices) > 1:
            price_std = np.std(prices)
            price_mean = np.mean(prices)
            if price_mean > 0:
                price_cv = price_std / price_mean  # 变异系数
                price_consistency = max(0.0, 1.0 - price_cv / self.config.max_price_deviation)
        
        # 3. 数量一致性
        quantity_consistency = 1.0
        if len(quantities) > 1:
            quantity_std = np.std(quantities)
            quantity_mean = np.mean(quantities)
            if quantity_mean > 0:
                quantity_cv = quantity_std / quantity_mean
                quantity_consistency = max(0.0, 1.0 - quantity_cv / self.config.max_quantity_deviation)
        
        # 4. 总体一致性
        overall_consistency = (
            action_consistency * self.consistency_weights['action'] +
            price_consistency * self.consistency_weights['price'] +
            quantity_consistency * self.consistency_weights['quantity']
        )
        
        # 5. 识别冲突模型
        conflicting_models = []
        if action_consistency < 0.7:  # 动作不一致
            minority_actions = [action for action, count in action_counts.items() 
                              if count < most_common_action[1]]
            for vote in model_votes:
                if vote.decision.action in minority_actions:
                    conflicting_models.append(vote.model_id)
        
        return ConsistencyMetrics(
            action_consistency=action_consistency,
            price_consistency=price_consistency,
            quantity_consistency=quantity_consistency,
            overall_consistency=overall_consistency,
            conflicting_models=conflicting_models
        )

    async def _weighted_voting_fusion(
        self,
        model_votes: List[ModelVote],
        consistency_metrics: ConsistencyMetrics,
        market_context: Optional[Dict[str, Any]] = None
    ) -> TradingDecision:
        """加权投票融合策略"""
        
        # 计算加权结果
        weighted_actions = defaultdict(float)
        weighted_prices = []
        weighted_quantities = []
        weighted_confidences = []
        
        total_weight = 0.0
        
        for vote in model_votes:
            model_id = vote.model_id
            weight = self.model_weights.get(model_id, ModelWeight(model_id, 1.0, 1.0, 1.0)).final_weight
            
            # 如果一致性低，降低冲突模型的权重
            if model_id in consistency_metrics.conflicting_models:
                weight *= 0.5
            
            # 动作加权投票
            weighted_actions[vote.decision.action] += weight
            
            # 价格和数量加权平均
            if vote.decision.price:
                weighted_prices.append((vote.decision.price, weight))
            if vote.decision.quantity:
                weighted_quantities.append((vote.decision.quantity, weight))
            
            weighted_confidences.append((vote.confidence, weight))
            total_weight += weight
        
        # 确定最终动作
        final_action = max(weighted_actions.items(), key=lambda x: x[1])[0]
        
        # 计算加权平均价格
        if weighted_prices:
            final_price = sum(price * weight for price, weight in weighted_prices) / sum(weight for _, weight in weighted_prices)
        else:
            final_price = None
        
        # 计算加权平均数量
        if weighted_quantities:
            final_quantity = int(sum(qty * weight for qty, weight in weighted_quantities) / sum(weight for _, weight in weighted_quantities))
        else:
            final_quantity = None
        
        # 计算加权平均置信度
        final_confidence = sum(conf * weight for conf, weight in weighted_confidences) / total_weight
        
        # 生成融合理由
        reasoning_parts = []
        for vote in model_votes:
            weight = self.model_weights.get(vote.model_id, ModelWeight(vote.model_id, 1.0, 1.0, 1.0)).final_weight
            reasoning_parts.append(f"{vote.model_id}(权重{weight:.2f}): {vote.decision.reasoning}")
        
        final_reasoning = f"加权投票融合结果。" + "; ".join(reasoning_parts)
        
        # 选择代表性模型ID
        representative_vote = max(model_votes, key=lambda v: self.model_weights.get(v.model_id, ModelWeight(v.model_id, 1.0, 1.0, 1.0)).final_weight)
        
        return TradingDecision(
            action=final_action,
            symbol=representative_vote.decision.symbol,
            quantity=final_quantity,
            price=final_price,
            confidence=final_confidence,
            reasoning=final_reasoning,
            model_id="fusion_weighted_voting",
            timestamp=datetime.now(),
            stop_loss=representative_vote.decision.stop_loss,
            take_profit=representative_vote.decision.take_profit
        )

    async def _consensus_based_fusion(
        self,
        model_votes: List[ModelVote],
        consistency_metrics: ConsistencyMetrics,
        market_context: Optional[Dict[str, Any]] = None
    ) -> TradingDecision:
        """基于共识的融合策略"""
        
        # 如果一致性太低，使用保守策略
        if consistency_metrics.overall_consistency < self.config.consistency_threshold:
            logger.warning(f"一致性过低({consistency_metrics.overall_consistency:.2f})，采用保守策略")
            return self._create_conservative_decision(model_votes)
        
        # 找到共识动作
        actions = [vote.decision.action for vote in model_votes]
        action_counts = Counter(actions)
        consensus_action = action_counts.most_common(1)[0][0]
        
        # 只考虑支持共识动作的模型
        consensus_votes = [vote for vote in model_votes if vote.decision.action == consensus_action]
        
        # 计算共识价格和数量
        prices = [vote.decision.price for vote in consensus_votes if vote.decision.price]
        quantities = [vote.decision.quantity for vote in consensus_votes if vote.decision.quantity]
        confidences = [vote.confidence for vote in consensus_votes]
        
        final_price = statistics.median(prices) if prices else None
        final_quantity = int(statistics.median(quantities)) if quantities else None
        final_confidence = statistics.mean(confidences)
        
        # 生成共识理由
        consensus_reasoning = f"基于{len(consensus_votes)}/{len(model_votes)}个模型的共识决策"
        
        representative_vote = consensus_votes[0]
        
        return TradingDecision(
            action=consensus_action,
            symbol=representative_vote.decision.symbol,
            quantity=final_quantity,
            price=final_price,
            confidence=final_confidence,
            reasoning=consensus_reasoning,
            model_id="fusion_consensus",
            timestamp=datetime.now(),
            stop_loss=representative_vote.decision.stop_loss,
            take_profit=representative_vote.decision.take_profit
        )

    async def _confidence_weighted_fusion(
        self,
        model_votes: List[ModelVote],
        consistency_metrics: ConsistencyMetrics,
        market_context: Optional[Dict[str, Any]] = None
    ) -> TradingDecision:
        """基于置信度加权的融合策略"""
        
        # 按置信度排序
        sorted_votes = sorted(model_votes, key=lambda v: v.confidence, reverse=True)
        
        # 只考虑高置信度的模型
        high_confidence_votes = [vote for vote in sorted_votes 
                               if vote.confidence >= self.config.confidence_threshold]
        
        if not high_confidence_votes:
            high_confidence_votes = sorted_votes[:max(1, len(sorted_votes) // 2)]
        
        # 使用置信度作为权重
        total_confidence = sum(vote.confidence for vote in high_confidence_votes)
        
        # 加权计算
        weighted_actions = defaultdict(float)
        weighted_prices = []
        weighted_quantities = []
        
        for vote in high_confidence_votes:
            weight = vote.confidence / total_confidence
            
            weighted_actions[vote.decision.action] += weight
            
            if vote.decision.price:
                weighted_prices.append((vote.decision.price, weight))
            if vote.decision.quantity:
                weighted_quantities.append((vote.decision.quantity, weight))
        
        # 确定最终结果
        final_action = max(weighted_actions.items(), key=lambda x: x[1])[0]
        
        if weighted_prices:
            final_price = sum(price * weight for price, weight in weighted_prices)
        else:
            final_price = None
        
        if weighted_quantities:
            final_quantity = int(sum(qty * weight for qty, weight in weighted_quantities))
        else:
            final_quantity = None
        
        final_confidence = statistics.mean([vote.confidence for vote in high_confidence_votes])
        
        reasoning = f"基于{len(high_confidence_votes)}个高置信度模型的加权融合"
        
        representative_vote = high_confidence_votes[0]
        
        return TradingDecision(
            action=final_action,
            symbol=representative_vote.decision.symbol,
            quantity=final_quantity,
            price=final_price,
            confidence=final_confidence,
            reasoning=reasoning,
            model_id="fusion_confidence_weighted",
            timestamp=datetime.now(),
            stop_loss=representative_vote.decision.stop_loss,
            take_profit=representative_vote.decision.take_profit
        )

    async def _ensemble_average_fusion(
        self,
        model_votes: List[ModelVote],
        consistency_metrics: ConsistencyMetrics,
        market_context: Optional[Dict[str, Any]] = None
    ) -> TradingDecision:
        """集成平均融合策略"""
        
        # 简单平均所有模型的结果
        actions = [vote.decision.action for vote in model_votes]
        prices = [vote.decision.price for vote in model_votes if vote.decision.price]
        quantities = [vote.decision.quantity for vote in model_votes if vote.decision.quantity]
        confidences = [vote.confidence for vote in model_votes]
        
        # 多数投票决定动作
        action_counts = Counter(actions)
        final_action = action_counts.most_common(1)[0][0]
        
        # 平均价格和数量
        final_price = statistics.mean(prices) if prices else None
        final_quantity = int(statistics.mean(quantities)) if quantities else None
        final_confidence = statistics.mean(confidences)
        
        reasoning = f"基于{len(model_votes)}个模型的集成平均结果"
        
        representative_vote = model_votes[0]
        
        return TradingDecision(
            action=final_action,
            symbol=representative_vote.decision.symbol,
            quantity=final_quantity,
            price=final_price,
            confidence=final_confidence,
            reasoning=reasoning,
            model_id="fusion_ensemble_average",
            timestamp=datetime.now(),
            stop_loss=representative_vote.decision.stop_loss,
            take_profit=representative_vote.decision.take_profit
        )

    def _create_conservative_decision(self, model_votes: List[ModelVote]) -> TradingDecision:
        """创建保守决策（当一致性过低时）"""
        representative_vote = model_votes[0]
        
        return TradingDecision(
            action=TradingAction.HOLD,  # 保守策略：持有
            symbol=representative_vote.decision.symbol,
            quantity=None,
            price=None,
            confidence=0.3,  # 低置信度
            reasoning="模型决策一致性过低，采用保守持有策略",
            model_id="fusion_conservative",
            timestamp=datetime.now()
        )

    def _calculate_fusion_confidence(
        self,
        model_votes: List[ModelVote],
        consistency_metrics: ConsistencyMetrics,
        fused_decision: TradingDecision
    ) -> float:
        """计算融合置信度"""
        
        # 基础置信度：模型置信度的加权平均
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for vote in model_votes:
            weight = self.model_weights.get(vote.model_id, ModelWeight(vote.model_id, 1.0, 1.0, 1.0)).final_weight
            weighted_confidence += vote.confidence * weight
            total_weight += weight
        
        base_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.5
        
        # 一致性调整
        consistency_bonus = consistency_metrics.overall_consistency * 0.2
        
        # 模型数量调整
        model_count_bonus = min(0.1, len(model_votes) * 0.02)
        
        # 最终置信度
        final_confidence = base_confidence + consistency_bonus + model_count_bonus
        
        return max(0.0, min(1.0, final_confidence))

    async def _generate_fusion_reasoning(
        self,
        model_votes: List[ModelVote],
        fused_decision: TradingDecision,
        consistency_metrics: ConsistencyMetrics
    ) -> str:
        """生成融合推理说明"""
        
        try:
            # 构建推理提示词
            prompt = self._build_fusion_reasoning_prompt(model_votes, fused_decision, consistency_metrics)
            
            response = await self.llm_gateway.generate(
                GatewayRequest(
                    messages=[{"role": "user", "content": prompt}],
                    model="deepseek",
                    temperature=0.3
                )
            )
            
            if response.success:
                return response.content
            
        except Exception as e:
            logger.error(f"生成融合推理失败: {e}")
        
        # 回退到简单推理
        return self._generate_simple_fusion_reasoning(model_votes, fused_decision, consistency_metrics)

    def _build_fusion_reasoning_prompt(
        self,
        model_votes: List[ModelVote],
        fused_decision: TradingDecision,
        consistency_metrics: ConsistencyMetrics
    ) -> str:
        """构建融合推理提示词"""
        
        votes_info = []
        for vote in model_votes:
            weight = self.model_weights.get(vote.model_id, ModelWeight(vote.model_id, 1.0, 1.0, 1.0)).final_weight
            votes_info.append(f"- {vote.model_id}(权重{weight:.2f}): {vote.decision.action.value} "
                            f"价格{vote.decision.price} 数量{vote.decision.quantity} "
                            f"置信度{vote.confidence:.2f} 理由: {vote.decision.reasoning}")
        
        votes_text = "\n".join(votes_info)
        
        prompt = f"""
请为以下多模型融合决策生成简洁的推理说明：

各模型决策：
{votes_text}

融合结果：
- 动作: {fused_decision.action.value}
- 价格: {fused_decision.price}
- 数量: {fused_decision.quantity}
- 置信度: {fused_decision.confidence:.2f}

一致性指标：
- 动作一致性: {consistency_metrics.action_consistency:.2f}
- 价格一致性: {consistency_metrics.price_consistency:.2f}
- 数量一致性: {consistency_metrics.quantity_consistency:.2f}
- 总体一致性: {consistency_metrics.overall_consistency:.2f}

请生成一个简洁的推理说明（不超过200字），解释融合决策的依据和逻辑。
"""
        return prompt

    def _generate_simple_fusion_reasoning(
        self,
        model_votes: List[ModelVote],
        fused_decision: TradingDecision,
        consistency_metrics: ConsistencyMetrics
    ) -> str:
        """生成简单融合推理"""
        
        model_count = len(model_votes)
        consistency = consistency_metrics.overall_consistency
        
        reasoning = f"融合{model_count}个模型决策，总体一致性{consistency:.1%}。"
        
        if consistency > 0.8:
            reasoning += "各模型高度一致，决策可靠性较高。"
        elif consistency > 0.6:
            reasoning += "各模型基本一致，决策具有一定可靠性。"
        else:
            reasoning += "各模型存在分歧，采用加权融合策略。"
        
        # 添加主要支持理由
        main_reasons = []
        for vote in model_votes[:3]:  # 取前3个模型的理由
            if vote.decision.reasoning:
                main_reasons.append(vote.decision.reasoning[:50])
        
        if main_reasons:
            reasoning += f" 主要依据：{'; '.join(main_reasons)}"
        
        return reasoning

    def _create_fallback_result(self, model_votes: List[ModelVote], error_msg: str) -> ModelFusionResult:
        """创建回退结果"""
        
        if model_votes:
            # 选择置信度最高的模型作为回退
            best_vote = max(model_votes, key=lambda v: v.confidence)
            fused_decision = best_vote.decision
            fused_decision.model_id = "fusion_fallback"
            fused_decision.reasoning = f"融合失败，使用最佳单模型结果。错误：{error_msg}"
        else:
            # 创建默认决策
            fused_decision = TradingDecision(
                action=TradingAction.HOLD,
                symbol="UNKNOWN",
                quantity=None,
                price=None,
                confidence=0.0,
                reasoning=f"融合失败，无可用模型。错误：{error_msg}",
                model_id="fusion_error",
                timestamp=datetime.now()
            )
        
        return ModelFusionResult(
            fused_decision=fused_decision,
            model_votes=model_votes,
            fusion_confidence=0.0,
            consistency_metrics={},
            fusion_strategy="fallback",
            fusion_reasoning=f"融合过程出现错误：{error_msg}",
            model_weights={},
            timestamp=datetime.now()
        )

    def update_model_performance(self, model_id: str, performance_score: float):
        """更新模型历史表现"""
        self.performance_history[model_id].append(performance_score)
        
        # 保持历史记录在合理范围内
        if len(self.performance_history[model_id]) > 100:
            self.performance_history[model_id] = self.performance_history[model_id][-50:]

    def get_model_weights(self) -> Dict[str, float]:
        """获取当前模型权重"""
        return {model_id: weight.final_weight for model_id, weight in self.model_weights.items()}

    def set_model_base_weight(self, model_id: str, base_weight: float):
        """设置模型基础权重"""
        if model_id not in self.model_weights:
            self.model_weights[model_id] = ModelWeight(model_id, base_weight, 1.0, 1.0)
        else:
            self.model_weights[model_id].base_weight = base_weight
            # 重新计算最终权重
            weight = self.model_weights[model_id]
            weight.final_weight = weight.base_weight * weight.performance_weight * weight.confidence_weight

    async def batch_fuse_decisions(
        self,
        batch_votes: List[List[ModelVote]],
        strategy: str = 'weighted_voting'
    ) -> List[ModelFusionResult]:
        """批量融合决策"""
        tasks = []
        for votes in batch_votes:
            task = self.fuse_decisions(votes, strategy)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)