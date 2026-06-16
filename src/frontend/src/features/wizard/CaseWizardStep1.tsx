import { useEffect, useMemo } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import axios from 'axios'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { useWizardStore } from '@/stores/wizardStore'
import { CaseStepper, PageHeader, Panel, SelectField, SynapButton, TextField } from '@/components/ui/prototype'
import {
  CROP_OPTIONS,
  HUMIDITY_OPTIONS,
  PROBLEM_OPTIONS,
  SOIL_OPTIONS,
  STAGE_OPTIONS,
  TEMPERATURE_OPTIONS,
  WATER_OPTIONS,
} from './constants'
import { caseStep1Schema } from './schemas'
import type { CaseStep1Form } from './schemas'

interface ZoneOption {
  id: string | number
  name?: string
  nombre?: string
}

export function CaseWizardStep1() {
  const token = useAuthStore((state) => state.token)
  const setStep = useWizardStore((state) => state.setStep)
  const update = useWizardStore((state) => state.update)
  const navigate = useNavigate()

  const { register, handleSubmit, reset, control } = useForm<CaseStep1Form>({
    resolver: zodResolver(caseStep1Schema),
    defaultValues: {
      finca_id: '',
      finca_name: '',
      crop: '',
      crop_stage: '',
      affected_area: undefined,
      soil_type: '',
      humidity: '',
      temperature: '',
      water_quality: '',
      problem_to_solve: '',
      last_agrochemical: '',
      max_budget_per_liter: 0,
    },
  })

  const watchedFincaId = useWatch({ control, name: 'finca_id' })

  const { data: fincas = [] } = useQuery<ZoneOption[]>({
    queryKey: ['user', 'zones'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/zones', {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    enabled: !!token,
  })

  const fincaOptions = useMemo(
    () =>
      fincas.map((finca) => ({
        value: String(finca.id),
        label: finca.name ?? finca.nombre ?? String(finca.id),
      })),
    [fincas],
  )

  useEffect(() => {
    setStep(1)
    const data = useWizardStore.getState().data
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
  }, [reset, setStep])

  const onSubmit = (values: CaseStep1Form) => {
    const selectedFinca = fincaOptions.find((finca) => finca.value === String(values.finca_id))
    update({ ...values, finca_name: selectedFinca?.label ?? values.finca_id })
    setStep(2)
    navigate('/cases/wizard/step-2')
  }

  return (
    <AppLayout>
      <section className="max-w-[1140px]">
        <PageHeader
          title="Explique su caso"
          subtitle="Complete la información de su finca para generar una recomendación personalizada"
          className="mb-5"
        />
        <CaseStepper step={1} />

        <Panel className="px-10 py-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
            <div>
              <h2 className="border-b border-[#9CA3AF] pb-2 text-2xl font-semibold text-[#111827]">
                Información del cultivo:
              </h2>
              <div className="mt-5 grid gap-x-10 gap-y-5 md:grid-cols-2">
                <Controller
                  control={control}
                  name="finca_id"
                  render={({ field, fieldState }) => (
                    <SelectField
                      label="Finca"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={fincaOptions}
                      error={fieldState.error?.message}
                    />
                  )}
                />
                <Controller
                  control={control}
                  name="crop"
                  render={({ field, fieldState }) => (
                    <SelectField
                      label="Cultivo"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={CROP_OPTIONS}
                      error={fieldState.error?.message}
                    />
                  )}
                />
                <Controller
                  control={control}
                  name="crop_stage"
                  render={({ field, fieldState }) => (
                    <SelectField
                      label="Etapa del cultivo"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={STAGE_OPTIONS}
                      error={fieldState.error?.message}
                    />
                  )}
                />
                <TextField
                  label="Área afectada (%)"
                  type="number"
                  placeholder="20"
                  {...register('affected_area', {
                    setValueAs: (value) => (value === '' ? undefined : Number(value)),
                  })}
                />
              </div>
            </div>

            <div>
              <h2 className="border-b border-[#9CA3AF] pb-2 text-2xl font-semibold text-[#111827]">
                Condiciones del ambiente:
              </h2>
              <div className="mt-5 grid gap-x-10 gap-y-5 md:grid-cols-2">
                <Controller
                  control={control}
                  name="soil_type"
                  render={({ field, fieldState }) => (
                    <SelectField
                      label="Tipo de suelo"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={SOIL_OPTIONS}
                      error={fieldState.error?.message}
                    />
                  )}
                />
                <Controller
                  control={control}
                  name="humidity"
                  render={({ field, fieldState }) => (
                    <SelectField
                      label="Humedad"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={HUMIDITY_OPTIONS}
                      error={fieldState.error?.message}
                    />
                  )}
                />
                <Controller
                  control={control}
                  name="temperature"
                  render={({ field, fieldState }) => (
                    <SelectField
                      label="Temperatura"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={TEMPERATURE_OPTIONS}
                      error={fieldState.error?.message}
                    />
                  )}
                />
                <Controller
                  control={control}
                  name="water_quality"
                  render={({ field, fieldState }) => (
                    <SelectField
                      label="Calidad del agua"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={WATER_OPTIONS}
                      error={fieldState.error?.message}
                    />
                  )}
                />
              </div>
            </div>

            <div>
              <h2 className="border-b border-[#9CA3AF] pb-2 text-2xl font-semibold text-[#111827]">
                Objetivo y restricciones:
              </h2>
              <div className="mt-5 grid gap-x-10 gap-y-5 md:grid-cols-2">
                <Controller
                  control={control}
                  name="problem_to_solve"
                  render={({ field, fieldState }) => (
                    <SelectField
                      label="Problema a resolver"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={PROBLEM_OPTIONS}
                      error={fieldState.error?.message}
                    />
                  )}
                />
                <TextField
                  label="Último producto usado"
                  type="text"
                  placeholder="Escriba el nombre del producto"
                  {...register('last_agrochemical')}
                />
                <TextField
                  label="Presupuesto máximo por litro ₡"
                  type="text"
                  placeholder="5 000"
                  {...register('max_budget_per_liter', {
                    setValueAs: (value) => Number(String(value).replace(/\D/g, '')) || 0,
                  })}
                />
              </div>
            </div>

            <div className="flex justify-end border-t border-[#9CA3AF] pt-6">
              <SynapButton type="submit" className="min-w-[220px]">
                Continuar
              </SynapButton>
            </div>
          </form>
        </Panel>
        <input type="hidden" value={watchedFincaId ?? ''} readOnly />
      </section>
    </AppLayout>
  )
}

export default CaseWizardStep1