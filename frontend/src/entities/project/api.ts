import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

export interface Customer {
  id: string
  nombre: string
  /** Persona de contacto responsable de la empresa. */
  representante: string | null
  documento: string | null
  telefono: string | null
  email: string | null
  direccion: string | null
  notas: string | null
  created_at: string
}

export interface Project {
  id: string
  codigo: string
  titulo: string
  descripcion_detallada: string
  customer_id: string
  monto_total: number
  /** Sumado por el backend; el frontend no suma pagos. */
  pagado: number
  /** Saldo restante calculado por el backend. */
  saldo: number
  contacto_nombre: string
  contacto_telefono: string | null
  contacto_email: string | null
  contacto_direccion: string | null
  estado_ventas: string
  estado_desarrollo: string
  estado_despacho: string
  acciones: string[]
  created_at: string
  updated_at: string
}

export interface Payment {
  id: string
  project_id: string
  monto: number
  porcentaje: number
  tipo: string
  metodo_pago: string
  notas: string | null
  fecha: string
}

export interface Invoice {
  id: string
  numero: string
  project_id: string
  monto: number
  porcentaje: number
  metodo_pago: string
  descripcion: string
  emitida_en: string
}

const Q = 'ventas'

export function useCustomers() {
  return useQuery({ queryKey: [Q, 'clientes'], queryFn: () => api.get<Customer[]>('/ventas/clientes') })
}

export function useCreateCustomer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: unknown) => api.post<Customer>('/ventas/clientes', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: [Q, 'clientes'] }),
  })
}

export function useUpdateCustomer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: unknown }) =>
      api.patch<Customer>(`/ventas/clientes/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: [Q, 'clientes'] }),
  })
}

export function useDeleteCustomer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete<void>(`/ventas/clientes/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [Q, 'clientes'] }),
  })
}

export function useProjects() {
  return useQuery({ queryKey: [Q, 'proyectos'], queryFn: () => api.get<Project[]>('/ventas/proyectos') })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: [Q, 'proyecto', id],
    queryFn: () => api.get<Project>(`/ventas/proyectos/${id}`),
    enabled: !!id,
  })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: unknown) => api.post<Project>('/ventas/proyectos', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: [Q, 'proyectos'] }),
  })
}

export function usePayments(pid: string) {
  return useQuery({
    queryKey: [Q, 'pagos', pid],
    queryFn: () => api.get<Payment[]>(`/ventas/proyectos/${pid}/pagos`),
    enabled: !!pid,
  })
}

export function useCreatePayment(pid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: unknown) => api.post<Payment>(`/ventas/proyectos/${pid}/pagos`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [Q, 'pagos', pid] })
      qc.invalidateQueries({ queryKey: [Q, 'facturas', pid] })
      qc.invalidateQueries({ queryKey: [Q, 'proyectos'] })
      qc.invalidateQueries({ queryKey: [Q, 'proyecto', pid] })
    },
  })
}

export function useSendToDesarrollo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (pid: string) => api.post<Project>(`/ventas/proyectos/${pid}/pasar-desarrollo`),
    onSuccess: async (_data, pid) => {
      // El proyecto entra en el tablero de Desarrollo: hay que refrescarlo ya.
      await Promise.all([
        qc.invalidateQueries({ queryKey: [Q, 'proyectos'] }),
        qc.invalidateQueries({ queryKey: [Q, 'proyecto', pid] }),
        qc.invalidateQueries({ queryKey: ['desarrollo', 'tablero'] }),
        qc.invalidateQueries({ queryKey: ['panel', 'contadores'] }),
      ])
    },
  })
}

export function useInvoices(pid: string) {
  return useQuery({
    queryKey: [Q, 'facturas', pid],
    queryFn: () => api.get<Invoice[]>(`/ventas/proyectos/${pid}/facturas`),
    enabled: !!pid,
  })
}

export function invoicePdfUrl(id: string): string {
  return `/api/ventas/facturas/${id}/pdf`
}
