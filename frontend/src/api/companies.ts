import { API_BASE, fetchJSON } from './http'
import type { Company, HistoryBar, HistoryResponse, CompaniesResponse } from '../models/stock'

export async function getCompanies() {
  return fetchJSON<CompaniesResponse>(`${API_BASE}/companies`)
}

export async function getCompany(code: string) {
  return fetchJSON<Company>(`${API_BASE}/companies/${code}`)
}

export async function getHistory(code: string) {
  return fetchJSON<HistoryResponse>(`${API_BASE}/history/${code}`)
}
