import type { Departamento } from '../../entities/auth/types'

export interface NavItem {
  to: string
  label: string
  icon: string
  /** true si el enlace debe resaltar solo en la ruta exacta */
  end?: boolean
}

export const NAV: Record<Departamento, NavItem[]> = {
  ventas: [
    { to: '/ventas', label: 'Proyectos', icon: 'point_of_sale', end: true },
    { to: '/ventas/clientes', label: 'Clientes', icon: 'badge' },
    { to: '/incidencias/nueva', label: 'Reportar incidencia', icon: 'report' },
  ],
  desarrollo: [
    { to: '/desarrollo', label: 'Proyectos', icon: 'terminal', end: true },
    { to: '/incidencias/nueva', label: 'Reportar incidencia', icon: 'report' },
  ],
  despacho: [
    { to: '/despacho', label: 'Cola de entregas', icon: 'local_shipping', end: true },
    { to: '/incidencias/nueva', label: 'Reportar incidencia', icon: 'report' },
  ],
  tecnologia: [{ to: '/tecnologia', label: 'Incidencias', icon: 'support_agent', end: true }],
  rrhh: [
    { to: '/rrhh', label: 'Panel general', icon: 'grid_view', end: true },
    { to: '/rrhh/usuarios', label: 'Usuarios', icon: 'manage_accounts' },
    { to: '/rrhh/proyectos', label: 'Proyectos', icon: 'folder_open' },
    { to: '/rrhh/actividad', label: 'Bitácora', icon: 'history' },
    { to: '/incidencias/nueva', label: 'Reportar incidencia', icon: 'report' },
  ],
}

export const DEPARTAMENTO_ICONS: Record<Departamento, string> = {
  ventas: 'point_of_sale',
  desarrollo: 'terminal',
  despacho: 'local_shipping',
  tecnologia: 'support_agent',
  rrhh: 'groups',
}

export const DEPARTAMENTO_DESCRIPCION: Record<Departamento, string> = {
  ventas: 'Levantamiento, cobros y facturación',
  desarrollo: 'Plan técnico, fases y seguimiento',
  despacho: 'Entregas y liquidación con el cliente',
  tecnologia: 'Mesa de ayuda e incidencias',
  rrhh: 'Administración y control de acceso',
}

/** Etiquetas e iconos de las categorías de la búsqueda global. */
export const TIPO_BUSQUEDA: Record<string, { label: string; icon: string }> = {
  proyecto: { label: 'Proyectos', icon: 'folder_open' },
  cliente: { label: 'Clientes', icon: 'badge' },
  incidencia: { label: 'Incidencias', icon: 'support_agent' },
  usuario: { label: 'Usuarios', icon: 'person' },
}

/**
 * Adónde navega un resultado de búsqueda, según el módulo del usuario.
 *
 * El backend devuelve solo `tipo` + `id`: elegir la ruta es presentación, no
 * negocio. Para `cliente` y `usuario` no existe página de detalle, así que se
 * abre el listado del módulo.
 */
const RUTA_POR_TIPO: Record<string, Partial<Record<Departamento, string>>> = {
  proyecto: {
    ventas: '/ventas/proyectos',
    desarrollo: '/desarrollo/proyectos',
    despacho: '/despacho/proyectos',
    // RRHH lee todos los departamentos; la ficha de Ventas es la más completa.
    rrhh: '/ventas/proyectos',
  },
  incidencia: {
    tecnologia: '/tecnologia/incidencias',
    rrhh: '/tecnologia/incidencias',
  },
  cliente: { ventas: '/ventas/clientes', rrhh: '/ventas/clientes' },
  usuario: { rrhh: '/rrhh/usuarios' },
}

export function rutaResultado(
  tipo: string,
  id: string,
  departamento: Departamento,
): string | null {
  const base = RUTA_POR_TIPO[tipo]?.[departamento]
  if (!base) return null
  const conDetalle = base.endsWith('/proyectos') || base.endsWith('/incidencias')
  return conDetalle ? `${base}/${id}` : base
}
