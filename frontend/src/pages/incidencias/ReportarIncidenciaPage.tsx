import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useAuthStore } from '../../entities/auth/store'
import { useCrearIncidencia, type Incidencia } from '../../entities/project/tecnologia-api'
import { Button } from '../../atoms/Button'
import { Card } from '../../atoms/Card'
import { Icon } from '../../atoms/Icon'
import { Input } from '../../atoms/Input'
import { Textarea } from '../../atoms/Textarea'
import { EstadoBadge, PrioridadBadge } from '../../molecules/EstadoBadge'
import { SectionHeader } from '../../molecules/SectionHeader'
import { PageHeader } from '../../templates/PageHeader'
import { DEPARTAMENTOS, PRIORIDADES, formatDateTime } from '../../shared/lib/format'

/** Guía de uso (no negocio): ayuda a elegir sin cambiar la cola. */
const DESCRIPCIONES: Record<string, string> = {
  baja: 'Fallo menor: aún hay forma de seguir trabajando.',
  media: 'Afecta el trabajo diario del puesto.',
  alta: 'Deja el puesto sin poder trabajar.',
  critica: 'Varios equipos o un área completa detenida.',
}

const PASOS = [
  {
    titulo: 'Llega a la Mesa de Ayuda',
    texto: 'Se registra con la hora en que la envía y entra a la cola de Tecnología.',
  },
  {
    titulo: 'Se atiende por llegada y prioridad',
    texto: 'La cola se ordena por orden de llegada y por la prioridad indicada aquí.',
  },
  {
    titulo: 'Se cierra con reporte',
    texto: 'Tecnología resuelve y deja diagnóstico, solución y evidencia.',
  },
]

const empty = { titulo: '', descripcion: '', equipo_afectado: '', prioridad: 'media' }

/**
 * Alta de incidencias desde cualquier departamento: solo envían el reporte.
 * Ver la cola, asignar y resolver es de Tecnología (lo exige el backend).
 */
