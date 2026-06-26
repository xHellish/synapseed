import { useEffect, useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { AlertTriangle, Check, ChevronDown, ChevronUp, Leaf, Loader2, Mail, MapPin, Phone, Search, Shield, Sparkles } from 'lucide-react'

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
  crop: 'Café',
  crop_stage: 'Floración',
  problem: 'Roya del café (hongo en las hojas)',
  status: 'completed',
  current_step: null,
  error_message: null,
  max_budget_per_liter: 25000,
  products: [
    {
      rank: 1,
      product_id: 1,
      nombre_comercial: 'RoyaShield Sistémico',
      justification:
        'Mejor opción para el cafetal de altura de la Zona de los Santos: control curativo y preventivo de la roya (Hemileia vastatrix), con buena residualidad para las condiciones frías y húmedas de Tarrazú.',
      dosis: '0.5 L/ha en aplicación foliar dirigida al follaje',
      precio_estimado: 22000,
      toxicidad: 'azul',
      intervalo_seguridad: 21,
      categoria: 'Fungicida sistémico (triazol + estrobilurina)',
      cultivo_objetivo: 'Café',
      problema_objetivo: 'Roya del café',
      ventajas: ['Acción curativa y preventiva', 'Alta residualidad en clima húmedo', 'Registrado en el SFE para café'],
      riesgos: ['Respetar el intervalo de seguridad de 21 días antes de cosecha', 'Rotar el modo de acción para evitar resistencia de la roya'],
      recomendacion_uso_general:
        'Aplicar al primer signo de roya, en horas de menor temperatura. Usar equipo de protección personal (EPP) según la etiqueta del SFE. No exceder dos aplicaciones por ciclo.',
    },
    {
      rank: 2,
      product_id: 2,
      nombre_comercial: 'CuproCafé Preventivo',
      justification: 'Alternativa cúprica de contacto, ideal como tratamiento preventivo antes de la época lluviosa y con menor costo por hectárea.',
      dosis: '2.5 kg/ha en aplicación foliar preventiva',
      precio_estimado: 12000,
      toxicidad: 'verde',
      intervalo_seguridad: 14,
      categoria: 'Fungicida de contacto (cúprico)',
      cultivo_objetivo: 'Café',
      problema_objetivo: 'Roya del café',
      ventajas: ['Menor costo por hectárea', 'Buen control preventivo', 'Banda verde (baja toxicidad)'],
      riesgos: ['Solo preventivo: no cura infecciones avanzadas', 'Se lava con lluvia fuerte y requiere reaplicación'],
      recomendacion_uso_general:
        'Aplicar de forma preventiva al inicio de las lluvias y repetir cada 21-28 días. Excelente para alternar con el sistémico y manejar resistencia.',
    },
    {
      rank: 3,
      product_id: 3,
      nombre_comercial: 'BioRoya Trichoderma',
      justification: 'Opción biológica a base de Trichoderma, de mínimo riesgo ambiental y apta para café con certificación sostenible.',
      dosis: '1.5 L/ha, 3-4 aplicaciones según severidad',
      precio_estimado: 9000,
      toxicidad: 'verde',
      intervalo_seguridad: 1,
      categoria: 'Fungicida biológico',
      cultivo_objetivo: 'Café',
      problema_objetivo: 'Roya del café',
      ventajas: ['Banda verde (mínima toxicidad)', 'Intervalo de seguridad de 1 día', 'Apto para café con certificación sostenible'],
      riesgos: ['Eficacia menor en infestaciones severas', 'Requiere aplicaciones más frecuentes'],
      recomendacion_uso_general:
        'Usar en etapas tempranas o como complemento de un programa integrado de manejo de roya. Consultar con un agrónomo certificado para el plan de rotación.',
    },
  ],
}

