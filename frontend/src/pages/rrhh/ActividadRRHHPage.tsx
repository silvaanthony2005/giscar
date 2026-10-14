import { useActividad } from '../../entities/project/rrhh-api'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { formatDateTime } from '../../shared/lib/format'

export function ActividadRRHHPage() {
  const { data, isLoading, error } = useActividad()
  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  return (
    <div className="p-6">
      <PageHeader breadcrumb={['RRHH', 'Bitácora']}
        title="Bitácora de Actividad"
        subtitle="Registro de auditoría de las acciones sensibles del sistema." />
      <DataTable
        rows={data ?? []}
        keyOf={(a) => a.id}
        empty="Sin actividad registrada"
        columns={[
          { header: 'Fecha', cell: (a) => formatDateTime(a.fecha), className: 'text-label-sm whitespace-nowrap' },
          { header: 'Usuario', cell: (a) => a.user_email ?? '—' },
          { header: 'Acción', cell: (a) => <span className="font-medium">{a.accion.replace(/_/g, ' ')}</span> },
          { header: 'Entidad', cell: (a) => a.entidad_tipo ?? '—' },
          { header: 'Detalle', cell: (a) => a.detalle ?? '—' },
        ]}
      />
    </div>
  )
}
