import { Link } from 'react-router-dom'
import { useDashboard } from '../../entities/project/rrhh-api'
import { Icon } from '../../atoms/Icon'
import { Badge } from '../../atoms/Badge'
import { SectionHeader } from '../../molecules/SectionHeader'
import { ErrorState, LoadingState, StatCard } from '../../organisms/Feedback'
import { PageHeader } from '../../templates/PageHeader'
import { formatMoney } from '../../shared/lib/format'

export function DashboardRRHHPage() {
  const { data, isLoading, error } = useDashboard()
  if (isLoading) return <LoadingState />
  if (error || !data)
    return <ErrorState message={error?.message ?? 'Error al cargar el panel'} />

  const { ventas, desarrollo, despacho, tecnologia, usuarios } = data

  return (
    <div className="p-6">
      <PageHeader
        breadcrumb={['RRHH', 'Panel general']}
        title="Panel Ejecutivo"
        subtitle="Visión global de GCISCAR: todas las cifras las calcula el servidor."
      />

      <section className="mb-space-xl">
        <SectionHeader icon="point_of_sale" title="Ventas" description="Admisión comercial y cobros." />
        <div className="grid grid-cols-2 gap-space-md lg:grid-cols-4">
          <StatCard label="Clientes" value={String(ventas.clientes)} />
          <StatCard label="Facturas" value={String(ventas.facturas)} />
          <StatCard label="Monto cobrado" value={formatMoney(ventas.monto_cobrado)} />
          <StatCard label="Proyectos" value={String(ventas.proyectos_total)} />
        </div>
        <Chips title="Proyectos por estado" data={ventas.proyectos_por_estado} />
      </section>

      <section className="mb-space-xl">
        <SectionHeader
          icon="terminal"
          title="Producción"
          description="Planes, fases y cancelaciones."
        />
        <div className="grid grid-cols-2 gap-space-md lg:grid-cols-3">
          <StatCard label="Planes" value={String(desarrollo.planes)} />
          <StatCard label="Cancelaciones" value={String(desarrollo.cancelaciones)} />
          <StatCard
            label="Fases activas"
            value={String(desarrollo.fases_por_estado['en_curso'] ?? 0)}
          />
        </div>
        <Chips title="Fases por estado" data={desarrollo.fases_por_estado} />
      </section>

      <section className="mb-space-xl">
        <SectionHeader
          icon="local_shipping"
          title="Despacho"
          description="Entregas, negaciones y saldos."
        />
        <Chips title="Proyectos por estado" data={despacho.proyectos_por_estado} />
      </section>

      <section className="mb-space-xl">
        <SectionHeader
          icon="support_agent"
          title="Tecnología"
          description="Incidencias de hardware y electrónica."
        />
        <div className="grid gap-space-lg lg:grid-cols-2">
          <Chips title="Incidencias por estado" data={tecnologia.incidencias_por_estado} />
          <Chips title="Incidencias por prioridad" data={tecnologia.incidencias_por_prioridad} />
        </div>
      </section>

      <section>
        <SectionHeader icon="group" title="Usuarios" description="Personal y bloqueos." />
        <div className="grid grid-cols-2 gap-space-md lg:grid-cols-3">
          <StatCard label="Total" value={String(usuarios.total)} />
          <StatCard label="Activos" value={String(usuarios.por_estado['activo'] ?? 0)} />
          <StatCard label="Bloqueados" value={String(usuarios.por_estado['bloqueado'] ?? 0)} />
        </div>
        <Chips title="Por departamento" data={usuarios.por_departamento} />
      </section>

      <nav className="mt-space-xl flex flex-wrap gap-space-md text-body-md">
        <Link to="/rrhh/usuarios" className="inline-flex items-center gap-1 text-secondary hover:underline">
          <Icon name="manage_accounts" size="sm" />
          Gestionar usuarios
        </Link>
        <Link to="/rrhh/proyectos" className="inline-flex items-center gap-1 text-secondary hover:underline">
          <Icon name="folder_open" size="sm" />
          Todos los proyectos
        </Link>
        <Link to="/rrhh/actividad" className="inline-flex items-center gap-1 text-secondary hover:underline">
          <Icon name="history" size="sm" />
          Bitácora de actividad
        </Link>
      </nav>
    </div>
  )
}

function Chips({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data)
  if (entries.length === 0) return null
  return (
    <div className="mt-space-md">
      <p className="mb-space-sm text-label-md font-semibold tracking-wide text-on-surface-variant uppercase">
        {title}
      </p>
      <div className="flex flex-wrap gap-space-xs">
        {entries.map(([k, v]) => (
          <Badge key={k} tone="neutral">
            {k.replace('_', ' ')}: <strong>{v}</strong>
          </Badge>
        ))}
      </div>
    </div>
  )
}
