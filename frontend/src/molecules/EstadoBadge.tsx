import type { ReactNode } from 'react'
import { Badge } from '../atoms/Badge'

type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

const ESTADOS: Record<string, { label: string; tone: Tone }> = {
  // Ventas
  borrador: { label: 'Borrador', tone: 'neutral' },
  levantamiento: { label: 'Levantamiento', tone: 'info' },
  cobrado_50: { label: 'Cobrado 50%', tone: 'warning' },
  cobrado_100: { label: 'Cobrado 100%', tone: 'success' },
  enviado_desarrollo: { label: 'En Producción', tone: 'info' },
  cerrado: { label: 'Cobro completo', tone: 'success' },
  // Producción
  pendiente: { label: 'Pendiente', tone: 'neutral' },
  en_planificacion: { label: 'Planificación', tone: 'info' },
  en_desarrollo: { label: 'En Producción', tone: 'info' },
  completado: { label: 'Completado', tone: 'success' },
  cancelado: { label: 'Cancelado', tone: 'danger' },
  enviado_despacho: { label: 'En Despacho', tone: 'success' },
  // Despacho
  pendiente_entrega: { label: 'Pendiente de entrega', tone: 'warning' },
  entregado: { label: 'Entregado', tone: 'success' },
  negado: { label: 'Negado', tone: 'danger' },
  saldo_pendiente: { label: 'Saldo pendiente', tone: 'warning' },
  // Fases
  en_curso: { label: 'En curso', tone: 'info' },
  // Incidencias
  abierta: { label: 'Abierta', tone: 'warning' },
  en_proceso: { label: 'En proceso', tone: 'info' },
  resuelta: { label: 'Resuelta', tone: 'success' },
  cerrada: { label: 'Cerrada', tone: 'neutral' },
  // Usuarios
  activo: { label: 'Activo', tone: 'success' },
  bloqueado: { label: 'Bloqueado', tone: 'danger' },
}

const PRIORIDADES: Record<string, { label: string; tone: Tone }> = {
  baja: { label: 'Baja', tone: 'neutral' },
  media: { label: 'Media', tone: 'info' },
  alta: { label: 'Alta', tone: 'warning' },
  critica: { label: 'Crítica', tone: 'danger' },
}

export function EstadoBadge({ valor }: { valor: string }) {
  const cfg = ESTADOS[valor] ?? { label: valor, tone: 'neutral' as Tone }
  return <Badge tone={cfg.tone}>{cfg.label}</Badge>
}

export function PrioridadBadge({ valor }: { valor: string }) {
  const cfg = PRIORIDADES[valor] ?? { label: valor, tone: 'neutral' as Tone }
  return <Badge tone={cfg.tone}>{cfg.label}</Badge>
}

export function EstadoBadgePair({
  ventas,
  desarrollo,
  despacho,
}: {
  ventas?: string
  desarrollo?: string
  despacho?: string
}): ReactNode {
  return (
    <div className="flex flex-wrap gap-1.5">
      {ventas && <EstadoBadge valor={ventas} />}
      {desarrollo && <EstadoBadge valor={desarrollo} />}
      {despacho && <EstadoBadge valor={despacho} />}
    </div>
  )
}
