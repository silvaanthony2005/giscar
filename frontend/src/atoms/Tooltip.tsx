import { useId, useState, type ReactNode } from 'react'

interface Props {
  /** Texto mostrado al pasar el ratón o al enfocar con el teclado. */
  label: string
  children: ReactNode
  /** Posición horizontal respecto al elemento. */
  side?: 'top' | 'bottom'
  className?: string
}

const sides = {
  top: 'bottom-full mb-2 left-1/2 -translate-x-1/2',
  bottom: 'top-full mt-2 left-1/2 -translate-x-1/2',
} as const

/**
 * Tooltip accesible: aparece con ratón y con foco de teclado, y se asocia al
 * contenido mediante `aria-describedby`. Es puramente presentacional.
 */
export function Tooltip({ label, children, side = 'top', className = '' }: Props) {
  const id = useId()
  const [open, setOpen] = useState(false)

  return (
    <span
      className={`group relative inline-flex ${className}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      <span aria-describedby={id} className="inline-flex">
        {children}
      </span>
      <span
        id={id}
        role="tooltip"
        className={`pointer-events-none absolute z-50 whitespace-nowrap rounded-md bg-inverse-surface px-2 py-1 text-label-sm text-inverse-on-surface shadow-raised transition-opacity duration-150 ${sides[side]} ${
          open ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {label}
      </span>
    </span>
  )
}
