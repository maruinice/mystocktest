# -*- coding: utf-8 -*-
"""
完整的Tushare API同步服务

根据Tushare官方文档 https://tushare.pro/document/2?doc_id=14 
同步所有股票相关的API接口信息到数据库
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db

logger = logging.getLogger(__name__)

class TushareApiSyncServiceComplete:
    """完整的Tushare API同步服务"""
    
    def __init__(self):
        """初始化同步服务"""
        self.tushare_apis = self._get_complete_tushare_api_definitions()
    
    def _get_complete_tushare_api_definitions(self) -> List[Dict[str, Any]]:
        """获取完整的Tushare API定义
        
        基于Tushare官方文档的所有股票相关API接口
        """
        return [
            # ==================== 基础数据 ====================
            {
                "api_code": "stock_basic",
                "api_name": "股票列表",
                "api_category": "基础数据",
                "description": "获取基础信息数据，包括股票代码、名称、上市日期、退市日期等",
                "endpoint": "/stock_basic",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "TS股票代码"},
                    {"name": "name", "type": "str", "description": "名称"},
                    {"name": "exchange", "type": "str", "description": "交易所 SSE上交所 SZSE深交所 BSE北交所"},
                    {"name": "market", "type": "str", "description": "市场类别"},
                    {"name": "is_hs", "type": "str", "description": "是否沪深港通标的"},
                    {"name": "list_status", "type": "str", "description": "上市状态 L上市 D退市 P暂停上市"},
                    {"name": "limit", "type": "int", "description": "单次返回数据长度"},
                    {"name": "offset", "type": "int", "description": "请求数据的开始位置"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS代码"},
                    {"name": "symbol", "type": "str", "description": "股票代码"},
                    {"name": "name", "type": "str", "description": "股票名称"},
                    {"name": "area", "type": "str", "description": "地域"},
                    {"name": "industry", "type": "str", "description": "所属行业"},
                    {"name": "market", "type": "str", "description": "市场类型"},
                    {"name": "exchange", "type": "str", "description": "交易所代码"},
                    {"name": "list_date", "type": "str", "description": "上市日期"},
                    {"name": "is_hs", "type": "str", "description": "是否沪深港通标的"}
                ],
                "required_points": 2000,
                "rate_limit": 200
            },
            {
                "api_code": "stock_company",
                "api_name": "上市公司基本信息",
                "api_category": "基础数据",
                "description": "获取上市公司基本信息，包括公司名称、成立日期、注册资本等",
                "endpoint": "/stock_company",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "exchange", "type": "str", "description": "交易所代码"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "chairman", "type": "str", "description": "法人代表"},
                    {"name": "manager", "type": "str", "description": "总经理"},
                    {"name": "secretary", "type": "str", "description": "董秘"},
                    {"name": "reg_capital", "type": "float", "description": "注册资本"},
                    {"name": "setup_date", "type": "str", "description": "注册日期"},
                    {"name": "province", "type": "str", "description": "所在省份"},
                    {"name": "city", "type": "str", "description": "所在城市"},
                    {"name": "introduction", "type": "str", "description": "公司介绍"},
                    {"name": "website", "type": "str", "description": "公司主页"},
                    {"name": "email", "type": "str", "description": "电子邮件"},
                    {"name": "office", "type": "str", "description": "办公室"},
                    {"name": "employees", "type": "int", "description": "员工人数"},
                    {"name": "main_business", "type": "str", "description": "主要业务及产品"},
                    {"name": "business_scope", "type": "str", "description": "经营范围"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },
            {
                "api_code": "trade_cal",
                "api_name": "交易日历",
                "api_category": "基础数据",
                "description": "获取各大交易所交易日历数据，默认提取的是上交所",
                "endpoint": "/trade_cal",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "exchange", "type": "str", "description": "交易所 SSE上交所,SZSE深交所,CFFEX中金所,SHFE上期所,CZCE郑商所,DCE大商所,INE上能源"},
                    {"name": "cal_date", "type": "str", "description": "日历日期"},
                    {"name": "start_date", "type": "str", "description": "开始日期"},
                    {"name": "end_date", "type": "str", "description": "结束日期"},
                    {"name": "is_open", "type": "str", "description": "是否交易 '0'休市 '1'交易"}
                ],
                "response_fields": [
                    {"name": "exchange", "type": "str", "description": "交易所"},
                    {"name": "cal_date", "type": "str", "description": "日历日期"},
                    {"name": "is_open", "type": "str", "description": "是否交易"},
                    {"name": "pretrade_date", "type": "str", "description": "上一个交易日"}
                ],
                "required_points": 2000,
                "rate_limit": 200
            },
            {
                "api_code": "hs_const",
                "api_name": "沪深港通成份股",
                "api_category": "基础数据",
                "description": "获取沪深港通成份股数据",
                "endpoint": "/hs_const",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "hs_type", "type": "str", "description": "沪深港通类型SH沪股通SZ深股通"},
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "is_new", "type": "str", "description": "是否最新"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS代码"},
                    {"name": "hs_type", "type": "str", "description": "沪深港通类型"},
                    {"name": "in_date", "type": "str", "description": "纳入日期"},
                    {"name": "out_date", "type": "str", "description": "剔除日期"},
                    {"name": "is_new", "type": "str", "description": "是否最新"}
                ],
                "required_points": 100,
                "rate_limit": 200
            },
            {
                "api_code": "namechange",
                "api_name": "股票曾用名",
                "api_category": "基础数据",
                "description": "历史名称变更记录",
                "endpoint": "/namechange",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "TS股票代码"},
                    {"name": "start_date", "type": "str", "description": "公告开始日期"},
                    {"name": "end_date", "type": "str", "description": "公告结束日期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS代码"},
                    {"name": "name", "type": "str", "description": "证券名称"},
                    {"name": "start_date", "type": "str", "description": "开始日期"},
                    {"name": "end_date", "type": "str", "description": "结束日期"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "change_reason", "type": "str", "description": "变更原因"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },
            {
                "api_code": "new_share",
                "api_name": "IPO新股列表",
                "api_category": "基础数据",
                "description": "获取新股上市列表数据",
                "endpoint": "/new_share",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "start_date", "type": "str", "description": "开始日期"},
                    {"name": "end_date", "type": "str", "description": "结束日期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS股票代码"},
                    {"name": "sub_code", "type": "str", "description": "申购代码"},
                    {"name": "name", "type": "str", "description": "名称"},
                    {"name": "ipo_date", "type": "str", "description": "上网发行日期"},
                    {"name": "issue_date", "type": "str", "description": "上市日期"},
                    {"name": "amount", "type": "float", "description": "发行总量(万股)"},
                    {"name": "market_amount", "type": "float", "description": "上网发行总量(万股)"},
                    {"name": "price", "type": "float", "description": "发行价格"},
                    {"name": "pe", "type": "float", "description": "市盈率"},
                    {"name": "limit_amount", "type": "float", "description": "个人申购上限(万股)"},
                    {"name": "funds", "type": "float", "description": "募集资金(万元)"},
                    {"name": "ballot", "type": "float", "description": "中签率"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },

            # ==================== 行情数据 ====================
            {
                "api_code": "daily",
                "api_name": "日线行情",
                "api_category": "行情数据",
                "description": "获取股票日线行情数据，包括开高低收成交量等",
                "endpoint": "/daily",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "start_date", "type": "str", "description": "开始日期"},
                    {"name": "end_date", "type": "str", "description": "结束日期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "open", "type": "float", "description": "开盘价"},
                    {"name": "high", "type": "float", "description": "最高价"},
                    {"name": "low", "type": "float", "description": "最低价"},
                    {"name": "close", "type": "float", "description": "收盘价"},
                    {"name": "pre_close", "type": "float", "description": "昨收价"},
                    {"name": "change", "type": "float", "description": "涨跌额"},
                    {"name": "pct_chg", "type": "float", "description": "涨跌幅"},
                    {"name": "vol", "type": "float", "description": "成交量(手)"},
                    {"name": "amount", "type": "float", "description": "成交额(千元)"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },
            {
                "api_code": "weekly",
                "api_name": "周线行情",
                "api_category": "行情数据",
                "description": "获取股票周线行情数据",
                "endpoint": "/weekly",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "start_date", "type": "str", "description": "开始日期"},
                    {"name": "end_date", "type": "str", "description": "结束日期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "open", "type": "float", "description": "开盘价"},
                    {"name": "high", "type": "float", "description": "最高价"},
                    {"name": "low", "type": "float", "description": "最低价"},
                    {"name": "close", "type": "float", "description": "收盘价"},
                    {"name": "pre_close", "type": "float", "description": "昨收价"},
                    {"name": "change", "type": "float", "description": "涨跌额"},
                    {"name": "pct_chg", "type": "float", "description": "涨跌幅"},
                    {"name": "vol", "type": "float", "description": "成交量(手)"},
                    {"name": "amount", "type": "float", "description": "成交额(千元)"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },
            {
                "api_code": "monthly",
                "api_name": "月线行情",
                "api_category": "行情数据",
                "description": "获取股票月线行情数据",
                "endpoint": "/monthly",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "start_date", "type": "str", "description": "开始日期"},
                    {"name": "end_date", "type": "str", "description": "结束日期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "open", "type": "float", "description": "开盘价"},
                    {"name": "high", "type": "float", "description": "最高价"},
                    {"name": "low", "type": "float", "description": "最低价"},
                    {"name": "close", "type": "float", "description": "收盘价"},
                    {"name": "pre_close", "type": "float", "description": "昨收价"},
                    {"name": "change", "type": "float", "description": "涨跌额"},
                    {"name": "pct_chg", "type": "float", "description": "涨跌幅"},
                    {"name": "vol", "type": "float", "description": "成交量(手)"},
                    {"name": "amount", "type": "float", "description": "成交额(千元)"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },
            {
                "api_code": "adj_factor",
                "api_name": "复权因子",
                "api_category": "行情数据",
                "description": "获取股票复权因子，可提取单只股票全部历史复权因子，也可以提取单日全部股票的复权因子",
                "endpoint": "/adj_factor",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "start_date", "type": "str", "description": "开始日期"},
                    {"name": "end_date", "type": "str", "description": "结束日期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "adj_factor", "type": "float", "description": "复权因子"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },
            {
                "api_code": "suspend_d",
                "api_name": "停复牌信息",
                "api_category": "行情数据",
                "description": "获取股票每日停复牌信息",
                "endpoint": "/suspend_d",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "suspend_date", "type": "str", "description": "停牌日期"},
                    {"name": "resume_date", "type": "str", "description": "复牌日期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "suspend_date", "type": "str", "description": "停牌日期"},
                    {"name": "resume_date", "type": "str", "description": "复牌日期"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "suspend_reason", "type": "str", "description": "停牌原因"},
                    {"name": "reason_type", "type": "str", "description": "停牌原因类别"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },
            {
                "api_code": "daily_basic",
                "api_name": "每日指标",
                "api_category": "行情数据",
                "description": "获取全部股票每日重要的基本面指标，可用于选股分析、报表展示等",
                "endpoint": "/daily_basic",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "start_date", "type": "str", "description": "开始日期"},
                    {"name": "end_date", "type": "str", "description": "结束日期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS股票代码"},
                    {"name": "trade_date", "type": "str", "description": "交易日期"},
                    {"name": "close", "type": "float", "description": "当日收盘价"},
                    {"name": "turnover_rate", "type": "float", "description": "换手率（%）"},
                    {"name": "turnover_rate_f", "type": "float", "description": "换手率（自由流通股）"},
                    {"name": "volume_ratio", "type": "float", "description": "量比"},
                    {"name": "pe", "type": "float", "description": "市盈率（总市值/净利润， 亏损的PE为空）"},
                    {"name": "pe_ttm", "type": "float", "description": "市盈率（TTM，亏损的PE为空）"},
                    {"name": "pb", "type": "float", "description": "市净率（总市值/净资产）"},
                    {"name": "ps", "type": "float", "description": "市销率"},
                    {"name": "ps_ttm", "type": "float", "description": "市销率（TTM）"},
                    {"name": "dv_ratio", "type": "float", "description": "股息率 （%）"},
                    {"name": "dv_ttm", "type": "float", "description": "股息率（TTM）（%）"},
                    {"name": "total_share", "type": "float", "description": "总股本 （万股）"},
                    {"name": "float_share", "type": "float", "description": "流通股本 （万股）"},
                    {"name": "free_share", "type": "float", "description": "自由流通股本 （万）"},
                    {"name": "total_mv", "type": "float", "description": "总市值 （万元）"},
                    {"name": "circ_mv", "type": "float", "description": "流通市值（万元）"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },

            # ==================== 财务数据 ====================
            {
                "api_code": "income",
                "api_name": "利润表",
                "api_category": "财务数据",
                "description": "获取上市公司财务利润表数据",
                "endpoint": "/income",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "f_ann_date", "type": "str", "description": "实际公告日期"},
                    {"name": "start_date", "type": "str", "description": "公告开始日期"},
                    {"name": "end_date", "type": "str", "description": "公告结束日期"},
                    {"name": "period", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"},
                    {"name": "comp_type", "type": "str", "description": "公司类型"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "f_ann_date", "type": "str", "description": "实际公告日期"},
                    {"name": "end_date", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"},
                    {"name": "comp_type", "type": "str", "description": "公司类型"},
                    {"name": "basic_eps", "type": "float", "description": "基本每股收益"},
                    {"name": "diluted_eps", "type": "float", "description": "稀释每股收益"},
                    {"name": "total_revenue", "type": "float", "description": "营业总收入"},
                    {"name": "revenue", "type": "float", "description": "营业收入"},
                    {"name": "n_income", "type": "float", "description": "净利润(含少数股东损益)"},
                    {"name": "n_income_attr_p", "type": "float", "description": "净利润(不含少数股东损益)"}
                ],
                "required_points": 2000,
                "rate_limit": 200
            },
            {
                "api_code": "balancesheet",
                "api_name": "资产负债表",
                "api_category": "财务数据",
                "description": "获取上市公司资产负债表数据",
                "endpoint": "/balancesheet",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "f_ann_date", "type": "str", "description": "实际公告日期"},
                    {"name": "start_date", "type": "str", "description": "公告开始日期"},
                    {"name": "end_date", "type": "str", "description": "公告结束日期"},
                    {"name": "period", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"},
                    {"name": "comp_type", "type": "str", "description": "公司类型"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "f_ann_date", "type": "str", "description": "实际公告日期"},
                    {"name": "end_date", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"},
                    {"name": "comp_type", "type": "str", "description": "公司类型"},
                    {"name": "total_share", "type": "float", "description": "期末总股本"},
                    {"name": "cap_rese", "type": "float", "description": "资本公积金"},
                    {"name": "undistr_porfit", "type": "float", "description": "未分配利润"},
                    {"name": "surplus_rese", "type": "float", "description": "盈余公积金"},
                    {"name": "money_cap", "type": "float", "description": "货币资金"},
                    {"name": "total_assets", "type": "float", "description": "资产总计"},
                    {"name": "total_liab", "type": "float", "description": "负债合计"},
                    {"name": "total_hldr_eqy_exc_min_int", "type": "float", "description": "股东权益合计(不含少数股东权益)"}
                ],
                "required_points": 2000,
                "rate_limit": 200
            },
            {
                "api_code": "cashflow",
                "api_name": "现金流量表",
                "api_category": "财务数据",
                "description": "获取上市公司现金流量表数据",
                "endpoint": "/cashflow",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "f_ann_date", "type": "str", "description": "实际公告日期"},
                    {"name": "start_date", "type": "str", "description": "公告开始日期"},
                    {"name": "end_date", "type": "str", "description": "公告结束日期"},
                    {"name": "period", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"},
                    {"name": "comp_type", "type": "str", "description": "公司类型"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "f_ann_date", "type": "str", "description": "实际公告日期"},
                    {"name": "end_date", "type": "str", "description": "报告期"},
                    {"name": "comp_type", "type": "str", "description": "公司类型"},
                    {"name": "report_type", "type": "str", "description": "报告类型"},
                    {"name": "net_profit", "type": "float", "description": "净利润"},
                    {"name": "finan_exp", "type": "float", "description": "财务费用"},
                    {"name": "c_fr_sale_sg", "type": "float", "description": "销售商品、提供劳务收到的现金"},
                    {"name": "n_cashflow_operate_a", "type": "float", "description": "经营活动产生的现金流量净额"},
                    {"name": "n_cashflow_invest_a", "type": "float", "description": "投资活动产生的现金流量净额"},
                    {"name": "n_cash_flows_fnc_act", "type": "float", "description": "筹资活动产生的现金流量净额"}
                ],
                "required_points": 2000,
                "rate_limit": 200
            },
            {
                "api_code": "fina_indicator",
                "api_name": "财务指标数据",
                "api_category": "财务数据",
                "description": "获取上市公司财务指标数据，为投资者提供作为一个整体的主要财务指标",
                "endpoint": "/fina_indicator",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "TS股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "start_date", "type": "str", "description": "报告期开始日期"},
                    {"name": "end_date", "type": "str", "description": "报告期结束日期"},
                    {"name": "period", "type": "str", "description": "报告期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "end_date", "type": "str", "description": "报告期"},
                    {"name": "eps", "type": "float", "description": "基本每股收益"},
                    {"name": "dt_eps", "type": "float", "description": "稀释每股收益"},
                    {"name": "total_revenue_ps", "type": "float", "description": "每股营业总收入"},
                    {"name": "revenue_ps", "type": "float", "description": "每股营业收入"},
                    {"name": "capital_rese_ps", "type": "float", "description": "每股资本公积"},
                    {"name": "surplus_rese_ps", "type": "float", "description": "每股盈余公积"},
                    {"name": "undist_profit_ps", "type": "float", "description": "每股未分配利润"},
                    {"name": "extra_item", "type": "float", "description": "非经常性损益"},
                    {"name": "profit_dedt", "type": "float", "description": "扣除非经常性损益后的净利润"},
                    {"name": "gross_margin", "type": "float", "description": "毛利"},
                    {"name": "current_ratio", "type": "float", "description": "流动比率"},
                    {"name": "quick_ratio", "type": "float", "description": "速动比率"},
                    {"name": "cash_ratio", "type": "float", "description": "保守速动比率"},
                    {"name": "ar_turn", "type": "float", "description": "应收账款周转率"},
                    {"name": "ca_turn", "type": "float", "description": "流动资产周转率"},
                    {"name": "fa_turn", "type": "float", "description": "固定资产周转率"},
                    {"name": "assets_turn", "type": "float", "description": "总资产周转率"},
                    {"name": "roe", "type": "float", "description": "净资产收益率"},
                    {"name": "roe_waa", "type": "float", "description": "加权平均净资产收益率"},
                    {"name": "roe_dt", "type": "float", "description": "净资产收益率(扣除非经常损益)"},
                    {"name": "roa", "type": "float", "description": "总资产报酬率"},
                    {"name": "npta", "type": "float", "description": "总资产净利润"},
                    {"name": "roic", "type": "float", "description": "投入资本回报率"},
                    {"name": "debt_to_assets", "type": "float", "description": "资产负债率"},
                    {"name": "assets_to_eqt", "type": "float", "description": "权益乘数"}
                ],
                "required_points": 2000,
                "rate_limit": 200
            },

            # ==================== 市场参考数据 ====================
            {
                "api_code": "forecast",
                "api_name": "业绩预告",
                "api_category": "市场参考数据",
                "description": "获取业绩预告数据",
                "endpoint": "/forecast",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "start_date", "type": "str", "description": "公告开始日期"},
                    {"name": "end_date", "type": "str", "description": "公告结束日期"},
                    {"name": "period", "type": "str", "description": "报告期"},
                    {"name": "type", "type": "str", "description": "预告类型"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "end_date", "type": "str", "description": "报告期"},
                    {"name": "type", "type": "str", "description": "业绩预告类型"},
                    {"name": "p_change_min", "type": "float", "description": "预告净利润变动幅度下限(%)"},
                    {"name": "p_change_max", "type": "float", "description": "预告净利润变动幅度上限(%)"},
                    {"name": "net_profit_min", "type": "float", "description": "预告净利润下限(万元)"},
                    {"name": "net_profit_max", "type": "float", "description": "预告净利润上限(万元)"},
                    {"name": "last_parent_net", "type": "float", "description": "上年同期归属母公司净利润"},
                    {"name": "first_ann_date", "type": "str", "description": "首次公告日"},
                    {"name": "summary", "type": "str", "description": "业绩预告摘要"},
                    {"name": "change_reason", "type": "str", "description": "业绩变动原因"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },
            {
                "api_code": "express",
                "api_name": "业绩快报",
                "api_category": "市场参考数据",
                "description": "获取上市公司业绩快报",
                "endpoint": "/express",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "start_date", "type": "str", "description": "公告开始日期"},
                    {"name": "end_date", "type": "str", "description": "公告结束日期"},
                    {"name": "period", "type": "str", "description": "报告期"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "end_date", "type": "str", "description": "报告期"},
                    {"name": "revenue", "type": "float", "description": "营业收入(元)"},
                    {"name": "operate_profit", "type": "float", "description": "营业利润(元)"},
                    {"name": "total_profit", "type": "float", "description": "利润总额(元)"},
                    {"name": "n_income", "type": "float", "description": "净利润(元)"},
                    {"name": "total_assets", "type": "float", "description": "总资产(元)"},
                    {"name": "total_hldr_eqy_exc_min_int", "type": "float", "description": "股东权益合计(不含少数股东权益)(元)"},
                    {"name": "diluted_eps", "type": "float", "description": "每股收益(摊薄)(元)"},
                    {"name": "diluted_roe", "type": "float", "description": "净资产收益率(摊薄)(%)"},
                    {"name": "yoy_net_profit", "type": "float", "description": "去年同期修正后净利润"},
                    {"name": "bps", "type": "float", "description": "每股净资产"}
                ],
                "required_points": 120,
                "rate_limit": 200
            },
            {
                "api_code": "dividend",
                "api_name": "分红送股",
                "api_category": "市场参考数据",
                "description": "分红送股数据",
                "endpoint": "/dividend",
                "method": "POST",
                "required_params": [],
                "optional_params": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日"},
                    {"name": "record_date", "type": "str", "description": "股权登记日"},
                    {"name": "ex_date", "type": "str", "description": "除权除息日"},
                    {"name": "imp_ann_date", "type": "str", "description": "实施公告日"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "TS代码"},
                    {"name": "end_date", "type": "str", "description": "分红年度"},
                    {"name": "ann_date", "type": "str", "description": "预案公告日"},
                    {"name": "div_proc", "type": "str", "description": "实施进度"},
                    {"name": "stk_div", "type": "float", "description": "每股送转"},
                    {"name": "stk_bo_rate", "type": "float", "description": "每股送股比例"},
                    {"name": "stk_co_rate", "type": "float", "description": "每股转增比例"},
                    {"name": "cash_div", "type": "float", "description": "每股分红(税后)"},
                    {"name": "cash_div_tax", "type": "float", "description": "每股分红(税前)"},
                    {"name": "record_date", "type": "str", "description": "股权登记日"},
                    {"name": "ex_date", "type": "str", "description": "除权除息日"},
                    {"name": "pay_date", "type": "str", "description": "派息日"},
                    {"name": "div_listdate", "type": "str", "description": "红股上市日"},
                    {"name": "imp_ann_date", "type": "str", "description": "实施公告日"},
                    {"name": "base_share", "type": "float", "description": "基准股本(万)"},
                    {"name": "base_date", "type": "str", "description": "基准日期"}
                ],
                "required_points": 120,
                "rate_limit": 200
            }
        ]
    
    def sync_apis_to_database(self, data_source_id: int) -> Dict[str, Any]:
        """同步API接口到数据库
        
        Args:
            data_source_id: 数据源ID
            
        Returns:
            Dict: 同步结果
        """
        try:
            # 获取数据库连接
            db = next(get_db())
            
            # 创建同步任务记录
            task_name = f"Tushare API完整同步 - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            task_insert_sql = """
                INSERT INTO api_sync_tasks (
                    data_source_id, task_name, task_type, status, progress,
                    total_apis, new_apis, updated_apis, failed_apis,
                    started_at, created_at
                ) VALUES (
                    :data_source_id, :task_name, 'full_sync', 'running', 0,
                    :total_apis, 0, 0, 0,
                    NOW(), NOW()
                )
            """
            
            result = db.execute(text(task_insert_sql), {
                'data_source_id': data_source_id,
                'task_name': task_name,
                'total_apis': len(self.tushare_apis)
            })
            db.commit()
            
            # 获取任务ID
            task_id = result.lastrowid
            
            new_apis = 0
            updated_apis = 0
            failed_apis = 0
            
            # 同步每个API
            for i, api_def in enumerate(self.tushare_apis):
                try:
                    # 检查API是否已存在
                    check_sql = """
                        SELECT id FROM api_interfaces 
                        WHERE data_source_id = :data_source_id AND api_code = :api_code
                    """
                    existing = db.execute(text(check_sql), {
                        'data_source_id': data_source_id,
                        'api_code': api_def['api_code']
                    }).fetchone()
                    
                    if existing:
                        # 更新现有API
                        update_sql = """
                            UPDATE api_interfaces SET
                                api_name = :api_name,
                                api_category = :api_category,
                                description = :description,
                                endpoint = :endpoint,
                                method = :method,
                                required_params = :required_params,
                                optional_params = :optional_params,
                                response_fields = :response_fields,
                                required_points = :required_points,
                                rate_limit = :rate_limit,
                                synced_at = NOW(),
                                updated_at = NOW()
                            WHERE id = :id
                        """
                        db.execute(text(update_sql), {
                            'id': existing[0],
                            'api_name': api_def['api_name'],
                            'api_category': api_def['api_category'],
                            'description': api_def['description'],
                            'endpoint': api_def['endpoint'],
                            'method': api_def['method'],
                            'required_params': json.dumps(api_def['required_params'], ensure_ascii=False),
                            'optional_params': json.dumps(api_def['optional_params'], ensure_ascii=False),
                            'response_fields': json.dumps(api_def['response_fields'], ensure_ascii=False),
                            'required_points': api_def['required_points'],
                            'rate_limit': api_def['rate_limit']
                        })
                        updated_apis += 1
                    else:
                        # 插入新API
                        insert_sql = """
                            INSERT INTO api_interfaces (
                                data_source_id, api_code, api_name, api_category,
                                description, endpoint, method, required_params, optional_params,
                                response_fields, required_points, rate_limit, status,
                                synced_at, created_at, updated_at
                            ) VALUES (
                                :data_source_id, :api_code, :api_name, :api_category,
                                :description, :endpoint, :method, :required_params, :optional_params,
                                :response_fields, :required_points, :rate_limit, 'active',
                                NOW(), NOW(), NOW()
                            )
                        """
                        db.execute(text(insert_sql), {
                            'data_source_id': data_source_id,
                            'api_code': api_def['api_code'],
                            'api_name': api_def['api_name'],
                            'api_category': api_def['api_category'],
                            'description': api_def['description'],
                            'endpoint': api_def['endpoint'],
                            'method': api_def['method'],
                            'required_params': json.dumps(api_def['required_params'], ensure_ascii=False),
                            'optional_params': json.dumps(api_def['optional_params'], ensure_ascii=False),
                            'response_fields': json.dumps(api_def['response_fields'], ensure_ascii=False),
                            'required_points': api_def['required_points'],
                            'rate_limit': api_def['rate_limit']
                        })
                        new_apis += 1
                    
                    db.commit()
                    
                    # 更新任务进度
                    progress = int((i + 1) / len(self.tushare_apis) * 100)
                    update_progress_sql = """
                        UPDATE api_sync_tasks SET
                            progress = :progress,
                            new_apis = :new_apis,
                            updated_apis = :updated_apis,
                            failed_apis = :failed_apis
                        WHERE id = :task_id
                    """
                    db.execute(text(update_progress_sql), {
                        'task_id': task_id,
                        'progress': progress,
                        'new_apis': new_apis,
                        'updated_apis': updated_apis,
                        'failed_apis': failed_apis
                    })
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"同步API {api_def['api_code']} 失败: {e}")
                    failed_apis += 1
                    continue
            
            # 完成任务
            complete_task_sql = """
                UPDATE api_sync_tasks SET
                    status = 'completed',
                    progress = 100,
                    new_apis = :new_apis,
                    updated_apis = :updated_apis,
                    failed_apis = :failed_apis,
                    completed_at = NOW()
                WHERE id = :task_id
            """
            db.execute(text(complete_task_sql), {
                'task_id': task_id,
                'new_apis': new_apis,
                'updated_apis': updated_apis,
                'failed_apis': failed_apis
            })
            db.commit()
            
            logger.info(f"API同步完成: 新增{new_apis}个, 更新{updated_apis}个, 失败{failed_apis}个")
            
            return {
                'success': True,
                'message': 'API同步完成',
                'data': {
                    'task_id': task_id,
                    'total_apis': len(self.tushare_apis),
                    'new_apis': new_apis,
                    'updated_apis': updated_apis,
                    'failed_apis': failed_apis
                }
            }
            
        except Exception as e:
            logger.error(f"API同步失败: {e}")
            return {
                'success': False,
                'message': f'API同步失败: {str(e)}',
                'data': None
            }
        finally:
            db.close()

# 创建完整的同步服务实例
tushare_api_sync_service_complete = TushareApiSyncServiceComplete()