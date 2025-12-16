export const API_BASE = 'http://127.0.0.1:5001'

export async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, init)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return (await resp.json()) as T
}
