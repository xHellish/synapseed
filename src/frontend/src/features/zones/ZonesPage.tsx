import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import * as Dialog from '@radix-ui/react-dialog'
import * as Toast from '@radix-ui/react-toast'
import { Plus, RefreshCw, Edit2, Trash2 } from 'lucide-react'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'

interface Zone {
  id: string
  name: string
  location: string
  soil_type: string
  humidity: string
  temperature: string
  water_quality: string
  user_id?: string
}

export function ZonesPage() {
  const token = useAuthStore((s) => s.token)
  const queryClient = useQueryClient()

  const [toastOpen, setToastOpen] = useState(false)
  const [toastTitle, setToastTitle] = useState('')
  const [toastDescription, setToastDescription] = useState('')

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingZone, setEditingZone] = useState<Zone | null>(null)

  const { data: zones = [], isLoading } = useQuery<Zone[]>({
    queryKey: ['zones'],
    queryFn: async () => {
      const res = await axios.get('/api/v1/zones', { headers: { Authorization: `Bearer ${token}` } })
      return res.data
    },
  })

  const addZoneMutation = useMutation({
    mutationFn: async (payload: Partial<Zone>) => {
      const res = await axios.post('/api/v1/zones', payload, { headers: { Authorization: `Bearer ${token}` } })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['zones'] })
      setToastTitle('Zona creada')
      setToastDescription('La zona fue añadida correctamente.')
      setToastOpen(true)
      setDialogOpen(false)
    },
    onError: () => {
      setToastTitle('Error')
      setToastDescription('No fue posible crear la zona.')
      setToastOpen(true)
    },
  })

  const updateZoneMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<Zone> }) => {
      const res = await axios.put(`/api/v1/zones/${id}`, payload, { headers: { Authorization: `Bearer ${token}` } })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['zones'] })
      setToastTitle('Zona actualizada')
      setToastDescription('Los cambios se guardaron correctamente.')
      setToastOpen(true)
      setDialogOpen(false)
      setEditingZone(null)
    },
  })

  const deleteZoneMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await axios.delete(`/api/v1/zones/${id}`, { headers: { Authorization: `Bearer ${token}` } })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['zones'] })
      setToastTitle('Zona eliminada')
      setToastDescription('La zona fue eliminada correctamente.')
      setToastOpen(true)
    },
  })

  const openCreate = () => {
    setEditingZone(null)
    setDialogOpen(true)
  }

  const openEdit = (zone: Zone) => {
    setEditingZone(zone)
    setDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const payload = {
      name: String(form.get('name') ?? '').trim(),
      location: String(form.get('location') ?? '').trim(),
      soil_type: String(form.get('soil_type') ?? '').trim(),
      humidity: String(form.get('humidity') ?? '').trim(),
      temperature: String(form.get('temperature') ?? '').trim(),
      water_quality: String(form.get('water_quality') ?? '').trim(),
    }

    try {
      if (editingZone) {
        await updateZoneMutation.mutateAsync({ id: editingZone.id, payload })
      } else {
        await addZoneMutation.mutateAsync(payload)
      }
    } catch (err) {
      // handled in mutations
    }
  }

  return (
    <Toast.Provider swipeDirection="right">
      <AppLayout>
        <section className="mx-auto max-w-6xl">
          <header className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-semibold text-[#111827]">Gestión de zonas</h1>
              <p className="mt-1 text-sm text-[#6B7280]">Administre las zonas o fincas agrícolas asociadas a su cuenta</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => void queryClient.invalidateQueries({ queryKey: ['zones'] })}
                className="inline-flex items-center gap-2 rounded-xl border border-[#E5E7EB] bg-white px-3 py-2 text-sm text-[#111827] shadow-sm hover:bg-[#F7F8F2]"
              >
                <RefreshCw className="h-4 w-4 text-primary-600" />
                Actualizar
              </button>

              <button
                type="button"
                onClick={openCreate}
                className="inline-flex items-center gap-2 rounded-xl bg-[#16A34A] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#14532D]"
              >
                <Plus className="h-4 w-4" />
                + Añadir zona
              </button>
            </div>
          </header>

          <div className="mb-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-[#6B7280]">Total de zonas</p>
              <div className="mt-3 flex items-end gap-3">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                  <Plus className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-3xl font-semibold text-[#111827]">{zones.length}</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-[#6B7280]">Última actualización</p>
              <div className="mt-3 flex items-end gap-3">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                  <RefreshCw className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-[#111827]">Hoy</p>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-[#111827]">Zonas o fincas añadidas</h2>

            {/* Table for desktop, cards for mobile */}
            <div className="hidden md:block">
              <table className="w-full table-auto">
                <thead>
                  <tr className="text-left text-sm text-[#6B7280]">
                    <th className="px-3 py-2">Nombre</th>
                    <th className="px-3 py-2">Ubicación</th>
                    <th className="px-3 py-2">Tipo de suelo</th>
                    <th className="px-3 py-2">Humedad</th>
                    <th className="px-3 py-2">Temperatura</th>
                    <th className="px-3 py-2">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    <tr>
                      <td colSpan={6} className="px-3 py-6 text-center text-sm text-[#6B7280]">Cargando zonas...</td>
                    </tr>
                  ) : zones.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-3 py-6 text-center text-sm text-[#6B7280]">No hay zonas registradas.</td>
                    </tr>
                  ) : (
                    zones.map((z) => (
                      <tr key={z.id} className="border-t border-[#F1F5F9]">
                        <td className="px-3 py-4 text-sm text-[#111827]">{z.name}</td>
                        <td className="px-3 py-4 text-sm text-[#111827]">{z.location}</td>
                        <td className="px-3 py-4 text-sm text-[#111827]">{z.soil_type}</td>
                        <td className="px-3 py-4 text-sm text-[#111827]">{z.humidity}</td>
                        <td className="px-3 py-4 text-sm text-[#111827]">{z.temperature}</td>
                        <td className="px-3 py-4 text-sm">
                          <div className="inline-flex gap-2">
                            <button
                              type="button"
                              onClick={() => openEdit(z)}
                              className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-white text-[#16A34A] shadow-sm ring-1 ring-[#E5E7EB] hover:bg-primary-50"
                              aria-label="Editar zona"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => void deleteZoneMutation.mutateAsync(z.id)}
                              className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-white text-[#DC2626] shadow-sm ring-1 ring-[#E5E7EB] hover:bg-[#FFF1F2]"
                              aria-label="Eliminar zona"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="grid gap-4 md:hidden">
              {isLoading ? (
                <div className="text-sm text-[#6B7280]">Cargando zonas...</div>
              ) : zones.length === 0 ? (
                <div className="text-sm text-[#6B7280]">No hay zonas registradas.</div>
              ) : (
                zones.map((z) => (
                  <div key={z.id} className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-[#6B7280]">{z.name}</p>
                        <p className="mt-1 text-sm text-[#111827]">{z.location} · {z.soil_type}</p>
                      </div>
                      <div className="inline-flex gap-2">
                        <button
                          type="button"
                          onClick={() => openEdit(z)}
                          className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-white text-[#16A34A] shadow-sm ring-1 ring-[#E5E7EB] hover:bg-primary-50"
                          aria-label="Editar zona"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => void deleteZoneMutation.mutateAsync(z.id)}
                          className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-white text-[#DC2626] shadow-sm ring-1 ring-[#E5E7EB] hover:bg-[#FFF1F2]"
                          aria-label="Eliminar zona"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                    <div className="mt-3 text-sm text-[#6B7280]">Humedad: {z.humidity} · Temp: {z.temperature}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Dialog for create/edit */}
          <Dialog.Root open={dialogOpen} onOpenChange={setDialogOpen}>
            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 bg-black/30" />
              <Dialog.Content
                className="fixed left-1/2 top-1/2 w-[min(96vw,600px)] -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-6 shadow-lg"
                aria-describedby={undefined}
              >
                <Dialog.Title className="text-lg font-semibold">{editingZone ? 'Editar zona' : 'Añadir zona'}</Dialog.Title>
                <form onSubmit={handleSubmit} className="mt-4 space-y-3">
                  <div className="grid gap-3 md:grid-cols-2">
                    <input name="name" defaultValue={editingZone?.name ?? ''} placeholder="Nombre de la zona" className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2" />
                    <input name="location" defaultValue={editingZone?.location ?? ''} placeholder="Ubicación" className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2" />
                    <select name="soil_type" defaultValue={editingZone?.soil_type ?? ''} className="w-full rounded-xl border border-[#E5E7EB] bg-white px-3 py-2">
                      <option value="" disabled>Seleccione tipo de suelo</option>
                      <option value="Franco">Franco</option>
                      <option value="Arcilloso">Arcilloso</option>
                      <option value="Franco Arcilloso">Franco Arcilloso</option>
                      <option value="Arenoso">Arenoso</option>
                      <option value="Volcánico">Volcánico</option>
                      <option value="Limoso">Limoso</option>
                    </select>
                    <select name="humidity" defaultValue={editingZone?.humidity ?? ''} className="w-full rounded-xl border border-[#E5E7EB] bg-white px-3 py-2">
                      <option value="" disabled>Seleccione humedad</option>
                      <option value="Muy baja">Muy baja</option>
                      <option value="Baja">Baja</option>
                      <option value="Media">Media</option>
                      <option value="Alta">Alta</option>
                      <option value="Muy alta">Muy alta</option>
                    </select>
                    <select name="temperature" defaultValue={editingZone?.temperature ?? ''} className="w-full rounded-xl border border-[#E5E7EB] bg-white px-3 py-2">
                      <option value="" disabled>Seleccione temperatura</option>
                      <option value="Menos de 10°C">Menos de 10°C</option>
                      <option value="10°C - 15°C">10°C - 15°C</option>
                      <option value="15°C - 20°C">15°C - 20°C</option>
                      <option value="20°C - 25°C">20°C - 25°C</option>
                      <option value="25°C - 30°C">25°C - 30°C</option>
                      <option value="Más de 30°C">Más de 30°C</option>
                    </select>
                    <select name="water_quality" defaultValue={editingZone?.water_quality ?? ''} className="w-full rounded-xl border border-[#E5E7EB] bg-white px-3 py-2">
                      <option value="" disabled>Seleccione calidad del agua</option>
                      <option value="Potable">Potable</option>
                      <option value="Regular">Regular</option>
                      <option value="Salina">Salina</option>
                      <option value="Buena">Buena</option>
                      <option value="Contaminada">Contaminada</option>
                      <option value="Desconocida">Desconocida</option>
                    </select>
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <button type="button" onClick={() => setDialogOpen(false)} className="rounded-xl border border-[#D1D5DB] bg-white px-4 py-2 text-sm font-semibold text-[#111827]">Cancelar</button>
                    <button type="submit" className="rounded-xl bg-[#16A34A] px-4 py-2 text-sm font-semibold text-white hover:bg-[#14532D]">{editingZone ? 'Guardar' : 'Crear'}</button>
                  </div>
                </form>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>

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
