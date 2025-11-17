# -*- coding: utf-8 -*-
"""
Tushare API同步服务

根据Tushare官方文档同步API接口信息到数据库
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db

logger = logging.getLogger(__name__)

class TushareApiSyncService:
    """Tushare API同步服务"""
    
    def __init__(self):
        """初始化同步服务"""
        self.tushare_apis = self._get_tushare_api_definitions()
    
    def _get_tushare_api_definitions(self) -> List[Dict[str, Any]]:
        """获取Tushare API定义
        
        基于Tushare官方文档 https://tushare.pro/document/2 的API接口
        """
        return [
            # 基础数据
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
                "api_code": "daily",
                "api_name": "日线行情",
                "api_category": "行情数据",
                "description": "获取股票日线行情数据",
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
                    {"name": "vol", "type": "float", "description": "成交量"},
                    {"name": "amount", "type": "float", "description": "成交额"}
                ],
                "required_points": 0,
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
                    {"name": "vol", "type": "float", "description": "成交量"},
                    {"name": "amount", "type": "float", "description": "成交额"}
                ],
                "required_points": 0,
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
                    {"name": "vol", "type": "float", "description": "成交量"},
                    {"name": "amount", "type": "float", "description": "成交额"}
                ],
                "required_points": 0,
                "rate_limit": 200
            },
            {
                "api_code": "adj_factor",
                "api_name": "复权因子",
                "api_category": "行情数据",
                "description": "获取股票复权因子数据",
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
                "required_points": 0,
                "rate_limit": 200
            },
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
                    {"name": "start_date", "type": "str", "description": "公告开始日期"},
                    {"name": "end_date", "type": "str", "description": "公告结束日期"},
                    {"name": "period", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "f_ann_date", "type": "str", "description": "实际公告日期"},
                    {"name": "end_date", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"},
                    {"name": "comp_type", "type": "str", "description": "公司类型"},
                    {"name": "basic_eps", "type": "float", "description": "基本每股收益"},
                    {"name": "diluted_eps", "type": "float", "description": "稀释每股收益"}
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
                    {"name": "start_date", "type": "str", "description": "公告开始日期"},
                    {"name": "end_date", "type": "str", "description": "公告结束日期"},
                    {"name": "period", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "f_ann_date", "type": "str", "description": "实际公告日期"},
                    {"name": "end_date", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"},
                    {"name": "comp_type", "type": "str", "description": "公司类型"},
                    {"name": "total_share", "type": "float", "description": "期末总股本"},
                    {"name": "cap_rese", "type": "float", "description": "资本公积金"}
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
                    {"name": "start_date", "type": "str", "description": "公告开始日期"},
                    {"name": "end_date", "type": "str", "description": "公告结束日期"},
                    {"name": "period", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"}
                ],
                "response_fields": [
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
                    {"name": "ann_date", "type": "str", "description": "公告日期"},
                    {"name": "f_ann_date", "type": "str", "description": "实际公告日期"},
                    {"name": "end_date", "type": "str", "description": "报告期"},
                    {"name": "report_type", "type": "str", "description": "报告类型"},
                    {"name": "comp_type", "type": "str", "description": "公司类型"},
                    {"name": "net_profit", "type": "float", "description": "净利润"},
                    {"name": "finan_exp", "type": "float", "description": "财务费用"}
                ],
                "required_points": 2000,
                "rate_limit": 200
            },
            {
                "api_code": "fina_indicator",
                "api_name": "财务指标数据",
                "api_category": "财务数据",
                "description": "获取上市公司财务指标数据",
                "endpoint": "/fina_indicator",
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
                    {"name": "ts_code", "type": "str", "description": "股票代码"},
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
                    {"name": "invturn_days", "type": "float", "description": "存货周转天数"},
                    {"name": "arturn_days", "type": "float", "description": "应收账款周转天数"},
                    {"name": "inv_turn", "type": "float", "description": "存货周转率"},
                    {"name": "ar_turn", "type": "float", "description": "应收账款周转率"},
                    {"name": "ca_turn", "type": "float", "description": "流动资产周转率"},
                    {"name": "fa_turn", "type": "float", "description": "固定资产周转率"},
                    {"name": "assets_turn", "type": "float", "description": "总资产周转率"},
                    {"name": "op_income", "type": "float", "description": "经营活动净收益"},
                    {"name": "valuechange_income", "type": "float", "description": "价值变动净收益"},
                    {"name": "interst_income", "type": "float", "description": "利息费用"},
                    {"name": "daa", "type": "float", "description": "折旧与摊销"},
                    {"name": "ebit", "type": "float", "description": "息税前利润"},
                    {"name": "ebitda", "type": "float", "description": "息税折旧摊销前利润"},
                    {"name": "fcff", "type": "float", "description": "企业自由现金流量"},
                    {"name": "fcfe", "type": "float", "description": "股权自由现金流量"},
                    {"name": "current_exint", "type": "float", "description": "无息流动负债"},
                    {"name": "noncurrent_exint", "type": "float", "description": "无息非流动负债"},
                    {"name": "interestdebt", "type": "float", "description": "带息债务"},
                    {"name": "netdebt", "type": "float", "description": "净债务"},
                    {"name": "tangible_asset", "type": "float", "description": "有形资产"},
                    {"name": "working_capital", "type": "float", "description": "营运资金"},
                    {"name": "networking_capital", "type": "float", "description": "营运流动资本"},
                    {"name": "invest_capital", "type": "float", "description": "全部投入资本"},
                    {"name": "retained_earnings", "type": "float", "description": "留存收益"},
                    {"name": "diluted2_eps", "type": "float", "description": "期末摊薄每股收益"},
                    {"name": "bps", "type": "float", "description": "每股净资产"},
                    {"name": "ocfps", "type": "float", "description": "每股经营活动产生的现金流量净额"},
                    {"name": "retainedps", "type": "float", "description": "每股留存收益"},
                    {"name": "cfps", "type": "float", "description": "每股现金流量净额"},
                    {"name": "ebit_ps", "type": "float", "description": "每股息税前利润"},
                    {"name": "fcff_ps", "type": "float", "description": "每股企业自由现金流量"},
                    {"name": "fcfe_ps", "type": "float", "description": "每股股东自由现金流量"},
                    {"name": "netprofit_margin", "type": "float", "description": "销售净利率"},
                    {"name": "grossprofit_margin", "type": "float", "description": "销售毛利率"},
                    {"name": "cogs_of_sales", "type": "float", "description": "销售成本率"},
                    {"name": "expense_of_sales", "type": "float", "description": "销售期间费用率"},
                    {"name": "profit_to_gr", "type": "float", "description": "净利润/营业总收入"},
                    {"name": "saleexp_to_gr", "type": "float", "description": "销售费用/营业总收入"},
                    {"name": "adminexp_of_gr", "type": "float", "description": "管理费用/营业总收入"},
                    {"name": "finaexp_of_gr", "type": "float", "description": "财务费用/营业总收入"},
                    {"name": "impai_ttm", "type": "float", "description": "资产减值损失/营业总收入"},
                    {"name": "gc_of_gr", "type": "float", "description": "营业总成本/营业总收入"},
                    {"name": "op_of_gr", "type": "float", "description": "营业利润/营业总收入"},
                    {"name": "ebit_of_gr", "type": "float", "description": "息税前利润/营业总收入"},
                    {"name": "roe", "type": "float", "description": "净资产收益率"},
                    {"name": "roe_waa", "type": "float", "description": "加权平均净资产收益率"},
                    {"name": "roe_dt", "type": "float", "description": "净资产收益率(扣除非经常损益)"},
                    {"name": "roa", "type": "float", "description": "总资产报酬率"},
                    {"name": "npta", "type": "float", "description": "总资产净利润"},
                    {"name": "roic", "type": "float", "description": "投入资本回报率"},
                    {"name": "roe_yearly", "type": "float", "description": "年化净资产收益率"},
                    {"name": "roa2_yearly", "type": "float", "description": "年化总资产报酬率"},
                    {"name": "roe_avg", "type": "float", "description": "平均净资产收益率(增发条件)"},
                    {"name": "opincome_of_ebt", "type": "float", "description": "经营活动净收益/利润总额"},
                    {"name": "investincome_of_ebt", "type": "float", "description": "价值变动净收益/利润总额"},
                    {"name": "n_op_profit_of_ebt", "type": "float", "description": "营业外收支净额/利润总额"},
                    {"name": "tax_to_ebt", "type": "float", "description": "所得税/利润总额"},
                    {"name": "dtprofit_to_profit", "type": "float", "description": "扣除非经常损益后的净利润/净利润"},
                    {"name": "salescash_to_or", "type": "float", "description": "销售商品提供劳务收到的现金/营业收入"},
                    {"name": "ocf_to_or", "type": "float", "description": "经营活动产生的现金流量净额/营业收入"},
                    {"name": "ocf_to_opincome", "type": "float", "description": "经营活动产生的现金流量净额/经营活动净收益"},
                    {"name": "capitalized_to_da", "type": "float", "description": "资本支出/折旧和摊销"},
                    {"name": "debt_to_assets", "type": "float", "description": "资产负债率"},
                    {"name": "assets_to_eqt", "type": "float", "description": "权益乘数"},
                    {"name": "dp_assets_to_eqt", "type": "float", "description": "权益乘数(杜邦分析)"},
                    {"name": "ca_to_assets", "type": "float", "description": "流动资产/总资产"},
                    {"name": "nca_to_assets", "type": "float", "description": "非流动资产/总资产"},
                    {"name": "tbassets_to_totalassets", "type": "float", "description": "有形资产/总资产"},
                    {"name": "int_to_talcap", "type": "float", "description": "带息债务/全部投入资本"},
                    {"name": "eqt_to_talcapital", "type": "float", "description": "归属于母公司的股东权益/全部投入资本"},
                    {"name": "currentdebt_to_debt", "type": "float", "description": "流动负债/负债合计"},
                    {"name": "longdeb_to_debt", "type": "float", "description": "非流动负债/负债合计"},
                    {"name": "ocf_to_shortdebt", "type": "float", "description": "经营活动产生的现金流量净额/流动负债"},
                    {"name": "debt_to_eqt", "type": "float", "description": "产权比率"},
                    {"name": "eqt_to_debt", "type": "float", "description": "归属于母公司的股东权益/负债合计"},
                    {"name": "eqt_to_interestdebt", "type": "float", "description": "归属于母公司的股东权益/带息债务"},
                    {"name": "tangibleasset_to_debt", "type": "float", "description": "有形资产/负债合计"},
                    {"name": "tangasset_to_intdebt", "type": "float", "description": "有形资产/带息债务"},
                    {"name": "tangibleasset_to_netdebt", "type": "float", "description": "有形资产/净债务"},
                    {"name": "ocf_to_debt", "type": "float", "description": "经营活动产生现金流量净额/负债合计"},
                    {"name": "ocf_to_interestdebt", "type": "float", "description": "经营活动产生现金流量净额/带息债务"},
                    {"name": "ocf_to_netdebt", "type": "float", "description": "经营活动产生现金流量净额/净债务"},
                    {"name": "ebit_to_interest", "type": "float", "description": "已获利息倍数(EBIT/利息费用)"},
                    {"name": "longdebt_to_workingcapital", "type": "float", "description": "长期债务与营运资金比率"},
                    {"name": "ebitda_to_debt", "type": "float", "description": "息税折旧摊销前利润/负债合计"},
                    {"name": "turn_days", "type": "float", "description": "营业周期"},
                    {"name": "roa_yearly", "type": "float", "description": "年化总资产净利率"},
                    {"name": "roa_dp", "type": "float", "description": "总资产净利率(杜邦分析)"},
                    {"name": "fixed_assets", "type": "float", "description": "固定资产合计"},
                    {"name": "profit_prefin_exp", "type": "float", "description": "扣除财务费用前营业利润"},
                    {"name": "non_op_profit", "type": "float", "description": "非营业利润"},
                    {"name": "op_to_ebt", "type": "float", "description": "营业利润／利润总额"},
                    {"name": "nop_to_ebt", "type": "float", "description": "非营业利润／利润总额"},
                    {"name": "ocf_to_profit", "type": "float", "description": "经营活动产生的现金流量净额／营业利润"},
                    {"name": "cash_to_liqdebt", "type": "float", "description": "货币资金／流动负债"},
                    {"name": "cash_to_liqdebt_withinterest", "type": "float", "description": "货币资金／带息流动负债"},
                    {"name": "op_to_liqdebt", "type": "float", "description": "营业利润／流动负债"},
                    {"name": "op_to_debt", "type": "float", "description": "营业利润／负债合计"},
                    {"name": "roic_yearly", "type": "float", "description": "年化投入资本回报率"},
                    {"name": "total_fa_trun", "type": "float", "description": "固定资产合计周转率"},
                    {"name": "profit_to_op", "type": "float", "description": "利润总额／营业收入"},
                    {"name": "q_opincome", "type": "float", "description": "经营活动单季度净收益"},
                    {"name": "q_investincome", "type": "float", "description": "价值变动单季度净收益"},
                    {"name": "q_dtprofit", "type": "float", "description": "扣除非经常损益后的单季度净利润"},
                    {"name": "q_eps", "type": "float", "description": "每股收益(单季度)"},
                    {"name": "q_netprofit_margin", "type": "float", "description": "销售净利率(单季度)"},
                    {"name": "q_gsprofit_margin", "type": "float", "description": "销售毛利率(单季度)"},
                    {"name": "q_exp_to_sales", "type": "float", "description": "销售期间费用率(单季度)"},
                    {"name": "q_profit_to_gr", "type": "float", "description": "净利润／营业总收入(单季度)"},
                    {"name": "q_saleexp_to_gr", "type": "float", "description": "销售费用／营业总收入 (单季度)"},
                    {"name": "q_adminexp_to_gr", "type": "float", "description": "管理费用／营业总收入 (单季度)"},
                    {"name": "q_finaexp_to_gr", "type": "float", "description": "财务费用／营业总收入 (单季度)"},
                    {"name": "q_impair_to_gr_ttm", "type": "float", "description": "资产减值损失／营业总收入(单季度)"},
                    {"name": "q_gc_to_gr", "type": "float", "description": "营业总成本／营业总收入 (单季度)"},
                    {"name": "q_op_to_gr", "type": "float", "description": "营业利润／营业总收入(单季度)"},
                    {"name": "q_roe", "type": "float", "description": "净资产收益率(单季度)"},
                    {"name": "q_dt_roe", "type": "float", "description": "净资产收益率(扣除非经常损益)(单季度)"},
                    {"name": "q_npta", "type": "float", "description": "总资产净利润(单季度)"},
                    {"name": "q_opincome_to_ebt", "type": "float", "description": "经营活动净收益／利润总额(单季度)"},
                    {"name": "q_investincome_to_ebt", "type": "float", "description": "价值变动净收益／利润总额(单季度)"},
                    {"name": "q_dtprofit_to_profit", "type": "float", "description": "扣除非经常损益后的净利润／净利润(单季度)"},
                    {"name": "q_salescash_to_or", "type": "float", "description": "销售商品提供劳务收到的现金／营业收入(单季度)"},
                    {"name": "q_ocf_to_sales", "type": "float", "description": "经营活动产生的现金流量净额／营业收入(单季度)"},
                    {"name": "q_ocf_to_or", "type": "float", "description": "经营活动产生的现金流量净额／经营活动净收益(单季度)"},
                    {"name": "basic_eps_yoy", "type": "float", "description": "基本每股收益同比增长率(%)"},
                    {"name": "dt_eps_yoy", "type": "float", "description": "稀释每股收益同比增长率(%)"},
                    {"name": "cfps_yoy", "type": "float", "description": "每股经营活动产生的现金流量净额同比增长率(%)"},
                    {"name": "op_yoy", "type": "float", "description": "营业利润同比增长率(%)"},
                    {"name": "ebt_yoy", "type": "float", "description": "利润总额同比增长率(%)"},
                    {"name": "netprofit_yoy", "type": "float", "description": "归属母公司股东的净利润同比增长率(%)"},
                    {"name": "dt_netprofit_yoy", "type": "float", "description": "归属母公司股东的净利润-扣除非经常损益同比增长率(%)"},
                    {"name": "ocf_yoy", "type": "float", "description": "经营活动产生的现金流量净额同比增长率(%)"},
                    {"name": "roe_yoy", "type": "float", "description": "净资产收益率(摊薄)同比增长率(%)"},
                    {"name": "bps_yoy", "type": "float", "description": "每股净资产相对年初增长率(%)"},
                    {"name": "assets_yoy", "type": "float", "description": "资产总计相对年初增长率(%)"},
                    {"name": "eqt_yoy", "type": "float", "description": "归属母公司的股东权益相对年初增长率(%)"},
                    {"name": "tr_yoy", "type": "float", "description": "营业总收入同比增长率(%)"},
                    {"name": "or_yoy", "type": "float", "description": "营业收入同比增长率(%)"},
                    {"name": "q_gr_yoy", "type": "float", "description": "营业总收入同比增长率(%)(单季度)"},
                    {"name": "q_gr_qoq", "type": "float", "description": "营业总收入环比增长率(%)(单季度)"},
                    {"name": "q_sales_yoy", "type": "float", "description": "营业收入同比增长率(%)(单季度)"},
                    {"name": "q_sales_qoq", "type": "float", "description": "营业收入环比增长率(%)(单季度)"},
                    {"name": "q_op_yoy", "type": "float", "description": "营业利润同比增长率(%)(单季度)"},
                    {"name": "q_op_qoq", "type": "float", "description": "营业利润环比增长率(%)(单季度)"},
                    {"name": "q_profit_yoy", "type": "float", "description": "净利润同比增长率(%)(单季度)"},
                    {"name": "q_profit_qoq", "type": "float", "description": "净利润环比增长率(%)(单季度)"},
                    {"name": "q_netprofit_yoy", "type": "float", "description": "归属母公司股东的净利润同比增长率(%)(单季度)"},
                    {"name": "q_netprofit_qoq", "type": "float", "description": "归属母公司股东的净利润环比增长率(%)(单季度)"},
                    {"name": "equity_yoy", "type": "float", "description": "净资产同比增长率"},
                    {"name": "rd_exp", "type": "float", "description": "研发费用"}
                ],
                "required_points": 2000,
                "rate_limit": 200
            }
        ]
    
    def sync_apis_to_database(self, data_source_id: int) -> Dict[str, Any]:
        """同步API接口到数据库
        
        Args:
            data_source_id: 数据源ID
            
        Returns:
            同步结果
        """
        try:
            db_gen = get_db()
            db_session = next(db_gen)
            
            try:
                # 创建同步任务记录
                task_query = """
                    INSERT INTO api_sync_tasks (data_source_id, task_name, task_type, status, started_at)
                    VALUES (:data_source_id, :task_name, :task_type, 'running', CURRENT_TIMESTAMP)
                """
                
                task_result = db_session.execute(text(task_query), {
                    'data_source_id': data_source_id,
                    'task_name': f'Tushare API同步 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    'task_type': 'full_sync'
                })
                
                task_id = task_result.lastrowid
                
                new_apis = 0
                updated_apis = 0
                failed_apis = 0
                
                for api_def in self.tushare_apis:
                    try:
                        # 检查API是否已存在
                        check_query = """
                            SELECT id FROM api_interfaces 
                            WHERE data_source_id = :data_source_id AND api_code = :api_code
                        """
                        
                        existing = db_session.execute(text(check_query), {
                            'data_source_id': data_source_id,
                            'api_code': api_def['api_code']
                        }).fetchone()
                        
                        if existing:
                            # 更新现有API
                            update_query = """
                                UPDATE api_interfaces 
                                SET api_name = :api_name,
                                    api_category = :api_category,
                                    description = :description,
                                    endpoint = :endpoint,
                                    method = :method,
                                    required_params = :required_params,
                                    optional_params = :optional_params,
                                    response_fields = :response_fields,
                                    required_points = :required_points,
                                    rate_limit = :rate_limit,
                                    synced_at = CURRENT_TIMESTAMP,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = :id
                            """
                            
                            db_session.execute(text(update_query), {
                                'id': existing.id,
                                'api_name': api_def['api_name'],
                                'api_category': api_def['api_category'],
                                'description': api_def['description'],
                                'endpoint': api_def['endpoint'],
                                'method': api_def['method'],
                                'required_params': json.dumps(api_def['required_params']),
                                'optional_params': json.dumps(api_def['optional_params']),
                                'response_fields': json.dumps(api_def['response_fields']),
                                'required_points': api_def['required_points'],
                                'rate_limit': api_def['rate_limit']
                            })
                            
                            updated_apis += 1
                        else:
                            # 插入新API
                            insert_query = """
                                INSERT INTO api_interfaces (
                                    data_source_id, api_code, api_name, api_category, description,
                                    endpoint, method, required_params, optional_params, response_fields,
                                    required_points, rate_limit, status, synced_at
                                ) VALUES (
                                    :data_source_id, :api_code, :api_name, :api_category, :description,
                                    :endpoint, :method, :required_params, :optional_params, :response_fields,
                                    :required_points, :rate_limit, 'active', CURRENT_TIMESTAMP
                                )
                            """
                            
                            db_session.execute(text(insert_query), {
                                'data_source_id': data_source_id,
                                'api_code': api_def['api_code'],
                                'api_name': api_def['api_name'],
                                'api_category': api_def['api_category'],
                                'description': api_def['description'],
                                'endpoint': api_def['endpoint'],
                                'method': api_def['method'],
                                'required_params': json.dumps(api_def['required_params']),
                                'optional_params': json.dumps(api_def['optional_params']),
                                'response_fields': json.dumps(api_def['response_fields']),
                                'required_points': api_def['required_points'],
                                'rate_limit': api_def['rate_limit']
                            })
                            
                            new_apis += 1
                            
                    except Exception as api_error:
                        logger.error(f"同步API {api_def['api_code']} 失败: {api_error}")
                        failed_apis += 1
                
                # 更新同步任务状态
                update_task_query = """
                    UPDATE api_sync_tasks 
                    SET status = 'completed',
                        completed_at = CURRENT_TIMESTAMP,
                        progress = 100,
                        total_apis = :total_apis,
                        new_apis = :new_apis,
                        updated_apis = :updated_apis,
                        failed_apis = :failed_apis
                    WHERE id = :task_id
                """
                
                db_session.execute(text(update_task_query), {
                    'task_id': task_id,
                    'total_apis': len(self.tushare_apis),
                    'new_apis': new_apis,
                    'updated_apis': updated_apis,
                    'failed_apis': failed_apis
                })
                
                db_session.commit()
                
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
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"同步API到数据库失败: {e}")
            return {
                'success': False,
                'error': '同步API失败',
                'message': str(e)
            }

# 全局实例
tushare_api_sync_service = TushareApiSyncService()