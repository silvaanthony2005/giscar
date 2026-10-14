import type { CSSProperties } from 'react'

interface Props {
  /** Nombre del glifo en Material Symbols Outlined (p. ej. `point_of_sale`). */
  name: string
  /** Rellena el icono (variante FILL 1 de Material Symbols). */
  filled?: boolean
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  style?: CSSProperties
}

const sizes: Record<NonNullable<Props['size']>, string> = {
  sm: 'text-[16px]',
  md: 'text-[20px]',
  lg: 'text-[24px]',
  xl: 'text-[32px]',
}

/**
 * Icono de Material Symbols. La fuente está auto-hospedada en `public/fonts`
 * porque el despliegue es local y puede no tener internet.
 */
export function Icon({ name, filled = false, size = 'md', className = '', style }: Props) {
  return (
    <span
      aria-hidden="true"
      className={`material-symbols-outlined select-none leading-none ${sizes[size]} ${className}`}
      style={{ fontVariationSettings: filled ? "'FILL' 1" : "'FILL' 0", ...style }}
    >
      {name}
    </span>
  )
}
