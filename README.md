# GCISCAR

Sistema de información interno para empleados (25–100 usuarios), corriendo en **una sola PC local**, sin exposición a internet. Gestiona proyectos de punta a punta:

| Departamento | Qué hace |
|---|---|
| **Ventas** | Levantamiento de cliente/proyecto, cobro 50 % / 100 %, emisión de factura PDF |
| **Desarrollo** | Plan con fases y personas, seguimiento de avance, adjuntos, cancelación con informe |
| **Despacho** | Cobro del saldo restante, confirmación de entrega, negación y resolución |
| **Tecnología** | Cola de incidencias de hardware/electrónicas ordenada por prioridad + llegada, resolución con informe y evidencia fotográfica |
| **RRHH** | Panel global de solo lectura, alta/bloqueo/reasignación de usuarios, bitácora |

> Requisitos originales del cliente: [`readme.md`](readme.md)
> Decisiones técnicas y convenciones obligatorias: [`AGENTS.md`](AGENTS.md)

---

## Claves de acceso

### Cuentas semilla

Todas las cuentas iniciales comparten **la misma contraseña**:

```
giscar1234
```

| Departamento | Correo | Nombre | Rol |
|---|---|---|---|
| RRHH | `rrhh@giscar.com` | Ana Reyes | Admin (lectura global + usuarios) |
| Ventas | `ventas@giscar.com` | Luis Pérez | Ventas |
| Desarrollo | `desarrollo@giscar.com` | Marta Gómez | Desarrollo |
| Despacho | `despacho@giscar.com` | Carlos Díaz | Despacho |
| Tecnología | `tecnologia@giscar.com` | Sofía López | Tecnología |

Se crean con:

```bash
cd backend && uv run python -m app.infrastructure.db.seed
```

El seed es **idempotente**: si la cuenta ya existe no la vuelve a crear.

> ⚠️ **Cambien estas claves en producción.** Están en `backend/app/infrastructure/db/seed.py` (`SEED_PASSWORD`) y son solo para arrancar el sistema.

### Secreto JWT

| Variable | Valor por defecto |
|---|---|
| `GISCAR_JWT_SECRET` | `giscar-local-dev-secret-change-me-32bytes-min` |

