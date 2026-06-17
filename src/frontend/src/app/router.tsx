// Rutas de la aplicacion

import { createBrowserRouter, Navigate } from 'react-router-dom'

import { ProtectedRoute } from '@/app/ProtectedRoute'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { CaseWizardStep1 } from '@/features/wizard/CaseWizardStep1'
import { CaseWizardConfirm } from '@/features/wizard/CaseWizardConfirm'
import { CaseWizardStep3 } from '@/features/wizard/CaseWizardStep3'
import { CaseWizardStep4 } from '@/features/wizard/CaseWizardStep4'
import { AccountPage } from '@/features/account/AccountPage'
import { ZonesPage } from '@/features/zones/ZonesPage'
import { AddZonePage } from '@/features/zones/AddZonePage'

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
      { path: '/cases', element: <Navigate to="/cases/wizard/step-1" replace /> },
      { path: '/cases/wizard/step-1', element: <CaseWizardStep1 /> },
      { path: '/cases/wizard/step-2', element: <CaseWizardConfirm /> },
      { path: '/recommendations/:id', element: <CaseWizardStep3 /> },
      { path: '/recommendations/:id/providers', element: <CaseWizardStep4 /> },
      { path: '/account', element: <AccountPage /> },
      { path: '/zones', element: <ZonesPage /> },
      { path: '/zones/new', element: <AddZonePage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
