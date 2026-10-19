import { useId, type InputHTMLAttributes, type ReactNode } from 'react'
import { Icon } from './Icon'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  /** Glifo de Material Symbols a la izquierda del campo. */
  icon?: string
  /** Texto de ayuda bajo el campo (uso, no negocio). */
  hint?: string
  error?: string
  /** Elemento a la derecha del campo (p. ej. botón de mostrar contraseña). */
  trailing?: ReactNode
}

export function Input({
  label,
  icon,
  hint,
  error,
  trailing,
  id,
  className = '',
  ...rest
}: Props) {
  const autoId = useId()
  const inputId = id ?? autoId
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-title-md text-on-surface">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {icon && (
          <Icon
            name={icon}
            size="sm"
            className="pointer-events-none absolute left-3.5 text-outline"
          />
        )}
        <input
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={`h-10 w-full rounded-lg bg-surface-container-low text-body-md text-on-surface shadow-hairline transition-all duration-150 placeholder:text-outline focus:bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-secondary ${
            icon ? 'pl-11' : 'pl-3.5'
          } ${trailing ? 'pr-11' : 'pr-3.5'} ${
            error ? 'ring-2 ring-error/40 focus:ring-error/60' : ''
          } ${className}`}
          {...rest}
        />
        {trailing && (
          <div className="absolute right-1.5 flex items-center text-outline">{trailing}</div>
        )}
      </div>
      {error ? (
        <p id={`${inputId}-error`} role="alert" className="text-label-sm text-on-error-container">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${inputId}-hint`} className="text-label-sm text-on-surface-variant">
            {hint}
          </p>
        )
      )}
    </div>
  )
}
