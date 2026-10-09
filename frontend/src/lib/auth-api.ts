import { api } from './api'
import { useAuthStore } from './auth-store'
import { refreshAccessToken } from './auth-session'

interface TokenResponse {
  access_token: string
  token_type: string
}

interface RegisterPayload {
  email: string
  password: string
  age: number
}

export interface UserProfile {
  email: string
  age: number
  skills: string[]
  role: string
  isActive: boolean
}

export async function registerUser(payload: RegisterPayload) {
  await api.post('/users/register', {
    ...payload,
    role: 'user',
    skills: [],
  })
}

export async function loginUser(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password })
  const { data } = await api.post<TokenResponse>('/auth/login', body)
  useAuthStore.getState().setAccessToken(data.access_token)
  return data
}

export { refreshAccessToken }

export async function logoutUser() {
  try {
    await api.post('/auth/logout')
  } finally {
    useAuthStore.getState().clearAccessToken()
  }
}

export async function getCurrentUser() {
  const { data } = await api.get<UserProfile>('/users/me')
  return data
}