const DEMO_PROVIDERS: NormalizedProvider[] = normalizeProviders([
  {
    id: 1,
    nombre: 'AgroServicios Tarrazú',
    product_id: 1,
    producto_asociado: 'RoyaShield Sistémico',
    telefono: '2546 - 6789',
    correo: 'ventas@agrotarrazu.cr',
    ubicacion: 'San Marcos de Tarrazú',
  },
  {
    id: 2,
    nombre: 'Insumos del Café Dota',
    product_id: 2,
    producto_asociado: 'CuproCafé Preventivo',
    telefono: '2541 - 6782',
    correo: 'info@insumosdota.cr',
    ubicacion: 'Santa María de Dota',
  },
  {
    id: 3,
    nombre: 'BioInsumos Los Santos',
    product_id: 3,
    producto_asociado: 'BioRoya Trichoderma',
    telefono: '2546 - 6783',
    correo: 'ventas@bioinsumosls.cr',
    ubicacion: 'San Pablo de León Cortés',
  },
])

// Modo demo: duración de cada fase del pipeline y las "subtareas" que se muestran
// rotando dentro de cada fase, para que se vea que el agente está trabajando.
const DEMO_PHASE_MS = 5000

const DEMO_PIPELINE_PHASES: { key: string; details: string[] }[] = [
  {
    key: 'context_analyzer',
    details: [
      'Leyendo las condiciones de la Finca Loma Alta...',
      'Identificando el cultivo: café de altura...',
      'Evaluando el clima de la Zona de los Santos...',
      'Detectando el problema: roya del café...',
    ],
  },
  {
    key: 'researcher',
    details: [
      'Buscando entre productos registrados en el SFE...',
      'Comparando fungicidas para roya (Hemileia vastatrix)...',
      'Filtrando por el presupuesto disponible...',
      'Seleccionando candidatos compatibles con café...',
    ],
  },
  {
    key: 'legal_validator',
    details: [
      'Verificando el registro ante el SFE...',
      'Validando el uso autorizado en café...',
      'Revisando los intervalos de seguridad...',
      'Descartando productos restringidos...',
    ],
  },
  {
    key: 'synthesizer',
    details: [
      'Rankeando las mejores opciones...',
      'Generando la tabla comparativa...',
      'Redactando justificaciones y dosis...',
      'Preparando la recomendación final...',
    ],
  },
]

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

