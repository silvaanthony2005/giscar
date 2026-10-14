import { useNavigate } from 'react-router-dom'
import { useDespachoProyectos } from '../../entities/project/despacho-api'
import { EstadoBadge } from '../../molecules/EstadoBadge'
import { SectionHeader } from '../../molecules/SectionHeader'
import { DataTable } from '../../organisms/DataTable'
import { ErrorState, LoadingState } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { formatMoney } from '../../shared/lib/format'

export function ColaDespachoPage() {
  const { data, isLoading, error } = useDespachoProyectos()
  const navigate = useNavigate()

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />

  // Las columnas las agrupa el backend; aquí solo se pintan.
  const { pendientes = [], cerrados = [] } = data ?? {}
  type Row = (typeof pendientes)[number]

  const columns = [
    { header: 'Código', cell: (p: Row) => <span className="font-medium">{p.codigo}</span> },
    { header: 'Cliente', cell: (p: Row) => p.cliente },
    { header: 'Título', cell: (p: Row) => p.titulo },
    { header: 'Saldo', cell: (p: Row) => formatMoney(p.saldo), className: 'text-right' },
    { header: 'Estado', cell: (p: Row) => <EstadoBadge valor={p.estado_despacho} /> },
  ]

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['Despacho', 'Cola']}
        title="Bandeja y Control de Entregas"
        subtitle="Contacto con el cliente, cobro del saldo pendiente y acta de entrega."
      />
      <section className="mb-space-xl">
        <SectionHeader
          icon="pending_actions"
          title="Pendientes"
          description="Proyectos listos para contacto, cobro de saldo y entrega."
          chip={String(pendientes.length)}
        />
        <DataTable
          rows={pendientes}
          keyOf={(p) => p.id}
          empty="No hay proyectos pendientes de despacho"
          onRowClick={(p) => navigate(`/despacho/proyectos/${p.id}`)}
          columns={columns}
        />
      </section>

      <section>
        <SectionHeader
          icon="inventory_2"
          title="Cerrados"
          description="Historial de entregas realizadas y denegadas."
          chip={String(cerrados.length)}
        />
        <DataTable
          rows={cerrados}
          keyOf={(p) => p.id}
          empty="Aún no hay proyectos cerrados"
          onRowClick={(p) => navigate(`/despacho/proyectos/${p.id}`)}
          columns={columns}
        />
      </section>
    </div>
  )
}
