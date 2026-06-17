import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as Toast from '@radix-ui/react-toast'
import { Edit2, MapPin, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { IconStat, PageHeader, Panel, SynapButton } from '@/components/ui/prototype'
import { zonesApi, type ZonePayload } from '@/lib/api'

type Zone = ZonePayload

export function ZonesPage() {
  const token = useAuthStore((state) => state.token)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [toastOpen, setToastOpen] = useState(false)
  const [toastTitle, setToastTitle] = useState('')
  const [toastDescription, setToastDescription] = useState('')

  const { data: zones = [], isLoading } = useQuery<Zone[]>({
    queryKey: ['zones'],
    queryFn: () => zonesApi.list(token),
    enabled: !!token,
  })

  const deleteZoneMutation = useMutation({
    mutationFn: (id: string | number) => zonesApi.delete(token, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['zones'] })
      setToastTitle('Zona eliminada')
      setToastDescription('La zona fue eliminada correctamente.')
      setToastOpen(true)
    },
    onError: () => {
      setToastTitle('Error')
      setToastDescription('No fue posible eliminar la zona.')
      setToastOpen(true)
    },
  })

  return (
    <Toast.Provider swipeDirection="right">
      <AppLayout>
        <section className="max-w-[1140px]">
          <PageHeader
            title="Gestión de zonas"
            subtitle="Administre las zonas o fincas agrícolas asociadas a su cuenta"
            action={
              <SynapButton className="mt-2 min-w-[190px]" onClick={() => navigate('/zones/new')}>
                <Plus className="h-5 w-5" />
                Añadir zona
              </SynapButton>
            }
          />

          <div className="mb-8 grid gap-7 md:grid-cols-2">
            <IconStat label="Total de zonas" value={zones.length} icon={MapPin} />
            <IconStat label="Última actualización" value="Hoy" icon={RefreshCw} />
          </div>

          <Panel className="overflow-hidden p-7">
            <h2 className="mb-6 text-2xl font-bold text-[#111827]">Zonas o fincas añadidas</h2>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[860px] border-collapse text-left">
                <thead>
                  <tr className="border-b border-[#E5E7EB] text-lg font-semibold text-[#6B7280]">
                    <th className="py-4 pr-4">Nombre</th>
                    <th className="px-4 py-4">Cultivo principal</th>
                    <th className="px-4 py-4">Tipo de suelo</th>
                    <th className="px-4 py-4">Humedad</th>
                    <th className="px-4 py-4">Temperatura</th>
                    <th className="px-4 py-4">Acciones</th>
                  </tr>
                </thead>
                <tbody className="text-lg text-[#111827]">
                  {isLoading ? (
                    <tr>
                      <td colSpan={6} className="py-10 text-center text-[#6B7280]">
                        Cargando zonas...
                      </td>
                    </tr>
                  ) : zones.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-10 text-center text-[#6B7280]">
                        No hay zonas registradas.
                      </td>
                    </tr>
                  ) : (
                    zones.map((zone) => (
                      <tr key={zone.id} className="border-b border-[#E5E7EB] last:border-b-0">
                        <td className="py-5 pr-4 font-medium">{zone.name}</td>
                        <td className="px-4 py-5">{zone.crop ?? 'No disponible'}</td>
                        <td className="px-4 py-5">{zone.soil_type}</td>
                        <td className="px-4 py-5">{zone.humidity}</td>
                        <td className="px-4 py-5">{zone.temperature}</td>
                        <td className="px-4 py-5">
                          <div className="flex items-center gap-3">
                            <button
                              type="button"
                              onClick={() => navigate('/zones/new', { state: { zone } })}
                              className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-white text-[#16A34A] ring-1 ring-[#E5E7EB] transition hover:bg-[#E8F7EE]"
                              aria-label="Editar zona"
                            >
                              <Edit2 className="h-5 w-5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => void deleteZoneMutation.mutateAsync(zone.id)}
                              className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-white text-[#DC2626] ring-1 ring-[#E5E7EB] transition hover:bg-[#FEF2F2]"
                              aria-label="Eliminar zona"
                            >
                              <Trash2 className="h-5 w-5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Panel>
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
