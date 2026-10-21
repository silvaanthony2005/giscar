import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  useAsignarMiembros,
  useCancel,
  useCancellation,
  useAcciones,
  useCatalogoUsuarios,
  useCreatePlan,
  usePhaseAction,
  usePlan,
  useProjectActions,
  useQuitarMiembro,
  useRecordProgress,
} from '../../entities/project/desarrollo-api'
import { Button } from '../../atoms/Button'
import { Card } from '../../atoms/Card'
import { Checkbox } from '../../atoms/Checkbox'
import { Icon } from '../../atoms/Icon'
import { IconButton } from '../../atoms/IconButton'
import { Input } from '../../atoms/Input'
import { Textarea } from '../../atoms/Textarea'
import { EstadoBadge } from '../../molecules/EstadoBadge'
import { FlujoProyecto } from '../../molecules/FlujoProyecto'
import { Modal } from '../../molecules/Modal'
import { SectionHeader } from '../../molecules/SectionHeader'
import { AdjuntosPanel } from '../../organisms/AdjuntosPanel'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { ApiError } from '../../shared/api/client'
import { DEPARTAMENTOS, formatDateTime } from '../../shared/lib/format'

interface FaseForm {
  orden: number
  nombre: string
  descripcion: string
  horas_estimadas: number
}

/** Borrador de la fase en edición: las horas van como texto para poder vaciarlas. */
interface FaseDraft {
  orden: number
  nombre: string
  descripcion: string
  horas: string
}

