import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

export interface Dashboard {
  ventas: {
    clientes: number
    facturas: number
    monto_cobrado: number
    proyectos_total: number
    proyectos_por_estado: Record<string, number>
  }
  desarrollo: { planes: number; fases_por_estado: Record<string, number>; cancelaciones: number }
  despacho: { proyectos_por_estado: Record<string, number> }
  tecnologia: { incidencias_por_estado: Record<string, number>; incidencias_por_prioridad: Record<string, number> }
  usuarios: { por_departamento: Record<string, number>; por_estado: Record<string, number>; total: number }
}

export interface Actividad {
  id: string
  user_email: string | null
  accion: string
  entidad_tipo: string | null
  entidad_id: string | null
  detalle: string | null
  fecha: string
}

export interface ProyectoRRHH {
  id: string
  codigo: string
  titulo: string
  estado_ventas: string
  estado_desarrollo: string
  estado_despacho: string
  [k: string]: unknown
}

export interface UsuarioRRHH {
  id: string
  email: string
  nombre: string
  departamento: string
  cargo: string | null
  estado: string
}

const Q = 'rrhh'

export function useDashboard() {
  return useQuery({ queryKey: [Q, 'dashboard'], queryFn: () => api.get<Dashboard>('/rrhh/dashboard') })
}

export function useActividad() {
  return useQuery({ queryKey: [Q, 'actividad'], queryFn: () => api.get<Actividad[]>('/rrhh/actividad') })
}

export function useProyectosRRHH() {
  return useQuery({ queryKey: [Q, 'proyectos'], queryFn: () => api.get<ProyectoRRHH[]>('/rrhh/proyectos') })
}

export function useUsuariosRRHH(departamento?: string) {
  return useQuery({
    queryKey: [Q, 'usuarios', departamento ?? 'todos'],
    queryFn: () => api.get<UsuarioRRHH[]>(`/rrhh/usuarios${departamento ? `?departamento=${departamento}` : ''}`),
  })
}

function useRefresh() {
  const qc = useQueryClient()
  return () => qc.invalidateQueries({ queryKey: [Q] })
}

export function useCrearUsuario() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: (body: unknown) => api.post('/auth/usuarios', body), onSuccess: refresh })
}

export function useActualizarUsuario() {
  const refresh = useRefresh()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: unknown }) => api.patch(`/auth/usuarios/${id}`, body),
    onSuccess: refresh,
  })
}
