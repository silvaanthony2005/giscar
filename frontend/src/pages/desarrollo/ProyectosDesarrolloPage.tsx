import { useNavigate } from 'react-router-dom'
import { useTableroDesarrollo } from '../../entities/project/desarrollo-api'
import { EstadoBadge } from '../../molecules/EstadoBadge'
import { SectionHeader } from '../../molecules/SectionHeader'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { formatMoney } from '../../shared/lib/format'

type ProyectoDesarrollo = {
  id: string
  codigo: string
  titulo: string
  monto_total: number
  estado_desarrollo: string
}

const columns = [
  {
    header: 'Código',
    cell: (p: ProyectoDesarrollo) => <span className="font-medium">{p.codigo}</span>,
  },
  { header: 'Título', cell: (p: ProyectoDesarrollo) => p.titulo },
  {
    header: 'Monto',
    cell: (p: ProyectoDesarrollo) => formatMoney(p.monto_total),
    className: 'text-right',
  },
  {
    header: 'Estado',
    cell: (p: ProyectoDesarrollo) => <EstadoBadge valor={p.estado_desarrollo} />,
  },
]

export function ProyectosDesarrolloPage() {
  const { data, isLoading, error } = useTableroDesarrollo()
  const navigate = useNavigate()

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  // Las columnas las agrupa el backend; aquí solo se pintan.
  const { recibidos = [], en_curso: enCurso = [], historial = [] } = data ?? {}

  const goTo = (p: ProyectoDesarrollo) => navigate(`/desarrollo/proyectos/${p.id}`)

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Producción', 'Proyectos']}
        title="Proyectos de Producción"
        subtitle="Planes técnicos, fases, personas asignadas y seguimiento de avance."
      />

      <Section
        icon="inbox"
        title="Recibidos de Ventas"
        description="Proyectos con cobro confirmado esperando plan técnico."
        count={recibidos.length}
        emptyText="No hay proyectos nuevos esperando plan"
      >
        <DataTable
          rows={recibidos}
          keyOf={(p) => p.id}
          empty="No hay proyectos nuevos esperando plan"
          onRowClick={goTo}
          columns={columns}
        />
      </Section>

      <Section
        icon="code"
        title="En curso"
        description="Proyectos en planificación o en producción activa."
        count={enCurso.length}
        emptyText="No hay proyectos en producción"
      >
        <DataTable
          rows={enCurso}
          keyOf={(p) => p.id}
          empty="No hay proyectos en producción"
          onRowClick={goTo}
          columns={columns}
        />
      </Section>

      <Section
        icon="history"
        title="Histórico"
        description="Proyectos completados, cancelados o ya traspasados."
        count={historial.length}
        emptyText="Aún no hay proyectos en el histórico"
      >
        <DataTable
          rows={historial}
          keyOf={(p) => p.id}
          empty="Aún no hay proyectos en el histórico"
          onRowClick={goTo}
          columns={columns}
        />
      </Section>
    </div>
  )
}

function Section({
  icon,
  title,
  description,
  count,
  emptyText,
  children,
}: {
  icon: string
  title: string
  description: string
  count: number
  emptyText: string
  children: React.ReactNode
}) {
  if (count === 0) {
    return (
      <section className="mb-space-xl">
        <SectionHeader icon={icon} title={title} description={description} chip="0" />
        <p className="rounded-xl bg-surface-container-lowest p-space-xl text-center text-body-md text-on-surface-variant shadow-hairline">
          {emptyText}
        </p>
      </section>
    )
  }
  return (
    <section className="mb-space-xl">
      <SectionHeader icon={icon} title={title} description={description} chip={String(count)} />
      {children}
    </section>
  )
}
