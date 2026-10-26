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
import { Checkbox } from '../../atoms/Checkbox'
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

const dt = 'text-label-md font-semibold tracking-wide text-on-surface-variant uppercase'

export function DetalleIncidenciaPage() {
  const { id = '' } = useParams()
  const { data: inc, isLoading, error } = useIncidencia(id)
  const {
    data: tecnicos,
    isLoading: tecnicosLoading,
    error: tecnicosError,
  } = useTecnicos()
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
  const [showAsignar, setShowAsignar] = useState(false)
  const [sel, setSel] = useState<string[]>([])

  if (isLoading) return <LoadingState />
  if (error || !inc) return <ErrorState message={error?.message ?? 'Incidencia no encontrada'} />

  const onAbrirAsignar = () => {
    setSel(inc.asignados.map((a) => a.user_id))
    setShowAsignar(true)
  }

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
          <div className="flex items-start justify-between gap-space-md">
            <SectionHeader
              icon="engineering"
              title="Asignación"
              description="Técnicos responsables."
            />
            {inc.estado !== 'cerrada' && (
              <Button size="sm" variant="tonal" icon="person_add" onClick={onAbrirAsignar}>
                Asignar
              </Button>
            )}
          </div>
          {inc.asignados.length > 0 ? (
            <ul className="space-y-space-xs">
              {inc.asignados.map((a) => (
                <li
                  key={a.user_id}
                  className="flex items-center gap-space-sm rounded-lg px-space-sm py-1.5"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-body-md text-on-surface">
                      {a.nombre ?? '—'}
                    </span>
                    <span className="block text-label-sm text-on-surface-variant">
                      {a.cargo ?? 'Tecnología'}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-body-md text-on-surface-variant">Sin técnicos asignados aún.</p>
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
                <span className="text-label-sm text-on-surface-variant">
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

      <Modal open={showAsignar} onClose={() => setShowAsignar(false)} title="Asignar técnicos">
        <p className="text-body-md text-on-surface-variant">
          Selecciona las personas responsables de la incidencia.
        </p>
        {tecnicosLoading && (
          <p className="mt-space-md text-body-md text-on-surface-variant">Cargando equipo…</p>
        )}
        {tecnicosError && (
          <p role="alert" className="mt-space-md text-body-md text-on-error-container">
            {tecnicosError.message}
          </p>
        )}
        {tecnicos && tecnicos.length === 0 && (
          <p className="mt-space-md text-body-md text-on-surface-variant">
            No hay técnicos disponibles para asignar.
          </p>
        )}
        {tecnicos && tecnicos.length > 0 && (
          <ul className="mt-space-md max-h-80 space-y-1 overflow-y-auto">
            {tecnicos.map((t) => (
              <li key={t.id}>
                <Checkbox
                  label={t.nombre}
                  sublabel={t.cargo ?? 'Tecnología'}
                  checked={sel.includes(t.id)}
                  onChange={() =>
                    setSel((prev) =>
                      prev.includes(t.id) ? prev.filter((x) => x !== t.id) : [...prev, t.id],
                    )
                  }
                />
              </li>
            ))}
          </ul>
        )}
        {asignar.error && (
          <p role="alert" className="mt-space-md text-body-md text-on-error-container">
            {asignar.error.message}
          </p>
        )}
        <div className="mt-space-lg flex justify-end gap-space-sm">
          <Button variant="secondary" onClick={() => setShowAsignar(false)}>
            Cerrar
          </Button>
          <Button
            loading={asignar.isPending}
            icon="check"
            onClick={() => asignar.mutate(sel, { onSuccess: () => setShowAsignar(false) })}
          >
            Guardar selección
          </Button>
        </div>
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
