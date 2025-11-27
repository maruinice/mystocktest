"""
实时行情服务
支持多个免费数据源，自动切换，确保数据获取的稳定性
"""

import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class RealtimeQuoteService:
    """实时行情服务"""
    
    def __init__(self):
        """初始化服务"""
        # 调整数据源优先级：腾讯 > 东方财富 > 新浪
        self.data_sources = ['tencent', 'eastmoney', 'sina']
        self.current_source = 0
        self.cache = {}  # 简单缓存，避免频繁请求
        self.cache_timeout = 3  # 缓存3秒
        
        # 添加请求头，避免被拦截
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://finance.sina.com.cn',
        }
    
    def get_realtime_price(self, stock_code: str) -> Optional[Dict]:
        """
        获取实时价格（自动切换数据源）
        
        Args:
            stock_code: 股票代码，如 '000001'、'600519' 或 '300001.SZ'
            
        Returns:
            {
                'code': '000001',
                'name': '平安银行',
                'current': 80.50,      # 当前价
                'open': 80.00,         # 今开
                'close': 79.80,        # 昨收
                'high': 81.00,         # 最高
                'low': 79.50,          # 最低
                'volume': 1000000,     # 成交量
                'amount': 80000000.0,  # 成交额
                'time': '15:00:00',    # 时间
                'change': 0.70,        # 涨跌额
                'change_pct': 0.88,    # 涨跌幅%
            }
        """
        # 标准化股票代码：去除后缀（如 .SZ, .SH）
        original_code = stock_code
        if '.' in stock_code:
            stock_code = stock_code.split('.')[0]
        
        # 检查缓存
        cache_key = f"{stock_code}_{int(time.time() / self.cache_timeout)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 尝试所有数据源
        for i in range(len(self.data_sources)):
            source = self.data_sources[self.current_source]
            try:
                if source == 'sina':
                    data = self._get_from_sina(stock_code)
                elif source == 'tencent':
                    data = self._get_from_tencent(stock_code)
                elif source == 'eastmoney':
                    data = self._get_from_eastmoney(stock_code)
                else:
                    data = None
                
                if data and data.get('current', 0) > 0:
                    # 计算涨跌
                    if data.get('close', 0) > 0:
                        data['change'] = data['current'] - data['close']
                        data['change_pct'] = (data['change'] / data['close']) * 100
                    
                    # 缓存结果
                    self.cache[cache_key] = data
                    logger.info(f"从{source}获取{stock_code}行情成功: ¥{data['current']}")
                    return data
                
            except Exception as e:
                logger.warning(f"从{source}获取{stock_code}行情失败: {e}")
                # 切换到下一个数据源
                self.current_source = (self.current_source + 1) % len(self.data_sources)
        
        logger.error(f"所有数据源都无法获取{stock_code}的行情")
        return None
    
    def _get_from_sina(self, stock_code: str) -> Optional[Dict]:
        """从新浪财经获取实时行情"""
        # 转换为新浪格式
        if stock_code.startswith('6'):
            sina_code = f'sh{stock_code}'  # 上海
        else:
            sina_code = f'sz{stock_code}'  # 深圳
        
        url = f'http://hq.sinajs.cn/list={sina_code}'
        response = requests.get(url, headers=self.headers, timeout=5)
        
        if response.status_code == 200 and response.text:
            # 解析数据
            content = response.text
            if 'var hq_str_' in content:
                data_str = content.split('"')[1]
                if data_str:
                    data = data_str.split(',')
                    return {
                        'code': stock_code,
                        'name': data[0],
                        'open': float(data[1]) if data[1] else 0.0,
                        'close': float(data[2]) if data[2] else 0.0,
                        'current': float(data[3]) if data[3] else 0.0,
                        'high': float(data[4]) if data[4] else 0.0,
                        'low': float(data[5]) if data[5] else 0.0,
                        'volume': int(float(data[8])) if data[8] else 0,
                        'amount': float(data[9]) if data[9] else 0.0,
                        'time': data[31] if len(data) > 31 else '',
                        'source': 'sina',
                    }
        return None
    
    def _get_from_tencent(self, stock_code: str) -> Optional[Dict]:
        """从腾讯财经获取实时行情"""
        if stock_code.startswith('6'):
            qq_code = f'sh{stock_code}'
        else:
            qq_code = f'sz{stock_code}'
        
        url = f'http://qt.gtimg.cn/q={qq_code}'
        response = requests.get(url, headers=self.headers, timeout=5)
        
        if response.status_code == 200 and response.text:
            # 解析数据
            content = response.text
            if 'v_' in content:
                data_str = content.split('"')[1]
                if data_str:
                    data = data_str.split('~')
                    if len(data) > 34:
                        return {
                            'code': stock_code,
                            'name': data[1],
                            'current': float(data[3]) if data[3] else 0.0,
                            'close': float(data[4]) if data[4] else 0.0,
                            'open': float(data[5]) if data[5] else 0.0,
                            'volume': int(float(data[6])) if data[6] else 0,
                            'high': float(data[33]) if data[33] else 0.0,
                            'low': float(data[34]) if data[34] else 0.0,
                            'amount': float(data[37]) if len(data) > 37 and data[37] else 0.0,
                            'time': data[30] if len(data) > 30 else '',
                            'source': 'tencent',
                        }
        return None
    
    def _get_from_eastmoney(self, stock_code: str) -> Optional[Dict]:
        """从东方财富获取实时行情"""
        if stock_code.startswith('6'):
            em_code = f'1.{stock_code}'  # 上海
        else:
            em_code = f'0.{stock_code}'  # 深圳
        
        url = 'http://push2.eastmoney.com/api/qt/stock/get'
        params = {
            'secid': em_code,
            'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60',
        }
        response = requests.get(url, params=params, headers=self.headers, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('data'):
                data = result['data']
                return {
                    'code': stock_code,
                    'name': data.get('f58', ''),
                    'current': data.get('f43', 0) / 100 if data.get('f43') else 0.0,
                    'close': data.get('f60', 0) / 100 if data.get('f60') else 0.0,
                    'open': data.get('f46', 0) / 100 if data.get('f46') else 0.0,
                    'high': data.get('f44', 0) / 100 if data.get('f44') else 0.0,
                    'low': data.get('f45', 0) / 100 if data.get('f45') else 0.0,
                    'volume': data.get('f47', 0),
                    'amount': data.get('f48', 0),
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'source': 'eastmoney',
                }
        return None
    
    def get_batch_realtime_prices(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """
        批量获取实时价格
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            {
                '000001': {...},
                '600519': {...},
            }
        """
        results = {}
        for code in stock_codes:
            data = self.get_realtime_price(code)
            if data:
                results[code] = data
        return results


# 全局实例
realtime_quote_service = RealtimeQuoteService()


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    service = RealtimeQuoteService()
    
    # 测试单个股票
    print("=" * 60)
    print("测试获取平安银行实时行情:")
    print("=" * 60)
    data = service.get_realtime_price('000001')
    if data:
        print(f"股票代码: {data['code']}")
        print(f"股票名称: {data['name']}")
        print(f"当前价格: ¥{data['current']:.2f}")
        print(f"今日开盘: ¥{data['open']:.2f}")
        print(f"昨日收盘: ¥{data['close']:.2f}")
        print(f"今日最高: ¥{data['high']:.2f}")
        print(f"今日最低: ¥{data['low']:.2f}")
        print(f"涨跌额: ¥{data.get('change', 0):.2f}")
        print(f"涨跌幅: {data.get('change_pct', 0):.2f}%")
        print(f"成交量: {data['volume']:,}")
        print(f"数据源: {data.get('source', 'unknown')}")
    
    # 测试批量获取
    print("\n" + "=" * 60)
    print("测试批量获取行情:")
    print("=" * 60)
    codes = ['000001', '600519', '600036']
    batch_data = service.get_batch_realtime_prices(codes)
    for code, data in batch_data.items():
        print(f"{code} ({data['name']}): ¥{data['current']:.2f}")
