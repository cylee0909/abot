import { API_BASE, fetchJSON } from './http'
import type { PatternResult, AllPatternsResponse } from '../models/model'

export async function getPatterns(code: string, params?: { start?: string; end?: string; limit?: number; days?: number; patterns?: string[] }) {
  const url = `${API_BASE}/patterns/${code}`
  return fetchJSON<PatternResult>(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(params || {})
  })
}

export async function getAllPatterns() {
  return fetchJSON<AllPatternsResponse>(`${API_BASE}/patterns`)
}