import { useNavigate } from 'react-router-dom'
import type { User } from '../entities/auth/types'
import { Icon } from '../atoms/Icon'
import { Tooltip } from '../atoms/Tooltip'
import { Buscador } from '../molecules/Buscador'
import { DEPARTAMENTOS } from '../shared/lib/format'

interface Props {
  user: User | null
  /** Abre/cierra el sidebar en móvil. */
  onMenuClick: () => void
  onLogout: () => void
}

export function TopBar({ user, onMenuClick, onLogout }: Props) {
  const navigate = useNavigate()

  return (
    <header className="fixed inset-x-0 top-0 z-50 h-16 bg-surface-container-lowest/90 shadow-hairline backdrop-blur-xl">
      <div className="flex h-16 items-center justify-between gap-space-lg px-space-lg">
        <div className="flex min-w-[240px] items-center gap-space-md">
          <button
            type="button"
            onClick={onMenuClick}
            aria-label="Abrir menú de navegación"
            className="flex size-9 items-center justify-center rounded-lg text-on-surface-variant transition-colors hover:bg-surface-container hover:text-on-surface lg:hidden"
          >
            <Icon name="menu" />
          </button>
          <button
            type="button"
            onClick={() => navigate('/panel')}
            className="flex items-center gap-space-md"
          >
            <span className="flex size-8 items-center justify-center rounded-md bg-primary text-on-primary">
              <Icon name="hub" size="sm" />
            </span>
            <span className="flex flex-col text-left leading-none">
              <span className="text-title-md font-bold tracking-tight text-primary">GCISCAR</span>
              <span className="text-label-sm font-medium text-on-surface-variant">
                Sistema de Información
              </span>
            </span>
          </button>
        </div>

        {user && <Buscador departamento={user.departamento} />}

        <div className="flex shrink-0 items-center gap-space-md">
          {user && (
            <span className="hidden items-center gap-space-xs rounded-lg bg-surface-container-high px-space-sm py-space-xs sm:flex">
              <Icon name="corporate_fare" size="sm" className="text-secondary" />
              <span className="text-label-md font-semibold text-on-surface">
                {DEPARTAMENTOS[user.departamento]}
              </span>
            </span>
          )}

          <Tooltip label="Cerrar sesión" side="bottom">
            <button
              type="button"
              onClick={onLogout}
              aria-label="Cerrar sesión"
              className="flex size-9 items-center justify-center rounded-lg text-on-surface-variant transition-colors hover:bg-surface-container hover:text-on-surface"
            >
              <Icon name="logout" />
            </button>
          </Tooltip>
        </div>
      </div>
    </header>
  )
}
