import { useState, type FormEvent } from 'react'
import {
  useActualizarUsuario,
  useCrearUsuario,
  useUsuariosRRHH,
} from '../../entities/project/rrhh-api'
import { Button } from '../../atoms/Button'
import { Badge } from '../../atoms/Badge'
import { Input } from '../../atoms/Input'
import { Select } from '../../atoms/Select'
import { Modal } from '../../molecules/Modal'
import { SectionHeader } from '../../molecules/SectionHeader'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'

const DEPARTAMENTOS = ['ventas', 'desarrollo', 'despacho', 'tecnologia', 'rrhh']

const deptoOptions = DEPARTAMENTOS.map((d) => ({ value: d, label: d }))

const empty = {
  nombre: '',
  email: '',
  password: '',
  cargo: '',
  departamento: 'ventas',
}

export function UsuariosRRHHPage() {
  const [depto, setDepto] = useState<string | undefined>(undefined)
  const { data, isLoading, error } = useUsuariosRRHH(depto)
  const crear = useCrearUsuario()
  const actualizar = useActualizarUsuario()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(empty)
  const [msg, setMsg] = useState<string | null>(null)

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    crear.mutate(
      { ...form, cargo: form.cargo || null },
      {
        onSuccess: () => {
          setOpen(false)
          setForm(empty)
        },
        onError: (err) => setMsg(err.message),
      },
    )
  }

  const toggleEstado = (id: string, estado: string) => {
    actualizar.mutate(
      { id, body: { estado: estado === 'activo' ? 'bloqueado' : 'activo' } },
      { onError: (err) => alert(err.message) },
    )
  }

  const cambiarDepto = (id: string, departamento: string) => {
    actualizar.mutate({ id, body: { departamento } }, { onError: (err) => alert(err.message) })
  }

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['RRHH', 'Usuarios']}
        title="Gestión de Usuarios y Personal"
        subtitle="Alta, bloqueo y reasignación de personal entre departamentos."
        actions={
          <Button icon="person_add" onClick={() => setOpen(true)}>
            Nuevo usuario
          </Button>
        }
      />

      <div className="mb-space-lg flex flex-wrap gap-space-sm">
        <Button size="sm" variant={depto === undefined ? 'primary' : 'ghost'} onClick={() => setDepto(undefined)}>
          Todos
        </Button>
        {DEPARTAMENTOS.map((d) => (
          <Button
            key={d}
            size="sm"
            variant={depto === d ? 'primary' : 'ghost'}
            onClick={() => setDepto(d)}
          >
            {d}
          </Button>
        ))}
      </div>

      <SectionHeader
        icon="manage_accounts"
        title="Directorio"
        description="Los cambios de departamento y estado se validan en el servidor."
      />
      <DataTable
        rows={data ?? []}
        keyOf={(u) => u.id}
        empty="No hay usuarios"
        columns={[
          { header: 'Nombre', cell: (u) => <span className="font-medium">{u.nombre}</span> },
          { header: 'Correo', cell: (u) => u.email },
          { header: 'Cargo', cell: (u) => u.cargo ?? '—' },
          {
            header: 'Departamento',
            cell: (u) => (
              <select
                value={u.departamento}
                aria-label={`Departamento de ${u.nombre}`}
                onChange={(e) => cambiarDepto(u.id, e.target.value)}
                onClick={(e) => e.stopPropagation()}
                className="h-8 rounded-lg bg-surface-container-low px-space-sm text-body-md text-on-surface shadow-hairline focus:outline-none focus:ring-2 focus:ring-secondary/20"
              >
                {DEPARTAMENTOS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            ),
          },
          {
            header: 'Estado',
            cell: (u) => (
              <Badge tone={u.estado === 'activo' ? 'success' : 'danger'}>{u.estado}</Badge>
            ),
          },
          {
            header: '',
            cell: (u) => (
              <Button
                size="sm"
                variant={u.estado === 'activo' ? 'danger' : 'primary'}
                onClick={(e) => {
                  e.stopPropagation()
                  toggleEstado(u.id, u.estado)
                }}
              >
                {u.estado === 'activo' ? 'Bloquear' : 'Desbloquear'}
              </Button>
            ),
          },
        ]}
      />

      <Modal open={open} onClose={() => setOpen(false)} title="Nuevo usuario">
        <form onSubmit={onSubmit} className="space-y-space-lg">
          <Input
            label="Nombre *"
            value={form.nombre}
            onChange={(e) => setForm({ ...form, nombre: e.target.value })}
            required
          />
          <Input
            label="Correo *"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
          <Input
            label="Contraseña *"
            hint="Mínimo 8 caracteres."
            type="password"
            minLength={8}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
          <Input
            label="Cargo"
            value={form.cargo}
            onChange={(e) => setForm({ ...form, cargo: e.target.value })}
          />
          <Select
            label="Departamento *"
            value={form.departamento}
            onChange={(e) => setForm({ ...form, departamento: e.target.value })}
            options={deptoOptions}
          />
          {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" loading={crear.isPending} className="w-full">
            Crear usuario
          </Button>
        </form>
      </Modal>
    </div>
  )
}
