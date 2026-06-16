import { useQuery, useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { AppLayout } from '@/features/layout/AppLayout'
import { useWizardStore } from '@/stores/wizardStore'
import { useAuthStore } from '@/stores/authStore'
import { Loader2 } from 'lucide-react'

// ─── Humidity label → numeric (matches backend NUMERIC column) ────────────────
const HUMIDITY_MAP: Record<string, number> = {
  'Muy baja': 20.0,
  'Baja': 40.0,
  'Media': 60.0,
  'Alta': 80.0,
  'Muy alta': 95.0,
}

// ─── Temperature label → numeric midpoint ────────────────────────────────────
const TEMP_MAP: Record<string, number> = {
  'Menos de 10°C': 8.0,
  '10°C - 15°C': 12.5,
  '15°C - 20°C': 17.5,
  '20°C - 25°C': 22.5,
  '25°C - 30°C': 27.5,
  'Más de 30°C': 35.0,
}

function resolveHumidity(h: string | undefined): number {
  if (!h) return 60
  if (HUMIDITY_MAP[h] !== undefined) return HUMIDITY_MAP[h]
  const n = Number(h)
  return isNaN(n) ? 60 : n
}

function resolveTemperature(t: string | undefined): number {
  if (!t) return 22
  if (TEMP_MAP[t] !== undefined) return TEMP_MAP[t]
  const n = Number(t)
  return isNaN(n) ? 22 : n
}

// ─── Stepper ─────────────────────────────────────────────────────────────────
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
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
                done || active ? 'bg-[#16A34A] text-white' : 'border border-[#E5E7EB] bg-white text-[#6B7280]'
              }`}
            >
              {idx}
            </div>
            <div className="text-sm">{label}</div>
            {i < steps.length - 1 && <div className={`h-0.5 w-12 ${done ? 'bg-[#16A34A]' : 'bg-[#E5E7EB]'}`} />}
          </div>
        )
      })}
    </div>
  )
}

// ─── Row helper ───────────────────────────────────────────────────────────────
function Row({ label, value }: { label: string; value: string | number | undefined }) {
  return (
    <div className="flex flex-col gap-0.5">
      <p className="text-xs font-medium uppercase tracking-wide text-[#9CA3AF]">{label}</p>
      <p className="text-base font-semibold text-[#111827]">{value ?? '—'}</p>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────
export function CaseWizardConfirm() {
  const data    = useWizardStore((s) => s.data)
  const step    = useWizardStore((s) => s.step)
  const prev    = useWizardStore((s) => s.prev)
  const update  = useWizardStore((s) => s.update)
  const setStep = useWizardStore((s) => s.setStep)
  const token   = useAuthStore((s) => s.token)
  const navigate = useNavigate()

  // ── Fetch zones live so the finca name is always up to date (e.g. just added) ──
  const { data: zones = [] } = useQuery<any[]>({
    queryKey: ['user', 'zones'],
    queryFn: async () => {
      const res = await axios.get('/api/v1/zones', { headers: { Authorization: `Bearer ${token}` } })
      return res.data
    },
    enabled: !!token,
    // Refetch every time this page mounts
    staleTime: 0,
    refetchOnMount: true,
  })

  // Resolve the displayed finca name from the live zones list
  const fincaLabel = (() => {
    if (!data.finca_id) return data.finca_name ?? '—'
    const match = zones.find((z: any) => String(z.id) === String(data.finca_id))
    return match?.name ?? data.finca_name ?? String(data.finca_id)
  })()

  // ── Mutation ──────────────────────────────────────────────────────────────
  const mutation = useMutation({
    mutationFn: async (payload: object) => {
      const res = await axios.post('/api/v1/recommendations/request', payload, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return res.data
    },
    onSuccess: (res: any) => {
      const recId = res.recommendation_id
      update({ ticket_id: res.ticket_id, recommendation_id: String(recId) })
      setStep(3)
      navigate(`/recommendations/${recId}`)
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail ?? 'Error desconocido'
      alert(`No fue posible solicitar la recomendación: ${detail}`)
    },
  })

  const handleConfirm = () => {
    // Resolve zone from live list to get zone_id (integer) for the backend
    const matchedZone = zones.find((z: any) => String(z.id) === String(data.finca_id))
    const zoneId = matchedZone ? Number(matchedZone.id) : undefined

    // Build the payload — map string labels to numeric values for backend NUMERIC columns
    const payload: Record<string, any> = {
      crop:               data.crop,
      crop_stage:         data.crop_stage,
      problem_to_solve:   data.problem_to_solve,
      soil_type:          data.soil_type ?? matchedZone?.soil_type,
      humidity:           resolveHumidity(data.humidity ?? matchedZone?.humidity),
      temperature:        resolveTemperature(data.temperature ?? matchedZone?.temperature),
      water_quality:      data.water_quality ?? matchedZone?.water_quality,
      max_budget_per_liter: data.max_budget_per_liter ?? 0,
      last_agrochemical:  data.last_agrochemical ?? null,
      affected_area:      data.affected_area ?? null,
    }

    // Only attach zone_id when we can confirm it resolves to a real zone
    if (zoneId) {
      payload.zone_id = zoneId
    }

    mutation.mutate(payload)
  }

  const isPending = mutation.isPending

  return (
    <AppLayout>
      <section className="mx-auto max-w-4xl">
        <Stepper step={step} />

        <div className="rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-semibold text-[#111827]">Resumen detectado por SynapSeed</h1>
          <p className="mt-1 text-sm text-[#6B7280]">Revise los datos antes de confirmar la solicitud de recomendación.</p>

          <div className="mt-6 divide-y divide-[#F1F5F9] rounded-xl border border-[#E5E7EB]">
            {/* ── Finca ── */}
            <div className="grid gap-4 p-4 sm:grid-cols-2">
              <Row label="Finca / Zona" value={fincaLabel} />
              <Row label="Área afectada" value={data.affected_area ? `${data.affected_area}%` : undefined} />
            </div>

            {/* ── Cultivo ── */}
            <div className="grid gap-4 p-4 sm:grid-cols-2">
              <Row label="Cultivo" value={data.crop} />
              <Row label="Etapa del cultivo" value={data.crop_stage} />
            </div>

            {/* ── Condiciones ── */}
            <div className="grid gap-4 p-4 sm:grid-cols-4">
              <Row label="Tipo de suelo" value={data.soil_type} />
              <Row label="Humedad" value={data.humidity} />
              <Row label="Temperatura" value={data.temperature} />
              <Row label="Calidad del agua" value={data.water_quality} />
            </div>

            {/* ── Problema y presupuesto ── */}
            <div className="grid gap-4 p-4 sm:grid-cols-3">
              <Row label="Problema a resolver" value={data.problem_to_solve} />
              <Row label="Último agroquímico" value={data.last_agrochemical || 'Ninguno'} />
              <Row label="Presupuesto máximo / L" value={data.max_budget_per_liter ? `₡ ${data.max_budget_per_liter.toLocaleString()}` : undefined} />
            </div>
          </div>

          <div className="mt-6 flex items-center justify-between">
            <button
              type="button"
              onClick={() => { prev(); navigate('/cases/wizard/step-1') }}
              disabled={isPending}
              className="rounded-xl border border-[#D1D5DB] bg-white px-4 py-2 text-sm font-semibold text-[#111827] hover:bg-[#F7F8F2] disabled:opacity-50"
            >
              Volver
            </button>

            <button
              type="button"
              onClick={handleConfirm}
              disabled={isPending}
              className="inline-flex items-center gap-2 rounded-xl bg-[#16A34A] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#14532D] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Enviando…
                </>
              ) : (
                'Confirmar y analizar'
              )}
            </button>
          </div>
        </div>
      </section>
    </AppLayout>
  )
}

export default CaseWizardConfirm
