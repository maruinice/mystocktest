<template>
  <div class="analysis-container">
    <div class="page-header">
      <h1 class="page-title">数据分析</h1>
      <p class="page-description">深度分析市场数据，洞察投资机会</p>
    </div>
    
    <!-- 分析工具栏 -->
    <div class="analysis-toolbar">
      <el-select v-model="selectedSymbol" placeholder="选择股票" style="width: 200px;">
        <el-option
          v-for="stock in stockList"
          :key="stock.symbol"
          :label="`${stock.symbol} - ${stock.name}`"
          :value="stock.symbol"
        />
      </el-select>
      
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        style="margin-left: 12px;"
      />
      
      <el-button type="primary" @click="loadAnalysisData" :loading="loading" style="margin-left: 12px;">
        <el-icon><Search /></el-icon>
        分析
      </el-button>
      
      <el-button @click="exportReport" style="margin-left: 12px;">
        <el-icon><Download /></el-icon>
        导出报告
      </el-button>
    </div>
    
    <!-- K线图表 -->
    <div class="card">
      <div class="card-header">
        <h3>K线图表</h3>
        <div class="chart-controls">
          <el-radio-group v-model="chartPeriod" size="small">
            <el-radio-button label="1D">日K</el-radio-button>
            <el-radio-button label="1W">周K</el-radio-button>
            <el-radio-button label="1M">月K</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div class="chart-container">
        <v-chart :option="klineChartOption" style="height: 400px;" />
      </div>
    </div>
    
    <!-- 技术指标 -->
    <el-row :gutter="16" class="indicators-section">
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>技术指标</h3>
            <el-select v-model="selectedIndicator" size="small" style="width: 120px;">
              <el-option label="MACD" value="macd" />
              <el-option label="RSI" value="rsi" />
              <el-option label="KDJ" value="kdj" />
              <el-option label="BOLL" value="boll" />
            </el-select>
          </div>
          <div class="chart-container">
            <v-chart :option="indicatorChartOption" style="height: 300px;" />
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>成交量分析</h3>
          </div>
          <div class="chart-container">
            <v-chart :option="volumeChartOption" style="height: 300px;" />
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 财务分析 -->
    <el-row :gutter="16" class="financial-section">
      <el-col :xs="24" :lg="16">
        <div class="card">
          <div class="card-header">
            <h3>财务指标</h3>
            <el-select v-model="financialPeriod" size="small" style="width: 120px;">
              <el-option label="年报" value="annual" />
              <el-option label="中报" value="semi" />
              <el-option label="季报" value="quarter" />
            </el-select>
          </div>
          
            <el-table :data="financialData" size="small">
            <el-table-column prop="report_date" label="报告期" width="120" />
            <el-table-column prop="revenue" label="营业收入" width="120" align="right">
              <template #default="{ row }">
                {{ formatLargeNumber(row.revenue) }}
              </template>
            </el-table-column>
            <el-table-column prop="net_income" label="净利润" width="120" align="right">
              <template #default="{ row }">
                <span :class="row.net_income >= 0 ? 'stock-up' : 'stock-down'">
                  {{ formatLargeNumber(row.net_income) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="eps" label="每股收益" width="100" align="right">
              <template #default="{ row }">
                {{ row.eps.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="roe" label="ROE" width="80" align="right">
              <template #default="{ row }">
                {{ (row.roe * 100).toFixed(2) }}%
              </template>
            </el-table-column>
            <el-table-column prop="pe_ratio" label="市盈率" width="80" align="right">
              <template #default="{ row }">
                {{ row.pe_ratio?.toFixed(2) || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="pb_ratio" label="市净率" width="80" align="right">
              <template #default="{ row }">
                {{ row.pb_ratio?.toFixed(2) || '-' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <div class="card">
          <div class="card-header">
            <h3>估值分析</h3>
          </div>
          
          <div class="valuation-metrics">
            <div class="metric-item">
              <div class="metric-label">当前价格</div>
              <div class="metric-value">¥{{ currentPrice.toFixed(2) }}</div>
            </div>
            
            <div class="metric-item">
              <div class="metric-label">目标价格</div>
              <div class="metric-value stock-up">¥{{ targetPrice.toFixed(2) }}</div>
            </div>
            
            <div class="metric-item">
              <div class="metric-label">上涨空间</div>
              <div class="metric-value stock-up">
                +{{ ((targetPrice - currentPrice) / currentPrice * 100).toFixed(2) }}%
              </div>
            </div>
            
            <div class="metric-item">
              <div class="metric-label">投资评级</div>
              <div class="metric-value">
                <el-tag type="success">买入</el-tag>
              </div>
            </div>
          </div>
          
          <div class="rating-distribution">
            <h4>机构评级分布</h4>
            <div class="rating-bars">
              <div class="rating-bar">
                <span class="rating-label">买入</span>
                <div class="rating-progress">
                  <div class="rating-fill buy" style="width: 60%"></div>
                </div>
                <span class="rating-count">12</span>
              </div>
              <div class="rating-bar">
                <span class="rating-label">持有</span>
                <div class="rating-progress">
                  <div class="rating-fill hold" style="width: 30%"></div>
                </div>
                <span class="rating-count">6</span>
              </div>
              <div class="rating-bar">
                <span class="rating-label">卖出</span>
                <div class="rating-progress">
                  <div class="rating-fill sell" style="width: 10%"></div>
                </div>
                <span class="rating-count">2</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 新闻和研报 -->
    <el-row :gutter="16" class="news-section">
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>相关新闻</h3>
            <el-link type="primary" @click="viewAllNews">查看全部</el-link>
          </div>
          
          <div class="news-list">
            <div v-for="news in recentNews" :key="news.id" class="news-item">
              <div class="news-title">{{ news.title }}</div>
              <div class="news-meta">
                <span class="news-source">{{ news.source }}</span>
                <span class="news-time">{{ formatRelativeTime(news.publish_time) }}</span>
              </div>
              <div class="news-summary">{{ news.summary }}</div>
            </div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <div class="card">
          <div class="card-header">
            <h3>研究报告</h3>
            <el-link type="primary" @click="viewAllReports">查看全部</el-link>
          </div>
          
          <div class="reports-list">
            <div v-for="report in recentReports" :key="report.id" class="report-item">
              <div class="report-header">
                <div class="report-title">{{ report.title }}</div>
                <el-tag :type="getRatingColor(report.rating)" size="small">
                  {{ report.rating }}
                </el-tag>
              </div>
              <div class="report-meta">
                <span class="report-analyst">{{ report.analyst }}</span>
                <span class="report-institution">{{ report.institution }}</span>
                <span class="report-time">{{ formatRelativeTime(report.publish_time) }}</span>
              </div>
              <div class="report-target" v-if="report.target_price">
                目标价: ¥{{ report.target_price.toFixed(2) }}
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { dataApi } from '@/api/data'
import type { StockInfo } from '@/types/data'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CandlestickChart, LineChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { formatLargeNumber, formatRelativeTime } from '@/utils/format'

function sma(arr: number[], period: number) {
  const res: number[] = []
  let sum = 0
  for (let i = 0; i < arr.length; i++) {
    sum += arr[i]
    if (i >= period) sum -= arr[i - period]
    if (i >= period - 1) res.push(sum / period)
    else res.push(NaN)
  }
  return res
}
function ema(arr: number[], period: number) {
  const res: number[] = []
  const k = 2 / (period + 1)
  let prev = arr[0]
  for (let i = 0; i < arr.length; i++) {
    const v = i === 0 ? arr[0] : arr[i] * k + prev * (1 - k)
    res.push(v)
    prev = v
  }
  return res
}
function calcRSI(closes: number[], period = 14) {
  const res: number[] = []
  let gain = 0
  let loss = 0
  for (let i = 1; i < closes.length; i++) {
    const ch = closes[i] - closes[i - 1]
    gain += ch > 0 ? ch : 0
    loss += ch < 0 ? -ch : 0
    if (i >= period) {
      const prevCh = closes[i - period + 1] - closes[i - period]
      gain -= prevCh > 0 ? prevCh : 0
      loss -= prevCh < 0 ? -prevCh : 0
      const rs = loss === 0 ? 100 : gain / loss
      const rsi = 100 - 100 / (1 + rs)
      res.push(rsi)
    } else res.push(NaN)
  }
  res.unshift(NaN)
  return res
}
function calcMACD(closes: number[], fast = 12, slow = 26, signal = 9) {
  const emaFast = ema(closes, fast)
  const emaSlow = ema(closes, slow)
  const macd: number[] = []
  for (let i = 0; i < closes.length; i++) macd.push(emaFast[i] - emaSlow[i])
  const signalLine = ema(macd, signal)
  const hist: number[] = []
  for (let i = 0; i < closes.length; i++) hist.push(macd[i] - signalLine[i])
  return { macd, signal: signalLine, hist }
}
function calcKDJ(highs: number[], lows: number[], closes: number[], period = 9) {
  const rsv: number[] = []
  for (let i = 0; i < closes.length; i++) {
    const start = Math.max(0, i - period + 1)
    let hh = -Infinity
    let ll = Infinity
    for (let j = start; j <= i; j++) {
      if (highs[j] > hh) hh = highs[j]
      if (lows[j] < ll) ll = lows[j]
    }
    const v = hh === ll ? 0 : ((closes[i] - ll) / (hh - ll)) * 100
    rsv.push(v)
  }
  const K: number[] = []
  const D: number[] = []
  let k = 50
  let d = 50
  for (let i = 0; i < rsv.length; i++) {
    k = (2 * k + rsv[i]) / 3
    d = (2 * d + k) / 3
    K.push(k)
    D.push(d)
  }
  const J: number[] = []
  for (let i = 0; i < K.length; i++) J.push(3 * K[i] - 2 * D[i])
  return { K, D, J }
}
function calcBOLL(closes: number[], period = 20, mult = 2) {
  const mid = sma(closes, period)
  const up: number[] = []
  const low: number[] = []
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      up.push(NaN)
      low.push(NaN)
    } else {
      const start = i - period + 1
      let s = 0
      for (let j = start; j <= i; j++) s += (closes[j] - mid[i]) * (closes[j] - mid[i])
      const std = Math.sqrt(s / period)
      up.push(mid[i] + mult * std)
      low.push(mid[i] - mult * std)
    }
  }
  return { mid, up, low }
}

use([
  CanvasRenderer,
  CandlestickChart,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
])

// 响应式数据
const loading = ref(false)
const selectedSymbol = ref('000001.SZ')
// 默认显示最近一个月的数据
import { getLastMonthRange } from '@/utils/date'
const dateRange = ref<[string, string]>(getLastMonthRange())
const chartPeriod = ref('1D')
const selectedIndicator = ref('macd')
const financialPeriod = ref('annual')

// 股票列表
const stockList = ref<StockInfo[]>([])

// 财务数据
const financialData = ref<any[]>([])

// 新闻数据
const recentNews = ref<any[]>([])

// 研报数据
const recentReports = ref<any[]>([])

// 当前价格和目标价格
const currentPrice = ref(0)
const targetPrice = ref(0)
const klineData = ref<any[]>([])

// 图表配置
const klineChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross'
    }
  },
  legend: {
    data: ['K线', 'MA5', 'MA20']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: klineData.value.length > 0 ? klineData.value.map((d:any)=>d.date) : ['2023-11-27', '2023-11-28', '2023-11-29', '2023-11-30', '2023-12-01'],
    scale: true,
    boundaryGap: false,
    axisLine: { onZero: false },
    splitLine: { show: false },
    min: 'dataMin',
    max: 'dataMax'
  },
  yAxis: {
    scale: true,
    splitArea: {
      show: true
    }
  },
  dataZoom: [
    {
      type: 'inside',
      start: 50,
      end: 100
    },
    {
      show: true,
      type: 'slider',
      top: '90%',
      start: 50,
      end: 100
    }
  ],
  series: [
    {
      name: 'K线',
      type: 'candlestick',
      data: klineData.value.length > 0 ? klineData.value.map((d:any)=>[d.open, d.close, d.low, d.high]) : [
        [10.20, 10.60, 10.15, 10.45],
        [10.45, 10.80, 10.40, 10.75],
        [10.75, 10.55, 10.50, 10.60],
        [10.60, 10.85, 10.55, 10.80],
        [10.80, 10.50, 10.45, 10.50]
      ],
      itemStyle: {
        color: '#ef232a',
        color0: '#14b143',
        borderColor: '#ef232a',
        borderColor0: '#14b143'
      }
    },
    {
      name: 'MA5',
      type: 'line',
      data: [10.40, 10.55, 10.60, 10.65, 10.62],
      smooth: true,
      lineStyle: {
        opacity: 0.5
      }
    },
    {
      name: 'MA20',
      type: 'line',
      data: [10.30, 10.35, 10.40, 10.45, 10.48],
      smooth: true,
      lineStyle: {
        opacity: 0.5
      }
    }
  ]
}))

const indicatorChartOption = computed(() => {
  const x = klineData.value.map((d:any)=>d.date)
  const closes = klineData.value.map((d:any)=>d.close)
  const highs = klineData.value.map((d:any)=>d.high)
  const lows = klineData.value.map((d:any)=>d.low)
  if (selectedIndicator.value === 'macd') {
    const m = calcMACD(closes)
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['MACD', 'Signal', 'Histogram'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: x },
      yAxis: { type: 'value' },
      series: [
        { name: 'MACD', type: 'line', data: m.macd },
        { name: 'Signal', type: 'line', data: m.signal },
        { name: 'Histogram', type: 'bar', data: m.hist }
      ]
    }
  }
  if (selectedIndicator.value === 'rsi') {
    const r = calcRSI(closes, 14)
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['RSI'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: x },
      yAxis: { type: 'value' },
      series: [{ name: 'RSI', type: 'line', data: r }]
    }
  }
  if (selectedIndicator.value === 'kdj') {
    const kd = calcKDJ(highs, lows, closes)
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['K', 'D', 'J'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: x },
      yAxis: { type: 'value' },
      series: [
        { name: 'K', type: 'line', data: kd.K },
        { name: 'D', type: 'line', data: kd.D },
        { name: 'J', type: 'line', data: kd.J }
      ]
    }
  }
  const b = calcBOLL(closes)
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['UPPER', 'MID', 'LOWER'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: x },
    yAxis: { type: 'value' },
    series: [
      { name: 'UPPER', type: 'line', data: b.up },
      { name: 'MID', type: 'line', data: b.mid },
      { name: 'LOWER', type: 'line', data: b.low }
    ]
  }
})

const volumeChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: klineData.value.map((d:any)=>d.date) },
  yAxis: { type: 'value', axisLabel: { formatter: (value: number) => formatLargeNumber(value) } },
  series: [{
    name: '成交量',
    type: 'bar',
    data: klineData.value.map((d:any)=>d.volume),
    itemStyle: {
      color: function(params: any) {
        const d = klineData.value[params.dataIndex]
        return d && d.close >= d.open ? '#ef232a' : '#14b143'
      }
    }
  }]
}))

// 方法
const loadAnalysisData = async () => {
  if (!selectedSymbol.value) {
    ElMessage.warning('请选择股票')
    return
  }
  loading.value = true
  try {
    const md = await dataApi.getMarketData(selectedSymbol.value, { start_date: dateRange.value[0], end_date: dateRange.value[1], period: chartPeriod.value })
    currentPrice.value = md.data?.current_price || 0
    klineData.value = md.data?.kline_data || []
    const fd = await dataApi.getFinancialData(selectedSymbol.value, { report_type: financialPeriod.value })
    financialData.value = Array.isArray(fd.data) ? fd.data : []
    const news = await dataApi.getNews({ symbol: selectedSymbol.value, page: 1, page_size: 20 })
    recentNews.value = news.data?.news || []
    const reports = await dataApi.getAnalysisReports({ symbol: selectedSymbol.value, page: 1, page_size: 20 })
    recentReports.value = reports.data?.reports || []
    if (recentReports.value.length > 0 && recentReports.value[0].target_price) {
      targetPrice.value = recentReports.value[0].target_price
    }
    ElMessage.success('数据加载成功')
  } catch (error) {
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

const exportReport = () => {
  if (!klineData.value.length) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const headers = ['日期','开盘','最高','最低','收盘','成交量']
  const closes = klineData.value.map((d:any)=>d.close)
  const highs = klineData.value.map((d:any)=>d.high)
  const lows = klineData.value.map((d:any)=>d.low)
  let extra: string[] = []
  let indValues: any[] = []
  if (selectedIndicator.value === 'macd') {
    const m = calcMACD(closes)
    extra = ['MACD','Signal','Hist']
    indValues = klineData.value.map((_:any,i:number)=>[m.macd[i], m.signal[i], m.hist[i]])
  } else if (selectedIndicator.value === 'rsi') {
    const r = calcRSI(closes,14)
    extra = ['RSI']
    indValues = klineData.value.map((_:any,i:number)=>[r[i]])
  } else if (selectedIndicator.value === 'kdj') {
    const kd = calcKDJ(highs,lows,closes)
    extra = ['K','D','J']
    indValues = klineData.value.map((_:any,i:number)=>[kd.K[i], kd.D[i], kd.J[i]])
  } else {
    const b = calcBOLL(closes)
    extra = ['UPPER','MID','LOWER']
    indValues = klineData.value.map((_:any,i:number)=>[b.up[i], b.mid[i], b.low[i]])
  }
  const csv = [headers.concat(extra).join(',')].concat(
    klineData.value.map((d:any,i:number)=>[
      d.timestamp,
      d.open,
      d.high,
      d.low,
      d.close,
      d.volume,
      ...indValues[i]
    ].join(','))
  ).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `分析报告_${selectedSymbol.value}_${new Date().toISOString().slice(0,10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告导出成功')
}

const viewAllNews = () => {
  ElMessage.info('查看所有新闻')
}

const viewAllReports = () => {
  ElMessage.info('查看所有研报')
}

const getRatingColor = (rating: string) => {
  const colorMap: Record<string, string> = {
    '买入': 'success',
    '增持': 'primary',
    '持有': 'warning',
    '减持': 'info',
    '卖出': 'danger'
  }
  return colorMap[rating] || 'info'
}

// 监听选中股票变化
watch(selectedSymbol, () => {
  loadAnalysisData()
})
watch(chartPeriod, () => {
  loadAnalysisData()
})

onMounted(async () => {
  try {
    const listResp = await dataApi.getStockList({ page: 1, page_size: 50 })
    stockList.value = listResp.data?.stocks || []
    if (stockList.value.length > 0) {
      selectedSymbol.value = stockList.value[0].symbol
    }
  } catch {}
  loadAnalysisData()
})
</script>

<style lang="scss" scoped>
.analysis-container {
  padding: 24px;
}

.analysis-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.card {
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-container {
  width: 100%;
}

.indicators-section,
.financial-section,
.news-section {
  margin-bottom: 24px;
}

.valuation-metrics {
  margin-bottom: 24px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  
  &:last-child {
    border-bottom: none;
  }
}

.metric-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.rating-distribution {
  h4 {
    margin: 0 0 16px 0;
    font-size: 14px;
    color: var(--el-text-color-primary);
  }
}

.rating-bars {
  .rating-bar {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    
    .rating-label {
      width: 40px;
      font-size: 12px;
      color: var(--el-text-color-regular);
    }
    
    .rating-progress {
      flex: 1;
      height: 8px;
      background: var(--el-fill-color-lighter);
      border-radius: 4px;
      margin: 0 8px;
      overflow: hidden;
      
      .rating-fill {
        height: 100%;
        border-radius: 4px;
        
        &.buy {
          background: var(--el-color-success);
        }
        
        &.hold {
          background: var(--el-color-warning);
        }
        
        &.sell {
          background: var(--el-color-danger);
        }
      }
    }
    
    .rating-count {
      width: 20px;
      font-size: 12px;
      color: var(--el-text-color-regular);
      text-align: right;
    }
  }
}

.news-list,
.reports-list {
  max-height: 400px;
  overflow-y: auto;
}

.news-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  
  &:last-child {
    border-bottom: none;
  }
  
  .news-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-primary);
    margin-bottom: 4px;
    cursor: pointer;
    
    &:hover {
      color: var(--el-color-primary);
    }
  }
  
  .news-meta {
    display: flex;
    gap: 12px;
    margin-bottom: 4px;
    
    .news-source,
    .news-time {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
  
  .news-summary {
    font-size: 12px;
    color: var(--el-text-color-regular);
    line-height: 1.4;
  }
}

.report-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  
  &:last-child {
    border-bottom: none;
  }
  
  .report-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 4px;
    
    .report-title {
      flex: 1;
      font-size: 14px;
      font-weight: 500;
      color: var(--el-text-color-primary);
      margin-right: 8px;
      cursor: pointer;
      
      &:hover {
        color: var(--el-color-primary);
      }
    }
  }
  
  .report-meta {
    display: flex;
    gap: 12px;
    margin-bottom: 4px;
    
    .report-analyst,
    .report-institution,
    .report-time {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
  
  .report-target {
    font-size: 12px;
    color: var(--el-color-success);
    font-weight: 500;
  }
}

@media (max-width: 768px) {
  .analysis-container {
    padding: 16px;
  }
  
  .analysis-toolbar {
    flex-direction: column;
    align-items: stretch;
    
    .el-select,
    .el-date-picker {
      width: 100% !important;
    }
  }
  
  .card {
    padding: 16px;
  }
}
</style>
