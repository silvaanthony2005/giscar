import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  useDespachoProyecto,
  useEntregar,
  useLiquidar,
  useNegar,
  useResolverNegacion,
} from '../../entities/project/despacho-api'
import { Button } from '../../atoms/Button'
import { Card } from '../../atoms/Card'
import { Icon } from '../../atoms/Icon'
import { Input } from '../../atoms/Input'
import { Select } from '../../atoms/Select'
import { Textarea } from '../../atoms/Textarea'
import { EstadoBadge } from '../../molecules/EstadoBadge'
import { Modal } from '../../molecules/Modal'
import { SectionHeader } from '../../molecules/SectionHeader'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { formatDateTime, formatMoney } from '../../shared/lib/format'

const METODOS = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
  { value: 'tarjeta', label: 'Tarjeta' },
  { value: 'cheque', label: 'Cheque' },
]

const dt = 'text-label-md font-semibold tracking-wide text-on-surface-variant uppercase'

export function DetalleDespachoPage() {
  const { id = '' } = useParams()
  const { data: p, isLoading, error } = useDespachoProyecto(id)
  const liquidar = useLiquidar(id)
  const entregar = useEntregar(id)
  const negar = useNegar(id)
  const resolver = useResolverNegacion(id)

  const [showLiq, setShowLiq] = useState(false)
  const [metodo, setMetodo] = useState('transferencia')
  const [notas, setNotas] = useState('')

  const [showEntrega, setShowEntrega] = useState(false)
  const [entrega, setEntrega] = useState(() => ({
    fecha_entrega: new Date().toISOString().slice(0, 10),
    hora_entrega: '',
    destinatario: '',
    detalle_entregado: '',
    notas: '',
  }))

  const [showNegar, setShowNegar] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [detalleNeg, setDetalleNeg] = useState('')
  const [msg, setMsg] = useState<string | null>(null)

  if (isLoading) return <LoadingState />
  if (error || !p) return <ErrorState message={error?.message ?? 'Proyecto no encontrado'} />

  const onLiquidar = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    liquidar.mutate(
      { metodo_pago: metodo, notas: notas || null },
      { onSuccess: () => setShowLiq(false), onError: (err) => setMsg(err.message) },
    )
  }

  const onEntregar = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    entregar.mutate(
      {
        ...entrega,
        hora_entrega: entrega.hora_entrega || null,
        notas: entrega.notas || null,
      },
      { onSuccess: () => setShowEntrega(false), onError: (err) => setMsg(err.message) },
    )
  }

  const onNegar = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    negar.mutate(
      { motivo, detalle: detalleNeg },
      { onSuccess: () => setShowNegar(false), onError: (err) => setMsg(err.message) },
    )
  }

  const nombreCliente =
    typeof p.cliente === 'object' && p.cliente !== null
      ? (p.cliente as { nombre?: string }).nombre
      : undefined

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Despacho', 'Proyectos', p.codigo]}
        title={p.titulo}
        subtitle="Contacto con el cliente, cobro del saldo y acta de entrega."
        code={p.codigo}
        actions={
          <div className="flex flex-wrap gap-space-sm">
            {p.acciones.includes('liquidar') && (
              <Button icon="payments" variant="tonal" onClick={() => setShowLiq(true)}>
                Liquidar saldo ({formatMoney(p.saldo)})
              </Button>
            )}
            {p.acciones.includes('confirmar_entrega') && (
              <Button icon="local_shipping" loading={entregar.isPending} onClick={() => setShowEntrega(true)}>
                Confirmar entrega
              </Button>
            )}
            {p.acciones.includes('negar') && (
              <Button icon="block" variant="danger" onClick={() => setShowNegar(true)}>
                Negar
              </Button>
            )}
            {p.acciones.includes('resolver_negacion') && (
              <Button icon="check_circle" loading={resolver.isPending} onClick={() => resolver.mutate()}>
                Resolver negación
              </Button>
            )}
          </div>
        }
      />
      <div className="mb-space-lg flex flex-wrap gap-space-xs">
        <EstadoBadge valor={p.estado_desarrollo} />
        <EstadoBadge valor={p.estado_despacho} />
      </div>

      <div className="grid gap-space-lg lg:grid-cols-3">
        <Card className="p-space-xl">
          <SectionHeader
            icon="account_balance_wallet"
            title="Cobro"
            description="Cifras calculadas por el servidor."
          />
          <dl className="space-y-space-sm text-body-md">
            <div className="flex justify-between">
              <dt className="text-on-surface-variant">Total</dt>
              <dd className="font-medium text-on-surface">{formatMoney(p.monto_total)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-on-surface-variant">Pagado</dt>
              <dd className="font-medium text-secondary">{formatMoney(p.pagado)}</dd>
            </div>
            <div className="flex justify-between border-t border-outline-variant/60 pt-space-sm">
              <dt className="text-on-surface-variant">Saldo</dt>
              <dd className="font-semibold text-on-surface">{formatMoney(p.saldo)}</dd>
            </div>
          </dl>
          {p.acciones.includes('liquidar') && (
            <p className="mt-space-md text-label-sm text-primary">
              El servidor habilitó la liquidación: registre el cobro restante antes de entregar.
            </p>
          )}
        </Card>

        <Card className="p-space-xl lg:col-span-2">
          <SectionHeader
            icon="assignment_turned_in"
            title="Entrega"
            description={`Cliente: ${nombreCliente ?? p.cliente ?? '—'}`}
            chip={p.entrega ? 'Registrada' : 'Pendiente'}
          />
          {p.entrega ? (
            <dl className="grid grid-cols-1 gap-space-md text-body-md sm:grid-cols-2">
              <div>
                <dt className={dt}>Fecha</dt>
                <dd className="text-on-surface">{p.entrega.fecha_entrega}</dd>
              </div>
              <div>
                <dt className={dt}>Hora</dt>
                <dd className="text-on-surface">{p.entrega.hora_entrega ?? '—'}</dd>
              </div>
              <div>
                <dt className={dt}>Destinatario</dt>
                <dd className="text-on-surface">{p.entrega.destinatario}</dd>
              </div>
              <div>
                <dt className={dt}>Detalle</dt>
                <dd className="text-on-surface">{p.entrega.detalle_entregado}</dd>
              </div>
              {p.entrega.notas && (
                <div className="sm:col-span-2">
                  <dt className={dt}>Notas</dt>
                  <dd className="text-on-surface">{p.entrega.notas}</dd>
                </div>
              )}
            </dl>
          ) : (
            <p className="text-body-md text-on-surface-variant">Sin entrega registrada.</p>
          )}
        </Card>
      </div>

      <Card className="mt-space-lg p-space-xl">
        <SectionHeader
          icon="contact_phone"
          title="Contacto del cliente"
          description="Datos capturados en el levantamiento; úselos para coordinar cobro y entrega."
        />
        <dl className="grid grid-cols-1 gap-space-md text-body-md sm:grid-cols-2">
          <div>
            <dt className={dt}>Contacto</dt>
            <dd className="text-on-surface">{p.contacto_nombre}</dd>
          </div>
          <div>
            <dt className={dt}>Teléfono</dt>
            <dd className="text-on-surface">{p.contacto_telefono ?? '—'}</dd>
          </div>
          <div>
            <dt className={dt}>Correo</dt>
            <dd className="text-on-surface">{p.contacto_email ?? '—'}</dd>
          </div>
          <div>
            <dt className={dt}>Dirección</dt>
            <dd className="text-on-surface">{p.contacto_direccion ?? '—'}</dd>
          </div>
        </dl>
      </Card>

      {p.negacion && (
        <Card className="mt-space-lg bg-error-container p-space-xl">
          <h2 className="text-title-lg font-bold text-on-error-container">
            Negación registrada
          </h2>
          <p className="mt-space-xs text-body-md text-on-error-container">
            <strong>Motivo:</strong> {p.negacion.motivo}
          </p>
          <p className="mt-space-sm text-body-md text-on-error-container">{p.negacion.detalle}</p>
          <p className="mt-space-sm text-label-sm text-on-error-container">
            {formatDateTime(p.negacion.fecha)}
          </p>
        </Card>
      )}

      <section className="mt-space-xl">
        <SectionHeader
          icon="receipt_long"
          title="Historial de pagos"
          description="Cobros de anticipos y liquidación."
        />
        <div className="space-y-space-md">
          {p.pagos.map((pg) => (
            <Card key={pg.id} className="flex items-center justify-between gap-space-md p-space-lg">
              <div className="min-w-0">
                <span className="text-body-md font-semibold text-on-surface">
                  {formatMoney(pg.monto)}
                </span>
                <span className="ml-space-sm text-body-md text-on-surface-variant">
                  · {pg.tipo} · {pg.metodo_pago}
                </span>
              </div>
              <div className="shrink-0 text-right">
                <span className="text-body-md text-on-surface">{pg.porcentaje}%</span>
                <p className="text-label-sm text-on-surface-variant">{formatDateTime(pg.fecha)}</p>
              </div>
            </Card>
          ))}
          {p.pagos.length === 0 && (
            <p className="text-body-md text-on-surface-variant">Sin pagos.</p>
          )}
        </div>
      </section>

      <Modal
        open={showLiq}
        onClose={() => setShowLiq(false)}
        title="Liquidar saldo pendiente"
      >
        <form onSubmit={onLiquidar} className="space-y-space-lg">
          <p className="text-body-md text-on-surface-variant">
            Se registrará un pago por el saldo restante de{' '}
            <strong className="text-on-surface">{formatMoney(p.saldo)}</strong>.
          </p>
          <Select
            label="Método de pago"
            value={metodo}
            onChange={(e) => setMetodo(e.target.value)}
            options={METODOS}
          />
          <Input label="Notas" value={notas} onChange={(e) => setNotas(e.target.value)} />
          {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" loading={liquidar.isPending} className="w-full">
            Confirmar liquidación
          </Button>
        </form>
      </Modal>

      <Modal
        open={showEntrega}
        onClose={() => setShowEntrega(false)}
        title="Confirmar entrega"
        width="max-w-2xl"
      >
        <form onSubmit={onEntregar} className="space-y-space-lg">
          <div className="grid grid-cols-1 gap-space-lg sm:grid-cols-2">
            <Input
              label="Fecha de entrega *"
              type="date"
              value={entrega.fecha_entrega}
              onChange={(e) => setEntrega({ ...entrega, fecha_entrega: e.target.value })}
              required
            />
            <Input
              label="Hora"
              type="time"
              value={entrega.hora_entrega}
              onChange={(e) => setEntrega({ ...entrega, hora_entrega: e.target.value })}
            />
            <Input
              label="Destinatario *"
              value={entrega.destinatario}
              onChange={(e) => setEntrega({ ...entrega, destinatario: e.target.value })}
              required
            />
            <div className="sm:col-span-2">
              <Textarea
                label="Detalle de lo entregado *"
                required
                rows={3}
                value={entrega.detalle_entregado}
                onChange={(e) => setEntrega({ ...entrega, detalle_entregado: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              <Textarea
                label="Notas"
                rows={2}
                value={entrega.notas}
                onChange={(e) => setEntrega({ ...entrega, notas: e.target.value })}
              />
            </div>
          </div>
          {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" loading={entregar.isPending} className="w-full">
            Confirmar entrega
          </Button>
        </form>
      </Modal>

      <Modal open={showNegar} onClose={() => setShowNegar(false)} title="Negar proyecto">
        <form onSubmit={onNegar} className="space-y-space-lg">
          <Input
            label="Motivo *"
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            required
          />
          <Textarea
            label="Detalle *"
            hint="Mínimo 15 caracteres."
            required
            minLength={15}
            rows={4}
            value={detalleNeg}
            onChange={(e) => setDetalleNeg(e.target.value)}
          />
          {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" variant="danger" loading={negar.isPending} className="w-full">
            Confirmar negación
          </Button>
        </form>
      </Modal>

      <p className="mt-space-xl text-body-md">
        <Link
          to="/despacho"
          className="inline-flex items-center gap-1 text-secondary hover:underline"
        >
          <Icon name="arrow_back" size="sm" />
          Volver a Despacho
        </Link>
      </p>
    </div>
  )
}
