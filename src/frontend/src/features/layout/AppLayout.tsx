import { useState, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ClipboardCheck, LogOut, MapPin, Menu, UserRound, X } from 'lucide-react'

import { useAuthStore } from '@/stores/authStore'

interface AppLayoutProps {
  children: ReactNode
}

const navItems = [
  { label: 'Mi cuenta', href: '/account', icon: UserRound },
  { label: 'Gestión de zona', href: '/zones', icon: MapPin },
  { label: 'Gestión de caso', href: '/cases', icon: ClipboardCheck },
]

export function AppLayout({ children }: AppLayoutProps) {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const logout = useAuthStore((state) => state.logout)
  const isActive = (href: string) => location.pathname === href || location.pathname.startsWith(`${href}/`)

  const handleLogout = () => {
    logout()
    setOpen(false)
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-[#F7F8F2] text-[#111827]">
      <div className="flex min-h-screen">
        <aside className="hidden w-[280px] shrink-0 bg-[#14532D] text-white lg:flex lg:flex-col xl:w-[302px]">
          <div className="px-9 pb-14 pt-9">
            <img src="/brand/synapseed-white.png" alt="SynapSeed" className="h-auto w-[230px] object-contain" />
          </div>

          <nav className="flex flex-1 flex-col gap-5 px-4">
            {navItems.map(({ label, href, icon: Icon }) => {
              const active = isActive(href)
              return (
                <Link
                  key={href}
                  to={href}
                  className={`flex h-[58px] items-center gap-4 rounded-md px-8 text-2xl font-bold transition ${
                    active ? 'bg-[#16A34A] text-white shadow-sm' : 'text-white hover:bg-white/10'
                  }`}
                >
                  <Icon className="h-8 w-8" />
                  <span>{label}</span>
                </Link>
              )
            })}
          </nav>

          <div className="px-4 pb-8">
            <button
              type="button"
              onClick={handleLogout}
              className="flex h-[58px] w-full items-center gap-4 rounded-md px-8 text-2xl font-bold text-white transition hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              <LogOut className="h-8 w-8" />
              <span>Cerrar sesión</span>
            </button>
          </div>
        </aside>

        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <header className="border-b border-[#E5E7EB] bg-white/90 p-4 backdrop-blur lg:hidden">
            <div className="flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setOpen((prev) => !prev)}
                className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-[#E5E7EB] bg-white text-[#111827] shadow-sm"
                aria-label="Abrir menú"
              >
                {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              <img src="/brand/synapseed-color.png" alt="SynapSeed" className="h-12 w-auto object-contain" />
            </div>

            {open && (
              <nav className="mt-4 flex flex-col gap-2 rounded-xl border border-[#E5E7EB] bg-white p-2 shadow-sm">
                {navItems.map(({ label, href, icon: Icon }) => {
                  const active = isActive(href)
                  return (
                    <Link
                      key={href}
                      to={href}
                      onClick={() => setOpen(false)}
                      className={`flex items-center gap-3 rounded-md px-3 py-3 text-sm font-bold ${
                        active ? 'bg-[#16A34A] text-white' : 'text-[#111827] hover:bg-[#F7F8F2]'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{label}</span>
                    </Link>
                  )
                })}

                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex items-center gap-3 rounded-md px-3 py-3 text-sm font-bold text-[#111827] hover:bg-[#F7F8F2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#14532D]"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Cerrar sesión</span>
                </button>
              </nav>
            )}
          </header>

          <main className="flex-1 bg-[#F7F8F2] px-5 py-8 sm:px-8 lg:px-[80px] lg:py-8">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}
