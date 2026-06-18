import { Navigate, Outlet } from 'react-router-dom'

import { useAuthStore } from '@/stores/authStore'

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const token = useAuthStore((state) => state.token)

  // Se exige el token (la credencial real) además del flag. Si el logout limpió
  // el store, no hay token y se bloquea aunque se intente entrar cambiando la URL.
  if (!isAuthenticated || !token) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />  // Outlet es el placeholder para las rutas hijas protegidas
}
