import axios from 'axios'
import { useAuthStore } from './auth-store'

interface TokenResponse {
  access_token: string
  token_type: string
}

const refreshClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  withCredentials: true,
})

let refreshPromise: Promise<string> | null = null

export function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = refreshClient.get<TokenResponse>('/auth/refresh')
      .then(({ data }) => {
        useAuthStore.getState().setAccessToken(data.access_token)
        return data.access_token
      })
      .catch((error: unknown) => {
        useAuthStore.getState().clearAccessToken()
        throw error
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

export async function ensureAccessToken() {
  return useAuthStore.getState().accessToken ?? refreshAccessToken()
}