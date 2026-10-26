# 02 · Backend

## 1. Estructura y arranque

```
backend/
  app/
    config.py                 # Settings
    main.py                   # create_app(), routers, CORS, SPA, startup
    domain/shared/            # types, money, state_machine, functions
    domain/{user,customer,project,payment,invoice,development,dispatch,incidence,attachment,audit,search}/
    application/              # vacío
    infrastructure/api/routes # auth, panel, buscar, ventas, desarrollo, despacho, tecnologia, rrhh, health
    infrastructure/api/schemas*.py
    infrastructure/db/        # session, models*, mappers*, repositories/, seed
    infrastructure/security/  # password, jwt, deps
    infrastructure/storage/   # files
  tests/                      # 192 tests
  pyproject.toml              # uv, ruff, mypy, pytest
```

`main.py`:

1. Crea `FastAPI(title=settings.app_name, version="0.1.0")`.
2. Añade `CORSMiddleware` con `settings.cors_origins` (dev: `:5173`).
3. Registra routers: `health`, `auth`, `panel`, `buscar`, `ventas`, `desarrollo`,
   `despacho`, `tecnologia`, `rrhh`.
4. Si existe `frontend/dist`, monta `/assets` y una ruta catch-all SPA que:
   - responde 404 JSON para `api/*`,
   - sirve archivos reales del build si existen,
   - si no, devuelve `index.html` (deep links de React Router).
5. En `startup`: `init_db()` y `seed()`.

`run()` arranca Uvicorn en `127.0.0.1:8000`; en modo congelado pasa el objeto `app`
(sin reload), en desarrollo usa `"app.main:app"` con reload.

## 2. Configuración

`app/config.py` (`pydantic-settings`, prefijo `GISCAR_`, archivo `.env` en `BASE_DIR`):

| Variable | Default | Uso |
|---|---|---|
| `GISCAR_APP_NAME` | `GCISCAR` | Título OpenAPI |
| `GISCAR_DATABASE_URL` | `sqlite:///<BASE_DIR>/giscar.db` | SQLAlchemy |
| `GISCAR_UPLOADS_DIR` | `<BASE_DIR>/uploads` | Archivos |
| `GISCAR_JWT_SECRET` | `giscar-local-dev-secret-change-me-32bytes-min` | Firma JWT |
| `GISCAR_JWT_ALGORITHM` | `HS256` | Algoritmo |
| `GISCAR_ACCESS_TOKEN_MINUTES` | `480` (8 h) | Expiración |
| `GISCAR_CORS_ORIGINS` | `http://127.0.0.1:5173`, `http://localhost:5173` | Dev |
| `GISCAR_MAX_UPLOAD_MB` | `20` | Límite por archivo |

`BASE_DIR`:

- Desarrollo: `backend/` (dos niveles arriba de `config.py`).
- Congelado (`.exe`): `%LOCALAPPDATA%\GCISCAR` (datos fuera de la carpeta de instalación).

## 3. `domain/shared`

### `types.py`

- `Ok[T]`, `Err[E]`, `Result = Ok | Err`.
- `map`, `unwrap`, `is_ok`.
- Helpers: `map_result`, `and_then`, `unwrap_or`, `collect`, `partition`, `error`.
- `DomainError(code, message)`; `UnwrapError` solo para fallos de programación.

### `money.py`

- `Money(cents)` entero, no negativo.
- `from_amount`, `amount`, `plus`, `minus`, `percent`, `__str__`.
- `parse_money(raw) -> Result[Money, DomainError]`.
- `ZERO`.

### `state_machine.py`

- `Transition(source, target, name)`.
- `StateMachine(initial, transitions)` con `allowed_targets`, `can_transition`, `next`.
- `transition_field()` y `with_replace()` como helpers funcionales.

### `functions.py`

`pipe`, `compose`, `curried_map`, `curried_filter`, `curried_reduce`, `sum_by`,
`count_where`, `group_by`, `find_first`, `all_match`, `any_match`, `sort_by`,
`unique_by`, `clamp`.

## 4. Módulos de dominio

### 4.1 `user`

Modelo `User` inmutable:

