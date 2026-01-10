import { API_BASE, fetchJSON } from './http'
import type { Company, HistoryResponse, CompaniesResponse } from '../models/model'

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
