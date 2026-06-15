import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useParams } from 'react-router-dom'
import { Phone, Mail, MapPin, Leaf } from 'lucide-react'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { useWizardStore } from '@/stores/wizardStore'
import { cn } from '@/lib/cn'

/* ──────────────────────────────────────────────
   Tipos
   ────────────────────────────────────────────── */

interface Provider {
  id: string | number
  name: string
  product_name: string
  phone?: string
  email?: string
  location?: string
}

/* ── Demo data (para visualización sin backend) ── */
const DEMO_PROVIDERS: Provider[] = [
  {
    id: 1,
    name: 'AgroSuministros del Valle',
    product_name: 'FungiShield Pro',
    phone: '+506 2274-5632',
    email: 'ventas@agrosuministros.cr',
    location: 'Alajuela, Costa Rica',
  },
  {
    id: 2,
    name: 'Distribuidora Agrícola Centroamericana',
    product_name: 'AgriProtect Plus',
    phone: '+506 2256-8971',
    email: 'info@daccentro.com',
    location: 'Heredia, Costa Rica',
  },
  {
    id: 3,
    name: 'EcoSoluciones CR',
    product_name: 'EcoFungi Natural',
    phone: '+506 2283-4512',
    email: 'contacto@ecosoluciones.cr',
    location: 'Cartago, Costa Rica',
  },
]

/* ──────────────────────────────────────────────
   Stepper
   ────────────────────────────────────────────── */

function Stepper({ step }: { step: number }) {
  const steps = ['Datos del caso', 'Confirmación', 'Recomendaciones', 'Proveedores']
  return (
    <div className="mb-6 flex w-full items-center gap-4">
      {steps.map((label, i) => {
        const idx = i + 1
        const active = idx === step
        const done = idx < step
        return (
          <div key={label} className="flex items-center gap-3">
            <div
              className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold',
                done || active ? 'bg-[#16A34A] text-white' : 'border border-[#E5E7EB] bg-white text-[#6B7280]',
              )}
            >
              {idx}
            </div>
            <div className="text-sm">{label}</div>
            {i < steps.length - 1 && (
              <div className={cn('h-0.5 w-12', done ? 'bg-[#16A34A]' : 'bg-[#E5E7EB]')} />
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ──────────────────────────────────────────────
   Componente principal
   ────────────────────────────────────────────── */

export function CaseWizardStep4() {
  const token = useAuthStore((s) => s.token)
  const wizardStep = useWizardStore((s) => s.step)
  const { id } = useParams<{ id: string }>()

  const isDemo = !id || id === 'demo'

  const {
    data: providersData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['providers', id],
    queryFn: async () => {
      if (isDemo) return DEMO_PROVIDERS
      const res = await axios.get(`/api/v1/recommendations/${id}/providers`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return res.data
    },
    enabled: !!token && !isDemo,
  })

  const providers = providersData ?? (isDemo ? DEMO_PROVIDERS : [])

  /* — Loading state */
  if (isLoading) {
    return (
      <AppLayout>
        <section className="mx-auto max-w-4xl">
          <Stepper step={wizardStep} />
          <div className="flex items-center justify-center py-24">
            <div className="flex flex-col items-center gap-3 text-[#6B7280]">
              <Leaf className="h-8 w-8 animate-pulse text-[#16A34A]" />
              <p className="text-sm">Cargando proveedores…</p>
            </div>
          </div>
        </section>
      </AppLayout>
    )
  }

  /* — Error / empty state */
  if (isError && providers.length === 0) {
    return (
      <AppLayout>
        <section className="mx-auto max-w-4xl">
          <Stepper step={wizardStep} />
          <div className="rounded-2xl border border-[#E5E7EB] bg-white p-6 text-center shadow-sm">
            <p className="text-sm text-[#6B7280]">No se encontraron proveedores disponibles.</p>
          </div>
        </section>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <section className="mx-auto max-w-4xl">
        <Stepper step={wizardStep} />

        <div className="space-y-4">
          {providers.map((provider) => (
            <div
              key={provider.id}
              className="flex flex-col gap-4 rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between"
            >
              {/* Información del proveedor */}
              <div className="flex-1 space-y-2">
                <h3 className="text-lg font-semibold text-[#111827]">{provider.name}</h3>
                <p className="text-sm text-[#6B7280]">
                  Producto asociado: <span className="font-medium text-[#111827]">{provider.product_name}</span>
                </p>

                {/* Metadatos de contacto */}
                <div className="mt-3 flex flex-wrap gap-4 text-sm text-[#6B7280]">
                  {provider.phone && (
                    <span className="flex items-center gap-1.5">
                      <Phone className="h-4 w-4 text-[#16A34A]" />
                      {provider.phone}
                    </span>
                  )}
                  {provider.email && (
                    <span className="flex items-center gap-1.5">
                      <Mail className="h-4 w-4 text-[#16A34A]" />
                      {provider.email}
                    </span>
                  )}
                  {provider.location && (
                    <span className="flex items-center gap-1.5">
                      <MapPin className="h-4 w-4 text-[#16A34A]" />
                      {provider.location}
                    </span>
                  )}
                </div>
              </div>

              {/* Botonera de acción */}
              <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
                <button
                  type="button"
                  className="rounded-xl bg-[#16A34A] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#14532D]"
                >
                  Contactar
                </button>
                {provider.email && (
                  <a
                    href={`mailto:${provider.email}`}
                    className="inline-flex items-center justify-center rounded-xl border border-[#111827] bg-transparent px-4 py-2 text-sm font-semibold text-[#111827] transition hover:bg-[#F7F8F2]"
                  >
                    Enviar correo
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </AppLayout>
  )
}

export default CaseWizardStep4