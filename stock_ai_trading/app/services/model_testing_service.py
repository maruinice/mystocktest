"""
模型测试服务
提供单模型和多模型组合的测试功能
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .model_connection_service import ModelConnectionService, ModelResponse
from .weight_management_service import WeightManagementService, ModelWeight, WeightStrategy

logger = logging.getLogger(__name__)

class TestType(Enum):
    """测试类型枚举"""
    SINGLE_MODEL = "single_model"
    MULTI_MODEL = "multi_model"
    PERFORMANCE = "performance"
    STRESS = "stress"
    ACCURACY = "accuracy"

class TestStatus(Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TestCase:
    """测试用例数据类"""
    test_id: str
    name: str
    input_text: str
    expected_output: Optional[str] = None
    test_type: TestType = TestType.SINGLE_MODEL
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.test_id:
            self.test_id = str(uuid.uuid4())

@dataclass
class SingleModelTestResult:
    """单模型测试结果"""
    model_id: str
    test_case: TestCase
    response: ModelResponse
    accuracy_score: Optional[float] = None
    similarity_score: Optional[float] = None
    test_duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class MultiModelTestResult:
    """多模型测试结果"""
    test_case: TestCase
    individual_results: List[SingleModelTestResult]
    combined_response: str = ""
    weights_used: Dict[str, ModelWeight] = field(default_factory=dict)
    fusion_strategy: str = ""
    overall_accuracy: Optional[float] = None
    test_duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TestSession:
    """测试会话"""
    session_id: str
    name: str
    test_cases: List[TestCase]
    models: List[str]
    status: TestStatus = TestStatus.PENDING
    results: List[Any] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AccuracyCalculator:
    """准确率计算器"""
    
    @staticmethod
    def calculate_exact_match(actual: str, expected: str) -> float:
        """计算精确匹配准确率"""
        if not actual or not expected:
            return 0.0
        return 1.0 if actual.strip().lower() == expected.strip().lower() else 0.0
    
    @staticmethod
    def calculate_token_overlap(actual: str, expected: str) -> float:
        """计算词汇重叠准确率"""
        if not actual or not expected:
            return 0.0
        
        actual_tokens = set(actual.lower().split())
        expected_tokens = set(expected.lower().split())
        
        if not expected_tokens:
            return 0.0
        
        intersection = actual_tokens.intersection(expected_tokens)
        return len(intersection) / len(expected_tokens)
    
    @staticmethod
    def calculate_jaccard_similarity(actual: str, expected: str) -> float:
        """计算Jaccard相似度"""
        if not actual or not expected:
            return 0.0
        
        actual_tokens = set(actual.lower().split())
        expected_tokens = set(expected.lower().split())
        
        intersection = actual_tokens.intersection(expected_tokens)
        union = actual_tokens.union(expected_tokens)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def calculate_semantic_similarity(actual: str, expected: str) -> float:
        """计算语义相似度（简化版本）"""
        # 这里使用简化的语义相似度计算
        # 在实际应用中，可以使用更复杂的NLP模型
        
        if not actual or not expected:
            return 0.0
        
        # 基于长度和词汇重叠的简单语义相似度
        length_similarity = 1.0 - abs(len(actual) - len(expected)) / max(len(actual), len(expected))
        token_similarity = AccuracyCalculator.calculate_token_overlap(actual, expected)
        
        return (length_similarity * 0.3 + token_similarity * 0.7)

class ModelTestingService:
    """模型测试服务"""
    
    def __init__(self, connection_service: ModelConnectionService, weight_service: WeightManagementService):
        self.connection_service = connection_service
        self.weight_service = weight_service
        self.test_sessions: Dict[str, TestSession] = {}
        self.accuracy_calculator = AccuracyCalculator()
    
    async def test_single_model(
        self, 
        model_id: str, 
        test_case: TestCase,
        calculate_accuracy: bool = True
    ) -> SingleModelTestResult:
        """测试单个模型"""
        start_time = time.time()
        
        try:
            # 发送消息到模型
            response = await self.connection_service.send_message(model_id, test_case.input_text)
            
            test_duration = time.time() - start_time
            
            # 计算准确率
            accuracy_score = None
            similarity_score = None
            
            if calculate_accuracy and test_case.expected_output:
                accuracy_score = self.accuracy_calculator.calculate_token_overlap(
                    response.content, test_case.expected_output
                )
                similarity_score = self.accuracy_calculator.calculate_semantic_similarity(
                    response.content, test_case.expected_output
                )
            
            return SingleModelTestResult(
                model_id=model_id,
                test_case=test_case,
                response=response,
                accuracy_score=accuracy_score,
                similarity_score=similarity_score,
                test_duration=test_duration
            )
            
        except Exception as e:
            test_duration = time.time() - start_time
            logger.error(f"Error testing model {model_id}: {e}")
            
            # 创建错误响应
            error_response = ModelResponse(
                success=False,
                error_message=str(e),
                error_code="TEST_ERROR"
            )
            
            return SingleModelTestResult(
                model_id=model_id,
                test_case=test_case,
                response=error_response,
                test_duration=test_duration
            )
    
    async def test_multiple_models(
        self, 
        model_ids: List[str], 
        test_case: TestCase,
        weight_strategy: WeightStrategy = WeightStrategy.EQUAL,
        fusion_strategy: str = "weighted_voting"
    ) -> MultiModelTestResult:
        """测试多个模型"""
        start_time = time.time()
        
        try:
            # 并发测试所有模型
            tasks = []
            for model_id in model_ids:
                task = self.test_single_model(model_id, test_case)
                tasks.append(task)
            
            individual_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            valid_results = []
            for i, result in enumerate(individual_results):
                if isinstance(result, Exception):
                    logger.error(f"Model {model_ids[i]} test failed: {result}")
                    # 创建失败结果
                    error_response = ModelResponse(
                        success=False,
                        error_message=str(result),
                        error_code="TEST_EXCEPTION"
                    )
                    error_result = SingleModelTestResult(
                        model_id=model_ids[i],
                        test_case=test_case,
                        response=error_response,
                        test_duration=0.0
                    )
                    individual_results[i] = error_result
                else:
                    if result.response.success:
                        valid_results.append(result)
            
            # 计算权重
            performances = {}
            for result in individual_results:
                if isinstance(result, SingleModelTestResult):
                    # 创建临时性能数据用于权重计算
                    from .weight_management_service import ModelPerformance
                    perf = ModelPerformance(
                        model_id=result.model_id,
                        accuracy=result.accuracy_score or 0.0,
                        response_time=result.test_duration,
                        success_rate=1.0 if result.response.success else 0.0
                    )
                    performances[result.model_id] = perf
            
            weights = self.weight_service.calculate_weights(
                weight_strategy, model_ids, performances
            )
            
            # 融合结果
            combined_response = self._fuse_responses(valid_results, weights, fusion_strategy)
            
            # 计算整体准确率
            overall_accuracy = None
            if test_case.expected_output:
                overall_accuracy = self.accuracy_calculator.calculate_token_overlap(
                    combined_response, test_case.expected_output
                )
            
            test_duration = time.time() - start_time
            
            return MultiModelTestResult(
                test_case=test_case,
                individual_results=individual_results,
                combined_response=combined_response,
                weights_used=weights,
                fusion_strategy=fusion_strategy,
                overall_accuracy=overall_accuracy,
                test_duration=test_duration
            )
            
        except Exception as e:
            test_duration = time.time() - start_time
            logger.error(f"Error in multi-model test: {e}")
            
            return MultiModelTestResult(
                test_case=test_case,
                individual_results=[],
                combined_response=f"测试失败: {str(e)}",
                test_duration=test_duration
            )
    
    def _fuse_responses(
        self, 
        results: List[SingleModelTestResult], 
        weights: Dict[str, ModelWeight],
        strategy: str
    ) -> str:
        """融合多个模型的响应"""
        if not results:
            return "无有效响应"
        
        if strategy == "weighted_voting":
            return self._weighted_voting_fusion(results, weights)
        elif strategy == "best_response":
            return self._best_response_fusion(results, weights)
        elif strategy == "consensus":
            return self._consensus_fusion(results, weights)
        else:
            # 默认使用加权投票
            return self._weighted_voting_fusion(results, weights)
    
    def _weighted_voting_fusion(
        self, 
        results: List[SingleModelTestResult], 
        weights: Dict[str, ModelWeight]
    ) -> str:
        """加权投票融合"""
        if not results:
            return ""
        
        # 根据权重选择最佳响应
        best_result = None
        best_score = -1
        
        for result in results:
            weight = weights.get(result.model_id)
            if weight:
                # 计算综合得分（权重 * 置信度）
                score = weight.weight * weight.confidence
                if result.accuracy_score:
                    score *= (1 + result.accuracy_score)
                
                if score > best_score:
                    best_score = score
                    best_result = result
        
        return best_result.response.content if best_result else results[0].response.content
    
    def _best_response_fusion(
        self, 
        results: List[SingleModelTestResult], 
        weights: Dict[str, ModelWeight]
    ) -> str:
        """最佳响应融合"""
        if not results:
            return ""
        
        # 选择准确率最高的响应
        best_result = max(
            results, 
            key=lambda r: (r.accuracy_score or 0.0, weights.get(r.model_id, ModelWeight("", 0.0)).weight)
        )
        
        return best_result.response.content
    
    def _consensus_fusion(
        self, 
        results: List[SingleModelTestResult], 
        weights: Dict[str, ModelWeight]
    ) -> str:
        """共识融合"""
        if not results:
            return ""
        
        # 简化的共识算法：选择最长的响应（假设更详细）
        responses = [r.response.content for r in results if r.response.success]
        if not responses:
            return "无有效响应"
        
        # 按长度和权重排序
        weighted_responses = []
        for result in results:
            if result.response.success:
                weight = weights.get(result.model_id, ModelWeight("", 0.0)).weight
                score = len(result.response.content) * weight
                weighted_responses.append((score, result.response.content))
        
        if weighted_responses:
            weighted_responses.sort(key=lambda x: x[0], reverse=True)
            return weighted_responses[0][1]
        
        return responses[0]
    
    async def run_test_session(
        self, 
        session: TestSession,
        weight_strategy: WeightStrategy = WeightStrategy.EQUAL,
        fusion_strategy: str = "weighted_voting"
    ) -> TestSession:
        """运行测试会话"""
        session.status = TestStatus.RUNNING
        session.start_time = datetime.now()
        
        try:
            results = []
            
            for test_case in session.test_cases:
                if len(session.models) == 1:
                    # 单模型测试
                    result = await self.test_single_model(session.models[0], test_case)
                    results.append(result)
                else:
                    # 多模型测试
                    result = await self.test_multiple_models(
                        session.models, test_case, weight_strategy, fusion_strategy
                    )
                    results.append(result)
            
            session.results = results
            session.status = TestStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Test session {session.session_id} failed: {e}")
            session.status = TestStatus.FAILED
            session.metadata["error"] = str(e)
        
        finally:
            session.end_time = datetime.now()
        
        return session
    
    def create_test_session(
        self, 
        name: str, 
        test_cases: List[TestCase], 
        models: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> TestSession:
        """创建测试会话"""
        session_id = str(uuid.uuid4())
        
        session = TestSession(
            session_id=session_id,
            name=name,
            test_cases=test_cases,
            models=models,
            metadata=metadata or {}
        )
        
        self.test_sessions[session_id] = session
        return session
    
    def get_test_session(self, session_id: str) -> Optional[TestSession]:
        """获取测试会话"""
        return self.test_sessions.get(session_id)
    
    def list_test_sessions(self) -> List[TestSession]:
        """列出所有测试会话"""
        return list(self.test_sessions.values())
    
    async def benchmark_models(
        self, 
        model_ids: List[str], 
        test_cases: List[TestCase],
        iterations: int = 1
    ) -> Dict[str, Dict[str, float]]:
        """基准测试模型"""
        benchmark_results = {}
        
        for model_id in model_ids:
            model_stats = {
                "avg_response_time": 0.0,
                "avg_accuracy": 0.0,
                "success_rate": 0.0,
                "total_tests": 0
            }
            
            total_time = 0.0
            total_accuracy = 0.0
            successful_tests = 0
            total_tests = 0
            
            for iteration in range(iterations):
                for test_case in test_cases:
                    result = await self.test_single_model(model_id, test_case)
                    
                    total_time += result.test_duration
                    total_tests += 1
                    
                    if result.response.success:
                        successful_tests += 1
                        if result.accuracy_score is not None:
                            total_accuracy += result.accuracy_score
            
            if total_tests > 0:
                model_stats["avg_response_time"] = total_time / total_tests
                model_stats["success_rate"] = successful_tests / total_tests
                model_stats["total_tests"] = total_tests
                
                if successful_tests > 0:
                    model_stats["avg_accuracy"] = total_accuracy / successful_tests
            
            benchmark_results[model_id] = model_stats
        
        return benchmark_results
    
    async def stress_test_model(
        self, 
        model_id: str, 
        test_case: TestCase,
        concurrent_requests: int = 10,
        duration_seconds: int = 60
    ) -> Dict[str, Any]:
        """压力测试模型"""
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        results = []
        total_requests = 0
        successful_requests = 0
        
        async def single_request():
            nonlocal total_requests, successful_requests
            result = await self.test_single_model(model_id, test_case, calculate_accuracy=False)
            total_requests += 1
            if result.response.success:
                successful_requests += 1
            return result
        
        # 运行压力测试
        while time.time() < end_time:
            # 创建并发请求
            tasks = [single_request() for _ in range(concurrent_requests)]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if not isinstance(result, Exception):
                    results.append(result)
        
        # 计算统计信息
        if results:
            response_times = [r.test_duration for r in results]
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # 计算百分位数
            sorted_times = sorted(response_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p50 = p95 = p99 = 0.0
        
        return {
            "model_id": model_id,
            "duration_seconds": duration_seconds,
            "concurrent_requests": concurrent_requests,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0.0,
            "requests_per_second": total_requests / duration_seconds,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "p50_response_time": p50,
            "p95_response_time": p95,
            "p99_response_time": p99
        }
    
    def generate_test_report(self, session: TestSession) -> Dict[str, Any]:
        """生成测试报告"""
        if not session.results:
            return {"error": "No test results available"}
        
        report = {
            "session_id": session.session_id,
            "session_name": session.name,
            "status": session.status.value,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "total_tests": len(session.test_cases),
            "models_tested": session.models,
            "summary": {},
            "detailed_results": []
        }
        
        # 计算汇总统计
        total_duration = 0.0
        successful_tests = 0
        total_accuracy = 0.0
        accuracy_count = 0
        
        for result in session.results:
            if isinstance(result, SingleModelTestResult):
                total_duration += result.test_duration
                if result.response.success:
                    successful_tests += 1
                if result.accuracy_score is not None:
                    total_accuracy += result.accuracy_score
                    accuracy_count += 1
                
                report["detailed_results"].append({
                    "test_id": result.test_case.test_id,
                    "model_id": result.model_id,
                    "success": result.response.success,
                    "response_time": result.test_duration,
                    "accuracy_score": result.accuracy_score,
                    "similarity_score": result.similarity_score
                })
                
            elif isinstance(result, MultiModelTestResult):
                total_duration += result.test_duration
                if result.combined_response:
                    successful_tests += 1
                if result.overall_accuracy is not None:
                    total_accuracy += result.overall_accuracy
                    accuracy_count += 1
                
                report["detailed_results"].append({
                    "test_id": result.test_case.test_id,
                    "models": [r.model_id for r in result.individual_results],
                    "fusion_strategy": result.fusion_strategy,
                    "response_time": result.test_duration,
                    "overall_accuracy": result.overall_accuracy,
                    "individual_results": len(result.individual_results)
                })
        
        # 汇总统计
        report["summary"] = {
            "success_rate": successful_tests / len(session.results) if session.results else 0.0,
            "avg_response_time": total_duration / len(session.results) if session.results else 0.0,
            "avg_accuracy": total_accuracy / accuracy_count if accuracy_count > 0 else None,
            "total_duration": total_duration
        }
        
        return report

# 创建全局测试服务实例（需要在使用时注入依赖）
def create_model_testing_service(connection_service, weight_service):
    """创建模型测试服务实例"""
    return ModelTestingService(connection_service, weight_service)