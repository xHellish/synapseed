import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import axios from 'axios'
import { useNavigate, Link } from 'react-router-dom'
import * as Toast from '@radix-ui/react-toast'
import { Lock, UserRound } from 'lucide-react'

import { useAuthStore } from '@/stores/authStore'
import { SynapButton, TextField } from '@/components/ui/prototype'
import { buttonClasses } from '@/components/ui/prototypeStyles'
import { getApiErrorMessage } from '@/lib/apiError'
import { AuthLayout } from './AuthLayout'

const loginSchema = z.object({
  identification: z
    .string()
    .trim()
    .min(1, 'El número de identificación es obligatorio.')
    .regex(/^\d\s\d{4}\s\d{4,5}$/, 'Ingrese una cédula válida con formato 0 0000 0000.'),
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
      const rawIdentification = values.identification.replace(/\s/g, '')
      const response = await axios.post('/api/v1/auth/login', {
        identification: rawIdentification,
        password: values.password,
      })

      const { access_token, user } = response.data
      login(access_token, user)

      setToastTitle('Inicio de sesión exitoso')
      setToastDescription('Redirigiendo a tu zona protegida...')
      setToastOpen(true)
      window.setTimeout(() => navigate('/zones'), 300)
    } catch (error: unknown) {
      const message = getApiErrorMessage(
        error,
        'No fue posible iniciar sesión. Verifique sus credenciales.',
      )
      setToastTitle('No se pudo iniciar sesión')
      setToastDescription(String(message))
      setToastOpen(true)
    }
  }

  return (
    <Toast.Provider swipeDirection="right">
      <AuthLayout
        title="Iniciar sesión"
        subtitle="Ingrese sus credenciales para acceder a su cuenta"
      >
        <form className="mt-8 space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
          <TextField
            label="Número de identificación:"
            icon={UserRound}
            type="text"
            inputMode="numeric"
            autoComplete="username"
            placeholder="0 0000 0000"
            error={errors.identification?.message}
            {...register('identification', {
              onChange: (event) => {
                const formatted = formatIdentification(event.target.value)
                setValue('identification', formatted, { shouldValidate: true })
              },
            })}
          />

          <TextField
            label="Contraseña:"
            icon={Lock}
            type="password"
            autoComplete="current-password"
            placeholder="********"
            error={errors.password?.message}
            {...register('password')}
          />

          <SynapButton
            type="submit"
            disabled={isSubmitting}
            size="lg"
            className="w-full"
          >
            {isSubmitting ? 'Iniciando sesión...' : 'Iniciar sesión'}
          </SynapButton>

          <div className="pt-1 text-center">
            <button
              type="button"
              className="text-lg text-[#6B7280] transition hover:text-[#16A34A]"
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>

          <Link
            to="/register"
            className={buttonClasses({ variant: 'outline', size: 'lg', className: 'w-full border-[#16A34A] text-[#16A34A]' })}
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
