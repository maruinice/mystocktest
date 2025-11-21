"""
同步管理器
统一管理所有数据同步任务
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .stock_basic_sync import StockBasicSyncService
from .trade_cal_sync import TradeCalSyncService
from .financial_indicator_sync import FinancialIndicatorSyncService
from .audit_opinion_sync import AuditOpinionSyncService
from .industry_classification_sync import IndustryClassificationSyncService
from .daily_sync import DailySyncService
from .daily_basic_sync import DailyBasicSyncService
from .adj_factor_sync import AdjFactorSyncService
from .suspend_sync import SuspendSyncService
from .limit_price_sync import LimitPriceSyncService

logger = logging.getLogger(__name__)


class SyncManager:
    """同步管理器"""
    
    # 同步服务配置
    SYNC_SERVICES = {
        'stock_basic': {
            'name': '股票基础信息',
            'service_class': StockBasicSyncService,
            'description': '同步股票代码、名称、行业等基础信息',
            'table': 'stock_basic',
            'frequency': '每日',
            'api': 'stock_basic'
        },
        'trade_cal': {
            'name': '交易日历',
            'service_class': TradeCalSyncService,
            'description': '同步交易所交易日历',
            'table': 'trade_cal',
            'frequency': '每日',
            'api': 'trade_cal'
        },
        'daily_history': {
            'name': '日线行情',
            'service_class': DailySyncService,
            'description': '同步股票日线行情数据',
            'table': 'daily_history',
            'frequency': '每日',
            'api': 'daily'
        },
        'daily_basic': {
            'name': '每日指标',
            'service_class': DailyBasicSyncService,
            'description': '同步PE、PB、市值等每日指标',
            'table': 'daily_basic',
            'frequency': '每日',
            'api': 'daily_basic'
        },
        'adj_factor': {
            'name': '复权因子',
            'service_class': AdjFactorSyncService,
            'description': '同步复权因子数据',
            'table': 'adj_factor',
            'frequency': '每日',
            'api': 'adj_factor'
        },
        'financial_indicators': {
            'name': '财务指标',
            'service_class': FinancialIndicatorSyncService,
            'description': '同步ROE、负债率等财务指标',
            'table': 'financial_indicators',
            'frequency': '每季度',
            'api': 'fina_indicator'
        },
        'industry_classification': {
            'name': '行业分类',
            'service_class': IndustryClassificationSyncService,
            'description': '同步申万行业分类数据',
            'table': 'industry_classification',
            'frequency': '每季度',
            'api': 'index_classify + index_member'
        },
        'audit_opinions': {
            'name': '审计意见',
            'service_class': AuditOpinionSyncService,
            'description': '同步财务审计意见',
            'table': 'audit_opinions',
            'frequency': '每年',
            'api': 'fina_audit'
        },
        'suspend_info': {
            'name': '停复牌信息',
            'service_class': SuspendSyncService,
            'description': '同步停复牌信息',
            'table': 'suspend_info',
            'frequency': '每日',
            'api': 'suspend_d'
        },
        'limit_prices': {
            'name': '涨跌停价格',
            'service_class': LimitPriceSyncService,
            'description': '同步涨跌停价格',
            'table': 'limit_prices',
            'frequency': '每日',
            'api': 'stk_limit'
        }
    }
    
    def __init__(self):
        """初始化同步管理器"""
        self.services = {}
        self._init_services()
    
    def _init_services(self):
        """初始化所有同步服务实例"""
        for key, config in self.SYNC_SERVICES.items():
            if config['service_class']:
                self.services[key] = config['service_class']()
    
    def get_service_list(self) -> list:
        """获取所有同步服务列表"""
        result = []
        for key, config in self.SYNC_SERVICES.items():
            result.append({
                'key': key,
                'name': config['name'],
                'description': config['description'],
                'table': config['table'],
                'frequency': config['frequency'],
                'api': config['api'],
                'implemented': config['service_class'] is not None
            })
        return result
    
    async def start_sync(self, service_key: str, **params) -> Dict[str, Any]:
        """
        启动同步任务
        
        Args:
            service_key: 服务标识
            **params: 同步参数
            
        Returns:
            同步结果
        """
        if service_key not in self.services:
            return {
                'success': False,
                'message': f'同步服务 {service_key} 未实现或不存在'
            }
        
        service = self.services[service_key]
        
        try:
            logger.info(f"开始同步: {self.SYNC_SERVICES[service_key]['name']}")
            result = await service.sync(**params)
            return result
            
        except Exception as e:
            error_msg = f"同步失败: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'message': error_msg}
    
    def get_sync_status(self, service_key: str) -> Dict[str, Any]:
        """
        获取同步状态
        
        Args:
            service_key: 服务标识
            
        Returns:
            同步状态
        """
        if service_key not in self.services:
            return {
                'is_running': False,
                'error': f'服务 {service_key} 不存在'
            }
        
        service = self.services[service_key]
        status = service.get_sync_status()
        
        # 添加服务信息
        status['service_name'] = self.SYNC_SERVICES[service_key]['name']
        status['service_key'] = service_key
        
        return status
    
    async def get_data_statistics(self, service_key: str) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Args:
            service_key: 服务标识
            
        Returns:
            数据统计
        """
        if service_key not in self.SYNC_SERVICES:
            return {'error': '服务不存在'}
        
        config = self.SYNC_SERVICES[service_key]
        table_name = config['table']
        
        if service_key not in self.services:
            return {
                'table': table_name,
                'total_count': 0,
                'last_sync_date': None,
                'implemented': False
            }
        
        service = self.services[service_key]
        
        try:
            # 获取记录总数
            total_count = await service.get_record_count(table_name)
            
            # 获取最新同步日期
            last_sync_date = None
            if table_name in ['trade_cal', 'daily_history', 'daily_basic', 'adj_factor', 'limit_prices', 'suspend_info']:
                last_sync_date = await service.get_last_sync_date(table_name, 'trade_date' if table_name != 'trade_cal' else 'cal_date')
            elif table_name in ['financial_indicators', 'audit_opinions']:
                last_sync_date = await service.get_last_sync_date(table_name, 'ann_date')
            
            return {
                'table': table_name,
                'total_count': total_count,
                'last_sync_date': last_sync_date,
                'implemented': True
            }
            
        except Exception as e:
            logger.error(f"获取数据统计失败: {e}")
            return {
                'table': table_name,
                'total_count': 0,
                'last_sync_date': None,
                'error': str(e)
            }


# 全局同步管理器实例
sync_manager = SyncManager()
