import * as Select from '@radix-ui/react-select'
import { Check, ChevronDown, type LucideIcon } from 'lucide-react'
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from 'react'

import { cn } from '@/lib/cn'
import { buttonClasses, type ButtonSize, type ButtonVariant } from './prototypeStyles'

interface SynapButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
}

export function SynapButton({
  variant = 'primary',
  size = 'md',
  className,
  type = 'button',
  ...props
}: SynapButtonProps) {
  return <button type={type} className={buttonClasses({ variant, size, className })} {...props} />
}

interface PageHeaderProps {
  title: string
  subtitle?: string
  action?: ReactNode
  className?: string
}

export function PageHeader({ title, subtitle, action, className }: PageHeaderProps) {
  return (
    <header className={cn('mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between', className)}>
      <div>
        <h1 className="text-[32px] font-bold leading-tight tracking-normal text-[#111827]">{title}</h1>
        {subtitle && <p className="mt-4 text-lg leading-7 text-[#6B7280]">{subtitle}</p>}
      </div>
      {action}
    </header>
  )
}

interface PanelProps {
  children: ReactNode
  className?: string
}

export function Panel({ children, className }: PanelProps) {
  return (
    <section className={cn('rounded-xl border border-[#E5E7EB] bg-white shadow-[0_2px_2px_rgba(17,24,39,0.18)]', className)}>
      {children}
    </section>
  )
}

interface SectionTitleProps {
  icon?: LucideIcon
  children: ReactNode
  className?: string
}

export function SectionTitle({ icon: Icon, children, className }: SectionTitleProps) {
  return (
    <div className={cn('mb-5 flex items-center gap-3 border-b border-[#9CA3AF] pb-2', className)}>
      {Icon && <Icon className="h-6 w-6 text-[#16A34A]" />}
      <h2 className="text-2xl font-semibold leading-tight text-[#111827]">{children}</h2>
    </div>
  )
}

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  icon?: LucideIcon
  error?: string
}

export function TextField({ label, icon: Icon, error, className, id, ...props }: TextFieldProps) {
  const inputId = id ?? props.name

  return (
    <div className="space-y-2">
      <label htmlFor={inputId} className="flex items-center gap-3 text-lg font-normal leading-none text-[#111827]">
        {Icon && <Icon className="h-5 w-5 text-[#16A34A]" />}
        {label}
      </label>
      <input
        id={inputId}
        className={cn(
          'h-[54px] w-full rounded-md border border-[#9CA3AF] bg-white px-4 text-xl text-[#111827] shadow-sm transition placeholder:text-[#6B7280] focus:border-[#16A34A] focus:outline-none focus:ring-2 focus:ring-[#16A34A]/20 disabled:bg-[#F7F8F2]',
          Icon && 'pl-4',
          className,
        )}
        {...props}
      />
      {error && <p className="text-sm font-medium text-[#DC2626]">{error}</p>}
    </div>
  )
}

export interface SelectOption {
  value: string
  label: string
}

function toOptions(values: string[] | SelectOption[]): SelectOption[] {
  return values.map((option) => (typeof option === 'string' ? { value: option, label: option } : option))
}

interface SelectFieldProps {
  label: string
  value?: string
  onValueChange: (value: string) => void
  options: string[] | SelectOption[]
  placeholder?: string
  error?: string
  id?: string
  className?: string
}

export function SelectField({
  label,
  value,
  onValueChange,
  options,
  placeholder = 'Seleccione una opción',
  error,
  id,
  className,
}: SelectFieldProps) {
  const normalized = toOptions(options)

  return (
    <div className={cn('space-y-2', className)}>
      <label htmlFor={id} className="block text-lg font-normal leading-none text-[#111827]">
        {label}
      </label>
      <Select.Root value={value ?? ''} onValueChange={onValueChange}>
        <Select.Trigger
          id={id}
          className="flex h-[54px] w-full items-center justify-between rounded-md border border-[#9CA3AF] bg-white px-4 text-left text-xl text-[#111827] shadow-sm transition data-[placeholder]:text-[#6B7280] focus:border-[#16A34A] focus:outline-none focus:ring-2 focus:ring-[#16A34A]/20"
        >
          <Select.Value placeholder={placeholder} />
          <Select.Icon>
            <ChevronDown className="h-6 w-6 text-[#6B7280]" />
          </Select.Icon>
        </Select.Trigger>
        <Select.Portal>
          <Select.Content
            position="popper"
            sideOffset={6}
            className="z-50 max-h-80 min-w-[var(--radix-select-trigger-width)] overflow-hidden rounded-xl bg-[#333333] py-2 text-white shadow-2xl"
          >
            <Select.Viewport>
              {normalized.map((option) => (
                <Select.Item
                  key={option.value}
                  value={option.value}
                  className="relative flex cursor-pointer select-none items-center px-10 py-3 text-lg outline-none data-[highlighted]:bg-white/10"
                >
                  <Select.ItemIndicator className="absolute left-3">
                    <Check className="h-4 w-4" />
                  </Select.ItemIndicator>
                  <Select.ItemText>{option.label}</Select.ItemText>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
      {error && <p className="text-sm font-medium text-[#DC2626]">{error}</p>}
    </div>
  )
}

interface CaseStepperProps {
  step: number
}

export function CaseStepper({ step }: CaseStepperProps) {
  const steps = ['Datos del caso', 'Confirmación', 'Recomendaciones', 'Proveedores']

  return (
    <div className="mb-10 flex flex-wrap items-center gap-3 text-lg">
      {steps.map((label, index) => {
        const number = index + 1
        const active = number === step
        const done = number < step

        return (
          <div key={label} className="flex items-center gap-3">
            <span
              className={cn(
                'flex h-9 w-9 items-center justify-center rounded-full text-lg font-bold',
                done || active ? 'bg-[#16A34A] text-white' : 'bg-[#E9EDF3] text-[#111827]',
              )}
            >
              {number}
            </span>
            <span className={cn('font-normal', active || done ? 'font-bold text-[#111827]' : 'text-[#6B7280]')}>{label}</span>
            {index < steps.length - 1 && <span className="h-px w-[96px] bg-[#9CA3AF]" />}
          </div>
        )
      })}
    </div>
  )
}

interface IconStatProps {
  label: string
  value: string | number
  icon: LucideIcon
}

export function IconStat({ label, value, icon: Icon }: IconStatProps) {
  return (
    <Panel className="flex min-h-[132px] items-center gap-5 p-7">
      <span className="flex h-12 w-12 items-center justify-center rounded-md bg-[#E8F7EE] text-[#16A34A]">
        <Icon className="h-7 w-7" />
      </span>
      <div>
        <p className="text-xl font-semibold text-[#6B7280]">{label}</p>
        <p className="mt-2 text-3xl font-bold text-[#111827]">{value}</p>
      </div>
    </Panel>
  )
}
