// Store de fincas en memoria para el modo demo (sales_pitch).
// NO se persiste a propósito: al recargar la pagina las fincas creadas se borran,
// tal como se espera en una prueba/demo en vivo.
import { create } from 'zustand'

export interface DemoZone {
  id: string
  name: string
  location: string
  soil_type: string
  humidity: string
  temperature: string
  water_quality: string
}

interface DemoZonesState {
  zones: DemoZone[]
  addZone: (zone: Omit<DemoZone, 'id'>) => DemoZone
  updateZone: (id: string, zone: Omit<DemoZone, 'id'>) => void
  removeZone: (id: string) => void
  clear: () => void
}

export const useDemoZonesStore = create<DemoZonesState>((set) => ({
  zones: [],
  addZone: (zone) => {
    const newZone: DemoZone = { ...zone, id: `demo-${Date.now()}` }
    set((state) => ({ zones: [...state.zones, newZone] }))
    return newZone
  },
  updateZone: (id, zone) =>
    set((state) => ({
      zones: state.zones.map((z) => (z.id === id ? { ...zone, id } : z)),
    })),
  removeZone: (id) =>
    set((state) => ({ zones: state.zones.filter((z) => z.id !== id) })),
  clear: () => set({ zones: [] }),
}))