```
id, email, password_hash, nombre, documento?, telefono?, direccion?, cargo?,
departamento (ventas|desarrollo|despacho|tecnologia|rrhh),
estado (activo|bloqueado|desactivado),
created_at, updated_at
```

Reglas (`user/service.py`):

- `create_user`: nombre obligatorio, email válido (regex), hash ≥ 10 caracteres.
  Normaliza email a minúsculas y teléfono a solo dígitos (`809-555 0001 → 8095550001`).
- `update_profile`: valida email/nombre si vienen; `''` vacía campos opcionales.
- `set_departamento`, `change_estado`, `change_password` (hash ≥ 10).
- `can_login`: rechaza `desactivado` y `bloqueado` con mensajes distintos.
- `validar_cambio_usuario`:
  - nadie puede bloquearse/desactivarse a sí mismo;
  - no se puede dejar el sistema sin ningún usuario **activo** de RRHH.
- `usuarios_bloqueados`: contador para RRHH.

`User.is_visible()` excluye `desactivado` de directorios/búsqueda.
`User.can_access(*deps)` devuelve `True` si el departamento está en `deps` **o si es
RRHH** (ver [06 · Seguridad](06-seguridad.md)).

### 4.2 `customer`

`Customer`: id, nombre, representante, documento, teléfono, email, dirección, notas,
`created_by`, timestamps.

- `create_customer`: **todos** los datos del levantamiento son obligatorios
  (nombre, representante, documento, teléfono, dirección). Teléfono solo dígitos.
- `update_customer`: parcial; `''` borra campos; email no se valida en dominio (sí en
  Pydantic).
- `puede_eliminar`: prohíbe borrar un cliente con proyectos (`customer.con_proyectos`).

### 4.3 `project` (agregado central)

`Project`:

```
id, codigo, titulo, descripcion_detallada, customer_id, monto_total: Money,
contacto_nombre, contacto_telefono?, contacto_email?, contacto_direccion?,
estado_ventas, estado_desarrollo, estado_despacho,
created_by, created_at, updated_at
```

`create_project`:

- título no vacío (la ruta lo deriva de los primeros 80 caracteres de los detalles si no
  llega);
- descripción ≥ 20 caracteres;
- monto > 0;
- estados iniciales: `levantamiento` / `pendiente` / `pendiente`.

