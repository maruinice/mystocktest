# 筛选条件改进待办清单

## 🚨 立即处理 (高优先级)

### 1. 前端条件清理
**文件**: `stock-ai-frontend/src/components/ConditionEditor.vue`

#### 需要删除的无效条件 (11个)
```javascript
// 在 indicators 对象中删除以下条件
const invalidConditions = [
  // 基本面 - 盈利能力
  'roe',           // 净资产收益率 - 后端未实现计算
  'roa',           // 总资产收益率 - 后端未实现计算  
  'gross_margin',  // 毛利率 - 后端未实现计算
  'net_margin',    // 净利率 - 后端未实现计算
  
  // 基本面 - 成长性
  'revenue_growth', // 营收增长率 - 后端未实现计算
  'profit_growth',  // 净利润增长率 - 后端未实现计算
  'eps_growth',     // EPS增长率 - 后端未实现计算
  
  // 基本面 - 估值
  'pb_mrq',        // 市净率MRQ - 应改为 'pb'
  
  // 基本面 - 财务健康
  'debt_ratio',    // 资产负债率 - 后端未实现计算
  'current_ratio', // 流动比率 - 后端未实现计算
  'quick_ratio'    // 速动比率 - 后端未实现计算
];
```

#### 需要修复的字段映射
```javascript
// 修改字段名称
{
  code: 'pb_mrq',  // 改为 'pb'
  name: '市净率MRQ', // 改为 '市净率'
  unit: '倍',
  range: [0, 20]
}
```

### 2. 后端数据获取完善
**文件**: `app/services/stock_screening_service.py`

#### 添加财务数据获取逻辑
在 `_get_base_screening_data` 方法中添加：

```python
# 获取最新财务数据
cursor.execute(f"""
    SELECT 
        -- 盈利能力指标
        roe,                    -- 净资产收益率
        roa,                    -- 总资产收益率  
        gross_profit_margin,    -- 毛利率
        netprofit_margin,       -- 净利率
        
        -- 成长性指标
        or_yoy,                 -- 营收同比增长率
        profit_yoy,             -- 净利润同比增长率
        eps_yoy,                -- EPS同比增长率
        
        -- 财务健康指标
        debt_to_assets,         -- 资产负债率
        current_ratio,          -- 流动比率
        quick_ratio,            -- 速动比率
        
        end_date
    FROM income i
    LEFT JOIN balancesheet b ON i.ts_code = b.ts_code AND i.end_date = b.end_date
    WHERE i.ts_code = '{ts_code}'
    AND i.end_date >= '{one_year_ago}'
    ORDER BY i.end_date DESC
    LIMIT 1
""")
financial_data = cursor.fetchone()
```

### 3. 数据库字段验证
**执行命令**:
```bash
# 检查财务数据表的实际字段名
python -c "
import pymysql
conn = pymysql.connect(host='localhost', user='root', password='123456', database='stock_trading')
cursor = conn.cursor()
cursor.execute('DESCRIBE income')
print('Income表字段:', [row[0] for row in cursor.fetchall()])
cursor.execute('DESCRIBE balancesheet') 
print('Balancesheet表字段:', [row[0] for row in cursor.fetchall()])
"
```

## 🔧 短期优化 (中优先级)

### 1. 添加新的有效筛选条件
**文件**: `stock-ai-frontend/src/components/ConditionEditor.vue`

#### 基于后端已支持字段添加条件
```javascript
// 在相应分类中添加以下条件
const newConditions = {
  market: {
    basic: [
      {code: 'amount', name: '成交额', unit: '万元', range: [0, 1000000]},
      {code: 'volume', name: '成交量', unit: '手', range: [0, 1000000]},
      {code: 'circ_mv', name: '流通市值', unit: '万元', range: [0, 10000000]},
      {code: 'pb', name: '市净率', unit: '倍', range: [0, 20]},
      {code: 'ps', name: '市销率', unit: '倍', range: [0, 50]}
    ]
  },
  technical: {
    advanced: [
      {code: 'macd_dif', name: 'MACD-DIF', unit: '', range: [-10, 10]},
      {code: 'macd_dea', name: 'MACD-DEA', unit: '', range: [-10, 10]},
      {code: 'kdj_j', name: 'KDJ-J', unit: '', range: [0, 100]},
      {code: 'boll_upper', name: '布林上轨', unit: '元', range: [0, 1000]},
      {code: 'boll_lower', name: '布林下轨', unit: '元', range: [0, 1000]}
    ]
  }
};
```

### 2. 完善筛选策略配置
**文件**: `screening_strategies` 表

