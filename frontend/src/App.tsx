import { useEffect } from 'react'
import axios from 'axios'
import { createRootRoute, createRoute, createRouter, Outlet, redirect, RouterProvider } from '@tanstack/react-router'
import { AuthPage } from './components/auth-page'
import { ProfilePage } from './components/profile-page'
import { getCurrentUser } from './lib/auth-api'
import { ensureAccessToken } from './lib/auth-session'
import { useAuthStore } from './lib/auth-store'
import './App.css'

const rootRoute = createRootRoute({
  component: Outlet,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: () => {
    throw redirect({ to: '/login' })
  },
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: () => <AuthPage mode="login" />,
})

const registerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/register',
  component: () => <AuthPage mode="register" />,
})

const loginSuccessRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login-success',
  validateSearch: (search: Record<string, unknown>) => ({
    token: typeof search.token === 'string' ? search.token : undefined,
  }),
  component: LoginSuccessPage,
})

const profileRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/profile',
  beforeLoad: async () => {
    try {
      await ensureAccessToken()
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        throw redirect({ to: '/login' })
      }
      throw error
    }
  },
  loader: async () => {
    try {
      return await getCurrentUser()
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        throw redirect({ to: '/login' })
      }
      throw error
    }
  },
  component: () => <ProfilePage profile={profileRoute.useLoaderData()} />,
})

function LoginSuccessPage() {
  const { token } = loginSuccessRoute.useSearch()
  const navigate = loginSuccessRoute.useNavigate()

  useEffect(() => {
    if (token) {
      useAuthStore.getState().setAccessToken(token)
      void navigate({ to: '/profile', replace: true })
    } else {
      void navigate({ to: '/login', replace: true })
    }
  }, [navigate, token])

  return <main className="login-success" role="status">Completing sign-in...</main>
}

const routeTree = rootRoute.addChildren([indexRoute, loginRoute, registerRoute, loginSuccessRoute, profileRoute])
const router = createRouter({ routeTree })

export default function App() {
  return <RouterProvider router={router} />
}
