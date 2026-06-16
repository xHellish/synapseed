import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import axios from 'axios'
import { useNavigate, Link } from 'react-router-dom'
import * as Toast from '@radix-ui/react-toast'
import { Lock, UserRound } from 'lucide-react'

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
      // Mock para desarrollo sin backend
      // Cuando haya backend, descomentar las líneas de axios.post
      // y eliminar el bloque mock
      const access_token = 'mock-token-12345'
      const user = {
        id: '1',
        identification: '1234567890',
        full_name: 'Usuario de Prueba',
        email: 'usuario@prueba.com',
      }

      login(access_token, user)
      setToastTitle('Inicio de sesión exitoso')
      setToastDescription('Redirigiendo a tu zona protegida...')
      setToastOpen(true)
      window.setTimeout(() => navigate('/zones'), 300)
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
        <form className="mt-6 space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
          {/* Número de Identificación */}
          <div className="space-y-2">
            <label htmlFor="identification" className="text-sm font-medium text-[#111827]">
              Número de Identificación
            </label>
            <div className="relative">
              <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#16A34A]">
                <UserRound className="h-4 w-4" />
              </span>
              <input
                id="identification"
                type="text"
                inputMode="numeric"
                autoComplete="username"
                placeholder="0 0000 0000"
                className="w-full rounded-lg border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] placeholder-[#6B7280] shadow-sm transition focus:border-[#16A34A] focus:outline-none focus:ring-2 focus:ring-[#16A34A]/20"
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

          {/* Contraseña */}
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium text-[#111827]">
              Contraseña
            </label>
            <div className="relative">
              <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#16A34A]">
                <Lock className="h-4 w-4" />
              </span>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="********"
                className="w-full rounded-lg border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] placeholder-[#6B7280] shadow-sm transition focus:border-[#16A34A] focus:outline-none focus:ring-2 focus:ring-[#16A34A]/20"
                {...register('password')}
              />
            </div>
            {errors.password && <p className="text-sm text-[#DC2626]">{errors.password.message}</p>}
          </div>

          {/* Botón Iniciar sesión */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-[#16A34A] px-4 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-[#15803D] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? 'Iniciando sesión...' : 'Iniciar sesión'}
          </button>

          {/* Enlace ¿Olvidaste tu contraseña? */}
          <div className="text-center">
            <button
              type="button"
              className="text-sm text-[#6B7280] transition hover:text-[#16A34A]"
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>

          {/* Botón Crear cuenta */}
          <Link
            to="/register"
            className="block w-full rounded-lg border border-[#16A34A] bg-transparent px-4 py-3 text-center text-sm font-bold text-[#16A34A] transition hover:bg-[#16A34A]/5"
          >
            Crear cuenta
          </Link>
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