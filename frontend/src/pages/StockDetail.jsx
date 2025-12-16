import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import './StockDetail.css'

function formatNumber(n) {
  return n >= 10000 ? `${(n / 10000).toFixed(2)}万` : n.toLocaleString()
}

async function fetchJSON(url) {
  const resp = await fetch(url)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return await resp.json()
}

function calcMA(dayCount, data) {
  const result = []
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount) {
      result.push('-')
      continue
    }
    let sum = 0
    for (let j = 0; j < dayCount; j++) {
      sum += data[i - j][1]
    }
    result.push((sum / dayCount).toFixed(2))
  }
  return result
}

function calcMACD(close, fast = 12, slow = 26, signal = 9) {
  const ema = (period, arr) => {
    const k = 2 / (period + 1)
    const out = []
    arr.forEach((v, i) => {
      if (i === 0) out.push(v)
      else out.push(v * k + out[i - 1] * (1 - k))
    })
    return out
  }
  const emaFast = ema(fast, close)
  const emaSlow = ema(slow, close)
  const dif = emaFast.map((v, i) => v - emaSlow[i])
  const dea = ema(signal, dif)
  const macd = dif.map((v, i) => (v - dea[i]) * 2)
  return { dif, dea, macd }
}

export default function StockDetail() {
  const chartRef = useRef(null)
  const [timeframe, setTimeframe] = useState('日K')
  const [baseData, setBaseData] = useState({ dates: [], ohlc: [], volumes: [] })
  const [data, setData] = useState({ dates: [], ohlc: [], volumes: [] })
  const [info, setInfo] = useState({
    name: '未知',
    code: '未知',
    price: 0,
    change: 0,
    changePct: 0,
    currency: '未知',
    high: 0,
    low: 0,
    open: 0,
    prevClose: 0,
    volume: 0,
    turnover: 0,
    pe: 0,
    pb: 0,
    mcap: 0,
    floatMcap: 0,
    turnoverRate: 0,
    amplitude: 0,
  })

  useEffect(() => {
    ;(async () => {
      try {
        const base = 'http://127.0.0.1:5001'
        const companies = await fetchJSON(`${base}/companies`)
        const first = companies?.data?.[0]
        const securityCode = first?.security_code
        if (!securityCode) return
        const company = await fetchJSON(`${base}/companies/${securityCode}`)
        const history = await fetchJSON(`${base}/history/${securityCode}`)

        const hist = Array.isArray(history?.data) ? history.data : []
        const dates = hist.map((d) => d.date)
        const ohlc = hist.map((d) => [d.open || 0, d.close || 0, d.low || 0, d.high || 0])
        const volumes = hist.map((d) => d.amount || 0)

        setBaseData({ dates, ohlc, volumes })
        setData({ dates, ohlc, volumes })

        const last = hist[hist.length - 1] || {}
        const prev = hist[hist.length - 2] || {}
        const price = last.close || 0
        const prevClose = prev.close || 0
        const change = price - prevClose
        const changePct = prevClose ? (change / prevClose) * 100 : 0

        setInfo({
          name: company.security_name_abbr || '未知',
          code: company.security_code || '未知',
          price,
          change,
          changePct,
          currency: '未知',
          high: last.high || 0,
          low: last.low || 0,
          open: last.open || 0,
          prevClose,
          volume: last.amount || 0,
          turnover: 0,
          pe: company.eps ? (price / company.eps).toFixed(2) : 0,
          pb: company.pb || 0,
          mcap: 0,
          floatMcap: company.free_cap || 0,
          turnoverRate: 0,
          amplitude: last.high && last.low ? (((last.high - last.low) / (last.open || 1)) * 100).toFixed(2) : 0,
        })
      } catch (e) {
        // 保持静默，使用默认值
      }
    })()
  }, [])

  useEffect(() => {
    const toWeekKey = (s) => {
      const d = new Date(s)
      const day = (d.getDay() + 6) % 7
      const ws = new Date(d)
      ws.setDate(d.getDate() - day)
      ws.setHours(0, 0, 0, 0)
      const y = ws.getFullYear()
      const m = String(ws.getMonth() + 1).padStart(2, '0')
      const dd = String(ws.getDate()).padStart(2, '0')
      return `${y}-${m}-${dd}`
    }
    const toMonthKey = (s) => {
      const d = new Date(s)
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      return `${y}-${m}`
    }
    const resample = (mode) => {
      if (!baseData.dates.length) return { dates: [], ohlc: [], volumes: [] }
      const groups = new Map()
      for (let i = 0; i < baseData.dates.length; i++) {
        const key = mode === '周K' ? toWeekKey(baseData.dates[i]) : mode === '月K' ? toMonthKey(baseData.dates[i]) : baseData.dates[i]
        if (!groups.has(key)) groups.set(key, [])
        groups.get(key).push({
          date: baseData.dates[i],
          o: baseData.ohlc[i][0],
          c: baseData.ohlc[i][1],
          l: baseData.ohlc[i][2],
          h: baseData.ohlc[i][3],
          v: baseData.volumes[i] || 0,
        })
      }
      const dates = []
      const ohlc = []
      const volumes = []
      for (const [k, arr] of groups.entries()) {
        const open = arr[0].o
        const close = arr[arr.length - 1].c
        let high = -Infinity
        let low = Infinity
        let vol = 0
        for (const x of arr) {
          if (x.h > high) high = x.h
          if (x.l < low) low = x.l
          vol += x.v
        }
        dates.push(k)
        ohlc.push([open, close, low === Infinity ? 0 : low, high === -Infinity ? 0 : high])
        volumes.push(vol)
      }
      return { dates, ohlc, volumes }
    }
    setData(resample(timeframe))
  }, [timeframe, baseData])

  useEffect(() => {
    const el = chartRef.current
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
        {
          name: 'K线',
          type: 'candlestick',
          data: data.ohlc,
        },
        { name: 'MA5', type: 'line', data: calcMA(5, data.ohlc), smooth: true, symbol: 'none' },
        { name: 'MA10', type: 'line', data: calcMA(10, data.ohlc), smooth: true, symbol: 'none' },
        { name: 'MA20', type: 'line', data: calcMA(20, data.ohlc), smooth: true, symbol: 'none' },
        { name: 'MA60', type: 'line', data: calcMA(60, data.ohlc), smooth: true, symbol: 'none' },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: data.volumes,
        },
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
        <div className="sd-stat"><span>最高</span><b>{info.high.toFixed(2)}</b></div>
        <div className="sd-stat"><span>最低</span><b>{info.low.toFixed(2)}</b></div>
        <div className="sd-stat"><span>今开</span><b>{info.open.toFixed(2)}</b></div>
        <div className="sd-stat"><span>昨收</span><b>{info.prevClose.toFixed(2)}</b></div>
        <div className="sd-stat"><span>成交量</span><b>{formatNumber(info.volume)}股</b></div>
        <div className="sd-stat"><span>成交额</span><b>{formatNumber(info.turnover)}元</b></div>
        <div className="sd-stat"><span>市盈率(TTM)</span><b>{info.pe}</b></div>
        <div className="sd-stat"><span>市净率</span><b>{info.pb}</b></div>
        <div className="sd-stat"><span>总市值</span><b>{formatNumber(info.mcap)}</b></div>
        <div className="sd-stat"><span>港股市值</span><b>{formatNumber(info.floatMcap)}</b></div>
        <div className="sd-stat"><span>换手</span><b>{info.turnoverRate}%</b></div>
        <div className="sd-stat"><span>振幅</span><b>{info.amplitude}%</b></div>
        <div className="sd-stat"><span>货币单位</span><b>{info.currency}</b></div>
      </section>

      <section className="sd-toolbar">
        {['日K', '周K', '月K'].map((t) => (
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
