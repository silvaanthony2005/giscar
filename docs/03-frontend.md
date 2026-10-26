# 03 · Frontend

## 1. Stack

| Pieza | Versión / uso |
|---|---|
| React | 19.2 |
| TypeScript | 6.0 (`tsc -b`) |
| Vite | 8.3 + `@vitejs/plugin-react` |
| Tailwind CSS | 4.3 (`@tailwindcss/vite`, tokens en `src/index.css`) |
| React Router | 7 (`BrowserRouter`, `Routes`, `NavLink`) |
| TanStack Query | 5 (estado servidor, caché, mutaciones) |
| Zustand | 5 + `persist` (sesión) |
| Linter | oxlint |
| Tests | **no configurados** |

`vite.config.ts`:

- puerto `5173`;
- proxy `/api → http://127.0.0.1:8000` para desarrollo;
- plugins React + Tailwind.

## 2. Organización Atom Design

```
frontend/src/
  atoms/        Icon, Button, IconButton, Input, Select, Textarea, Checkbox,
                Badge, Card, Tooltip
  molecules/    Buscador, EstadoBadge/PrioridadBadge, FlujoProyecto, Modal, SectionHeader
  organisms/    DataTable, Feedback (Loading/Error/Empty/StatCard), AdjuntosPanel
  templates/    TopBar, Sidebar, PageHeader, DashboardLayout
  pages/        auth, ventas, desarrollo, despacho, tecnologia, incidencias, rrhh
  entities/     auth, panel, project (api + hooks), search
  shared/       api/client.ts, lib/format.ts, lib/nav.ts
  app/          App.tsx (router), ProtectedRoute.tsx
  main.tsx      QueryClient + BrowserRouter
  index.css     design system M3
```

Flujo de composición: `index.css` define tokens → `atoms` los consumen → `molecules`
combinan átomos → `organisms` montan bloques → `templates` dan el layout → `pages`
orquestan datos y acciones.

## 3. Rutas

Definidas en `src/app/App.tsx`.

| Ruta | Página | Módulo |
|---|---|---|
| `/login` | `LoginPage` | Público (solo si no hay token) |
| `/` | redirect a `/panel` | — |
| `/panel` | redirect según departamento | — |
| `/ventas` | `ProyectosVentasPage` | Ventas |
| `/ventas/clientes` | `ClientesPage` | Ventas |
| `/ventas/proyectos/:id` | `DetalleProyectoVentasPage` | Ventas |
| `/desarrollo` | `ProyectosDesarrolloPage` | Producción |
| `/desarrollo/proyectos/:id` | `DetalleProyectoDesarrolloPage` | Producción |
| `/despacho` | `ColaDespachoPage` | Despacho |
| `/despacho/proyectos/:id` | `DetalleDespachoPage` | Despacho |
| `/tecnologia` | `ColaIncidenciasPage` | Tecnología |
| `/tecnologia/incidencias/:id` | `DetalleIncidenciaPage` | Tecnología |
| `/incidencias/nueva` | `ReportarIncidenciaPage` | Todos |
| `/rrhh` | `DashboardRRHHPage` | RRHH |
| `/rrhh/usuarios` | `UsuariosRRHHPage` | RRHH |
| `/rrhh/proyectos` | `ProyectosRRHHPage` | RRHH |
| `/rrhh/actividad` | `ActividadRRHHPage` | RRHH |
| `*` | redirect | — |

**Protección:** `ProtectedRoute` solo comprueba la existencia del token. **No hay guardas
por rol en el router**: la autorización real la aplica el backend en cada request. La UI
oculta navegación por departamento (`NAV`), pero escribir una URL de otro módulo renderiza
la página y las llamadas devuelven 403.

`PanelRedirect` mapea departamento → ruta inicial:

```
ventas → /ventas
desarrollo → /desarrollo
despacho → /despacho
tecnologia → /tecnologia
rrhh → /rrhh
```

## 4. Sesión y autenticación

`entities/auth/store.ts` (Zustand + `persist`, clave `giscar-auth` en `localStorage`):

