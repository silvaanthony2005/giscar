import { useAuthStore } from '../../entities/auth/store'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = useAuthStore.getState().token
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let res: Response
  try {
    res = await fetch(`/api${path}`, { ...init, headers })
  } catch {
    // fetch solo falla así cuando no hay red/servidor; el cuerpo no existe que leer
    throw new ApiError(0, 'No hay conexión con el servidor')
  }

  // Un 401 sin token no es sesión expirada: son credenciales inválidas (login).
  if (res.status === 401 && token) {
    useAuthStore.getState().clear()
    throw new ApiError(401, 'Sesión expirada')
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const msg = body?.detail ?? `Error ${res.status}`
    throw new ApiError(res.status, typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body instanceof FormData ? body : JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

const nombreDesdeDisposition = (h: string | null): string | null => {
  const estrella = h?.match(/filename\*=UTF-8''([^;]+)/i)
  if (estrella) return decodeURIComponent(estrella[1])
  const simple = h?.match(/filename="?([^";]+)"?/i)
  return simple ? simple[1] : null
}

/**
 * Descarga un archivo autenticado. El navegador no envía el header
 * Authorization en un `<a href>`, así que el binario se trae con fetch
 * (con el mismo manejo de sesión y errores que el resto de la API) y la
 * descarga se dispara desde un blob.
 */
export async function descargar(url: string): Promise<void> {
  const token = useAuthStore.getState().token
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  })
  if (res.status === 401) {
    useAuthStore.getState().clear()
    throw new ApiError(401, 'Sesión expirada')
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const msg = body?.detail ?? `Error ${res.status}`
    throw new ApiError(res.status, typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  const blobUrl = URL.createObjectURL(await res.blob())
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = nombreDesdeDisposition(res.headers.get('content-disposition')) ?? 'archivo'
  a.click()
  URL.revokeObjectURL(blobUrl)
}
