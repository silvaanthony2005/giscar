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
  ],
  desarrollo: [{ to: '/desarrollo', label: 'Proyectos', icon: 'terminal', end: true }],
  despacho: [{ to: '/despacho', label: 'Cola de entregas', icon: 'local_shipping', end: true }],
  tecnologia: [{ to: '/tecnologia', label: 'Incidencias', icon: 'support_agent', end: true }],
  rrhh: [
    { to: '/rrhh', label: 'Panel general', icon: 'grid_view', end: true },
    { to: '/rrhh/usuarios', label: 'Usuarios', icon: 'manage_accounts' },
    { to: '/rrhh/proyectos', label: 'Proyectos', icon: 'folder_open' },
    { to: '/rrhh/actividad', label: 'Bitácora', icon: 'history' },
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
