import type { HTMLAttributes, ReactNode } from 'react'

interface Props extends HTMLAttributes<HTMLDivElement> {
  /** Encabezado opcional con título y acciones a la derecha. */
  header?: ReactNode
  /** Pie opcional (texto de estado, acciones secundarias...). */
  footer?: ReactNode
}

export function Card({ header, footer, className = '', children, ...rest }: Props) {
  return (
    <section
      className={`rounded-xl border border-outline-variant/60 bg-surface-container-lowest shadow-raised ${className}`}
      {...rest}
    >
      {header && (
        <div className="flex items-center justify-between gap-3 border-b border-outline-variant/60 px-space-lg py-space-md">
          {header}
        </div>
      )}
      {children}
      {footer && (
        <div className="border-t border-outline-variant/60 px-space-lg py-space-md">{footer}</div>
      )}
    </section>
  )
}
