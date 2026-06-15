import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import axios from 'axios'
import * as Toast from '@radix-ui/react-toast'
import { Key, Lock, Mail, Phone, ShieldCheck, UserRound } from 'lucide-react'

import { AppLayout } from '@/features/layout/AppLayout'
import { useAuthStore } from '@/stores/authStore'

const profileSchema = z
  .object({
    identification: z.string().min(1),
    fullName: z.string().trim().min(3, 'Ingrese su nombre completo.'),
    email: z.string().trim().email('Ingrese un correo electrónico válido.'),
    phone: z
      .string()
      .trim()
      .regex(/^\+506\s\d{4}\s\d{4}$/, 'Ingrese un teléfono válido con formato +506 8888 8888.'),
    currentPassword: z.string().optional().or(z.literal('')),
    newPassword: z.string().optional().or(z.literal('')),
    confirmPassword: z.string().optional().or(z.literal('')),
  })
  .refine((data) => !data.newPassword || data.newPassword.length >= 6, {
    message: 'La contraseña debe tener al menos 6 caracteres.',
    path: ['newPassword'],
  })
  .refine((data) => !data.newPassword || data.newPassword === data.confirmPassword, {
    message: 'Las contraseñas no coinciden.',
    path: ['confirmPassword'],
  })
  .refine((data) => !data.newPassword || data.currentPassword, {
    message: 'Debe ingresar su contraseña actual.',
    path: ['currentPassword'],
  })

type AccountFormValues = z.infer<typeof profileSchema>

