import { useEffect, useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useNavigate, useParams } from 'react-router-dom'
import { AlertTriangle, Check, Leaf, Loader2, Search, Shield, Sparkles } from 'lucide-react'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { useWizardStore } from '@/stores/wizardStore'
import { CaseStepper, PageHeader, Panel, SynapButton } from '@/components/ui/prototype'
import { cn } from '@/lib/cn'
import {
  buildComparisonRows,
  buildProductComparisons,
  normalizeProviders,
  type NormalizedProvider,
  type ProviderPayload,
  type RecommendationData,
} from './recommendationMapper'

const DEMO_RECOMMENDATION: RecommendationData = {
  id: 0,
  ticket_id: 'demo',
  crop: 'Tomate',
  crop_stage: 'Floración',
  problem: 'Hongo en las hojas',
  status: 'completed',
  current_step: null,
  error_message: null,
  max_budget_per_liter: 10000,
  products: [
    {
      rank: 1,
      product_id: 1,
      nombre_comercial: 'FungiShield Pro',
      justification: 'Mejor opción para el contexto indicado por su alta eficacia sistémica contra hongos foliares en tomate.',
      dosis: '1.5 L/ha en aplicación foliar',
      precio_estimado: 10000,
      toxicidad: 'azul',
      intervalo_seguridad: 3,
      categoria: 'Fungicida Sistémico',
      cultivo_objetivo: 'Tomate',
      problema_objetivo: 'Hongo en las hojas',
      ventajas: ['Amplio espectro sistémico', 'Residualidad de 14 días', 'Registrado SFE para tomate'],
      riesgos: ['Respetar intervalo de seguridad de 3 días', 'Rotar modo de acción para evitar resistencia'],
      recomendacion_uso_general: 'Aplicar en las horas de menor temperatura. Usar equipo de protección personal (EPP) según etiqueta SFE.',
    },
    {
      rank: 2,
      product_id: 2,
      nombre_comercial: 'AgriProtect Plus',
      justification: 'Alternativa viable cuando se requiere producto de contacto con menor costo por hectárea.',
      dosis: '2 L/ha en aplicación foliar',
      precio_estimado: 7000,
      toxicidad: 'azul',
      intervalo_seguridad: 5,
      categoria: 'Fungicida de contacto',
      cultivo_objetivo: 'Tomate',
      problema_objetivo: 'Hongo en las hojas',
      ventajas: ['Precio accesible', 'Buen control preventivo', 'Compatible con otros fungicidas'],
      riesgos: ['Requiere mayor frecuencia de aplicación', 'Sensible al lavado por lluvia'],
      recomendacion_uso_general: 'Ideal como tratamiento preventivo antes de períodos lluviosos. Aplicar cada 7-10 días.',
    },
    {
      rank: 3,
      product_id: 3,
      nombre_comercial: 'EcoFungi Natural',
      justification: 'Opción orgánica con menor riesgo ambiental, apta para producción con certificación.',
      dosis: '3-4 aplicaciones semanales según severidad',
      precio_estimado: 10000,
      toxicidad: 'verde',
      intervalo_seguridad: 1,
      categoria: 'Fungicida orgánico',
      cultivo_objetivo: 'Tomate',
      problema_objetivo: 'Hongo en las hojas',
      ventajas: ['Banda verde (mínima toxicidad)', 'Intervalo de seguridad de 1 día', 'Apto para producción orgánica'],
      riesgos: ['Eficacia menor en infestaciones severas', 'Mayor frecuencia de aplicación necesaria'],
      recomendacion_uso_general: 'Usar en etapas tempranas o como complemento de un programa integrado. Consultar agrónomo certificado.',
    },
  ],
}

