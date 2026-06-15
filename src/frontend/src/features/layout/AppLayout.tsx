import { useState, type ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Briefcase, Leaf, Menu, ShieldCheck, UserRound, X } from 'lucide-react'

interface AppLayoutProps {
  children: ReactNode
}

const navItems = [
  { label: 'Mi cuenta', href: '/account', icon: UserRound },
  { label: 'Gestión de zona', href: '/zones', icon: ShieldCheck },
  { label: 'Gestión de caso', href: '/cases', icon: Briefcase },
]

export function AppLayout({ children }: AppLayoutProps) {
  const [open, setOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="min-h-screen bg-[#F7F8F2] text-[#111827]">
      <div className="mx-auto flex min-h-screen max-w-7xl overflow-hidden rounded-none lg:rounded-3xl lg:border lg:border-[#E5E7EB] lg:bg-white lg:shadow-sm">
        <aside className="hidden w-72 shrink-0 bg-[#14532D] text-white lg:flex lg:flex-col">
          <div className="border-b border-white/10 p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/10">
                <Leaf className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.25em] text-white/70">SynapSeed</p>
                <h2 className="text-xl font-semibold">Panel</h2>
              </div>
            </div>
          </div>
          <nav className="flex flex-1 flex-col gap-2 p-4">
            {navItems.map(({ label, href, icon: Icon }) => {
              const active = location.pathname === href
              return (
                <Link
                  key={href}
                  to={href}
                  className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition ${
                    active
                      ? 'bg-[#16A34A] text-white shadow-sm'
                      : 'text-white/80 hover:bg-white/8 hover:text-white'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </Link>
              )
            })}
          </nav>
        </aside>

        <div className="flex min-h-screen flex-1 flex-col">
          <header className="border-b border-[#E5E7EB] bg-white/90 p-4 backdrop-blur lg:hidden">
            <div className="flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setOpen((prev) => !prev)}
                className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[#E5E7EB] bg-white text-[#111827] shadow-sm"
                aria-label="Abrir menú"
              >
                {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              <div className="flex items-center gap-2 text-[#14532D]">
                <Leaf className="h-5 w-5" />
                <span className="text-sm font-semibold uppercase tracking-[0.25em]">SynapSeed</span>
              </div>
            </div>
            {open && (
              <nav className="mt-4 flex flex-col gap-2 rounded-2xl border border-[#E5E7EB] bg-white p-2 shadow-sm">
                {navItems.map(({ label, href, icon: Icon }) => {
                  const active = location.pathname === href
                  return (
                    <Link
                      key={href}
                      to={href}
                      onClick={() => setOpen(false)}
                      className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium ${
                        active ? 'bg-[#16A34A] text-white' : 'text-[#111827] hover:bg-[#F7F8F2]'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{label}</span>
                    </Link>
                  )
                })}
              </nav>
            )}
          </header>

          <main className="flex-1 bg-[#F7F8F2] p-4 sm:p-6 lg:p-8">{children}</main>
        </div>
      </div>
    </div>
  )
}
