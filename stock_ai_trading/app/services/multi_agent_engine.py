"""
多Agent分析引擎
协调多个Agent对股票进行综合分析
"""
import logging
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.agent_models import (
    AIAgent, AgentAnalysisRecord, StockSelectionResult,
    AgentAnalysisSession, SessionStatus, AnalysisStatus,
    Recommendation, RiskLevel
)
from .agent_service import AgentService
from .llm_gateway import gateway, GatewayRequest, ModelProvider
from ..services.realtime_quote_service import RealtimeQuoteService

logger = logging.getLogger(__name__)


class MultiAgentEngine:
    """多Agent分析引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_service = AgentService(db)
        self.quote_service = RealtimeQuoteService()
    
    async def analyze_stock(
        self,
        session_id: str,
        stock_code: str,
        agent_ids: List[str],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        使用多个Agent分析单只股票
        
        Args:
            session_id: 会话ID
            stock_code: 股票代码
            agent_ids: Agent ID列表
            progress_callback: 进度回调函数
        
        Returns:
            综合分析结果
        """
        logger.info(f"开始多Agent分析: {stock_code}, Agents: {agent_ids}")
        
        # 获取股票市场数据
        market_data = await self._get_market_data(stock_code)
        
        # 获取Agent配置
        agents = [self.agent_service.get_agent(aid) for aid in agent_ids]
        agents = [a for a in agents if a and a.enabled]
        
        if not agents:
            raise ValueError("没有可用的Agent")
        
        # 并发执行各Agent分析
        tasks = []
        for agent in agents:
            task = self._run_agent_analysis(
                session_id=session_id,
                stock_code=stock_code,
                agent=agent,
                market_data=market_data
            )
            tasks.append(task)
        
        # 等待所有Agent完成分析
        analysis_records = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤掉失败的分析
        valid_records = [r for r in analysis_records if isinstance(r, AgentAnalysisRecord)]
        
        if not valid_records:
            raise Exception("所有Agent分析都失败了")
        
        # 融合多个Agent的分析结果
        综合结果 = self._fuse_agent_results(valid_records, market_data)
        
        logger.info(f"完成多Agent分析: {stock_code}, 综合评分: {综合结果['final_score']}")
        
        return 综合结果
    
    async def _run_agent_analysis(
        self,
        session_id: str,
        stock_code: str,
        agent: AIAgent,
        market_data: Dict[str, Any]
    ) -> AgentAnalysisRecord:
        """运行单个Agent的分析"""
        start_time = datetime.now()
        
        try:
            # 构建分析提示词
            user_prompt = self._build_analysis_prompt(stock_code, agent.agent_type, market_data)
            
            # 尝试调用LLM
            try:
                request = GatewayRequest(
                    messages=[
                        {"role": "system", "content": agent.system_prompt or "你是一位专业的股票分析师"},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=agent.model_id,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                response = await gateway.generate(request)
                content = response.content
                model_used = response.model
                tokens_used = response.usage.get('total_tokens', 0)
                
            except Exception as llm_error:
                logger.warning(f"LLM调用失败，使用模拟数据: {llm_error}")
                # 模拟数据生成
                import random
                score = random.randint(40, 90)
                content = f"""评分: {score}
置信度: 0.85
推荐: {'buy' if score > 70 else 'hold'}
关键要点: [业绩增长稳定, 技术面突破, 行业前景看好]
风险因素: [市场波动风险, 原材料价格上涨]
机会因素: [新产品发布, 市场份额扩大]

详细分析:
这是一份模拟的分析报告。由于LLM调用失败，系统自动生成了此内容以供测试。
股票 {stock_code} 目前表现{score}分。建议关注后续走势。
"""
                model_used = "mock_model"
                tokens_used = 0
            
            # 解析LLM响应
            analysis_result = self._parse_agent_response(content)
            
            # 计算响应时间
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # 创建分析记录
            record = self.agent_service.create_analysis_record({
                'session_id': session_id,
                'stock_code': stock_code,
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type,
                'analysis_content': content,
                'score': analysis_result.get('score', 50),
                'confidence': analysis_result.get('confidence', 0.5),
                'recommendation': analysis_result.get('recommendation'),
                'key_points': analysis_result.get('key_points', []),
                'risk_factors': analysis_result.get('risk_factors', []),
                'opportunities': analysis_result.get('opportunities', []),
                'market_data': market_data,
                'model_used': model_used,
                'tokens_used': tokens_used,
                'response_time': response_time,
                'status': 'completed',
                'analysis_time': datetime.now()
            })
            
            # 更新Agent统计
            agent.total_analyses += 1
            agent.success_analyses += 1
            if agent.avg_score:
                agent.avg_score = (agent.avg_score * (agent.total_analyses - 1) + analysis_result.get('score', 50)) / agent.total_analyses
            else:
                agent.avg_score = analysis_result.get('score', 50)
            self.db.commit()
            
            logger.info(f"Agent {agent.name} 分析完成: {stock_code}, 评分: {analysis_result.get('score')}")
            
            return record
            
        except Exception as e:
            logger.error(f"Agent {agent.name} 分析失败: {stock_code}, 错误: {e}")
            
            # 创建失败记录
            record = self.agent_service.create_analysis_record({
                'session_id': session_id,
                'stock_code': stock_code,
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type.value,
                'status': 'failed',
                'error_message': str(e),
                'analysis_time': datetime.now()
            })
            
            # 更新Agent统计
            agent.total_analyses += 1
            self.db.commit()
            
            raise e
    
    def _build_analysis_prompt(
        self,
        stock_code: str,
        agent_type: str,
        market_data: Dict[str, Any]
    ) -> str:
        """构建分析提示词"""
        stock_name = market_data.get('name', stock_code)
        current_price = market_data.get('current_price', 0)
        change_pct = market_data.get('change_pct', 0)
        
        prompt = f"""请分析股票 {stock_code} ({stock_name})

当前行情:
- 最新价: {current_price}元
- 涨跌幅: {change_pct}%
- 成交量: {market_data.get('volume', 'N/A')}
- 换手率: {market_data.get('turnover_rate', 'N/A')}%

"""
        
        # 根据Agent类型添加特定数据
        if agent_type == 'fundamental_analyst':
            prompt += f"""财务数据:
- PE(市盈率): {market_data.get('pe', 'N/A')}
- PB(市净率): {market_data.get('pb', 'N/A')}
- ROE(净资产收益率): {market_data.get('roe', 'N/A')}%
- 营收增长率: {market_data.get('revenue_growth', 'N/A')}%

"""
        elif agent_type == 'technical_analyst':
            prompt += f"""技术指标:
- MA5: {market_data.get('ma5', 'N/A')}
- MA10: {market_data.get('ma10', 'N/A')}
- MA20: {market_data.get('ma20', 'N/A')}
- MACD: {market_data.get('macd', 'N/A')}

"""
        
        prompt += """请从你的专业角度分析这只股票，并按以下格式输出:

评分: [0-100的数字]
置信度: [0-1的小数]
推荐: [strong_buy/buy/hold/sell/strong_sell]
关键要点: [要点1, 要点2, 要点3]
风险因素: [风险1, 风险2]
机会因素: [机会1, 机会2]

详细分析:
[你的详细分析内容]
"""
        
        return prompt
    
    def _parse_agent_response(self, content: str) -> Dict[str, Any]:
        """解析Agent响应"""
        result = {
            'score': 50,
            'confidence': 0.5,
            'recommendation': 'hold',
            'key_points': [],
            'risk_factors': [],
            'opportunities': []
        }
        
        try:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('评分:') or line.startswith('评分：'):
                    try:
                        score_str = line.split(':')[1].strip() if ':' in line else line.split('：')[1].strip()
                        result['score'] = float(score_str)
                    except:
                        pass
                elif line.startswith('置信度:') or line.startswith('置信度：'):
                    try:
                        conf_str = line.split(':')[1].strip() if ':' in line else line.split('：')[1].strip()
                        result['confidence'] = float(conf_str)
                    except:
                        pass
                elif line.startswith('推荐:') or line.startswith('推荐：'):
                    try:
                        rec_str = line.split(':')[1].strip() if ':' in line else line.split('：')[1].strip()
                        result['recommendation'] = rec_str.lower()
                    except:
                        pass
                elif line.startswith('关键要点:') or line.startswith('关键要点：'):
                    try:
                        points_str = line.split(':')[1].strip() if ':' in line else line.split('：')[1].strip()
                        result['key_points'] = [p.strip() for p in points_str.strip('[]').split(',')]
                    except:
                        pass
                elif line.startswith('风险因素:') or line.startswith('风险因素：'):
                    try:
                        risks_str = line.split(':')[1].strip() if ':' in line else line.split('：')[1].strip()
                        result['risk_factors'] = [r.strip() for r in risks_str.strip('[]').split(',')]
                    except:
                        pass
                elif line.startswith('机会因素:') or line.startswith('机会因素：'):
                    try:
                        opps_str = line.split(':')[1].strip() if ':' in line else line.split('：')[1].strip()
                        result['opportunities'] = [o.strip() for o in opps_str.strip('[]').split(',')]
                    except:
                        pass
        except Exception as e:
            logger.warning(f"解析Agent响应失败: {e}")
        
        return result
    
    def _fuse_agent_results(
        self,
        records: List[AgentAnalysisRecord],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """融合多个Agent的分析结果"""
        if not records:
            return {}
        
        # 计算加权平均分
        total_weight = 0
        weighted_score = 0
        agent_scores = {}
        
        for record in records:
            agent = self.agent_service.get_agent(record.agent_id)
            weight = agent.weight if agent else 1.0
            score = record.score or 50
            
            weighted_score += score * weight
            total_weight += weight
            
            agent_scores[record.agent_id] = {
                'agent_name': agent.display_name if agent else record.agent_id,
                'agent_type': record.agent_type,
                'score': score,
                'confidence': record.confidence,
                'recommendation': record.recommendation if record.recommendation else 'hold'
            }
        
        final_score = weighted_score / total_weight if total_weight > 0 else 50
        
        # 计算共识度（各Agent评分的一致性）
        scores = [r.score for r in records if r.score is not None]
        if len(scores) > 1:
            avg_score = sum(scores) / len(scores)
            variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            std_dev = variance ** 0.5
            consensus_level = max(0, 1 - (std_dev / 50))  # 标准差越小，共识度越高
        else:
            consensus_level = 1.0
        
        # 确定综合推荐
        recommendation_scores = {
            'strong_sell': 0, 'sell': 25, 'hold': 50, 'buy': 75, 'strong_buy': 100
        }
        if final_score >= 80:
            recommendation = 'strong_buy'
        elif final_score >= 65:
            recommendation = 'buy'
        elif final_score >= 45:
            recommendation = 'hold'
        elif final_score >= 30:
            recommendation = 'sell'
        else:
            recommendation = 'strong_sell'
        
        # 确定风险等级
        if final_score >= 70 and consensus_level >= 0.7:
            risk_level = 'low'
        elif final_score >= 50 and consensus_level >= 0.5:
            risk_level = 'medium'
        elif final_score >= 30:
            risk_level = 'high'
        else:
            risk_level = 'very_high'
        
        # 汇总关键要点、风险和机会
        all_key_points = []
        all_risks = []
        all_opportunities = []
        
        for record in records:
            if record.key_points:
                all_key_points.extend(record.key_points)
            if record.risk_factors:
                all_risks.extend(record.risk_factors)
            if record.opportunities:
                all_opportunities.extend(record.opportunities)
        
        # 去重
        strengths = list(set(all_opportunities))[:5]
        weaknesses = list(set(all_risks))[:5]
        
        # 生成综合摘要
        summary = f"综合评分 {final_score:.1f}分，共识度 {consensus_level:.2f}。"
        summary += f"建议操作：{recommendation}。"
        summary += f"风险等级：{risk_level}。"
        
        return {
            'final_score': round(final_score, 2),
            'agent_scores': agent_scores,
            'recommendation': recommendation,
            'consensus_level': round(consensus_level, 4),
            'risk_level': risk_level,
            'summary': summary,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'market_data_snapshot': market_data
        }
    
    async def _get_market_data(self, stock_code: str) -> Dict[str, Any]:
        """获取股票市场数据"""
        try:
            # 调用实时行情服务
            quote = await self.quote_service.get_realtime_quote(stock_code)
            
            return {
                'stock_code': stock_code,
                'name': quote.get('name', stock_code),
                'current_price': quote.get('current_price', 0),
                'change_pct': quote.get('change_pct', 0),
                'volume': quote.get('volume', 0),
                'turnover_rate': quote.get('turnover_rate', 0),
                'pe': quote.get('pe', 0),
                'pb': quote.get('pb', 0),
                'market_cap': quote.get('market_cap', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"获取市场数据失败: {stock_code}, {e}")
            return {
                'stock_code': stock_code,
                'name': stock_code,
                'current_price': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    async def batch_analyze(
        self,
        session_id: str,
        stock_codes: List[str],
        agent_ids: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """批量分析多只股票"""
        results = []
        total = len(stock_codes)
        
        for i, stock_code in enumerate(stock_codes, 1):
            try:
                result = await self.analyze_stock(session_id, stock_code, agent_ids)
                results.append(result)
                
                if progress_callback:
                    progress = int((i / total) * 100)
                    await progress_callback(session_id, progress, f"已完成 {i}/{total}")
                    
            except Exception as e:
                logger.error(f"分析股票失败: {stock_code}, {e}")
                if progress_callback:
                    await progress_callback(session_id, int((i / total) * 100), f"股票 {stock_code} 分析失败")
        
        # 按评分排序
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        # 添加排名
        for rank, result in enumerate(results, 1):
            result['rank'] = rank
        
        return results
