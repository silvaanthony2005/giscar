import type { ButtonHTMLAttributes } from 'react'
import { Icon } from './Icon'

type Tone = 'default' | 'danger'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Glifo de Material Symbols. */
  icon: string
  /** Etiqueta accesible: obligatoria porque el botón no tiene texto. */
  label: string
  tone?: Tone
}

const tones: Record<Tone, string> = {
  default: 'text-on-surface-variant hover:bg-surface-container focus-visible:ring-secondary',
  danger: 'text-on-error-container hover:bg-error-container/60 focus-visible:ring-error',
}

/**
 * Botón de solo icono. Fijo en 44px para conservar la zona táctil mínima
 * (WCAG 2.5.8); `Button` no sirve aquí porque fija su propio padding.
 */
export function IconButton({ icon, label, tone = 'default', className = '', ...rest }: Props) {
  return (
    <button
      aria-label={label}
      className={`flex size-11 shrink-0 items-center justify-center rounded-lg transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-surface ${tones[tone]} ${className}`}
      {...rest}
    >
      <Icon name={icon} size="sm" />
    </button>
  )
}