function ProductCard({
  product,
  providers,
}: {
  product: ReturnType<typeof buildProductComparisons>[number]
  providers: NormalizedProvider[]
}) {
  const [showDetails, setShowDetails] = useState(false)
  const [showContact, setShowContact] = useState(false)

  const productProviders = providers.filter((p) => p.productId === product.productId)
  const hasProvider = productProviders.length > 0

  return (
    <Panel className="relative p-7 flex flex-col">
      <span className={cn('absolute right-6 top-6 rounded-full px-5 py-2 text-sm font-bold', badgeClass(product.badgeColor))}>
        {product.badge}
      </span>

      {/* Información esencial */}
      <h3 className="mt-12 text-2xl font-bold text-[#111827]">{product.name}</h3>
      <dl className="mt-5 space-y-4 text-xl leading-7">
        <div>
          <dt className="font-semibold text-[#6B7280]">Tipo</dt>
          <dd className="text-[#111827]">{product.type}</dd>
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

      {/* Botones de acción */}
      <div className="mt-6 flex flex-col gap-2">
        <button
          onClick={() => setShowContact((prev) => !prev)}
          disabled={!hasProvider}
          className={cn(
            'flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors',
            hasProvider
              ? 'bg-[#16A34A] text-white hover:bg-[#15803D]'
              : 'cursor-not-allowed bg-[#E5E7EB] text-[#9CA3AF]',
          )}
        >
          <Phone className="h-4 w-4" />
          {hasProvider ? 'Contactar proveedor' : 'Sin proveedor disponible'}
        </button>

        <button
          onClick={() => setShowDetails((prev) => !prev)}
          className="flex items-center justify-center gap-2 rounded-xl border border-[#E5E7EB] px-4 py-2.5 text-sm font-semibold text-[#374151] transition-colors hover:bg-[#F9FAFB]"
        >
          {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          {showDetails ? 'Ocultar detalles' : 'Ver más detalles'}
        </button>
      </div>

      {/* Panel de contacto */}
      {showContact && hasProvider && (
        <div className="mt-4 rounded-xl border border-[#D1FAE5] bg-[#F0FDF4] p-4 space-y-3">
          {productProviders.map((prov) => (
            <div key={prov.id} className="space-y-2">
              <p className="font-semibold text-[#166534]">{prov.name}</p>
              {prov.phone && prov.phone !== 'No disponible' && (
                <a href={`tel:${prov.phone}`} className="flex items-center gap-2 text-sm text-[#374151] hover:text-[#16A34A]">
                  <Phone className="h-3.5 w-3.5 shrink-0 text-[#16A34A]" />
                  {prov.phone}
                </a>
              )}
              {prov.email && prov.email !== 'No disponible' && (
                <a href={`mailto:${prov.email}`} className="flex items-center gap-2 text-sm text-[#374151] hover:text-[#16A34A]">
                  <Mail className="h-3.5 w-3.5 shrink-0 text-[#16A34A]" />
                  {prov.email}
                </a>
              )}
              {prov.location && prov.location !== 'No disponible' && (
                <span className="flex items-center gap-2 text-sm text-[#6B7280]">
                  <MapPin className="h-3.5 w-3.5 shrink-0" />
                  {prov.location}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Panel de detalles adicionales */}
      {showDetails && (
        <div className="mt-4 space-y-4 border-t border-[#F3F4F6] pt-4">
          {product.registrante && product.registrante !== 'No disponible' && (
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-[#6B7280]">Registrante</p>
              <p className="mt-0.5 text-sm text-[#374151]">{product.registrante}</p>
            </div>
          )}
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-[#6B7280]">Compatibilidad con el cultivo</p>
            <p className="mt-0.5 text-sm text-[#374151]">{product.compatibility}</p>
          </div>
          {product.justification && (
            <div className="rounded-lg bg-[#F9FAFB] p-3">
              <p className="text-xs italic text-[#4B5563] leading-relaxed">&ldquo;{product.justification}&rdquo;</p>
            </div>
          )}
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
          {product.recomendacion_uso_general && (
            <div className="rounded-lg bg-[#F0FDF4] p-3">
              <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#166534]">Uso recomendado</p>
              <p className="text-xs text-[#166534] leading-relaxed">{product.recomendacion_uso_general}</p>
            </div>
          )}
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
        </div>
      )}
    </Panel>
  )
}

export function CaseWizardStep3() {
  const token = useAuthStore((state) => state.token)
  const setStep = useWizardStore((state) => state.setStep)
  const navigate = useNavigate()
  const location = useLocation()
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const isDemo = !id || id === 'demo'  // modo demo: muestra datos de ejemplo sin backend
  // La animacion de los agentes solo corre al llegar desde "Confirmar" (state.runDemo).
  // Al volver desde Proveedores (sin ese state) se muestran los resultados de una vez.
  const runDemoAnimation = isDemo && (location.state as { runDemo?: boolean } | null)?.runDemo === true

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

  // Estado solo para la animación de la demo: barra de progreso suave y subtarea actual.
  const [demoProgress, setDemoProgress] = useState(0)
  const [demoDetail, setDemoDetail] = useState<string | null>(null)

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

  // Modo demo (sales pitch): simula el avance de los 4 agentes con fases de 5s cada una,
  // mostrando subtareas rotativas y una barra de progreso suave, sin llamar al backend.
  // Un único intervalo deriva la fase, la subtarea y el % a partir del tiempo transcurrido.
  useEffect(() => {
    if (!isDemo) return
    // Si no venimos de "Confirmar", saltamos la animacion y mostramos los resultados ya.
    if (!runDemoAnimation) {
      setPipelineState({ status: 'completed', current_step: null, error_message: null })
      setDemoProgress(100)
      setDemoDetail(null)
      return
    }
    const total = DEMO_PIPELINE_PHASES.length * DEMO_PHASE_MS
    const start = Date.now()
    setPipelineState({ status: 'processing', current_step: DEMO_PIPELINE_PHASES[0].key, error_message: null })
    setDemoDetail(DEMO_PIPELINE_PHASES[0].details[0])

    const tick = window.setInterval(() => {
      const elapsed = Date.now() - start
      if (elapsed >= total) {
        setPipelineState({ status: 'completed', current_step: null, error_message: null })
        setDemoProgress(100)
        setDemoDetail(null)
        window.clearInterval(tick)
        return
      }
      const phaseIndex = Math.min(DEMO_PIPELINE_PHASES.length - 1, Math.floor(elapsed / DEMO_PHASE_MS))
      const phase = DEMO_PIPELINE_PHASES[phaseIndex]
      const within = elapsed - phaseIndex * DEMO_PHASE_MS
      const detailIndex = Math.min(
        phase.details.length - 1,
        Math.floor(within / (DEMO_PHASE_MS / phase.details.length)),
      )
      // Curva no lineal: arranca rapido, frena en la mitad, se arrastra al final.
      // t=0→10%: sube a 15%; t=10→50%: sube a 60%; t=50→80%: sube a 82%; t=80→100%: llega a 94%.
      const t = elapsed / total
      let eased: number
      if      (t < 0.10) eased = t / 0.10 * 15
      else if (t < 0.50) eased = 15 + (t - 0.10) / 0.40 * 45
      else if (t < 0.80) eased = 60 + (t - 0.50) / 0.30 * 22
      else               eased = 82 + (t - 0.80) / 0.20 * 12
      setPipelineState({ status: 'processing', current_step: phase.key, error_message: null })
      setDemoProgress(Math.round(eased))
      setDemoDetail(phase.details[detailIndex])
    }, 200)

    return () => window.clearInterval(tick)
  }, [isDemo, runDemoAnimation])

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
    const baseProgress = getProgressInfo(pipelineState.status, pipelineState.current_step)
    // En demo la barra avanza suave (demoProgress); en real usa los % por etapa.
    const progress = isDemo ? { ...baseProgress, percentage: demoProgress } : baseProgress
    const steps = [
      { key: 'context_analyzer', name: 'Analizador de contexto', icon: Sparkles },
      { key: 'researcher', name: 'Investigador RAG', icon: Search },
      { key: 'legal_validator', name: 'Validador legal', icon: Shield },
      { key: 'synthesizer', name: 'Sintetizador IA', icon: Leaf },
    ]
    const activeIndex = steps.findIndex((step) => step.key === pipelineState.current_step)

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
              {isDemo && demoDetail && (
                <p className="mt-1 text-base italic text-[#16A34A]">{demoDetail}</p>
              )}
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
              {steps.map((step, index) => {
                const Icon = step.icon
                const active = pipelineState.current_step === step.key
                const done = activeIndex > index // fases ya superadas (en demo van quedando en verde)
                return (
                  <div
                    key={step.key}
                    className={cn(
                      'rounded-xl border p-5 transition-colors',
                      active || done ? 'border-[#16A34A] bg-[#F0FDF4]' : 'border-[#E5E7EB] bg-white',
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <Icon className={cn('h-6 w-6', active || done ? 'text-[#16A34A]' : 'text-[#6B7280]')} />
                      {done ? (
                        <Check className="h-5 w-5 text-[#16A34A]" />
                      ) : active ? (
                        <Loader2 className="h-5 w-5 animate-spin text-[#16A34A]" />
                      ) : null}
                    </div>
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
                <ProductCard key={product.productId} product={product} providers={providerList} />
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