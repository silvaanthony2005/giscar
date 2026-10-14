import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useCreateProject,
  useCustomers,
  useProjects,
  useSendToDesarrollo,
} from '../../entities/project/api'
import { Button } from '../../atoms/Button'
import { Input } from '../../atoms/Input'
import { Select } from '../../atoms/Select'
import { Textarea } from '../../atoms/Textarea'
import { Modal } from '../../molecules/Modal'
import { EstadoBadge } from '../../molecules/EstadoBadge'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { formatMoney } from '../../shared/lib/format'

const empty = {
  customer_id: '',
  titulo: '',
  descripcion_detallada: '',
  monto_total: '',
  contacto_nombre: '',
  contacto_telefono: '',
}

export function ProyectosVentasPage() {
  const { data, isLoading, error } = useProjects()
  const { data: customers } = useCustomers()
  const create = useCreateProject()
  const send = useSendToDesarrollo()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(empty)
  const [msg, setMsg] = useState<string | null>(null)

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    create.mutate(
      {
        ...form,
        monto_total: Number(form.monto_total),
        contacto_telefono: form.contacto_telefono || null,
      },
      {
        onSuccess: () => {
          setOpen(false)
          setForm(empty)
        },
        onError: (err) => setMsg(err.message),
      },
    )
  }

  const onSend = (pid: string) => {
    send.mutate(pid, { onError: (err) => alert(err.message) })
  }

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Ventas', 'Proyectos']}
        title="Levantamiento de Requerimiento de Proyecto"
        subtitle="Gestione la admisión comercial, el levantamiento detallado y el cobro con traspaso automático a ingeniería."
        actions={<Button onClick={() => setOpen(true)}>Nuevo proyecto</Button>}
      />
      <DataTable
        rows={data ?? []}
        keyOf={(p) => p.id}
        empty="Aún no hay proyectos"
        onRowClick={(p) => navigate(`/ventas/proyectos/${p.id}`)}
        columns={[
          { header: 'Código', cell: (p) => <span className="font-medium">{p.codigo}</span> },
          { header: 'Título', cell: (p) => p.titulo },
          { header: 'Monto', cell: (p) => formatMoney(p.monto_total), className: 'text-right' },
          { header: 'Estado Ventas', cell: (p) => <EstadoBadge valor={p.estado_ventas} /> },
          {
            header: '',
            cell: (p) =>
              p.acciones.includes('pasar_desarrollo') ? (
                <Button
                  size="sm"
                  variant="tonal"
                  loading={send.isPending}
                  onClick={(e) => {
                    e.stopPropagation()
                    onSend(p.id)
                  }}
                >
                  Enviar a Desarrollo
                </Button>
              ) : null,
          },
        ]}
      />

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Nuevo proyecto (levantamiento)"
        width="max-w-2xl"
      >
        <form onSubmit={onSubmit} className="space-y-space-lg">
          <Select
            label="Cliente *"
            placeholder="Seleccione un cliente…"
            required
            value={form.customer_id}
            onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
            options={(customers ?? []).map((c) => ({ value: c.id, label: c.nombre }))}
          />
          <div className="grid grid-cols-1 gap-space-lg sm:grid-cols-2">
            <Input
              label="Título del proyecto *"
              value={form.titulo}
              onChange={(e) => setForm({ ...form, titulo: e.target.value })}
              required
            />
            <Input
              label="Monto total *"
              type="number"
              min="1"
              step="0.01"
              value={form.monto_total}
              onChange={(e) => setForm({ ...form, monto_total: e.target.value })}
              required
            />
          </div>
          <Textarea
            label="Levantamiento detallado *"
            hint="Mínimo 20 caracteres."
            rows={5}
            minLength={20}
            required
            value={form.descripcion_detallada}
            onChange={(e) => setForm({ ...form, descripcion_detallada: e.target.value })}
            placeholder="Detalle completo del producto/servicio que solicita el cliente…"
          />
          <div className="grid grid-cols-1 gap-space-lg sm:grid-cols-2">
            <Input
              label="Contacto (nombre) *"
              value={form.contacto_nombre}
              onChange={(e) => setForm({ ...form, contacto_nombre: e.target.value })}
              required
            />
            <Input
              label="Contacto (teléfono)"
              value={form.contacto_telefono}
              onChange={(e) => setForm({ ...form, contacto_telefono: e.target.value })}
            />
          </div>
          {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" loading={create.isPending} className="w-full">
            Guardar proyecto
          </Button>
        </form>
      </Modal>
    </div>
  )
}
