import { NavLink } from 'react-router-dom'
import { useContadores } from '../entities/panel/api'
import type { Departamento, User } from '../entities/auth/types'
import { Icon } from '../atoms/Icon'
import { NAV, type NavItem } from '../shared/lib/nav'
import { DEPARTAMENTOS } from '../shared/lib/format'

interface Props {
  user: User | null
  /** Cierra el panel en móvil. */
  onNavigate?: () => void
}

export function Sidebar({ user, onNavigate }: Props) {
  // Los números vienen ya calculados del backend; aquí solo se pintan.
  const { data: contadores } = useContadores()

  if (!user) return null

  // Cada grupo lleva su etiqueta: así los nombres repetidos ("Proyectos")
  // no se confunden entre departamentos.
  const grupos: { titulo: string; departamento: Departamento; items: NavItem[] }[] = [
    { titulo: 'Mi módulo', departamento: user.departamento, items: NAV[user.departamento] },
  ]
  if (user.departamento === 'rrhh') {
    grupos.push(
      ...(Object.keys(NAV) as Departamento[])
        .filter((d) => d !== 'rrhh')
        .map((d) => ({
          titulo: DEPARTAMENTOS[d],
          departamento: d,
          // «Reportar incidencia» es compartido y ya está en «Mi módulo»:
          // sin este filtro RRHH lo vería repetido en cada grupo.
          items: NAV[d].filter((i) => i.to !== '/incidencias/nueva'),
        })),
    )
  }

  return (
    <div className="flex h-full flex-col justify-between overflow-y-auto bg-surface-container-lowest py-space-md shadow-hairline">
      <div className="space-y-space-md">
        {grupos.map((grupo) => (
          <div key={grupo.titulo}>
            <div className="mb-space-xs flex items-center justify-between px-space-lg">
              <span className="text-label-sm font-bold uppercase tracking-wider text-on-surface-variant">
                {grupo.titulo}
              </span>
              {/* RRHH no es una cola de trabajo: no lleva contador. */}
              {grupo.departamento !== 'rrhh' &&
                contadores?.[grupo.departamento] !== undefined && (
                  <span className="rounded bg-surface-container px-space-xs text-label-sm font-semibold text-on-surface-variant">
                    {contadores[grupo.departamento]}
                  </span>
                )}
            </div>
            <nav className="space-y-0.5 px-space-sm">
              {grupo.items.map((item) => (
                <NavLink
                  key={`${grupo.titulo}-${item.to}`}
                  to={item.to}
                  end={item.end ?? false}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    `flex items-center justify-between rounded-lg px-space-md py-space-sm transition-colors group ${
                      isActive
                        ? 'bg-primary-container text-on-primary font-semibold'
                        : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                    }`
                  }
                >
                  <span className="flex min-w-0 items-center gap-space-md">
                    <Icon
                      name={item.icon}
                      className="shrink-0 text-outline transition-colors group-hover:text-primary"
                    />
                    <span className="truncate text-body-md">{item.label}</span>
                  </span>
                </NavLink>
              ))}
            </nav>
          </div>
        ))}
      </div>

      <div className="mx-space-sm rounded-lg bg-surface-container-low px-space-md py-space-sm">
        <div className="flex items-center gap-space-sm">
          <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-secondary-container text-label-sm font-bold text-on-secondary">
            {user.nombre.slice(0, 1).toUpperCase()}
          </span>
          <div className="min-w-0">
            <div className="truncate text-title-md text-on-surface">{user.nombre}</div>
            <div className="truncate text-label-sm text-on-surface-variant">
              {DEPARTAMENTOS[user.departamento]}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
