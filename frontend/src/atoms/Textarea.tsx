import { useId, type TextareaHTMLAttributes } from 'react'

interface Props extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  /** Texto de ayuda bajo el campo (uso, no negocio). */
  hint?: string
  error?: string
}

/** Área de texto con el mismo tratamiento visual que `Input`. */
export function Textarea({ label, hint, error, id, className = '', ...rest }: Props) {
  const autoId = useId()
  const areaId = id ?? autoId
  const describedBy = error ? `${areaId}-error` : hint ? `${areaId}-hint` : undefined

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={areaId} className="text-title-md text-on-surface">
          {label}
        </label>
      )}
      <textarea
        id={areaId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`w-full resize-y rounded-lg bg-surface-container-low px-3.5 py-2.5 text-body-md text-on-surface shadow-hairline transition-all duration-150 placeholder:text-outline focus:bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-secondary/20 ${
          error ? 'ring-2 ring-error/40 focus:ring-error/60' : ''
        } ${className}`}
        {...rest}
      />
      {error ? (
        <p id={`${areaId}-error`} className="text-label-sm text-on-error-container">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${areaId}-hint`} className="text-label-sm text-on-surface-variant">
            {hint}
          </p>
        )
      )}
    </div>
  )
}
