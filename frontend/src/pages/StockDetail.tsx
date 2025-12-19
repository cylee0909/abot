import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import './StockDetail.css'
import StockList from './StockList'
import SelectGroupModal from './SelectGroupModal'
import PatternSelector from './PatternSelector'
import { calcMA, calcMACD, DataSeries, formatNumber, resample, StockInfo, type Timeframe, type PatternResult } from '../models/stock'
import { getCompany, getHistory, getPatterns } from '../api/companies'

export default function StockDetail() {
  const chartRef = useRef<HTMLDivElement | null>(null)
  const [timeframe, setTimeframe] = useState<Timeframe>('日K')
  const [baseData, setBaseData] = useState<DataSeries>(new DataSeries())
  const [data, setData] = useState<DataSeries>(new DataSeries())
  const [info, setInfo] = useState<StockInfo>(new StockInfo())
  const [patterns, setPatterns] = useState<PatternResult | null>(null)
  const [selectedStock, setSelectedStock] = useState<string>('')
  const [isSelectGroupModalVisible, setIsSelectGroupModalVisible] = useState(false)
  const [showPatternSelect, setShowPatternSelect] = useState(false)
  const [selectedPatterns, setSelectedPatterns] = useState<string[]>([])
  const [hasRequestedPatterns, setHasRequestedPatterns] = useState(false)

  // 获取单个股票详情
  const fetchStockDetail = async (securityCode: string) => {
    try {
      const company = await getCompany(securityCode)
      
      // 定义时间区间参数，默认获取最近3年数据
      const timeParams = {
        limit: 1095, // 默认获取3年数据
        days: 30     // 默认检测最近30天的形态
      }
      
      const history = await getHistory(securityCode, timeParams)

      const hist = Array.isArray(history?.data) ? history.data : []
      const series = DataSeries.fromHistory(hist)
      setBaseData(series)
      setData(series)
      // 不在这里请求形态数据，只有点击形态选择按钮时才请求
      // setPatterns(patterns)

      setInfo(StockInfo.from(company, hist))
      // 重置形态数据和请求状态
      setPatterns(null)
      setHasRequestedPatterns(false)
    } catch (error) {
      console.error('获取股票详情失败:', error)
    }
  }

  // 请求形态数据
  const fetchPatterns = async () => {
    if (!selectedStock || hasRequestedPatterns) return
    
    try {
      const timeParams = {
        limit: 1095,
        days: 1095
      }
      const patterns = await getPatterns(selectedStock, timeParams)
      setPatterns(patterns)
      setHasRequestedPatterns(true)
    } catch (error) {
      console.error('获取形态数据失败:', error)
    }
  }

  // 选中股票处理
  const handleStockSelect = (securityCode: string) => {
    setSelectedStock(securityCode)
    fetchStockDetail(securityCode)
  }

  useEffect(() => {
    // 初始加载不执行，等待用户选择股票
  }, [])

  useEffect(() => {
    setData(resample(baseData, timeframe))
  }, [timeframe, baseData])

  // 点击外部区域关闭形态选择弹框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const button = document.querySelector('.pattern-select-btn');
      const dropdown = document.querySelector('.pattern-select-dropdown');
      
      if (button && dropdown && showPatternSelect && !button.contains(event.target as Node) && !dropdown.contains(event.target as Node)) {
        setShowPatternSelect(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showPatternSelect]);

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
    
    // 准备形态标记数据
    const patternMarkers: Array<{ name: string; x: number; y: number; symbol: string; color: string; text: string; direction: string }> = [];
    if (patterns?.patterns && selectedPatterns.length > 0) {
      patterns.patterns.forEach(pattern => {
        // 只显示被选中的形态
        if (selectedPatterns.includes(pattern.chinese_name)) {
          // 找到对应日期在data.dates中的索引
          const index = data.dates.indexOf(pattern.date);
          if (index !== -1) {
            const klineData = data.ohlc[index];
            const high = klineData[3]; // OHLC数组中的high是第四个元素（索引3）
            const low = klineData[2]; // OHLC数组中的low是第三个元素（索引2）
            
            // 根据形态方向设置标记位置和样式
            if (pattern.direction === 'bullish') {
              // 看涨形态标记在上方
              patternMarkers.push({
                name: pattern.chinese_name,
                x: index,
                y: high,
                symbol: 'triangle',
                color: '#ef5350',
                text: '↑',
                direction: pattern.direction
              });
            } else {
              // 看跌形态标记在下方
              patternMarkers.push({
                name: pattern.chinese_name,
                x: index,
                y: low,
                symbol: 'triangle',
                color: '#26a69a',
                text: '↓',
                direction: pattern.direction
              });
            }
          }
        }
      });
    }
    
    // 定义MA线配置常量
    const MA_CONFIG = {
      common: {
        type: 'line' as const,
        smooth: true,
        symbol: 'none' as const,
        lineStyle: {
          width: 1
        }
      },
      colors: {
        MA5: '#FFA500', 
        MA10: '#1E90FF', 
        MA20: '#9370DB',
        MA60: '#093',
        DIF: '#FF6B6B',
        DEA: '#093'
      }
    };
    
    // 计算各均线数据
    const maData = {
      MA5: calcMA(5, data.ohlc),
      MA10: calcMA(10, data.ohlc),
      MA20: calcMA(20, data.ohlc),
      MA60: calcMA(60, data.ohlc)
    };
    
    const option = {
      animation: false,
      backgroundColor: '#fff',
      legend: {
        show: false // 隐藏默认图例
      },
      tooltip: {
        trigger: 'axis',
        position: ['0px', '0px'], // 调整位置到左上角边缘
        formatter: function(params) {
          let html = `均线 `;
          
          // 简化MA线数据显示逻辑
          const maLines = ['MA5', 'MA10', 'MA20', 'MA60'];
          maLines.forEach(maLine => {
            const maData = params.find(p => p.seriesName === maLine);
            if (maData) {
              const color = MA_CONFIG.colors[maLine as keyof typeof MA_CONFIG.colors];
              html += `<span style="color: ${color};">${maLine}:${maData.data.toFixed(2)} </span>`;
            }
          });
          
          return html;
        },
        backgroundColor: 'transparent',
        borderWidth: 0,
        textStyle: {
          fontSize: 12,
          lineHeight: 1.5
        }
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
        { 
          name: 'K线', 
          type: 'candlestick', 
          data: data.ohlc, 
          itemStyle: { 
            borderWidth: 1,
            color: 'transparent', // 阳线空心
            borderColor: '#ef5350', // 阳线上边框颜色
            color0: '#093', // 阴线颜色
            borderColor0: '#093' // 阴线下边框颜色
          } 
        },
        // 简化MA线配置，使用常量和映射
        { 
          name: 'MA5', 
          ...MA_CONFIG.common, 
          data: maData.MA5,
          lineStyle: { ...MA_CONFIG.common.lineStyle, color: MA_CONFIG.colors.MA5 }
        },
        { 
          name: 'MA10', 
          ...MA_CONFIG.common, 
          data: maData.MA10,
          lineStyle: { ...MA_CONFIG.common.lineStyle, color: MA_CONFIG.colors.MA10 }
        },
        { 
          name: 'MA20', 
          ...MA_CONFIG.common, 
          data: maData.MA20,
          lineStyle: { ...MA_CONFIG.common.lineStyle, color: MA_CONFIG.colors.MA20 }
        },
        { 
          name: 'MA60', 
          ...MA_CONFIG.common, 
          data: maData.MA60,
          lineStyle: { ...MA_CONFIG.common.lineStyle, color: MA_CONFIG.colors.MA60 }
        },
        // 添加形态标记系列
        { 
          name: '形态标记',
          type: 'scatter',
          data: patternMarkers.map(marker => ({
            name: marker.name,
            value: [marker.x, marker.y],
            itemStyle: {
              color: marker.color,
            },
            symbolSize: 12,
            symbol: marker.symbol,
            symbolRotate: marker.direction === 'bullish' ? 0 : 180,
          })),
          tooltip: {
            formatter: '{b}'
          },
          z: 10
        },
        { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: data.volumes },
        // 简化MACD相关线配置
        { 
          name: 'DIF', 
          ...MA_CONFIG.common,
          xAxisIndex: 2, 
          yAxisIndex: 2, 
          data: dif,
          lineStyle: { ...MA_CONFIG.common.lineStyle, color: MA_CONFIG.colors.DIF }
        },
        { 
          name: 'DEA', 
          ...MA_CONFIG.common,
          xAxisIndex: 2, 
          yAxisIndex: 2, 
          data: dea,
          lineStyle: { ...MA_CONFIG.common.lineStyle, color: MA_CONFIG.colors.DEA }
        },
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
  }, [timeframe, data, patterns, selectedPatterns])

  return (
    <div className="stock-detail-container">
      {/* 左侧股票列表 */}
      <StockList selectedStock={selectedStock} onStockSelect={handleStockSelect} />

      {/* 右侧股票详情 */}
      <main className="stock-detail">
        <header className="sd-header">
          <div className="sd-title">
            <div className="sd-code">{info.name}（{info.code}）</div>
            <div className={`sd-price ${info.change >= 0 ? 'up' : 'down'}`}>{info.price.toFixed(2)}</div>
            <div className={`sd-change ${info.change >= 0 ? 'up' : 'down'}`}>
              {info.change >= 0 ? '+' : ''}{info.change.toFixed(2)} {info.changePct >= 0 ? '+' : ''}{info.changePct.toFixed(2)}%
            </div>
          </div>
          <div className="sd-actions">
            <button 
              className="sd-btn ghost" 
              onClick={() => setIsSelectGroupModalVisible(true)}
            >
              加入分组
            </button>
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
          <PatternSelector
            patterns={patterns}
            selectedPatterns={selectedPatterns}
            onPatternSelect={(patternName, isSelected) => {
              if (isSelected) {
                setSelectedPatterns([...selectedPatterns, patternName]);
              } else {
                setSelectedPatterns(selectedPatterns.filter(p => p !== patternName));
              }
            }}
            showPatternSelect={showPatternSelect}
            onTogglePatternSelect={() => {
              setShowPatternSelect(!showPatternSelect);
              // 如果是打开弹窗，并且还没有请求过形态数据，则请求
              if (!showPatternSelect && !hasRequestedPatterns) {
                fetchPatterns();
              }
            }}
          />
        </section>

        <section className="sd-chart" ref={chartRef} />
      </main>

      {/* 选择分组弹窗 */}
      <SelectGroupModal
        visible={isSelectGroupModalVisible}
        stockCode={selectedStock}
        onClose={() => setIsSelectGroupModalVisible(false)}
        onSuccess={() => {
          // 可以在这里添加成功提示
          console.log('股票已成功添加到分组')
        }}
      />
    </div>
  )
}
