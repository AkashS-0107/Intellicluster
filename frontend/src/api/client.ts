/**
 * Centralized API client for IntelliCluster
 * Strictly typed, handles backend domain errors, validation errors, and network failures.
 */

export class ApiClientError extends Error {
  public status: number
  public errorCode?: string
  public details?: unknown

  constructor(status: number, message: string, errorCode?: string, details?: unknown) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.errorCode = errorCode
    this.details = details
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  headers?: Record<string, string>
  params?: Record<string, string | number | boolean | null | undefined>
  body?: unknown
  signal?: AbortSignal
}

function buildQueryString(params?: Record<string, string | number | boolean | null | undefined>): string {
  if (!params) return ''
  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value))
    }
  }
  const qs = searchParams.toString()
  return qs ? `?${qs}` : ''
}

/**
 * Resolves the full URL for an endpoint.
 * Supports import.meta.env.VITE_API_BASE_URL when defined, avoiding duplicate slashes.
 * When undefined or empty, returns relative endpoint for dev server proxy and test compatibility.
 */
export function resolveApiUrl(
  endpoint: string,
  params?: Record<string, string | number | boolean | null | undefined>
): string {
  const rawBase = (import.meta.env?.VITE_API_BASE_URL ?? '').trim()
  const queryString = buildQueryString(params)

  if (!rawBase) {
    return `${endpoint}${queryString}`
  }

  const cleanBase = rawBase.replace(/\/+$/, '')
  const cleanEndpoint = endpoint.replace(/^\/+/, '')
  return `${cleanBase}/${cleanEndpoint}${queryString}`
}

export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', headers = {}, params, body, signal } = options
  const url = resolveApiUrl(endpoint, params)

  const reqHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...headers,
  }

  let reqBody: string | undefined
  if (body !== undefined && body !== null) {
    reqHeaders['Content-Type'] = 'application/json'
    reqBody = JSON.stringify(body)
  }

  let response: Response
  try {
    response = await fetch(url, {
      method,
      headers: reqHeaders,
      body: reqBody,
      signal,
    })
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw err
    }
    const errMsg = err instanceof Error ? err.message : String(err)
    throw new ApiClientError(
      0,
      `Backend connection failure: Unable to reach IntelliCluster backend at ${url}. (${errMsg})`,
      'NETWORK_FAILURE',
      err
    )
  }

  if (!response.ok) {
    let errorPayload: unknown
    try {
      errorPayload = await response.json()
    } catch {
      errorPayload = null
    }

    let parsedMessage = `Request failed with HTTP status ${response.status} (${response.statusText})`
    let parsedErrorCode: string | undefined

    if (errorPayload && typeof errorPayload === 'object') {
      const errObj = errorPayload as Record<string, unknown>
      
      // Domain exception format: { error_code, message, details }
      if (typeof errObj.message === 'string') {
        parsedMessage = errObj.message
      }
      if (typeof errObj.error_code === 'string') {
        parsedErrorCode = errObj.error_code
      }

      // FastAPI validation error format: { detail: [{ loc, msg, type }] }
      if (Array.isArray(errObj.detail)) {
        const issues = errObj.detail
          .map((d: unknown) => {
            if (typeof d === 'object' && d !== null) {
              const item = d as { loc?: unknown[]; msg?: string }
              const field = Array.isArray(item.loc) ? item.loc.join('.') : 'field'
              return `${field}: ${item.msg || 'invalid value'}`
            }
            return String(d)
          })
          .join('; ')
        parsedMessage = `Validation error: ${issues}`
        parsedErrorCode = 'VALIDATION_ERROR'
      } else if (typeof errObj.detail === 'string') {
        parsedMessage = errObj.detail
      }
    }

    throw new ApiClientError(response.status, parsedMessage, parsedErrorCode, errorPayload)
  }

  // Handle empty 204 No Content
  if (response.status === 204) {
    return null as T
  }

  try {
    return (await response.json()) as T
  } catch (err: unknown) {
    throw new ApiClientError(
      response.status,
      'Failed to parse JSON response from server',
      'JSON_PARSE_ERROR',
      err
    )
  }
}
