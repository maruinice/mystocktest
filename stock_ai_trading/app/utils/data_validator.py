"""
数据质量验证器
提供各种数据类型的验证功能
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """数据验证器类"""
    
    def __init__(self):
        """初始化验证器"""
        # 股票代码正则表达式
        self.stock_code_patterns = {
            'SH': r'^[0-9]{6}\.SH$',  # 上海证券交易所
            'SZ': r'^[0-9]{6}\.SZ$',  # 深圳证券交易所
            'BJ': r'^[0-9]{6}\.BJ$',  # 北京证券交易所
        }
        
        # 日期格式
        self.date_formats = ['%Y%m%d', '%Y-%m-%d', '%Y/%m/%d']
        
        # 数据质量阈值
        self.quality_thresholds = {
            'missing_rate': 0.1,  # 缺失率阈值10%
            'duplicate_rate': 0.05,  # 重复率阈值5%
            'outlier_rate': 0.02,  # 异常值率阈值2%
        }
    
    def validate_stock_code(self, code: str) -> bool:
        """验证股票代码格式"""
        if not isinstance(code, str):
            return False
        
        for exchange, pattern in self.stock_code_patterns.items():
            if re.match(pattern, code):
                return True
        
        return False
    
    def validate_date_format(self, date_str: str) -> bool:
        """验证日期格式"""
        if not isinstance(date_str, str):
            return False
        
        for fmt in self.date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def check_missing_values(self, df: pd.DataFrame, critical_columns: List[str] = None) -> Dict[str, Any]:
        """检查缺失值"""
        missing_info = {}
        
        # 整体缺失率
        total_missing = df.isnull().sum().sum()
        total_values = df.size
        missing_rate = total_missing / total_values if total_values > 0 else 0
        
        missing_info['total_missing_rate'] = missing_rate
        missing_info['column_missing'] = df.isnull().sum().to_dict()
        
        # 检查关键列的缺失情况
        if critical_columns:
            critical_missing = {}
            for col in critical_columns:
                if col in df.columns:
                    col_missing_rate = df[col].isnull().sum() / len(df) if len(df) > 0 else 0
                    critical_missing[col] = col_missing_rate
            missing_info['critical_missing'] = critical_missing
        
        return missing_info
    
    def check_duplicates(self, df: pd.DataFrame, subset: List[str] = None) -> Dict[str, Any]:
        """检查重复数据"""
        duplicate_info = {}
        
        # 检查完全重复的行
        total_duplicates = df.duplicated().sum()
        duplicate_rate = total_duplicates / len(df) if len(df) > 0 else 0
        
        duplicate_info['total_duplicates'] = total_duplicates
        duplicate_info['duplicate_rate'] = duplicate_rate
        
        # 检查指定列的重复情况
        if subset:
            subset_duplicates = df.duplicated(subset=subset).sum()
            subset_duplicate_rate = subset_duplicates / len(df) if len(df) > 0 else 0
            duplicate_info['subset_duplicates'] = subset_duplicates
            duplicate_info['subset_duplicate_rate'] = subset_duplicate_rate
        
        return duplicate_info
    
    def check_outliers(self, df: pd.DataFrame, numeric_columns: List[str] = None) -> Dict[str, Any]:
        """检查异常值（使用IQR方法）"""
        outlier_info = {}
        
        if numeric_columns is None:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_columns:
            if col in df.columns and df[col].dtype in [np.float64, np.int64, np.float32, np.int32]:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                outlier_count = len(outliers)
                outlier_rate = outlier_count / len(df) if len(df) > 0 else 0
                
                outlier_info[col] = {
                    'count': outlier_count,
                    'rate': outlier_rate,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                }
        
        return outlier_info
    
    def validate_data_quality(self, df: pd.DataFrame, 
                            critical_columns: List[str] = None,
                            numeric_columns: List[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """综合数据质量验证"""
        quality_report = {}
        is_valid = True
        
        # 检查基本信息
        quality_report['basic_info'] = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum()
        }
        
        # 检查缺失值
        missing_info = self.check_missing_values(df, critical_columns)
        quality_report['missing_values'] = missing_info
        
        if missing_info['total_missing_rate'] > self.quality_thresholds['missing_rate']:
            is_valid = False
            logger.warning(f"数据缺失率过高: {missing_info['total_missing_rate']:.2%}")
        
        # 检查重复数据
        duplicate_info = self.check_duplicates(df, critical_columns)
        quality_report['duplicates'] = duplicate_info
        
        if duplicate_info['duplicate_rate'] > self.quality_thresholds['duplicate_rate']:
            is_valid = False
            logger.warning(f"数据重复率过高: {duplicate_info['duplicate_rate']:.2%}")
        
        # 检查异常值
        outlier_info = self.check_outliers(df, numeric_columns)
        quality_report['outliers'] = outlier_info
        
        # 计算平均异常值率
        if outlier_info:
            avg_outlier_rate = np.mean([info['rate'] for info in outlier_info.values()])
            if avg_outlier_rate > self.quality_thresholds['outlier_rate']:
                is_valid = False
                logger.warning(f"平均异常值率过高: {avg_outlier_rate:.2%}")
        
        quality_report['is_valid'] = is_valid
        return is_valid, quality_report
    
    # ==================== 特定数据类型验证 ====================
    
    def validate_stock_basic(self, df: pd.DataFrame) -> bool:
        """验证股票基础数据"""
        required_columns = ['ts_code', 'symbol', 'name', 'area', 'industry', 'list_date']
        
        # 检查必需列
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"股票基础数据缺少必需列: {missing_columns}")
            return False
        
        # 验证股票代码格式
        if 'ts_code' in df.columns:
            invalid_codes = df[~df['ts_code'].apply(self.validate_stock_code)]
            if len(invalid_codes) > 0:
                logger.error(f"发现{len(invalid_codes)}个无效股票代码")
                return False
        
        # 验证上市日期格式
        if 'list_date' in df.columns:
            invalid_dates = df[df['list_date'].notna() & 
                             ~df['list_date'].astype(str).apply(self.validate_date_format)]
            if len(invalid_dates) > 0:
                logger.error(f"发现{len(invalid_dates)}个无效上市日期")
                return False
        
        # 数据质量检查
        is_valid, _ = self.validate_data_quality(df, critical_columns=['ts_code', 'name'])
        return is_valid
    
    def validate_daily_quotes(self, df: pd.DataFrame) -> bool:
        """验证日线行情数据"""
        required_columns = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol']
        
        # 检查必需列
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"日线数据缺少必需列: {missing_columns}")
            return False
        
        # 验证价格逻辑关系
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # 最高价应该 >= 开盘价、收盘价、最低价
            invalid_high = df[(df['high'] < df['open']) | 
                            (df['high'] < df['close']) | 
                            (df['high'] < df['low'])]
            if len(invalid_high) > 0:
                logger.error(f"发现{len(invalid_high)}条最高价异常数据")
                return False
            
            # 最低价应该 <= 开盘价、收盘价、最高价
            invalid_low = df[(df['low'] > df['open']) | 
                           (df['low'] > df['close']) | 
                           (df['low'] > df['high'])]
            if len(invalid_low) > 0:
                logger.error(f"发现{len(invalid_low)}条最低价异常数据")
                return False
        
        # 验证交易日期格式
        if 'trade_date' in df.columns:
            invalid_dates = df[~df['trade_date'].astype(str).apply(self.validate_date_format)]
            if len(invalid_dates) > 0:
                logger.error(f"发现{len(invalid_dates)}个无效交易日期")
                return False
        
        # 数据质量检查
        numeric_columns = ['open', 'high', 'low', 'close', 'vol', 'amount']
        is_valid, _ = self.validate_data_quality(df, 
                                               critical_columns=['ts_code', 'trade_date'],
                                               numeric_columns=numeric_columns)
        return is_valid
    
    def validate_financial_data(self, df: pd.DataFrame) -> bool:
        """验证财务数据"""
        required_columns = ['ts_code', 'ann_date', 'f_ann_date', 'end_date']
        
        # 检查必需列
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"财务数据缺少必需列: {missing_columns}")
            return False
        
        # 验证日期格式
        date_columns = ['ann_date', 'f_ann_date', 'end_date']
        for col in date_columns:
            if col in df.columns:
                invalid_dates = df[df[col].notna() & 
                                 ~df[col].astype(str).apply(self.validate_date_format)]
                if len(invalid_dates) > 0:
                    logger.error(f"发现{len(invalid_dates)}个无效{col}日期")
                    return False
        
        # 数据质量检查
        numeric_columns = [col for col in df.columns 
                         if df[col].dtype in [np.float64, np.int64, np.float32, np.int32]]
        is_valid, _ = self.validate_data_quality(df, 
                                               critical_columns=['ts_code', 'end_date'],
                                               numeric_columns=numeric_columns)
        return is_valid
    
    def validate_index_basic(self, df: pd.DataFrame) -> bool:
        """验证指数基础数据"""
        required_columns = ['ts_code', 'name', 'market', 'publisher', 'category']
        
        # 检查必需列
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"指数基础数据缺少必需列: {missing_columns}")
            return False
        
        # 数据质量检查
        is_valid, _ = self.validate_data_quality(df, critical_columns=['ts_code', 'name'])
        return is_valid
    
    def clean_data(self, df: pd.DataFrame, 
                   remove_duplicates: bool = True,
                   fill_missing: bool = True,
                   remove_outliers: bool = False) -> pd.DataFrame:
        """数据清洗"""
        cleaned_df = df.copy()
        
        # 移除重复数据
        if remove_duplicates:
            before_count = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            after_count = len(cleaned_df)
            if before_count != after_count:
                logger.info(f"移除了{before_count - after_count}条重复数据")
        
        # 填充缺失值
        if fill_missing:
            numeric_columns = cleaned_df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if cleaned_df[col].isnull().any():
                    # 使用前向填充
                    cleaned_df[col] = cleaned_df[col].fillna(method='ffill')
                    # 如果还有缺失值，使用0填充
                    cleaned_df[col] = cleaned_df[col].fillna(0)
        
        # 移除异常值（可选）
        if remove_outliers:
            numeric_columns = cleaned_df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                Q1 = cleaned_df[col].quantile(0.25)
                Q3 = cleaned_df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                before_count = len(cleaned_df)
                cleaned_df = cleaned_df[(cleaned_df[col] >= lower_bound) & 
                                      (cleaned_df[col] <= upper_bound)]
                after_count = len(cleaned_df)
                
                if before_count != after_count:
                    logger.info(f"列{col}移除了{before_count - after_count}个异常值")
        
        return cleaned_df