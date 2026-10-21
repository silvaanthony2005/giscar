import { Badge } from '../atoms/Badge'
import { Card } from '../atoms/Card'
import { Icon } from '../atoms/Icon'

/**
 * Guía de progreso del proyecto en Desarrollo.
 *
 * El backend decide el estado (`estado_desarrollo`); aquí solo se pinta como
 * un recorrido: en qué etapa está el proyecto y cuáles ya pasaron.
 */

interface Paso {
  estado: string
  titulo: string
  icono: string
}

const PASOS: Paso[] = [
  { estado: 'pendiente', titulo: 'Recibido de Ventas', icono: 'inbox' },
  { estado: 'en_planificacion', titulo: 'Plan técnico', icono: 'account_tree' },
  { estado: 'en_desarrollo', titulo: 'En Producción', icono: 'code' },
  { estado: 'completado', titulo: 'Completado', icono: 'check_circle' },
  { estado: 'enviado_despacho', titulo: 'En Despacho', icono: 'local_shipping' },
]

const ETAPA_ACTUAL = (estado: string) => PASOS.findIndex((p) => p.estado === estado)

export function FlujoProyecto({ estado }: { estado: string }) {
  const actual = ETAPA_ACTUAL(estado)
  const cancelado = estado === 'cancelado'
  // Ya traspasado a Despacho: en Desarrollo no queda nada pendiente.
  const traspasado = estado === 'enviado_despacho'

  return (
    <Card className="p-space-xl">
      <div className="flex flex-wrap items-center justify-between gap-space-md pb-space-md">
        <p className="text-title-lg font-bold text-on-surface">Progreso del proyecto</p>
        {cancelado && (
          <Badge tone="danger" icon="cancel">
            Cancelado
          </Badge>
        )}
      </div>
      <ol className="flex flex-col gap-space-md sm:flex-row sm:items-start sm:gap-space-sm">
        {PASOS.map((p, i) => {
          const hecho = !cancelado && (traspasado || actual > i)
          const enCurso = !cancelado && !traspasado && actual === i
          return (
            <li
              key={p.estado}
              aria-current={enCurso ? 'step' : undefined}
              className="flex flex-1 items-center gap-space-sm sm:flex-col sm:items-center sm:text-center"
            >
              <span
                className={`flex size-8 shrink-0 items-center justify-center rounded-full text-label-md font-semibold ${
                  hecho
                    ? 'bg-secondary text-on-secondary'
                    : enCurso
                      ? 'bg-primary text-on-primary shadow-raised'
                      : 'border border-outline-variant bg-surface-container-low text-outline'
                }`}
              >
                {hecho ? <Icon name="check" size="sm" /> : <Icon name={p.icono} size="sm" />}
              </span>
              <span className="min-w-0">
                <span
                  className={`block text-body-md font-medium ${enCurso ? 'text-primary' : 'text-on-surface'}`}
                >
                  {p.titulo}
                </span>
                <span className="block text-label-sm text-on-surface-variant">
                  {hecho
                    ? traspasado && i === PASOS.length - 1
                      ? 'Traspasado'
                      : 'Completado'
                    : enCurso
                      ? 'Etapa actual'
                      : 'Pendiente'}
                </span>
              </span>
            </li>
          )
        })}
      </ol>
    </Card>
  )
}