export function ReportarIncidenciaPage() {
  const user = useAuthStore((s) => s.user)
  const crear = useCrearIncidencia()
  const [form, setForm] = useState(empty)
  const [msg, setMsg] = useState<string | null>(null)
  const [enviada, setEnviada] = useState<Incidencia | null>(null)
  const confirmacionRef = useRef<HTMLDivElement>(null)

  // El foco pasa a la confirmación: teclado y lector de pantalla se enteran
  // de que el envío terminó, aunque el cambio ocurra fuera del foco.
  useEffect(() => {
    if (enviada) confirmacionRef.current?.focus()
  }, [enviada])

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    crear.mutate(form, {
      onSuccess: (inc) => {
        setEnviada(inc)
        setForm(empty)
      },
      onError: (err) => setMsg(err.message),
    })
  }

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={[DEPARTAMENTOS[user?.departamento ?? ''] ?? '', 'Reportar incidencia']}
        title="Reportar incidencia"
        subtitle="Describa el fallo de hardware o electrónica: sale directo a la Mesa de Ayuda de Tecnología."
      />

      <div className="grid gap-space-xl lg:grid-cols-12">
        {/* ------------------------------------------------ formulario */}
        <div className="lg:col-span-7">
          {enviada ? (
            <Card className="overflow-hidden">
              <div
                ref={confirmacionRef}
                role="status"
                tabIndex={-1}
                className="outline-none"
              >
                <div className="flex items-center gap-space-md bg-success-container px-space-xl py-space-lg text-on-success-container">
                  <Icon name="check_circle" size="lg" />
                  <div className="min-w-0">
                    <h2 className="text-title-lg font-bold">
                      Incidencia {enviada.codigo} enviada
                    </h2>
                    <p className="text-body-sm">
                      La Mesa de Ayuda ya la recibió y quedó en cola.
                    </p>
                  </div>
                </div>

                <dl className="grid gap-space-lg p-space-xl sm:grid-cols-2">
                  <div>
                    <dt className="text-label-sm uppercase tracking-wider text-on-surface-variant">
                      Título
                    </dt>
                    <dd className="text-body-md text-on-surface">{enviada.titulo}</dd>
                  </div>
                  <div>
                    <dt className="text-label-sm uppercase tracking-wider text-on-surface-variant">
                      Equipo afectado
                    </dt>
                    <dd className="text-body-md text-on-surface">{enviada.equipo_afectado}</dd>
                  </div>
                  <div>
                    <dt className="text-label-sm uppercase tracking-wider text-on-surface-variant">
                      Prioridad
                    </dt>
                    <dd className="mt-1">
                      <PrioridadBadge valor={enviada.prioridad} />
                    </dd>
                  </div>
                  <div>
                    <dt className="text-label-sm uppercase tracking-wider text-on-surface-variant">
                      Estado
                    </dt>
                    <dd className="mt-1">
                      <EstadoBadge valor={enviada.estado} />
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-label-sm uppercase tracking-wider text-on-surface-variant">
                      Enviada
                    </dt>
                    <dd className="text-body-md text-on-surface">
                      {formatDateTime(enviada.created_at)}
                    </dd>
                  </div>
                </dl>

                <div className="flex flex-wrap items-center justify-between gap-space-md border-t border-outline-variant/60 px-space-xl py-space-md">
                  <p className="text-body-sm text-on-surface-variant">
                    Atiende Tecnología; desde aquí solo se envía el reporte.
                  </p>
                  <Button variant="secondary" icon="add" onClick={() => setEnviada(null)}>
                    Reportar otra incidencia
                  </Button>
                </div>
              </div>
            </Card>
          ) : (
            <Card>
              <form onSubmit={onSubmit} className="flex flex-col gap-space-xl p-space-xl">
                <SectionHeader
                  icon="edit_note"
                  title="Datos de la incidencia"
                  description="Los cuatro datos son obligatorios."
                  chip="Obligatorio"
                />

                <Input
                  label="Título *"
                  icon="title"
                  value={form.titulo}
                  onChange={(e) => setForm({ ...form, titulo: e.target.value })}
                  placeholder="Ej: Impresora no responde"
                  required
                />
                <Input
                  label="Equipo afectado *"
                  icon="devices"
                  value={form.equipo_afectado}
                  onChange={(e) => setForm({ ...form, equipo_afectado: e.target.value })}
                  placeholder="Ej: PC-03, impresora, monitor…"
                  required
                />
                <Textarea
                  label="Descripción *"
                  hint="Mínimo 15 caracteres: qué falla, desde cuándo y qué se ve."
                  required
                  minLength={15}
                  rows={4}
                  value={form.descripcion}
                  onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
                  placeholder="Describe el fallo observado…"
                />

                <fieldset aria-describedby="prioridad-ayuda">
                  <legend className="text-title-md text-on-surface">Prioridad *</legend>
                  <p id="prioridad-ayuda" className="mt-1 text-label-sm text-on-surface-variant">
                    La cola se atiende por orden de llegada y prioridad.
                  </p>
                  <div className="mt-space-sm grid gap-space-sm sm:grid-cols-2">
                    {Object.entries(PRIORIDADES).map(([valor, etiqueta]) => (
                      <label
                        key={valor}
                        className="flex cursor-pointer items-start gap-space-sm rounded-xl border border-outline-variant/70 bg-surface-container-lowest p-space-md shadow-hairline transition duration-150 hover:border-secondary has-[:checked]:border-secondary has-[:checked]:bg-surface-container has-[:checked]:shadow-raised has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-secondary has-[:focus-visible]:ring-offset-2 has-[:focus-visible]:ring-offset-surface"
                      >
                        <input
                          type="radio"
                          name="prioridad"
                          value={valor}
                          required
                          checked={form.prioridad === valor}
                          onChange={(e) => setForm({ ...form, prioridad: e.target.value })}
                          className="mt-0.5 size-4 shrink-0 accent-secondary"
                        />
                        <span className="flex min-w-0 flex-col">
                          <span className="text-title-md text-on-surface">{etiqueta}</span>
                          <span className="text-body-sm text-on-surface-variant">
                            {DESCRIPCIONES[valor]}
                          </span>
                        </span>
                      </label>
                    ))}
                  </div>
                </fieldset>

                {msg && (
                  <div
                    role="alert"
                    className="flex items-start gap-space-sm rounded-xl border border-error/40 bg-error-container px-space-md py-space-sm text-body-md text-on-error-container"
                  >
                    <Icon name="error" size="sm" className="mt-0.5 shrink-0" />
                    <span>{msg}</span>
                  </div>
                )}

                <div className="flex flex-col gap-space-sm">
                  <Button type="submit" size="lg" loading={crear.isPending} icon="send" className="w-full">
                    Enviar a Tecnología
                  </Button>
                  <p className="text-center text-label-sm text-on-surface-variant">
                    Asignar, atender y cerrar la incidencia lo hace Tecnología.
                  </p>
                </div>
              </form>
            </Card>
          )}
        </div>

        {/* ------------------------------------------------ cómo se atiende */}
        <aside aria-labelledby="pasos-titulo" className="lg:col-span-5">
          <Card className="overflow-hidden bg-surface-container">
            {/* Cinta de taller: identidad visual del módulo de ayuda. */}
            <div
              aria-hidden="true"
              className="h-2 bg-[repeating-linear-gradient(135deg,var(--color-secondary)_0_6px,var(--color-secondary-container)_6px_12px)]"
            />
            <div className="p-space-xl">
              <h2 id="pasos-titulo" className="text-title-lg font-bold text-on-surface">
                Cómo se atiende
              </h2>
              <p className="mt-1 text-body-sm text-on-surface-variant">
                Esta incidencia entra a la cola de la Mesa de Ayuda.
              </p>

              <ol className="mt-space-lg space-y-space-lg">
                {PASOS.map((paso, i) => (
                  <li key={paso.titulo} className="flex gap-space-md">
                    {/* El <ol> ya numera para el lector: el círculo es decorativo. */}
                    <span
                      aria-hidden="true"
                      className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-body-md font-bold text-on-primary"
                    >
                      {i + 1}
                    </span>
                    <div className="min-w-0">
                      <p className="text-title-md text-on-surface">{paso.titulo}</p>
                      <p className="text-body-sm text-on-surface-variant">{paso.texto}</p>
                    </div>
                  </li>
                ))}
              </ol>

              <p className="mt-space-lg flex items-start gap-space-sm border-t border-outline-variant/60 pt-space-md text-body-sm text-on-surface-variant">
                <Icon name="info" size="sm" className="mt-0.5 shrink-0 text-secondary" />
                <span>
                  Desde tu módulo solo se envía el reporte; la cola completa vive en la Mesa de
                  Ayuda de Tecnología.
                </span>
              </p>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  )
}