export function AccountPage() {
  const token = useAuthStore((state) => state.token)
  const user = useAuthStore((state) => state.user)
  const login = useAuthStore((state) => state.login)
  const [toastOpen, setToastOpen] = useState(false)
  const [toastTitle, setToastTitle] = useState('')
  const [toastDescription, setToastDescription] = useState('')

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
      currentPassword: '',
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
        reset({
          identification: profile.identification ?? '',
          fullName: profile.full_name ?? '',
          email: profile.email ?? '',
          phone: profile.phone?.replace(/-/g, ' ') ?? '+506 8888 8888',
          currentPassword: '',
          newPassword: '',
          confirmPassword: '',
        })
        login(token, {
          id: profile.id ?? user?.id ?? 'demo-user',
          identification: profile.identification ?? user?.identification ?? '',
          full_name: profile.full_name ?? user?.full_name ?? '',
          email: profile.email ?? user?.email ?? '',
        })
      } catch {
        // Fallback to current store values.
      }
    }

    void loadProfile()
  }, [token, user?.email, user?.full_name, user?.identification, user?.id, login, reset])

  const onSubmit = async (values: AccountFormValues) => {
    try {
      const requests: Promise<unknown>[] = []
      const profileChanged =
        values.fullName.trim() !== (user?.full_name ?? '') ||
        values.email.trim() !== (user?.email ?? '') ||
        values.phone.trim() !== '+506 8888 8888'

      if (profileChanged) {
        requests.push(
          axios.put(
            '/api/v1/users/me',
            {
              full_name: values.fullName.trim(),
              email: values.email.trim(),
              phone: values.phone.trim(),
            },
            { headers: { Authorization: `Bearer ${token}` } },
          ),
        )
      }

      if (values.newPassword && values.currentPassword) {
        requests.push(
          axios.put(
            '/api/v1/users/me/password',
            {
              current_password: values.currentPassword,
              new_password: values.newPassword,
            },
            { headers: { Authorization: `Bearer ${token}` } },
          ),
        )
      }

      await Promise.all(requests)

      if (profileChanged) {
        login(token ?? '', {
          id: user?.id ?? 'demo-user',
          identification: values.identification,
          full_name: values.fullName.trim(),
          email: values.email.trim(),
        })
      }

      setToastTitle('Cambios guardados')
      setToastDescription('Tu perfil y/o contraseña se actualizaron correctamente.')
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
        <section className="mx-auto flex max-w-6xl flex-col gap-6">
          <header className="flex flex-col gap-2">
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-primary-700">Mi cuenta</p>
            <h1 className="text-3xl font-semibold text-[#111827]">Configuración de perfil y seguridad</h1>
            <p className="text-sm text-[#6B7280]">Actualiza tus datos personales y cambia la contraseña si es necesario.</p>
          </header>

          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)} noValidate>
            <article className="rounded-3xl border border-[#E5E7EB] bg-white p-6 shadow-sm sm:p-8">
              <div className="mb-6 flex items-center gap-3">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-primary-50 text-primary-700 ring-1 ring-primary-100">
                  <UserRound className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-[#111827]">Datos personales</h2>
                  <p className="text-sm text-[#6B7280]">Tu identidad permanece protegida y solo lectura.</p>
                </div>
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-[#111827]">Número de identificación</label>
                  <input
                    type="text"
                    disabled
                    className="w-full rounded-xl border border-[#E5E7EB] bg-[#F7F8F2] px-4 py-3 text-sm text-[#111827] shadow-sm"
                    {...register('identification')}
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="fullName" className="text-sm font-medium text-[#111827]">Nombre completo</label>
                  <input
                    id="fullName"
                    type="text"
                    className="w-full rounded-xl border border-[#E5E7EB] bg-white px-4 py-3 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                    {...register('fullName')}
                  />
                  {errors.fullName && <p className="text-sm text-[#DC2626]">{errors.fullName.message}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium text-[#111827]">Correo electrónico</label>
                  <div className="relative">
                    <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                      <Mail className="h-4 w-4" />
                    </span>
                    <input
                      id="email"
                      type="email"
                      className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      {...register('email')}
                    />
                  </div>
                  {errors.email && <p className="text-sm text-[#DC2626]">{errors.email.message}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="phone" className="text-sm font-medium text-[#111827]">Teléfono</label>
                  <div className="relative">
                    <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                      <Phone className="h-4 w-4" />
                    </span>
                    <input
                      id="phone"
                      type="text"
                      className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      {...register('phone')}
                    />
                  </div>
                  {errors.phone && <p className="text-sm text-[#DC2626]">{errors.phone.message}</p>}
                </div>
              </div>
            </article>

            <article className="rounded-3xl border border-[#E5E7EB] bg-white p-6 shadow-sm sm:p-8">
              <div className="mb-4 flex items-center gap-3 border-b border-[#E5E7EB] pb-4">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-primary-50 text-primary-700 ring-1 ring-primary-100">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-[#111827]">Seguridad</h2>
                  <p className="text-sm text-[#6B7280]">Actualiza tu contraseña cuando lo necesites.</p>
                </div>
              </div>

              <div className="grid gap-5 md:grid-cols-3">
                <div className="space-y-2">
                  <label htmlFor="currentPassword" className="text-sm font-medium text-[#111827]">Contraseña actual</label>
                  <div className="relative">
                    <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                      <Key className="h-4 w-4" />
                    </span>
                    <input
                      id="currentPassword"
                      type="password"
                      placeholder="••••••••"
                      className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      {...register('currentPassword')}
                    />
                  </div>
                  {errors.currentPassword && <p className="text-sm text-[#DC2626]">{errors.currentPassword.message}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="newPassword" className="text-sm font-medium text-[#111827]">Contraseña nueva</label>
                  <div className="relative">
                    <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                      <Lock className="h-4 w-4" />
                    </span>
                    <input
                      id="newPassword"
                      type="password"
                      placeholder="••••••••"
                      className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      {...register('newPassword')}
                    />
                  </div>
                  {errors.newPassword && <p className="text-sm text-[#DC2626]">{errors.newPassword.message}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="confirmPassword" className="text-sm font-medium text-[#111827]">Confirmar contraseña nueva</label>
                  <div className="relative">
                    <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                      <Lock className="h-4 w-4" />
                    </span>
                    <input
                      id="confirmPassword"
                      type="password"
                      placeholder="••••••••"
                      className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      {...register('confirmPassword')}
                    />
                  </div>
                  {errors.confirmPassword && <p className="text-sm text-[#DC2626]">{errors.confirmPassword.message}</p>}
                </div>
              </div>
            </article>

            <div className="flex flex-col-reverse justify-end gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => {
                  reset({
                    identification: user?.identification ?? '',
                    fullName: user?.full_name ?? '',
                    email: user?.email ?? '',
                    phone: '+506 8888 8888',
                    currentPassword: '',
                    newPassword: '',
                    confirmPassword: '',
                  })
                }}
                className="rounded-xl border border-[#D1D5DB] bg-white px-4 py-3 text-sm font-semibold text-[#111827] shadow-sm transition hover:bg-[#F7F8F2]"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="rounded-xl bg-[#16A34A] px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#14532D] disabled:cursor-not-allowed disabled:bg-primary-300"
              >
                {isSubmitting ? 'Guardando...' : 'Guardar cambios'}
              </button>
            </div>
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