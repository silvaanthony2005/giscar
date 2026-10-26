# Plan: GISCAR — Sistema de Información por Departamentos

## Resumen

Sistema interno (PC local) para gestionar el flujo de proyectos de la empresa a través de 5
departamentos: **Ventas → Desarrollo → Despacho**, con **Tecnología** (incidencias transversales)
y **Recursos Humanos** (administradores con visión global).

- **Frontend:** React + TypeScript (Vite), arquitectura **Atom Design**, Tailwind CSS, estética
  profesional y moderna.
- **Backend:** FastAPI con **DDD** (capas domain / application / infrastructure) y programación
  **funcional** (funciones puras, inmutabilidad, HOFs `map`/`filter`/`reduce`, `Result` en vez de
  excepciones en el dominio).
- **Base de datos:** SQLite ligera (archivo único, WAL), vía SQLAlchemy 2.x. Sin servidor.
- **Despliegue:** local, un PC. Uvicorn sirve la API; FastAPI sirve el build del frontend.
- **Idioma:** español. **Facturación:** solo registro interno + PDF generado en backend.
- **Escala:** 25–100 usuarios.

---

## Decisiones de arquitectura

### Backend (DDD + funcional)

```
backend/app/
  domain/                 # PURO. Sin FastAPI, sin SQL, sin I/O. Testeable aislado.
    shared/
      types.py            # Result[T,E], DomainError, Money, UniqueId
      functions.py        # HOFs: pipeline, map/filter/reduce reutilizables, validators puros
      state_machine.py    # Motor genérico de transiciones de estado (puro)
    user/       model.py (frozen dataclass) · service.py (funciones puras) · events.py
    customer/   model.py · service.py
    project/    model.py (agregado) · states.py · service.py
    payment/    model.py · service.py        # pagos 50/100 y saldo restante
    invoice/    model.py · service.py · pdf.py (puro: datos → struct PDF)
    development/ model.py (Plan + Fase + Miembro + Avance) · service.py
    dispatch/   model.py · service.py        # estados entregado/pendiente/negado
    incidence/  model.py · service.py        # tickets Tecnología
    attachment/ model.py                     # documentos polimórficos
  application/            # Casos de uso. Orquestan domain + repos. Devuelven Result.
    ...                   # funciones de caso de uso, sin lógica de negocio embebida
  infrastructure/
    api/routes/           # Routers FastAPI (delgados: parsean → caso de uso → responden)
    db/                   # SQLAlchemy models + repositorios (implementan Protocol del domain)
    security/             # hashing bcrypt/argon2, JWT, dependencias de auth/roles
    storage/              # guardado de archivos en disco (uploads/)
  main.py                 # app FastAPI, CORS, montaje de routers, static del frontend
```

Principios aplicados:
- **Modelos de dominio `@dataclass(frozen=True)`** (inmutables). Cambios = nuevas instancias.
- **Funciones puras** en `service.py`: `(estado, comando) -> Result[nuevo_estado, error]`. Sin
  side-effects. La persistencia vive solo en infrastructure.
- **`Result[T, DomainError]`** para errores de negocio (evita excepciones en el flujo normal).
- **`Protocol`** para repositorios en domain; implementaciones concretas en infrastructure
  (inversión de dependencias / puertos y adaptadores).
- **State machine genérica** que define qué transiciones son válidas por departamento y las
  aplica de forma pura; el agregado Project la usa.

### Seguridad

- Hash de contraseñas **argon2** (fallback bcrypt).
- **JWT** de acceso (corto) con `sub`, `rol`, `departamento`; refresh simple.
- **Control de acceso por rol/departamento** como dependencias FastAPI:
  `require_role(...)`, `require_department(...)`.
- Validación estricta con **Pydantic** en la capa de API (desde/dominio no depende de Pydantic).
- Rate-limit básico en login; sanitización de nombres de archivo; MIME/ tamaño permitidos en
  uploads; path seguro (sin traversal) al guardar/ servir adjuntos.
- **Bitácora (AuditLog)** de acciones sensibles (login, cambios de usuario, cancelaciones,
  facturación) para la visibilidad de RRHH.

### Frontend (Atom Design)