```ts
token: string | null
user: User | null
setAuth(token, user)
clear()
```

- `LoginPage` llama `login(email, password)` → `POST /api/auth/login`, guarda token y
  usuario, navega a `/panel`.
- El directorio de accesos precarga el correo de cada departamento
  (`produccion@giscar.com` para `desarrollo`); **no** contiene contraseñas.
- `TopBar` permite cerrar sesión: limpia el store y navega a `/login`.
- No hay endpoint de logout en el backend; la auditoría define `logout` pero no se usa.

## 5. Cliente API

`shared/api/client.ts`:

- prefija `/api` a cada ruta;
- añade `Authorization: Bearer <token>` si hay sesión;
- `Content-Type: application/json` salvo `FormData`;
- 401 con token → limpia sesión y lanza `ApiError(401, 'Sesión expirada')`;
- 401 sin token (login) → propaga el error de credenciales;
- 204 → `undefined`; resto → JSON;
- error de red → `ApiError(0, 'No hay conexión con el servidor')`;
- `descargar(url)` trae el binario con `fetch` (porque un `<a href>` no envía Bearer),
  crea un blob y dispara la descarga con el nombre de `Content-Disposition`.

Métodos disponibles: `api.get/post/put/patch/delete`.

## 6. Estado del servidor (React Query)

`main.tsx` configura:

```ts
retry: 1
refetchOnWindowFocus: false
staleTime: 30_000
```

Claves principales:

| Clave | Datos |
|---|---|
| `['ventas', 'clientes']` | Clientes |
| `['ventas', 'proyectos']` / `['ventas', 'proyecto', id]` | Proyectos |
| `['ventas', 'pagos', pid]`, `['ventas', 'facturas', pid]` | Cobros/facturas |
| `['desarrollo', 'tablero']` | Columnas del tablero |
| `['desarrollo', 'plan', pid]`, `['desarrollo', 'acciones', pid]` | Plan/acciones |
| `['desarrollo', 'cancelacion', pid]` | Informe de cancelación |
| `['despacho', 'proyectos']`, `['despacho', 'proyecto', pid]` | Cola/detalle |
| `['tecnologia', 'cola']`, `['tecnologia', 'incidencia', id]` | Incidencias |
| `['rrhh', ...]` | Dashboard, actividad, proyectos, usuarios |
| `['panel', 'contadores']` | Contadores del sidebar |
| `['buscar', término]` | Búsqueda global |
| `['auth', 'usuarios']` | Catálogo de usuarios |

Tras una mutación se invalidan **todas** las claves afectadas (incluidas las de otros
departamentos), porque el estado del proyecto es compartido. Ejemplos:

- enviar a Producción invalida `ventas/proyectos`, `desarrollo/tablero` y
  `panel/contadores`;
- liquidar en Despacho invalida `despacho`, `ventas` y `panel`;
- acciones de Desarrollo invalidan plan, acciones, cancelación, tablero, ventas,
  despacho y contadores.

## 7. Principio de frontend pasivo

La UI **no calcula** reglas de negocio. El backend envía:

- `pagado`, `saldo`, `por_pagado` (Despacho);
- `acciones: string[]` por proyecto y por fase;
- tableros ya agrupados (`recibidos/en_curso/historial`,
  `pendientes/cerrados`);
- contadores del sidebar;
- KPIs de RRHH;
- resultados de búsqueda ya filtrados por rol.

La UI decide únicamente presentación:

- qué botón pintar según `acciones.includes(...)`;
- formato de moneda/fecha (`shared/lib/format.ts`, `Intl` es-DO, DOP);
- estado de modales, tabs, menús, debounce de búsqueda;
- validación HTML (`required`, `minLength`) como ayuda, nunca como fuente de verdad.

Excepciones menores (solo presentación): el buscador suma los resultados visibles para
mostrar “hay N coincidencias”, y `nav.ts` decide la URL de destino según `tipo`.

## 8. Navegación por rol

`shared/lib/nav.ts`:

