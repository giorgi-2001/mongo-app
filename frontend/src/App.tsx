import axios from 'axios'
import { createRootRoute, createRoute, createRouter, Outlet, redirect, RouterProvider } from '@tanstack/react-router'
import { AuthPage } from './components/auth-page'
import { ProfilePage } from './components/profile-page'
import { getCurrentUser } from './lib/auth-api'
import { ensureAccessToken } from './lib/auth-session'
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

const routeTree = rootRoute.addChildren([indexRoute, loginRoute, registerRoute, profileRoute])
const router = createRouter({ routeTree })

export default function App() {
  return <RouterProvider router={router} />
}
