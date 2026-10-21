const currency = new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP' })

export const formatMoney = (v: number): string => currency.format(v)

export const formatDate = (iso: string): string =>
  new Date(iso).toLocaleDateString('es-DO', { day: '2-digit', month: 'short', year: 'numeric' })

export const formatDateTime = (iso: string): string =>
  new Date(iso).toLocaleString('es-DO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

export const DEPARTAMENTOS: Record<string, string> = {
  ventas: 'Ventas',
  desarrollo: 'Producción',
  despacho: 'Despacho',
  tecnologia: 'Tecnología',
  rrhh: 'Recursos Humanos',
}

export const PRIORIDADES: Record<string, string> = {
  baja: 'Baja',
  media: 'Media',
  alta: 'Alta',
  critica: 'Crítica',
}
