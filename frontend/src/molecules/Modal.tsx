import type { ReactNode } from 'react'
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
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-inverse-surface/40 p-4"
      onClick={onClose}
    >
      <Card
        className={`w-full ${width} max-h-[90vh] overflow-auto rounded-xl p-space-xl shadow-pop`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-space-lg flex items-start justify-between gap-space-md">
          <h2 className="text-title-lg font-bold text-primary">{title}</h2>
          <button
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
