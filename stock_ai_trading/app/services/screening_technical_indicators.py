"""
选股功能专用技术指标计算模块
提供MA、RSI、KDJ等选股常用技术指标的快速计算
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ScreeningTechnicalIndicators:
    """选股技术指标计算器"""
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: List[int] = [5, 20, 60]) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: 包含close列的DataFrame
            periods: 周期列表，默认[5, 20, 60]
            
        Returns:
            添加了ma5, ma20, ma60列的DataFrame
        """
        try:
            if 'close' not in df.columns:
                logger.error("数据中缺少close列")
                return df
            
            for period in periods:
                col_name = f'ma{period}'
                df[col_name] = df['close'].rolling(window=period, min_periods=period).mean()
                logger.debug(f"计算{col_name}完成")
            
            return df
            
        except Exception as e:
            logger.error(f"计算MA失败: {e}")
            return df
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 12) -> pd.DataFrame:
        """
        计算RSI相对强弱指数
        
        Args:
            df: 包含close列的DataFrame
            period: RSI周期，默认12
            
        Returns:
            添加了rsi12列的DataFrame
        """
        try:
            if 'close' not in df.columns:
                logger.error("数据中缺少close列")
                return df
            
            # 计算价格变化
            delta = df['close'].diff()
            
            # 分离上涨和下跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # 计算平均涨跌幅
            avg_gain = gain.rolling(window=period, min_periods=period).mean()
            avg_loss = loss.rolling(window=period, min_periods=period).mean()
            
            # 计算RS和RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            col_name = f'rsi{period}'
            df[col_name] = rsi
            logger.debug(f"计算{col_name}完成")
            
            return df
            
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return df
    
    @staticmethod
    def calculate_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """
        计算KDJ指标
        
        Args:
            df: 包含high, low, close列的DataFrame
            n: RSV周期，默认9
            m1: K值平滑参数，默认3
            m2: D值平滑参数，默认3
            
        Returns:
            添加了kdj_k, kdj_d, kdj_j列的DataFrame
        """
        try:
            required_cols = ['high', 'low', 'close']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"数据中缺少必要列: {required_cols}")
                return df
            
            # 确保数据类型为float
            close = pd.to_numeric(df['close'], errors='coerce')
            high = pd.to_numeric(df['high'], errors='coerce')
            low = pd.to_numeric(df['low'], errors='coerce')
            
            # 计算RSV (未成熟随机值)
            low_n = low.rolling(window=n, min_periods=n).min()
            high_n = high.rolling(window=n, min_periods=n).max()
            
            # 避免除零
            denominator = high_n - low_n
            rsv = np.where(
                denominator != 0,
                (close - low_n) / denominator * 100,
                50  # 默认值
            )
            rsv = pd.Series(rsv, index=df.index)
            
            # 计算K值 (RSV的移动平均)
            # K = (2/3) * 前一日K + (1/3) * 当日RSV
            # 使用ewm实现: alpha = 1/m1
            k = rsv.ewm(alpha=1/m1, adjust=False).mean()
            
            # 计算D值 (K的移动平均)
            # D = (2/3) * 前一日D + (1/3) * 当日K
            d = k.ewm(alpha=1/m2, adjust=False).mean()
            
            # 计算J值
            j = 3 * k - 2 * d
            
            df['kdj_k'] = k
            df['kdj_d'] = d
            df['kdj_j'] = j
            
            logger.debug("计算KDJ完成")
            
            return df
            
        except Exception as e:
            logger.error(f"计算KDJ失败: {e}")
            return df
    
    @staticmethod
    def calculate_all_screening_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有选股需要的技术指标
        
        Args:
            df: 包含OHLC数据的DataFrame
            
        Returns:
            添加了所有技术指标的DataFrame
        """
        try:
            # 计算MA
            df = ScreeningTechnicalIndicators.calculate_ma(df, periods=[5, 20, 60])
            
            # 计算RSI
            df = ScreeningTechnicalIndicators.calculate_rsi(df, period=12)
            
            # 计算KDJ
            df = ScreeningTechnicalIndicators.calculate_kdj(df, n=9)
            
            logger.info("所有选股技术指标计算完成")
            
            return df
            
        except Exception as e:
            logger.error(f"计算选股技术指标失败: {e}")
            return df
    
    @staticmethod
    def get_latest_indicators(df: pd.DataFrame) -> Dict[str, float]:
        """
        获取最新的技术指标值
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            最新指标值的字典
        """
        try:
            if df.empty:
                return {}
            
            latest = df.iloc[-1]
            indicators = {}
            
            # MA指标
            for period in [5, 20, 60]:
                col_name = f'ma{period}'
                if col_name in df.columns:
                    indicators[col_name] = float(latest[col_name]) if pd.notna(latest[col_name]) else None
            
            # RSI指标
            if 'rsi12' in df.columns:
                indicators['rsi12'] = float(latest['rsi12']) if pd.notna(latest['rsi12']) else None
            
            # KDJ指标
            for col in ['kdj_k', 'kdj_d', 'kdj_j']:
                if col in df.columns:
                    indicators[col] = float(latest[col]) if pd.notna(latest[col]) else None
            
            return indicators
            
        except Exception as e:
            logger.error(f"获取最新指标值失败: {e}")
            return {}
    
    @staticmethod
    def validate_data(df: pd.DataFrame, min_periods: int = 60) -> bool:
        """
        验证数据是否满足计算要求
        
        Args:
            df: 数据DataFrame
            min_periods: 最小数据周期数
            
        Returns:
            是否满足要求
        """
        if df.empty:
            logger.warning("数据为空")
            return False
        
        if len(df) < min_periods:
            logger.warning(f"数据不足{min_periods}个周期，当前{len(df)}个")
            return False
        
        required_cols = ['close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"缺少必要列: {missing_cols}")
            return False
        
        return True


# 创建全局实例
screening_tech_indicators = ScreeningTechnicalIndicators()


# 便捷函数
def calculate_screening_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    便捷函数：计算所有选股技术指标
    
    Args:
        df: OHLC数据
        
    Returns:
        添加了技术指标的DataFrame
    """
    return screening_tech_indicators.calculate_all_screening_indicators(df)


