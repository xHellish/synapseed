import { useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useParams } from 'react-router-dom'
import { Leaf, Mail, MapPin, Phone } from 'lucide-react'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { useWizardStore } from '@/stores/wizardStore'
import { CaseStepper, PageHeader, Panel, SynapButton } from '@/components/ui/prototype'
import { buttonClasses } from '@/components/ui/prototypeStyles'
import { normalizeProviders, type ProviderPayload } from './recommendationMapper'

const DEMO_PROVIDERS = normalizeProviders([
  {
    id: 1,
    nombre: 'AgroServicios Tarrazú',
    producto_asociado: 'RoyaShield Sistémico',
    product_id: 1,
    telefono: '2546 - 6789',
    correo: 'ventas@agrotarrazu.cr',
    ubicacion: 'San Marcos de Tarrazú',
  },
  {
    id: 2,
    nombre: 'Insumos del Café Dota',
    producto_asociado: 'CuproCafé Preventivo',
    product_id: 2,
    telefono: '2541 - 6782',
    correo: 'info@insumosdota.cr',
    ubicacion: 'Santa María de Dota',
  },
  {
    id: 3,
    nombre: 'BioInsumos Los Santos',
    producto_asociado: 'BioRoya Trichoderma',
    product_id: 3,
    telefono: '2546 - 6783',
    correo: 'ventas@bioinsumosls.cr',
    ubicacion: 'San Pablo de León Cortés',
  },
])

export function CaseWizardStep4() {
  const token = useAuthStore((state) => state.token)
  const setStep = useWizardStore((state) => state.setStep)
  const { id } = useParams<{ id: string }>()
  const isDemo = !id || id === 'demo'

  useEffect(() => {
    setStep(4)
  }, [setStep])

  const {
    data: providersData,
    isLoading,
    isError,
  } = useQuery<ProviderPayload[]>({
    queryKey: ['providers', id],
    queryFn: async () => {
      if (isDemo) return []
      const response = await axios.get(`/api/v1/recommendations/${id}/providers`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    enabled: isDemo || !!token,
  })

  const providers = useMemo(
    () => (isDemo ? DEMO_PROVIDERS : normalizeProviders(providersData ?? [])),
    [isDemo, providersData],
  )

  if (isLoading) {
    return (
      <AppLayout>
        <section className="max-w-[1140px]">
          <CaseStepper step={4} />
          <Panel className="flex min-h-[360px] items-center justify-center p-10">
            <div className="flex flex-col items-center gap-4 text-[#6B7280]">
              <Leaf className="h-12 w-12 animate-pulse text-[#16A34A]" />
              <p className="text-lg font-semibold">Cargando proveedores...</p>
            </div>
          </Panel>
        </section>
      </AppLayout>
    )
  }

  if (isError || providers.length === 0) {
    return (
      <AppLayout>
        <section className="max-w-[1140px]">
          <CaseStepper step={4} />
          <Panel className="p-10 text-center">
            <p className="text-lg text-[#6B7280]">No se encontraron proveedores disponibles.</p>
          </Panel>
        </section>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <section className="max-w-[1140px]">
        <PageHeader
          title="Recomendaciones de productos"
          subtitle="Revise las opciones recomendadas basadas en su contexto"
          className="mb-5"
        />
        <CaseStepper step={4} />

        <div className="space-y-11">
          {providers.map((provider) => (
            <Panel
              key={provider.id}
              className="grid gap-8 px-8 py-7 md:grid-cols-[1fr_210px] md:items-center"
            >
              <div>
                <h3 className="text-2xl font-bold text-[#111827]">{provider.name}</h3>
                <p className="mt-4 text-xl text-[#6B7280]">
                  Producto asociado: <span className="font-semibold text-[#111827]">{provider.productName}</span>
                </p>
                <div className="mt-5 space-y-4 text-xl text-[#111827]">
                  <p className="flex items-center gap-4">
                    <Phone className="h-5 w-5 text-[#16A34A]" />
                    {provider.phone}
                  </p>
                  <p className="flex items-center gap-4">
                    <Mail className="h-5 w-5 text-[#16A34A]" />
                    {provider.email}
                  </p>
                  <p className="flex items-center gap-4">
                    <MapPin className="h-5 w-5 text-[#16A34A]" />
                    {provider.location}
                  </p>
                </div>
              </div>

              <div className="flex flex-col gap-4">
                <SynapButton
                  className="w-full"
                  onClick={() => {
                    const query = encodeURIComponent(`${provider.name} ${provider.productName}`)
                    window.open(`https://www.google.com/search?q=${query}`, '_blank')
                  }}
                >
                  Contactar
                </SynapButton>
                {provider.email !== 'No disponible' ? (
                  <a href={`mailto:${provider.email}`} className={buttonClasses({ variant: 'outline', className: 'w-full' })}>
                    Enviar correo
                  </a>
                ) : (
                  <SynapButton variant="outline" disabled className="w-full">
                    Enviar correo
                  </SynapButton>
                )}
              </div>
            </Panel>
          ))}
        </div>
      </section>
    </AppLayout>
  )
}

export default CaseWizardStep4
