import type { ReactNode } from 'react'
import { Leaf } from 'lucide-react'

interface AuthLayoutProps {
  title: string
  subtitle: string
  children: ReactNode
}

export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F7F8F2] px-4">
      <section className="w-full max-w-md rounded-lg border border-[#E5E7EB] bg-white px-8 py-10 shadow-sm">
        {/* Logo */}
        <div className="mb-2 flex flex-col items-center text-center">
          <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl">
            <Leaf className="h-8 w-8 text-[#14532D]" />
          </div>
          <span className="mb-6 text-sm font-semibold uppercase tracking-[0.22em] text-[#14532D]">
            SynapSeed
          </span>

          <h1 className="text-2xl font-bold text-[#111827]">{title}</h1>
          <p className="mt-1 text-sm text-[#6B7280]">{subtitle}</p>
        </div>

        {children}
      </section>
    </main>
  )
}