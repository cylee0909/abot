import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import './StockDetail.css'
import { calcMA, calcMACD, DataSeries, formatNumber, resample, StockInfo, type Timeframe } from '../models/stock'
import { getCompanies, getCompany, getHistory } from '../api/companies'

export default function StockDetail() {
  const chartRef = useRef<HTMLDivElement | null>(null)
  const [timeframe, setTimeframe] = useState<Timeframe>('日K')
  const [baseData, setBaseData] = useState<DataSeries>(new DataSeries())
  const [data, setData] = useState<DataSeries>(new DataSeries())
  const [info, setInfo] = useState<StockInfo>(new StockInfo())

  useEffect(() => {
    ;(async () => {
      try {
        const companies = await getCompanies()
        const first = companies?.data?.[0]
        const securityCode = first?.security_code
        if (!securityCode) return
        const company = await getCompany(securityCode)
        const history = await getHistory(securityCode)

        const hist = Array.isArray(history?.data) ? history.data : []
        const series = DataSeries.fromHistory(hist)
        setBaseData(series)
        setData(series)

        setInfo(StockInfo.from(company, hist))
      } catch (_) {
        // 保持静默，使用默认值
      }
    })()
  }, [])

  useEffect(() => {
    setData(resample(baseData, timeframe))
  }, [timeframe, baseData])

  useEffect(() => {
    const el = chartRef.current
    if (!el) return
    const chart = echarts.init(el)

    const close = data.ohlc.map((d) => d[1])
    const { dif, dea, macd } = calcMACD(close)

    const option = {
      animation: false,
      backgroundColor: '#fff',
      tooltip: { trigger: 'axis' },
      axisPointer: { link: [{ xAxisIndex: [0, 1, 2] }] },
      grid: [
        { left: 50, right: 30, top: 60, height: 220 },
        { left: 50, right: 30, top: 300, height: 80 },
        { left: 50, right: 30, top: 400, height: 100 },
      ],
      xAxis: [
        { type: 'category', data: data.dates, boundaryGap: false, axisLine: { onZero: false } },
        { type: 'category', data: data.dates, gridIndex: 1 },
        { type: 'category', data: data.dates, gridIndex: 2 },
      ],
      yAxis: [
        { scale: true },
        { gridIndex: 1 },
        { gridIndex: 2 },
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1, 2], start: 80, end: 100 },
        { show: true, xAxisIndex: [0, 1, 2], top: 520, start: 80, end: 100 },
      ],
      series: [
        { name: 'K线', type: 'candlestick', data: data.ohlc },
        { name: 'MA5', type: 'line', data: calcMA(5, data.ohlc), smooth: true, symbol: 'none' },
        { name: 'MA10', type: 'line', data: calcMA(10, data.ohlc), smooth: true, symbol: 'none' },
        { name: 'MA20', type: 'line', data: calcMA(20, data.ohlc), smooth: true, symbol: 'none' },
        { name: 'MA60', type: 'line', data: calcMA(60, data.ohlc), smooth: true, symbol: 'none' },
        { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: data.volumes },
        { name: 'DIF', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: dif, symbol: 'none' },
        { name: 'DEA', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: dea, symbol: 'none' },
        { name: 'MACD', type: 'bar', xAxisIndex: 2, yAxisIndex: 2, data: macd },
      ],
      legend: { top: 32 },
    }

    chart.setOption(option)

    function onResize() {
      chart.resize()
    }
    window.addEventListener('resize', onResize)
    return () => {
      window.removeEventListener('resize', onResize)
      chart.dispose()
    }
  }, [timeframe, data])

  return (
    <div className="stock-detail">
      <header className="sd-header">
        <div className="sd-title">
          <div className="sd-code">{info.name}（{info.code}）</div>
          <div className={`sd-price ${info.change >= 0 ? 'up' : 'down'}`}>HK${info.price.toFixed(2)}</div>
          <div className={`sd-change ${info.change >= 0 ? 'up' : 'down'}`}>
            {info.change.toFixed(2)} {info.changePct.toFixed(2)}%
          </div>
        </div>
        <div className="sd-actions">
          <button className="sd-btn ghost">加自选</button>
        </div>
      </header>

      <section className="sd-stats">
        <div className="sd-stat"><span>最高</span><b>{Number(info.high).toFixed(2)}</b></div>
        <div className="sd-stat"><span>最低</span><b>{Number(info.low).toFixed(2)}</b></div>
        <div className="sd-stat"><span>今开</span><b>{Number(info.open).toFixed(2)}</b></div>
        <div className="sd-stat"><span>昨收</span><b>{Number(info.prevClose).toFixed(2)}</b></div>
        <div className="sd-stat"><span>成交量</span><b>{formatNumber(Number(info.volume))}股</b></div>
        <div className="sd-stat"><span>成交额</span><b>{formatNumber(Number(info.turnover))}元</b></div>
        <div className="sd-stat"><span>市盈率(TTM)</span><b>{info.pe}</b></div>
        <div className="sd-stat"><span>市净率</span><b>{info.pb}</b></div>
        <div className="sd-stat"><span>总市值</span><b>{formatNumber(Number(info.mcap))}</b></div>
        <div className="sd-stat"><span>港股市值</span><b>{formatNumber(Number(info.floatMcap))}</b></div>
        <div className="sd-stat"><span>换手</span><b>{Number(info.turnoverRate)}%</b></div>
        <div className="sd-stat"><span>振幅</span><b>{info.amplitude}%</b></div>
        <div className="sd-stat"><span>货币单位</span><b>{info.currency}</b></div>
      </section>

      <section className="sd-toolbar">
        {(['日K', '周K', '月K'] as Timeframe[]).map((t) => (
          <button
            key={t}
            className={`sd-tab ${timeframe === t ? 'active' : ''}`}
            onClick={() => setTimeframe(t)}
          >
            {t}
          </button>
        ))}
        <div className="sd-spacer" />
        <div className="sd-legend">MA5/10/20/60 · MACD</div>
      </section>

      <section className="sd-chart" ref={chartRef} />
    </div>
  )
}
