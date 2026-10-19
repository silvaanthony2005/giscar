import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  invoicePdfUrl,
  useCreatePayment,
  useInvoices,
  usePayments,
  useProject,
  useSendToDesarrollo,
} from '../../entities/project/api'
import { Button } from '../../atoms/Button'
import { Card } from '../../atoms/Card'
import { Icon } from '../../atoms/Icon'
import { Input } from '../../atoms/Input'
import { Select } from '../../atoms/Select'
import { EstadoBadge } from '../../molecules/EstadoBadge'
import { SectionHeader } from '../../molecules/SectionHeader'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { descargar } from '../../shared/api/client'
import { formatDateTime, formatMoney } from '../../shared/lib/format'

const METODOS = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
  { value: 'tarjeta', label: 'Tarjeta' },
  { value: 'cheque', label: 'Cheque' },
]

export function DetalleProyectoVentasPage() {
  const { id = '' } = useParams()
  const { data: project, isLoading, error } = useProject(id)
  const { data: pagos } = usePayments(id)
  const { data: facturas } = useInvoices(id)
  const createPayment = useCreatePayment(id)
  const send = useSendToDesarrollo()
  const [monto, setMonto] = useState('')
  const [metodo, setMetodo] = useState('efectivo')
  const [msg, setMsg] = useState<string | null>(null)
  const [errPdf, setErrPdf] = useState<string | null>(null)

  if (isLoading) return <LoadingState />
  if (error || !project)
    return <ErrorState message={error?.message ?? 'Proyecto no encontrado'} />

  // El backend entrega pagado/saldo ya calculados (AGENTS.md: sin lógica aquí).
  const pagado = project.pagado
  const saldo = project.saldo

  const onPay = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    createPayment.mutate(
      { monto: Number(monto), metodo_pago: metodo },
      {
        onSuccess: () => setMonto(''),
        onError: (err) => setMsg(err.message),
      },
    )
  }

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Ventas', 'Proyectos', project.codigo]}
        title={project.titulo}
        subtitle="Levantamiento comercial, control de cobro y emisión de facturas."
        code={project.codigo}
        actions={
          project.acciones.includes('pasar_desarrollo') ? (
            <Button
              icon="send"
              loading={send.isPending}
              onClick={() => send.mutate(id, { onError: (e) => alert(e.message) })}
            >
              Enviar a Desarrollo
            </Button>
          ) : null
        }
      />
      <div className="mb-space-lg flex flex-wrap gap-space-xs">
        <EstadoBadge valor={project.estado_ventas} />
        <EstadoBadge valor={project.estado_desarrollo} />
        <EstadoBadge valor={project.estado_despacho} />
      </div>

      <div className="grid gap-space-lg lg:grid-cols-3">
        <Card className="p-space-xl lg:col-span-2">
          <SectionHeader
            icon="description"
            title="Levantamiento"
            description="Especificación capturada por Ventas al momento de la admisión comercial."
            chip="Obligatorio"
          />
          <p className="whitespace-pre-wrap text-body-md text-on-surface">
            {project.descripcion_detallada}
          </p>
          <dl className="mt-space-lg grid grid-cols-1 gap-space-md sm:grid-cols-2">
            <div>
              <dt className="text-label-md font-semibold tracking-wide text-outline uppercase">
                Contacto
              </dt>
              <dd className="text-body-md text-on-surface">{project.contacto_nombre}</dd>
            </div>
            <div>
              <dt className="text-label-md font-semibold tracking-wide text-outline uppercase">
                Teléfono
              </dt>
              <dd className="text-body-md text-on-surface">
                {project.contacto_telefono ?? '—'}
              </dd>
            </div>
          </dl>
        </Card>

        <Card className="p-space-xl">
          <SectionHeader
            icon="payments"
            title="Resumen de cobro"
            description="Cifras calculadas por el servidor."
          />
          <dl className="space-y-space-sm text-body-md">
            <div className="flex justify-between">
              <dt className="text-on-surface-variant">Total</dt>
              <dd className="font-medium text-on-surface">{formatMoney(project.monto_total)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-on-surface-variant">Pagado</dt>
              <dd className="font-medium text-secondary">{formatMoney(pagado)}</dd>
            </div>
            <div className="flex justify-between border-t border-outline-variant/60 pt-space-sm">
              <dt className="text-on-surface-variant">Saldo</dt>
              <dd className="font-semibold text-on-surface">{formatMoney(saldo)}</dd>
            </div>
          </dl>

          {project.acciones.includes('registrar_pago') && (
            <form onSubmit={onPay} className="mt-space-lg space-y-space-md border-t border-outline-variant/60 pt-space-lg">
              <Input
                label="Monto a cobrar"
                type="number"
                min="1"
                step="0.01"
                value={monto}
                onChange={(e) => setMonto(e.target.value)}
                required
              />
              <Select
                label="Método de pago"
                value={metodo}
                onChange={(e) => setMetodo(e.target.value)}
                options={METODOS}
              />
              {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
              <Button type="submit" loading={createPayment.isPending} className="w-full">
                Registrar cobro
              </Button>
            </form>
          )}
        </Card>
      </div>

      <div className="mt-space-lg grid gap-space-lg lg:grid-cols-2">
        <div>
          <h2 className="mb-space-md text-title-lg font-bold text-on-surface">
            Historial de pagos
          </h2>
          <DataTable
            rows={pagos ?? []}
            keyOf={(p) => p.id}
            empty="Sin pagos registrados"
            columns={[
              { header: 'Fecha', cell: (p) => formatDateTime(p.fecha) },
              { header: 'Monto', cell: (p) => formatMoney(p.monto), className: 'text-right' },
              { header: '%', cell: (p) => `${p.porcentaje}%` },
              { header: 'Método', cell: (p) => p.metodo_pago },
            ]}
          />
        </div>
        <div>
          <h2 className="mb-space-md text-title-lg font-bold text-on-surface">
            Facturas emitidas
          </h2>
          <DataTable
            rows={facturas ?? []}
            keyOf={(f) => f.id}
            empty="Sin facturas emitidas"
            columns={[
              { header: 'Número', cell: (f) => <span className="font-medium">{f.numero}</span> },
              { header: 'Monto', cell: (f) => formatMoney(f.monto), className: 'text-right' },
              {
                header: '',
                cell: (f) => (
                  <button
                    type="button"
                    onClick={() =>
                      descargar(invoicePdfUrl(f.id)).catch((e: Error) => setErrPdf(e.message))
                    }
                    className="inline-flex items-center gap-1 text-secondary hover:underline"
                  >
                    <Icon name="download" size="sm" />
                    PDF
                  </button>
                ),
              },
            ]}
          />
          {errPdf && (
            <p role="alert" className="mt-space-sm text-body-md text-on-error-container">
              {errPdf}
            </p>
          )}
        </div>
      </div>

      <p className="mt-space-xl text-body-md">
        <Link to="/ventas" className="inline-flex items-center gap-1 text-secondary hover:underline">
          <Icon name="arrow_back" size="sm" />
          Volver a Ventas
        </Link>
      </p>
    </div>
  )
}