export function DetalleProyectoDesarrolloPage() {
  const { id = '' } = useParams()
  const { data: plan, isLoading, error } = usePlan(id)
  const createPlan = useCreatePlan(id)
  const phaseAction = usePhaseAction(id)
  const recordProgress = useRecordProgress(id)
  const actions = useProjectActions(id)
  const cancel = useCancel(id)
  const catalogo = useCatalogoUsuarios()
  const asignar = useAsignarMiembros(id)
  const quitar = useQuitarMiembro(id)
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
  const [faseTmp, setFaseTmp] = useState<FaseDraft>({
    orden: 1,
    nombre: '',
    descripcion: '',
    horas: '',
  })
  const [msg, setMsg] = useState<string | null>(null)
  const [faseError, setFaseError] = useState<string | null>(null)
  const [miembrosSel, setMiembrosSel] = useState<string[]>([])
  const [showMembers, setShowMembers] = useState(false)
  const [seleccion, setSeleccion] = useState<string[]>([])

  const alternaMiembro = (uid: string) =>
    setMiembrosSel((prev) => (prev.includes(uid) ? prev.filter((x) => x !== uid) : [...prev, uid]))

  const addFase = () => {
    if (!faseTmp.nombre.trim()) {
      setFaseError('La fase necesita un nombre para poder añadirse.')
      return
    }
    setFases([
      ...fases,
      {
        orden: faseTmp.orden,
        nombre: faseTmp.nombre,
        descripcion: faseTmp.descripcion,
        horas_estimadas: Number(faseTmp.horas),
      },
    ])
    setFaseTmp({ orden: fases.length + 2, nombre: '', descripcion: '', horas: '' })
    setFaseError(null)
  }

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
            breadcrumb={['Producción', 'Proyectos']}
            title="Plan de producción"
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
              Volver a Producción
            </Link>
          </p>
        </div>
      )
    }
    return (
      <div className="p-6">
        <PageHeader
          breadcrumb={['Producción', 'Proyectos']}
          title="Crear plan de producción"
          subtitle="Alcance, equipo y desglose de fases con estimación de horas."
          actions={
            <Link
              to="/desarrollo"
              className="inline-flex items-center gap-1 text-body-md text-secondary hover:underline"
            >
              <Icon name="arrow_back" size="sm" />
              Volver
            </Link>
          }
        />
        {/* El 404 es el estado normal (aún no hay plan); solo avisamos fallos reales. */}
        {error && !(error instanceof ApiError && error.status === 404) && (
          <ErrorState message={error.message} />
        )}
        <FlujoProyecto estado={accionesData?.estado_desarrollo ?? 'pendiente'} />

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
                miembros: miembrosSel,
              },
              { onError: (err) => setMsg(err.message) },
            )
          }}
          className="mt-space-xl"
        >
          <div className="grid gap-space-xl lg:grid-cols-3">
            <Card className="p-space-xl lg:col-span-2">
              <SectionHeader
                icon="article"
                title="Alcance del plan"
                description="Qué se construye y cuántas horas se estiman."
                chip="Obligatorio"
              />
              <div className="space-y-space-lg">
                <Input
                  label="Resumen *"
                  hint="Una frase con el alcance del trabajo."
                  value={resumen}
                  onChange={(e) => setResumen(e.target.value)}
                  required
                />
                <Textarea
                  label="Objetivos"
                  rows={4}
                  hint="Resultado que debe lograrse con este proyecto."
                  value={objetivos}
                  onChange={(e) => setObjetivos(e.target.value)}
                />
                <Input
                  label="Horas estimadas totales *"
                  type="number"
                  min="1"
                  inputMode="numeric"
                  hint="Suma esperada de horas del equipo."
                  value={horas}
                  onChange={(e) => setHoras(e.target.value)}
                  required
                />
              </div>
            </Card>

            <Card className="p-space-xl">
              <SectionHeader
                icon="groups"
                title="Equipo asignado"
                description="Personas que trabajarán en el proyecto."
              />
              {catalogo.isLoading && (
                <p className="text-body-md text-on-surface-variant">Cargando equipo…</p>
              )}
              {catalogo.error && (
                <p role="alert" className="text-body-md text-on-error-container">
                  {catalogo.error.message}
                </p>
              )}
              {catalogo.data && catalogo.data.length === 0 && (
                <p className="text-body-md text-on-surface-variant">
                  No hay usuarios disponibles para asignar.
                </p>
              )}
              {catalogo.data && catalogo.data.length > 0 && (
                <fieldset>
                  <legend className="sr-only">Miembros del proyecto</legend>
                  <ul className="max-h-72 space-y-1 overflow-y-auto">
                    {catalogo.data.map((u) => (
                      <li key={u.id}>
                        <Checkbox
                          label={u.nombre}
                          sublabel={DEPARTAMENTOS[u.departamento] ?? u.departamento}
                          checked={miembrosSel.includes(u.id)}
                          onChange={() => alternaMiembro(u.id)}
                        />
                      </li>
                    ))}
                  </ul>
                </fieldset>
              )}
            </Card>
          </div>

          <Card className="mt-space-xl p-space-xl">
            <SectionHeader
              icon="list_alt"
              title="Fases del trabajo"
              description="Cada fase con sus horas; se podrán mover una vez inicies la producción."
              chip={fases.length > 0 ? `${fases.length} añadida${fases.length === 1 ? '' : 's'}` : undefined}
            />
            {fases.length > 0 && (
              <ul className="space-y-space-sm">
                {fases.map((f, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-space-sm rounded-lg border border-outline-variant/60 bg-surface-container-lowest px-space-md py-space-sm"
                  >
                    <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-secondary text-label-sm font-bold text-on-secondary">
                      {f.orden}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-body-md font-medium text-on-surface">
                        {f.nombre}
                        <span className="font-normal text-on-surface-variant">
                          {' '}
                          · {f.horas_estimadas}h
                        </span>
                      </span>
                      {f.descripcion && (
                        <span className="block text-body-sm text-on-surface-variant">
                          {f.descripcion}
                        </span>
                      )}
                    </span>
                    <IconButton
                      icon="delete"
                      tone="danger"
                      label={`Quitar la fase ${f.nombre}`}
                      onClick={() => setFases(fases.filter((_, j) => j !== i))}
                    />
                  </li>
                ))}
              </ul>
            )}
            {fases.length === 0 && (
              <p className="text-body-md text-on-surface-variant">
                Aún no hay fases. Añade la primera abajo.
              </p>
            )}

            <div className="mt-space-lg rounded-lg border border-dashed border-outline-variant bg-surface-container-lowest p-space-md">
              <p className="text-label-md font-semibold text-on-surface-variant">Añadir fase</p>
              <div className="mt-space-sm grid gap-space-md sm:grid-cols-12">
                <div className="sm:col-span-2">
                  <Input
                    label="Orden"
                    type="number"
                    min="1"
                    inputMode="numeric"
                    value={faseTmp.orden}
                    onChange={(e) => setFaseTmp({ ...faseTmp, orden: Number(e.target.value) })}
                  />
                </div>
                <div className="sm:col-span-6">
                  <Input
                    label="Nombre de la fase *"
                    value={faseTmp.nombre}
                    onChange={(e) => {
                      setFaseTmp({ ...faseTmp, nombre: e.target.value })
                      setFaseError(null)
                    }}
                    error={faseError ?? undefined}
                  />
                </div>
                <div className="sm:col-span-4">
                  <Input
                    label="Horas"
                    type="number"
                    min="0"
                    inputMode="numeric"
                    value={faseTmp.horas}
                    onChange={(e) => setFaseTmp({ ...faseTmp, horas: e.target.value })}
                  />
                </div>
                <div className="sm:col-span-12">
                  <Textarea
                    label="Descripción"
                    rows={2}
                    hint="Qué se hace en esta fase (opcional)."
                    value={faseTmp.descripcion}
                    onChange={(e) => setFaseTmp({ ...faseTmp, descripcion: e.target.value })}
                  />
                </div>
                <div className="flex justify-end sm:col-span-12">
                  <Button type="button" variant="tonal" icon="add" onClick={addFase}>
                    Añadir fase
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {msg && (
            <p role="alert" className="mt-space-lg text-body-md text-on-error-container">
              {msg}
            </p>
          )}
          <div className="mt-space-lg flex justify-end">
            <Button type="submit" loading={createPlan.isPending} icon="save">
              Guardar plan
            </Button>
          </div>
        </form>
      </div>
    )
  }

  const proyecto = plan
  const accionesDelProyecto = proyecto.acciones

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Producción', 'Proyectos', 'Plan']}
        title={proyecto.plan.resumen}
        subtitle="Seguimiento técnico por fases, avances, evidencia y cancelación formal."
        code={`${proyecto.plan.horas_estimadas}h · ${proyecto.fases.length} fases`}
        actions={
          <div className="flex flex-wrap gap-space-sm">
            {proyecto.puede_registrar_avance && (
              <Button icon="trending_up" variant="tonal" onClick={() => setShowProgress(true)}>
                Registrar avance
              </Button>
            )}
            {accionesDelProyecto.includes('iniciar') && (
              <Button
                icon="play_arrow"
                loading={actions.iniciar.isPending}
                onClick={() => onAccion(actions.iniciar)}
              >
                Iniciar producción
              </Button>
            )}
            {accionesDelProyecto.includes('completar') && (
              <Button
                icon="check_circle"
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
        actions.pasarDespacho.error ||
        quitar.error) && (
        <p
          role="alert"
          className="mb-space-lg rounded-lg bg-error-container px-space-md py-space-sm text-body-md font-medium text-on-error-container"
        >
          {accionError ??
            phaseAction.error?.message ??
            actions.iniciar.error?.message ??
            actions.completar.error?.message ??
            actions.pasarDespacho.error?.message ??
            quitar.error?.message}
        </p>
      )}

      <FlujoProyecto estado={proyecto.estado_desarrollo} />

      <div className="mt-space-lg grid gap-space-xl lg:grid-cols-3">
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
              <dt className="text-label-md font-semibold tracking-wide text-on-surface-variant uppercase">
                Horas plan
              </dt>
              <dd className="text-title-lg text-on-surface">{proyecto.plan.horas_estimadas}h</dd>
            </div>
            <div>
              <dt className="text-label-md font-semibold tracking-wide text-on-surface-variant uppercase">
                Horas fases
              </dt>
              <dd className="text-title-lg text-on-surface">{proyecto.horas_totales_fases}h</dd>
            </div>
            <div>
              <dt className="text-label-md font-semibold tracking-wide text-on-surface-variant uppercase">
                Avances
              </dt>
              <dd className="text-title-lg text-on-surface">{proyecto.avances.length}</dd>
            </div>
          </dl>
        </Card>

        <Card className="p-space-xl">
          <div className="flex items-start justify-between gap-space-md">
            <SectionHeader
              icon="groups"
              title="Miembros asignados"
              description="Equipo del proyecto."
            />
            <Button
              size="sm"
              variant="tonal"
              icon="person_add"
              onClick={() => {
                setSeleccion(proyecto.miembros.map((m) => m.user_id))
                setShowMembers(true)
              }}
            >
              Asignar
            </Button>
          </div>
          {proyecto.miembros.length === 0 ? (
            <p className="text-body-md text-on-surface-variant">Sin miembros asignados aún.</p>
          ) : (
            <ul className="space-y-space-xs">
              {proyecto.miembros.map((m) => (
                <li
                  key={m.id}
                  className="flex items-center justify-between gap-space-sm rounded-lg px-space-sm py-1.5 hover:bg-surface-container-low"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-body-md text-on-surface">
                      {m.nombre_usuario}
                    </span>
                    <span className="block text-label-sm text-on-surface-variant">{m.rol_proyecto}</span>
                  </span>
                  <IconButton
                    icon="person_remove"
                    tone="danger"
                    label={`Quitar a ${m.nombre_usuario} del proyecto`}
                    onClick={() => quitar.mutate(m.id)}
                  />
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <section className="mt-space-2xl">
        <SectionHeader
          icon="list_alt"
          title="Fases"
          description={
            proyecto.puede_registrar_avance
              ? 'Estado y control de cada fase del plan.'
              : 'Estado de cada fase del plan. Se habilitan al iniciar la producción.'
          }
        />
        <div className="space-y-space-lg">
          {proyecto.fases.map((f) => (
            <Card key={f.id} className="flex flex-wrap items-center justify-between gap-space-md p-space-xl">
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
                <p className="mt-1 text-label-sm text-on-surface-variant">
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

      <section className="mt-space-2xl grid gap-space-xl lg:grid-cols-2">
        <div>
          <SectionHeader
            icon="history"
            title="Historial de avances"
            description="Registro cronológico del porcentaje de avance."
          />
          <div className="space-y-space-md">
            {proyecto.avances.map((a) => (
              <Card key={a.id} className="p-space-xl">
                <div className="flex items-center justify-between">
                  <span className="text-body-md font-semibold text-on-surface">{a.autor}</span>
                  <span className="text-body-md font-semibold text-secondary">{a.porcentaje}%</span>
                </div>
                <p className="mt-1 text-body-md text-on-surface-variant">{a.notas}</p>
                <p className="mt-1 text-label-sm text-on-surface-variant">{formatDateTime(a.fecha)}</p>
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
        <Card className="mt-space-2xl bg-error-container p-space-xl">
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

      <Modal open={showMembers} onClose={() => setShowMembers(false)} title="Asignar miembros">
        <p className="text-body-md text-on-surface-variant">
          Selecciona las personas que formarán parte del proyecto.
        </p>
        {catalogo.isLoading && (
          <p className="mt-space-md text-body-md text-on-surface-variant">Cargando equipo…</p>
        )}
        {catalogo.error && (
          <p role="alert" className="mt-space-md text-body-md text-on-error-container">
            {catalogo.error.message}
          </p>
        )}
        {catalogo.data && (
          <ul className="mt-space-md max-h-80 space-y-1 overflow-y-auto">
            {catalogo.data.map((u) => (
              <li key={u.id}>
                <Checkbox
                  label={u.nombre}
                  sublabel={DEPARTAMENTOS[u.departamento] ?? u.departamento}
                  checked={seleccion.includes(u.id)}
                  onChange={() =>
                    setSeleccion((prev) =>
                      prev.includes(u.id) ? prev.filter((x) => x !== u.id) : [...prev, u.id],
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
          <Button variant="secondary" onClick={() => setShowMembers(false)}>
            Cerrar
          </Button>
          <Button
            loading={asignar.isPending}
            icon="check"
            onClick={() => asignar.mutate(seleccion, { onSuccess: () => setShowMembers(false) })}
          >
            Guardar selección
          </Button>
        </div>
      </Modal>

      <p className="mt-space-xl text-body-md">
        <Link
          to="/desarrollo"
          className="inline-flex items-center gap-1 text-secondary hover:underline"
        >
          <Icon name="arrow_back" size="sm" />
          Volver a Producción
        </Link>
      </p>
    </div>
  )
}