| Departamento | Ítems |
|---|---|
| ventas | Proyectos · Clientes · Reportar incidencia |
| desarrollo | Proyectos · Reportar incidencia |
| despacho | Cola de entregas · Reportar incidencia |
| tecnologia | Incidencias |
| rrhh | Panel general · Usuarios · Proyectos · Bitácora · Reportar incidencia |

El sidebar de RRHH añade, además, un grupo por cada departamento (sin duplicar «Reportar
incidencia»), con contador cuando aplica.

Búsqueda global (`molecules/Buscador.tsx`):

- input en el TopBar (visible desde `md`);
- debounce 300 ms; consulta desde 2 caracteres;
- `GET /api/buscar?q=…`;
- resultados agrupados por tipo con icono y código;
- navegación según `rutaResultado(tipo, id, departamento)`; para cliente/usuario abre el
  listado porque no hay página de detalle.

## 9. Design system

Tokens en `index.css` bajo `@theme` (Tailwind 4):

- **Tipografía**: Inter (sans) y JetBrains Mono (código); escala M3
  `display-lg`, `headline-lg/md`, `title-lg/md`, `body-lg/md/sm`, `label-md/sm`,
  `code-sm`.
- **Color**: paleta M3 (`primary #00236f`, `secondary #0051d5`, superficies, outline,
  error) + semánticos `success`, `warning`, `info` + rampa `brand-50…900`.
- **Espaciado**: `space-2xs … 2xl`, `margin*`, `gutter*`.
- **Radios**: `md/lg` 0.25 rem, `xl` 0.5 rem, `pill` 0.75 rem.
- **Sombras**: `hairline`, `raised`, `pop`.
- Scrollbars personalizadas y respeto a `prefers-reduced-motion`.

Reglas de estilo:

- No usar colores de la paleta Tailwind (`text-emerald-600`, etc.) ni tamaños `text-*`
  arbitrarios; usar tokens (`text-title-md`, `bg-surface-container`, `text-error`).
- Iconos siempre con `atoms/Icon` (Material Symbols auto-hospedado en
  `public/fonts/`). No se carga nada desde CDN.
- Componentes reutilizables; nada de HTML de Stitch copiado.

## 10. Experiencia de uso

- **Login**: tarjeta partida formulario/directorio, mostrar/ocultar contraseña, mensajes
  específicos para 401/403/red.
- **DashboardLayout**: TopBar fija, sidebar fijo en desktop, drawer en móvil, scroll al
  inicio al cambiar de ruta.
- **Tableros**: `DataTable` para listados y tarjetas/columnas para colas.
- **Detalle de proyecto (Producción)**: guía de pasos `FlujoProyecto`, plan/fases,
  miembros, avances, adjuntos, cancelación con informe.
- **Detalle de Despacho**: datos de contacto, saldo, pagos, facturas descargables,
  entrega, negación y resolución.
- **Tecnología**: cola ordenada, prioridad, asignación múltiple, reporte de resolución y
  evidencias.
- **RRHH**: KPIs, proyectos globales, usuarios (alta/edición/bloqueo/reasignación) y
  bitácora.
- **Accesibilidad**: roles ARIA en buscador/modal, `aria-current`, foco visible,
  contraste corregido, movimiento reducido.

## 11. Nomenclatura «Desarrollo» vs «Producción»

- El **departamento** y todas las claves internas siguen siendo `desarrollo`
  (`/api/desarrollo`, `estado_desarrollo`, tabla `dev_*`).
- La **etiqueta visible** es «Producción» (`DEPARTAMENTOS.desarrollo = 'Producción'`).
- El correo semilla es `produccion@giscar.com`, pero el usuario se almacena con
  `departamento = "desarrollo"`.

No renombrar las claves sin migración: rompería datos, rutas y permisos.

## 12. Build y verificación

```bash
cd frontend && npm run build   # tsc -b && vite build → dist/
cd frontend && npm run lint    # oxlint
```

El backend sirve `frontend/dist` en producción y en el `.exe`. No hay tests de frontend;
la verificación es typecheck, lint y build.
