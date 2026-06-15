// ============================================
// SynapSeed — Router (fase 0)
// ============================================
// En la fase 0 solo tenemos una ruta ("/") que muestra el placeholder.
// En la fase 5 se agregan las rutas públicas y protegidas.

import { createBrowserRouter, Navigate } from 'react-router-dom'

// import { App } from '@/App'
import { ProtectedRoute } from '@/app/ProtectedRoute'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    element: <ProtectedRoute />,
    children: [{ path: '/dashboard', element: <DashboardPage /> }],
  },
  //     { path: '/wizard', element: <ContextWizardPage /> },
  //     { path: '/recommendations/:id', element: <RecommendationResultPage /> },
  //     { path: '/history', element: <HistoryPage /> },
  //     { path: '/zones', element: <ZonesPage /> },
  //     { path: '/account', element: <AccountPage /> },
  //   ],
  // },
  { path: '*', element: <Navigate to="/" replace /> },
])
