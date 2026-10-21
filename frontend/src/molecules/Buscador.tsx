import { useEffect, useId, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useBuscar, MINIMA_LONGITUD } from '../entities/search/api'
import type { ResultadoBusqueda } from '../entities/search/api'
import type { Departamento } from '../entities/auth/types'
import { Icon } from '../atoms/Icon'
import { TIPO_BUSQUEDA, rutaResultado } from '../shared/lib/nav'
import { DEPARTAMENTOS } from '../shared/lib/format'

const DEBOUNCE_MS = 300

interface Props {
  departamento: Departamento
}

/**
 * Búsqueda global del TopBar.
 *
 * El backend decide qué puede buscar cada departamento y devuelve las
 * coincidencias ya filtradas; aquí solo hay estado de interfaz (input abierto,
 * texto escrito) y la petición diferida para no saturar el servidor.
 */
export function Buscador({ departamento }: Props) {
  const navigate = useNavigate()
  const id = useId()
  const [texto, setTexto] = useState('')
  const [debounce, setDebounce] = useState('')
  const [abierto, setAbierto] = useState(false)
  const raiz = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const t = setTimeout(() => setDebounce(texto), DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [texto])

  useEffect(() => {
    if (!abierto) return
    const fuera = (e: PointerEvent) => {
      if (!raiz.current?.contains(e.target as Node)) setAbierto(false)
    }
    const esc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setAbierto(false)
    }
    document.addEventListener('pointerdown', fuera)
    document.addEventListener('keydown', esc)
    return () => {
      document.removeEventListener('pointerdown', fuera)
      document.removeEventListener('keydown', esc)
    }
  }, [abierto])

  const { data, isFetching, error } = useBuscar(debounce)
  const grupos = Object.entries(data?.resultados ?? {})
  const total = grupos.reduce((n, [, xs]) => n + xs.length, 0)
  const corta = debounce.trim().length < MINIMA_LONGITUD

  const irA = (r: ResultadoBusqueda) => {
    const ruta = rutaResultado(r.tipo, r.id, departamento)
    if (ruta) {
      navigate(ruta)
      setAbierto(false)
      setTexto('')
    }
  }

  return (
    <div ref={raiz} className="relative hidden w-full max-w-xl md:block">
      <div className="relative flex items-center">
        <Icon
          name="search"
          size="sm"
          className="pointer-events-none absolute left-space-md text-outline"
        />
        <input
          id={id}
          type="search"
          role="combobox"
          aria-expanded={abierto}
          aria-controls={`${id}-resultados`}
          aria-autocomplete="list"
          autoComplete="off"
          placeholder="Buscar proyectos, clientes, incidencias o personal…"
          value={texto}
          onChange={(e) => {
            setTexto(e.target.value)
            setAbierto(true)
          }}
          onFocus={() => setAbierto(true)}
          className={`h-10 w-full rounded-lg pr-space-md pl-11 text-body-md text-on-surface transition-all duration-150 placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-secondary/20 ${
            abierto
              ? 'bg-surface-container-lowest shadow-hairline'
              : 'bg-surface-container-low'
          }`}
        />
      </div>

      {abierto && (
        <div
          id={`${id}-resultados`}
          role="listbox"
          className="absolute inset-x-0 top-12 z-50 max-h-96 overflow-y-auto rounded-xl bg-surface-container-lowest p-space-xs shadow-pop"
        >
          {corta ? (
            <p className="px-space-md py-space-sm text-body-md text-on-surface-variant">
              Escribe al menos {MINIMA_LONGITUD} caracteres para buscar en{' '}
              {(data?.tipos ?? []).length > 0
                ? data?.tipos.map((t) => TIPO_BUSQUEDA[t]?.label ?? t).join(', ')
                : 'tus módulos'}
              .
            </p>
          ) : error ? (
            <p className="px-space-md py-space-sm text-body-md text-on-error-container">
              {(error as Error).message}
            </p>
          ) : total === 0 && !isFetching ? (
            <p className="px-space-md py-space-sm text-body-md text-on-surface-variant">
              Sin resultados para «{debounce.trim()}».
            </p>
          ) : (
            grupos.map(([tipo, items]) => (
              <div key={tipo} className="py-space-2xs">
                <p className="px-space-md py-space-xs text-label-sm font-semibold tracking-wide text-on-surface-variant uppercase">
                  {TIPO_BUSQUEDA[tipo]?.label ?? tipo}
                </p>
                {items.map((r) => (
                  <button
                    key={`${r.tipo}-${r.id}`}
                    type="button"
                    role="option"
                    onClick={() => irA(r)}
                    className="flex w-full items-center gap-space-md rounded-lg px-space-md py-space-sm text-left transition-colors hover:bg-surface-container-low"
                  >
                    <Icon
                      name={TIPO_BUSQUEDA[tipo]?.icon ?? 'search'}
                      size="sm"
                      className="shrink-0 text-outline"
                    />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-body-md text-on-surface">
                        {r.titulo}
                      </span>
                      {r.subtitulo && (
                        <span className="block truncate text-label-sm text-on-surface-variant">
                          {r.subtitulo}
                        </span>
                      )}
                    </span>
                    {r.codigo && (
                      <span className="shrink-0 rounded bg-surface-container px-space-xs py-0.5 font-code-sm text-code-sm text-on-surface-variant">
                        {r.codigo}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            ))
          )}

          {total > 0 && (
            <p className="border-t border-outline-variant/60 px-space-md py-space-xs text-label-sm text-on-surface-variant">
              Buscando en {data?.tipos.map((t) => DEPARTAMENTOS[t as Departamento] ?? t).join(', ')}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
