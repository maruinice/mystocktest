# 交易条件显示增强

## 更新内容

将买入/卖出条件从简单的文本输入框升级为详细的条件卡片，清晰展示买卖信号的触发条件。

## 新功能特性

### 1. 条件卡片展示

每个交易条件现在以卡片形式展示，包含：

#### **条件类型标签**
- 🔵 **技术指标** (indicator) - 蓝色标签
- 🟢 **价格条件** (price) - 绿色标签
- 🟡 **成交量** (volume) - 黄色标签
- ⚪ **自定义** (custom) - 灰色标签
- 🔴 **风险控制** (risk) - 红色标签

#### **详细信息展示**
- **指标名称**: 如 MA、RSI、MACD 等
- **运算符**: 大于、小于、上穿、下穿等
- **阈值**: 触发条件的具体数值
- **参数**: 指标的详细参数（如周期、快慢线等）
- **描述**: 条件的文字说明

### 2. 运算符中文化

| 英文运算符 | 中文显示 |
|-----------|---------|
| greater_than | 大于 > |
| less_than | 小于 < |
| equal | 等于 = |
| cross_above | 上穿 ↗ |
| cross_below | 下穿 ↘ |
| trigger | 触发 |

### 3. 视觉效果

- **悬停效果**: 鼠标悬停时卡片边框变为紫色，添加阴影
- **分层布局**: 条件信息分层展示，层次清晰
- **图标提示**: 使用图标增强可读性
- **颜色编码**: 不同类型的条件使用不同颜色标识

## 示例展示

### 趋势跟踪策略 - 买入条件

```
┌─────────────────────────────────────┐
│ 🔵 技术指标                    ❌   │
├─────────────────────────────────────┤
│ 指标: MA                            │
│ 运算符: 上穿 ↗                      │
│ 参数: short_period: 5               │
│      long_period: 20                │
│ ℹ️ 短期均线上穿长期均线              │
└─────────────────────────────────────┘
```

### 均值回归策略 - 买入条件

```
┌─────────────────────────────────────┐
│ 🔵 技术指标                    ❌   │
├─────────────────────────────────────┤
│ 指标: RSI                           │
│ 运算符: 小于 <                      │
│ 阈值: 30                            │
│ 参数: period: 14                    │
│ ℹ️ RSI低于30（超卖）                │
└─────────────────────────────────────┘
```

### 动量策略 - 买入条件

```
┌─────────────────────────────────────┐
│ 🔵 技术指标                    ❌   │
├─────────────────────────────────────┤
│ 指标: MACD                          │
│ 运算符: 上穿 ↗                      │
│ 参数: fast_period: 12               │
│      slow_period: 26                │
│      signal_period: 9               │
│ ℹ️ MACD上穿信号线                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🟡 成交量                      ❌   │
├─────────────────────────────────────┤
│ 运算符: 大于 >                      │
│ 阈值: 1.5                           │
│ ℹ️ 成交量放大                       │
└─────────────────────────────────────┘
```

## 代码实现

### 模板部分

```vue
<div class="condition-card">
  <template v-if="typeof condition === 'object'">
    <div class="condition-content">
      <!-- 条件类型标签和删除按钮 -->
      <div class="condition-header">
        <el-tag :type="getConditionTypeColor(condition.type)" size="small">
          {{ getConditionTypeLabel(condition.type) }}
        </el-tag>
        <el-button @click="removeCondition(index)" size="small" text type="danger" circle>
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
      
      <!-- 条件详细信息 -->
      <div class="condition-details">
        <!-- 指标 -->
        <div class="condition-row" v-if="condition.indicator">
          <span class="label">指标:</span>
          <el-tag size="small">{{ condition.indicator }}</el-tag>
        </div>
        
        <!-- 运算符 -->
        <div class="condition-row" v-if="condition.operator">
          <span class="label">运算符:</span>
          <el-tag type="info" size="small">{{ getOperatorLabel(condition.operator) }}</el-tag>
        </div>
        
        <!-- 阈值 -->
        <div class="condition-row" v-if="condition.value !== undefined">
          <span class="label">阈值:</span>
          <el-tag type="warning" size="small">{{ condition.value }}</el-tag>
        </div>
        
        <!-- 参数列表 -->
        <div class="condition-row" v-if="condition.params">
          <span class="label">参数:</span>
          <div class="params-list">
            <el-tag v-for="(value, key) in condition.params" :key="key" size="small">
              {{ key }}: {{ value }}
            </el-tag>
          </div>
        </div>
        
        <!-- 描述 -->
        <div class="condition-description">
          <el-icon><InfoFilled /></el-icon>
          {{ condition.description }}
        </div>
      </div>
    </div>
  </template>
</div>
```

### 辅助函数

