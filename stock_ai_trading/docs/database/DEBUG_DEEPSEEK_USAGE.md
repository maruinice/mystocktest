# DeepSeek Token使用调试指南

## 📊 当前状态

根据截图显示：
- **余额：** ¥49.75（未变化）
- **本月消费：** ¥0.20
- **API调用次数：** 40次
- **Token使用：** 93,792 tokens

**问题：** 有API调用和Token使用，但消费金额没有增加

## 🔍 可能的原因

### 1. 免费额度
DeepSeek可能提供了免费额度：
- 新用户免费额度
- 每月免费Token配额
- 测试期免费使用

### 2. 计费延迟
API调用和计费可能有延迟：
- 实时显示Token使用
- 但费用可能延迟几小时或1天结算

### 3. 使用了缓存响应
DeepSeek可能缓存了相似的请求：
- 缓存的响应不计费
- 但仍然计入Token统计

### 4. 实际在调用模板生成
虽然有Token统计，但可能：
- 统计数据不准确
- 实际使用了模板生成
- 需要通过日志确认

## 🧪 调试步骤

### 步骤1：查看详细日志

已添加详细的调试日志，现在重启服务并测试：

```bash
# 停止当前服务（Ctrl+C）
python app/main_flask.py
```

### 步骤2：生成一个策略

1. 打开策略管理页面
2. 点击"AI策略生成"
3. 输入提示词：**"生成一个基于MACD的趋势跟踪策略"**
4. 点击"生成策略"

### 步骤3：查看控制台日志

日志会显示完整的调用过程，包括：

**API层日志：**
```
====================================================================================================
[AI策略生成API] 开始调用AI生成器...
[AI策略生成API] 原始提示词: 生成一个基于MACD的趋势跟踪策略
[AI策略生成API] 补全提示词长度: XXX
[AI策略生成API] 生成选项: {...}
```

**Gateway初始化日志：**
```
[AI策略生成] Gateway未初始化，开始初始化...
[AI策略生成] Gateway初始化完成，适配器数量: 1
[AI策略生成] 已注册的适配器: ['deepseek']
DeepSeek adapter registered as primary LLM
```

**DeepSeek API调用日志：**
```
================================================================================
[DeepSeek API] 开始调用
[DeepSeek API] URL: https://api.deepseek.com/v1/chat/completions
[DeepSeek API] Model: deepseek-chat
[DeepSeek API] API Key: sk-xxxxxxxx...xxxx
[DeepSeek API] Messages count: 2
[DeepSeek API] Message 1 (system): 你是一个专业的量化交易策略设计师...
[DeepSeek API] Message 2 (user): 生成一个基于MACD的趋势跟踪策略...
[DeepSeek API] Max tokens: 2000
[DeepSeek API] Temperature: 0.7
[DeepSeek API] Response status: 200
[DeepSeek API] Response time: 2.35秒
[DeepSeek API] Response model: deepseek-chat
[DeepSeek API] Token usage:
  - Prompt tokens: 1234
  - Completion tokens: 567
  - Total tokens: 1801
[DeepSeek API] Response content length: 2345
[DeepSeek API] Response content preview:
{
  "name": "MACD趋势跟踪策略",
  "description": "基于MACD指标的趋势跟踪策略...",
  ...
}
================================================================================
```

**AI生成器日志：**
```
[AI策略生成] LLM响应状态: success=True
[AI策略生成] LLM响应内容长度: 2345
[AI策略生成] LLM响应模型: deepseek-chat
[AI策略生成] LLM响应提供商: deepseek
[AI策略生成] LLM Token使用: {'prompt_tokens': 1234, 'completion_tokens': 567, 'total_tokens': 1801}
[AI策略生成] LLM响应时间: 2.35秒
[AI策略生成] LLM完整响应内容:
================================================================================
{完整的JSON响应}
================================================================================
[AI策略生成] 策略解析成功: MACD趋势跟踪策略
[AI策略生成] 策略类型: trend_following
[AI策略生成] 是否模板生成: False  ← 关键！应该是False
```

**API返回日志：**
```
[AI策略生成API] AI生成完成
[AI策略生成API] 策略名称: MACD趋势跟踪策略
[AI策略生成API] 策略类型: trend_following
[AI策略生成API] 是否模板生成: False  ← 关键！
[AI策略生成API] 策略描述: 基于MACD指标的趋势跟踪策略...
====================================================================================================
```

