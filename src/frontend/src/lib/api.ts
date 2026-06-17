import axios from 'axios'

import type { ProviderPayload, RecommendationData } from '@/features/wizard/recommendationMapper'

const apiClient = axios.create({
  baseURL: '/api/v1',
})

function authHeaders(token: string | null) {
  return token ? { Authorization: `Bearer ${token}` } : undefined
}

export interface AuthUserPayload {
  id: string | number
  identification: string
  full_name: string
  email: string
  phone?: string | null
}

export interface LoginResponse {
  access_token: string
  refresh_token?: string
  expires_in?: number
  token_type?: string
  user: AuthUserPayload
}

export interface ZonePayload {
  id: string | number
  name?: string
  nombre?: string
  location?: string
  soil_type?: string
  humidity?: string
  temperature?: string
  water_quality?: string
  crop?: string
  user_id?: string
}

export interface ZoneFormPayload {
  name: string
  location: string
  temperature: string
  humidity: string
  soil_type: string
  water_quality: string
}

export interface CropOptionPayload {
  id: string
  name: string
}

export interface RecommendationRequestResponse {
  recommendation_id: string | number
  ticket_id: string
}

export const authApi = {
  async login(payload: { identification: string; password: string }) {
    const response = await apiClient.post<LoginResponse>('/auth/login', payload)
    return response.data
  },

  async register(payload: {
    identification: string
    full_name: string
    phone: string
    email: string
    password: string
  }) {
    const response = await apiClient.post('/auth/register', payload)
    return response.data
  },

  async resetPassword(payload: {
    identification: string
    email: string
    new_password: string
  }) {
    const response = await apiClient.post('/auth/reset-password', payload)
    return response.data
  },
}

export const userApi = {
  async getMe(token: string | null) {
    const response = await apiClient.get<AuthUserPayload>('/users/me', {
      headers: authHeaders(token),
    })
    return response.data
  },

  async updateMe(
    token: string | null,
    payload: {
      full_name: string
      email: string
      phone: string
    },
  ) {
    const response = await apiClient.put<AuthUserPayload>('/users/me', payload, {
      headers: authHeaders(token),
    })
    return response.data
  },
}

export const zonesApi = {
  async list(token: string | null) {
    const response = await apiClient.get<ZonePayload[]>('/zones', {
      headers: authHeaders(token),
    })
    return response.data
  },

  async create(token: string | null, payload: ZoneFormPayload) {
    const response = await apiClient.post('/zones', payload, {
      headers: authHeaders(token),
    })
    return response.data
  },

  async update(token: string | null, id: string | number, payload: ZoneFormPayload) {
    const response = await apiClient.put(`/zones/${id}`, payload, {
      headers: authHeaders(token),
    })
    return response.data
  },

  async delete(token: string | null, id: string | number) {
    const response = await apiClient.delete(`/zones/${id}`, {
      headers: authHeaders(token),
    })
    return response.data
  },
}

export const catalogsApi = {
  async crops() {
    const response = await apiClient.get<CropOptionPayload[]>('/catalogs/crops')
    return response.data
  },
}

export const recommendationsApi = {
  async request(token: string | null, payload: Record<string, unknown>) {
    const response = await apiClient.post<RecommendationRequestResponse>(
      '/recommendations/request',
      payload,
      { headers: authHeaders(token) },
    )
    return response.data
  },

  async detail(token: string | null, id: string | number) {
    const response = await apiClient.get<RecommendationData>(`/recommendations/${id}`, {
      headers: authHeaders(token),
    })
    return response.data
  },

  async providers(token: string | null, id: string | number) {
    const response = await apiClient.get<ProviderPayload[]>(
      `/recommendations/${id}/providers`,
      { headers: authHeaders(token) },
    )
    return response.data
  },
}
