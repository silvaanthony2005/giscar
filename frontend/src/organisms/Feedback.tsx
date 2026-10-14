import type { ReactNode } from 'react'
import { Card } from '../atoms/Card'

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string
  value: ReactNode
  hint?: string
}) {
  return (
    <Card className="p-space-lg">
      <p className="text-label-md font-semibold tracking-wide text-on-surface-variant uppercase">
        {label}
      </p>
      <p className="mt-1 text-headline-md text-on-surface tracking-tight">{value}</p>
      {hint && <p className="mt-1 text-label-sm text-outline">{hint}</p>}
    </Card>
  )
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <Card className="p-space-xl text-center">
      <p className="text-title-md font-semibold text-on-surface">{title}</p>
      {description && <p className="mt-1 text-body-md text-on-surface-variant">{description}</p>}
    </Card>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <Card className="rounded-lg bg-error-container p-space-md">
      <p className="text-body-md font-medium text-on-error-container">{message}</p>
    </Card>
  )
}

export function LoadingState({ text = 'Cargando…' }: { text?: string }) {
  return (
    <div className="flex items-center justify-center gap-space-sm p-space-xl text-on-surface-variant">
      <span className="size-4 animate-spin rounded-full border-2 border-secondary border-t-transparent" />
      <span className="text-body-md">{text}</span>
    </div>
  )
}
