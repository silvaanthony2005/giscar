import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

export interface Incidencia {
  id: string
  codigo: string
  titulo: string
  descripcion: string
  equipo_afectado: string
  departamento_origen: string
  prioridad: 'baja' | 'media' | 'alta' | 'critica'
  estado: string
  orden_llegada: number
  reportado_por: string
  reportado_por_nombre: string | null
  asignado_a: string | null
  asignado_a_nombre: string | null
  created_at: string
}

export interface ReporteResolucion {
  id: string
  diagnostico: string
  solucion: string
  tiempo_resolucion_horas: number
  resuelto_por_nombre: string | null
  fecha: string
}

export interface IncidenciaDetalle extends Incidencia {
  reportes: ReporteResolucion[]
}

export interface ColaIncidencias {
  incidencias: Incidencia[]
  resumen: Record<string, number>
}

const Q = 'tecnologia'

export function useIncidencias() {
  return useQuery({
    queryKey: [Q, 'cola'],
    queryFn: () => api.get<ColaIncidencias>('/tecnologia/incidencias'),
  })
}

export function useIncidencia(iid: string) {
  return useQuery({
    queryKey: [Q, 'incidencia', iid],
    queryFn: () => api.get<IncidenciaDetalle>(`/tecnologia/incidencias/${iid}`),
    enabled: !!iid,
  })
}

function useRefresh(iid?: string) {
  const qc = useQueryClient()
  return () => {
    qc.invalidateQueries({ queryKey: [Q, 'cola'] })
    if (iid) qc.invalidateQueries({ queryKey: [Q, 'incidencia', iid] })
  }
}

export function useCrearIncidencia() {
  const refresh = useRefresh()
  return useMutation({
    mutationFn: (body: unknown) => api.post<Incidencia>('/tecnologia/incidencias', body),
    onSuccess: refresh,
  })
}

export function useCambiarEstadoIncidencia(iid: string) {
  const refresh = useRefresh(iid)
  return useMutation({
    mutationFn: (target: string) => api.post(`/tecnologia/incidencias/${iid}/estado`, { target }),
    onSuccess: refresh,
  })
}

export function useAsignarIncidencia(iid: string) {
  const refresh = useRefresh(iid)
  return useMutation({
    mutationFn: (user_id: string) => api.post(`/tecnologia/incidencias/${iid}/asignar`, { user_id }),
    onSuccess: refresh,
  })
}

export function useResolverIncidencia(iid: string) {
  const refresh = useRefresh(iid)
  return useMutation({
    mutationFn: (body: unknown) => api.post(`/tecnologia/incidencias/${iid}/reporte`, body),
    onSuccess: refresh,
  })
}

export function useTecnicos() {
  return useQuery({
    queryKey: [Q, 'tecnicos'],
    queryFn: () => api.get<{ id: string; nombre: string }[]>('/tecnologia/tecnicos'),
    retry: false,
  })
}
