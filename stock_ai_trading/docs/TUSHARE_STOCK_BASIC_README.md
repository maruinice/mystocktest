# Tushare股票基础信息集成

本文档介绍如何使用Tushare API获取股票基础信息并导入到数据库中。

## 📋 概述

基于Tushare的`stock_basic`接口<mcreference link="https://tushare.pro/document/2?doc_id=25" index="0">0</mcreference>，实现了股票基础信息的自动获取和存储功能。

### 主要功能
- 🔄 调用Tushare stock_basic接口获取股票基础信息
- 🗄️ 创建标准化的股票基础信息数据表
- 📊 支持批量数据导入和更新
- 🔍 提供数据统计和查询视图

## 🏗️ 数据库表结构

### 主表：stock_basic

```sql
CREATE TABLE stock_basic (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL UNIQUE COMMENT 'TS代码（如000001.SZ）',
    symbol VARCHAR(10) NOT NULL COMMENT '股票代码（如000001）',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    area VARCHAR(50) COMMENT '地域',
    industry VARCHAR(100) COMMENT '所属行业',
    fullname VARCHAR(200) COMMENT '股票全称',
    enname VARCHAR(200) COMMENT '英文全称',
    cnspell VARCHAR(50) COMMENT '拼音缩写',
    market VARCHAR(50) COMMENT '市场类型（主板/创业板/科创板/CDR/北交所）',
    exchange VARCHAR(10) COMMENT '交易所代码（SSE/SZSE/BSE）',
    curr_type VARCHAR(10) COMMENT '交易货币',
    list_status VARCHAR(10) COMMENT '上市状态（L上市/D退市/P暂停上市）',
    list_date DATE COMMENT '上市日期',
    delist_date DATE COMMENT '退市日期',
    is_hs VARCHAR(10) COMMENT '是否沪深港通标的（N否/H沪股通/S深股通）',
    act_name VARCHAR(200) COMMENT '实控人名称',
    act_ent_type VARCHAR(100) COMMENT '实控人企业性质',
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    data_source VARCHAR(50) DEFAULT 'tushare',
    sync_status VARCHAR(20) DEFAULT 'active'
);
```

### 视图：v_stock_basicctive

仅显示正常上市的股票：
```sql
CREATE VIEW v_stock_basicctive AS
SELECT ts_code, symbol, name, area, industry, market, exchange, list_date, is_hs
FROM stock_basic 
WHERE list_status = 'L' AND sync_status = 'active';
```

### 视图：v_stock_industry_stats

按行业统计：
```sql
CREATE VIEW v_stock_industry_stats AS
SELECT 
    industry,
    COUNT(*) as stock_count,
    COUNT(CASE WHEN is_hs IN ('H', 'S') THEN 1 END) as hs_count
FROM stock_basic 
WHERE list_status = 'L' AND sync_status = 'active'
GROUP BY industry;
```

## 🚀 快速开始

### 1. 环境准备

#### 安装依赖
```bash
pip install tushare pandas python-dotenv sqlalchemy pymysql
```

#### 配置环境变量
在`.env`文件中设置：
```env
# Tushare配置
TUSHARE_TOKEN=your_tushare_token_here

# 数据库配置
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/database_name
```

### 2. 创建数据库表

```bash
# 执行建表SQL
mysql -u username -p database_name < sql/create_stock_basic_table.sql
```

### 3. 测试API连接

```bash
# 测试Tushare API连接
python test_tushare_simple.py
```

### 4. 导入股票数据

```bash
# 完整数据导入
python scripts/import_stock_basic.py
```

## 📊 API接口说明

### Tushare stock_basic接口

**接口名称**: `stock_basic`  
**接口说明**: 获取基础信息数据，包括股票代码、名称、上市日期、退市日期等  
**权限要求**: 2000积分起  
**文档地址**: https://tushare.pro/document/2?doc_id=25

