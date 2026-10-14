import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  useCancel,
  useCancellation,
  useAcciones,
  useCreatePlan,
  usePhaseAction,
  usePlan,
  useProjectActions,
  useRecordProgress,
} from '../../entities/project/desarrollo-api'
import { Button } from '../../atoms/Button'
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

interface FaseForm {
  orden: number
  nombre: string
  descripcion: string
  horas_estimadas: number
}

const filaFase = 'pl-3.5 pr-3.5'

export function DetalleProyectoDesarrolloPage() {
  const { id = '' } = useParams()
  const { data: plan, isLoading, error } = usePlan(id)
  const createPlan = useCreatePlan(id)
  const phaseAction = usePhaseAction(id)
  const recordProgress = useRecordProgress(id)
  const actions = useProjectActions(id)
  const cancel = useCancel(id)
  const { data: cancellation } = useCancellation(id)
  const { data: accionesData } = useAcciones(id)
  const sinPlanAcciones = accionesData?.acciones ?? []
  const [accionError, setAccionError] = useState<string | null>(null)
  const onAccion = (m: { mutate: () => void }) => {
    setAccionError(null)
    m.mutate()
  }
  const onPhase = (fid: string, target: string) => {
    setAccionError(null)
    phaseAction.mutate({ fid, target })
  }

  const [resumen, setResumen] = useState('')
  const [objetivos, setObjetivos] = useState('')
  const [horas, setHoras] = useState('')
  const [fases, setFases] = useState<FaseForm[]>([])
  const [faseTmp, setFaseTmp] = useState<FaseForm>({
    orden: 1,
    nombre: '',
    descripcion: '',
    horas_estimadas: 0,
  })
  const [msg, setMsg] = useState<string | null>(null)

  const [showProgress, setShowProgress] = useState(false)
  const [avancePct, setAvancePct] = useState(50)
  const [avanceNotas, setAvanceNotas] = useState('')

  const [showCancel, setShowCancel] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [informe, setInforme] = useState('')

  if (isLoading) return <LoadingState />

  if (!plan) {
    if (!sinPlanAcciones.includes('crear_plan')) {
      return (
        <div className="p-6">
          <PageHeader
            breadcrumb={['Desarrollo', 'Proyectos']}
            title="Plan de desarrollo"
            subtitle="El proyecto aún no tiene plan"
          />
          <Card className="max-w-2xl p-space-xl">
            <p className="text-body-md text-on-surface-variant">
              El proyecto todavía no está listo para planificar.
              {sinPlanAcciones.includes('cancelar') && ' También puede cancelarse desde aquí.'}
            </p>
          </Card>
          <p className="mt-space-xl text-body-md">
            <Link
              to="/desarrollo"
              className="inline-flex items-center gap-1 text-secondary hover:underline"
            >
              <Icon name="arrow_back" size="sm" />
              Volver a Desarrollo
            </Link>
          </p>
        </div>
      )
    }
    return (
      <div className="p-6">
        <PageHeader
          breadcrumb={['Desarrollo', 'Proyectos']}
          title="Crear plan de desarrollo"
          subtitle="Resumen, objetivos y desglose de fases con estimación de horas."
        />
        {error && <ErrorState message={error.message} />}
        <Card className="max-w-2xl p-space-xl">
          <SectionHeader
            icon="account_tree"
            title="Plan técnico"
            description="Define el alcance y el desglose de trabajo por fases."
            chip="Obligatorio"
          />
          <form
            onSubmit={(e: FormEvent) => {
              e.preventDefault()
              setMsg(null)
              createPlan.mutate(
                {
                  resumen,
                  objetivos,
                  horas_estimadas: Number(horas),
                  fases,
                  miembros: [],
                },
                { onError: (err) => setMsg(err.message) },
              )
            }}
            className="space-y-space-lg"
          >
            <Input
              label="Resumen *"
              value={resumen}
              onChange={(e) => setResumen(e.target.value)}
              required
            />
            <Textarea
              label="Objetivos"
              rows={3}
              value={objetivos}
              onChange={(e) => setObjetivos(e.target.value)}
            />
            <Input
              label="Horas estimadas totales *"
              type="number"
              min="1"
              value={horas}
              onChange={(e) => setHoras(e.target.value)}
              required
            />

            <div className="border-t border-outline-variant/60 pt-space-lg">
              <p className="mb-space-md text-title-md text-on-surface">Fases</p>
              <div className="grid grid-cols-12 gap-space-sm">
                <Input
                  aria-label="Orden"
                  className={`col-span-2 ${filaFase}`}
                  type="number"
                  min="1"
                  placeholder="Orden"
                  value={faseTmp.orden}
                  onChange={(e) => setFaseTmp({ ...faseTmp, orden: Number(e.target.value) })}
                />
                <Input
                  aria-label="Nombre de la fase"
                  className={`col-span-4 ${filaFase}`}
                  placeholder="Nombre"
                  value={faseTmp.nombre}
                  onChange={(e) => setFaseTmp({ ...faseTmp, nombre: e.target.value })}
                />
                <Input
                  aria-label="Horas de la fase"
                  className={`col-span-3 ${filaFase}`}
                  type="number"
                  min="0"
                  placeholder="Horas"
                  value={faseTmp.horas_estimadas}
                  onChange={(e) =>
                    setFaseTmp({ ...faseTmp, horas_estimadas: Number(e.target.value) })
                  }
                />
                <Button
                  type="button"
                  variant="tonal"
                  className="col-span-3 h-10"
                  onClick={() => {
                    if (!faseTmp.nombre.trim()) return
                    setFases([...fases, faseTmp])
                    setFaseTmp({
                      orden: fases.length + 2,
                      nombre: '',
                      descripcion: '',
                      horas_estimadas: 0,
                    })
                  }}
                >
                  Añadir fase
                </Button>
              </div>
              {fases.length > 0 && (
                <ul className="mt-space-md space-y-space-xs">
                  {fases.map((f, i) => (
                    <li
                      key={i}
                      className="flex items-center justify-between rounded-lg bg-surface-container-low px-space-md py-space-sm text-body-md"
                    >
                      <span className="text-on-surface">
                        {f.orden}. {f.nombre} ({f.horas_estimadas}h)
                      </span>
                      <button
                        type="button"
                        onClick={() => setFases(fases.filter((_, j) => j !== i))}
                        className="text-on-error-container hover:underline"
                      >
                        Quitar
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
            <Button type="submit" loading={createPlan.isPending} className="w-full">
              Guardar plan
            </Button>
          </form>
        </Card>
      </div>
    )
  }

  const proyecto = plan
  const accionesDelProyecto = proyecto.acciones

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Desarrollo', 'Proyectos', 'Plan']}
        title={proyecto.plan.resumen}
        subtitle="Seguimiento técnico por fases, avances, evidencia y cancelación formal."
        code={`${proyecto.plan.horas_estimadas}h · ${proyecto.fases.length} fases`}
        actions={
          <div className="flex flex-wrap gap-space-sm">
            <Button icon="trending_up" onClick={() => setShowProgress(true)}>
              Registrar avance
            </Button>
            {accionesDelProyecto.includes('iniciar') && (
              <Button
                icon="play_arrow"
                variant="tonal"
                loading={actions.iniciar.isPending}
                onClick={() => onAccion(actions.iniciar)}
              >
                Iniciar desarrollo
              </Button>
            )}
            {accionesDelProyecto.includes('completar') && (
              <Button
                icon="check_circle"
                variant="tonal"
                loading={actions.completar.isPending}
                onClick={() => onAccion(actions.completar)}
              >
                Completar
              </Button>
            )}
            {accionesDelProyecto.includes('pasar_despacho') && (
              <Button
                icon="local_shipping"
                loading={actions.pasarDespacho.isPending}
                onClick={() => onAccion(actions.pasarDespacho)}
              >
                Pasar a Despacho
              </Button>
            )}
            {accionesDelProyecto.includes('cancelar') && (
              <Button icon="cancel" variant="danger" onClick={() => setShowCancel(true)}>
                Cancelar
              </Button>
            )}
          </div>
        }
      />
      {(accionError ||
        phaseAction.error ||
        actions.iniciar.error ||
        actions.completar.error ||
        actions.pasarDespacho.error) && (
        <p className="mb-space-lg rounded-lg bg-error-container px-space-md py-space-sm text-body-md font-medium text-on-error-container">
          {accionError ??
            phaseAction.error?.message ??
            actions.iniciar.error?.message ??
            actions.completar.error?.message ??
            actions.pasarDespacho.error?.message}
        </p>
      )}

      <div className="grid gap-space-lg lg:grid-cols-3">
        <Card className="p-space-xl lg:col-span-2">
          <SectionHeader
            icon="article"
            title="Resumen"
            description="Alcance definido en el plan técnico."
          />
          <p className="text-body-md text-on-surface">{proyecto.plan.resumen}</p>
          {proyecto.plan.objetivos && (
            <>
              <h3 className="mt-space-lg mb-space-xs text-title-md text-on-surface">
                Objetivos
              </h3>
              <p className="text-body-md text-on-surface-variant">{proyecto.plan.objetivos}</p>
            </>
          )}
          <dl className="mt-space-lg grid grid-cols-3 gap-space-md border-t border-outline-variant/60 pt-space-lg text-center">
            <div>
              <dt className="text-label-md font-semibold tracking-wide text-outline uppercase">
                Horas plan
              </dt>
              <dd className="text-title-lg text-on-surface">{proyecto.plan.horas_estimadas}h</dd>
            </div>
            <div>
              <dt className="text-label-md font-semibold tracking-wide text-outline uppercase">
                Horas fases
              </dt>
              <dd className="text-title-lg text-on-surface">{proyecto.horas_totales_fases}h</dd>
            </div>
            <div>
              <dt className="text-label-md font-semibold tracking-wide text-outline uppercase">
                Avances
              </dt>
              <dd className="text-title-lg text-on-surface">{proyecto.avances.length}</dd>
            </div>
          </dl>
        </Card>

        <Card className="p-space-xl">
          <SectionHeader
            icon="groups"
            title="Miembros asignados"
            description="Equipo del proyecto."
          />
          {proyecto.miembros.length === 0 ? (
            <p className="text-body-md text-on-surface-variant">Sin miembros asignados aún.</p>
          ) : (
            <ul className="space-y-space-sm">
              {proyecto.miembros.map((m) => (
                <li key={m.id} className="flex items-center justify-between text-body-md">
                  <span className="text-on-surface">{m.nombre_usuario}</span>
                  <span className="text-on-surface-variant">{m.rol_proyecto}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <section className="mt-space-xl">
        <SectionHeader
          icon="list_alt"
          title="Fases"
          description="Estado y control de cada fase del plan."
        />
        <div className="space-y-space-md">
          {proyecto.fases.map((f) => (
            <Card key={f.id} className="flex flex-wrap items-center justify-between gap-space-md p-space-lg">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-space-sm">
                  <span className="text-body-md font-semibold text-on-surface">
                    {f.orden}. {f.nombre}
                  </span>
                  <EstadoBadge valor={f.estado} />
                </div>
                {f.descripcion && (
                  <p className="mt-1 text-body-md text-on-surface-variant">{f.descripcion}</p>
                )}
                <p className="mt-1 text-label-sm text-outline">
                  Estimado: {f.horas_estimadas}h
                  {f.fecha_fin_estimada ? ` · Fin estimado: ${f.fecha_fin_estimada}` : ''}
                </p>
              </div>
              <div className="flex gap-space-sm">
                {f.acciones.includes('en_curso') && (
                  <Button
                    size="sm"
                    variant="tonal"
                    loading={phaseAction.isPending && phaseAction.variables?.fid === f.id}
                    onClick={() => onPhase(f.id, 'en_curso')}
                  >
                    Iniciar
                  </Button>
                )}
                {f.acciones.includes('completada') && (
                  <Button
                    size="sm"
                    loading={phaseAction.isPending && phaseAction.variables?.fid === f.id}
                    onClick={() => onPhase(f.id, 'completada')}
                  >
                    Completar
                  </Button>
                )}
              </div>
            </Card>
          ))}
          {proyecto.fases.length === 0 && (
            <p className="text-body-md text-on-surface-variant">Sin fases definidas.</p>
          )}
        </div>
      </section>

      <section className="mt-space-xl grid gap-space-lg lg:grid-cols-2">
        <div>
          <SectionHeader
            icon="history"
            title="Historial de avances"
            description="Registro cronológico del porcentaje de avance."
          />
          <div className="space-y-space-md">
            {proyecto.avances.map((a) => (
              <Card key={a.id} className="p-space-lg">
                <div className="flex items-center justify-between">
                  <span className="text-body-md font-semibold text-on-surface">{a.autor}</span>
                  <span className="text-body-md font-semibold text-secondary">{a.porcentaje}%</span>
                </div>
                <p className="mt-1 text-body-md text-on-surface-variant">{a.notas}</p>
                <p className="mt-1 text-label-sm text-outline">{formatDateTime(a.fecha)}</p>
              </Card>
            ))}
            {proyecto.avances.length === 0 && (
              <p className="text-body-md text-on-surface-variant">Sin avances registrados.</p>
            )}
          </div>
        </div>
        <AdjuntosPanel tipo="plan" entidadId={proyecto.plan.id} />
      </section>

      {cancellation && (
        <Card className="mt-space-xl bg-error-container p-space-xl">
          <h2 className="text-title-lg font-bold text-on-error-container">
            Informe de cancelación
          </h2>
          <p className="mt-space-xs text-body-md text-on-error-container">
            <strong>Motivo:</strong> {cancellation.motivo}
          </p>
          <p className="mt-space-sm whitespace-pre-wrap text-body-md text-on-error-container">
            {cancellation.informe}
          </p>
          <p className="mt-space-sm text-label-sm text-on-error-container">
            {formatDateTime(cancellation.fecha)}
          </p>
        </Card>
      )}

      <Modal open={showProgress} onClose={() => setShowProgress(false)} title="Registrar avance">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            recordProgress.mutate(
              { porcentaje: avancePct, notas: avanceNotas },
              {
                onSuccess: () => {
                  setShowProgress(false)
                  setAvanceNotas('')
                },
              },
            )
          }}
          className="space-y-space-lg"
        >
          <div>
            <label htmlFor="avance-pct" className="mb-1.5 block text-title-md text-on-surface">
              Porcentaje: {avancePct}%
            </label>
            <input
              id="avance-pct"
              type="range"
              min="0"
              max="100"
              step="5"
              value={avancePct}
              onChange={(e) => setAvancePct(Number(e.target.value))}
              className="w-full accent-secondary"
            />
          </div>
          <Textarea
            label="Notas *"
            required
            rows={3}
            value={avanceNotas}
            onChange={(e) => setAvanceNotas(e.target.value)}
            placeholder="Describe lo avanzado…"
          />
          <Button type="submit" loading={recordProgress.isPending} className="w-full">
            Guardar avance
          </Button>
        </form>
      </Modal>

      <Modal open={showCancel} onClose={() => setShowCancel(false)} title="Cancelar proyecto">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            cancel.mutate({ motivo, informe }, { onSuccess: () => setShowCancel(false) })
          }}
          className="space-y-space-lg"
        >
          <Input
            label="Motivo *"
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            required
          />
          <Textarea
            label="Informe *"
            hint="Mínimo 30 caracteres."
            required
            minLength={30}
            rows={5}
            value={informe}
            onChange={(e) => setInforme(e.target.value)}
            placeholder="Explique por qué se cancela este proyecto…"
          />
          {cancel.error && (
            <p className="text-body-md text-on-error-container">{cancel.error.message}</p>
          )}
          <Button type="submit" variant="danger" loading={cancel.isPending} className="w-full">
            Confirmar cancelación
          </Button>
        </form>
      </Modal>

      <p className="mt-space-xl text-body-md">
        <Link
          to="/desarrollo"
          className="inline-flex items-center gap-1 text-secondary hover:underline"
        >
          <Icon name="arrow_back" size="sm" />
          Volver a Desarrollo
        </Link>
      </p>
    </div>
  )
}
