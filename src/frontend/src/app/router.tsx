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
import { AccountPage } from '@/features/account/AccountPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { ZonesPage } from '@/features/zones/ZonesPage'
import { AddZonePage } from '@/features/zones/AddZonePage'
import { CaseWizardStep1 } from '@/features/wizard/CaseWizardStep1'
import { CaseWizardConfirm } from '@/features/wizard/CaseWizardConfirm'
import { CaseWizardStep3 } from '@/features/wizard/CaseWizardStep3'
import { CaseWizardStep4 } from '@/features/wizard/CaseWizardStep4'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/zones', element: <ZonesPage /> },
      { path: '/zones/new', element: <AddZonePage /> },
      { path: '/cases', element: <CaseWizardStep1 /> },
      { path: '/cases/wizard/step-1', element: <CaseWizardStep1 /> },
      { path: '/cases/wizard/step-2', element: <CaseWizardConfirm /> },
      { path: '/recommendations/:id', element: <CaseWizardStep3 /> },
      { path: '/recommendations/:id/providers', element: <CaseWizardStep4 /> },
      { path: '/account', element: <AccountPage /> },
    ],
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