#### 主要参数
| 参数 | 类型 | 必选 | 描述 |
|------|------|------|------|
| ts_code | str | N | TS股票代码 |
| name | str | N | 名称 |
| exchange | str | N | 交易所（SSE上交所/SZSE深交所/BSE北交所） |
| market | str | N | 市场类别（主板/创业板/科创板/CDR/北交所） |
| list_status | str | N | 上市状态（L上市/D退市/P暂停上市，默认L） |
| is_hs | str | N | 是否沪深港通标的（N否/H沪股通/S深股通） |

#### 主要字段
| 字段 | 类型 | 描述 |
|------|------|------|
| ts_code | str | TS代码 |
| symbol | str | 股票代码 |
| name | str | 股票名称 |
| area | str | 地域 |
| industry | str | 所属行业 |
| market | str | 市场类型 |
| exchange | str | 交易所代码 |
| list_date | str | 上市日期 |
| is_hs | str | 是否沪深港通标的 |

## 📁 文件结构

```
stock_ai_trading/
├── sql/
│   └── create_stock_basic_table.sql          # 建表SQL脚本
├── scripts/
│   └── import_stock_basic.py                 # 数据导入脚本
├── app/services/
│   └── tushare_service.py                    # Tushare API服务
├── test_tushare_simple.py                    # API测试脚本
└── docs/
    └── TUSHARE_STOCK_BASIC_README.md         # 本文档
```

## 🔧 使用示例

### Python代码示例

```python
import tushare as ts
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化API
ts.set_token(os.getenv('TUSHARE_TOKEN'))
pro = ts.pro_api()

# 获取股票基础信息
df = pro.stock_basic(
    exchange='',        # 全部交易所
    list_status='L',    # 仅上市股票
    fields='ts_code,symbol,name,area,industry,market,exchange,list_date'
)

print(f"获取到 {len(df)} 条股票数据")
print(df.head())
```

### SQL查询示例

```sql
-- 查询所有上市股票
SELECT * FROM v_stock_basicctive LIMIT 10;

-- 按行业统计股票数量
SELECT * FROM v_stock_industry_stats ORDER BY stock_count DESC;

-- 查询科技行业的股票
SELECT ts_code, symbol, name, market, exchange 
FROM stock_basic 
WHERE industry LIKE '%科技%' AND list_status = 'L';

-- 查询沪深港通标的
SELECT ts_code, symbol, name, is_hs 
FROM stock_basic 
WHERE is_hs IN ('H', 'S') AND list_status = 'L';
```

## 📈 数据统计

运行测试脚本后的示例输出：

```
✅ 成功获取 10 条股票数据

📋 数据预览:
TS代码         股票代码     股票名称         地域       行业           市场
000001.SZ    000001   平安银行         深圳       银行           主板
000002.SZ    000002   万科A          深圳       全国地产         主板
000004.SZ    000004   *ST国华        深圳       软件服务         主板

📊 数据字段信息:
  - 总字段数: 8
  - 字段列表: ts_code, symbol, name, area, industry, market, exchange, list_date

📈 统计信息:
  - 市场分布: {'主板': 10}
  - 交易所分布: {'SZSE': 10}
```

## ⚠️ 注意事项

1. **API权限**: 需要Tushare账户并且积分≥2000
2. **调用频率**: 注意API调用频率限制，避免过于频繁的请求
3. **数据更新**: 建议定期更新股票基础信息，特别是新股上市时
4. **错误处理**: 脚本包含完整的错误处理和重试机制
5. **数据备份**: 导入前建议备份现有数据

## 🔍 故障排除

### 常见问题

1. **Token错误**
   ```
   错误: 未设置TUSHARE_TOKEN环境变量
   解决: 在.env文件中正确设置TUSHARE_TOKEN
   ```

2. **积分不足**
   ```
   错误: 权限不足或积分不够
   解决: 检查Tushare账户积分，stock_basic接口需要2000积分
   ```

3. **网络连接**
   ```
   错误: 连接超时
   解决: 检查网络连接，可能需要代理设置
   ```

4. **数据库连接**
   ```
   错误: 数据库连接失败
   解决: 检查DATABASE_URL配置和数据库服务状态
   ```

## 📞 技术支持

- Tushare官方文档: https://tushare.pro/document/2
- 项目GitHub: [项目地址]
- 技术交流群: [群号]

---

*最后更新: 2025-01-30*