const DEMO_PROVIDERS: NormalizedProvider[] = normalizeProviders([
  {
    id: 1,
    nombre: 'AgroSuministros del Valle',
    product_id: 1,
    producto_asociado: 'FungiShield Pro',
    telefono: '2345 - 6789',
    correo: 'ventas@agrovalle.cr',
    ubicacion: 'Cartago, Pacayas',
  },
  {
    id: 2,
    nombre: 'Distribuidora Agrícola Central',
    product_id: 2,
    producto_asociado: 'AgriProtect Plus',
    telefono: '2345 - 6782',
    correo: 'info@agricentral.cr',
    ubicacion: 'Cartago, El Carmen',
  },
  {
    id: 3,
    nombre: 'Insumos Orgánicos La Esperanza',
    product_id: 3,
    producto_asociado: 'EcoFungi Natural',
    telefono: '2345 - 6783',
    correo: 'ventas@laesperanza.cr',
    ubicacion: 'Cartago, Taras',
  },
])

function getProgressInfo(status: string, step: string | null) {
  if (status === 'pending') return { percentage: 10, message: 'Iniciando pipeline de agentes...' }
  if (status === 'failed') return { percentage: 100, message: 'Error en el procesamiento' }
  if (status === 'completed') return { percentage: 100, message: 'Recomendaciones listas' }

  switch (step) {
    case 'context_analyzer':
      return { percentage: 25, message: 'Analizando contexto y condiciones del suelo...' }
    case 'researcher':
      return { percentage: 50, message: 'Buscando agroquímicos candidatos...' }
    case 'legal_validator':
      return { percentage: 75, message: 'Validando restricciones normativas...' }
    case 'synthesizer':
      return { percentage: 90, message: 'Generando recomendaciones finales...' }
    default:
      return { percentage: 15, message: 'Procesando caso agrícola...' }
  }
}

function toneIcon(tone: 'ok' | 'warning' | 'muted') {
  if (tone === 'ok') return <Check className="h-4 w-4 text-[#16A34A]" />
  if (tone === 'warning') return <AlertTriangle className="h-4 w-4 text-[#F59E0B]" />
  return <span className="h-4 w-4 rounded-full bg-[#E5E7EB]" />
}

function badgeClass(color: 'green' | 'blue' | 'amber') {
  if (color === 'green') return 'bg-[#16A34A] text-white'
  if (color === 'blue') return 'bg-[#4F46E5] text-white'
  return 'bg-[#F59E0B] text-white'
}

function ProductCard({ product }: { product: ReturnType<typeof buildProductComparisons>[number] }) {
  return (
    <Panel className="relative min-h-[330px] p-7">
      <span className={cn('absolute right-6 top-6 rounded-full px-5 py-2 text-sm font-bold', badgeClass(product.badgeColor))}>
        {product.badge}
      </span>
      <h3 className="mt-12 text-2xl font-bold text-[#111827]">{product.name}</h3>
      {product.registrante && product.registrante !== 'No disponible' && (
        <p className="mt-1.5 text-base font-semibold text-[#6B7280]">Registrante: {product.registrante}</p>
      )}
      <dl className="mt-5 space-y-4 text-xl leading-7">
        <div>
          <dt className="font-semibold text-[#6B7280]">Tipo</dt>
          <dd className="text-[#111827]">{product.type}</dd>
        </div>
        <div>
          <dt className="font-semibold text-[#6B7280]">Compatibilidad con el cultivo</dt>
          <dd className="text-[#111827]">{product.compatibility}</dd>
        </div>
        <div>
          <dt className="font-semibold text-[#6B7280]">Precio estimado</dt>
          <dd className="text-[#111827]">{product.price}</dd>
        </div>
        <div>
          <dt className="font-semibold text-[#6B7280]">Disponibilidad</dt>
          <dd className="text-[#111827]">{product.availability}</dd>
        </div>
      </dl>
    </Panel>
  )
}

