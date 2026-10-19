import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
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
  /** Estado del proyecto según el backend (lo pinta la guía de progreso). */
  estado_desarrollo: string
  /** True solo mientras el proyecto está en desarrollo (lo decide el backend). */
  puede_registrar_avance: boolean
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

/**
 * Refresca todo lo que una acción de Desarrollo toca: el detalle del proyecto,
 * su tablero y las listas de los demás departamentos (el estado del proyecto es
 * compartido). Se `await` en el `onSuccess` de cada mutación para que el botón
 * siga en "cargando" hasta que la interfaz pinte el estado nuevo, y el usuario
 * no tenga que refrescar la página para verlo.
 */
async function refrescar(qc: QueryClient, pid: string, planSolo = false) {
  const claves: string[][] = planSolo
    ? [
        [Q, 'plan', pid],
        [Q, 'acciones', pid],
      ]
    : [
        [Q, 'plan', pid],
        [Q, 'acciones', pid],
        [Q, 'cancelacion', pid],
        [Q, 'tablero'],
        ['ventas', 'proyectos'],
        ['ventas', 'proyecto', pid],
        ['despacho', 'proyectos'],
        ['panel', 'contadores'],
      ]
  await Promise.all(claves.map((queryKey) => qc.invalidateQueries({ queryKey })))
}

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
    queryFn: () =>
      api.get<{ acciones: string[]; estado_desarrollo: string }>(
        `/desarrollo/proyectos/${pid}/acciones`,
      ),
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
    onSuccess: () => refrescar(qc, pid),
  })
}

export function usePhaseAction(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ fid, target }: { fid: string; target: string }) =>
      api.post(`/desarrollo/proyectos/${pid}/fases/${fid}/estado`, { target }),
    onSuccess: () => refrescar(qc, pid, true),
  })
}

export function useRecordProgress(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: unknown) => api.post<Progress>(`/desarrollo/proyectos/${pid}/avance`, body),
    onSuccess: () => refrescar(qc, pid, true),
  })
}

export function useProjectActions(pid: string) {
  const qc = useQueryClient()
  const despues = () => refrescar(qc, pid)
  return {
    iniciar: useMutation({
      mutationFn: () => api.post(`/desarrollo/proyectos/${pid}/iniciar`),
      onSuccess: despues,
    }),
    completar: useMutation({
      mutationFn: () => api.post(`/desarrollo/proyectos/${pid}/completar`),
      onSuccess: despues,
    }),
    pasarDespacho: useMutation({
      mutationFn: () => api.post(`/desarrollo/proyectos/${pid}/pasar-despacho`),
      onSuccess: despues,
    }),
  }
}

export interface CatalogoUsuario {
  id: string
  nombre: string
  departamento: string
}

/** Usuarios activos que Desarrollo puede asignar (lo lista el backend). */
export function useCatalogoUsuarios() {
  return useQuery({
    queryKey: [Q, 'catalogo-usuarios'],
    queryFn: () => api.get<CatalogoUsuario[]>('/desarrollo/catalogo-usuarios'),
    staleTime: 60_000,
    retry: false,
  })
}

export function useAsignarMiembros(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (user_ids: string[]) =>
      api.post<Member[]>(`/desarrollo/proyectos/${pid}/miembros`, { user_ids }),
    onSuccess: () => refrescar(qc, pid, true),
  })
}

export function useQuitarMiembro(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (mid: string) => api.delete(`/desarrollo/proyectos/${pid}/miembros/${mid}`),
    onSuccess: () => refrescar(qc, pid, true),
  })
}

export function useCancel(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: unknown) => api.post<Cancellation>(`/desarrollo/proyectos/${pid}/cancelar`, body),
    onSuccess: () => refrescar(qc, pid),
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
