import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import axios from 'axios'
import * as Toast from '@radix-ui/react-toast'
import { Lock, UserRound } from 'lucide-react'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'
import { PageHeader, Panel, SectionTitle, SynapButton, TextField } from '@/components/ui/prototype'

const profileSchema = z
  .object({
    identification: z.string().min(1),
    fullName: z.string().trim().min(3, 'Ingrese su nombre completo.'),
    email: z.string().trim().email('Ingrese un correo electrónico válido.'),
    phone: z
      .string()
      .trim()
      .regex(/^\+?[\d\s-]{8,20}$/, 'Ingrese un número de teléfono válido (mínimo 8 dígitos).'),
    newPassword: z.string().optional().or(z.literal('')),
    confirmPassword: z.string().optional().or(z.literal('')),
  })
  .refine((data) => !data.newPassword || data.newPassword.length >= 8, {
    message: 'La contraseña debe tener al menos 8 caracteres.',
    path: ['newPassword'],
  })
  .refine((data) => !data.newPassword || data.newPassword === data.confirmPassword, {
    message: 'Las contraseñas no coinciden.',
    path: ['confirmPassword'],
  })

type AccountFormValues = z.infer<typeof profileSchema>

export function AccountPage() {
  const token = useAuthStore((state) => state.token)
  const user = useAuthStore((state) => state.user)
  const login = useAuthStore((state) => state.login)
  const [toastOpen, setToastOpen] = useState(false)
  const [toastTitle, setToastTitle] = useState('')
  const [toastDescription, setToastDescription] = useState('')
  const [originalPhone, setOriginalPhone] = useState('+506 8888 8888')

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AccountFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      identification: user?.identification ?? '',
      fullName: user?.full_name ?? '',
      email: user?.email ?? '',
      phone: '+506 8888 8888',
      newPassword: '',
      confirmPassword: '',
    },
  })

  useEffect(() => {
    const loadProfile = async () => {
      if (!token) return
      try {
        const response = await axios.get('/api/v1/users/me', {
          headers: { Authorization: `Bearer ${token}` },
        })
        const profile = response.data
        const phoneVal = profile.phone?.replace(/-/g, ' ') ?? '+506 8888 8888'
        setOriginalPhone(phoneVal)
        reset({
          identification: profile.identification ?? '',
          fullName: profile.full_name ?? '',
          email: profile.email ?? '',
          phone: phoneVal,
          newPassword: '',
          confirmPassword: '',
        })
        login(token, {
          id: String(profile.id ?? user?.id ?? 'demo-user'),
          identification: profile.identification ?? user?.identification ?? '',
          full_name: profile.full_name ?? user?.full_name ?? '',
          email: profile.email ?? user?.email ?? '',
        })
      } catch {
        // Keep persisted values if the profile endpoint is not available.
      }
    }

    void loadProfile()
  }, [token, user?.email, user?.full_name, user?.identification, user?.id, login, reset])

  const resetToUser = () => {
    reset({
      identification: user?.identification ?? '',
      fullName: user?.full_name ?? '',
      email: user?.email ?? '',
      phone: originalPhone,
      newPassword: '',
      confirmPassword: '',
    })
  }

  const onSubmit = async (values: AccountFormValues) => {
    try {
      const profileChanged =
        values.fullName.trim() !== (user?.full_name ?? '') ||
        values.email.trim() !== (user?.email ?? '') ||
        values.phone.trim() !== originalPhone

      if (values.newPassword) {
        setToastTitle('Contraseña no actualizada')
        setToastDescription('El backend actual requiere contraseña actual; el prototipo solo muestra contraseña nueva.')
        setToastOpen(true)
        return
      }

      if (profileChanged) {
        await axios.put(
          '/api/v1/users/me',
          {
            full_name: values.fullName.trim(),
            email: values.email.trim(),
            phone: values.phone.trim(),
          },
          { headers: { Authorization: `Bearer ${token}` } },
        )

        setOriginalPhone(values.phone.trim())

        login(token ?? '', {
          id: user?.id ?? 'demo-user',
          identification: values.identification,
          full_name: values.fullName.trim(),
          email: values.email.trim(),
        })
      }

      setToastTitle('Cambios guardados')
      setToastDescription('Tu perfil se actualizó correctamente.')
      setToastOpen(true)
    } catch (error: unknown) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail ?? 'No fue posible actualizar la información.'
        : 'No fue posible actualizar la información.'
      setToastTitle('No se pudieron guardar los cambios')
      setToastDescription(String(message))
      setToastOpen(true)
    }
  }

  return (
    <Toast.Provider swipeDirection="right">
      <AppLayout>
        <section className="max-w-[1140px]">
          <PageHeader
            title="Mi cuenta"
            subtitle="Actualice su información personal y credenciales de acceso"
          />

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <Panel className="px-10 py-8">
              <SectionTitle icon={UserRound}>Datos personales</SectionTitle>
              <div className="grid gap-x-10 gap-y-6 md:grid-cols-2">
                <TextField
                  label="Número de identificación:"
                  type="text"
                  disabled
                  {...register('identification')}
                />
                <TextField label="Nombre completo:" type="text" error={errors.fullName?.message} {...register('fullName')} />
                <TextField label="Correo electrónico:" type="email" error={errors.email?.message} {...register('email')} />
                <TextField label="Teléfono:" type="text" error={errors.phone?.message} {...register('phone')} />
              </div>

              <SectionTitle icon={Lock} className="mt-10">
                Seguridad
              </SectionTitle>
              <div className="grid gap-x-10 gap-y-6 md:grid-cols-2">
                <TextField
                  label="Contraseña nueva:"
                  type="password"
                  placeholder="********"
                  error={errors.newPassword?.message}
                  {...register('newPassword')}
                />
                <TextField
                  label="Confirmar contraseña nueva:"
                  type="password"
                  placeholder="********"
                  error={errors.confirmPassword?.message}
                  {...register('confirmPassword')}
                />
              </div>

              <div className="mt-12 flex flex-col justify-end gap-4 border-t border-[#9CA3AF] pt-6 sm:flex-row">
                <SynapButton type="button" variant="outline" className="min-w-[210px]" onClick={resetToUser}>
                  Cancelar
                </SynapButton>
                <SynapButton type="submit" disabled={isSubmitting} className="min-w-[230px]">
                  {isSubmitting ? 'Guardando...' : 'Guardar cambios'}
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
