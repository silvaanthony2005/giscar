import type { ReactNode } from 'react'
import { Icon } from '../atoms/Icon'

interface Props {
  /** Ruta de migas de pan: ['Ventas', 'Proyectos', 'ACME'] */
  breadcrumb?: string[]
  title: string
  subtitle?: string
  /** Código de referencia junto al título (p. ej. el del proyecto). */
  code?: string
  actions?: ReactNode
}

export function PageHeader({ breadcrumb, title, subtitle, code, actions }: Props) {
  return (
    <div className="mb-space-lg">
      {breadcrumb && breadcrumb.length > 0 && (
        <nav aria-label="Migas de pan" className="mb-space-xs flex items-center gap-1">
          {breadcrumb.map((crumb, i) => (
            <span key={`${crumb}-${i}`} className="flex items-center gap-1">
              {i > 0 && <Icon name="chevron_right" size="sm" className="text-outline" />}
              <span
                className={`text-label-sm ${
                  i === breadcrumb.length - 1
                    ? 'font-semibold text-primary'
                    : 'text-on-surface-variant'
                }`}
              >
                {crumb}
              </span>
            </span>
          ))}
        </nav>
      )}
      <div className="flex flex-wrap items-start justify-between gap-space-md">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-space-md">
            <h1 className="text-headline-md text-primary tracking-tight">{title}</h1>
            {code && (
              <span className="rounded bg-secondary-container px-space-sm py-0.5 font-code-sm text-code-sm text-on-secondary shadow-hairline">
                {code}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="mt-1 max-w-3xl text-body-md text-on-surface-variant">{subtitle}</p>
          )}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-space-sm">{actions}</div>}
      </div>
    </div>
  )
}
