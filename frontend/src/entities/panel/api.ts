import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api/client'
import type { Departamento } from '../auth/types'

/**
 * Contadores de carga por departamento. Los calcula el backend; el frontend
 * solo los pinta (AGENTS.md — sin cuentas en la interfaz).
 *
 * Solo aparecen los departamentos que el usuario puede ver.
 */
export type Contadores = Partial<Record<Departamento, number>>

export function useContadores() {
  return useQuery({
    queryKey: ['panel', 'contadores'],
    queryFn: () => api.get<Contadores>('/panel/contadores'),
    staleTime: 30_000,
    retry: false,
  })
}
