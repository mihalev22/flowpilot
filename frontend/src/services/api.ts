import { apiClient } from './apiClient'
import type { components } from '../types/api'

export type LoginIn = components['schemas']['LoginIn']
export type RegisterIn = components['schemas']['RegisterIn']
export type TokenOut = components['schemas']['TokenOut']
export type UserOut = components['schemas']['UserOut']
export type RequestOut = components['schemas']['RequestOut']
export type RequestDetailOut = components['schemas']['RequestDetailOut']
export type RequestCreateIn = components['schemas']['RequestCreateIn']
export type RequestUpdateIn = components['schemas']['RequestUpdateIn']
export type RequestStatus = components['schemas']['RequestStatus']
export type MessageSource = components['schemas']['MessageSource']
export type Intent = components['schemas']['Intent']
export type ClientOut = components['schemas']['ClientOut']
export type ClientDetailOut = components['schemas']['ClientDetailOut']
export type DashboardStatsOut = components['schemas']['DashboardStatsOut']
export type ServiceOut = components['schemas']['ServiceOut']

export const authApi = {
  login: (data: LoginIn) => apiClient.post<TokenOut>('/api/auth/login', data),
  register: (data: RegisterIn) => apiClient.post<TokenOut>('/api/auth/register', data),
  me: () => apiClient.get<UserOut>('/api/auth/me'),
}

export type RequestListParams = {
  status?: RequestStatus
  requires_review?: boolean
  limit?: number
  offset?: number
}

export const requestsApi = {
  list: (params: RequestListParams = {}) => {
    const search = new URLSearchParams()
    if (params.status) search.set('status', params.status)
    if (params.requires_review !== undefined) {
      search.set('requires_review', String(params.requires_review))
    }
    if (params.limit !== undefined) search.set('limit', String(params.limit))
    if (params.offset !== undefined) search.set('offset', String(params.offset))
    const qs = search.toString()
    return apiClient.get<RequestOut[]>(`/api/requests${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => apiClient.get<RequestDetailOut>(`/api/requests/${id}`),
  create: (data: RequestCreateIn) => apiClient.post<RequestDetailOut>('/api/requests', data),
  update: (id: number, data: Partial<RequestUpdateIn>) =>
    apiClient.patch<RequestOut>(`/api/requests/${id}`, data),
}

export const clientsApi = {
  list: (search?: string) => {
    const qs = search ? `?search=${encodeURIComponent(search)}` : ''
    return apiClient.get<ClientOut[]>(`/api/clients${qs}`)
  },
  get: (id: number) => apiClient.get<ClientDetailOut>(`/api/clients/${id}`),
}

export const servicesApi = {
  list: () => apiClient.get<ServiceOut[]>('/api/services'),
}

export const dashboardApi = {
  stats: () => apiClient.get<DashboardStatsOut>('/api/dashboard/stats'),
}

export type SettingsOut = {
  ai_provider: string
  ai_mode: string
  ai_key_set: boolean
  telegram_bot_token_set: boolean
  telegram_webhook_secret_set: boolean
}

export const settingsApi = {
  get: () => apiClient.get<SettingsOut>('/api/settings'),
}
