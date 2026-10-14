import type { ReactNode } from 'react'
import { Icon } from './Icon'

type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

const tones: Record<Tone, string> = {
  neutral: 'bg-surface-container text-on-surface-variant',
  info: 'bg-info-container text-on-info-container',
  success: 'bg-success-container text-on-success-container',
  warning: 'bg-warning-container text-on-warning-container',
  danger: 'bg-error-container text-on-error-container',
}

interface Props {
  tone?: Tone
  /** Glifo de Material Symbols mostrado a la izquierda. */
  icon?: string
  className?: string
  children: ReactNode
}

/** Chip de estado al estilo M3 (contenedor de color + texto sobre él). */
export function Badge({ tone = 'neutral', icon, className = '', children }: Props) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-label-sm font-semibold whitespace-nowrap ${tones[tone]} ${className}`}
    >
      {icon && <Icon name={icon} size="sm" />}
      {children}
    </span>
  )
}
