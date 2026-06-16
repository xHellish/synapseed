import { useEffect, useMemo } from 'react'
import { useWatch } from 'react-hook-form'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import axios from 'axios'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { useWizardStore } from '@/stores/wizardStore'
import { caseStep1Schema } from './schemas'
import type { CaseStep1Form } from './schemas'

const TEMPERATURE_OPTIONS = ['Menos de 10°C', '10°C - 15°C', '15°C - 20°C', '20°C - 25°C', '25°C - 30°C', 'Más de 30°C']
const HUMIDITY_OPTIONS = ['Muy baja', 'Baja', 'Media', 'Alta', 'Muy alta']
const SOIL_OPTIONS = ['Franco', 'Arcilloso', 'Franco Arcilloso', 'Arenoso', 'Volcánico', 'Limoso']
const WATER_OPTIONS = ['Potable', 'Regular', 'Salina', 'Buena', 'Contaminada', 'Desconocida']
const CROP_OPTIONS = ['Tomate', 'Papa', 'Lechuga', 'Arroz', 'Brocoli', 'Pepino']
const STAGE_OPTIONS = ['Germinación', 'Plántula', 'Crecimiento (Fase vegetativa)', 'Floración', 'Fructificación y Madurez']
const PROBLEM_OPTIONS = ['Hongo en las hojas', 'Hongos en los tallos', 'Plagas', 'Deficiencia de nutrientes', 'Enfermedad en raiz']

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

export function CaseWizardStep1() {
  const token = useAuthStore((s) => s.token)
  const wizardStep = useWizardStore((s) => s.step)
  const setStep = useWizardStore((s) => s.setStep)
  const update = useWizardStore((s) => s.update)
  const navigate = useNavigate()

  // form
  const { register, handleSubmit, reset, control } = useForm<CaseStep1Form>({ resolver: zodResolver(caseStep1Schema) })

  // Watch finca_id to resolve its display name in real time
  const watchedFincaId = useWatch({ control, name: 'finca_id' })

  // fetch catalogs
  const fetchCatalog = async (url: string) => {
    const res = await axios.get(url, { headers: { Authorization: `Bearer ${token}` } })
    return res.data
  }

  const { data: fincas = [] } = useQuery({ queryKey: ['user', 'zones'], queryFn: async () => fetchCatalog('/api/v1/zones'), enabled: !!token })
  const { data: crops = [] } = useQuery({ queryKey: ['catalog', 'crops'], queryFn: async () => fetchCatalog('/api/v1/catalogs/crops'), enabled: !!token })
  const { data: stages = [] } = useQuery({ queryKey: ['catalog', 'crop_stages'], queryFn: async () => fetchCatalog('/api/v1/catalogs/crop-stages'), enabled: !!token })
  const { data: problems = [] } = useQuery({ queryKey: ['catalog', 'problems'], queryFn: async () => fetchCatalog('/api/v1/catalogs/problems'), enabled: !!token })

  const fincasFallback = useMemo(() => (fincas && fincas.length ? fincas : []), [fincas])

  useEffect(() => {
    // populate defaults from store if present
    const data = useWizardStore.getState().data
    if (data) {
      reset({
        finca_id: data.finca_id ?? '',
        finca_name: data.finca_name ?? '',
        crop: data.crop ?? '',
        crop_stage: data.crop_stage ?? '',
        affected_area: data.affected_area ?? undefined,
        soil_type: data.soil_type ?? '',
        humidity: data.humidity ?? '',
        temperature: data.temperature ?? '',
        water_quality: data.water_quality ?? '',
        problem_to_solve: data.problem_to_solve ?? '',
        last_agrochemical: data.last_agrochemical ?? '',
        max_budget_per_liter: data.max_budget_per_liter ?? 0,
      })
    }
  }, [reset])

  const onSubmit = (values: CaseStep1Form) => {
    // Resolve the finca name from the loaded list and persist into store
    const selectedFinca = fincasFallback.find((f: any) => String(f.id) === String(values.finca_id))
    update({ ...values, finca_name: selectedFinca?.name ?? values.finca_id })
    setStep(2)
    navigate('/cases/wizard/step-2')
  }

  return (
    <AppLayout>
      <section className="mx-auto max-w-4xl">
        <Stepper step={wizardStep} />

        <div className="rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-semibold text-[#111827]">Explique su caso</h1>
          <p className="mt-1 text-sm text-[#6B7280]">Complete la información para que SynapSeed entienda su situación.</p>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-6">
            {/* Información del cultivo */}
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-[#111827]">Información del cultivo</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Finca</label>
                  <select {...register('finca_id')} className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm">
                    <option value="">Seleccione finca</option>
                    {fincasFallback.map((f: any) => (
                      <option key={f.id} value={f.id}>
                        {f.name || f.nombre || f.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Cultivo</label>
                  <select {...register('crop')} className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm">
                    <option value="">Seleccione cultivo</option>
                    {crops.length > 0
                      ? crops.map((c: any) => (
                          <option key={c.id || c.name} value={c.name}>{c.name}</option>
                        ))
                      : CROP_OPTIONS.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))
                    }
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Etapa del cultivo</label>
                  <select {...register('crop_stage')} className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm">
                    <option value="">Seleccione etapa</option>
                    {stages.length > 0
                      ? stages.map((s: any) => (
                          <option key={s.id || s.name} value={s.name}>{s.name}</option>
                        ))
                      : STAGE_OPTIONS.map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))
                    }
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Área afectada (%)</label>
                  <input type="number" {...register('affected_area', { valueAsNumber: true })} placeholder="20" className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm" />
                </div>
              </div>
            </div>

            {/* Condiciones del ambiente */}
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-[#111827]">Condiciones del ambiente</h2>
              <div className="grid gap-4 sm:grid-cols-4">
                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Tipo de suelo</label>
                  <select {...register('soil_type')} className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm">
                    <option value="">Seleccione</option>
                    {SOIL_OPTIONS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Humedad</label>
                  <select {...register('humidity')} className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm">
                    <option value="">Seleccione</option>
                    {HUMIDITY_OPTIONS.map((h) => (
                      <option key={h} value={h}>{h}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Temperatura</label>
                  <select {...register('temperature')} className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm">
                    <option value="">Seleccione</option>
                    {TEMPERATURE_OPTIONS.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Calidad del agua</label>
                  <select {...register('water_quality')} className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm">
                    <option value="">Seleccione</option>
                    {WATER_OPTIONS.map((w) => (
                      <option key={w} value={w}>{w}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Objetivo y restricciones */}
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-[#111827]">Objetivo y restricciones</h2>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Problema a resolver</label>
                  <select {...register('problem_to_solve')} className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm">
                    <option value="">Seleccione</option>
                    {PROBLEM_OPTIONS.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Último producto usado</label>
                  <input {...register('last_agrochemical')} placeholder="Ej: Fungicida A" className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-[#111827]">Presupuesto máximo por litro ₡</label>
                  <input type="number" {...register('max_budget_per_liter', { valueAsNumber: true })} placeholder="5 000" className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm" />
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button type="submit" className="rounded-xl bg-[#16A34A] px-4 py-2 text-sm font-semibold text-white hover:bg-[#14532D]">
                Continuar
              </button>
            </div>
          </form>
        </div>
      </section>
    </AppLayout>
  )
}

export default CaseWizardStep1