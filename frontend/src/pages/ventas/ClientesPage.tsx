import { useState, type FormEvent } from 'react'
import {
  useCreateCustomer,
  useCustomers,
  useDeleteCustomer,
  useUpdateCustomer,
  type Customer,
} from '../../entities/project/api'
import { Button } from '../../atoms/Button'
import { Input } from '../../atoms/Input'
import { Modal } from '../../molecules/Modal'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { formatDateTime } from '../../shared/lib/format'

const empty = {
  nombre: '',
  representante: '',
  documento: '',
  telefono: '',
  email: '',
  direccion: '',
}

type Form = typeof empty

const alFormulario = (c: Customer): Form => ({
  nombre: c.nombre,
  representante: c.representante ?? '',
  documento: c.documento ?? '',
  telefono: c.telefono ?? '',
  email: c.email ?? '',
  direccion: c.direccion ?? '',
})

const dt = 'text-label-md font-semibold tracking-wide text-on-surface-variant uppercase'

export function ClientesPage() {
  const { data, isLoading, error } = useCustomers()
  const create = useCreateCustomer()
  const update = useUpdateCustomer()
  const remove = useDeleteCustomer()

  const [abierto, setAbierto] = useState(false)
  const [editando, setEditando] = useState<Customer | null>(null)
  const [viendo, setViendo] = useState<Customer | null>(null)
  const [porBorrar, setPorBorrar] = useState<Customer | null>(null)
  const [form, setForm] = useState<Form>(empty)
  const [msg, setMsg] = useState<string | null>(null)

  const abrirAlta = () => {
    setForm(empty)
    setEditando(null)
    setMsg(null)
    setAbierto(true)
  }

  const abrirEdicion = (c: Customer) => {
    setForm(alFormulario(c))
    setEditando(c)
    setMsg(null)
    setViendo(null)
    setAbierto(true)
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    const cerrar = () => setAbierto(false)
    const onError = (err: Error) => setMsg(err.message)
    if (editando) {
      // El backend recibe el registro completo: cadena vacía = borrar el dato.
      update.mutate({ id: editando.id, body: form }, { onSuccess: cerrar, onError })
    } else {
      create.mutate({ ...form, email: form.email || null }, { onSuccess: cerrar, onError })
    }
  }

  const onBorrar = () => {
    if (!porBorrar) return
    setMsg(null)
    remove.mutate(porBorrar.id, {
      onSuccess: () => setPorBorrar(null),
      onError: (err) => setMsg(err.message),
    })
  }

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  const datos: [string, string | null | undefined][] = [
    ['Representante', viendo?.representante],
    ['Documento', viendo?.documento],
    ['Teléfono', viendo?.telefono],
    ['Correo', viendo?.email],
    ['Dirección', viendo?.direccion],
  ]

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Ventas', 'Clientes']}
        title="Clientes"
        subtitle="Datos levantados por Ventas"
        actions={<Button icon="person_add" onClick={abrirAlta}>Nuevo cliente</Button>}
      />
      <DataTable
        rows={data ?? []}
        keyOf={(c) => c.id}
        empty="Aún no hay clientes registrados"
        columns={[
          { header: 'Empresa', cell: (c) => <span className="font-medium">{c.nombre}</span> },
          { header: 'Representante', cell: (c) => c.representante ?? '—' },
          { header: 'Documento', cell: (c) => c.documento ?? '—' },
          { header: 'Teléfono', cell: (c) => c.telefono ?? '—' },
          { header: 'Correo', cell: (c) => c.email ?? '—' },
          { header: 'Dirección', cell: (c) => c.direccion ?? '—' },
          {
            header: '',
            className: 'text-right',
            cell: (c) => (
              <div className="flex justify-end gap-space-xs">
                <Button size="sm" variant="ghost" icon="visibility" onClick={() => setViendo(c)}>
                  Ver
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  icon="delete"
                  onClick={() => {
                    setMsg(null)
                    setPorBorrar(c)
                  }}
                >
                  Eliminar
                </Button>
              </div>
            ),
          },
        ]}
      />

      <Modal open={viendo !== null} onClose={() => setViendo(null)} title={viendo?.nombre ?? 'Cliente'}>
        <dl className="space-y-space-md text-body-md">
          {datos.map(([etiqueta, valor]) => (
            <div key={etiqueta}>
              <dt className={dt}>{etiqueta}</dt>
              <dd className="text-on-surface">{valor || '—'}</dd>
            </div>
          ))}
          <div>
            <dt className={dt}>Registrado</dt>
            <dd className="text-on-surface">{viendo ? formatDateTime(viendo.created_at) : '—'}</dd>
          </div>
        </dl>
        <div className="mt-space-xl flex justify-end gap-space-sm">
          <Button variant="secondary" onClick={() => setViendo(null)}>
            Cerrar
          </Button>
          {viendo && (
            <Button icon="edit" onClick={() => abrirEdicion(viendo)}>
              Editar
            </Button>
          )}
        </div>
      </Modal>

      <Modal
        open={abierto}
        onClose={() => setAbierto(false)}
        title={editando ? `Editar cliente: ${editando.nombre}` : 'Nuevo cliente'}
      >
        <form onSubmit={onSubmit} className="space-y-space-lg">
          <Input icon="business" label="Nombre de la empresa *" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
          <Input icon="person" label="Nombre del cliente (representante) *" value={form.representante} onChange={(e) => setForm({ ...form, representante: e.target.value })} required />
          <Input icon="badge" label="Documento (RIF o cédula) *" value={form.documento} onChange={(e) => setForm({ ...form, documento: e.target.value })} required />
          <Input
            icon="call"
            label="Número telefónico *"
            type="tel"
            inputMode="numeric"
            value={form.telefono}
            onChange={(e) => setForm({ ...form, telefono: e.target.value.replace(/\D/g, '') })}
            required
          />
          <Input icon="alternate_email" label="Correo" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input icon="location_on" label="Dirección *" value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} required />
          {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" icon="save" loading={create.isPending || update.isPending} className="w-full">
            {editando ? 'Guardar cambios' : 'Guardar cliente'}
          </Button>
        </form>
      </Modal>

      <Modal open={porBorrar !== null} onClose={() => setPorBorrar(null)} title="Eliminar cliente">
        <p className="text-body-md text-on-surface">
          Se eliminará <strong>{porBorrar?.nombre}</strong> del registro de clientes. Esta acción no
          se puede deshacer.
        </p>
        <p className="mt-space-sm text-body-md text-on-surface-variant">
          Si el cliente tiene proyectos registrados, el servidor no permitirá el borrado.
        </p>
        {msg && <p className="mt-space-md text-body-md text-on-error-container">{msg}</p>}
        <div className="mt-space-xl flex gap-space-sm">
          <Button variant="secondary" icon="cancel" className="flex-1" onClick={() => setPorBorrar(null)}>
            Cancelar
          </Button>
          <Button variant="danger" className="flex-1" loading={remove.isPending} onClick={onBorrar}>
            Eliminar
          </Button>
        </div>
      </Modal>
    </div>
  )
}
