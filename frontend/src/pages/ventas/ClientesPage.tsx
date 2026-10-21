import { useState, type FormEvent } from 'react'
import { useCustomers, useCreateCustomer } from '../../entities/project/api'
import { Button } from '../../atoms/Button'
import { Input } from '../../atoms/Input'
import { Modal } from '../../molecules/Modal'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'

const empty = {
  nombre: '',
  representante: '',
  documento: '',
  telefono: '',
  email: '',
  direccion: '',
}

export function ClientesPage() {
  const { data, isLoading, error } = useCustomers()
  const create = useCreateCustomer()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(empty)
  const [msg, setMsg] = useState<string | null>(null)

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    create.mutate(
      { ...form, email: form.email || null },
      {
        onSuccess: () => {
          setOpen(false)
          setForm(empty)
        },
        onError: (err) => setMsg(err.message),
      },
    )
  }

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Ventas', 'Clientes']}
        title="Clientes"
        subtitle="Datos levantados por Ventas"
        actions={<Button onClick={() => setOpen(true)}>Nuevo cliente</Button>}
      />
      <DataTable
        rows={data ?? []}
        keyOf={(c) => c.id}
        empty="Aún no hay clientes registrados"
        columns={[
          { header: 'Empresa', cell: (c) => c.nombre },
          { header: 'Representante', cell: (c) => c.representante ?? '—' },
          { header: 'Documento', cell: (c) => c.documento ?? '—' },
          { header: 'Teléfono', cell: (c) => c.telefono ?? '—' },
          { header: 'Correo', cell: (c) => c.email ?? '—' },
          { header: 'Dirección', cell: (c) => c.direccion ?? '—' },
        ]}
      />
      <Modal open={open} onClose={() => setOpen(false)} title="Nuevo cliente">
        <form onSubmit={onSubmit} className="space-y-space-lg">
          <Input label="Nombre de la empresa *" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
          <Input label="Nombre del cliente (representante) *" value={form.representante} onChange={(e) => setForm({ ...form, representante: e.target.value })} required />
          <Input label="Documento (RIF o cédula) *" value={form.documento} onChange={(e) => setForm({ ...form, documento: e.target.value })} required />
          <Input label="Número telefónico *" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} required />
          <Input label="Correo" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input label="Dirección *" value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} required />
          {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" loading={create.isPending} className="w-full">
            Guardar cliente
          </Button>
        </form>
      </Modal>
    </div>
  )
}