Máquinas de estado (`project/states.py`): ver
[07 · Flujos](07-flujos-y-procesos.md#3-máquinas-de-estado).

Reglas de servicio:

| Función | Regla |
|---|---|
| `saldo_restante(total, pagado)` | `max(0, total - pagado)` |
| `puede_pasar_a_desarrollo` | exige pagado ≥ 50 % del total; pasa Ventas a `enviado_desarrollo` |
| `puede_pasar_a_despacho` | exige `estado_desarrollo == completado`; pasa a `enviado_despacho` y fija la espera de Despacho |
| `estado_espera_despacho(saldo)` | `pendiente_cobro` si hay saldo; si no, `pendiente_entrega` |
| `tras_liquidar` | `pendiente_cobro → pendiente_entrega` |
| `puede_entregar` | exige saldo 0; marca `entregado` y cierra Ventas (`enviado_desarrollo → cerrado`) |

Acciones que expone el backend (la UI solo pinta):

| Función | Cuándo devuelve qué |
|---|---|
| `acciones_ventas` | vacío si ya salió de Ventas; `registrar_pago` si hay saldo; `pasar_desarrollo` si pagó ≥ 50 % |
| `acciones_desarrollo` | vacío si Ventas no lo envió; traduce transiciones válidas a `crear_plan`, `iniciar`, `completar`, `pasar_despacho`, `cancelar`; quita `completar` si hay fases pendientes |
| `acciones_despacho` | vacío si Producción no lo envió; `liquidar` (con saldo y no entregado), `confirmar_entrega` (saldo 0 y transición válida), `negar`, `resolver_negacion` (si `negado`) |

Columnas de tablero:

- Desarrollo: `recibidos` (no llegó / `pendiente`), `en_curso` (`en_planificacion`,
  `en_desarrollo`), `historial` (`completado`, `cancelado`, `enviado_despacho`).
- Despacho: `pendientes` (todo lo abierto), `cerrados` (`entregado`, `negado`).

Contadores del sidebar: `pendientes_ventas`, `activos_desarrollo`,
`pendientes_despacho`.

### 4.4 `payment`

`Payment`: id, project_id, monto, porcentaje (0–100 del total acumulado), tipo
(`anticipo|liquidacion|total`), método, notas, registrado_por, fecha.

`create_payment`:

- monto > 0;
- no excede el saldo;
- calcula `porcentaje = round(pagado_total * 100 / total)`.

`sumar_pagos` agrega con `reduce`.

Clasificación del tipo (en la ruta de Ventas):

- primer pago que cubre el total → `total`;
- pago que cubre el resto → `liquidacion`;
- resto → `anticipo`.

> **Matiz observado:** el estado de Ventas pasa a `cobrado_50` con **cualquier** pago
> parcial (aunque sea < 50 %); `cobrado_100` solo al cubrir el total. El umbral del 50 %
> se valida aparte en `puede_pasar_a_desarrollo`.

### 4.5 `invoice` + PDF

`Invoice` guarda un **snapshot inmutable** del proyecto/cliente al facturar
(`InvoiceSnapshot`) y los datos del pago.

`create_invoice`: valida que el pago pertenezca al proyecto y que el monto sea > 0;
construye la descripción `Cobro de proyecto {codigo} — {titulo} ({porcentaje}% del total)`.
Se emite en Ventas con cada pago y en Despacho al liquidar el saldo restante.

`next_numero(existing, year)`: calcula el siguiente `FAC-YYYY-NNNNN` ignorando otros años
y formatos. Es puro y lo comparten ambas rutas.

`invoice/pdf.py` genera bytes con reportlab:

- tamaño carta, cabecera azul `#1d4ed8`, fuente Helvetica;
- número, fecha, cliente, proyecto, método, porcentaje, total;
- bloque destacado con el monto cobrado;
- detalle del levantamiento (máx. 24 líneas, wrap a 95 caracteres);
- pie «Documento de registro interno — GCISCAR» + emisor.

Es una función pura: no escribe en disco; la ruta devuelve `Response` con
`Content-Disposition: attachment`.

### 4.6 `development` (Producción)

Modelos: `DevPlan`, `Phase`, `ProjectMember`, `ProgressUpdate`, `Cancellation`.

Reglas:

- `create_plan`: resumen obligatorio, horas > 0.
- `create_phase`: nombre obligatorio, `orden ≥ 1`, horas ≥ 0, fin ≥ inicio.
- `set_phase_state`: `pendiente → en_curso → completada`; al completar fija
  `fecha_fin_real` si se pasa `now`.
- `update_phase_progress`: horas reales ≥ 0.
- `record_progress`: porcentaje 0–100 y notas no vacías.
- `create_cancellation`: motivo obligatorio e informe ≥ 30 caracteres.
- `fases_pendientes` / `error_fases_pendientes`: no se puede completar el proyecto con
  fases abiertas.
- `plan_horas_por_fases`: suma de horas estimadas.
- `acciones_fase`: destino(s) válidos según estado.

La ruta `POST /proyectos/{pid}/plan` crea plan + fases + miembros en una transacción y
mueve el proyecto a `en_planificacion`. Los miembros solo pueden ser usuarios **activos
del departamento `desarrollo`**.

### 4.7 `dispatch` (Despacho)

- `Dispatch`: formulario interno de entrega (fecha, hora, destinatario, detalle, notas,
  confirmado_por, fecha_registro).
- `Denial`: motivo + detalle del rechazo.

Reglas:

- `confirm_delivery`: destinatario, detalle y fecha obligatorios.
- `register_denial`: motivo obligatorio y detalle ≥ 15 caracteres.

La transición de estado la decide `project/service.py` (no este módulo).

### 4.8 `incidence` (Tecnología)

- `Incidence`: código, título, descripción, equipo afectado, departamento origen,
  prioridad, estado, orden de llegada, reportado_por, asignados (tupla), timestamps.
- `IncidentReport`: diagnóstico, solución, horas de resolución, resuelto_por.

Reglas:

- `create_incidence`: título, equipo y descripción ≥ 15; prioridad en
  `baja|media|alta|critica`; nace `abierta`.
- `transition_incidence`:
  `abierta → en_proceso | cerrada`; `en_proceso → resuelta | cerrada`;
  `resuelta → cerrada`; `cerrada` es terminal.
- `assign_incidence`: no permite asignar cerradas; deduplica IDs; lista vacía = sin
  técnicos.
- `create_report`: diagnóstico y solución ≥ 10, horas ≥ 0.
- `ordenar_cola`: prioridad descendente (`critica=4 … baja=1`) y luego `orden_llegada`
  ascendente.
- `contar_por_estado`, `incidencias_activas` (no resueltas ni cerradas).

### 4.9 `attachment`

- `EntidadTipo`: `proyecto|plan|fase|cancelacion|despacho|incidencia|factura`.
- `validate_upload`: nombre, MIME permitido, tamaño > 0 y ≤ máximo.
- MIME permitidos: PDF, PNG, JPEG, WebP, GIF, texto plano, DOC/DOCX, XLS/XLSX.
- `safe_filename`: reemplaza caracteres no seguros y prefija el id (`<id>_<nombre>`).
- Metadatos en BD (`attachments`) y bytes en `uploads/`.

### 4.10 `audit`

`AuditLog`: user_id, user_email, acción, entidad, detalle, ip, fecha.

`record` valida contra una **whitelist** de acciones:

```
login, login_fallido, logout, usuario_creado, usuario_actualizado,
usuario_bloqueado, usuario_desbloqueado, usuario_desactivado,
usuario_password_restablecido, departamento_cambiado, cliente_eliminado,
proyecto_creado, pago_registrado, factura_emitida, proyecto_cancelado,
entrega_confirmada, proyecto_negado, incidencia_creada, incidencia_resuelta
```

`log_action` es *best-effort*: si la acción no está en la lista, se ignora; no rompe el
flujo de negocio.

### 4.11 `search`

Búsqueda global pura:

- consulta mínima de 2 caracteres; normaliza minúsculas/espacios;
- coincidencia por subcadena en campos identificadores (no en descripciones largas);
- máximo 8 resultados por categoría;
- categorías permitidas por departamento:
  - proyecto: ventas, desarrollo, despacho;
  - cliente: ventas;
  - incidencia: tecnologia;
  - usuario: rrhh;
  - RRHH: todas.
- el dominio devuelve `tipo` + `id`; la URL la decide el frontend.

## 5. Infraestructura HTTP

### 5.1 Routers

| Router | Prefijo | Quién (además de RRHH) |
|---|---|---|
| `health` | `/api` | Público |
| `auth` | `/api/auth` | Login público; gestión de usuarios solo RRHH |
| `panel` | `/api/panel` | Cualquier autenticado (filtra por departamento) |
| `buscar` | `/api/buscar` | Cualquier autenticado (filtra por departamento) |
| `ventas` | `/api/ventas` | Ventas (el PDF de factura también lo ve Despacho) |
| `desarrollo` | `/api/desarrollo` | Desarrollo; adjuntos también Ventas/Despacho/Tecnología |
| `despacho` | `/api/despacho` | Despacho |
| `tecnologia` | `/api/tecnologia` | Reportar: todos; gestionar: Tecnología |
| `rrhh` | `/api/rrhh` | RRHH |

El listado completo de endpoints está en
[05 · API e integraciones](05-api-e-integraciones.md).

### 5.2 Esquemas Pydantic

- `schemas.py`: login, usuario, búsqueda.
- `schemas_ventas.py`: cliente, proyecto, pago, factura.
- `schemas_desarrollo.py`: plan, fases, miembros, avance, cancelación, adjuntos.
- `schemas_despacho.py`: entrega, negación, incidencias y reportes.

Los esquemas **no** se comparten con el dominio: son contratos de borde. Usan
`EmailStr`, `Field(min_length=…)`, `Literal` y enums duplicados a propósito.

### 5.3 Errores y códigos HTTP

| Código | Cuándo |
|---|---|
| 200 | Lectura/transición correcta |
| 201 | Recurso creado (cliente, proyecto, pago, plan, avance, cancelación, adjunto, entrega, negación, incidencia, reporte) |
| 204 | Borrado correcto (cliente, miembro) |
| 400 | No se usa explícitamente |
| 401 | Sin token, token inválido/expirado, usuario inexistente o inactivo |
| 403 | Departamento incorrecto; login de usuario bloqueado/desactivado |
| 404 | Entidad no encontrada; archivo físico ausente |
| 409 | Email duplicado; plan ya existente |
| 422 | Validación Pydantic o `DomainError` de negocio |
| 500 | Error no controlado |

## 6. Persistencia

- `session.py`: `engine` SQLite, `check_same_thread=False`, `pool_pre_ping=True`;
  PRAGMAs `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout=5000`;
  `SessionLocal(autoflush=False, autocommit=False, expire_on_commit=False)`.
- `init_db()` importa todos los módulos de modelos y ejecuta `create_all`, seguido de
  parches idempotentes:
  - añade `customers.representante` si falta;
  - migra `incidents.asignado_a` a `incident_assignees`;
  - pasa a `pendiente_cobro` los proyectos en Despacho con saldo.
- Mappers (`mappers*.py`) convierten fila ↔ dataclass y dinero centavos ↔ `Money`.
- Repositorios: `UserRepository`, `CustomerRepository`, `ProjectRepository`,
  `PaymentRepository`, `InvoiceRepository`, `PlanRepository`, `PhaseRepository`,
  `MemberRepository`, `ProgressRepository`, `CancellationRepository`,
  `AttachmentRepository`, `DispatchRepository`, `DenialRepository`,
  `IncidentRepository`, `IncidentReportRepository`, `AuditRepository`.
- `seed()` crea 5 usuarios si no existen y renombra `desarrollo@giscar.com` →
  `produccion@giscar.com` en bases antiguas.

## 7. Seguridad de infraestructura

- `password.py`: Argon2 (`time_cost=2`, `memory_cost=64 MiB`, `parallelism=2`),
  verificación con `VerifyMismatchError`/`VerificationError`.
- `jwt.py`: HS256, claims `sub`, `dep`, `exp`, `iat`; `decode_token` devuelve `Result`.
- `deps.py`: `get_current_user` (Bearer → decode → cargar usuario → exigir activo),
  `require_department(*deps)`.
- `storage/files.py`: `save_upload`, `read_upload`, `upload_path`.
- Detalle completo en [06 · Seguridad](06-seguridad.md).

## 8. Pruebas

`backend/tests/` contiene **192 tests** que corren en ~2 s. La mayoría no toca BD ni
servidor; hay un test de integración con SQLite en memoria que verifica la factura de la
liquidación y la descarga del PDF:

- dominio puro: `test_money`, `test_shared_types`, `test_state_and_hofs`,
  `test_user_domain`, `test_customer_domain`, `test_ventas_domain`,
  `test_desarrollo_domain`, `test_despacho_incidence_domain`;
- lógica de tableros/acciones: `test_acciones_disponibles`, `test_agrupaciones`;
- búsqueda: `test_busqueda`;
- contratos de rutas/esquemas: `test_rutas_ventas`, `test_rutas_desarrollo`,
  `test_rutas_tecnologia`, `test_rutas_adjuntos` (verifican que las rutas existan y que
  los esquemas acepten/rechacen lo esperado, sin levantar FastAPI).

Comando:

```bash
cd backend && uv run pytest -q
```

Configuración en `pyproject.toml`: `testpaths = ["tests"]`, `pythonpath = ["."]`.
No hay `conftest.py` ni fixtures de BD.

## 9. Convenciones para añadir un módulo

1. Crear `domain/<modulo>/model.py` con dataclasses `frozen=True, slots=True`.
2. Crear `domain/<modulo>/service.py` con funciones puras que devuelvan `Result`.
3. Añadir tests de dominio (sin BD).
4. Crear `models_<modulo>.py` y `mappers_<modulo>.py` en infrastructure.
5. Crear repositorio con operaciones explícitas (sin lógica de negocio).
6. Añadir esquemas Pydantic y router delgado.
7. Registrar el router en `main.py` y el módulo de modelos en `init_db()`.
8. Exponer valores derivados ya calculados en la respuesta.
