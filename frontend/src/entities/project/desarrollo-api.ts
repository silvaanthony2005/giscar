import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'
import type { Project } from './api'

export interface Phase {
  id: string
  orden: number
  nombre: string
  descripcion: string
  fecha_inicio: string | null
  fecha_fin_estimada: string | null
  fecha_fin_real: string | null
  horas_estimadas: number
  horas_reales: number
  estado: string
  acciones: string[]
}

export interface Member {
  id: string
  user_id: string
  nombre_usuario: string
  rol_proyecto: string
  fecha_asignacion: string
}

export interface Progress {
  id: string
  phase_id: string | null
  porcentaje: number
  notas: string
  fecha: string
  autor: string
}

export interface Plan {
  plan: { id: string; project_id: string; resumen: string; objetivos: string; horas_estimadas: number }
  fases: Phase[]
  miembros: Member[]
  avances: Progress[]
  horas_totales_fases: number
  acciones: string[]
}

export interface Cancellation {
  id: string
  project_id: string
  motivo: string
  informe: string
  fecha: string
}

const Q = 'desarrollo'

/** Columnas del tablero: el backend decide en cuál cae cada proyecto. */
export interface TableroDesarrollo {
  recibidos: Project[]
  en_curso: Project[]
  historial: Project[]
}

export function useTableroDesarrollo() {
  return useQuery({
    queryKey: [Q, 'tablero'],
    queryFn: () => api.get<TableroDesarrollo>('/desarrollo/proyectos'),
  })
}

export function useAcciones(pid: string) {
  return useQuery({
    queryKey: [Q, 'acciones', pid],
    queryFn: () => api.get<{ acciones: string[] }>(`/desarrollo/proyectos/${pid}/acciones`),
    enabled: !!pid,
    retry: false,
  })
}

export function usePlan(pid: string) {
  return useQuery({
    queryKey: [Q, 'plan', pid],
    queryFn: () => api.get<Plan>(`/desarrollo/proyectos/${pid}/plan`),
    enabled: !!pid,
    retry: false,
  })
}

export function useCreatePlan(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: unknown) => api.post(`/desarrollo/proyectos/${pid}/plan`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: [Q, 'plan', pid] }),
  })
}

export function usePhaseAction(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ fid, target }: { fid: string; target: string }) =>
      api.post(`/desarrollo/proyectos/${pid}/fases/${fid}/estado`, { target }),
    onSuccess: () => qc.invalidateQueries({ queryKey: [Q, 'plan', pid] }),
  })
}

export function useRecordProgress(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: unknown) => api.post<Progress>(`/desarrollo/proyectos/${pid}/avance`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: [Q, 'plan', pid] }),
  })
}

export function useProjectActions(pid: string) {
  const qc = useQueryClient()
  const inv = () => qc.invalidateQueries({ queryKey: [Q, 'plan', pid] })
  return {
    iniciar: useMutation({ mutationFn: () => api.post(`/desarrollo/proyectos/${pid}/iniciar`) }),
    completar: useMutation({ mutationFn: () => api.post(`/desarrollo/proyectos/${pid}/completar`), onSuccess: inv }),
    pasarDespacho: useMutation({ mutationFn: () => api.post(`/desarrollo/proyectos/${pid}/pasar-despacho`), onSuccess: inv }),
  }
}

export function useCancel(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: unknown) => api.post<Cancellation>(`/desarrollo/proyectos/${pid}/cancelar`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [Q, 'plan', pid] })
      qc.invalidateQueries({ queryKey: ['ventas', 'proyectos'] })
    },
  })
}

export function useCancellation(pid: string) {
  return useQuery({
    queryKey: [Q, 'cancelacion', pid],
    queryFn: () => api.get<Cancellation | null>(`/desarrollo/proyectos/${pid}/cancelacion`),
    enabled: !!pid,
    retry: false,
  })
}

// --- Adjuntos ---

export interface Attachment {
  id: string
  entidad_tipo: string
  entidad_id: string
  nombre: string
  mime: string
  tamano: number
  fecha: string
}

export function useAttachments(tipo: string, entidadId: string) {
  return useQuery({
    queryKey: [Q, 'adjuntos', tipo, entidadId],
    queryFn: () => api.get<Attachment[]>(`/desarrollo/adjuntos/${tipo}/${entidadId}`),
    enabled: !!entidadId,
    retry: false,
  })
}

export function useUploadAttachment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ tipo, entidadId, file }: { tipo: string; entidadId: string; file: File }) => {
      const fd = new FormData()
      fd.append('file', file)
      return api.post<Attachment>(`/desarrollo/adjuntos/${tipo}/${entidadId}`, fd)
    },
    onSuccess: (_d, vars) =>
      qc.invalidateQueries({ queryKey: [Q, 'adjuntos', vars.tipo, vars.entidadId] }),
  })
}

export function attachmentUrl(id: string): string {
  return `/api/desarrollo/adjuntos/${id}/descargar`
}

// --- Catálogo de usuarios para asignar ---

export interface Usuario {
  id: string
  nombre: string
  departamento: string
}

export function useUsuarios() {
  return useQuery({
    queryKey: ['auth', 'usuarios'],
    queryFn: () => api.get<Usuario[]>('/auth/usuarios'),
    retry: false,
  })
}
