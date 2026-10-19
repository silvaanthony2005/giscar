import type { ButtonHTMLAttributes } from 'react'
import { Icon } from './Icon'

type Variant = 'primary' | 'secondary' | 'tonal' | 'danger' | 'ghost'
type Size = 'sm' | 'md' | 'lg'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  /** Icono de Material Symbols a la izquierda del texto. */
  icon?: string
}

const variants: Record<Variant, string> = {
  // Filled
  primary:
    'bg-primary text-on-primary hover:bg-secondary focus-visible:ring-secondary shadow-hairline',
  // Outlined
  secondary:
    'border border-outline text-primary bg-surface-container-lowest hover:bg-surface-container focus-visible:ring-secondary',
  // Tonal
  tonal:
    'bg-secondary-container text-on-secondary hover:bg-secondary focus-visible:ring-secondary',
  danger: 'bg-error text-on-error hover:bg-on-error-container focus-visible:ring-error',
  ghost: 'text-secondary hover:bg-surface-container focus-visible:ring-secondary',
}

const sizes: Record<Size, string> = {
  sm: 'h-8 px-3 text-label-md',
  md: 'h-10 px-4 text-body-md',
  lg: 'h-11 px-5 text-title-md',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  className = '',
  disabled,
  children,
  ...rest
}: Props) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-surface disabled:cursor-not-allowed disabled:opacity-40 ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? (
        <span
          aria-hidden="true"
          className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      ) : (
        icon !== undefined && <Icon name={icon} size="sm" />
      )}
      {children}
    </button>
  )
}

export type { Variant as ButtonVariant }
