import { useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useLocation, useNavigate } from 'react-router-dom'
import * as Toast from '@radix-ui/react-toast'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { HUMIDITY_OPTIONS, SOIL_OPTIONS, TEMPERATURE_OPTIONS, WATER_OPTIONS } from '@/features/wizard/constants'
import { PageHeader, Panel, SelectField, SynapButton, TextField } from '@/components/ui/prototype'

const addZoneSchema = z.object({
  name: z.string().min(1, 'El nombre es obligatorio'),
  location: z.string().min(1, 'La ubicación es obligatoria'),
  temperature: z.string().min(1, 'Seleccione temperatura'),
  humidity: z.string().min(1, 'Seleccione humedad'),
  soil_type: z.string().min(1, 'Seleccione tipo de suelo'),
  water_quality: z.string().min(1, 'Seleccione calidad del agua'),
})

type AddZoneForm = z.infer<typeof addZoneSchema>

interface ZoneState {
  zone?: AddZoneForm & { id: string }
}

export function AddZonePage() {
  const token = useAuthStore((state) => state.token)
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const editingZone = (location.state as ZoneState | null)?.zone
  const [toastOpen, setToastOpen] = useState(false)
  const [toastTitle, setToastTitle] = useState('')
  const [toastDescription, setToastDescription] = useState('')

  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AddZoneForm>({
    resolver: zodResolver(addZoneSchema),
    defaultValues: {
      name: editingZone?.name ?? '',
      location: editingZone?.location ?? '',
      temperature: editingZone?.temperature ?? '',
      humidity: editingZone?.humidity ?? '',
      soil_type: editingZone?.soil_type ?? '',
      water_quality: editingZone?.water_quality ?? '',
    },
  })

  const saveMutation = useMutation({
    mutationFn: async (payload: AddZoneForm) => {
      if (editingZone?.id) {
        const response = await axios.put(`/api/v1/zones/${editingZone.id}`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        })
        return response.data
      }

      const response = await axios.post('/api/v1/zones', payload, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['zones'] })
      setToastTitle(editingZone ? 'Zona actualizada' : 'Zona creada')
      setToastDescription(editingZone ? 'Los cambios se guardaron correctamente.' : 'La nueva zona fue registrada correctamente.')
      setToastOpen(true)
      window.setTimeout(() => navigate('/zones'), 400)
    },
    onError: () => {
      setToastTitle('Error')
      setToastDescription(editingZone ? 'No fue posible actualizar la zona.' : 'No fue posible crear la zona.')
      setToastOpen(true)
    },
  })

  const onSubmit = async (values: AddZoneForm) => {
    await saveMutation.mutateAsync(values)
  }

  return (
    <Toast.Provider swipeDirection="right">
      <AppLayout>
        <section className="max-w-[1140px]">
          <PageHeader
            title={editingZone ? 'Editar zona o finca' : 'Añadir nueva zona o finca'}
            subtitle="Registre una nueva zona o finca agrícola para usarla en sus futuras recomendaciones"
          />

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <Panel className="px-10 py-8">
              <div className="grid gap-x-10 gap-y-7 md:grid-cols-2">
                <TextField
                  label="Nombre"
                  type="text"
                  placeholder="Ej: Finca Las Palmas"
                  error={errors.name?.message}
                  {...register('name')}
                />
                <TextField
                  label="Ubicación"
                  type="text"
                  placeholder="Ej: Cartago, Costa Rica"
                  error={errors.location?.message}
                  {...register('location')}
                />

                <Controller
                  control={control}
                  name="temperature"
                  render={({ field }) => (
                    <SelectField
                      label="Temperatura"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={TEMPERATURE_OPTIONS}
                      error={errors.temperature?.message}
                    />
                  )}
                />
                <Controller
                  control={control}
                  name="humidity"
                  render={({ field }) => (
                    <SelectField
                      label="Humedad"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={HUMIDITY_OPTIONS}
                      error={errors.humidity?.message}
                    />
                  )}
                />
                <Controller
                  control={control}
                  name="soil_type"
                  render={({ field }) => (
                    <SelectField
                      label="Tipo de suelo"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={SOIL_OPTIONS}
                      error={errors.soil_type?.message}
                    />
                  )}
                />
                <Controller
                  control={control}
                  name="water_quality"
                  render={({ field }) => (
                    <SelectField
                      label="Calidad del agua"
                      value={field.value}
                      onValueChange={field.onChange}
                      options={WATER_OPTIONS}
                      error={errors.water_quality?.message}
                    />
                  )}
                />
              </div>

              <div className="mt-12 flex flex-col justify-end gap-4 border-t border-[#9CA3AF] pt-6 sm:flex-row">
                <SynapButton type="button" variant="outline" className="min-w-[210px]" onClick={() => navigate('/zones')}>
                  Cancelar
                </SynapButton>
                <SynapButton type="submit" disabled={isSubmitting} className="min-w-[230px]">
                  {isSubmitting ? 'Guardando...' : editingZone ? 'Guardar cambios' : 'Guardar zona'}
                </SynapButton>
              </div>
            </Panel>
          </form>
        </section>

        <Toast.Root
          open={toastOpen}
          onOpenChange={setToastOpen}
          className="z-[100] w-[calc(100vw-2rem)] max-w-md rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-xl"
        >
          <Toast.Title className="text-sm font-semibold text-[#111827]">{toastTitle}</Toast.Title>
          <Toast.Description className="mt-1 text-sm text-[#6B7280]">{toastDescription}</Toast.Description>
        </Toast.Root>
        <Toast.Viewport className="fixed bottom-4 right-4 z-[101] flex w-auto max-w-sm flex-col gap-2 outline-none" />
      </AppLayout>
    </Toast.Provider>
  )
}
