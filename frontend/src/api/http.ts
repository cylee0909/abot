export const API_BASE = 'http://127.0.0.1:5001'

export async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  // 为请求添加默认的Content-Type头，如果是JSON请求
  const headers = new Headers(init?.headers)
  if (init?.body && typeof init.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  
  // 使用API_BASE作为基础URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`
  
  const resp = await fetch(fullUrl, {
    ...init,
    headers
  })
  
  if (!resp.ok) {
    try {
      // 尝试获取后端返回的错误信息
      const errorData = await resp.json()
      if (errorData && errorData.error) {
        throw new Error(`${errorData.error} (HTTP ${resp.status})`)
      }
    } catch (innerError) {
      // 如果获取错误信息失败，使用默认的错误信息
      throw new Error(`HTTP ${resp.status}`)
    }
    // 如果没有获取到错误信息，使用默认的错误信息
    throw new Error(`HTTP ${resp.status}`)
  }
  
  return (await resp.json()) as T
}
