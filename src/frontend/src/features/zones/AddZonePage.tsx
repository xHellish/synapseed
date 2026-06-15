import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import * as Toast from '@radix-ui/react-toast'
import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'

const addZoneSchema = z.object({
  name: z.string().min(1, 'El nombre es obligatorio'),
  location: z.string().min(1, 'La ubicación es obligatoria'),
  temperature: z.string().min(1, 'Seleccione temperatura'),
  humidity: z.string().min(1, 'Seleccione humedad'),
  soil_type: z.string().min(1, 'Seleccione tipo de suelo'),
  water_quality: z.string().min(1, 'Seleccione calidad del agua'),
})

type AddZoneForm = z.infer<typeof addZoneSchema>

export function AddZonePage() {
  const token = useAuthStore((s) => s.token)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [toastOpen, setToastOpen] = useState(false)
  const [toastTitle, setToastTitle] = useState('')
  const [toastDescription, setToastDescription] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<AddZoneForm>({ resolver: zodResolver(addZoneSchema) })

  // Fetch catalogs concurrently
  const fetchCatalog = async (url: string) => {
    const res = await axios.get(url, { headers: { Authorization: `Bearer ${token}` } })
    return res.data
  }

  const { data: soilOptions = [] } = useQuery<string[]>({
    queryKey: ['catalog', 'soil_types'],
    queryFn: () => fetchCatalog('/api/v1/catalogs/soil-types'),
    enabled: !!token,
    retry: 1,
    staleTime: 1000 * 60 * 60,
  })

  const { data: humidityOptions = [] } = useQuery<string[]>({
    queryKey: ['catalog', 'humidity'],
    queryFn: () => fetchCatalog('/api/v1/catalogs/humidity'),
    enabled: !!token,
    retry: 1,
    staleTime: 1000 * 60 * 60,
  })

  const { data: temperatureOptions = [] } = useQuery<string[]>({
    queryKey: ['catalog', 'temperature'],
    queryFn: () => fetchCatalog('/api/v1/catalogs/temperature'),
    enabled: !!token,
    retry: 1,
    staleTime: 1000 * 60 * 60,
  })

  const { data: waterOptions = [] } = useQuery<string[]>({
    queryKey: ['catalog', 'water_quality'],
    queryFn: () => fetchCatalog('/api/v1/catalogs/water-quality'),
    enabled: !!token,
    retry: 1,
    staleTime: 1000 * 60 * 60,
  })

  // Fallback options if backend catalogs missing
  const soilFallback = useMemo(() => (soilOptions && soilOptions.length ? soilOptions : ['Arcilloso', 'Arenoso', 'Franco']), [soilOptions])
  const humidityFallback = useMemo(() => (humidityOptions && humidityOptions.length ? humidityOptions : ['Alta', 'Media', 'Baja']), [humidityOptions])
  const temperatureFallback = useMemo(() => (temperatureOptions && temperatureOptions.length ? temperatureOptions : ['<20°C', '20-25°C', '>25°C']), [temperatureOptions])
  const waterFallback = useMemo(() => (waterOptions && waterOptions.length ? waterOptions : ['Buena', 'Regular', 'Mala']), [waterOptions])

  const addMutation = useMutation({
    mutationFn: async (payload: AddZoneForm) => {
      const res = await axios.post('/api/v1/zones', payload, { headers: { Authorization: `Bearer ${token}` } })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['zones'] })
      setToastTitle('Zona creada')
      setToastDescription('La nueva zona fue registrada correctamente.')
      setToastOpen(true)
      // short delay to show toast then navigate
      setTimeout(() => navigate('/zones'), 400)
    },
    onError: () => {
      setToastTitle('Error')
      setToastDescription('No fue posible crear la zona. Intente de nuevo.')
      setToastOpen(true)
    },
  })

  useEffect(() => {
    // Pre-fill defaults if desired
    reset({ name: '', location: '', temperature: '', humidity: '', soil_type: '', water_quality: '' })
  }, [reset])

  const onSubmit = async (values: AddZoneForm) => {
    await addMutation.mutateAsync(values)
  }

  return (
    <Toast.Provider swipeDirection="right">
      <AppLayout>
        <section className="mx-auto max-w-4xl">
          <header className="mb-6">
            <h1 className="text-3xl font-semibold text-[#111827]">Añadir nueva zona o finca</h1>
            <p className="mt-1 text-sm text-[#6B7280]">Registre una nueva zona o finca agrícola para usarla en sus futuras recomendaciones</p>
          </header>

          <form onSubmit={handleSubmit(onSubmit)} className="rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[#111827]">Nombre</label>
                <input {...register('name')} placeholder="Ej: Finca Las Palmas" className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm" />
                {errors.name && <p className="text-sm text-[#DC2626]">{errors.name.message}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#111827]">Ubicación</label>
                <input {...register('location')} placeholder="Ej: Cartago, Costa Rica" className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm" />
                {errors.location && <p className="text-sm text-[#DC2626]">{errors.location.message}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#111827]">Temperatura</label>
                <select {...register('temperature')} defaultValue="" className="w-full rounded-xl border border-[#E5E7EB] bg-white px-3 py-2 text-sm">
                  <option value="" disabled>Seleccione una opción</option>
                  {temperatureFallback.map((t: string) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
                {errors.temperature && <p className="text-sm text-[#DC2626]">{errors.temperature.message}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#111827]">Humedad</label>
                <select {...register('humidity')} defaultValue="" className="w-full rounded-xl border border-[#E5E7EB] bg-white px-3 py-2 text-sm">
                  <option value="" disabled>Seleccione una opción</option>
                  {humidityFallback.map((h: string) => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
                {errors.humidity && <p className="text-sm text-[#DC2626]">{errors.humidity.message}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#111827]">Tipo de suelo</label>
                <select {...register('soil_type')} defaultValue="" className="w-full rounded-xl border border-[#E5E7EB] bg-white px-3 py-2 text-sm">
                  <option value="" disabled>Seleccione una opción</option>
                  {soilFallback.map((s: string) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                {errors.soil_type && <p className="text-sm text-[#DC2626]">{errors.soil_type.message}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#111827]">Calidad del agua</label>
                <select {...register('water_quality')} defaultValue="" className="w-full rounded-xl border border-[#E5E7EB] bg-white px-3 py-2 text-sm">
                  <option value="" disabled>Seleccione una opción</option>
                  {waterFallback.map((w: string) => (
                    <option key={w} value={w}>{w}</option>
                  ))}
                </select>
                {errors.water_quality && <p className="text-sm text-[#DC2626]">{errors.water_quality.message}</p>}
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => navigate('/zones')}
                className="rounded-xl border border-[#D1D5DB] bg-white px-4 py-2 text-sm font-semibold text-[#111827] hover:bg-[#F7F8F2]"
              >
                Cancelar
              </button>
              <button type="submit" disabled={isSubmitting} className="rounded-xl bg-[#16A34A] px-4 py-2 text-sm font-semibold text-white hover:bg-[#14532D] disabled:opacity-60">
                {isSubmitting ? 'Guardando...' : 'Guardar zona'}
              </button>
            </div>
          </form>

          <Toast.Root open={toastOpen} onOpenChange={setToastOpen} className="z-[100] w-[calc(100vw-2rem)] max-w-md rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-xl">
            <Toast.Title className="text-sm font-semibold text-[#111827]">{toastTitle}</Toast.Title>
            <Toast.Description className="mt-1 text-sm text-[#6B7280]">{toastDescription}</Toast.Description>
          </Toast.Root>
          <Toast.Viewport className="fixed bottom-4 right-4 z-[101] flex w-auto max-w-sm flex-col gap-2 outline-none" />
        </section>
      </AppLayout>
    </Toast.Provider>
  )
}
