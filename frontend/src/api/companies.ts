import { API_BASE, fetchJSON } from './http'
import type { Company, HistoryBar, HistoryResponse, CompaniesResponse, PatternResult } from '../models/stock'

export async function getCompanies() {
  return fetchJSON<CompaniesResponse>(`${API_BASE}/companies`)
}

export async function getCompany(code: string) {
  return fetchJSON<Company>(`${API_BASE}/companies/${code}`)
}

export async function getHistory(code: string, params?: { start?: string; end?: string; limit?: number }) {
  const url = new URL(`${API_BASE}/history/${code}`)
  if (params) {
    if (params.start) url.searchParams.append('start', params.start)
    if (params.end) url.searchParams.append('end', params.end)
    if (params.limit) url.searchParams.append('limit', params.limit.toString())
  }
  return fetchJSON<HistoryResponse>(url.toString())
}

export async function getPatterns(code: string, params?: { start?: string; end?: string; limit?: number; days?: number; patterns?: string[] }) {
  const url = new URL(`${API_BASE}/patterns/${code}`)
  if (params) {
    if (params.start) url.searchParams.append('start', params.start)
    if (params.end) url.searchParams.append('end', params.end)
    if (params.limit) url.searchParams.append('limit', params.limit.toString())
    if (params.days) url.searchParams.append('days', params.days.toString())
    if (params.patterns && params.patterns.length > 0) {
      url.searchParams.append('patterns', params.patterns.join(','))
    }
  }
  return fetchJSON<PatternResult>(url.toString())
}
