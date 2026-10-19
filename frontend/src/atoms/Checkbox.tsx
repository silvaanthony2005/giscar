import type { InputHTMLAttributes } from 'react'

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string
  /** Texto secundario bajo el nombre (p. ej. el departamento). */
  sublabel?: string
}

/** Casilla con su etiqueta en fila, para listas seleccionables. */
export function Checkbox({ label, sublabel, className = '', ...rest }: Props) {
  return (
    <label
      className={`flex cursor-pointer items-center gap-3 rounded-lg px-space-sm py-2.5 transition-colors hover:bg-surface-container-low focus-within:bg-surface-container-low ${className}`}
    >
      <input type="checkbox" className="size-4 shrink-0 accent-secondary" {...rest} />
      <span className="min-w-0">
        <span className="block truncate text-body-md text-on-surface">{label}</span>
        {sublabel && <span className="block text-label-sm text-outline">{sublabel}</span>}
      </span>
    </label>
  )
}
