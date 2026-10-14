import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  useAsignarIncidencia,
  useCambiarEstadoIncidencia,
  useIncidencia,
  useResolverIncidencia,
  useTecnicos,
} from '../../entities/project/tecnologia-api'
import { Button } from '../../atoms/Button'
import { Badge } from '../../atoms/Badge'
import { Card } from '../../atoms/Card'
import { Icon } from '../../atoms/Icon'
import { Input } from '../../atoms/Input'
import { Textarea } from '../../atoms/Textarea'
import { EstadoBadge } from '../../molecules/EstadoBadge'
import { Modal } from '../../molecules/Modal'
import { SectionHeader } from '../../molecules/SectionHeader'
import { AdjuntosPanel } from '../../organisms/AdjuntosPanel'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { formatDateTime } from '../../shared/lib/format'

const prioridadTone: Record<string, 'danger' | 'warning' | 'info' | 'neutral'> = {
  critica: 'danger',
  alta: 'warning',
  media: 'info',
  baja: 'neutral',
}

const dt = 'text-label-md font-semibold tracking-wide text-outline uppercase'

export function DetalleIncidenciaPage() {
  const { id = '' } = useParams()
  const { data: inc, isLoading, error } = useIncidencia(id)
  const { data: tecnicos } = useTecnicos()
  const cambiarEstado = useCambiarEstadoIncidencia(id)
  const asignar = useAsignarIncidencia(id)
  const resolver = useResolverIncidencia(id)

  const [showResolver, setShowResolver] = useState(false)
  const [form, setForm] = useState({
    diagnostico: '',
    solucion: '',
    tiempo_resolucion_horas: 1,
  })
  const [msg, setMsg] = useState<string | null>(null)

  if (isLoading) return <LoadingState />
  if (error || !inc) return <ErrorState message={error?.message ?? 'Incidencia no encontrada'} />

  const onResolver = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    resolver.mutate(form, {
      onSuccess: () => setShowResolver(false),
      onError: (err) => setMsg(err.message),
    })
  }

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Tecnología', 'Cola', inc.codigo]}
        title={inc.titulo}
        subtitle="Mesa de ayuda de hardware y electrónica."
        code={inc.codigo}
        actions={
          <div className="flex flex-wrap gap-space-sm">
            {inc.estado === 'abierta' && (
              <Button
                icon="play_arrow"
                variant="tonal"
                onClick={() => cambiarEstado.mutate('en_proceso')}
              >
                Tomar en proceso
              </Button>
            )}
            {inc.estado !== 'resuelta' && (
              <Button icon="build" onClick={() => setShowResolver(true)}>
                Resolver con reporte
              </Button>
            )}
          </div>
        }
      />
      <div className="mb-space-lg flex flex-wrap items-center gap-space-xs">
        <EstadoBadge valor={inc.estado} />
        <Badge tone={prioridadTone[inc.prioridad] ?? 'neutral'}>{inc.prioridad}</Badge>
        <Badge tone="info">{inc.departamento_origen}</Badge>
      </div>

      <div className="grid gap-space-lg lg:grid-cols-3">
        <Card className="p-space-xl lg:col-span-2">
          <SectionHeader
            icon="report_problem"
            title="Descripción"
            description="Detalle del fallo reportado."
            chip={`Orden #${inc.orden_llegada}`}
          />
          <p className="whitespace-pre-wrap text-body-md text-on-surface">{inc.descripcion}</p>
          <dl className="mt-space-lg grid grid-cols-1 gap-space-md border-t border-outline-variant/60 pt-space-lg text-body-md sm:grid-cols-2">
            <div>
              <dt className={dt}>Equipo afectado</dt>
              <dd className="text-on-surface">{inc.equipo_afectado}</dd>
            </div>
            <div>
              <dt className={dt}>Reportada</dt>
              <dd className="text-on-surface">{formatDateTime(inc.created_at)}</dd>
            </div>
            <div>
              <dt className={dt}>Reportada por</dt>
              <dd className="text-on-surface">{inc.reportado_por_nombre ?? '—'}</dd>
            </div>
            <div>
              <dt className={dt}>Orden de llegada</dt>
              <dd className="text-on-surface">#{inc.orden_llegada}</dd>
            </div>
          </dl>
        </Card>

        <Card className="p-space-xl">
          <SectionHeader
            icon="engineering"
            title="Asignación"
            description="Técnico responsable."
          />
          <p className="mb-space-md text-body-md text-on-surface-variant">
            {inc.asignado_a_nombre ? (
              <>
                Asignada a{' '}
                <strong className="text-on-surface">{inc.asignado_a_nombre}</strong>
              </>
            ) : (
              'Sin asignar'
            )}
          </p>
          {(tecnicos ?? []).length > 0 && (
            <div className="flex flex-wrap gap-space-sm">
              {(tecnicos ?? []).map((t) => (
                <Button
                  key={t.id}
                  size="sm"
                  variant={inc.asignado_a === t.id ? 'primary' : 'tonal'}
                  loading={asignar.isPending && asignar.variables === t.id}
                  onClick={() => asignar.mutate(t.id)}
                >
                  {t.nombre}
                </Button>
              ))}
            </div>
          )}
          {asignar.error && (
            <p className="mt-space-sm text-body-md text-on-error-container">
              {asignar.error.message}
            </p>
          )}
        </Card>
      </div>

      <section className="mt-space-xl">
        <SectionHeader
          icon="fact_check"
          title="Reportes de resolución"
          description="Diagnóstico y solución registrados al cerrar la incidencia."
        />
        <div className="space-y-space-md">
          {inc.reportes.map((r) => (
            <Card key={r.id} className="p-space-xl">
              <div className="flex flex-wrap items-center justify-between gap-space-sm">
                <span className="text-body-md font-semibold text-on-surface">
                  {r.resuelto_por_nombre ?? '—'}
                </span>
                <span className="text-label-sm text-outline">
                  {formatDateTime(r.fecha)} · {r.tiempo_resolucion_horas}h
                </span>
              </div>
              <p className="mt-space-md text-body-md">
                <span className="font-semibold text-on-surface">Diagnóstico:</span>{' '}
                <span className="text-on-surface-variant">{r.diagnostico}</span>
              </p>
              <p className="mt-space-sm text-body-md">
                <span className="font-semibold text-on-surface">Solución:</span>{' '}
                <span className="text-on-surface-variant">{r.solucion}</span>
              </p>
            </Card>
          ))}
          {inc.reportes.length === 0 && (
            <p className="text-body-md text-on-surface-variant">
              Sin reportes de resolución.
            </p>
          )}
        </div>
      </section>

      <section className="mt-space-xl">
        <AdjuntosPanel
          tipo="incidencia"
          entidadId={inc.id}
          title="Evidencia fotográfica y documentos"
          description="Fotos del fallo, del equipo y del acta de resolución."
        />
      </section>

      <Modal
        open={showResolver}
        onClose={() => setShowResolver(false)}
        title="Resolver incidencia"
        width="max-w-2xl"
      >
        <form onSubmit={onResolver} className="space-y-space-lg">
          <Textarea
            label="Diagnóstico *"
            hint="Mínimo 10 caracteres."
            required
            minLength={10}
            rows={3}
            value={form.diagnostico}
            onChange={(e) => setForm({ ...form, diagnostico: e.target.value })}
          />
          <Textarea
            label="Solución *"
            hint="Mínimo 10 caracteres."
            required
            minLength={10}
            rows={3}
            value={form.solucion}
            onChange={(e) => setForm({ ...form, solucion: e.target.value })}
          />
          <Input
            label="Tiempo de resolución (horas)"
            type="number"
            min="0"
            value={form.tiempo_resolucion_horas}
            onChange={(e) =>
              setForm({ ...form, tiempo_resolucion_horas: Number(e.target.value) })
            }
          />
          <p className="text-label-sm text-on-surface-variant">
            La incidencia pasará a <strong>resuelta</strong>.
          </p>
          {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" loading={resolver.isPending} className="w-full">
            Guardar y resolver
          </Button>
        </form>
      </Modal>

      <p className="mt-space-xl text-body-md">
        <Link
          to="/tecnologia"
          className="inline-flex items-center gap-1 text-secondary hover:underline"
        >
          <Icon name="arrow_back" size="sm" />
          Volver a la cola
        </Link>
      </p>
    </div>
  )
}
