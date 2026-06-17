import { useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { useWizardStore } from '@/stores/wizardStore'
import { CaseStepper, PageHeader, Panel, SynapButton } from '@/components/ui/prototype'

interface ZoneSummary {
  id: string | number
  name?: string
  soil_type?: string
  humidity?: string
  temperature?: string
  water_quality?: string
}

interface RecommendationRequestResponse {
  recommendation_id: string | number
  ticket_id: string
}

const HUMIDITY_MAP: Record<string, number> = {
  'Muy baja': 20,
  Baja: 40,
  Media: 60,
  Alta: 80,
  'Muy alta': 95,
}

const TEMP_MAP: Record<string, number> = {
  'Menos de 10°C': 8,
  '10°C - 15°C': 12.5,
  '15°C - 20°C': 17.5,
  '20°C - 25°C': 22.5,
  '25°C - 30°C': 27.5,
  'Más de 30°C': 35,
}

function resolveHumidity(value: string | undefined): number {
  if (!value) return 60
  if (HUMIDITY_MAP[value] !== undefined) return HUMIDITY_MAP[value]
  const parsed = Number(value)
  return Number.isNaN(parsed) ? 60 : parsed
}

function resolveTemperature(value: string | undefined): number {
  if (!value) return 22
  if (TEMP_MAP[value] !== undefined) return TEMP_MAP[value]
  const parsed = Number(value)
  return Number.isNaN(parsed) ? 22 : parsed
}

function SummaryItem({ label, value }: { label: string; value: string | number | undefined }) {
  return (
    <div className="min-h-[86px]">
      <p className="text-2xl leading-8 text-[#6B7280]">{label}</p>
      <p className="mt-2 text-2xl font-bold leading-8 text-[#111827]">{value || 'No disponible'}</p>
    </div>
  )
}

export function CaseWizardConfirm() {
  const data = useWizardStore((state) => state.data)
  const prev = useWizardStore((state) => state.prev)
  const update = useWizardStore((state) => state.update)
  const setStep = useWizardStore((state) => state.setStep)
  const token = useAuthStore((state) => state.token)
  const navigate = useNavigate()

  useEffect(() => {
    setStep(2)
  }, [setStep])

  const { data: zones = [] } = useQuery<ZoneSummary[]>({
    queryKey: ['user', 'zones'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/zones', {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    enabled: !!token,
    staleTime: 0,
    refetchOnMount: true,
  })

  const fincaLabel = (() => {
    if (!data.finca_id) return data.finca_name ?? 'No disponible'
    const match = zones.find((zone) => String(zone.id) === String(data.finca_id))
    return match?.name ?? data.finca_name ?? String(data.finca_id)
  })()

  const mutation = useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const response = await axios.post('/api/v1/recommendations/request', payload, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    onSuccess: (response: RecommendationRequestResponse) => {
      const recommendationId = response.recommendation_id
      update({ ticket_id: response.ticket_id, recommendation_id: String(recommendationId) })
      setStep(3)
      navigate(`/recommendations/${recommendationId}`)
    },
    onError: (error: unknown) => {
      const detail = axios.isAxiosError(error) ? error.response?.data?.detail ?? 'Error desconocido' : 'Error desconocido'
      alert(`No fue posible solicitar la recomendación: ${detail}`)
    },
  })

  const handleConfirm = () => {
    const matchedZone = zones.find((zone) => String(zone.id) === String(data.finca_id))
    const zoneId = matchedZone ? Number(matchedZone.id) : undefined

    // Usar || en lugar de ?? para que los strings vacíos también hagan fallback a la zona
    const payload: Record<string, unknown> = {
      crop: data.crop,
      crop_stage: data.crop_stage,
      problem_to_solve: data.problem_to_solve,
      soil_type: data.soil_type || matchedZone?.soil_type,
      humidity: resolveHumidity(data.humidity || matchedZone?.humidity),
      temperature: resolveTemperature(data.temperature || matchedZone?.temperature),
      water_quality: data.water_quality || matchedZone?.water_quality,
      max_budget_per_liter: data.max_budget_per_liter ?? 0,
      last_agrochemical: data.last_agrochemical ?? null,
      affected_area: data.affected_area ?? null,
    }

    if (zoneId) payload.zone_id = zoneId
    mutation.mutate(payload)
  }

  const isPending = mutation.isPending
  const matchedZoneForDisplay = zones.find((zone) => String(zone.id) === String(data.finca_id))
  const effectiveHumidity = data.humidity || matchedZoneForDisplay?.humidity
  const effectiveTemperature = data.temperature || matchedZoneForDisplay?.temperature
  const climate = [effectiveHumidity, effectiveTemperature].filter(Boolean).join(', ')

  return (
    <AppLayout>
      <section className="max-w-[1140px]">
        <PageHeader
          title="Confirmar su caso"
          subtitle="Revise la información antes de enviar su caso al agente"
          className="mb-5"
        />
        <CaseStepper step={2} />

        <Panel className="px-12 py-8">
          <h2 className="text-2xl font-semibold text-[#111827]">Resumen detectado por SynapSeed:</h2>

          <div className="mx-auto mt-12 grid max-w-[900px] gap-x-28 gap-y-8 md:grid-cols-2">
            <SummaryItem label="Finca:" value={fincaLabel} />
            <SummaryItem label="Cultivo:" value={data.crop} />
            <SummaryItem label="Etapa del cultivo:" value={data.crop_stage} />
            <SummaryItem label="Área afectada:" value={data.affected_area ? `${data.affected_area}%` : undefined} />
            <SummaryItem label="Clima:" value={climate} />
            <SummaryItem label="Problema a resolver:" value={data.problem_to_solve} />
            <SummaryItem label="Último producto usado:" value={data.last_agrochemical || 'Ninguno'} />
            <SummaryItem
              label="Presupuesto estimado:"
              value={data.max_budget_per_liter ? `₡ ${data.max_budget_per_liter.toLocaleString('es-CR')}` : undefined}
            />
          </div>

          <div className="mt-12 flex flex-col justify-between gap-4 border-t border-[#9CA3AF] pt-8 sm:flex-row">
            <SynapButton
              variant="outline"
              className="min-w-[220px]"
              disabled={isPending}
              onClick={() => {
                prev()
                navigate('/cases/wizard/step-1')
              }}
            >
              Volver
            </SynapButton>

            <SynapButton className="min-w-[220px]" disabled={isPending} onClick={handleConfirm}>
              {isPending ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Confirmando
                </>
              ) : (
                'Confirmar'
              )}
            </SynapButton>
          </div>
        </Panel>
      </section>
    </AppLayout>
  )
}

export default CaseWizardConfirm
