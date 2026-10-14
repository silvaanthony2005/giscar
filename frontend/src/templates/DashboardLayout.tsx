import { useEffect, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../entities/auth/store'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

export function DashboardLayout() {
  const user = useAuthStore((s) => s.user)
  const clear = useAuthStore((s) => s.clear)
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  // Al cambiar de ruta, vuelve arriba (el scroll es del documento).
  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [location.pathname])

  const logout = () => {
    clear()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-background">
      <TopBar user={user} onMenuClick={() => setMenuOpen((v) => !v)} onLogout={logout} />

      {/* Sidebar fijo (desktop) */}
      <aside className="fixed bottom-0 left-0 top-16 z-40 hidden w-64 lg:block">
        <Sidebar user={user} />
      </aside>

      {/* Drawer (móvil) */}
      {menuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-inverse-surface/40"
            onClick={() => setMenuOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute inset-y-0 left-0 w-64">
            <Sidebar user={user} onNavigate={() => setMenuOpen(false)} />
          </div>
        </div>
      )}

      <main className="relative min-h-screen pt-16 lg:pl-64">
        <div className="mx-auto max-w-7xl">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