### 步骤4：分析日志

**✅ 成功调用DeepSeek的标志：**
1. `[DeepSeek API] 开始调用` - 确认调用了DeepSeek
2. `[DeepSeek API] Response status: 200` - API调用成功
3. `[DeepSeek API] Token usage:` - 显示Token使用情况
4. `[DeepSeek API] Response content preview:` - 显示AI生成的内容
5. `是否模板生成: False` - 不是模板生成

**❌ 使用模板生成的标志：**
1. 没有`[DeepSeek API]`相关日志
2. 直接跳到`[AI策略生成] 降级到模板生成`
3. `是否模板生成: True`

### 步骤5：检查DeepSeek余额

1. 访问 https://platform.deepseek.com/usage
2. 刷新页面
3. 查看"本月消费"是否增加
4. 查看"API调用次数"是否增加
5. 查看"Token使用"是否增加

## 📋 关键检查点

### 检查点1：API Key是否正确

在日志中查看：
```
[DeepSeek API] API Key: sk-xxxxxxxx...xxxx
```

确认：
- API Key以`sk-`开头
- 后4位与你的实际Key匹配

### 检查点2：是否真的调用了API

在日志中查看：
```
[DeepSeek API] Response status: 200
```

如果看到这行，说明确实调用了DeepSeek API。

### 检查点3：Token使用情况

在日志中查看：
```
[DeepSeek API] Token usage:
  - Prompt tokens: XXXX
  - Completion tokens: XXXX
  - Total tokens: XXXX
```

记录这些数字，然后在DeepSeek平台上对比。

### 检查点4：响应内容

在日志中查看：
```
[DeepSeek API] Response content preview:
{实际的AI生成内容}
```

如果内容是JSON格式的策略定义，说明是AI生成的。
如果内容是固定的模板，说明用了模板生成。

## 💡 可能的解释

### 解释1：DeepSeek有免费额度

DeepSeek可能提供：
- 新用户免费额度（如前100万tokens免费）
- 每月免费配额
- 测试期免费使用

**验证方法：**
- 查看DeepSeek官网的定价页面
- 查看账户设置中的免费额度信息
- 联系DeepSeek客服确认

### 解释2：计费延迟

API调用和计费可能有时间差：
- Token使用实时统计
- 费用可能延迟几小时或1天结算

**验证方法：**
- 等待24小时后再查看
- 查看历史账单

### 解释3：缓存机制

如果多次使用相同或相似的提示词：
- DeepSeek可能返回缓存的响应
- 缓存响应可能不计费或费用很低

**验证方法：**
- 使用完全不同的提示词测试
- 查看是否有缓存相关的响应头

## 🎯 下一步行动

### 立即执行：

1. **重启后端服务**
   ```bash
   python app/main_flask.py
   ```

2. **生成一个策略**
   - 使用新的、独特的提示词
   - 例如："生成一个基于布林带和成交量的突破策略"

3. **复制完整的控制台日志**
   - 从`[AI策略生成API] 开始调用AI生成器...`开始
   - 到`[AI策略生成API] AI生成完成`结束
   - 包括所有`[DeepSeek API]`日志

4. **检查DeepSeek平台**
   - 记录当前的Token使用数量
   - 记录当前的消费金额
   - 等待5分钟后刷新查看

5. **对比数据**
   - 日志中的Token使用 vs 平台显示的Token使用
   - 是否有新的API调用记录
   - 消费金额是否变化

### 预期结果：

**如果日志显示成功调用DeepSeek：**
- 应该看到完整的API调用日志
- 应该看到Token使用统计
- 应该看到AI生成的JSON内容
- `是否模板生成: False`

**如果余额仍然不变：**
- 可能是免费额度
- 可能是计费延迟
- 需要联系DeepSeek客服确认

## 📞 联系DeepSeek支持

如果确认调用成功但费用不变，可以：

1. **访问DeepSeek支持页面**
   - https://platform.deepseek.com/support

2. **提供以下信息：**
   - 账户ID
   - API Key（前10位和后4位）
   - 调用时间
   - Token使用数量
   - 完整的API请求和响应日志

3. **询问：**
   - 是否有免费额度？
   - 计费周期是多久？
   - 为什么有Token使用但费用不变？

---

**现在请：**
1. 重启后端服务
2. 生成一个策略
3. 复制完整的控制台日志给我
4. 我会帮你分析具体问题
