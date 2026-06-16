import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useNavigate, useParams } from 'react-router-dom'
import { Check, AlertTriangle, Leaf, Shield, Search, Sparkles, Loader2, ArrowLeft } from 'lucide-react'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { useWizardStore } from '@/stores/wizardStore'
import { cn } from '@/lib/cn'

/* ──────────────────────────────────────────────
   Tipos
   ────────────────────────────────────────────── */

interface ProductDetail {
  rank: number
  product_id: number
  nombre_comercial: string
  justification: string
  dosis: string | null
  precio_estimado: number | null
  toxicidad: string | null
  intervalo_seguridad: number | null
}

interface RecommendationData {
  id: number
  ticket_id: string
  crop: string
  crop_stage: string
  problem: string
  status: string
  current_step: string | null
  error_message: string | null
  products: ProductDetail[]
}

/* ── Demo data (para visualización sin backend) ── */
const DEMO_RECOMMENDATION: RecommendationData = {
  id: 0,
  ticket_id: 'demo',
  crop: 'Tomate',
  crop_stage: 'Floración',
  problem: 'Mosca blanca',
  status: 'completed',
  current_step: null,
  error_message: null,
  products: [
    {
      rank: 1,
      product_id: 1,
      nombre_comercial: 'FungiShield Pro',
      justification: 'Excelente insecticida con amplio espectro que controla efectivamente la mosca blanca en etapas de floración sin afectar los polinizadores locales.',
      dosis: '1.5 cc / litro de agua',
      precio_estimado: 12500,
      toxicidad: 'verde',
      intervalo_seguridad: 3,
    },
    {
      rank: 2,
      product_id: 2,
      nombre_comercial: 'AgriProtect Plus',
      justification: 'Alternativa viable de contacto rápido. Recomendado para reducir poblaciones densas de plagas antes de la cosecha.',
      dosis: '2.0 cc / litro de agua',
      precio_estimado: 18000,
      toxicidad: 'azul',
      intervalo_seguridad: 5,
    },
    {
      rank: 3,
      product_id: 3,
      nombre_comercial: 'EcoFungi Natural',
      justification: 'Opción orgánica de bajo costo con extractos botánicos. Ideal para agricultura sostenible o manejo integrado de plagas.',
      dosis: '3.0 cc / litro de agua',
      precio_estimado: 8500,
      toxicidad: 'verde',
      intervalo_seguridad: 1,
    },
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
            <div className="text-sm font-medium text-[#374151]">{label}</div>
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
   Progreso del Pipeline (Helpers)
   ────────────────────────────────────────────── */

interface ProgressInfo {
  percentage: number
  message: string
}

function getProgressInfo(status: string, step: string | null): ProgressInfo {
  if (status === 'pending') {
    return { percentage: 10, message: 'Iniciando pipeline de agentes...' }
  }
  if (status === 'failed') {
    return { percentage: 100, message: 'Error en el procesamiento' }
  }
  if (status === 'completed') {
    return { percentage: 100, message: 'Recomendaciones listas' }
  }

  switch (step) {
    case 'context_analyzer':
      return { percentage: 25, message: 'Agente 1: Analizando contexto y condiciones del suelo...' }
    case 'researcher':
      return { percentage: 50, message: 'Agente 2: Buscando agroquímicos candidatos en el catálogo...' }
    case 'legal_validator':
      return { percentage: 75, message: 'Agente 3: Validando restricciones normativas con el SFE...' }
    case 'synthesizer':
      return { percentage: 90, message: 'Agente 4: Generando justificaciones finales...' }
    default:
      return { percentage: 15, message: 'Procesando caso agrícola...' }
  }
}

const getToxicBandBadge = (band: string | null | undefined) => {
  if (!band) return null
  const b = band.toLowerCase()
  const labels: Record<string, string> = {
    roja: 'Extremadamente Tóxico (Banda Roja)',
    amarilla: 'Altamente Tóxico (Banda Amarilla)',
    azul: 'Moderadamente Tóxico (Banda Azul)',
    verde: 'Ligeramente Tóxico (Banda Verde)',
    no_aplica: 'No Aplica',
  }
  const styles: Record<string, string> = {
    roja: 'bg-red-100 text-red-800 border-red-200',
    amarilla: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    azul: 'bg-blue-100 text-blue-800 border-blue-200',
    verde: 'bg-green-100 text-green-800 border-green-200',
    no_aplica: 'bg-gray-100 text-gray-800 border-gray-200',
  }
  return (
    <span className={cn('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold shadow-sm', styles[b] || 'bg-gray-100 text-gray-800 border-gray-200')}>
      {labels[b] || band}
    </span>
  )
}

/* ──────────────────────────────────────────────
   Componente principal
   ────────────────────────────────────────────── */

export function CaseWizardStep3() {
  const token = useAuthStore((s) => s.token)
  const wizardStep = useWizardStore((s) => s.step)
  const setStep = useWizardStore((s) => s.setStep)
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const isDemo = !id || id === 'demo'

  // Query principal para detalles de la recomendación
  const {
    data: recommendation,
    isLoading,
    isError,
  } = useQuery<RecommendationData>({
    queryKey: ['recommendation', id],
    queryFn: async () => {
      console.log('[CaseWizardStep3] useQuery: Fetching recommendation details from API. ID:', id, 'isDemo:', isDemo)
      if (isDemo) {
        console.log('[CaseWizardStep3] Returning DEMO_RECOMMENDATION')
        return DEMO_RECOMMENDATION
      }
      const res = await axios.get(`/api/v1/recommendations/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      console.log('[CaseWizardStep3] API raw response data:', res.data)
      return res.data
    },
    enabled: !!token && !isDemo,
  })

  // Sincronizar estado local del pipeline con la respuesta del backend
  const [pipelineState, setPipelineState] = useState<{
    status: string
    current_step: string | null
    error_message: string | null
  } | null>(null)

  useEffect(() => {
    if (recommendation) {
      console.log('[CaseWizardStep3] Syncing local pipelineState from query cache:', {
        status: recommendation.status,
        current_step: recommendation.current_step,
        error_message: recommendation.error_message,
        productsCount: recommendation.products?.length ?? 0
      })
      setPipelineState({
        status: recommendation.status,
        current_step: recommendation.current_step,
        error_message: recommendation.error_message,
      })
    }
  }, [recommendation])

  // Polling activo cada 1 segundo (1000 ms) mientras la recomendación se esté procesando.
  // Lee 'current_step' y 'status' para avanzar la barra de progreso en tiempo real.
  useEffect(() => {
    if (isDemo || !id || !token) {
      console.log('[CaseWizardStep3] Polling bypassed. Reason:', { isDemo, hasId: !!id, hasToken: !!token })
      return
    }
    if (!recommendation) {
      console.log('[CaseWizardStep3] Polling waiting: recommendation data not loaded yet.')
      return
    }
    if (recommendation.status !== 'pending' && recommendation.status !== 'processing') {
      console.log('[CaseWizardStep3] Polling skipped: status is already final:', recommendation.status)
      return
    }

    console.log('[CaseWizardStep3] Setting up active polling interval (1s) to track pipeline steps.')
    const poll = async () => {
      try {
        console.log(`[CaseWizardStep3] Polling: GET /api/v1/recommendations/${id}...`)
        const res = await axios.get(`/api/v1/recommendations/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        const data = res.data
        console.log('[CaseWizardStep3] Poll result:', {
          status: data.status,
          current_step: data.current_step,
          productsCount: data.products?.length ?? 0
        })
        
        // Si hay un cambio en el estado, en el agente actual (current_step) o en la cantidad de productos,
        // actualizamos la query cache directamente para evitar loops de refetch/cancelación por la alta frecuencia.
        const hasStatusChanged = data.status !== recommendation.status
        const hasStepChanged = data.current_step !== recommendation.current_step
        const hasProductsChanged = (data.products?.length ?? 0) !== (recommendation.products?.length ?? 0)

        if (hasStatusChanged || hasStepChanged || hasProductsChanged) {
          console.log('[CaseWizardStep3] Transition detected! Updating React Query cache directly:', {
            oldStatus: recommendation.status,
            newStatus: data.status,
            oldStep: recommendation.current_step,
            newStep: data.current_step,
            oldProductsCount: recommendation.products?.length ?? 0,
            newProductsCount: data.products?.length ?? 0
          })
          queryClient.setQueryData(['recommendation', id], data)
        }
      } catch (err) {
        console.warn('[CaseWizardStep3] Error in background status polling:', err)
      }
    }

    const interval = setInterval(poll, 1000)
    return () => {
      console.log('[CaseWizardStep3] Cleaning up active polling interval.')
      clearInterval(interval)
    }
  }, [id, token, isDemo, recommendation, queryClient])

  // Log simple para cada render en la consola
  console.log('[CaseWizardStep3] Rendering state:', {
    isLoading,
    isError,
    recStatus: recommendation?.status,
    recStep: recommendation?.current_step,
    localStatus: pipelineState?.status,
    localStep: pipelineState?.current_step,
    productsCount: recommendation?.products?.length ?? 0
  })

  const handleGoToProviders = () => {
    console.log('[CaseWizardStep3] Navigating to providers. Rec ID:', id)
    setStep(4)
    navigate(`/recommendations/${id}/providers`)
  }

  /* — Estado de carga inicial (GET request) */
  if (isLoading) {
    console.log('[CaseWizardStep3] Rendering Loader screen...')
    return (
      <AppLayout>
        <section className="mx-auto max-w-5xl px-4 py-8">
          <Stepper step={wizardStep} />
          <div className="flex items-center justify-center py-24">
            <div className="flex flex-col items-center gap-3 text-[#6B7280]">
              <Loader2 className="h-10 w-10 animate-spin text-[#16A34A]" />
              <p className="text-sm font-medium">Buscando ticket de recomendación...</p>
            </div>
          </div>
        </section>
      </AppLayout>
    )
  }

  /* — Estado de error general */
  if (isError && !isDemo) {
    console.log('[CaseWizardStep3] Rendering Error screen...')
    return (
      <AppLayout>
        <section className="mx-auto max-w-5xl px-4 py-8">
          <Stepper step={wizardStep} />
          <div className="rounded-2xl border border-[#FCA5A5] bg-[#FEF2F2] p-8 text-center shadow-md">
            <AlertTriangle className="mx-auto h-12 w-12 text-[#EF4444]" />
            <h2 className="mt-3 text-lg font-semibold text-[#991B1B]">No se pudo cargar la recomendación</h2>
            <p className="mt-1 text-sm text-[#7F1D1D]">
              Verifique su conexión de red o que el ticket de recomendación sea el correcto.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="mt-6 inline-flex items-center gap-2 rounded-xl border border-[#D1D5DB] bg-white px-5 py-2.5 text-sm font-semibold text-[#374151] shadow-sm transition hover:bg-[#F9FAFB]"
            >
              <ArrowLeft className="h-4 w-4" /> Volver al Inicio
            </button>
          </div>
        </section>
      </AppLayout>
    )
  }

  /* — Pantalla de progreso del pipeline (SSE escuchando activamente) */
  if (pipelineState?.status === 'pending' || pipelineState?.status === 'processing') {
    const progressInfo = getProgressInfo(pipelineState.status, pipelineState.current_step)
    const stepsOrder = ['context_analyzer', 'researcher', 'legal_validator', 'synthesizer']
    const currentStepIdx = pipelineState.current_step ? stepsOrder.indexOf(pipelineState.current_step) : -1

    console.log('[CaseWizardStep3] Rendering Progress screen. Info:', {
      percentage: progressInfo.percentage,
      message: progressInfo.message,
      step: pipelineState.current_step,
      idx: currentStepIdx
    })

    const stepsList = [
      { key: 'context_analyzer', name: 'Analizador de Contexto', desc: 'Estructurando datos agronómicos y ambientales', icon: Sparkles },
      { key: 'researcher', name: 'Investigador RAG', desc: 'Buscando productos candidatos compatibles en el catálogo SFE', icon: Search },
      { key: 'legal_validator', name: 'Validador Legal', desc: 'Cruzando candidatos con las regulaciones de agroquímicos del MAG', icon: Shield },
      { key: 'synthesizer', name: 'Sintetizador IA', desc: 'Estructurando dosis, precios y redactando justificaciones finales', icon: Leaf },
    ]

    return (
      <AppLayout>
        <section className="mx-auto max-w-3xl px-4 py-8">
          <Stepper step={2} />
          
          <div className="rounded-3xl border border-[#E5E7EB] bg-white p-8 shadow-xl">
            {/* Header animation */}
            <div className="flex flex-col items-center text-center mb-8">
              <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-[#E8F5E9] text-[#16A34A] mb-4 shadow-inner">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#16A34A]/10 opacity-75"></span>
                <Leaf className="h-10 w-10 animate-pulse" />
              </div>
              <h1 className="text-2xl font-bold text-[#111827]">Motor de Agentes IA Ejecutándose</h1>
              <p className="mt-2 text-sm text-[#6B7280]">
                Procesando el caso para {recommendation?.crop} ({recommendation?.crop_stage}) ante el problema de {recommendation?.problem}.
              </p>
            </div>

            {/* Progress Bar */}
            <div className="mb-10">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-[#16A34A]">{progressInfo.message}</span>
                <span className="text-sm font-bold text-[#111827]">{progressInfo.percentage}%</span>
              </div>
              <div className="h-3 w-full rounded-full bg-[#F3F4F6] overflow-hidden border border-[#E5E7EB] shadow-inner">
                <div 
                  className="h-full rounded-full bg-gradient-to-r from-[#16A34A] via-[#10B981] to-[#34D399] transition-all duration-500 ease-out"
                  style={{ width: `${progressInfo.percentage}%` }}
                />
              </div>
            </div>

            {/* Pipeline Step Tracker */}
            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#9CA3AF] mb-3">Workflow del Pipeline</h3>
              {stepsList.map((stepItem, i) => {
                const isCompleted = pipelineState.status === 'completed' || currentStepIdx > i
                const isActive = pipelineState.status === 'processing' && currentStepIdx === i
                const IconComponent = stepItem.icon

                return (
                  <div 
                    key={stepItem.key} 
                    className={cn(
                      "flex items-start gap-4 p-4 rounded-2xl border transition-all duration-300",
                      isActive 
                        ? "border-[#16A34A] bg-[#F0FDF4] shadow-md shadow-[#16A34A]/5 scale-[1.01]" 
                        : isCompleted 
                        ? "border-[#E5E7EB] bg-[#F9FAFB] opacity-80" 
                        : "border-[#F3F4F6] bg-white opacity-40"
                    )}
                  >
                    <div 
                      className={cn(
                        "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors duration-300",
                        isCompleted 
                          ? "bg-[#16A34A] text-white" 
                          : isActive 
                          ? "bg-[#16A34A] text-white animate-pulse" 
                          : "bg-[#F3F4F6] text-[#9CA3AF]"
                      )}
                    >
                      {isCompleted ? <Check className="h-5 w-5" /> : <IconComponent className="h-5 w-5" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-center">
                        <h4 className={cn("text-base font-semibold", isActive ? "text-[#15803D]" : "text-[#111827]")}>
                          {stepItem.name}
                        </h4>
                        {isActive && (
                          <span className="flex items-center gap-1 text-xs font-semibold text-[#16A34A]">
                            <Loader2 className="h-3 w-3 animate-spin" /> Procesando
                          </span>
                        )}
                        {isCompleted && (
                          <span className="text-xs font-semibold text-[#16A34A]">Listo</span>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-[#6B7280]">{stepItem.desc}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>
      </AppLayout>
    )
  }

  /* — Pantalla de falla del pipeline */
  if (pipelineState?.status === 'failed') {
    console.log('[CaseWizardStep3] Rendering Pipeline Failure screen. Error message:', pipelineState.error_message)
    return (
      <AppLayout>
        <section className="mx-auto max-w-xl px-4 py-8">
          <Stepper step={2} />
          
          <div className="rounded-3xl border border-[#FCA5A5] bg-[#FEF2F2] p-8 shadow-xl text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#FEE2E2] text-[#EF4444] mb-4 shadow-sm">
              <AlertTriangle className="h-8 w-8" />
            </div>
            <h1 className="text-xl font-bold text-[#991B1B]">Fallo en el Pipeline de Agentes</h1>
            <p className="mt-2 text-sm text-[#7F1D1D] mb-6">
              El pipeline no pudo finalizar exitosamente. Esto suele suceder por límites de cuota de la API del LLM o datos incompletos.
            </p>
            <div className="rounded-2xl bg-white p-4 text-left border border-[#FCA5A5]/30 mb-8 max-h-48 overflow-y-auto font-mono text-xs text-[#991B1B] break-words shadow-inner">
              <strong>Error:</strong>
              <p className="mt-1 whitespace-pre-wrap">{pipelineState.error_message || 'Fallo general sin mensaje.'}</p>
            </div>
            
            <div className="flex justify-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="flex items-center gap-2 rounded-xl border border-[#D1D5DB] bg-white px-5 py-2.5 text-sm font-semibold text-[#374151] shadow-sm transition hover:bg-[#F9FAFB]"
              >
                <ArrowLeft className="h-4 w-4" /> Ir al Dashboard
              </button>
              <button
                onClick={() => {
                  console.log('[CaseWizardStep3] Retry clicked. Invalidating recommendation query.')
                  queryClient.invalidateQueries({ queryKey: ['recommendation', id] })
                  setPipelineState({ status: 'pending', current_step: null, error_message: null })
                }}
                className="rounded-xl bg-[#EF4444] px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#B91C1C]"
              >
                Reintentar Carga
              </button>
            </div>
          </div>
        </section>
      </AppLayout>
    )
  }

  /* — Pantalla de éxito (Visualización de recomendaciones de productos) */
  // Ordenar los productos de acuerdo al ranking (rank 1 primero, luego 2, luego 3)
  const products = [...(recommendation?.products ?? [])].sort((a, b) => a.rank - b.rank)
  console.log('[CaseWizardStep3] Success: Sorting and displaying recommendation products. Products array:', products)
  
  // Re-mapear colores para tarjetas de rango
  const variantStyles = (rank: number) => {
    if (rank === 1) return { border: 'border-[#16A34A]', badge: 'bg-[#16A34A] text-white', label: 'Mejor Opción' }
    if (rank === 2) return { border: 'border-[#3B82F6]', badge: 'bg-[#3B82F6] text-white', label: 'Alternativa Viable' }
    return { border: 'border-[#F59E0B]', badge: 'bg-[#F59E0B] text-white', label: 'Más Económico' }
  }

  // Construir filas comparativas en base a los productos dinámicos
  const tableRows = [
    {
      criteria: 'Dosis recomendada',
      product1: products.find(p => p.rank === 1)?.dosis ?? '—',
      product2: products.find(p => p.rank === 2)?.dosis ?? '—',
      product3: products.find(p => p.rank === 3)?.dosis ?? '—',
    },
    {
      criteria: 'Precio estimado',
      product1: products.find(p => p.rank === 1)?.precio_estimado ? `${products.find(p => p.rank === 1)?.precio_estimado} ₡` : 'No disponible',
      product2: products.find(p => p.rank === 2)?.precio_estimado ? `${products.find(p => p.rank === 2)?.precio_estimado} ₡` : 'No disponible',
      product3: products.find(p => p.rank === 3)?.precio_estimado ? `${products.find(p => p.rank === 3)?.precio_estimado} ₡` : 'No disponible',
    },
    {
      criteria: 'Banda Toxicológica',
      product1: products.find(p => p.rank === 1)?.toxicidad ? String(products.find(p => p.rank === 1)?.toxicidad) : '—',
      product2: products.find(p => p.rank === 2)?.toxicidad ? String(products.find(p => p.rank === 2)?.toxicidad) : '—',
      product3: products.find(p => p.rank === 3)?.toxicidad ? String(products.find(p => p.rank === 3)?.toxicidad) : '—',
    },
    {
      criteria: 'Periodo de carencia (días)',
      product1: products.find(p => p.rank === 1)?.intervalo_seguridad !== null ? `${products.find(p => p.rank === 1)?.intervalo_seguridad} días` : 'No aplica / No dip.',
      product2: products.find(p => p.rank === 2)?.intervalo_seguridad !== null ? `${products.find(p => p.rank === 2)?.intervalo_seguridad} días` : 'No aplica / No dip.',
      product3: products.find(p => p.rank === 3)?.intervalo_seguridad !== null ? `${products.find(p => p.rank === 3)?.intervalo_seguridad} días` : 'No aplica / No dip.',
    },
  ]

  return (
    <AppLayout>
      <section className="mx-auto max-w-5xl px-4 py-8">
        <Stepper step={3} />

        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-[#111827]">Recomendaciones Fitosanitarias</h1>
            <p className="text-sm text-[#6B7280]">
              Resultado del análisis técnico y legal para su cultivo de {recommendation?.crop}.
            </p>
          </div>
        </div>

        {/* ====== Tarjetas de productos ====== */}
        {products.length === 0 ? (
          <div className="mb-8 rounded-3xl border border-yellow-200 bg-yellow-50/50 p-8 text-center shadow-md">
            <AlertTriangle className="mx-auto h-12 w-12 text-yellow-600" />
            <h2 className="mt-3 text-lg font-bold text-yellow-800">No se encontraron productos recomendados</h2>
            <p className="mt-2 text-sm text-yellow-700 max-w-xl mx-auto leading-relaxed">
              El motor de agentes IA completó el análisis normativo del SFE y restricciones del MAG, pero no se encontraron productos registrados en el catálogo compatibles y seguros para el cultivo de <strong>{recommendation?.crop}</strong> ante el problema de <strong>{recommendation?.problem}</strong>.
            </p>
            <div className="mt-4 text-left max-w-md mx-auto text-xs text-yellow-700/80 space-y-1 bg-yellow-50 border border-yellow-200/50 p-4 rounded-xl">
              <p className="font-semibold mb-1">Recomendaciones sugeridas:</p>
              <p>• Verifique que el cultivo y problema correspondan a términos válidos (ej. Tomate, Papa, Brocoli).</p>
              <p>• El problema detectado podría requerir un principio activo no registrado en el país o prohibido por la legislación del SFE.</p>
              <p>• Consulte directamente con un asesor técnico o agrónomo certificado para este tipo de hortaliza.</p>
            </div>
          </div>
        ) : (
          <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {products.map((product) => {
              const style = variantStyles(product.rank)
              return (
                <div
                  key={product.product_id}
                  className={cn(
                    "flex flex-col rounded-3xl border bg-white p-6 shadow-md transition-all duration-300 hover:shadow-lg",
                    style.border
                  )}
                >
                  <div className="mb-4">
                    <span className={cn('inline-block rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider', style.badge)}>
                      {style.label}
                    </span>
                  </div>
                  
                  <h3 className="text-xl font-bold text-[#111827] line-clamp-2 min-h-[3.5rem]">{product.nombre_comercial}</h3>
                  
                  <div className="mt-3 mb-4 flex flex-wrap gap-2">
                    {getToxicBandBadge(product.toxicidad)}
                  </div>

                  <div className="flex-1 border-t border-[#F3F4F6] pt-4">
                    <p className="text-sm italic text-[#4B5563] line-clamp-5 leading-relaxed">
                      "{product.justification}"
                    </p>
                  </div>

                  <div className="mt-6 space-y-2.5 border-t border-[#F3F4F6] pt-4 text-xs text-[#6B7280]">
                    <div className="flex justify-between">
                      <span>Dosis:</span>
                      <span className="font-semibold text-[#374151]">{product.dosis || 'No disponible'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Precio Est.:</span>
                      <span className="font-semibold text-[#374151]">
                        {product.precio_estimado ? `${product.precio_estimado} ₡` : 'No disponible'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Plazo de espera:</span>
                      <span className="font-semibold text-[#374151]">
                        {product.intervalo_seguridad !== null ? `${product.intervalo_seguridad} días` : 'No aplica'}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* ====== Tabla comparativa ====== */}
        {products.length > 0 && (
          <div className="overflow-x-auto rounded-3xl border border-[#E5E7EB] bg-white p-6 shadow-md">
            <h2 className="mb-4 text-lg font-bold text-[#111827]">Comparativa Técnica de Productos</h2>
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-[#E5E7EB]">
                  <th className="pb-3 pr-4 font-semibold text-[#6B7280]">Criterio</th>
                  {products.map((p) => (
                    <th key={p.product_id} className="pb-3 px-4 font-bold text-[#111827] max-w-[200px] truncate">
                      {p.nombre_comercial}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableRows.map((row, ri) => (
                  <tr key={ri} className="border-b border-[#E5E7EB] last:border-b-0 hover:bg-[#F9FAFB] transition-colors">
                    <td className="py-3.5 pr-4 font-medium text-[#4B5563]">{row.criteria}</td>
                    {[row.product1, row.product2, row.product3].slice(0, products.length).map((val, ci) => (
                      <td key={ci} className="py-3.5 px-4 text-[#111827]">
                        {val === 'roja' || val === 'amarilla' || val === 'azul' || val === 'verde' ? (
                          getToxicBandBadge(val)
                        ) : (
                          val
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ====== Botón de transición ====== */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={handleGoToProviders}
            className="rounded-xl bg-[#16A34A] hover:bg-[#15803D] px-8 py-3.5 text-sm font-bold text-white shadow-md transition-all duration-300 hover:scale-[1.02]"
          >
            Siguiente: Ver distribuidores autorizados
          </button>
        </div>
      </section>
    </AppLayout>
  )
}

export default CaseWizardStep3