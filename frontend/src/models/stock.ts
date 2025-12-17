export type OHLC = [number, number, number, number]

export interface CompaniesResponse {
  data: Company[]
}

export interface HistoryResponse {
  data: HistoryBar[]
}

export interface Company {
  security_code: string
  security_name_abbr: string
  eps?: number
  pb?: number
  free_cap?: number
  [key: string]: unknown
}

export interface HistoryBar {
  date: string
  open?: number
  close?: number
  low?: number
  high?: number
  amount?: number
}

export interface PatternItem {
  date: string
  pattern: string
  chinese_name: string
  value: number
  direction: 'bullish' | 'bearish'
}

export interface PatternResult {
  latest_date: string | null
  patterns: PatternItem[]
}

export class DataSeries {
  dates: string[]
  ohlc: OHLC[]
  volumes: number[]

  constructor(dates: string[] = [], ohlc: OHLC[] = [], volumes: number[] = []) {
    this.dates = dates
    this.ohlc = ohlc
    this.volumes = volumes
  }

  static fromHistory(hist: HistoryBar[]): DataSeries {
    const dates = hist.map((d) => d.date)
    const ohlc: OHLC[] = hist.map((d) => [d.open || 0, d.close || 0, d.low || 0, d.high || 0])
    const volumes = hist.map((d) => d.amount || 0)
    return new DataSeries(dates, ohlc, volumes)
  }
}

export class StockInfo {
  name: string
  code: string
  price: number
  change: number
  changePct: number
  currency: string
  high: number
  low: number
  open: number
  prevClose: number
  volume: number
  turnover: number
  pe: number | string
  pb: number | string
  mcap: number
  floatMcap: number | string
  turnoverRate: number
  amplitude: number | string

  constructor(init?: Partial<StockInfo>) {
    Object.assign(this, {
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
      ...(init || {}),
    })
  }

  static from(company: Company, hist: HistoryBar[]): StockInfo {
    const last = hist[hist.length - 1] || {}
    const prev = hist[hist.length - 2] || {}
    const price = last.close || 0
    const prevClose = prev.close || 0
    const change = price - prevClose
    const changePct = prevClose ? (change / prevClose) * 100 : 0
    const amplitude = last.high && last.low ? (((last.high - last.low) / (last.open || 1)) * 100).toFixed(2) : 0

    return new StockInfo({
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
      amplitude,
    })
  }
}

export type Timeframe = '日K' | '周K' | '月K'

export function resample(base: DataSeries, mode: Timeframe): DataSeries {
  if (!base.dates.length) return new DataSeries()

  const toWeekKey = (s: string) => {
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

  const toMonthKey = (s: string) => {
    const d = new Date(s)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    return `${y}-${m}`
  }

  const groups = new Map<string, { o: number; c: number; l: number; h: number; v: number }[]>()
  for (let i = 0; i < base.dates.length; i++) {
    const key = mode === '周K' ? toWeekKey(base.dates[i]) : mode === '月K' ? toMonthKey(base.dates[i]) : base.dates[i]
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push({
      o: base.ohlc[i][0],
      c: base.ohlc[i][1],
      l: base.ohlc[i][2],
      h: base.ohlc[i][3],
      v: base.volumes[i] || 0,
    })
  }

  const dates: string[] = []
  const ohlc: OHLC[] = []
  const volumes: number[] = []
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
  return new DataSeries(dates, ohlc, volumes)
}

export function calcMA(dayCount: number, data: OHLC[]): (number | string)[] {
  const result: (number | string)[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount) {
      result.push('-')
      continue
    }
    let sum = 0
    for (let j = 0; j < dayCount; j++) {
      sum += data[i - j][1]
    }
    result.push(Number((sum / dayCount).toFixed(2)))
  }
  return result
}

export function calcMACD(close: number[], fast = 12, slow = 26, signal = 9) {
  const ema = (period: number, arr: number[]) => {
    const k = 2 / (period + 1)
    const out: number[] = []
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

export function formatNumber(n: number): string {
  return n >= 10000 ? `${(n / 10000).toFixed(2)}万` : n.toLocaleString()
}
