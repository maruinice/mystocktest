<template>
  <div class="backtest-result">
    <div class="result-header">
      <div class="header-info">
        <h2>{{ result.strategy_name }} - 回测结果</h2>
        <div class="result-meta">
          <span>回测期间: {{ formatDate(result.start_date) }} - {{ formatDate(result.end_date) }}</span>
          <span>初始资金: ¥{{ formatNumber(result.initial_capital) }}</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="exportResult" size="large">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
        <el-button @click="$emit('close')" size="large">
          关闭
        </el-button>
      </div>
    </div>

    <div class="result-content">
      <!-- 核心指标卡片 -->
      <div class="metrics-cards">
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="metric-card total-return">
              <div class="metric-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value" :class="result.total_return >= 0 ? 'positive' : 'negative'">
                  {{ result.total_return >= 0 ? '+' : '' }}{{ (result.total_return * 100).toFixed(2) }}%
                </div>
                <div class="metric-label">总收益率</div>
                <div class="metric-compare">
                  vs 基准: {{ result.alpha >= 0 ? '+' : '' }}{{ (result.alpha * 100).toFixed(2) }}%
                </div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="metric-card sharpe-ratio">
              <div class="metric-icon">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ result.sharpe_ratio.toFixed(2) }}</div>
                <div class="metric-label">夏普比率</div>
                <div class="metric-compare">
                  {{ getSharpeRating(result.sharpe_ratio) }}
                </div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="metric-card max-drawdown">
              <div class="metric-icon">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value negative">
                  -{{ (result.max_drawdown * 100).toFixed(2) }}%
                </div>
                <div class="metric-label">最大回撤</div>
                <div class="metric-compare">
                  {{ getDrawdownRating(result.max_drawdown) }}
                </div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="metric-card win-rate">
              <div class="metric-icon">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ (result.win_rate * 100).toFixed(1) }}%</div>
                <div class="metric-label">胜率</div>
                <div class="metric-compare">
                  {{ result.winning_trades }}/{{ result.total_trades }} 笔
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 详细指标表格 -->
      <div class="detailed-metrics">
        <el-row :gutter="24">
          <el-col :span="12">
            <div class="metrics-section">
              <h3>收益指标</h3>
              <el-table :data="profitMetrics" :show-header="false" size="small">
                <el-table-column prop="label" width="150" />
                <el-table-column prop="value" align="right">
                  <template #default="{ row }">
                    <span :class="row.class">{{ row.value }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-col>
          
          <el-col :span="12">
            <div class="metrics-section">
              <h3>风险指标</h3>
              <el-table :data="riskMetrics" :show-header="false" size="small">
                <el-table-column prop="label" width="150" />
                <el-table-column prop="value" align="right">
                  <template #default="{ row }">
                    <span :class="row.class">{{ row.value }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 图表区域 -->
      <div class="charts-section">
        <el-tabs v-model="activeChart" type="border-card">
          <el-tab-pane label="净值曲线" name="equity">
            <div class="chart-container">
              <div ref="equityChartRef" class="chart"></div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="回撤分析" name="drawdown">
            <div class="chart-container">
              <div ref="drawdownChartRef" class="chart"></div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="收益分布" name="returns">
            <div class="chart-container">
              <div ref="returnsChartRef" class="chart"></div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="月度收益" name="monthly">
            <div class="chart-container">
              <div ref="monthlyChartRef" class="chart"></div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 资产与统计 -->
      <div class="extra-section">
        <el-tabs type="border-card">
          <el-tab-pane label="资产变化" name="assets">
            <el-table :data="props.result.daily_assets || []" size="small">
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column prop="cash" label="现金" width="140" align="right">
                <template #default="{ row }">¥{{ formatNumber(row.cash) }}</template>
              </el-table-column>
              <el-table-column prop="market_value" label="持仓市值" width="160" align="right">
                <template #default="{ row }">¥{{ formatNumber(row.market_value) }}</template>
              </el-table-column>
              <el-table-column prop="total_value" label="总资产" width="160" align="right">
                <template #default="{ row }">¥{{ formatNumber(row.total_value) }}</template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="交易统计" name="stats">
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-label">买入次数</div>
                <div class="stat-value">{{ props.result.trade_stats?.buy_count || 0 }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">卖出次数</div>
                <div class="stat-value">{{ props.result.trade_stats?.sell_count || 0 }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">买入金额</div>
                <div class="stat-value">¥{{ formatNumber(props.result.trade_stats?.buy_amount || 0) }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">卖出金额</div>
                <div class="stat-value">¥{{ formatNumber(props.result.trade_stats?.sell_amount || 0) }}</div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 交易记录 -->
      <div class="trades-section">
        <div class="section-header">
          <h3>交易记录</h3>
          <div class="header-actions">
            <el-input
              v-model="tradeSearch"
              placeholder="搜索股票代码..."
              style="width: 200px;"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button @click="exportTrades">
              <el-icon><Download /></el-icon>
              导出交易
            </el-button>
          </div>
        </div>
        
        <el-table :data="filteredTrades" v-loading="false" size="small">
          <el-table-column prop="date" label="日期" width="100" />
          <el-table-column prop="code" label="股票代码" width="100" />
          <el-table-column prop="name" label="股票名称" width="120" />
          <el-table-column prop="side" label="方向" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">
                {{ row.side === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="100" align="right" />
          <el-table-column prop="price" label="价格" width="100" align="right">
            <template #default="{ row }">
              ¥{{ row.price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ formatNumber(row.amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="commission" label="手续费" width="100" align="right">
            <template #default="{ row }">
              ¥{{ row.commission.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="profit_loss" label="盈亏" width="120" align="right">
            <template #default="{ row }">
              <span v-if="row.profit_loss !== 0" :class="row.profit_loss > 0 ? 'positive' : 'negative'">
                {{ row.profit_loss > 0 ? '+' : '' }}¥{{ Math.abs(row.profit_loss).toFixed(2) }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="trades-pagination">
          <el-pagination
            v-model:current-page="tradePage"
            v-model:page-size="tradePageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="result.trades?.length || 0"
            layout="total, sizes, prev, pager, next, jumper"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { BacktestResult as BacktestResultType } from '@/types/strategy'

// Props
interface Props {
  result: BacktestResultType
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
}>()

// 响应式数据
const activeChart = ref('equity')
const tradeSearch = ref('')
const tradePage = ref(1)
const tradePageSize = ref(20)

// 图表引用
const equityChartRef = ref<HTMLElement>()
const drawdownChartRef = ref<HTMLElement>()
const returnsChartRef = ref<HTMLElement>()
const monthlyChartRef = ref<HTMLElement>()
import * as echarts from 'echarts'
let equityChart: echarts.ECharts | null = null
let drawdownChart: echarts.ECharts | null = null

// 计算属性
const profitMetrics = computed(() => [
  { label: '总收益率', value: `${(props.result.total_return * 100).toFixed(2)}%`, class: props.result.total_return >= 0 ? 'positive' : 'negative' },
  { label: '年化收益率', value: `${(props.result.annualized_return * 100).toFixed(2)}%`, class: props.result.annualized_return >= 0 ? 'positive' : 'negative' },
  { label: '基准收益率', value: `${(props.result.benchmark_return * 100).toFixed(2)}%`, class: props.result.benchmark_return >= 0 ? 'positive' : 'negative' },
  { label: 'Alpha', value: `${(props.result.alpha * 100).toFixed(2)}%`, class: props.result.alpha >= 0 ? 'positive' : 'negative' },
  { label: 'Beta', value: props.result.beta.toFixed(2), class: '' },
  { label: '最终资金', value: `¥${formatNumber(props.result.final_capital)}`, class: 'positive' },
  { label: '盈利因子', value: props.result.profit_factor.toFixed(2), class: props.result.profit_factor > 1 ? 'positive' : 'negative' }
])

const riskMetrics = computed(() => [
  { label: '夏普比率', value: props.result.sharpe_ratio.toFixed(2), class: props.result.sharpe_ratio > 1 ? 'positive' : '' },
  { label: 'Sortino比率', value: props.result.sortino_ratio.toFixed(2), class: props.result.sortino_ratio > 1 ? 'positive' : '' },
  { label: '最大回撤', value: `${(props.result.max_drawdown * 100).toFixed(2)}%`, class: 'negative' },
  { label: '波动率', value: `${(props.result.volatility * 100).toFixed(2)}%`, class: '' },
  { label: '胜率', value: `${(props.result.win_rate * 100).toFixed(1)}%`, class: props.result.win_rate > 0.5 ? 'positive' : '' },
  { label: '总交易次数', value: props.result.total_trades.toString(), class: '' },
  { label: '平均盈利', value: `${(props.result.avg_win * 100).toFixed(2)}%`, class: 'positive' },
  { label: '平均亏损', value: `${(props.result.avg_loss * 100).toFixed(2)}%`, class: 'negative' }
])

const filteredTrades = computed(() => {
  if (!props.result.trades) return []
  
  let trades = props.result.trades
  
  if (tradeSearch.value) {
    trades = trades.filter(trade => 
      trade.code.toLowerCase().includes(tradeSearch.value.toLowerCase()) ||
      trade.name.toLowerCase().includes(tradeSearch.value.toLowerCase())
    )
  }
  
  const start = (tradePage.value - 1) * tradePageSize.value
  const end = start + tradePageSize.value
  
  return trades.slice(start, end)
})

// 方法
const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const getSharpeRating = (sharpe: number): string => {
  if (sharpe > 2) return '优秀'
  if (sharpe > 1) return '良好'
  if (sharpe > 0.5) return '一般'
  return '较差'
}

const getDrawdownRating = (drawdown: number): string => {
  if (drawdown < 0.05) return '优秀'
  if (drawdown < 0.1) return '良好'
  if (drawdown < 0.2) return '一般'
  return '较差'
}

const exportResult = () => {
  // 导出回测报告
  const reportData = {
    strategy_name: props.result.strategy_name,
    backtest_period: `${formatDate(props.result.start_date)} - ${formatDate(props.result.end_date)}`,
    metrics: {
      total_return: props.result.total_return,
      annualized_return: props.result.annualized_return,
      sharpe_ratio: props.result.sharpe_ratio,
      max_drawdown: props.result.max_drawdown,
      win_rate: props.result.win_rate
    },
    trades: props.result.trades
  }
  
  const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.result.strategy_name}_回测报告_${Date.now()}.json`
  link.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('回测报告导出成功')
}

const exportTrades = () => {
  if (!props.result.trades || props.result.trades.length === 0) {
    ElMessage.warning('没有交易记录可导出')
    return
  }
  
  // 转换为CSV格式
  const headers = ['日期', '股票代码', '股票名称', '方向', '数量', '价格', '金额', '手续费', '盈亏']
  const csvContent = [
    headers.join(','),
    ...props.result.trades.map(trade => [
      trade.date,
      trade.code,
      trade.name,
      trade.side === 'buy' ? '买入' : '卖出',
      trade.quantity,
      trade.price,
      trade.amount,
      trade.commission,
      trade.profit_loss
    ].join(','))
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.result.strategy_name}_交易记录_${Date.now()}.csv`
  link.click()
  ElMessage.success('交易记录导出成功')
}

const initCharts = async () => {
  await nextTick()
  
  // 净值曲线
  if (equityChartRef.value) {
    equityChart = echarts.init(equityChartRef.value)
    const dates = (props.result.equity_curve || []).map(d => d.date)
    const values = (props.result.equity_curve || []).map(d => d.value)
    equityChart.setOption({
      title: { text: '净值曲线', left: 'center' },
      tooltip: { 
        trigger: 'axis',
        formatter: (params: any) => {
          const data = params[0]
          return `${data.name}<br/>净值: ${formatNumber(data.value)}`
        }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { 
        type: 'category', 
        data: dates,
        axisLabel: { rotate: 45 }
      },
      yAxis: { 
        type: 'value',
        axisLabel: { formatter: (val: number) => formatNumber(val) }
      },
      series: [{ 
        type: 'line', 
        data: values, 
        smooth: true, 
        name: '净值',
        lineStyle: { width: 2, color: '#667eea' },
        areaStyle: { 
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
              { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
            ]
          }
        }
      }]
    })
  }
  
  // 回撤分析
  if (drawdownChartRef.value) {
    drawdownChart = echarts.init(drawdownChartRef.value)
    const curve = props.result.equity_curve || []
    let peak = curve.length ? curve[0].value : 0
    const drawdowns = curve.map(p => {
      if (p.value > peak) peak = p.value
      return peak > 0 ? ((peak - p.value) / peak * 100) : 0
    })
    drawdownChart.setOption({
      title: { text: '回撤分析', left: 'center' },
      tooltip: { 
        trigger: 'axis',
        formatter: (params: any) => {
          const data = params[0]
          return `${data.name}<br/>回撤: ${data.value.toFixed(2)}%`
        }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { 
        type: 'category', 
        data: curve.map(d => d.date),
        axisLabel: { rotate: 45 }
      },
      yAxis: { 
        type: 'value',
        axisLabel: { formatter: '{value}%' }
      },
      series: [{ 
        type: 'line', 
        data: drawdowns, 
        name: '回撤',
        lineStyle: { width: 2, color: '#ef4444' },
        areaStyle: { color: 'rgba(239, 68, 68, 0.2)' }
      }]
    })
  }
  
  // 收益分布（直方图）
  if (returnsChartRef.value) {
    const chart = echarts.init(returnsChartRef.value)
    const dist = props.result.returns_distribution || []
    chart.setOption({
      title: { text: '收益分布', left: 'center' },
      tooltip: { 
        trigger: 'axis',
        formatter: (params: any) => {
          const data = params[0]
          return `${data.name}<br/>频数: ${data.value}`
        }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { 
        type: 'category', 
        data: dist.map(d => `${(d.bin_start*100).toFixed(1)}%`),
        axisLabel: { rotate: 45, fontSize: 10 }
      },
      yAxis: { 
        type: 'value',
        name: '频数'
      },
      series: [{ 
        type: 'bar', 
        data: dist.map(d => d.count), 
        name: '频数',
        itemStyle: {
          color: (params: any) => {
            const binStart = dist[params.dataIndex].bin_start
            return binStart >= 0 ? '#10b981' : '#ef4444'
          }
        }
      }]
    })
  }
  
  // 月度收益
  if (monthlyChartRef.value) {
    const chart = echarts.init(monthlyChartRef.value)
    const mr = props.result.monthly_returns || []
    chart.setOption({
      title: { text: '月度收益', left: 'center' },
      tooltip: { 
        trigger: 'axis',
        formatter: (params: any) => {
          const data = params[0]
          return `${data.name}<br/>收益率: ${data.value}%`
        }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { 
        type: 'category', 
        data: mr.map(d => d.month),
        axisLabel: { rotate: 45 }
      },
      yAxis: { 
        type: 'value',
        axisLabel: { formatter: '{value}%' }
      },
      series: [{ 
        type: 'bar', 
        data: mr.map(d => (d.return*100).toFixed(2)), 
        name: '月收益率',
        itemStyle: {
          color: (params: any) => {
            return params.value >= 0 ? '#10b981' : '#ef4444'
          }
        }
      }]
    })
  }
}

// 监听tab切换
watch(activeChart, async (newVal) => {
  await nextTick()
  // 根据当前tab重新渲染对应图表
  if (newVal === 'equity' && equityChartRef.value) {
    if (!equityChart) {
      equityChart = echarts.init(equityChartRef.value)
    }
    equityChart.resize()
  } else if (newVal === 'drawdown' && drawdownChartRef.value) {
    if (!drawdownChart) {
      drawdownChart = echarts.init(drawdownChartRef.value)
      const curve = props.result.equity_curve || []
      let peak = curve.length ? curve[0].value : 0
      const drawdowns = curve.map(p => {
        if (p.value > peak) peak = p.value
        return peak > 0 ? ((peak - p.value) / peak * 100) : 0
      })
      drawdownChart.setOption({
        title: { text: '回撤分析', left: 'center' },
        tooltip: { 
          trigger: 'axis',
          formatter: (params: any) => {
            const data = params[0]
            return `${data.name}<br/>回撤: ${data.value.toFixed(2)}%`
          }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { 
          type: 'category', 
          data: curve.map(d => d.date),
          axisLabel: { rotate: 45 }
        },
        yAxis: { 
          type: 'value',
          axisLabel: { formatter: '{value}%' }
        },
        series: [{ 
          type: 'line', 
          data: drawdowns, 
          name: '回撤',
          lineStyle: { width: 2, color: '#ef4444' },
          areaStyle: { color: 'rgba(239, 68, 68, 0.2)' }
        }]
      })
    }
    drawdownChart.resize()
  } else if (newVal === 'returns' && returnsChartRef.value) {
    const chart = echarts.getInstanceByDom(returnsChartRef.value) || echarts.init(returnsChartRef.value)
    const dist = props.result.returns_distribution || []
    if (dist.length > 0) {
      chart.setOption({
        title: { text: '收益分布', left: 'center' },
        tooltip: { 
          trigger: 'axis',
          formatter: (params: any) => {
            const data = params[0]
            return `${data.name}<br/>频数: ${data.value}`
          }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { 
          type: 'category', 
          data: dist.map(d => `${(d.bin_start*100).toFixed(1)}%`),
          axisLabel: { rotate: 45, fontSize: 10 }
        },
        yAxis: { 
          type: 'value',
          name: '频数'
        },
        series: [{ 
          type: 'bar', 
          data: dist.map(d => d.count), 
          name: '频数',
          itemStyle: {
            color: (params: any) => {
              const binStart = dist[params.dataIndex].bin_start
              return binStart >= 0 ? '#10b981' : '#ef4444'
            }
          }
        }]
      })
    }
    chart.resize()
  } else if (newVal === 'monthly' && monthlyChartRef.value) {
    const chart = echarts.getInstanceByDom(monthlyChartRef.value) || echarts.init(monthlyChartRef.value)
    const mr = props.result.monthly_returns || []
    if (mr.length > 0) {
      chart.setOption({
        title: { text: '月度收益', left: 'center' },
        tooltip: { 
          trigger: 'axis',
          formatter: (params: any) => {
            const data = params[0]
            return `${data.name}<br/>收益率: ${data.value}%`
          }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { 
          type: 'category', 
          data: mr.map(d => d.month),
          axisLabel: { rotate: 45 }
        },
        yAxis: { 
          type: 'value',
          axisLabel: { formatter: '{value}%' }
        },
        series: [{ 
          type: 'bar', 
          data: mr.map(d => (d.return*100).toFixed(2)), 
          name: '月收益率',
          itemStyle: {
            color: (params: any) => {
              return params.value >= 0 ? '#10b981' : '#ef4444'
            }
          }
        }]
      })
    }
    chart.resize()
  }
})

// 生命周期
onMounted(() => {
  initCharts()
})
</script>

<style lang="scss" scoped>
.backtest-result {
  height: 100%;
  display: flex;
  flex-direction: column;
}

// 结果头部
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  
  .header-info {
    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 600;
    }
    
    .result-meta {
      display: flex;
      gap: 24px;
      font-size: 14px;
      opacity: 0.9;
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

// 结果内容
.result-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: #f8fafc;
}

// 指标卡片
.metrics-cards {
  margin-bottom: 24px;
  
  .metric-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    display: flex;
    align-items: center;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    .metric-icon {
      width: 60px;
      height: 60px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 20px;
      
      .el-icon {
        font-size: 28px;
        color: white;
      }
    }
    
    .metric-content {
      flex: 1;
      
      .metric-value {
        font-size: 28px;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 4px;
        font-family: 'Courier New', monospace;
        
        &.positive { color: #10b981; }
        &.negative { color: #ef4444; }
      }
      
      .metric-label {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 4px;
      }
      
      .metric-compare {
        font-size: 12px;
        color: #9ca3af;
      }
    }
    
    &.total-return .metric-icon {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    
    &.sharpe-ratio .metric-icon {
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    }
    
    &.max-drawdown .metric-icon {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    
    &.win-rate .metric-icon {
      background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    }
  }
}

// 详细指标
.detailed-metrics {
  margin-bottom: 24px;
  
  .metrics-section {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    
    h3 {
      margin: 0 0 16px 0;
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
    }
    
    .el-table {
      .positive { color: #10b981; font-weight: 600; }
      .negative { color: #ef4444; font-weight: 600; }
    }
  }
}

// 资产与统计
.extra-section {
  margin: 24px 0;
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    margin-top: 12px;
  }
  .stat-card {
    background: white;
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.08);
    .stat-label { color: #6b7280; font-size: 12px; }
    .stat-value { font-size: 18px; font-weight: 600; color: #1f2937; }
  }
}

// 图表区域
.charts-section {
  margin-bottom: 24px;
  
  .el-tabs {
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    
    .chart-container {
      padding: 20px;
      
      .chart {
        height: 400px;
        
        .chart-placeholder {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f3f4f6;
          border-radius: 8px;
          color: #6b7280;
          font-size: 16px;
        }
      }
    }
  }
}

// 交易记录
.trades-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }
  
  .el-table {
    .positive { color: #10b981; font-weight: 600; }
    .negative { color: #ef4444; font-weight: 600; }
  }
  
  .trades-pagination {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .metrics-cards {
    .el-col {
      margin-bottom: 16px;
    }
  }
}

@media (max-width: 768px) {
  .result-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
    
    .result-meta {
      flex-direction: column;
      gap: 8px;
    }
  }
  
  .result-content {
    padding: 16px;
  }
  
  .detailed-metrics {
    .el-col {
      margin-bottom: 16px;
    }
  }
  
  .section-header {
    flex-direction: column;
    gap: 12px;
    
    .header-actions {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>