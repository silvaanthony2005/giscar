import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon } from '../../atoms/Icon'
import { Input } from '../../atoms/Input'
import { login } from '../../entities/auth/api'
import { useAuthStore } from '../../entities/auth/store'
import type { Departamento } from '../../entities/auth/types'
import { DEPARTAMENTO_DESCRIPCION, DEPARTAMENTO_ICONS } from '../../shared/lib/nav'
import { DEPARTAMENTOS } from '../../shared/lib/format'

/**
 * Directorio de accesos: al elegir un departamento se precarga su correo.
 * Son direcciones fijas de la siembra local (sin contraseñas en el bundle).
 */
const ACCESOS: Departamento[] = ['ventas', 'desarrollo', 'despacho', 'tecnologia', 'rrhh']
// El módulo se llama Producción, pero la clave del departamento sigue siendo
// 'desarrollo' (así están guardados los usuarios): solo cambia el correo.
const correoDe = (d: Departamento): string => `${d === 'desarrollo' ? 'produccion' : d}@giscar.com`

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [verPassword, setVerPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await login(email, password)
      setAuth(res.access_token, res.user)
      navigate('/panel')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error de conexión')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-full w-full items-center justify-center bg-background p-space-lg">
      <div className="w-full max-w-5xl">
        {/* Encabezado de marca */}
        <div className="mb-space-lg flex flex-col items-center text-center">
          <div className="relative mb-space-xs flex size-20 items-center justify-center rounded-xl bg-surface-container-lowest p-2 shadow-raised">
            <Icon name="hub" size="xl" className="text-primary" />
            <span className="absolute -bottom-1 -right-1 flex size-5 items-center justify-center rounded-full bg-secondary shadow-hairline">
              <Icon name="verified_user" size="sm" className="text-[12px] text-on-secondary" />
            </span>
          </div>
          <div className="mb-space-xs flex items-center gap-space-sm">
            <span className="font-code-sm text-code-sm font-semibold uppercase tracking-wider text-secondary">
              GCISCAR v1.0
            </span>
            <span className="size-1.5 rounded-full bg-outline-variant" />
            <span className="text-label-sm font-medium text-on-surface-variant">
              Acceso centralizado
            </span>
          </div>
          <h1 className="text-display-lg-mobile text-primary tracking-tight">GCISCAR</h1>
          <p className="mt-1 text-title-lg text-on-surface-variant">
            Sistema de información interno
          </p>
        </div>

        {/* Tarjeta partida: formulario | directorio */}
        <div className="grid grid-cols-1 overflow-hidden rounded-xl bg-surface-container-lowest shadow-pop lg:grid-cols-12">
          {/* Formulario */}
          <div className="flex flex-col justify-between p-8 sm:p-10 lg:col-span-7">
            <div>
              <div className="mb-space-lg flex items-center justify-between rounded-lg bg-surface-container-low px-space-md py-space-sm">
                <span className="flex items-center gap-space-sm">
                  <Icon name="shield" className="text-secondary" filled />
                  <span className="text-title-md font-semibold text-primary">
                    Credenciales corporativas
                  </span>
                </span>
                <span className="rounded bg-surface-container px-space-xs py-0.5 font-code-sm text-code-sm text-on-surface-variant">
                  LOCAL_AUTH
                </span>
              </div>

              <form onSubmit={onSubmit} className="space-y-space-lg">
                <Input
                  id="email"
                  type="email"
                  label="Correo electrónico"
                  icon="alternate_email"
                  placeholder="usuario@giscar.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="username"
                />

                <Input
                  id="password"
                  type={verPassword ? 'text' : 'password'}
                  label="Contraseña"
                  icon="lock"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  trailing={
                    <button
                      type="button"
                      onClick={() => setVerPassword((v) => !v)}
                      aria-label={verPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                      className="flex size-8 items-center justify-center rounded transition-colors hover:bg-surface-container hover:text-on-surface"
                    >
                      <Icon name={verPassword ? 'visibility_off' : 'visibility'} size="sm" />
                    </button>
                  }
                />

                {error && (
                  <p role="alert" className="text-body-sm text-error">
                    {error}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="flex h-12 w-full items-center justify-center gap-space-sm rounded-lg bg-primary text-title-md text-on-primary shadow-raised transition-colors duration-200 hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading ? (
                    <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  ) : (
                    <>
                      <span>Iniciar sesión</span>
                      <Icon name="arrow_forward" size="sm" />
                    </>
                  )}
                </button>
              </form>
            </div>

            <div className="mt-space-lg flex items-center justify-between rounded-lg bg-surface-container-low px-space-md py-space-sm text-on-surface-variant">
              <span className="flex items-center gap-space-sm">
                <Icon name="dns" size="sm" className="text-outline" />
                <span className="font-code-sm text-code-sm">Despliegue local</span>
              </span>
              <span className="flex items-center gap-space-sm">
                <span className="size-2 rounded-full bg-success" />
                <span className="text-label-sm font-semibold text-on-surface">Servicio activo</span>
              </span>
            </div>
          </div>

          {/* Directorio de accesos */}
          <div className="bg-surface-container-low p-8 lg:col-span-5">
            <div className="mb-space-md flex items-center justify-between">
              <span className="flex items-center gap-space-sm">
                <Icon name="switch_account" className="text-secondary" filled />
                <h2 className="text-title-lg text-primary">Accesos por departamento</h2>
              </span>
              <span className="rounded bg-surface-container px-space-xs py-0.5 text-label-sm font-medium text-on-surface-variant">
                Local
              </span>
            </div>
            <p className="mb-space-md text-body-sm text-on-surface-variant">
              Selecciona un departamento para precargar su correo. Cada usuario usa su propia
              contraseña.
            </p>

            <ul className="space-y-space-sm">
              {ACCESOS.map((d) => (
                <li key={d}>
                  <button
                    type="button"
                    onClick={() => {
                      setEmail(correoDe(d))
                      setVerPassword(false)
                    }}
                    className={`flex w-full items-center justify-between rounded-lg p-space-md text-left shadow-hairline transition-all hover:shadow-raised ${
                      email === correoDe(d)
                        ? 'bg-surface-container-high ring-2 ring-secondary/30'
                        : 'bg-surface-container-lowest'
                    }`}
                  >
                    <span className="flex min-w-0 items-center gap-space-md">
                      <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-surface-container-high text-secondary">
                        <Icon name={DEPARTAMENTO_ICONS[d]} size="sm" filled />
                      </span>
                      <span className="min-w-0">
                        <span className="block truncate text-title-md text-on-surface">
                          {DEPARTAMENTOS[d]}
                        </span>
                        <span className="block truncate text-label-sm text-on-surface-variant">
                          {DEPARTAMENTO_DESCRIPCION[d]}
                        </span>
                      </span>
                    </span>
                    <Icon
                      name={email === correoDe(d) ? 'check_circle' : 'radio_button_unchecked'}
                      size="sm"
                      className={
                        email === correoDe(d) ? 'shrink-0 text-secondary' : 'shrink-0 text-outline'
                      }
                      filled={email === correoDe(d)}
                    />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </main>
  )
}
