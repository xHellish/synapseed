import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import axios from 'axios'
import { Link, useNavigate } from 'react-router-dom'
import * as Toast from '@radix-ui/react-toast'
import { BadgeCheck, Lock, Mail, Phone, UserRound } from 'lucide-react'

import { AuthLayout } from './AuthLayout'

const registerSchema = z
  .object({
    identification: z
      .string()
      .trim()
      .min(1, 'El número de identificación es obligatorio.')
      .regex(/^\d\s\d{4}\s\d{4}$/, 'Ingrese una cédula válida con formato 0 0000 0000.'),
    fullName: z.string().trim().min(3, 'Ingrese su nombre completo.'),
    phone: z
      .string()
      .trim()
      .regex(/^\d{4}\s-\s\d{4}$/, 'Ingrese un teléfono válido en formato 8888 - 8888.'),
    email: z.string().trim().email('Ingrese un correo electrónico válido.'),
    password: z.string().min(6, 'La contraseña debe tener al menos 6 caracteres.'),
    confirmPassword: z.string().min(6, 'Confirme su contraseña.'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden.',
    path: ['confirmPassword'],
  })

type RegisterFormValues = z.infer<typeof registerSchema>

export function RegisterPage() {
  const navigate = useNavigate()
  const [toastOpen, setToastOpen] = useState(false)
  const [toastTitle, setToastTitle] = useState('')
  const [toastDescription, setToastDescription] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      identification: '',
      fullName: '',
      phone: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  })

  const formatIdentification = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 10)
    if (digits.length <= 1) return digits
    if (digits.length <= 5) return `${digits.slice(0, 1)} ${digits.slice(1)}`
    return `${digits.slice(0, 1)} ${digits.slice(1, 5)} ${digits.slice(5)}`.trimEnd()
  }

  const formatPhone = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 8)
    if (digits.length <= 4) return digits
    return `${digits.slice(0, 4)} - ${digits.slice(4)}`
  }

  const onSubmit = async (values: RegisterFormValues) => {
    try {
      await axios.post('/api/auth/register', {
        identification: values.identification.replace(/\s+/g, ''),
        full_name: values.fullName.trim(),
        phone: values.phone.trim(),
        email: values.email.trim(),
        password: values.password,
      })

      setToastTitle('Cuenta creada')
      setToastDescription('Tu registro se completó correctamente. Redirigiendo al inicio de sesión...')
      setToastOpen(true)
      window.setTimeout(() => navigate('/login'), 350)
    } catch (error: unknown) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail ?? 'No fue posible crear la cuenta. Verifique los datos ingresados.'
        : 'No fue posible crear la cuenta. Intente nuevamente.'

      setToastTitle('No se pudo crear la cuenta')
      setToastDescription(String(message))
      setToastOpen(true)
    }
  }

  return (
    <Toast.Provider swipeDirection="right">
      <AuthLayout
        title="Crear cuenta"
        subtitle="Cree una cuenta para recibir recomendaciones personalizadas"
      >
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <label htmlFor="identification" className="text-sm font-medium text-[#111827]">Número de identificación</label>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                  <BadgeCheck className="h-4 w-4" />
                </span>
                <input
                  id="identification"
                  type="text"
                  inputMode="numeric"
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
              {errors.identification && <p className="text-sm text-[#DC2626]">{errors.identification.message}</p>}
            </div>

            <div className="space-y-2 sm:col-span-2">
              <label htmlFor="fullName" className="text-sm font-medium text-[#111827]">Nombre completo</label>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                  <UserRound className="h-4 w-4" />
                </span>
                <input
                  id="fullName"
                  type="text"
                  placeholder="Juan Pérez González"
                  className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  {...register('fullName')}
                />
              </div>
              {errors.fullName && <p className="text-sm text-[#DC2626]">{errors.fullName.message}</p>}
            </div>

            <div className="space-y-2 sm:col-span-2">
              <label htmlFor="phone" className="text-sm font-medium text-[#111827]">Teléfono</label>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                  <Phone className="h-4 w-4" />
                </span>
                <input
                  id="phone"
                  type="text"
                  inputMode="numeric"
                  placeholder="8888 - 8888"
                  className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  {...register('phone', {
                    onChange: (event) => {
                      const formatted = formatPhone(event.target.value)
                      setValue('phone', formatted, { shouldValidate: true })
                    },
                  })}
                />
              </div>
              {errors.phone && <p className="text-sm text-[#DC2626]">{errors.phone.message}</p>}
            </div>

            <div className="space-y-2 sm:col-span-2">
              <label htmlFor="email" className="text-sm font-medium text-[#111827]">Correo electrónico</label>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                  <Mail className="h-4 w-4" />
                </span>
                <input
                  id="email"
                  type="email"
                  placeholder="juan@ejemplo.com"
                  className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  {...register('email')}
                />
              </div>
              {errors.email && <p className="text-sm text-[#DC2626]">{errors.email.message}</p>}
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-[#111827]">Contraseña</label>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#6B7280]">
                  <Lock className="h-4 w-4" />
                </span>
                <input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-[#E5E7EB] bg-white py-3 pl-10 pr-4 text-sm text-[#111827] shadow-sm transition focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  {...register('password')}
                />
              </div>
              {errors.password && <p className="text-sm text-[#DC2626]">{errors.password.message}</p>}
            </div>

            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="text-sm font-medium text-[#111827]">Confirmar contraseña</label>
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

          <div className="space-y-3 pt-1">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-xl bg-[#16A34A] px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#14532D] disabled:cursor-not-allowed disabled:bg-primary-300"
            >
              {isSubmitting ? 'Creando cuenta...' : 'Crear cuenta'}
            </button>

            <Link
              to="/login"
              className="block w-full rounded-xl border border-[#16A34A] bg-transparent px-4 py-3 text-center text-sm font-semibold text-[#16A34A] transition hover:bg-primary-50"
            >
              Ya tengo cuenta
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
