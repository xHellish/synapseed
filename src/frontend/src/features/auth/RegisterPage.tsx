import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import * as Toast from '@radix-ui/react-toast'
import { BadgeCheck, Lock, Mail, Phone, UserRound } from 'lucide-react'

import { SynapButton, TextField } from '@/components/ui/prototype'
import { buttonClasses } from '@/components/ui/prototypeStyles'
import { authApi } from '@/lib/api'
import { getApiErrorMessage } from '@/lib/apiError'
import { AuthLayout } from './AuthLayout'

const registerSchema = z
  .object({
    identification: z
      .string()
      .trim()
      .min(1, 'El número de identificación es obligatorio.')
      .regex(/^\d\s\d{4}\s\d{4,5}$/, 'Ingrese una cédula válida con formato 0 0000 0000.'),
    fullName: z.string().trim().min(3, 'Ingrese su nombre completo.'),
    phone: z
      .string()
      .trim()
      .regex(/^\d{4}\s-\s\d{4}$/, 'Ingrese un teléfono válido en formato 8888 - 8888.'),
    email: z.string().trim().email('Ingrese un correo electrónico válido.'),
    password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres.'),
    confirmPassword: z.string().min(8, 'Confirme su contraseña.'),
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
      await authApi.register({
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
      const message = getApiErrorMessage(
        error,
        'No fue posible crear la cuenta. Verifique los datos ingresados.',
      )

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
          <TextField
            label="Número de identificación:"
            icon={BadgeCheck}
            type="text"
            inputMode="numeric"
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
            label="Nombre completo:"
            icon={UserRound}
            type="text"
            placeholder="Juan Pérez Gonzáles"
            error={errors.fullName?.message}
            {...register('fullName')}
          />

          <TextField
            label="Teléfono:"
            icon={Phone}
            type="text"
            inputMode="numeric"
            placeholder="8888 - 8888"
            error={errors.phone?.message}
            {...register('phone', {
              onChange: (event) => {
                const formatted = formatPhone(event.target.value)
                setValue('phone', formatted, { shouldValidate: true })
              },
            })}
          />

          <TextField
            label="Correo electrónico:"
            icon={Mail}
            type="email"
            placeholder="juan@ejemplo.com"
            error={errors.email?.message}
            {...register('email')}
          />

          <TextField
            label="Contraseña:"
            icon={Lock}
            type="password"
            placeholder="********"
            error={errors.password?.message}
            {...register('password')}
          />

          <TextField
            label="Confirmar contraseña:"
            icon={Lock}
            type="password"
            placeholder="********"
            error={errors.confirmPassword?.message}
            {...register('confirmPassword')}
          />

          <div className="space-y-4 pt-4">
            <SynapButton type="submit" disabled={isSubmitting} size="lg" className="w-full">
              {isSubmitting ? 'Creando cuenta...' : 'Crear cuenta'}
            </SynapButton>

            <Link
              to="/login"
              className={buttonClasses({ variant: 'outline', size: 'lg', className: 'w-full border-[#16A34A] text-[#16A34A]' })}
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
