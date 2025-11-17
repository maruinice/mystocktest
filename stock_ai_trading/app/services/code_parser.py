"""
策略代码解析器
从Python代码中提取策略配置信息
"""
import re
import ast
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StrategyCodeParser:
    """策略代码解析器 - 从代码反向生成配置"""
    
    def __init__(self):
        self.indicators_map = {
            'ma': 'MA',
            'ema': 'EMA',
            'rsi': 'RSI',
            'macd': 'MACD',
            'kdj': 'KDJ',
            'bollinger': 'BOLL',
            'cci': 'CCI',
            'atr': 'ATR',
            'obv': 'OBV',
            'volume': 'VOLUME'
        }
    
    def parse_strategy_code(self, code: str) -> Dict[str, Any]:
        """
        解析策略代码，提取配置信息
        
        Args:
            code: 策略Python代码
            
        Returns:
            包含参数、指标、买入卖出条件的字典
        """
        try:
            result = {
                'parameters': {},
                'indicators': [],
                'buy_conditions': [],
                'sell_conditions': [],
                'risk_controls': {}
            }
            
            # 1. 提取参数
            result['parameters'] = self._extract_parameters(code)
            
            # 2. 提取技术指标
            result['indicators'] = self._extract_indicators(code)
            
            # 3. 提取买入条件
            result['buy_conditions'] = self._extract_buy_conditions(code)
            
            # 4. 提取卖出条件
            result['sell_conditions'] = self._extract_sell_conditions(code)
            
            # 5. 提取风险控制
            result['risk_controls'] = self._extract_risk_controls(code)
            
            logger.info(f"[代码解析] 成功解析策略代码")
            logger.info(f"[代码解析] 参数: {len(result['parameters'])}, 指标: {len(result['indicators'])}, "
                       f"买入条件: {len(result['buy_conditions'])}, 卖出条件: {len(result['sell_conditions'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"[代码解析] 解析失败: {e}")
            return {
                'parameters': {},
                'indicators': [],
                'buy_conditions': [],
                'sell_conditions': [],
                'risk_controls': {}
            }
    
    def _extract_parameters(self, code: str) -> Dict[str, Any]:
        """提取策略参数"""
        parameters = {}
        
        # 查找 initialize 函数中的 context.xxx = value 赋值
        init_pattern = r'def initialize\(context\):(.*?)(?=\ndef\s|\Z)'
        init_match = re.search(init_pattern, code, re.DOTALL)
        
        if init_match:
            init_code = init_match.group(1)
            
            # 提取 context.xxx = value 形式的参数
            param_pattern = r'context\.(\w+)\s*=\s*([^\n#]+)'
            for match in re.finditer(param_pattern, init_code):
                param_name = match.group(1)
                param_value = match.group(2).strip()
                
                # 跳过特殊属性
                if param_name in ['stocks', 'portfolio', 'asset']:
                    continue
                
                # 尝试解析值
                try:
                    # 移除注释
                    if '#' in param_value:
                        param_value = param_value.split('#')[0].strip()
                    
                    # 尝试转换为Python对象
                    parsed_value = ast.literal_eval(param_value)
                    parameters[param_name] = parsed_value
                except:
                    # 如果无法解析，保存为字符串
                    parameters[param_name] = param_value
        
        return parameters
    
    def _extract_indicators(self, code: str) -> List[str]:
        """提取使用的技术指标"""
        indicators = set()
        
        code_lower = code.lower()
        
        # 检查常见指标关键词
        for key, indicator in self.indicators_map.items():
            if key in code_lower:
                indicators.add(indicator)
        
        # 检查特定的函数调用
        if 'calculate_ma' in code_lower or 'mean()' in code_lower:
            indicators.add('MA')
        
        if 'calculate_rsi' in code_lower:
            indicators.add('RSI')
        
        if 'calculate_macd' in code_lower:
            indicators.add('MACD')
        
        return sorted(list(indicators))
    
    def _extract_buy_conditions(self, code: str) -> List[Dict[str, Any]]:
        """提取买入条件"""
        conditions = []
        
        # 查找买入相关的注释和代码
        buy_patterns = [
            r'#\s*买入条件[：:](.*?)(?=\n)',
            r'#\s*Buy condition[：:](.*?)(?=\n)',
            r'if\s+.*?买入.*?:',
            r'if\s+.*?buy.*?:',
        ]
        
        for pattern in buy_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                description = match.group(0).strip()
                
                # 清理描述
                description = re.sub(r'^#\s*', '', description)
                description = re.sub(r'^if\s+', '', description)
                description = re.sub(r':$', '', description)
                
                if description and len(description) > 5:
                    conditions.append({
                        'type': 'custom',
                        'description': description,
                        'operator': 'custom',
                        'value': ''
                    })
        
        # 如果没有找到注释，尝试从代码逻辑中提取
        if not conditions:
            # 查找包含买入逻辑的if语句
            if_pattern = r'if\s+(.*?)(?:and|or|\n).*?order_target_percent'
            matches = re.finditer(if_pattern, code, re.DOTALL)
            
            for match in matches:
                condition_text = match.group(1).strip()
                if len(condition_text) < 100:  # 避免太长的条件
                    conditions.append({
                        'type': 'custom',
                        'description': f'买入条件: {condition_text}',
                        'operator': 'custom',
                        'value': ''
                    })
        
        # 如果还是没有，返回默认条件
        if not conditions:
            conditions.append({
                'type': 'custom',
                'description': '根据策略逻辑触发买入信号',
                'operator': 'custom',
                'value': ''
            })
        
        return conditions[:5]  # 最多返回5个条件
    
    def _extract_sell_conditions(self, code: str) -> List[Dict[str, Any]]:
        """提取卖出条件"""
        conditions = []
        
        # 查找卖出相关的注释和代码
        sell_patterns = [
            r'#\s*卖出条件[：:](.*?)(?=\n)',
            r'#\s*Sell condition[：:](.*?)(?=\n)',
            r'elif\s+.*?卖出.*?:',
            r'elif\s+.*?sell.*?:',
        ]
        
        for pattern in sell_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                description = match.group(0).strip()
                
                # 清理描述
                description = re.sub(r'^#\s*', '', description)
                description = re.sub(r'^elif\s+', '', description)
                description = re.sub(r':$', '', description)
                
                if description and len(description) > 5:
                    conditions.append({
                        'type': 'custom',
                        'description': description,
                        'operator': 'custom',
                        'value': ''
                    })
        
        # 如果没有找到，返回默认条件
        if not conditions:
            conditions.append({
                'type': 'custom',
                'description': '根据策略逻辑触发卖出信号',
                'operator': 'custom',
                'value': ''
            })
        
        return conditions[:5]  # 最多返回5个条件
    
    def _extract_risk_controls(self, code: str) -> Dict[str, Any]:
        """提取风险控制参数"""
        risk_controls = {}
        
        # 查找止损止盈相关的参数
        patterns = {
            'stop_loss': r'stop_loss\s*=\s*([\d.]+)',
            'take_profit': r'take_profit\s*=\s*([\d.]+)',
            'max_position_size': r'(?:max_)?position_size\s*=\s*([\d.]+)',
            'max_drawdown': r'max_drawdown\s*=\s*([\d.]+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                try:
                    risk_controls[key] = float(match.group(1))
                except:
                    pass
        
        # 设置默认值
        if not risk_controls.get('stop_loss'):
            risk_controls['stop_loss'] = 5.0
        if not risk_controls.get('take_profit'):
            risk_controls['take_profit'] = 10.0
        if not risk_controls.get('max_position_size'):
            risk_controls['max_position_size'] = 0.3
        
        return risk_controls


# 创建全局实例
code_parser = StrategyCodeParser()
