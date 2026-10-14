import type { ReactNode } from 'react'
import { Icon } from '../atoms/Icon'

interface Props {
  /** Glifo de Material Symbols del cuadro izquierdo. */
  icon: string
  title: string
  description?: string
  /** Etiqueta corta a la derecha (p. ej. "Obligatorio", "Paso 2"). */
  chip?: string
  actions?: ReactNode
}

/** Encabezado de sección: cuadro con icono + título + descripción + chip. */
export function SectionHeader({ icon, title, description, chip, actions }: Props) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-space-md pb-space-sm">
      <div className="flex min-w-0 items-start gap-space-sm">
        <span className="flex size-8 shrink-0 items-center justify-center rounded bg-surface-container-high text-primary">
          <Icon name={icon} />
        </span>
        <div className="min-w-0">
          <h2 className="text-title-lg font-bold text-on-surface">{title}</h2>
          {description && (
            <p className="text-body-sm text-on-surface-variant">{description}</p>
          )}
        </div>
      </div>
      {chip && (
        <span className="rounded bg-surface-container-high px-space-sm py-0.5 text-label-sm font-semibold text-primary">
          {chip}
        </span>
      )}
      {actions}
    </div>
  )
}
