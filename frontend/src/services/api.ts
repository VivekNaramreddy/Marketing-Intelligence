export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, { method, headers: body instanceof FormData ? undefined : { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body) })
  if (!response.ok) {
    let message = 'Something went wrong. Please try again.'
    try { const error = await response.json(); message = typeof error.detail === 'string' ? error.detail : 'Check the submitted fields.' } catch { /* Non-JSON server response. */ }
    throw new Error(message)
  }
  return response.json()
}
