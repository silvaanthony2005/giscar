import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

export interface ResultadoBusqueda {
  tipo: string
  id: string
  titulo: string
  subtitulo: string | null
  codigo: string | null
}

export interface Busqueda {
  consulta: string
  /** Categorías que este usuario tiene permitido buscar. */
  tipos: string[]
  resultados: Record<string, ResultadoBusqueda[]>
}

/** Mínimo que acepta el backend; debajo de esto no se dispara la consulta. */
export const MINIMA_LONGITUD = 2

/**
 * Búsqueda global. El filtrado lo hace el backend (AGENTS.md: filtrar es
 * lógica de negocio); aquí solo se pinta lo que devuelve.
 */
export function useBuscar(consulta: string) {
  const limpia = consulta.trim()
  return useQuery({
    queryKey: ['buscar', limpia],
    queryFn: () => api.get<Busqueda>(`/buscar?q=${encodeURIComponent(limpia)}`),
    enabled: limpia.length >= MINIMA_LONGITUD,
    staleTime: 15_000,
    retry: false,
    placeholderData: keepPreviousData,
  })
}