#### 添加更多预定义策略
```sql
-- 价值投资策略
INSERT INTO screening_strategies (
  strategy_name, strategy_code, strategy_type, description,
  conditions, sort_rules, is_system, is_active
) VALUES (
  '价值投资策略', 'value_investing', 'fundamental',
  '寻找低估值、高分红的价值股',
  '{"pe_ttm": {"min": 0, "max": 15}, "pb": {"min": 0, "max": 2}, "market_cap": {"min": 1000000}}',
  '{"pe_ttm": "asc", "pb": "asc"}',
  1, 1
);

-- 成长股策略  
INSERT INTO screening_strategies (
  strategy_name, strategy_code, strategy_type, description,
  conditions, sort_rules, is_system, is_active
) VALUES (
  '成长股策略', 'growth_stock', 'mixed',
  '寻找高成长、合理估值的成长股',
  '{"change_pct": {"min": 0}, "turnover_rate": {"min": 2}, "market_cap": {"min": 500000, "max": 5000000}}',
  '{"change_pct": "desc", "turnover_rate": "desc"}',
  1, 1
);
```

### 3. 优化筛选结果展示
**文件**: `stock-ai-frontend/src/views/Screening.vue`

#### 添加更多结果字段显示
```javascript
const resultColumns = [
  {key: 'symbol', title: '代码'},
  {key: 'name', title: '名称'},
  {key: 'industry', title: '行业'},
  {key: 'close_price', title: '收盘价'},
  {key: 'change_pct', title: '涨跌幅'},
  {key: 'pe', title: '市盈率'},
  {key: 'pb', title: '市净率'},
  {key: 'market_cap', title: '总市值'},
  {key: 'turnover_rate', title: '换手率'},
  {key: 'composite_score', title: '综合评分'}
];
```

## 🚀 长期规划 (低优先级)

### 1. 数据质量监控
**新建文件**: `app/services/data_quality_service.py`

#### 实现数据质量检查
```python
class DataQualityService:
    def check_financial_data_completeness(self):
        """检查财务数据完整性"""
        pass
    
    def validate_screening_conditions(self):
        """验证筛选条件有效性"""
        pass
    
    def monitor_data_freshness(self):
        """监控数据新鲜度"""
        pass
```

### 2. 智能筛选功能
**新建文件**: `app/services/intelligent_screening_service.py`

#### 实现机器学习筛选
```python
class IntelligentScreeningService:
    def train_screening_model(self):
        """训练筛选模型"""
        pass
    
    def predict_stock_potential(self):
        """预测股票潜力"""
        pass
    
    def recommend_conditions(self):
        """推荐筛选条件"""
        pass
```

## 📋 执行检查清单

### 第一阶段 (1-2天)
- [ ] 删除前端11个无效筛选条件
- [ ] 修复 `pb_mrq` -> `pb` 字段映射
- [ ] 验证数据库表字段名称
- [ ] 测试修改后的筛选功能

### 第二阶段 (3-5天)
- [ ] 实现财务指标计算逻辑
- [ ] 添加5-10个新的有效筛选条件
- [ ] 完善数据获取和处理流程
- [ ] 添加2-3个新的预定义策略

### 第三阶段 (1周)
- [ ] 优化筛选结果展示
- [ ] 完善错误处理和日志记录
- [ ] 编写单元测试和集成测试
- [ ] 更新用户文档和API文档

## 🔍 验证方法

### 功能验证
```bash
# 运行筛选条件有效性检查
python analyze_condition_effectiveness.py

# 测试筛选功能
python test_condition_flow.py
```

### 性能验证
```bash
# 检查筛选响应时间
curl -X POST http://localhost:5000/api/screening/execute \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": 1, "conditions": {"pe_ttm": {"max": 20}}}'
```

### 数据验证
```sql
-- 检查筛选结果数据质量
SELECT COUNT(*) as total_results,
       AVG(pe) as avg_pe,
       AVG(pb) as avg_pb,
       COUNT(DISTINCT industry) as industry_count
FROM screening_results sr
JOIN JSON_TABLE(sr.result_data, '$.results[*]' 
  COLUMNS (
    pe DECIMAL(10,2) PATH '$.pe',
    pb DECIMAL(10,2) PATH '$.pb', 
    industry VARCHAR(50) PATH '$.industry'
  )
) jt;
```

## 📞 需要支持的配置

### 环境变量
```bash
# .env 文件中添加
TUSHARE_TOKEN=your_tushare_token
DATABASE_URL=mysql://root:123456@localhost/stock_trading
REDIS_URL=redis://localhost:6379/0
```

### 数据库索引优化
```sql
-- 为筛选查询添加索引
CREATE INDEX idx_daily_basic_pe_pb ON daily_basic(pe, pb, trade_date);
CREATE INDEX idx_income_roe_roa ON income(roe, roa, end_date);
CREATE INDEX idx_stock_basic_industry ON stock_basic(industry, list_status);
```

## ⚠️ 注意事项

1. **数据一致性**: 确保财务数据的时间对齐
2. **性能影响**: 新增字段可能影响查询性能
3. **用户体验**: 分阶段发布，避免功能突然变化
4. **数据质量**: 加强数据验证和异常处理
5. **文档更新**: 及时更新API文档和用户手册

## 📈 成功指标

- 筛选条件有效率 > 90%
- 筛选响应时间 < 3秒
- 筛选结果准确率 > 95%
- 用户满意度评分 > 4.5/5
- 系统稳定性 > 99.9%