export function CaseWizardStep3() {
  const token = useAuthStore((state) => state.token)
  const setStep = useWizardStore((state) => state.setStep)
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const isDemo = !id || id === 'demo'  // modo demo: muestra datos de ejemplo sin backend

  useEffect(() => {
    setStep(3)
  }, [setStep])

  const {
    data: recommendation,
    isLoading,
    isError,
  } = useQuery<RecommendationData>({
    queryKey: ['recommendation', id],
    queryFn: async () => {
      if (isDemo) return DEMO_RECOMMENDATION
      const response = await axios.get(`/api/v1/recommendations/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    enabled: isDemo || !!token,
  })

  // Los proveedores solo se piden cuando la recomendacion ya esta completa
  const { data: providersPayload = [] } = useQuery<ProviderPayload[]>({
    queryKey: ['providers', id],
    queryFn: async () => {
      if (isDemo) return []
      const response = await axios.get(`/api/v1/recommendations/${id}/providers`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    enabled: !!token && !isDemo && recommendation?.status === 'completed',
  })

  const providers = useMemo(
    () => (isDemo ? DEMO_PROVIDERS : normalizeProviders(providersPayload)),
    [isDemo, providersPayload],
  )

  const [pipelineState, setPipelineState] = useState<{
    status: string
    current_step: string | null
    error_message: string | null
  } | null>(null)

  useEffect(() => {
    if (isDemo) return // en demo, el estado lo maneja la animacion simulada de abajo
    if (recommendation) {
      setPipelineState({
        status: recommendation.status,
        current_step: recommendation.current_step,
        error_message: recommendation.error_message,
      })
    }
  }, [recommendation, isDemo])

  // Modo demo (sales pitch): simula el avance de los 4 agentes en ~2s y luego muestra
  // las recomendaciones falsas, sin llamar al backend ni esperar al pipeline real.
  useEffect(() => {
    if (!isDemo) return
    const steps = ['context_analyzer', 'researcher', 'legal_validator', 'synthesizer']
    setPipelineState({ status: 'processing', current_step: steps[0], error_message: null })
    const timers = steps.map((step, i) =>
      window.setTimeout(() => {
        setPipelineState({ status: 'processing', current_step: step, error_message: null })
      }, i * 500),
    )
    timers.push(
      window.setTimeout(() => {
        setPipelineState({ status: 'completed', current_step: null, error_message: null })
      }, steps.length * 500),
    )
    return () => timers.forEach((t) => clearTimeout(t))
  }, [isDemo])

  // Mientras la recomendacion esta pending/processing, consulta el detalle cada segundo
  // (polling) y actualiza el cache; se detiene en cuanto pasa a completed/failed.
  useEffect(() => {
    if (isDemo || !id || !token || !recommendation) return
    if (recommendation.status !== 'pending' && recommendation.status !== 'processing') return

    const interval = setInterval(() => {
      void axios
        .get(`/api/v1/recommendations/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((response) => {
          queryClient.setQueryData(['recommendation', id], response.data)  // refresca la UI
        })
        .catch(() => undefined)
    }, 1000)

    return () => clearInterval(interval)  // limpia el intervalo al desmontar o cambiar de estado
  }, [id, token, isDemo, recommendation, queryClient])

  if (isLoading) {
    return (
      <AppLayout>
        <section className="max-w-[1140px]">
          <CaseStepper step={3} />
          <Panel className="flex min-h-[360px] items-center justify-center p-10">
            <div className="flex flex-col items-center gap-4 text-[#6B7280]">
              <Loader2 className="h-12 w-12 animate-spin text-[#16A34A]" />
              <p className="text-lg font-semibold">Buscando ticket de recomendación...</p>
            </div>
          </Panel>
        </section>
      </AppLayout>
    )
  }

  if (isError && !isDemo) {
    return (
      <AppLayout>
        <section className="max-w-[1140px]">
          <PageHeader
            title="Recomendaciones de productos"
            subtitle="Revise las opciones recomendadas basadas en su contexto"
            className="mb-5"
          />
          <CaseStepper step={3} />
          <Panel className="p-10 text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-[#DC2626]" />
            <h2 className="mt-4 text-2xl font-bold text-[#111827]">No se pudo cargar la recomendación</h2>
            <p className="mt-2 text-lg text-[#6B7280]">Verifique su conexión o el ticket de recomendación.</p>
          </Panel>
        </section>
      </AppLayout>
    )
  }

  if (pipelineState?.status === 'pending' || pipelineState?.status === 'processing') {
    const progress = getProgressInfo(pipelineState.status, pipelineState.current_step)
    const steps = [
      { key: 'context_analyzer', name: 'Analizador de contexto', icon: Sparkles },
      { key: 'researcher', name: 'Investigador RAG', icon: Search },
      { key: 'legal_validator', name: 'Validador legal', icon: Shield },
      { key: 'synthesizer', name: 'Sintetizador IA', icon: Leaf },
    ]

    return (
      <AppLayout>
        <section className="max-w-[1140px]">
          <PageHeader
            title="Recomendaciones de productos"
            subtitle="Revise las opciones recomendadas basadas en su contexto"
            className="mb-5"
          />
          <CaseStepper step={3} />
          <Panel className="p-10">
            <div className="text-center">
              <Leaf className="mx-auto h-14 w-14 animate-pulse text-[#16A34A]" />
              <h1 className="mt-4 text-3xl font-bold text-[#111827]">Motor de agentes IA ejecutándose</h1>
              <p className="mt-3 text-lg text-[#6B7280]">{progress.message}</p>
            </div>
            <div className="mt-10">
              <div className="mb-3 flex items-center justify-between text-lg font-bold">
                <span className="text-[#16A34A]">Progreso</span>
                <span>{progress.percentage}%</span>
              </div>
              <div className="h-4 overflow-hidden rounded-full bg-[#E5E7EB]">
                <div className="h-full rounded-full bg-[#16A34A]" style={{ width: `${progress.percentage}%` }} />
              </div>
            </div>
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {steps.map((step) => {
                const Icon = step.icon
                const active = pipelineState.current_step === step.key
                return (
                  <div
                    key={step.key}
                    className={cn('rounded-xl border p-5', active ? 'border-[#16A34A] bg-[#F0FDF4]' : 'border-[#E5E7EB] bg-white')}
                  >
                    <Icon className={cn('h-6 w-6', active ? 'text-[#16A34A]' : 'text-[#6B7280]')} />
                    <p className="mt-3 text-lg font-bold text-[#111827]">{step.name}</p>
                  </div>
                )
              })}
            </div>
          </Panel>
        </section>
      </AppLayout>
    )
  }

  if (pipelineState?.status === 'failed') {
    return (
      <AppLayout>
        <section className="max-w-[1140px]">
          <PageHeader
            title="Recomendaciones de productos"
            subtitle="Revise las opciones recomendadas basadas en su contexto"
            className="mb-5"
          />
          <CaseStepper step={3} />
          <Panel className="border-[#FCA5A5] bg-[#FEF2F2] p-10 text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-[#DC2626]" />
            <h1 className="mt-4 text-2xl font-bold text-[#991B1B]">Fallo en el pipeline de agentes</h1>
            <p className="mt-3 text-lg text-[#7F1D1D]">{pipelineState.error_message || 'Fallo general sin mensaje.'}</p>
          </Panel>
        </section>
      </AppLayout>
    )
  }

  const providerList = isDemo ? DEMO_PROVIDERS : providers
  const products = buildProductComparisons(
    recommendation ?? DEMO_RECOMMENDATION,
    providerList,
  )
  const rows = buildComparisonRows(products)

  return (
    <AppLayout>
      <section className="max-w-[1140px]">
        <PageHeader
          title="Recomendaciones de productos"
          subtitle="Revise las opciones recomendadas basadas en su contexto"
          className="mb-5"
        />
        <CaseStepper step={3} />

        {products.length === 0 ? (
          <Panel className="p-10 text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-[#F59E0B]" />
            <h2 className="mt-4 text-2xl font-bold text-[#111827]">No se encontraron productos recomendados</h2>
            <p className="mt-2 text-lg text-[#6B7280]">
              El motor completó el análisis, pero no encontró productos compatibles para el caso.
            </p>
          </Panel>
        ) : (
          <>
            <div className="grid gap-7 lg:grid-cols-3">
              {products.map((product) => (
                <ProductCard key={product.productId} product={product} />
              ))}
            </div>

            <div className="mt-9 grid gap-7 lg:grid-cols-3">
              {products.map((product) => (
                <Panel key={product.productId} className="p-6 flex flex-col gap-4">
                  {/* Justificación del agente */}
                  <div className="border-b border-[#F3F4F6] pb-4">
                    <p className="text-sm italic text-[#4B5563] leading-relaxed break-words whitespace-pre-wrap">
                      &ldquo;{product.justification}&rdquo;
                    </p>
                  </div>

                  {/* Ventajas */}
                  {product.ventajas.length > 0 && (
                    <div>
                      <p className="mb-1.5 text-xs font-bold uppercase tracking-wide text-[#16A34A]">Ventajas</p>
                      <ul className="space-y-1">
                        {product.ventajas.map((v, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-xs text-[#374151]">
                            <Check className="mt-0.5 h-3 w-3 shrink-0 text-[#16A34A]" />
                            {v}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Riesgos */}
                  {product.riesgos.length > 0 && (
                    <div>
                      <p className="mb-1.5 text-xs font-bold uppercase tracking-wide text-[#F59E0B]">Riesgos</p>
                      <ul className="space-y-1">
                        {product.riesgos.map((r, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-xs text-[#374151]">
                            <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-[#F59E0B]" />
                            {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recomendación de uso */}
                  {product.recomendacion_uso_general && (
                    <div className="rounded-lg bg-[#F0FDF4] p-3">
                      <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#166534]">Uso recomendado</p>
                      <p className="text-xs text-[#166534] leading-relaxed">{product.recomendacion_uso_general}</p>
                    </div>
                  )}

                  {/* Datos técnicos */}
                  <div className="space-y-2 border-t border-[#F3F4F6] pt-3 text-xs text-[#6B7280]">
                    <div className="flex justify-between">
                      <span>Dosis:</span>
                      <span className="font-semibold text-[#374151]">{product.dosis || 'No disponible'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Precio Est.:</span>
                      <span className="font-semibold text-[#374151]">
                        {product.precio_estimado !== undefined && product.precio_estimado !== null
                          ? `${product.precio_estimado.toLocaleString('es-CR')} ₡`
                          : 'No disponible'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Plazo de espera:</span>
                      <span className="font-semibold text-[#374151]">
                        {product.intervalo_seguridad !== undefined && product.intervalo_seguridad !== null
                          ? `${product.intervalo_seguridad} días`
                          : 'No aplica'}
                      </span>
                    </div>
                  </div>
                </Panel>
              ))}
            </div>

            {products.length > 0 && (
              <Panel className="mt-9 p-7">
                <h2 className="mb-4 text-xl font-bold text-[#111827]">Tabla comparativa</h2>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[820px] border-collapse text-left text-base">
                    <thead>
                      <tr className="border-b border-[#E5E7EB]">
                        <th className="py-3 pr-4 font-bold text-[#111827]">Producto</th>
                        {products.map((product) => (
                          <th key={product.productId} className="px-4 py-3 font-bold text-[#111827]">
                            {product.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row) => (
                        <tr key={row.label} className="border-b border-[#E5E7EB] last:border-b-0">
                          <td className="py-3 pr-4 text-[#111827]">{row.label}</td>
                          {row.values.map((cell, index) => (
                            <td key={`${row.label}-${index}`} className="px-4 py-3 text-[#111827]">
                              <span className="inline-flex items-center gap-2">
                                {toneIcon(cell.tone)}
                                {cell.value}
                              </span>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-8 flex justify-center">
                  <SynapButton className="min-w-[330px]" onClick={() => navigate(`/recommendations/${id ?? 'demo'}/providers`)}>
                    Ver proveedores
                  </SynapButton>
                </div>
              </Panel>
            )}
          </>
        )}
      </section>
    </AppLayout>
  )
}

export default CaseWizardStep3