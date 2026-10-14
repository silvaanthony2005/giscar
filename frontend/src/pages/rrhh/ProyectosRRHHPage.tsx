import { useProyectosRRHH } from '../../entities/project/rrhh-api'
import { EstadoBadge } from '../../molecules/EstadoBadge'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'

export function ProyectosRRHHPage() {
  const { data, isLoading, error } = useProyectosRRHH()
  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  return (
    <div className="p-6">
      <PageHeader breadcrumb={['RRHH', 'Proyectos']}
        title="Todos los Proyectos"
        subtitle="Lectura global de los tres departamentos: Ventas, Desarrollo y Despacho." />
      <DataTable
        rows={data ?? []}
        keyOf={(p) => p.id}
        empty="Aún no hay proyectos"
        columns={[
          { header: 'Código', cell: (p) => <span className="font-medium">{p.codigo}</span> },
          { header: 'Título', cell: (p) => p.titulo },
          { header: 'Ventas', cell: (p) => <EstadoBadge valor={p.estado_ventas} /> },
          { header: 'Desarrollo', cell: (p) => <EstadoBadge valor={p.estado_desarrollo} /> },
          { header: 'Despacho', cell: (p) => <EstadoBadge valor={p.estado_despacho} /> },
        ]}
      />
    </div>
  )
}
