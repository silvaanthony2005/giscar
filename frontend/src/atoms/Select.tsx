import { useId, type SelectHTMLAttributes } from 'react'
import { Icon } from './Icon'

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  hint?: string
  error?: string
  /** Etiqueta inicial deshabilitada. */
  placeholder?: string
  options: { value: string; label: string }[]
}

/** Selector nativo con el mismo tratamiento visual que `Input`. */
export function Select({
  label,
  hint,
  error,
  placeholder,
  options,
  id,
  className = '',
  ...rest
}: Props) {
  const autoId = useId()
  const selectId = id ?? autoId
  const describedBy = error ? `${selectId}-error` : hint ? `${selectId}-hint` : undefined

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={selectId} className="text-title-md text-on-surface">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        <select
          id={selectId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={`h-10 w-full appearance-none rounded-lg bg-surface-container-low pr-10 pl-3.5 text-body-md text-on-surface shadow-hairline transition-all duration-150 focus:bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-secondary ${
            error ? 'ring-2 ring-error/40 focus:ring-error/60' : ''
          } ${className}`}
          {...rest}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <Icon
          name="expand_more"
          size="sm"
          className="pointer-events-none absolute right-3 text-outline"
        />
      </div>
      {error ? (
        <p id={`${selectId}-error`} className="text-label-sm text-on-error-container">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${selectId}-hint`} className="text-label-sm text-on-surface-variant">
            {hint}
          </p>
        )
      )}
    </div>
  )
}
