import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import axios from 'axios'
import { useNavigate, Link } from 'react-router-dom'
import * as Toast from '@radix-ui/react-toast'
import { Lock, ShieldCheck, UserRound } from 'lucide-react'

import { useAuthStore } from '@/stores/authStore'
import { AuthLayout } from './AuthLayout'

const loginSchema = z.object({
  identification: z
    .string()
    .trim()
    .min(1, 'El número de identificación es obligatorio.')
    .regex(/^\d{1}\s\d{4}\s\d{4}$/, 'Ingrese una cédula válida con formato 0 0000 0000.'),
  password: z.string().min(6, 'La contraseña debe tener al menos 6 caracteres.'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export function LoginPage() {
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)
  const [toastOpen, setToastOpen] = useState(false)
  const [toastTitle, setToastTitle] = useState('')
  const [toastDescription, setToastDescription] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      identification: '',
      password: '',
    },
  })

  const formatIdentification = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 10)
    if (digits.length <= 1) return digits
    if (digits.length <= 5) return `${digits.slice(0, 1)} ${digits.slice(1)}`
    return `${digits.slice(0, 1)} ${digits.slice(1, 5)} ${digits.slice(5)}`.trimEnd()
  }

  const onSubmit = async (values: LoginFormValues) => {
    try {
      const normalizedIdentification = values.identification.replace(/\s+/g, '')
      const response = await axios.post('/api/v1/auth/login', {
        identification: normalizedIdentification,
        password: values.password,
      })

      const { access_token, user } = response.data
      login(access_token, user)
      setToastTitle('Inicio de sesión exitoso')
      setToastDescription('Redirigiendo a tu zona protegida...')
      setToastOpen(true)
      window.setTimeout(() => navigate('/dashboard'), 300)
    } catch (error: unknown) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail ?? 'No fue posible iniciar sesión. Verifique sus credenciales.'
        : 'No fue posible iniciar sesión. Intente nuevamente.'
      setToastTitle('No se pudo iniciar sesión')
      setToastDescription(String(message))
      setToastOpen(true)
    }
  }

  const identificationHint = useMemo(() => 'Formato sugerido: 1 2345 6789', [])

  return (
    <Toast.Provider swipeDirection="right">
      <AuthLayout
        title="Iniciar sesión"
        subtitle="Ingrese sus credenciales para acceder a su cuenta"
      >
        <form className="space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="space-y-2">
            <label htmlFor="identification" className="text-sm font-medium text-[#111827]">
              Número de Identificación
            </label>
            <div className="relative">
              <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                <UserRound className="h-4 w-4" />
              </span>
              <input
                id="identification"
                type="text"
                inputMode="numeric"
                autoComplete="username"
                placeholder="0 0000 0000"
                className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                {...register('identification', {
                  onChange: (event) => {
                    const formatted = formatIdentification(event.target.value)
                    setValue('identification', formatted, { shouldValidate: true })
                  },
                })}
              />
            </div>
            <p className="text-xs text-[#6B7280]">{identificationHint}</p>
            {errors.identification && (
              <p className="text-sm text-[#DC2626]">{errors.identification.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium text-[#111827]">
              Contraseña
            </label>
            <div className="relative">
              <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                <Lock className="h-4 w-4" />
              </span>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                {...register('password')}
              />
            </div>
            {errors.password && <p className="text-sm text-[#DC2626]">{errors.password.message}</p>}
          </div>

          <div className="flex items-center justify-between gap-3 text-sm">
            <button
              type="button"
              className="text-[#6B7280] transition hover:text-primary-700"
            >
              ¿Olvidaste tu contraseña?
            </button>
            <div className="inline-flex items-center gap-1 rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700 ring-1 ring-primary-100">
              <ShieldCheck className="h-3.5 w-3.5" />
              Sesión segura
            </div>
          </div>

          <div className="space-y-3 pt-1">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-xl bg-[#16A34A] px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#14532D] disabled:cursor-not-allowed disabled:bg-primary-300"
            >
              {isSubmitting ? 'Iniciando sesión...' : 'Iniciar sesión'}
            </button>

            <Link
              to="/register"
              className="block w-full rounded-xl border border-[#16A34A] bg-transparent px-4 py-3 text-center text-sm font-semibold text-[#16A34A] transition hover:bg-primary-50"
            >
              Crear cuenta
            </Link>
          </div>
        </form>

        <Toast.Root
          open={toastOpen}
          onOpenChange={setToastOpen}
          className="z-[100] w-[calc(100vw-2rem)] max-w-md rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-xl data-[state=open]:animate-in data-[state=closed]:animate-out"
        >
          <Toast.Title className="text-sm font-semibold text-[#111827]">{toastTitle}</Toast.Title>
          <Toast.Description className="mt-1 text-sm text-[#6B7280]">{toastDescription}</Toast.Description>
        </Toast.Root>
        <Toast.Viewport className="fixed bottom-4 right-4 z-[101] flex w-auto max-w-sm flex-col gap-2 outline-none" />
      </AuthLayout>
    </Toast.Provider>
  )
}
