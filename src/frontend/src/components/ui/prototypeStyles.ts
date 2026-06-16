import { cn } from '@/lib/cn'

export type ButtonVariant = 'primary' | 'outline' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md' | 'lg'

export function buttonClasses({
  variant = 'primary',
  size = 'md',
  className,
}: {
  variant?: ButtonVariant
  size?: ButtonSize
  className?: string
} = {}) {
  return cn(
    'inline-flex items-center justify-center gap-2 rounded-md font-bold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#16A34A] disabled:cursor-not-allowed disabled:opacity-60',
    size === 'sm' && 'h-9 px-4 text-sm',
    size === 'md' && 'h-12 px-6 text-base',
    size === 'lg' && 'h-[54px] px-8 text-lg',
    variant === 'primary' && 'bg-[#16A34A] text-white shadow-sm hover:bg-[#15803D]',
    variant === 'outline' && 'border border-[#9CA3AF] bg-white text-[#111827] hover:bg-[#F7F8F2]',
    variant === 'ghost' && 'bg-transparent text-[#6B7280] hover:text-[#16A34A]',
    variant === 'danger' && 'bg-[#DC2626] text-white hover:bg-[#B91C1C]',
    className,
  )
}
