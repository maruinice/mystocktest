"""
Agent管理服务
"""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..models.agent_models import (
    AIAgent, AgentType, AgentAnalysisRecord, 
    StockSelectionScheme, StockSelectionResult,
    AgentAnalysisSession, SessionType, SessionStatus,
    AnalysisStatus, Recommendation, RiskLevel
)

logger = logging.getLogger(__name__)


class AgentService:
    """Agent管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Agent CRUD ====================
    
    def create_agent(self, agent_data: Dict[str, Any]) -> AIAgent:
        """创建Agent"""
        agent_id = agent_data.get('agent_id') or f"agent_{uuid.uuid4().hex[:12]}"
        
        agent = AIAgent(
            agent_id=agent_id,
            name=agent_data['name'],
            display_name=agent_data.get('display_name'),
            description=agent_data.get('description'),
            agent_type=agent_data['agent_type'],
            model_id=agent_data.get('model_id'),
            system_prompt=agent_data.get('system_prompt'),
            enabled=agent_data.get('enabled', True),
            priority=agent_data.get('priority', 1),
            weight=agent_data.get('weight', 1.0),
            config_json=agent_data.get('config_json'),
            created_by=agent_data.get('created_by')
        )
        
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        
        logger.info(f"创建Agent成功: {agent.agent_id}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[AIAgent]:
        """获取Agent"""
        return self.db.query(AIAgent).filter(AIAgent.agent_id == agent_id).first()
    
    def list_agents(
        self, 
        agent_type: Optional[str] = None,
        enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取Agent列表"""
        query = self.db.query(AIAgent)
        
        # 筛选条件
        if agent_type:
            query = query.filter(AIAgent.agent_type == agent_type)
        if enabled is not None:
            query = query.filter(AIAgent.enabled == enabled)
        
        # 总数
        total = query.count()
        
        # 分页
        agents = query.order_by(AIAgent.priority, AIAgent.created_at.desc())\
                     .offset((page - 1) * page_size)\
                     .limit(page_size)\
                     .all()
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': agents
        }
    
    def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Optional[AIAgent]:
        """更新Agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        # 更新字段
        for key, value in update_data.items():
            if hasattr(agent, key) and key not in ['agent_id', 'created_at', 'created_by']:
                if key == 'agent_type' and value:
                    setattr(agent, key, value)
                else:
                    setattr(agent, key, value)
        
        agent.updated_by = update_data.get('updated_by')
        
        self.db.commit()
        self.db.refresh(agent)
        
        logger.info(f"更新Agent成功: {agent_id}")
        return agent
    
    def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        self.db.delete(agent)
        self.db.commit()
        
        logger.info(f"删除Agent成功: {agent_id}")
        return True
    
    def toggle_agent_status(self, agent_id: str, enabled: bool) -> Optional[AIAgent]:
        """切换Agent启用状态"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        agent.enabled = enabled
        self.db.commit()
        self.db.refresh(agent)
        
        logger.info(f"切换Agent状态: {agent_id} -> {enabled}")
        return agent
    
    # ==================== 选股方案 CRUD ====================
    
    def create_scheme(self, scheme_data: Dict[str, Any]) -> StockSelectionScheme:
        """创建选股方案"""
        scheme_id = scheme_data.get('scheme_id') or f"scheme_{uuid.uuid4().hex[:12]}"
        
        scheme = StockSelectionScheme(
            scheme_id=scheme_id,
            name=scheme_data['name'],
            description=scheme_data.get('description'),
            filter_conditions=scheme_data.get('filter_conditions'),
            agent_config=scheme_data.get('agent_config'),
            stock_pool=scheme_data.get('stock_pool'),
            enabled=scheme_data.get('enabled', True),
            created_by=scheme_data.get('created_by')
        )
        
        self.db.add(scheme)
        self.db.commit()
        self.db.refresh(scheme)
        
        logger.info(f"创建选股方案成功: {scheme.scheme_id}")
        return scheme
    
    def get_scheme(self, scheme_id: str) -> Optional[StockSelectionScheme]:
        """获取选股方案"""
        return self.db.query(StockSelectionScheme).filter(
            StockSelectionScheme.scheme_id == scheme_id
        ).first()
    
    def list_schemes(
        self,
        enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取选股方案列表"""
        query = self.db.query(StockSelectionScheme)
        
        if enabled is not None:
            query = query.filter(StockSelectionScheme.enabled == enabled)
        
        total = query.count()
        
        schemes = query.order_by(StockSelectionScheme.created_at.desc())\
                      .offset((page - 1) * page_size)\
                      .limit(page_size)\
                      .all()
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': schemes
        }
    
    def update_scheme(self, scheme_id: str, update_data: Dict[str, Any]) -> Optional[StockSelectionScheme]:
        """更新选股方案"""
        scheme = self.get_scheme(scheme_id)
        if not scheme:
            return None
        
        for key, value in update_data.items():
            if hasattr(scheme, key) and key not in ['scheme_id', 'created_at', 'created_by']:
                setattr(scheme, key, value)
        
        scheme.updated_by = update_data.get('updated_by')
        
        self.db.commit()
        self.db.refresh(scheme)
        
        logger.info(f"更新选股方案成功: {scheme_id}")
        return scheme
    
    def delete_scheme(self, scheme_id: str) -> bool:
        """删除选股方案"""
        scheme = self.get_scheme(scheme_id)
        if not scheme:
            return False
        
        self.db.delete(scheme)
        self.db.commit()
        
        logger.info(f"删除选股方案成功: {scheme_id}")
        return True
    
    # ==================== 分析会话管理 ====================
    
    def create_session(self, session_data: Dict[str, Any]) -> AgentAnalysisSession:
        """创建分析会话"""
        session_id = session_data.get('session_id') or f"session_{uuid.uuid4().hex[:12]}"
        
        session = AgentAnalysisSession(
            session_id=session_id,
            session_type=session_data['session_type'],
            scheme_id=session_data.get('scheme_id'),
            stock_codes=session_data.get('stock_codes', []),
            agent_ids=session_data.get('agent_ids', []),
            total_stocks=len(session_data.get('stock_codes', [])),
            total_agents=len(session_data.get('agent_ids', [])),
            created_by=session_data.get('created_by')
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"创建分析会话成功: {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[AgentAnalysisSession]:
        """获取分析会话"""
        return self.db.query(AgentAnalysisSession).filter(
            AgentAnalysisSession.session_id == session_id
        ).first()
    
    def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[AgentAnalysisSession]:
        """更新会话状态"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        session.status = status
        if progress is not None:
            session.progress = progress
        if error_message:
            session.error_message = error_message
        
        if status == SessionStatus.RUNNING and not session.started_at:
            session.started_at = datetime.now()
        elif status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED]:
            session.completed_at = datetime.now()
            session.progress = 100 if status == SessionStatus.COMPLETED else session.progress
        
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def list_sessions(
        self,
        session_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取会话列表"""
        query = self.db.query(AgentAnalysisSession)
        
        if session_type:
            query = query.filter(AgentAnalysisSession.session_type == session_type)
        if status:
            query = query.filter(AgentAnalysisSession.status == status)
        
        total = query.count()
        
        sessions = query.order_by(AgentAnalysisSession.created_at.desc())\
                       .offset((page - 1) * page_size)\
                       .limit(page_size)\
                       .all()
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': sessions
        }
    
    # ==================== 分析记录管理 ====================
    
    def create_analysis_record(self, record_data: Dict[str, Any]) -> AgentAnalysisRecord:
        """创建分析记录"""
        record_id = record_data.get('record_id') or f"record_{uuid.uuid4().hex[:12]}"
        
        record = AgentAnalysisRecord(
            record_id=record_id,
            session_id=record_data['session_id'],
            stock_code=record_data['stock_code'],
            agent_id=record_data['agent_id'],
            agent_type=record_data['agent_type'],
            analysis_content=record_data.get('analysis_content'),
            score=record_data.get('score'),
            confidence=record_data.get('confidence'),
            recommendation=record_data.get('recommendation'),
            key_points=record_data.get('key_points'),
            risk_factors=record_data.get('risk_factors'),
            opportunities=record_data.get('opportunities'),
            market_data=record_data.get('market_data'),
            model_used=record_data.get('model_used'),
            tokens_used=record_data.get('tokens_used'),
            response_time=record_data.get('response_time'),
            status=record_data.get('status', 'completed'),
            error_message=record_data.get('error_message'),
            analysis_time=record_data.get('analysis_time', datetime.now())
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    def get_session_records(self, session_id: str) -> List[AgentAnalysisRecord]:
        """获取会话的所有分析记录"""
        return self.db.query(AgentAnalysisRecord).filter(
            AgentAnalysisRecord.session_id == session_id
        ).order_by(AgentAnalysisRecord.analysis_time).all()
    
    def get_stock_records(self, session_id: str, stock_code: str) -> List[AgentAnalysisRecord]:
        """获取某只股票的所有Agent分析记录"""
        return self.db.query(AgentAnalysisRecord).filter(
            and_(
                AgentAnalysisRecord.session_id == session_id,
                AgentAnalysisRecord.stock_code == stock_code
            )
        ).all()
    
    # ==================== 选股结果管理 ====================
    
    def create_selection_result(self, result_data: Dict[str, Any]) -> StockSelectionResult:
        """创建选股结果"""
        result_id = result_data.get('result_id') or f"result_{uuid.uuid4().hex[:12]}"
        
        result = StockSelectionResult(
            result_id=result_id,
            session_id=result_data['session_id'],
            scheme_id=result_data['scheme_id'],
            stock_code=result_data['stock_code'],
            stock_name=result_data.get('stock_name'),
            final_score=result_data.get('final_score'),
            agent_scores=result_data.get('agent_scores'),
            recommendation=result_data.get('recommendation'),
            consensus_level=result_data.get('consensus_level'),
            risk_level=result_data.get('risk_level'),
            summary=result_data.get('summary'),
            strengths=result_data.get('strengths'),
            weaknesses=result_data.get('weaknesses'),
            market_data_snapshot=result_data.get('market_data_snapshot'),
            rank=result_data.get('rank')
        )
        
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        
        return result
    
    def get_session_results(
        self,
        session_id: str,
        order_by: str = 'score'
    ) -> List[StockSelectionResult]:
        """获取会话的选股结果"""
        query = self.db.query(StockSelectionResult).filter(
            StockSelectionResult.session_id == session_id
        )
        
        if order_by == 'score':
            query = query.order_by(desc(StockSelectionResult.final_score))
        elif order_by == 'rank':
            query = query.order_by(StockSelectionResult.rank)
        
        return query.all()
    
    # ==================== 统计信息 ====================
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent统计信息"""
        agent = self.get_agent(agent_id)
        if not agent:
            return {}
        
        # 最近分析记录
        recent_records = self.db.query(AgentAnalysisRecord).filter(
            AgentAnalysisRecord.agent_id == agent_id
        ).order_by(desc(AgentAnalysisRecord.analysis_time)).limit(10).all()
        
        return {
            'agent_id': agent.agent_id,
            'name': agent.name,
            'total_analyses': agent.total_analyses,
            'success_analyses': agent.success_analyses,
            'success_rate': agent.success_analyses / agent.total_analyses if agent.total_analyses > 0 else 0,
            'avg_score': agent.avg_score,
            'recent_records': recent_records
        }
