import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useNavigate, useParams } from 'react-router-dom'
import { Check, AlertTriangle, Leaf } from 'lucide-react'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { useWizardStore } from '@/stores/wizardStore'
import { cn } from '@/lib/cn'

/* ──────────────────────────────────────────────
   Tipos
   ────────────────────────────────────────────── */

interface Product {
  name: string
  badge_label: string
  badge_variant: 'best' | 'alternative' | 'economic'
}

interface ComparisonRow {
  criteria: string
  product1: boolean | string
  product2: boolean | string
  product3: boolean | string
}

interface RecommendationData {
  id: string
  products: Product[]
  comparison_table: ComparisonRow[]
}

/* ── Demo data (para visualización sin backend) ── */
const DEMO_RECOMMENDATION: RecommendationData = {
  id: 'demo',
  products: [
    { name: 'FungiShield Pro', badge_label: 'Mejor opción', badge_variant: 'best' },
    { name: 'AgriProtect Plus', badge_label: 'Alternativa viable', badge_variant: 'alternative' },
    { name: 'EcoFungi Natural', badge_label: 'Más económico', badge_variant: 'economic' },
  ],
  comparison_table: [
    { criteria: 'Trata hongo en hojas', product1: true, product2: true, product3: true },
    { criteria: 'Dentro del presupuesto', product1: true, product2: false, product3: true },
    { criteria: 'Disponible localmente', product1: true, product2: true, product3: false },
    { criteria: 'Riesgo ambiental', product1: 'Bajo', product2: 'Medio', product3: 'Alto' },
    { criteria: 'Efectividad comprobada', product1: true, product2: true, product3: 'Advertencia' },
  ],
}

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
   Badge
   ────────────────────────────────────────────── */

function Badge({ label, variant }: { label: string; variant: Product['badge_variant'] }) {
  const styles: Record<Product['badge_variant'], string> = {
    best: 'bg-[#16A34A] text-white',
    alternative: 'bg-[#3B82F6] text-white',
    economic: 'bg-[#F59E0B] text-white',
  }
  return (
    <span className={cn('inline-block rounded-full px-3 py-0.5 text-xs font-semibold', styles[variant])}>
      {label}
    </span>
  )
}

/* ──────────────────────────────────────────────
   Componente principal
   ────────────────────────────────────────────── */

export function CaseWizardStep3() {
  const token = useAuthStore((s) => s.token)
  const wizardStep = useWizardStore((s) => s.step)
  const ticketId = useWizardStore((s) => s.data.ticket_id)
  const setStep = useWizardStore((s) => s.setStep)
  const navigate = useNavigate()

  const isDemo = ticketId === 'demo' || !ticketId

  const {
    data: recommendation,
    isLoading,
    isError,
  } = useQuery<RecommendationData>({
    queryKey: ['recommendation', ticketId],
    queryFn: async () => {
      if (isDemo) return DEMO_RECOMMENDATION
      const res = await axios.get(`/api/v1/recommendations/${ticketId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return res.data
    },
    enabled: !!token && !!ticketId,
  })

  const handleGoToProviders = () => {
    setStep(4)
    navigate(`/recommendations/${ticketId}/providers`)
  }

  const effectiveRecommendation = recommendation || (isDemo ? DEMO_RECOMMENDATION : null)

  /* — Loading state */
  if (isLoading) {
    return (
      <AppLayout>
        <section className="mx-auto max-w-5xl">
          <Stepper step={wizardStep} />
          <div className="flex items-center justify-center py-24">
            <div className="flex flex-col items-center gap-3 text-[#6B7280]">
              <Leaf className="h-8 w-8 animate-pulse text-[#16A34A]" />
              <p className="text-sm">Cargando recomendaciones…</p>
            </div>
          </div>
        </section>
      </AppLayout>
    )
  }

  /* — Error state */
  if (isError && !effectiveRecommendation) {
    return (
      <AppLayout>
        <section className="mx-auto max-w-5xl">
          <Stepper step={wizardStep} />
          <div className="rounded-2xl border border-[#E5E7EB] bg-white p-6 text-center shadow-sm">
            <AlertTriangle className="mx-auto h-10 w-10 text-[#F59E0B]" />
            <p className="mt-3 text-sm text-[#6B7280]">
              No pudimos cargar las recomendaciones. Intente de nuevo más tarde.
            </p>
          </div>
        </section>
      </AppLayout>
    )
  }

  const data = effectiveRecommendation
  const products = data?.products ?? []
  const tableRows = data?.comparison_table ?? []

  /* ── Product badges ── */
  const variantForIndex = (i: number): Product['badge_variant'] => {
    if (i === 0) return 'best'
    if (i === 1) return 'alternative'
    return 'economic'
  }

  return (
    <AppLayout>
      <section className="mx-auto max-w-5xl">
        <Stepper step={wizardStep} />

        {/* ====== Tarjetas de productos ====== */}
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((product, i) => (
            <div
              key={product.name}
              className="flex flex-col items-center rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-sm"
            >
              <Badge label={product.badge_label} variant={variantForIndex(i)} />
              <h3 className="mt-4 text-lg font-semibold text-[#111827]">{product.name}</h3>
            </div>
          ))}
        </div>

        {/* ====== Tabla comparativa ====== */}
        <div className="overflow-x-auto rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-[#111827]">Comparativa de productos</h2>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#E5E7EB]">
                <th className="pb-3 pr-4 font-medium text-[#6B7280]">Criterio</th>
                {products.map((p) => (
                  <th key={p.name} className="pb-3 px-4 font-medium text-[#111827]">
                    {p.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row, ri) => (
                <tr key={ri} className="border-b border-[#E5E7EB] last:border-b-0">
                  <td className="py-3 pr-4 text-[#111827]">{row.criteria}</td>
                  {[row.product1, row.product2, row.product3].map((val, ci) => (
                    <td key={ci} className="py-3 px-4">
                      {typeof val === 'boolean' ? (
                        val ? (
                          <Check className="h-5 w-5 text-[#16A34A]" />
                        ) : (
                          <span className="text-[#D1D5DB]">—</span>
                        )
                      ) : (
                        <span className={cn(val === '⚠️' || val === 'Advertencia' ? 'text-[#F59E0B]' : 'text-[#111827]')}>
                          {val}
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* ====== Botón de transición ====== */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={handleGoToProviders}
            className="rounded-xl bg-[#16A34A] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#14532D]"
          >
            Ver proveedores
          </button>
        </div>
      </section>
    </AppLayout>
  )
}

export default CaseWizardStep3