```
frontend/src/
  atoms/        # Button, Input, Select, Badge, Avatar, Icon, Spinner, Modal, Card, Tag
  molecules/    # FormField, SearchInput, StatusBadge, UserCard, ConfirmDialog, FileDrop
  organisms/    # Sidebar, Topbar, DataTable, ProjectCard, PhaseTimeline, InvoiceSummary,
                #   IncidentQueue, UserTable, StatCard
  templates/    # DashboardLayout (sidebar+topbar), AuthLayout, PageHeader
  pages/        # Login, PanelPorRol, y por módulo:
                #   ventas/ · desarrollo/ · despacho/ · tecnologia/ · rrhh/
  entities/     # project, user, customer, invoice, incident... (types + api hooks)
  shared/       # api/client.ts (fetch + JWT), lib/ (fechas, moneda, hofs), hooks/, ui-primitives
  app/          # router, providers (auth, query), main.tsx
```

- **TanStack Query** para estado servidor (caché, mutaciones), **Zustand** para estado de sesión.
- **React Router** con rutas protegidas por rol.
- Componentes de UI consistentes (paleta, espaciado, tipografía) para "diseño excelente".

### Dominio / Modelo de datos (tablas)

- **users**: id, email, password_hash, nombre, documento, telefono, direccion, cargo,
  departamento (`ventas|desarrollo|despacho|tecnologia|rrhh`), estado (`activo|bloqueado`),
  timestamps.
- **customers**: id, nombre, documento, telefono, email, direccion, notas, created_by.
- **projects** (agregado central / expediente): id, codigo_unico, titulo, descripcion_detallada,
  customer_id, monto_total, estado_global, estado_ventas, estado_desarrollo, estado_despacho,
  created_by, timestamps.
- **invoices**: id, project_id, numero_factura, monto, porcentaje, metodo_pago, fecha,
  detalles_transaccion, snapshot_levantamiento (JSON), pdf_path.
- **payments**: id, project_id, monto, porcentaje (50|100|restante), metodo_pago, fecha,
  registrado_por, invoice_id. → control de saldo (anticipo + liquidación en despacho).
- **dev_plans**: id, project_id, resumen, objetivos, created_by.
- **dev_phases**: id, plan_id, orden, nombre, descripcion, fecha_inicio, fecha_fin_estimada,
  fecha_fin_real, horas_estimadas, horas_reales, estado.
- **project_members**: id, project_id, user_id, rol_proyecto, fecha_asignacion.
- **progress_updates**: id, project_id, phase_id?, user_id, porcentaje, notas, fecha.
- **cancellations**: id, project_id, motivo, informe, user_id, fecha.
- **dispatches**: id, project_id, estado (`pendiente|entregado|negado`), fecha_entrega, hora,
  destinatario, detalle_entregado, notas, confirmado_por.
- **incidents**: id, codigo, titulo, descripcion, reportado_por, departamento_origen,
  equipo_afectado, prioridad (`baja|media|alta|critica`), estado (`abierta|en_proceso|resuelta|
  cerrada`), orden_llegada, timestamps.
- **incident_assignees**: id, incident_id, user_id. Varios técnicos por incidencia.
- **incident_reports**: id, incident_id, user_id, diagnostico, solucion, tiempo_resolucion, fecha.
- **attachments**: id, entidad_tipo, entidad_id, nombre, ruta, mime, tamano, subido_por, fecha.
- **audit_logs**: id, user_id, accion, entidad_tipo, entidad_id, detalles, ip, fecha.

**Máquina de estados del proyecto (transiciones válidas):**
```
VENTAS:        borrador → levantamiento → cobrado_50 | cobrado_100 → enviado_desarrollo
DESARROLLO:    en_planificacion → en_desarrollo → completado → enviado_despacho
               (en cualquier punto → cancelado, con informe obligatorio)
DESPACHO:      pendiente_entrega → entregado
               pendiente_entrega → negado → (resuelto) pendiente_entrega → entregado
```
El pago restante se registra en Despacho antes de marcar `entregado` si el anticipo fue 50%.

---

## Alcance de la primera entrega (flujo completo)

1. **Auth + usuarios**: login JWT, registro/CRUD de usuarios por RRHH, asignar departamento/cargo,
   bloquear/desbloquear, cambiar departamento.
