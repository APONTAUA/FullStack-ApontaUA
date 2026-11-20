import { API_BASE_URL } from './baseUrl'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/*
 * Papel provisório (US-015): enquanto não há autenticação (EPIC-01/EPIC-02), o backend lê o papel
 * do cabeçalho X-Dev-Role, apenas em development e test. Só é enviado em modo de desenvolvimento.
 */
export const DEV_ROLES = ['administrador', 'representante', 'moderador', 'docente', 'estudante'] as const
export type DevRole = (typeof DEV_ROLES)[number]

let devRole: DevRole = 'administrador'

export function getDevRole(): DevRole {
  return devRole
}

export function setDevRole(role: DevRole): void {
  devRole = role
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
}

function errorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}

export async function apiRequest<T>(path: string, { method = 'GET', body }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (import.meta.env.DEV) headers['X-Dev-Role'] = devRole

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (response.status === 204) return undefined as T
  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) throw new ApiError(response.status, errorMessage(payload, response.statusText))
  return payload as T
}
