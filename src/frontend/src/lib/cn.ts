// ============================================
// SynapSeed — cn() helper (clsx + tailwind-merge)
// ============================================
// Utilidad estándar para combinar clases condicionales
// y resolver conflictos de Tailwind de forma predecible.

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
