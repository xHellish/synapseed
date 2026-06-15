import type { ReactNode } from 'react'
import { Leaf } from 'lucide-react'

interface AuthLayoutProps {
  title: string
  subtitle: string
  children: ReactNode
}

export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <main className="min-h-screen bg-[#F7F8F2] px-4 py-10 text-[#111827] sm:px-6 lg:px-8">
      <section className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-6xl items-center justify-center">
        <article className="grid w-full overflow-hidden rounded-3xl border border-[#E5E7EB] bg-white shadow-[0_20px_40px_-24px_rgba(15,23,42,0.35)] lg:grid-cols-[1.05fr_0.95fr]">
          <aside className="hidden bg-gradient-to-br from-primary-50 via-white to-primary-100 p-10 lg:flex lg:flex-col lg:justify-between">
            <div>
              <div className="mb-6 inline-flex items-center gap-3 rounded-full bg-white/80 px-4 py-2 shadow-sm ring-1 ring-primary-100">
                <Leaf className="h-5 w-5 text-primary-700" />
                <span className="text-sm font-semibold uppercase tracking-[0.22em] text-primary-800">SynapSeed</span>
              </div>
              <h2 className="max-w-sm text-3xl font-semibold text-[#14532D]">Gestiona tu día agrícola con claridad y confianza.</h2>
              <p className="mt-4 max-w-sm text-sm text-[#475569]">Recomendaciones, seguimiento y decisiones más inteligentes para zonas y cultivos.</p>
            </div>
            <div className="rounded-2xl border border-primary-100 bg-white/80 p-5 text-sm text-[#334155] shadow-sm">
              <p className="font-semibold text-[#14532D]">Acceso seguro</p>
              <p className="mt-2 text-[#475569]">Tu sesión se mantiene protegida mediante token y redirección a la zona autorizada.</p>
            </div>
          </aside>

          <div className="flex items-center justify-center p-6 sm:p-8 lg:p-10">
            <div className="w-full max-w-md">
              <div className="mb-8 flex flex-col items-center text-center lg:items-start lg:text-left">
                <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-50 text-primary-700 shadow-sm ring-1 ring-primary-100">
                  <Leaf className="h-7 w-7" />
                </div>
                <h1 className="text-3xl font-semibold text-[#111827]">{title}</h1>
                <p className="mt-2 text-sm text-[#6B7280]">{subtitle}</p>
              </div>
              {children}
            </div>
          </div>
        </article>
      </section>
    </main>
  )
}
