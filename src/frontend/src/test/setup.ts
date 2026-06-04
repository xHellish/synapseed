// ============================================
// SynapSeed — Vitest global setup
// ============================================
// Se ejecuta antes de cada test. Importa los matchers
// de jest-dom para usar `toBeInTheDocument`, `toHaveTextContent`, etc.

import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Limpiar el DOM después de cada test para evitar fugas
afterEach(() => {
  cleanup()
})