**Obligatorio cambiarlo** antes de usar el sistema en serio. Ver [Configuración](#configuración).

---

## Requisitos

- **Python ≥ 3.12** + [`uv`](https://docs.astral.sh/uv/) (`uv --version`)
- **Node.js ≥ 20** + npm

---

## Comandos de lanzamiento

### Atajos desde la raíz del repo

Hay un `package.json` en la raíz que delega en `frontend/` y `backend/`, así que
**no hace falta cambiar de carpeta**:

```bash
npm run dev     # frontend (Vite)        → http://127.0.0.1:5173
npm run api     # backend (Uvicorn)      → http://127.0.0.1:8000
npm run build   # typecheck + bundle (frontend)
npm run lint    # oxlint (frontend) + ruff (backend)
npm run fmt     # ruff format (backend)
npm run test    # pytest (backend)
npm run check   # build + lint + tests (todo de una vez)
```

Necesitas **dos terminales**: una para `npm run api` y otra para `npm run dev`.

### 1. Primera instalación

```bash
# Backend: crea el entorno virtual e instala dependencias
cd backend && uv sync

# Frontend: instala dependencias
cd ../frontend && npm install
```

### 2. Arrancar en desarrollo (dos terminales)

```bash
# Terminal 1 — API en http://127.0.0.1:8000
npm run api

# Terminal 2 — Frontend en http://127.0.0.1:5173
npm run dev
```

Abrir **http://127.0.0.1:5173** y entrar con una de las cuentas de arriba.

> En desarrollo, Vite hace de proxy: las llamadas a `/api/*` se reenvían al puerto 8000.

Equivalente con los comandos "largos" (si prefieres las carpetas):

```bash
# Terminal 1
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

### 3. Arrancar en producción (PC local, un solo proceso)

```bash
# 1. Construir el frontend
cd frontend && npm run build

# 2. Arrancar el backend (sirve la API y el frontend ya compilado)
cd ../backend
uv run giscar-backend
```

Abrir **http://127.0.0.1:8000** — la app completa se sirve desde ahí.

Alternativa con uvicorn directamente:

```bash
cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

El backend monta `frontend/dist` automáticamente y añade un *fallback* SPA, así que recargar rutas como `/ventas` o `/rrhh/usuarios` funciona sin recargar el servidor.

---

## Comandos de verificación

Ejecutar **antes de dar por terminado cualquier cambio**:

```bash
# Todo de una vez (desde la raíz)
npm run check

# O por separado
npm run build    # typecheck + bundle (frontend)
npm run lint     # oxlint (frontend) + ruff (backend)
npm run test     # pytest (backend)
```

Estado esperado: **110 passed**, ruff y oxlint sin errores, build correcto.

---

## Configuración

Todas las variables usan el prefijo `GISCAR_` y pueden ir en un archivo `backend/.env` o en el entorno (ver `backend/app/config.py`):

| Variable | Por defecto | Descripción |
|---|---|---|
| `GISCAR_JWT_SECRET` | *(valor de desarrollo)* | **Cambiar.** Secreto para firmar los tokens. Mínimo 32 bytes. |
| `GISCAR_DATABASE_URL` | `sqlite:///backend/giscar.db` | Base de datos SQLite (modo WAL) |
| `GISCAR_UPLOADS_DIR` | `backend/uploads/` | Almacenamiento de adjuntos y evidencias |
| `GISCAR_ACCESS_TOKEN_MINUTES` | `480` (8 h) | Duración del token de sesión |
| `GISCAR_CORS_ORIGINS` | `http://127.0.0.1:5173, http://localhost:5173` | Orígenes permitidos en desarrollo |
| `GISCAR_MAX_UPLOAD_MB` | `20` | Tamaño máximo por archivo adjunto |

Ejemplo de `backend/.env`:

```env
GISCAR_JWT_SECRET=cambien-esto-por-una-clave-larga-y-aleatoria-de-32-bytes-o-mas
GISCAR_ACCESS_TOKEN_MINUTES=480
```

---

## Reiniciar la base de datos

```bash
cd backend
rm -f giscar.db giscar.db-wal giscar.db-shm
uv run python -m app.infrastructure.db.seed
```

Esto borra **todos** los datos (clientes, proyectos, pagos, incidencias), recrea el esquema completo (16 tablas) y las 5 cuentas semilla.

---

## API

El backend expone OpenAPI/Swagger interactivo:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

Todas las rutas van bajo `/api/...` y usan **Bearer token**. Para probarlas desde Swagger:

1. Obtener el token:

   ```bash
   curl -s -X POST http://127.0.0.1:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"ventas@giscar.com","password":"giscar1234"}'
   ```

2. Copiar el valor de `access_token` y pegarlo en **Authorize → Bearer** en http://127.0.0.1:8000/docs (sin la palabra `Bearer`, solo el token).

> El token caduca a las **8 horas** por defecto.

---

## Estructura del proyecto

```
backend/
  app/
    domain/           # PURO: modelos frozen, servicios, tipos Result (sin FastAPI/SQLAlchemy)
      shared/         #   Result, Money, state_machine, HOFs
      user/ customer/ project/ payment/ invoice/
      development/ dispatch/ incidence/ attachment/ audit/
    application/      # casos de uso (vacío por ahora; los routers llaman al dominio)
    infrastructure/   # routers FastAPI, SQLAlchemy, seguridad, storage
    main.py           # punto de entrada
  tests/              # tests de dominio puro
  giscar.db           # SQLite local (regenerable)

frontend/src/
  atoms/ molecules/ organisms/ templates/ pages/   # Atom Design
  entities/ shared/ app/
```

---

## Diseño de interfaz

El aspecto visual sale del proyecto de Stitch **"Enterprise Information System UI"**, pero
del diseño **solo se extrajo el _design system_** (paleta, tipografía, espaciado, radios y
sombras); el HTML de sus pantallas no se copia. Todo se reconstruye con componentes
reutilizables del Atom Design:

| Pieza | Dónde |
|---|---|
| Tokens M3 (colores, tipos, spacing, radios, sombras) | `frontend/src/index.css` → `@theme` |
| Iconos Material Symbols | `frontend/src/atoms/Icon.tsx` (fuente en `public/fonts/`) |
| `Tooltip`, `Badge`, `Button`, `Card`, `Input`, `Select`, `Textarea` | `frontend/src/atoms/` |
| `EstadoBadge`, `Modal`, `SectionHeader` | `frontend/src/molecules/` |
| `DataTable`, `Feedback`, `AdjuntosPanel` | `frontend/src/organisms/` |
| `TopBar`, `Sidebar`, `PageHeader`, `DashboardLayout` | `frontend/src/templates/` |
| Configuración de navegación (iconos y rutas por rol) | `frontend/src/shared/lib/nav.ts` |

---

## Notas importantes

- **El frontend no calcula nada.** Totales, saldos, transiciones de estado, permisos **y las columnas de los tableros** los decide el backend; cada proyecto expone un campo `acciones` con las operaciones válidas, y la interfaz solo las pinta. Detalle en [`AGENTS.md`](AGENTS.md).
- **Las fuentes están auto-hospedadas** en `frontend/public/fonts/` (Inter, JetBrains Mono y Material Symbols). No se descarga nada de internet en ejecución, así la app funciona en la PC local sin conexión.
- **Los adjuntos usan el mismo permiso para subir, listar y descargar.** Cualquiera de los cuatro departamentos operativos (Ventas, Desarrollo, Despacho, Tecnología) que sube evidencia puede verla y bajarla; RRHH tiene acceso global por diseño. El servidor valida MIME y tamaño (`GISCAR_MAX_UPLOAD_MB`).
- **Facturación solo interna:** no integra pasarelas de pago; genera registros y facturas PDF con reportlab.
- **Documentos del usuario** (facturas, reportes, adjuntos) se generan en el servidor, nunca en el navegador.
- El directorio `uploads/` es *runtime* y está ignorado por git.

---

## Qué NO se versiona

El [`.gitignore`](.gitignore) excluye, entre otros:

| Ruta | Motivo |
|---|---|
| `backend/giscar.db*` | Datos reales de la PC local |
| `backend/uploads/` | Adjuntos y evidencias de usuarios |
| `backend/.env`, `.env` | Contiene `GISCAR_JWT_SECRET` |
| `backend/.venv/` | Entorno virtual |
| `frontend/dist/`, `node_modules/` | Artefactos de build |

Antes de hacer `git add .`, comprueba que nada sensible se escapa:

```bash
git add -An --dry-run | grep -Ei "\.db|uploads/|\.env|\.venv|node_modules|dist/"
```
