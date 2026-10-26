import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'
import type { Invoice } from './api'

export interface DespachoProyecto {
  id: string
  codigo: string
  titulo: string
  monto_total: number
  estado_ventas: string
  estado_desarrollo: string
  estado_despacho: string
  acciones: string[]
  cliente: string
  pagado: number
  saldo: number
  entrega: unknown | null
  negacion: unknown | null
}

export interface DespachoDetalle {
  id: string
  codigo: string
  titulo: string
  monto_total: number
  estado_ventas: string
  estado_desarrollo: string
  estado_despacho: string
  acciones: string[]
  cliente: {
    id: string
    nombre: string
    telefono?: string | null
    email?: string | null
    direccion?: string | null
  }
  contacto_nombre: string
  contacto_telefono?: string | null
  contacto_email?: string | null
  contacto_direccion?: string | null
  pagado: number
  saldo: number
  por_pagado: number
  pagos: { id: string; monto: number; porcentaje: number; tipo: string; metodo_pago: string; fecha: string }[]
  /** Facturas de anticipo (Ventas) y de liquidación (Despacho). */
  facturas: Invoice[]
  entrega: {
    fecha_entrega: string
    hora_entrega?: string | null
    destinatario: string
    detalle_entregado: string
    notas?: string | null
  } | null
  negacion: { motivo: string; detalle: string; fecha: string } | null
}

/** Columnas del tablero: el backend decide quién va en cada una. */
export interface DespachoTablero {
  pendientes: DespachoProyecto[]
  cerrados: DespachoProyecto[]
}

const Q = 'despacho'

export function useDespachoProyectos() {
  return useQuery({
    queryKey: [Q, 'proyectos'],
    queryFn: () => api.get<DespachoTablero>(`/despacho/proyectos`),
  })
}

export function useDespachoProyecto(pid: string) {
  return useQuery({
    queryKey: [Q, 'proyecto', pid],
    queryFn: () => api.get<DespachoDetalle>(`/despacho/proyectos/${pid}`),
    enabled: !!pid,
  })
}

function useRefresh(pid?: string) {
  const qc = useQueryClient()
  return () => {
    qc.invalidateQueries({ queryKey: [Q, 'proyectos'] })
    if (pid) qc.invalidateQueries({ queryKey: [Q, 'proyecto', pid] })
    // Ventas y el panel leen el mismo proyecto: hay que refrescarlos también
    qc.invalidateQueries({ queryKey: ['ventas'] })
    qc.invalidateQueries({ queryKey: ['panel', 'contadores'] })
  }
}

export function useLiquidar(pid: string) {
  const refresh = useRefresh(pid)
  return useMutation({
    mutationFn: (body: { metodo_pago: string; notas?: string | null }) =>
      api.post(`/despacho/proyectos/${pid}/liquidar`, body),
    onSuccess: refresh,
  })
}

export function useEntregar(pid: string) {
  const refresh = useRefresh(pid)
  return useMutation({
    mutationFn: (body: unknown) => api.post(`/despacho/proyectos/${pid}/confirmar-entrega`, body),
    onSuccess: refresh,
  })
}

export function useNegar(pid: string) {
  const refresh = useRefresh(pid)
  return useMutation({
    mutationFn: (body: { motivo: string; detalle: string }) =>
      api.post(`/despacho/proyectos/${pid}/negar`, body),
    onSuccess: refresh,
  })
}

export function useResolverNegacion(pid: string) {
  const refresh = useRefresh(pid)
  return useMutation({
    mutationFn: () => api.post(`/despacho/proyectos/${pid}/resolver-negacion`),
    onSuccess: refresh,
  })
}

export function useSetEstadoDespacho(pid: string) {
  const refresh = useRefresh(pid)
  return useMutation({
    mutationFn: (target: string) => api.post(`/despacho/proyectos/${pid}/estado`, { target }),
    onSuccess: refresh,
  })
}
