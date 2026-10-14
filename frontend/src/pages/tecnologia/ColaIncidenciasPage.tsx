import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCrearIncidencia, useIncidencias } from '../../entities/project/tecnologia-api'
import { Button } from '../../atoms/Button'
import { Badge } from '../../atoms/Badge'
import { Input } from '../../atoms/Input'
import { Select } from '../../atoms/Select'
import { Textarea } from '../../atoms/Textarea'
import { Modal } from '../../molecules/Modal'
import { EstadoBadge } from '../../molecules/EstadoBadge'
import { SectionHeader } from '../../molecules/SectionHeader'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState, StatCard } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { formatDateTime } from '../../shared/lib/format'

const PRIORIDADES = [
  { value: 'baja', label: 'Baja' },
  { value: 'media', label: 'Media' },
  { value: 'alta', label: 'Alta' },
  { value: 'critica', label: 'Crítica' },
]

const prioridadTone: Record<string, 'danger' | 'warning' | 'info' | 'neutral'> = {
  critica: 'danger',
  alta: 'warning',
  media: 'info',
  baja: 'neutral',
}

const empty = { titulo: '', descripcion: '', equipo_afectado: '', prioridad: 'media' }

export function ColaIncidenciasPage() {
  const { data, isLoading, error } = useIncidencias()
  const crear = useCrearIncidencia()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(empty)
  const [msg, setMsg] = useState<string | null>(null)

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    crear.mutate(form, {
      onSuccess: () => {
        setOpen(false)
        setForm(empty)
      },
      onError: (err) => setMsg(err.message),
    })
  }

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  type Incidencia = NonNullable<typeof data>['incidencias'][number]
  const incidencias = data?.incidencias ?? []
  const resumen = data?.resumen ?? {}

  const columns = [
    {
      header: 'Código',
      cell: (i: Incidencia) => <span className="font-medium">{i.codigo}</span>,
    },
    { header: 'Título', cell: (i: Incidencia) => i.titulo },
    { header: 'Equipo', cell: (i: Incidencia) => i.equipo_afectado },
    {
      header: 'Prioridad',
      cell: (i: Incidencia) => (
        <Badge tone={prioridadTone[i.prioridad] ?? 'neutral'}>{i.prioridad}</Badge>
      ),
    },
    { header: 'Estado', cell: (i: Incidencia) => <EstadoBadge valor={i.estado} /> },
    { header: 'Origen', cell: (i: Incidencia) => i.departamento_origen },
    {
      header: 'Reportada',
      cell: (i: Incidencia) => <span className="text-label-sm">{formatDateTime(i.created_at)}</span>,
    },
  ]

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Tecnología', 'Cola']}
        title="Mesa de Ayuda"
        subtitle="Cola de incidencias de hardware y electrónica, ordenada por llegada y severidad."
        actions={
          <Button icon="add" onClick={() => setOpen(true)}>
            Nueva incidencia
          </Button>
        }
      />

      <div className="mb-space-xl grid grid-cols-2 gap-space-md sm:grid-cols-4">
        {Object.entries(resumen).map(([k, v]) => (
          <StatCard key={k} label={k.replace('_', ' ')} value={v} />
        ))}
      </div>

      <SectionHeader
        icon="list"
        title="Incidencias"
        description="Seleccione una fila para ver el detalle y el acta de resolución."
      />
      <DataTable
        rows={incidencias}
        keyOf={(i) => i.id}
        empty="No hay incidencias registradas"
        onRowClick={(i) => navigate(`/tecnologia/incidencias/${i.id}`)}
        columns={columns}
      />

      <Modal open={open} onClose={() => setOpen(false)} title="Nueva incidencia" width="max-w-xl">
        <form onSubmit={onSubmit} className="space-y-space-lg">
          <Input
            label="Título *"
            value={form.titulo}
            onChange={(e) => setForm({ ...form, titulo: e.target.value })}
            required
          />
          <Input
            label="Equipo afectado *"
            value={form.equipo_afectado}
            onChange={(e) => setForm({ ...form, equipo_afectado: e.target.value })}
            placeholder="Ej: PC-03, impresora, monitor…"
            required
          />
          <Textarea
            label="Descripción *"
            hint="Mínimo 15 caracteres."
            required
            minLength={15}
            rows={4}
            value={form.descripcion}
            onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
            placeholder="Describe el fallo observado…"
          />
          <Select
            label="Prioridad *"
            value={form.prioridad}
            onChange={(e) => setForm({ ...form, prioridad: e.target.value })}
            options={PRIORIDADES}
          />
          {msg && <p className="text-body-md text-on-error-container">{msg}</p>}
          <Button type="submit" loading={crear.isPending} className="w-full">
            Registrar incidencia
          </Button>
        </form>
      </Modal>
    </div>
  )
}
