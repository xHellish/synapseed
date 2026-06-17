import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import axios from 'axios'
import { useNavigate, Link } from 'react-router-dom'
import * as Dialog from '@radix-ui/react-dialog'
import * as Toast from '@radix-ui/react-toast'
import { Lock, Mail, UserRound, X } from 'lucide-react'

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

const passwordResetSchema = z
  .object({
    identification: z
      .string()
      .trim()
      .min(1, 'El número de identificación es obligatorio.')
      .regex(/^\d{1}\s\d{4}\s\d{4}$/, 'Ingrese una cédula válida con formato 0 0000 0000.'),
    email: z.string().trim().email('Ingrese un correo electrónico válido.'),
    newPassword: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres.'),
    confirmPassword: z.string().min(8, 'Confirme su nueva contraseña.'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Las contraseñas no coinciden.',
    path: ['confirmPassword'],
  })

type LoginFormValues = z.infer<typeof loginSchema>
type PasswordResetFormValues = z.infer<typeof passwordResetSchema>

export function LoginPage() {
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)
  const [passwordResetOpen, setPasswordResetOpen] = useState(false)
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

  const {
    register: registerPasswordReset,
    handleSubmit: handlePasswordResetSubmit,
    formState: { errors: passwordResetErrors, isSubmitting: isResettingPassword },
    setValue: setPasswordResetValue,
    reset: resetPasswordResetForm,
  } = useForm<PasswordResetFormValues>({
    resolver: zodResolver(passwordResetSchema),
    defaultValues: {
      identification: '',
      email: '',
      newPassword: '',
      confirmPassword: '',
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

  const onPasswordResetSubmit = async (values: PasswordResetFormValues) => {
    try {
      await axios.post('/api/v1/auth/reset-password', {
        identification: values.identification.replace(/\s/g, ''),
        email: values.email.trim(),
        new_password: values.newPassword,
      })

      resetPasswordResetForm()
      setPasswordResetOpen(false)
      setToastTitle('Contraseña actualizada')
      setToastDescription('Ya puede iniciar sesión.')
      setToastOpen(true)
    } catch (error: unknown) {
      const message = getApiErrorMessage(
        error,
        'No fue posible restablecer la contraseña con los datos ingresados.',
      )
      setToastTitle('No se pudo actualizar la contraseña')
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
            <Dialog.Root
              open={passwordResetOpen}
              onOpenChange={(nextOpen) => {
                setPasswordResetOpen(nextOpen)
                if (!nextOpen) resetPasswordResetForm()
              }}
            >
              <Dialog.Trigger asChild>
                <button
                  type="button"
                  className="text-lg text-[#6B7280] transition hover:text-[#16A34A]"
                >
                  ¿Olvidaste tu contraseña?
                </button>
              </Dialog.Trigger>

              <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 z-50 bg-[#111827]/45 backdrop-blur-sm" />
                <Dialog.Content className="fixed left-1/2 top-1/2 z-[60] w-[calc(100vw-2rem)] max-w-[560px] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[#E5E7EB] bg-white p-6 text-left shadow-2xl sm:p-8">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <Dialog.Title className="text-[28px] font-bold leading-tight text-[#111827]">
                        Recuperar contraseña
                      </Dialog.Title>
                      <Dialog.Description className="mt-3 text-base leading-6 text-[#6B7280]">
                        Ingrese su identificación, correo y una nueva contraseña.
                      </Dialog.Description>
                    </div>

                    <Dialog.Close asChild>
                      <button
                        type="button"
                        className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-[#E5E7EB] bg-white text-[#111827] transition hover:bg-[#F7F8F2]"
                        aria-label="Cerrar"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </Dialog.Close>
                  </div>

                  <form className="mt-6 space-y-4" onSubmit={handlePasswordResetSubmit(onPasswordResetSubmit)} noValidate>
                    <TextField
                      id="reset-identification"
                      label="Número de identificación:"
                      icon={UserRound}
                      type="text"
                      inputMode="numeric"
                      autoComplete="username"
                      placeholder="0 0000 0000"
                      error={passwordResetErrors.identification?.message}
                      {...registerPasswordReset('identification', {
                        onChange: (event) => {
                          const formatted = formatIdentification(event.target.value)
                          setPasswordResetValue('identification', formatted, { shouldValidate: true })
                        },
                      })}
                    />

                    <TextField
                      id="reset-email"
                      label="Correo electrónico:"
                      icon={Mail}
                      type="email"
                      autoComplete="email"
                      placeholder="usuario@correo.com"
                      error={passwordResetErrors.email?.message}
                      {...registerPasswordReset('email')}
                    />

                    <TextField
                      id="reset-new-password"
                      label="Nueva contraseña:"
                      icon={Lock}
                      type="password"
                      autoComplete="new-password"
                      placeholder="********"
                      error={passwordResetErrors.newPassword?.message}
                      {...registerPasswordReset('newPassword')}
                    />

                    <TextField
                      id="reset-confirm-password"
                      label="Confirmar contraseña:"
                      icon={Lock}
                      type="password"
                      autoComplete="new-password"
                      placeholder="********"
                      error={passwordResetErrors.confirmPassword?.message}
                      {...registerPasswordReset('confirmPassword')}
                    />

                    <div className="grid gap-3 pt-3 sm:grid-cols-2">
                      <Dialog.Close asChild>
                        <button
                          type="button"
                          className={buttonClasses({ variant: 'outline', size: 'lg', className: 'w-full' })}
                        >
                          Cancelar
                        </button>
                      </Dialog.Close>

                      <SynapButton type="submit" disabled={isResettingPassword} size="lg" className="w-full">
                        {isResettingPassword ? 'Actualizando...' : 'Actualizar contraseña'}
                      </SynapButton>
                    </div>
                  </form>
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>
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
