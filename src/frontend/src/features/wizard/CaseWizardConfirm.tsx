import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { AppLayout } from '@/features/layout/AppLayout'
import { useWizardStore } from '@/stores/wizardStore'
import { useAuthStore } from '@/stores/authStore'
import { useMutation } from '@tanstack/react-query'

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

export function CaseWizardConfirm() {
  const data = useWizardStore((s) => s.data)
  const step = useWizardStore((s) => s.step)
  const prev = useWizardStore((s) => s.prev)
  const update = useWizardStore((s) => s.update)
  const setStep = useWizardStore((s) => s.setStep)
  const token = useAuthStore((s) => s.token)
  const navigate = useNavigate()

  const postRecommendation = async (payload: object) => {
    const res = await axios.post('/api/v1/recommendations/request', payload, { headers: { Authorization: `Bearer ${token}` } })
    return res.data
  }

  const mutation = useMutation({
    mutationFn: postRecommendation,
    onSuccess: (res: any) => {
      const recId = res.recommendation_id
      update({ ticket_id: res.ticket_id, recommendation_id: String(recId) })
      setStep(3)
      navigate(`/recommendations/${recId}`)
    },
    onError: () => {
      // TODO: show toast (simple alert for now)
      alert('No fue posible solicitar la recomendación. Intente de nuevo.')
    },
  })

  const handleConfirm = () => {
    // Map stored values into API payload
    const mapHumidity = (h: any) => {
      if (h === 'low') return 30
      if (h === 'medium') return 60
      if (h === 'high') return 90
      return Number(h) || 50
    }
    const mapTemperature = (t: any) => {
      if (t === '<20') return 18
      if (t === '20-25') return 22.5
      if (t === '>25') return 28
      return Number(t) || 22
    }

    const payload = {
      crop: data.crop,
      crop_stage: data.crop_stage,
      problem_to_solve: data.problem_to_solve,
      soil_type: data.soil_type,
      humidity: mapHumidity(data.humidity),
      temperature: mapTemperature(data.temperature),
      water_quality: data.water_quality,
      max_budget_per_liter: data.max_budget_per_liter ?? 0,
      last_agrochemical: data.last_agrochemical ?? null,
      affected_area: data.affected_area ?? null,
    }

    mutation.mutate(payload)
  }

  return (
    <AppLayout>
      <section className="mx-auto max-w-4xl">
        <Stepper step={step} />

        <div className="rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-semibold text-[#111827]">Resumen detectado por SynapSeed</h1>
          <p className="mt-1 text-sm text-[#6B7280]">Revise los datos antes de confirmar la solicitud de recomendación.</p>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              <p className="text-sm text-[#6B7280]">Finca</p>
              <p className="text-lg font-semibold text-[#111827]">{data.finca_name ?? data.finca_id ?? '—'}</p>

              <p className="mt-4 text-sm text-[#6B7280]">Cultivo</p>
              <p className="text-lg font-semibold text-[#111827]">{data.crop ?? '—'}</p>

              <p className="mt-4 text-sm text-[#6B7280]">Etapa</p>
              <p className="text-lg font-semibold text-[#111827]">{data.crop_stage ?? '—'}</p>

              <p className="mt-4 text-sm text-[#6B7280]">Área afectada</p>
              <p className="text-lg font-semibold text-[#111827]">{data.affected_area ? `${data.affected_area}%` : '—'}</p>
            </div>

            <div className="space-y-3">
              <p className="text-sm text-[#6B7280]">Condiciones</p>
              <p className="text-lg font-semibold text-[#111827]">{`${data.soil_type ?? '—'} · ${data.humidity ?? '—'} · ${data.temperature ?? '—'}`}</p>

              <p className="mt-4 text-sm text-[#6B7280]">Problema a resolver</p>
              <p className="text-lg font-semibold text-[#111827]">{data.problem_to_solve ?? '—'}</p>

              <p className="mt-4 text-sm text-[#6B7280]">Presupuesto estimado</p>
              <p className="text-lg font-semibold text-[#111827]">₡ {data.max_budget_per_liter ?? '—'}</p>
            </div>
          </div>

          <div className="mt-6 flex justify-between">
            <button onClick={() => { prev(); navigate('/cases/wizard/step-1') }} className="rounded-xl border border-[#D1D5DB] bg-white px-4 py-2 text-sm font-semibold text-[#111827] hover:bg-[#F7F8F2]">
              Volver
            </button>

            <button onClick={handleConfirm} className="rounded-xl bg-[#16A34A] px-4 py-2 text-sm font-semibold text-white hover:bg-[#14532D]">
              Confirmar
            </button>
          </div>
        </div>
      </section>
    </AppLayout>
  )
}

export default CaseWizardConfirm
