import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface WizardData {
  finca_id?: string
  finca_name?: string
  crop?: string
  crop_stage?: string
  affected_area?: number
  soil_type?: string
  humidity?: string
  temperature?: string
  water_quality?: string
  problem_to_solve?: string
  last_agrochemical?: string
  max_budget_per_liter?: number
  ticket_id?: string
  recommendation_id?: string
}

interface WizardState {
  step: number
  data: WizardData
  setStep: (s: number) => void
  next: () => void
  prev: () => void
  update: (d: Partial<WizardData>) => void
  reset: () => void
}

// Store global del wizard: guarda el paso actual y los datos del caso entre pantallas.
// persist() lo respalda en localStorage para no perder el progreso al recargar.
export const useWizardStore = create<WizardState>()(
  persist(
    (set) => ({
      step: 1,
      data: {},
      setStep: (s) => set({ step: s }),
      next: () => set((state) => ({ step: Math.min(4, state.step + 1) })),  // avanza sin pasar de 4
      prev: () => set((state) => ({ step: Math.max(1, state.step - 1) })),  // retrocede sin bajar de 1
      update: (d) => set((state) => ({ data: { ...state.data, ...d } })),  // fusiona datos nuevos con los previos
      reset: () => set({ step: 1, data: {} }),  // limpia todo (al terminar o cancelar el caso)
    }),
    { name: 'synapseed-wizard' },  // clave en localStorage
  ),
)

export default useWizardStore
