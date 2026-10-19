import { useEffect, useId, useRef, type ReactNode } from 'react'
import { Card } from '../atoms/Card'
import { Icon } from '../atoms/Icon'

export function Modal({
  open,
  onClose,
  title,
  children,
  width = 'max-w-lg',
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  width?: string
}) {
  const titleId = useId()
  const dialogRef = useRef<HTMLDivElement>(null)
  const cerrarRef = useRef<HTMLButtonElement>(null)
  // `onClose` cambia de identidad en cada render; sin esta ref el efecto del
  // foco se re-ejecutaría con cada tecla escrita dentro del modal.
  const onCloseRef = useRef(onClose)
  useEffect(() => {
    onCloseRef.current = onClose
  })

  // Al abrir: foco en el modal y Escape para cerrar. Al volver a Tabular se
  // mantiene el foco dentro mientras el modal está abierto (patrón de diálogo).
  useEffect(() => {
    if (!open) return
    const focoPrevio = document.activeElement as HTMLElement | null
    cerrarRef.current?.focus()
    const alPulsar = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCloseRef.current()
        return
      }
      if (e.key !== 'Tab') return
      const foco = dialogRef.current?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])',
      )
      if (!foco || foco.length === 0) return
      const activo = document.activeElement
      const dentro = dialogRef.current?.contains(activo) ?? false
      if (e.shiftKey && (!dentro || activo === foco[0])) {
        e.preventDefault()
        foco[foco.length - 1].focus()
      } else if (!e.shiftKey && (dentro === false || activo === foco[foco.length - 1])) {
        e.preventDefault()
        foco[0].focus()
      }
    }
    document.addEventListener('keydown', alPulsar)
    return () => {
      document.removeEventListener('keydown', alPulsar)
      focoPrevio?.focus()
    }
  }, [open])

  if (!open) return null
  return (
    <div
      ref={dialogRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-inverse-surface/40 p-4"
      onClick={onClose}
    >
      <Card
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={`w-full ${width} max-h-[90vh] overflow-auto rounded-xl p-space-xl shadow-pop`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-space-lg flex items-start justify-between gap-space-md">
          <h2 id={titleId} className="text-title-lg font-bold text-primary">
            {title}
          </h2>
          <button
            ref={cerrarRef}
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="-mt-1 flex size-8 items-center justify-center rounded-lg text-on-surface-variant transition-colors hover:bg-surface-container hover:text-on-surface"
          >
            <Icon name="close" size="sm" />
          </button>
        </div>
        {children}
      </Card>
    </div>
  )
}