2. **Ventas**: CRUD clientes, crear proyecto (levantamiento detallado), registrar pago 50/100,
   emitir factura PDF, registro/historial de ventas.
3. **Desarrollo**: ver proyectos recibidos, crear plan + fases + tiempos, asignar personas,
   actualizar avance, subir adjuntos (PDF/imágenes/docs), cancelar con informe → expediente.
4. **Despacho**: ver proyectos listos, formulario interno de entrega (fecha/hora/detalle),
   estados entregado/pendiente/negado, registrar pago restante, adjuntos, contacto con cliente.
5. **Tecnología**: crear incidencias desde cualquier departamento, cola ordenada por llegada y
   prioridad, asignar, resolver con informe + evidencia fotográfica.
6. **RRHH**: dashboard global (todos los departamentos), auditoría, gestión de usuarios.
7. **Cross-cutting**: adjuntos polimórficos, bitácora, PDF de facturas e informes.

---

## Orden de implementación (fases de trabajo)

**Fase 0 — Andamiaje**
- Estructurar `backend/` (uv: `uv init`, deps: fastapi, uvicorn, sqlalchemy, pydantic, argon2,
  pyjwt, reportlab, python-multipart) y `frontend/` (Vite + React + TS + Tailwind + router +
  tanstack-query + zustand). Config de app, DB SQLite + WAL, health endpoint.

**Fase 1 — Dominio base y auth**
- `domain/shared` (Result, Money, state_machine, HOFs). Módulo `user` (modelo + service puro).
- Infra: SQLAlchemy models, repos, seguridad (hash, JWT), routers de auth y usuarios.
- Frontend: atoms/molecules, AuthLayout, Login, store de sesión, cliente API con JWT, rutas
  protegidas.

**Fase 2 — Ventas (clientes, proyectos, pagos, facturas)**
- Dominio: `customer`, `project` (agregado + máquina de estados), `payment`, `invoice` + PDF.
- Casos de uso + routers. Frontend: módulo ventas (clientes, formulario de levantamiento,
  pago, factura PDF, tabla de ventas).

**Fase 3 — Desarrollo (plan, fases, avance, expediente)**
- Dominio: `development` (plan, phases, members, progress), `cancellations`, `attachment`.
- Casos de uso + routers + storage de archivos. Frontend: módulo desarrollo (planificador,
  timeline de fases, panel de avance, adjuntos, cancelación).

**Fase 4 — Despacho y Tecnología**
- Dominio: `dispatch`, `incidence` (+ reportes de resolución).
- Casos de uso + routers. Frontend: módulo despacho (formulario entrega, estados, pago
  restante) y módulo tecnología (cola de incidencias, prioridad, resolución + evidencia).

**Fase 5 — RRHH, auditoría y pulido**
- Dashboard global RRHH, bitácora, gestión de usuarios completa. Ajuste de permisos,
  estados vacíos, loading/errores, responsive, pulido visual.

**Fase 6 — Verificación end-to-end**
- Script de seed (usuarios por departamento, clientes, proyectos de ejemplo). Probar el flujo
  completo Ventas→Desarrollo→Despacho y el ciclo de incidencias. Typecheck + lint + build.

---

## Criterios de terminado por fase
- `uv run pytest` (tests de dominio puro) en verde.
- `npm run build` y `tsc --noEmit` sin errores.
- Rutas protegidas por rol; flujo navegable de punta a punta con datos seed.

---

## Comandos de arranque previstos
```bash
# Backend (uv)
cd backend && uv sync && uv run uvicorn app.main:app --port 8000
# Frontend (dev)
cd frontend && npm install && npm run dev
# Producción local: npm run build y FastAPI sirve frontend/dist
```

---

## Riesgos / notas
- **SQLite + 100 usuarios:** usar WAL y transacciones cortas; suficiente para uso interno. Fácil
  migrar a Postgres después (SQLAlchemy).
- **Permisos:** definir matriz rol×recurso desde el inicio para no rehacer rutas.
- **Adjuntos en disco:** carpeta `uploads/` local, con nombres seguros y servidos por la API con
  autorización.
- **PDF:** plantillas simples con reportlab (factura, informe de cancelación, informe de
  incidencia).