```typescript
// 条件类型标签
const getConditionTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    'indicator': '技术指标',
    'price': '价格条件',
    'volume': '成交量',
    'custom': '自定义',
    'risk': '风险控制'
  }
  return labels[type] || type
}

// 条件类型颜色
const getConditionTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    'indicator': 'primary',
    'price': 'success',
    'volume': 'warning',
    'custom': 'info',
    'risk': 'danger'
  }
  return colors[type] || 'info'
}

// 运算符标签
const getOperatorLabel = (operator: string) => {
  const labels: Record<string, string> = {
    'greater_than': '大于 >',
    'less_than': '小于 <',
    'equal': '等于 =',
    'cross_above': '上穿 ↗',
    'cross_below': '下穿 ↘',
    'trigger': '触发'
  }
  return labels[operator] || operator
}
```

### 样式

```scss
.condition-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #667eea;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
  }
}

.condition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.condition-details {
  .condition-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    
    .label {
      font-size: 12px;
      color: #6b7280;
      min-width: 50px;
      font-weight: 500;
    }
  }
  
  .condition-description {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 12px;
    padding: 8px 12px;
    background: #fff;
    border-radius: 6px;
    font-size: 13px;
    color: #374151;
    border-left: 3px solid #667eea;
  }
}
```

## 数据结构

### 后端返回的条件格式

```typescript
interface TradingCondition {
  type: 'indicator' | 'price' | 'volume' | 'custom' | 'risk'
  description: string
  operator?: 'greater_than' | 'less_than' | 'equal' | 'cross_above' | 'cross_below' | 'trigger'
  indicator?: string        // 指标名称，如 'MA', 'RSI', 'MACD'
  value?: string | number   // 阈值
  params?: Record<string, any>  // 指标参数
}
```

### 示例数据

```json
{
  "buy_conditions": [
    {
      "type": "indicator",
      "indicator": "MA",
      "operator": "cross_above",
      "params": {
        "short_period": 5,
        "long_period": 20
      },
      "description": "短期均线上穿长期均线"
    },
    {
      "type": "volume",
      "operator": "greater_than",
      "value": 1.5,
      "description": "成交量放大确认"
    }
  ],
  "sell_conditions": [
    {
      "type": "indicator",
      "indicator": "MA",
      "operator": "cross_below",
      "params": {
        "short_period": 5,
        "long_period": 20
      },
      "description": "短期均线下穿长期均线"
    },
    {
      "type": "risk",
      "operator": "trigger",
      "description": "止损或止盈触发"
    }
  ]
}
```

## 优势对比

### 修改前
```
买入条件:
┌──────────────────────────┐
│ [Object Object]          │
└──────────────────────────┘
```
❌ 无法看到具体条件
❌ 无法理解买卖信号
❌ 用户体验差

### 修改后
```
买入条件:
┌─────────────────────────────────────┐
│ 🔵 技术指标                    ❌   │
├─────────────────────────────────────┤
│ 指标: MA                            │
│ 运算符: 上穿 ↗                      │
│ 参数: short_period: 5               │
│      long_period: 20                │
│ ℹ️ 短期均线上穿长期均线              │
└─────────────────────────────────────┘
```
✅ 清晰展示所有条件信息
✅ 用户能理解买卖信号逻辑
✅ 专业的视觉呈现
✅ 易于理解和验证

## 兼容性

代码保持向后兼容，支持两种格式：

1. **对象格式**（推荐）：显示详细的条件卡片
2. **字符串格式**（旧版本）：显示简单的文本条件

## 使用场景

### 1. AI策略生成器
用户通过AI生成策略后，可以清楚看到：
- 买入信号的触发条件
- 卖出信号的触发条件
- 每个条件使用的指标和参数
- 条件的逻辑关系

### 2. 策略审查
在保存策略前，用户可以：
- 验证条件的正确性
- 检查参数是否合理
- 理解策略的交易逻辑

### 3. 策略学习
新手用户可以：
- 学习不同策略的条件设置
- 理解技术指标的应用
- 掌握交易信号的判断

## 后续优化

### 1. 条件编辑功能
添加内联编辑功能，允许用户直接修改：
- 指标类型
- 运算符
- 阈值
- 参数

### 2. 条件验证
添加实时验证：
- 参数范围检查
- 逻辑一致性验证
- 智能提示和建议

### 3. 可视化预览
添加图表预览：
- 在K线图上标注买卖点
- 显示指标曲线
- 模拟历史信号

### 4. 条件模板
提供常用条件模板：
- 金叉死叉
- 超买超卖
- 趋势突破
- 量价配合

## 总结

本次更新将交易条件从简单的文本显示升级为专业的卡片展示，极大提升了用户体验：

✅ **信息完整**: 展示所有条件细节
✅ **易于理解**: 中文化、图标化、颜色编码
✅ **专业美观**: 现代化的UI设计
✅ **向后兼容**: 支持旧数据格式

用户现在可以清楚地看到每个买卖信号的触发条件，包括使用的指标、运算符、阈值和参数，真正理解策略的交易逻辑！
