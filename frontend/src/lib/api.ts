import axios, { type AxiosError } from 'axios'
import { refreshAccessToken } from './auth-session'
import { useAuthStore } from './auth-store'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config
    const isAuthEndpoint = ['/auth/login', '/auth/refresh', '/auth/logout']
      .some((endpoint) => request?.url?.endsWith(endpoint))

    if (error.response?.status !== 401 || !request || request._authRetry || isAuthEndpoint) {
      return Promise.reject(error)
    }

    request._authRetry = true
    try {
      const token = await refreshAccessToken()
      request.headers.Authorization = `Bearer ${token}`
      return api(request)
    } catch (refreshError) {
      useAuthStore.getState().clearAccessToken()
      return Promise.reject(refreshError)
    }
  },
)

declare module 'axios' {
  interface InternalAxiosRequestConfig {
    _authRetry?: boolean
  }
}