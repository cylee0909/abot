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

    // 计算默认显示范围
    let start = 80;
    const dataLength = data.dates.length;
    
    if (timeframe === '日K') {
      // 日K显示近6个月，假设每月20个交易日
      const showDays = 6 * 20;
      start = Math.max(0, 100 - (showDays / dataLength) * 100);
    } else if (timeframe === '周K') {
      // 周K显示近1年，假设每年52周
      const showWeeks = 52;
      start = Math.max(0, 100 - (showWeeks / dataLength) * 100);
    } else if (timeframe === '月K') {
      // 月K显示近3年
      const showMonths = 36;
      start = Math.max(0, 100 - (showMonths / dataLength) * 100);
    }
    
    const option = {
      animation: false,
      backgroundColor: '#fff',
      tooltip: {
        trigger: 'axis',
        position: 'top',
        formatter: function(params) {
          const date = params[0].axisValue;
          let html = `<div style="padding: 8px;"><div><strong>${date}</strong></div>`;
          
          // 查找 K 线数据
          const kline = params.find(p => p.seriesName === 'K线');
          if (kline) {
            html += `
              <div>开: ${kline.data[1].toFixed(2)}</div>
              <div>收: ${kline.data[4].toFixed(2)}</div>
              <div>高: ${kline.data[2].toFixed(2)}</div>
              <div>低: ${kline.data[3].toFixed(2)}</div>
            `;
          }
          
          // 查找成交量数据
          const volume = params.find(p => p.seriesName === '成交量');
          if (volume) {
            html += `<div>量: ${volume.data.toFixed(0)}手</div>`;
          }
          
          // 查找 MACD 数据
          const dif = params.find(p => p.seriesName === 'DIF');
          const dea = params.find(p => p.seriesName === 'DEA');
          const macdBar = params.find(p => p.seriesName === 'MACD');
          if (dif && dea && macdBar) {
            html += `
              <div>DIF: ${dif.data.toFixed(4)}</div>
              <div>DEA: ${dea.data.toFixed(4)}</div>
              <div>MACD: ${macdBar.data.toFixed(4)}</div>
            `;
          }
          
          html += '</div>';
          return html;
        },
        confine: true
      },
      axisPointer: { link: [{ xAxisIndex: [0, 1, 2] }] },
      grid: [
        { left: 50, right: 30, top: 30, height: 220 },
        { left: 50, right: 30, top: 270, height: 80 },
        { left: 50, right: 30, top: 370, height: 100 },
      ],
      xAxis: [
        { type: 'category', data: data.dates, boundaryGap: false, axisLine: { onZero: false } },
        { type: 'category', data: data.dates, gridIndex: 1 },
        { type: 'category', data: data.dates, gridIndex: 2 },
      ],
      yAxis: [
        { scale: true },
        { gridIndex: 1, splitNumber: 3, axisLabel: { fontSize: 10 } },
        { gridIndex: 2, splitNumber: 3, axisLabel: { fontSize: 10 } },
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1, 2], start: start, end: 100 },
        { show: true, xAxisIndex: [0, 1, 2], top: 520, start: start, end: 100 },
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
          <div className={`sd-price ${info.change >= 0 ? 'up' : 'down'}`}>{info.price.toFixed(2)}</div>
          <div className={`sd-change ${info.change >= 0 ? 'up' : 'down'}`}>
            {info.change.toFixed(2)} {info.changePct.toFixed(2)}%
          </div>
        </div>
        <div className="sd-actions">
          <button className="sd-btn ghost">加自选</button>
        </div>
      </header>

      <section className="sd-stats">
        {(Number(info.high) > 0) && <div className="sd-stat"><span>最高</span><b>{Number(info.high).toFixed(2)}</b></div>}
        {(Number(info.low) > 0) && <div className="sd-stat"><span>最低</span><b>{Number(info.low).toFixed(2)}</b></div>}
        {(Number(info.open) > 0) && <div className="sd-stat"><span>今开</span><b>{Number(info.open).toFixed(2)}</b></div>}
        {(Number(info.prevClose) > 0) && <div className="sd-stat"><span>昨收</span><b>{Number(info.prevClose).toFixed(2)}</b></div>}
        {(Number(info.volume) > 0) && <div className="sd-stat"><span>成交量</span><b>{formatNumber(Number(info.volume))}股</b></div>}
        {(Number(info.turnover) > 0) && <div className="sd-stat"><span>成交额</span><b>{formatNumber(Number(info.turnover))}元</b></div>}
        {(Number(info.pe) > 0) && <div className="sd-stat"><span>市盈率(TTM)</span><b>{info.pe}</b></div>}
        {(Number(info.pb) > 0) && <div className="sd-stat"><span>市净率</span><b>{info.pb}</b></div>}
        {(Number(info.mcap) > 0) && <div className="sd-stat"><span>总市值</span><b>{formatNumber(Number(info.mcap))}</b></div>}
        {(Number(info.floatMcap) > 0) && <div className="sd-stat"><span>港股市值</span><b>{formatNumber(Number(info.floatMcap))}</b></div>}
        {(Number(info.turnoverRate) > 0) && <div className="sd-stat"><span>换手</span><b>{Number(info.turnoverRate)}%</b></div>}
        {(Number(info.amplitude) > 0) && <div className="sd-stat"><span>振幅</span><b>{info.amplitude}%</b></div>}
        {(info.currency && info.currency !== '未知') && <div className="sd-stat"><span>货币单位</span><b>{info.currency}</b></div>}
      </section>

      <section className="sd-toolbar">
        {(['日K', '周K', '月K'] as Timeframe[]).map((t) => (
          <span
            key={t}
            className={`sd-tab ${timeframe === t ? 'active' : ''}`}
            onClick={() => setTimeframe(t)}
          >
            {t}
          </span>
        ))}
        <div className="sd-spacer" />

      </section>

      <section className="sd-chart" ref={chartRef} />
    </div>
  )
}
