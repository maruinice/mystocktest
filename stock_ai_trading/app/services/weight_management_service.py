"""
权重管理服务
提供多种权重分配和管理策略
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class WeightStrategy(Enum):
    """权重策略枚举"""
    EQUAL = "equal"  # 等权重
    ACCURACY_BASED = "accuracy_based"  # 基于准确率
    MANUAL = "manual"  # 手动配置
    DYNAMIC = "dynamic"  # 动态调整
    PERFORMANCE_BASED = "performance_based"  # 基于性能

@dataclass
class ModelWeight:
    """模型权重数据类"""
    model_id: str
    weight: float
    confidence: float = 1.0
    last_updated: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # 确保权重在有效范围内
        self.weight = max(0.0, min(1.0, self.weight))
        self.confidence = max(0.0, min(1.0, self.confidence))

@dataclass
class ModelPerformance:
    """模型性能数据类"""
    model_id: str
    accuracy: float = 0.0
    response_time: float = 0.0
    success_rate: float = 0.0
    usage_count: int = 0
    error_rate: float = 0.0
    
    def get_performance_score(self) -> float:
        """计算综合性能得分"""
        # 权重：准确率40%，成功率30%，响应时间20%，错误率10%
        accuracy_score = self.accuracy * 0.4
        success_score = self.success_rate * 0.3
        
        # 响应时间得分（越快越好，使用倒数）
        time_score = 0.0
        if self.response_time > 0:
            # 将响应时间转换为得分（1秒=1.0分，10秒=0.1分）
            time_score = min(1.0, 1.0 / self.response_time) * 0.2
        
        # 错误率得分（越低越好）
        error_score = (1.0 - self.error_rate) * 0.1
        
        return accuracy_score + success_score + time_score + error_score

class BaseWeightCalculator(ABC):
    """权重计算器基类"""
    
    @abstractmethod
    def calculate_weights(self, models: List[str], performances: Dict[str, ModelPerformance]) -> Dict[str, ModelWeight]:
        """计算模型权重"""
        pass
    
    @abstractmethod
    def validate_weights(self, weights: Dict[str, ModelWeight]) -> bool:
        """验证权重是否有效"""
        pass

class EqualWeightCalculator(BaseWeightCalculator):
    """等权重计算器"""
    
    def calculate_weights(self, models: List[str], performances: Dict[str, ModelPerformance]) -> Dict[str, ModelWeight]:
        """计算等权重"""
        if not models:
            return {}
        
        equal_weight = 1.0 / len(models)
        weights = {}
        
        for model_id in models:
            weights[model_id] = ModelWeight(
                model_id=model_id,
                weight=equal_weight,
                confidence=1.0,
                metadata={"strategy": "equal"}
            )
        
        return weights
    
    def validate_weights(self, weights: Dict[str, ModelWeight]) -> bool:
        """验证等权重"""
        if not weights:
            return False
        
        total_weight = sum(w.weight for w in weights.values())
        return abs(total_weight - 1.0) < 1e-6

class AccuracyBasedWeightCalculator(BaseWeightCalculator):
    """基于准确率的权重计算器"""
    
    def __init__(self, min_weight: float = 0.1, smoothing_factor: float = 0.1):
        self.min_weight = min_weight
        self.smoothing_factor = smoothing_factor
    
    def calculate_weights(self, models: List[str], performances: Dict[str, ModelPerformance]) -> Dict[str, ModelWeight]:
        """基于准确率计算权重"""
        if not models:
            return {}
        
        weights = {}
        
        # 获取所有模型的准确率
        accuracies = {}
        for model_id in models:
            perf = performances.get(model_id)
            if perf:
                # 使用平滑因子避免零权重
                accuracies[model_id] = perf.accuracy + self.smoothing_factor
            else:
                accuracies[model_id] = self.smoothing_factor
        
        # 计算总准确率
        total_accuracy = sum(accuracies.values())
        
        if total_accuracy == 0:
            # 如果所有准确率都为0，使用等权重
            return EqualWeightCalculator().calculate_weights(models, performances)
        
        # 计算基于准确率的权重
        for model_id in models:
            raw_weight = accuracies[model_id] / total_accuracy
            # 确保最小权重
            final_weight = max(self.min_weight, raw_weight)
            
            # 获取置信度（基于使用次数）
            perf = performances.get(model_id)
            confidence = 1.0
            if perf and perf.usage_count > 0:
                # 使用次数越多，置信度越高
                confidence = min(1.0, perf.usage_count / 100.0)
            
            weights[model_id] = ModelWeight(
                model_id=model_id,
                weight=final_weight,
                confidence=confidence,
                metadata={
                    "strategy": "accuracy_based",
                    "raw_accuracy": accuracies[model_id] - self.smoothing_factor,
                    "usage_count": perf.usage_count if perf else 0
                }
            )
        
        # 归一化权重
        self._normalize_weights(weights)
        
        return weights
    
    def validate_weights(self, weights: Dict[str, ModelWeight]) -> bool:
        """验证基于准确率的权重"""
        if not weights:
            return False
        
        total_weight = sum(w.weight for w in weights.values())
        return abs(total_weight - 1.0) < 1e-6
    
    def _normalize_weights(self, weights: Dict[str, ModelWeight]):
        """归一化权重使总和为1"""
        total_weight = sum(w.weight for w in weights.values())
        if total_weight > 0:
            for weight in weights.values():
                weight.weight /= total_weight

class PerformanceBasedWeightCalculator(BaseWeightCalculator):
    """基于综合性能的权重计算器"""
    
    def __init__(self, min_weight: float = 0.05):
        self.min_weight = min_weight
    
    def calculate_weights(self, models: List[str], performances: Dict[str, ModelPerformance]) -> Dict[str, ModelWeight]:
        """基于综合性能计算权重"""
        if not models:
            return {}
        
        weights = {}
        
        # 计算所有模型的性能得分
        scores = {}
        for model_id in models:
            perf = performances.get(model_id)
            if perf:
                scores[model_id] = perf.get_performance_score()
            else:
                scores[model_id] = 0.1  # 默认最低分
        
        total_score = sum(scores.values())
        
        if total_score == 0:
            return EqualWeightCalculator().calculate_weights(models, performances)
        
        # 计算权重
        for model_id in models:
            raw_weight = scores[model_id] / total_score
            final_weight = max(self.min_weight, raw_weight)
            
            perf = performances.get(model_id)
            confidence = 0.5
            if perf:
                # 基于成功率和使用次数计算置信度
                confidence = (perf.success_rate + min(1.0, perf.usage_count / 50.0)) / 2.0
            
            weights[model_id] = ModelWeight(
                model_id=model_id,
                weight=final_weight,
                confidence=confidence,
                metadata={
                    "strategy": "performance_based",
                    "performance_score": scores[model_id],
                    "accuracy": perf.accuracy if perf else 0.0,
                    "success_rate": perf.success_rate if perf else 0.0
                }
            )
        
        # 归一化权重
        self._normalize_weights(weights)
        
        return weights
    
    def validate_weights(self, weights: Dict[str, ModelWeight]) -> bool:
        """验证基于性能的权重"""
        if not weights:
            return False
        
        total_weight = sum(w.weight for w in weights.values())
        return abs(total_weight - 1.0) < 1e-6
    
    def _normalize_weights(self, weights: Dict[str, ModelWeight]):
        """归一化权重"""
        total_weight = sum(w.weight for w in weights.values())
        if total_weight > 0:
            for weight in weights.values():
                weight.weight /= total_weight

class DynamicWeightCalculator(BaseWeightCalculator):
    """动态权重计算器"""
    
    def __init__(self, learning_rate: float = 0.1, decay_factor: float = 0.95):
        self.learning_rate = learning_rate
        self.decay_factor = decay_factor
        self.historical_weights: Dict[str, ModelWeight] = {}
    
    def calculate_weights(self, models: List[str], performances: Dict[str, ModelPerformance]) -> Dict[str, ModelWeight]:
        """动态计算权重"""
        if not models:
            return {}
        
        # 如果没有历史权重，使用基于性能的初始权重
        if not self.historical_weights:
            calculator = PerformanceBasedWeightCalculator()
            self.historical_weights = calculator.calculate_weights(models, performances)
        
        weights = {}
        
        for model_id in models:
            perf = performances.get(model_id)
            historical_weight = self.historical_weights.get(model_id)
            
            if historical_weight and perf:
                # 基于最近性能调整权重
                performance_score = perf.get_performance_score()
                
                # 计算权重调整
                adjustment = self.learning_rate * (performance_score - 0.5)  # 0.5为中性分数
                new_weight = historical_weight.weight * (1 + adjustment)
                
                # 应用衰减因子
                new_weight *= self.decay_factor
                
                # 确保权重在有效范围内
                new_weight = max(0.01, min(0.8, new_weight))
                
                weights[model_id] = ModelWeight(
                    model_id=model_id,
                    weight=new_weight,
                    confidence=min(1.0, perf.usage_count / 20.0),
                    metadata={
                        "strategy": "dynamic",
                        "adjustment": adjustment,
                        "performance_score": performance_score,
                        "previous_weight": historical_weight.weight
                    }
                )
            else:
                # 新模型或无性能数据，使用默认权重
                weights[model_id] = ModelWeight(
                    model_id=model_id,
                    weight=0.1,
                    confidence=0.1,
                    metadata={"strategy": "dynamic", "is_new": True}
                )
        
        # 归一化权重
        self._normalize_weights(weights)
        
        # 更新历史权重
        self.historical_weights.update(weights)
        
        return weights
    
    def validate_weights(self, weights: Dict[str, ModelWeight]) -> bool:
        """验证动态权重"""
        if not weights:
            return False
        
        total_weight = sum(w.weight for w in weights.values())
        return abs(total_weight - 1.0) < 1e-6
    
    def _normalize_weights(self, weights: Dict[str, ModelWeight]):
        """归一化权重"""
        total_weight = sum(w.weight for w in weights.values())
        if total_weight > 0:
            for weight in weights.values():
                weight.weight /= total_weight

class WeightManagementService:
    """权重管理服务"""
    
    def __init__(self):
        self.calculators = {
            WeightStrategy.EQUAL: EqualWeightCalculator(),
            WeightStrategy.ACCURACY_BASED: AccuracyBasedWeightCalculator(),
            WeightStrategy.PERFORMANCE_BASED: PerformanceBasedWeightCalculator(),
            WeightStrategy.DYNAMIC: DynamicWeightCalculator()
        }
        self.manual_weights: Dict[str, Dict[str, ModelWeight]] = {}
    
    def calculate_weights(
        self, 
        strategy: WeightStrategy, 
        models: List[str], 
        performances: Dict[str, ModelPerformance],
        ensemble_id: Optional[str] = None
    ) -> Dict[str, ModelWeight]:
        """计算模型权重"""
        try:
            if strategy == WeightStrategy.MANUAL:
                return self._get_manual_weights(ensemble_id, models)
            
            calculator = self.calculators.get(strategy)
            if not calculator:
                logger.error(f"Unsupported weight strategy: {strategy}")
                return {}
            
            weights = calculator.calculate_weights(models, performances)
            
            # 验证权重
            if not calculator.validate_weights(weights):
                logger.warning(f"Invalid weights calculated for strategy {strategy}, falling back to equal weights")
                return self.calculators[WeightStrategy.EQUAL].calculate_weights(models, performances)
            
            return weights
            
        except Exception as e:
            logger.error(f"Error calculating weights with strategy {strategy}: {e}")
            # 回退到等权重
            return self.calculators[WeightStrategy.EQUAL].calculate_weights(models, performances)
    
    def set_manual_weights(self, ensemble_id: str, weights: Dict[str, float]) -> bool:
        """设置手动权重"""
        try:
            # 验证权重
            if not self._validate_manual_weights(weights):
                return False
            
            # 转换为ModelWeight对象
            model_weights = {}
            for model_id, weight in weights.items():
                model_weights[model_id] = ModelWeight(
                    model_id=model_id,
                    weight=weight,
                    confidence=1.0,
                    metadata={"strategy": "manual", "ensemble_id": ensemble_id}
                )
            
            self.manual_weights[ensemble_id] = model_weights
            logger.info(f"Manual weights set for ensemble {ensemble_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting manual weights for ensemble {ensemble_id}: {e}")
            return False
    
    def get_manual_weights(self, ensemble_id: str) -> Optional[Dict[str, ModelWeight]]:
        """获取手动权重"""
        return self.manual_weights.get(ensemble_id)
    
    def _get_manual_weights(self, ensemble_id: Optional[str], models: List[str]) -> Dict[str, ModelWeight]:
        """获取手动权重（内部方法）"""
        if not ensemble_id or ensemble_id not in self.manual_weights:
            # 如果没有手动权重，使用等权重
            return self.calculators[WeightStrategy.EQUAL].calculate_weights(models, {})
        
        manual_weights = self.manual_weights[ensemble_id]
        
        # 确保所有模型都有权重
        result = {}
        for model_id in models:
            if model_id in manual_weights:
                result[model_id] = manual_weights[model_id]
            else:
                # 新模型使用默认权重
                result[model_id] = ModelWeight(
                    model_id=model_id,
                    weight=0.1,
                    confidence=0.5,
                    metadata={"strategy": "manual", "is_default": True}
                )
        
        # 重新归一化
        self._normalize_weights(result)
        
        return result
    
    def _validate_manual_weights(self, weights: Dict[str, float]) -> bool:
        """验证手动权重"""
        if not weights:
            return False
        
        # 检查权重范围
        for weight in weights.values():
            if weight < 0 or weight > 1:
                return False
        
        # 检查权重总和
        total_weight = sum(weights.values())
        return abs(total_weight - 1.0) < 1e-6
    
    def _normalize_weights(self, weights: Dict[str, ModelWeight]):
        """归一化权重"""
        total_weight = sum(w.weight for w in weights.values())
        if total_weight > 0:
            for weight in weights.values():
                weight.weight /= total_weight
    
    def update_performance(self, model_id: str, performance: ModelPerformance):
        """更新模型性能数据"""
        # 如果使用动态权重策略，更新其性能数据
        dynamic_calculator = self.calculators.get(WeightStrategy.DYNAMIC)
        if isinstance(dynamic_calculator, DynamicWeightCalculator):
            # 动态计算器会在下次计算权重时使用新的性能数据
            pass
    
    def get_weight_explanation(self, weights: Dict[str, ModelWeight]) -> Dict[str, str]:
        """获取权重分配的解释"""
        explanations = {}
        
        for model_id, weight in weights.items():
            strategy = weight.metadata.get("strategy", "unknown")
            
            if strategy == "equal":
                explanations[model_id] = f"等权重分配: {weight.weight:.3f}"
            elif strategy == "accuracy_based":
                accuracy = weight.metadata.get("raw_accuracy", 0)
                explanations[model_id] = f"基于准确率 {accuracy:.3f}: {weight.weight:.3f}"
            elif strategy == "performance_based":
                score = weight.metadata.get("performance_score", 0)
                explanations[model_id] = f"基于性能得分 {score:.3f}: {weight.weight:.3f}"
            elif strategy == "dynamic":
                prev_weight = weight.metadata.get("previous_weight", 0)
                adjustment = weight.metadata.get("adjustment", 0)
                explanations[model_id] = f"动态调整 {prev_weight:.3f}→{weight.weight:.3f} (调整: {adjustment:+.3f})"
            elif strategy == "manual":
                explanations[model_id] = f"手动设置: {weight.weight:.3f}"
            else:
                explanations[model_id] = f"权重: {weight.weight:.3f}"
        
        return explanations

# 全局权重管理服务实例
weight_management_service = WeightManagementService()