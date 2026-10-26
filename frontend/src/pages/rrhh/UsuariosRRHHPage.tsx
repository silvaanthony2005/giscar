import { useState, type FormEvent } from 'react'
import {
  useActualizarUsuario,
  useCrearUsuario,
  useUsuariosRRHH,
  type UsuarioRRHH,
} from '../../entities/project/rrhh-api'
import { Button } from '../../atoms/Button'
import { Badge } from '../../atoms/Badge'
import { IconButton } from '../../atoms/IconButton'
import { Input } from '../../atoms/Input'
import { Select } from '../../atoms/Select'
import { Tooltip } from '../../atoms/Tooltip'
import { Modal } from '../../molecules/Modal'
import { SectionHeader } from '../../molecules/SectionHeader'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { DEPARTAMENTOS as NOMBRE_DEPTO } from '../../shared/lib/format'

const DEPTOS = Object.keys(NOMBRE_DEPTO)

const deptoOptions = DEPTOS.map((d) => ({ value: d, label: NOMBRE_DEPTO[d] ?? d }))

const formVacio = {
  id: null as string | null,
  estado: 'activo',
  nombre: '',
  email: '',
  password: '',
  documento: '',
  telefono: '',
  direccion: '',
  cargo: '',
  departamento: 'ventas',
}

const ESTADO_TONE: Record<string, 'success' | 'danger' | 'warning'> = {
  activo: 'success',
  bloqueado: 'danger',
  desactivado: 'warning',
}