def get_latest_technical_values(df: pd.DataFrame) -> Dict[str, float]:
    """
    便捷函数：获取最新技术指标值
    
    Args:
        df: 包含技术指标的DataFrame
        
    Returns:
        最新指标值字典
    """
    return screening_tech_indicators.get_latest_indicators(df)


# 批量计算函数
def batch_calculate_indicators(stock_data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, float]]:
    """
    批量计算多只股票的技术指标
    
    Args:
        stock_data_dict: {ts_code: DataFrame} 字典
        
    Returns:
        {ts_code: {indicator: value}} 字典
    """
    results = {}
    
    for ts_code, df in stock_data_dict.items():
        try:
            # 验证数据
            if not screening_tech_indicators.validate_data(df):
                logger.warning(f"{ts_code}: 数据不满足计算要求")
                results[ts_code] = {}
                continue
            
            # 计算指标
            df_with_indicators = calculate_screening_indicators(df.copy())
            
            # 获取最新值
            latest_values = get_latest_technical_values(df_with_indicators)
            results[ts_code] = latest_values
            
        except Exception as e:
            logger.error(f"{ts_code}: 计算失败 - {e}")
            results[ts_code] = {}
    
    return results


if __name__ == '__main__':
    # 测试代码
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from app.core.database import get_db
    from sqlalchemy import text
    
    print("\n" + "="*80)
    print("技术指标计算测试")
    print("="*80)
    
    # 获取测试数据
    db = next(get_db())
    result = db.execute(text("""
        SELECT trade_date, open_price as open, high_price as high, 
               low_price as low, close_price as close, volume
        FROM daily_history
        WHERE ts_code = '000001.SZ'
        ORDER BY trade_date DESC
        LIMIT 100
    """)).fetchall()
    
    if result:
        # 转换为DataFrame
        df = pd.DataFrame(result, columns=['trade_date', 'open', 'high', 'low', 'close', 'volume'])
        df = df.sort_values('trade_date').reset_index(drop=True)
        
        print(f"\n获取到 {len(df)} 条数据")
        print(f"日期范围: {df['trade_date'].min()} ~ {df['trade_date'].max()}")
        
        # 计算技术指标
        print("\n计算技术指标...")
        df_with_indicators = calculate_screening_indicators(df)
        
        # 显示最新值
        latest = get_latest_technical_values(df_with_indicators)
        print("\n最新技术指标值:")
        for indicator, value in latest.items():
            if value is not None:
                print(f"  {indicator:15s}: {value:10.2f}")
            else:
                print(f"  {indicator:15s}: N/A")
        
        # 显示最后几行数据
        print("\n最后5行数据:")
        cols_to_show = ['trade_date', 'close', 'ma5', 'ma20', 'ma60', 'rsi12', 'kdj_k', 'kdj_d']
        print(df_with_indicators[cols_to_show].tail())
        
    else:
        print("未找到测试数据")
