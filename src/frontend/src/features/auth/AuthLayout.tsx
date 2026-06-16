import type { ReactNode } from 'react'

interface AuthLayoutProps {
  title: string
  subtitle: string
  children: ReactNode
}

export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F7F8F2] px-5 py-10 text-[#111827]">
      <section className="w-full max-w-[580px] rounded-xl border border-[#E5E7EB] bg-white px-8 py-9 shadow-[0_2px_2px_rgba(17,24,39,0.18)] sm:px-10">
        <div className="mb-8 flex flex-col items-center text-center">
          <img
            src="/brand/synapseed-color-cropped.png"
            alt="SynapSeed"
            className="mb-8 h-auto w-[300px] object-contain"
          />

          <h1 className="text-[32px] font-bold leading-tight tracking-normal text-[#111827]">{title}</h1>
          <p className="mt-4 text-xl leading-7 text-[#6B7280]">{subtitle}</p>
        </div>

        {children}
      </section>
    </main>
  )
}
