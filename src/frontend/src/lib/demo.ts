// sales_pitch: bandera global del modo demo.
// En demo la app no llama al backend para login, fincas ni la parte agentica:
// usa datos falsos en memoria para una presentacion fluida y sin dependencias.
import type { AuthUser } from '@/stores/authStore'

export const DEMO_MODE = true

// Token y usuario falsos que se guardan en el authStore al "iniciar sesion" en demo.
export const DEMO_TOKEN = 'demo-token'

export const DEMO_USER: AuthUser = {
  id: 'demo',
  identification: '1 0000 0000',
  full_name: 'Usuario Demo',
  email: 'demo@synapseed.cr',
}

// Cultivos para el dropdown del wizard cuando no hay backend (catalogo offline).
export const DEMO_CROPS = [
  { id: 'tomato', name: 'Tomate' },
  { id: 'coffee', name: 'Café' },
  { id: 'banana', name: 'Banano' },
  { id: 'rice', name: 'Arroz' },
  { id: 'potato', name: 'Papa' },
  { id: 'bean', name: 'Frijol' },
]