export function UsuariosRRHHPage() {
  const [depto, setDepto] = useState<string | undefined>(undefined)
  const { data, isLoading, error } = useUsuariosRRHH(depto)
  const crear = useCrearUsuario()
  const actualizar = useActualizarUsuario()

  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(formVacio)
  const [msg, setMsg] = useState<string | null>(null)
  const [errorAccion, setErrorAccion] = useState<string | null>(null)
  const [porDesactivar, setPorDesactivar] = useState<UsuarioRRHH | null>(null)

  const abrirEdicion = (u: UsuarioRRHH) => {
    setForm({
      id: u.id,
      estado: u.estado,
      nombre: u.nombre,
      email: u.email,
      password: '',
      documento: u.documento ?? '',
      telefono: u.telefono ?? '',
      direccion: u.direccion ?? '',
      cargo: u.cargo ?? '',
      departamento: u.departamento,
    })
    setMsg(null)
    setOpen(true)
  }

  const abrirAlta = () => {
    setForm(formVacio)
    setMsg(null)
    setOpen(true)
  }

  const cerrarForm = () => {
    setOpen(false)
    setForm(formVacio)
    setMsg(null)
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    const body = {
      nombre: form.nombre,
      email: form.email,
      documento: form.documento.trim() || null,
      telefono: form.telefono.trim() || null,
      direccion: form.direccion.trim() || null,
      cargo: form.cargo.trim() || null,
      departamento: form.departamento,
    }
    if (form.id) {
      // Contraseña vacía = no cambiar.
      const cambios = form.password ? { ...body, password: form.password } : body
      actualizar.mutate({ id: form.id, body: cambios }, {
        onSuccess: cerrarForm,
        onError: (err) => setMsg(err.message),
      })
    } else {
      crear.mutate({ ...body, password: form.password }, {
        onSuccess: cerrarForm,
        onError: (err) => setMsg(err.message),
      })
    }
  }

  const cambiarEstado = (u: UsuarioRRHH, estado: string) => {
    setErrorAccion(null)
    actualizar.mutate({ id: u.id, body: { estado } }, { onError: (err) => setErrorAccion(err.message) })
  }

  const cambiarDepto = (id: string, departamento: string) => {
    setErrorAccion(null)
    actualizar.mutate({ id, body: { departamento } }, { onError: (err) => setErrorAccion(err.message) })
  }

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['RRHH', 'Usuarios']}
        title="Gestión de Usuarios y Personal"
        subtitle="Alta, edición, bloqueo, baja lógica y reasignación de personal entre departamentos."
        actions={
          <Button icon="person_add" onClick={abrirAlta}>
            Nuevo usuario
          </Button>
        }
      />

      <div className="mb-space-lg flex flex-wrap gap-space-sm">
        <Button size="sm" variant={depto === undefined ? 'primary' : 'ghost'} aria-pressed={depto === undefined} onClick={() => setDepto(undefined)}>
          Todos
        </Button>
        {DEPTOS.map((d) => (
          <Button
            key={d}
            size="sm"
            variant={depto === d ? 'primary' : 'ghost'}
            aria-pressed={depto === d}
            onClick={() => setDepto(d)}
          >
            {NOMBRE_DEPTO[d] ?? d}
          </Button>
        ))}
      </div>

      <SectionHeader
        icon="manage_accounts"
        title="Directorio"
        description="Los desactivados quedan en la base de datos pero dejan de aparecer en los módulos y no pueden iniciar sesión."
      />
      {errorAccion && (
        <p role="alert" className="mb-space-md rounded-lg bg-error-container/40 px-space-md py-space-sm text-body-md text-on-error-container">
          {errorAccion}
        </p>
      )}
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
                disabled={u.estado === 'desactivado'}
                onChange={(e) => cambiarDepto(u.id, e.target.value)}
                className="h-8 rounded-lg bg-surface-container-low px-space-sm text-body-md text-on-surface shadow-hairline focus:outline-none focus:ring-2 focus:ring-secondary/20 disabled:opacity-50"
              >
                {DEPTOS.map((d) => (
                  <option key={d} value={d}>
                    {NOMBRE_DEPTO[d] ?? d}
                  </option>
                ))}
              </select>
            ),
          },
          {
            header: 'Estado',
            cell: (u) => <Badge tone={ESTADO_TONE[u.estado] ?? 'warning'}>{u.estado}</Badge>,
          },
          {
            header: 'Acciones',
            className: 'whitespace-nowrap',
            cell: (u) => (
              <div className="flex flex-nowrap items-center gap-space-xs">
                <Tooltip label="Editar">
                  <IconButton icon="edit" label={`Editar a ${u.nombre}`} onClick={() => abrirEdicion(u)} />
                </Tooltip>
                {u.estado === 'desactivado' ? (
                  <Tooltip label="Restaurar">
                    <IconButton icon="restore" label={`Restaurar a ${u.nombre}`} onClick={() => cambiarEstado(u, 'activo')} />
                  </Tooltip>
                ) : (
                  <>
                    <Tooltip label={u.estado === 'activo' ? 'Bloquear' : 'Desbloquear'}>
                      <IconButton
                        icon={u.estado === 'activo' ? 'lock' : 'lock_open'}
                        label={`${u.estado === 'activo' ? 'Bloquear' : 'Desbloquear'} a ${u.nombre}`}
                        onClick={() => cambiarEstado(u, u.estado === 'activo' ? 'bloqueado' : 'activo')}
                      />
                    </Tooltip>
                    <Tooltip label="Dar de baja (reversible)">
                      <IconButton
                        icon="delete"
                        tone="danger"
                        label={`Dar de baja a ${u.nombre}`}
                        onClick={() => setPorDesactivar(u)}
                      />
                    </Tooltip>
                  </>
                )}
              </div>
            ),
          },
        ]}
      />

      <Modal open={open} onClose={cerrarForm} title={form.id ? 'Editar usuario' : 'Nuevo usuario'}>
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
            label="Documento"
            value={form.documento}
            onChange={(e) => setForm({ ...form, documento: e.target.value })}
          />
          <Input
            label="Teléfono"
            type="tel"
            inputMode="numeric"
            value={form.telefono}
            onChange={(e) => setForm({ ...form, telefono: e.target.value.replace(/\D/g, '') })}
          />
          <Input
            label="Dirección"
            value={form.direccion}
            onChange={(e) => setForm({ ...form, direccion: e.target.value })}
          />
          <Input
            label="Cargo"
            value={form.cargo}
            onChange={(e) => setForm({ ...form, cargo: e.target.value })}
          />
          <Select
            label="Departamento *"
            value={form.departamento}
            disabled={form.estado === 'desactivado'}
            onChange={(e) => setForm({ ...form, departamento: e.target.value })}
            options={deptoOptions}
          />
          <Input
            label={form.id ? 'Contraseña' : 'Contraseña *'}
            hint={form.id ? 'Déjalo vacío para conservar la actual. Mínimo 8 caracteres.' : 'Mínimo 8 caracteres.'}
            type="password"
            minLength={8}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required={!form.id}
          />
          {msg && <p role="alert" className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" loading={crear.isPending || actualizar.isPending} className="w-full">
            {form.id ? 'Guardar cambios' : 'Crear usuario'}
          </Button>
        </form>
      </Modal>

      <Modal open={porDesactivar !== null} onClose={() => setPorDesactivar(null)} title="Dar de baja">
        <p className="text-body-md text-on-surface">
          ¿Dar de baja a <span className="font-medium">{porDesactivar?.nombre}</span>? No podrá
          iniciar sesión ni aparecer en los módulos, pero podrás restaurarlo desde este directorio.
        </p>
        <div className="mt-space-lg flex justify-end gap-space-sm">
          <Button variant="ghost" onClick={() => setPorDesactivar(null)}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            icon="delete"
            onClick={() => {
              if (porDesactivar) cambiarEstado(porDesactivar, 'desactivado')
              setPorDesactivar(null)
            }}
          >
            Dar de baja
          </Button>
        </div>
      </Modal>
    </div>
  )
}
