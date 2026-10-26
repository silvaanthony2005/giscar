# 05 · API e integraciones

## 1. Generalidades

- **Base URL**: `http://127.0.0.1:8000`
- **Prefijo**: todos los endpoints de negocio cuelgan de `/api`.
- **Formato**: JSON UTF-8; subidas `multipart/form-data`.
- **Autenticación**: `Authorization: Bearer <JWT>` en todas las rutas salvo
  `POST /api/auth/login` y `GET /api/health`.
- **Documentación viva**:
  - Swagger UI: `http://127.0.0.1:8000/docs`
  - OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- **Healthcheck**: `GET /api/health → {"status":"ok"}` (lo usa el lanzador del `.exe`).
- **CORS**: solo para desarrollo (`http://127.0.0.1:5173`, `http://localhost:5173`).
  En producción el frontend se sirve desde el mismo origen.
- **Errores**: `{"detail": "<mensaje en español>"}`. Ver tabla de códigos en
  [02 · Backend](02-backend.md#53-errores-y-códigos-http).

> `require_department` deja pasar siempre a RRHH (`User.can_access`). En las tablas de
> «Quién» se indica el departamento funcional; **RRHH puede invocar todas las rutas**.

## 2. Resumen de recursos

| Recurso | Endpoints | Quién |
|---|---|---|
| Salud | 1 | Público |
| Autenticación y usuarios | 5 | Público / autenticado / RRHH |
| Panel (contadores) | 1 | Autenticado |
| Búsqueda global | 1 | Autenticado |
| Ventas | 12 | Ventas |
| Producción/Desarrollo | 18 | Desarrollo (+ adjuntos a 4 departamentos) |
| Despacho | 7 | Despacho |
| Tecnología | 7 | Todos reportan; Tecnología gestiona |
| RRHH | 4 | RRHH |

## 3. Salud

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/api/health` | `{"status":"ok"}` |

## 4. Autenticación y usuarios

| Método | Ruta | Quién | Cuerpo / query | Respuesta |
|---|---|---|---|---|
| POST | `/api/auth/login` | Público | `{email, password}` | `{access_token, token_type, user}` |
| GET | `/api/auth/me` | Autenticado | — | `UserOut` |
| GET | `/api/auth/usuarios` | RRHH | — | `UserOut[]` |
| POST | `/api/auth/usuarios` | RRHH | `CreateUserRequest` | `201 UserOut` |
| PATCH | `/api/auth/usuarios/{user_id}` | RRHH | `UpdateUserRequest` | `UserOut` |

### `POST /api/auth/login`

```json
{ "email": "ventas@giscar.com", "password": "giscar1234" }
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "9f2c...",
    "email": "ventas@giscar.com",
    "nombre": "Luis Pérez",
    "documento": null,
    "telefono": null,
    "direccion": null,
    "cargo": "Ejecutivo de ventas",
    "departamento": "ventas",
    "estado": "activo",
    "created_at": "2026-10-26T12:00:00Z"
  }
}
```

- Credenciales inválidas → `401`.
- Usuario bloqueado/desactivado → `403` con el motivo.
- Cada intento se registra en `audit_logs` (`login` o `login_fallido`).

### `POST /api/auth/usuarios`

```json
{
  "email": "nuevo@giscar.com",
  "password": "minimo8",
  "nombre": "Nombre Apellido",
  "documento": "001-0000000-0",
  "telefono": "8095550000",
  "direccion": "Calle 1",
  "cargo": "Analista",
  "departamento": "desarrollo"
}
```

- Email duplicado → `409`.
- El alta registra `usuario_creado` en la bitácora.

### `PATCH /api/auth/usuarios/{id}`

Campos opcionales: `email`, `nombre`, `documento`, `telefono`, `direccion`, `cargo`,
`departamento`, `estado` (`activo|bloqueado|desactivado`), `password`.

- Bloquearse/desactivarse a sí mismo → `422`.
- Dejar RRHH sin usuarios activos → `422`.
- Cambiar contraseña o estado genera entradas de auditoría específicas.

## 5. Panel

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/api/panel/contadores` | `{"ventas": n, "desarrollo": n, "despacho": n, "tecnologia": n, "rrhh": n}` |

Solo incluye los departamentos visibles para el usuario; RRHH recibe todos. Los números
los calcula el dominio.

## 6. Búsqueda global

| Método | Ruta | Query | Respuesta |
|---|---|---|---|
| GET | `/api/buscar` | `q` (1–100) | `BusquedaOut` |

```json
{
  "consulta": "acme",
  "tipos": ["proyecto", "cliente"],
  "resultados": {
    "proyecto": [
      { "tipo": "proyecto", "id": "…", "titulo": "Portal ACME", "subtitulo": "PRJ-2026-0001", "codigo": "PRJ-2026-0001" }
    ],
    "cliente": [
      { "tipo": "cliente", "id": "…", "titulo": "ACME S.A.", "subtitulo": "1-3123456-7", "codigo": "1-3123456-7" }
    ]
  }
}
```

- Menos de 2 caracteres útiles → `422`.
- Máximo 8 por categoría; categorías según departamento.
- El backend no devuelve URLs.

## 7. Ventas — `/api/ventas`

### Clientes

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/clientes` | — | `CustomerOut[]` |
| POST | `/clientes` | `CreateCustomerRequest` | `201 CustomerOut` |
| PATCH | `/clientes/{cid}` | `UpdateCustomerRequest` | `CustomerOut` |
| DELETE | `/clientes/{cid}` | — | `204` |

`CreateCustomerRequest` exige `nombre`, `representante`, `documento`, `telefono` y
`direccion`; `email` y `notas` son opcionales.

`DELETE` falla con `422` si el cliente tiene proyectos.

### Proyectos

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/proyectos` | — | `ProjectOut[]` |
| GET | `/proyectos/{pid}` | — | `ProjectOut` |
| POST | `/proyectos` | `CreateProjectRequest` | `201 ProjectOut` |
| POST | `/proyectos/{pid}/pasar-desarrollo` | — | `ProjectOut` |

`CreateProjectRequest`:

```json
{
  "customer_id": "…",
  "titulo": null,
  "descripcion_detallada": "Detalle del producto o servicio solicitado (≥ 20 caracteres)",
  "monto_total": 150000.0,
  "contacto_nombre": "Ana Reyes",
  "contacto_telefono": "8095550001",
  "contacto_email": "ana@acme.com",
  "contacto_direccion": "Av. Principal 1"
}
```

`ProjectOut` incluye **valores ya calculados**: `monto_total`, `pagado`, `saldo`,
`estado_ventas`, `estado_desarrollo`, `estado_despacho` y `acciones`.

`pasar-desarrollo` exige ≥ 50 % cobrado y devuelve `422` si no.

### Pagos y facturas

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/proyectos/{pid}/pagos` | — | `PaymentOut[]` |
| POST | `/proyectos/{pid}/pagos` | `{monto, metodo_pago, notas?}` | `201 PaymentOut` |
| GET | `/proyectos/{pid}/facturas` | — | `InvoiceOut[]` |
| GET | `/facturas/{iid}/pdf` | — | `application/pdf` |

Al registrar un pago, la ruta en una sola transacción:

1. valida contra el saldo;
2. crea el `Payment`;
3. actualiza `estado_ventas` (`cobrado_50` con parcial, `cobrado_100` al cubrir total);
4. emite una `Invoice` con numeración `FAC-YYYY-NNNNN` y snapshot;
5. audita `pago_registrado` y `factura_emitida`.

`monto` excede el saldo → `422`. Proyecto inexistente → `404`.

## 8. Producción/Desarrollo — `/api/desarrollo`

### Tablero y acciones

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/proyectos` | `{recibidos: Project[], en_curso: Project[], historial: Project[]}` |
| GET | `/proyectos/{pid}/acciones` | `{acciones: string[], estado_desarrollo: string}` |

Las columnas y acciones las decide el dominio; el frontend solo las pinta.

### Plan, fases y avance

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/proyectos/{pid}/plan` | — | plan + fases + miembros + avances + totales |
| POST | `/proyectos/{pid}/plan` | `CreatePlanWithPhasesRequest` | `201 PlanOut` |
| GET | `/proyectos/{pid}/fases/{fid}` | — | `PhaseOut` |
| POST | `/proyectos/{pid}/fases/{fid}/estado` | `{target}` | `PhaseOut` |
| POST | `/proyectos/{pid}/avance` | `{porcentaje, notas, phase_id?}` | `201 ProgressOut` |

`CreatePlanWithPhasesRequest`:

```json
{
  "resumen": "Rediseño del portal",
  "objetivos": "Mejorar tiempos de carga",
  "horas_estimadas": 120,
  "fases": [
    { "orden": 1, "nombre": "Análisis", "descripcion": "", "horas_estimadas": 20,
      "fecha_inicio": "2026-11-01", "fecha_fin_estimada": "2026-11-07" }
  ],
  "miembros": ["id-usuario-desarrollo"]
}
```

- Plan duplicado → `409`.
- Fase inválida → `422` con `Fase '<nombre>': <motivo>`.
- Miembro inexistente → `404`; de otro departamento → `422`.

El endpoint de plan devuelve también:

```json
{
  "horas_totales_fases": 20,
  "estado_desarrollo": "en_planificacion",
  "puede_registrar_avance": false,
  "acciones": ["iniciar", "cancelar"]
}
```

### Transiciones del proyecto

| Método | Ruta | Respuesta |
|---|---|---|
| POST | `/proyectos/{pid}/iniciar` | `{estado_desarrollo}` |
| POST | `/proyectos/{pid}/completar` | `{estado_desarrollo}` |
| POST | `/proyectos/{pid}/pasar-despacho` | `{estado_desarrollo}` |

- `iniciar`: `en_planificacion → en_desarrollo`. Las fases/avances solo se editan en
  `en_desarrollo`.
- `completar`: exige **todas** las fases completadas (`422` con la lista de pendientes).
- `pasar-despacho`: exige `completado`; fija `pendiente_cobro` o `pendiente_entrega`
  según el saldo.

### Cancelación

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| POST | `/proyectos/{pid}/cancelar` | `{motivo, informe}` (informe ≥ 30) | `201 CancellationOut` |
| GET | `/proyectos/{pid}/cancelacion` | — | `CancellationOut` o `null` |

Se valida la transición **antes** de escribir y luego se guarda informe + estado.

### Miembros

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/catalogo-usuarios` | — | usuarios activos de Producción |
| POST | `/proyectos/{pid}/miembros` | `{user_ids: string[]}` | `MemberOut[]` |
| DELETE | `/proyectos/{pid}/miembros/{mid}` | — | `204` |

### Adjuntos (compartidos con Ventas, Despacho y Tecnología)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| POST | `/adjuntos/{entidad_tipo}/{entidad_id}` | `multipart: file` | `201 AttachmentOut` |
| GET | `/adjuntos/{aid}/descargar` | — | binario (`FileResponse`) |
| GET | `/adjuntos/{entidad_tipo}/{entidad_id}` | — | `AttachmentOut[]` |

- `entidad_tipo` ∈ `proyecto|plan|fase|cancelacion|despacho|incidencia|factura`.
- Tamaño máximo: `GISCAR_MAX_UPLOAD_MB` (20 por defecto).
- MIME en lista blanca; nombre saneado; se guarda en `uploads/`.
- La descarga se declara **antes** que el listado para que `/{aid}/descargar` no colisione
  con `/{entidad_tipo}/{entidad_id}`.

## 9. Despacho — `/api/despacho`

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/proyectos` | — | `{pendientes: [], cerrados: []}` |
| GET | `/proyectos/{pid}` | — | detalle completo (cliente, pagos, entrega, negación, `por_pagado`) |
| POST | `/proyectos/{pid}/liquidar` | `{metodo_pago, notas?}` | `201 {id, monto, porcentaje, tipo}` |
| POST | `/proyectos/{pid}/confirmar-entrega` | `DeliveryIn` | `201 DeliveryOut` |
| POST | `/proyectos/{pid}/negar` | `{motivo, detalle}` (detalle ≥ 15) | `201 DenialOut` |
| POST | `/proyectos/{pid}/resolver-negacion` | — | `{estado_despacho}` |
| POST | `/proyectos/{pid}/estado` | `{target}` | `{estado_despacho}` |

`DeliveryIn`:

```json
{
  "fecha_entrega": "2026-11-15",
  "hora_entrega": "10:30",
  "destinatario": "Ana Reyes",
  "detalle_entregado": "Servidor y licencias",
  "notas": "Recibido conforme"
}
```

Comportamiento:

- `liquidar` cobra **todo el saldo** (no acepta importe parcial), crea `Payment` tipo
  `liquidacion`, cierra Ventas (`cerrado`) y pasa Despacho de `pendiente_cobro` a
  `pendiente_entrega`. **No emite factura.**
- `confirmar-entrega` exige saldo 0; guarda el acta interna y marca `entregado`.
- `negar` pasa a `negado` con motivo/detalle.
- `resolver-negacion` vuelve a `pendiente_cobro` o `pendiente_entrega` según saldo.
- `/estado` es una transición genérica validada por la máquina de estados.

## 10. Tecnología — `/api/tecnologia`

| Método | Ruta | Quién | Cuerpo | Respuesta |
|---|---|---|---|---|
| POST | `/incidencias` | Todos | `CreateIncidenceRequest` | `201` incidencia |
| GET | `/incidencias` | Tecnología | — | `{incidencias: [], resumen: {estado: n}}` |
| GET | `/incidencias/{iid}` | Tecnología | — | incidencia + `reportes[]` |
| POST | `/incidencias/{iid}/asignar` | Tecnología | `{user_ids: []}` | incidencia |
| POST | `/incidencias/{iid}/estado` | Tecnología | `{target}` | incidencia |
| POST | `/incidencias/{iid}/reporte` | Tecnología | `IncidentReportIn` | incidencia + `reporte_id` |
| GET | `/tecnicos` | Tecnología | — | `[{id, nombre, cargo}]` |

```json
{
  "titulo": "Monitor sin señal",
  "descripcion": "El monitor del puesto 4 no enciende desde esta mañana.",
  "equipo_afectado": "Monitor Dell U2419H",
  "prioridad": "alta"
}
```

- Código automático `INC-YYYY-NNNN`; `orden_llegada` consecutivo.
- La cola se ordena por prioridad descendente y llegada ascendente.
- `reporte` acepta incidencias `abierta` (las pasa a `en_proceso`) y las deja `resuelta`.
- `resumen` cuenta por estado (`abierta`, `en_proceso`, `resuelta`, `cerrada`).

## 11. RRHH — `/api/rrhh`

| Método | Ruta | Query | Respuesta |
|---|---|---|---|
| GET | `/dashboard` | — | KPIs globales |
| GET | `/actividad` | `limit` (máx. 500, def. 200) | `AuditLog[]` |
| GET | `/proyectos` | — | todos los proyectos (solo lectura) |
| GET | `/usuarios` | `departamento?` | usuarios (vista RRHH) |

`/dashboard` devuelve agregados calculados en SQL:

```json
{
  "ventas": { "clientes": 10, "facturas": 12, "monto_cobrado": 15000.0,
               "proyectos_total": 8, "proyectos_por_estado": {"cobrado_50": 3} },
  "desarrollo": { "planes": 5, "fases_por_estado": {"completada": 7}, "cancelaciones": 1 },
  "despacho": { "proyectos_por_estado": {"entregado": 2} },
  "tecnologia": { "incidencias_por_estado": {"abierta": 1},
                  "incidencias_por_prioridad": {"alta": 1} },
  "usuarios": { "por_departamento": {"ventas": 2}, "por_estado": {"activo": 5}, "total": 5 }
}
```

## 12. Integraciones

GCISCAR **no integra servicios externos**. Sus «integraciones» son internas:

| Integración | Cómo funciona |
|---|---|
| Frontend ↔ Backend | HTTP JSON con Bearer; Vite proxy en dev; mismo origen en prod |
| PDF de facturas | reportlab en memoria → `Response` con `Content-Disposition` |
| Adjuntos | `multipart/form-data` → disco (`uploads/`) + metadatos en SQLite |
| Ventas ↔ Producción ↔ Despacho | Estado compartido del agregado `Project`; el backend calcula transiciones y acciones |
| Tecnología ↔ todos | Cualquier departamento crea incidencias; solo Tecnología las gestiona |
| RRHH ↔ todos | Lectura global + gestión de usuarios; bitácora |
| Búsqueda ↔ todos | Agrega proyectos, clientes, incidencias y usuarios según permisos |
| Instalador ↔ app | Lanzador comprueba `/api/health` antes de abrir WebView2 |

No hay webhooks, correo, SMS, pasarelas de pago, servicios cloud ni telemetría.

## 13. Ejemplos con `curl`

```bash
# Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ventas@giscar.com","password":"giscar1234"}' | jq -r .access_token)

# Listar proyectos
curl -s http://127.0.0.1:8000/api/ventas/proyectos \
  -H "Authorization: Bearer $TOKEN"

# Descargar factura
curl -s -OJ http://127.0.0.1:8000/api/ventas/facturas/<id>/pdf \
  -H "Authorization: Bearer $TOKEN"

# Subir evidencia
curl -s -X POST http://127.0.0.1:8000/api/desarrollo/adjuntos/incidencia/<id> \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@foto.jpg"
```

## 14. Compatibilidad y versionado

- No hay versión en la URL (`/api/v1`); la app es local y se despliega junto al frontend.
- Los cambios de contrato implican rebuild del frontend y del instalador.
- OpenAPI se regenera solo con el código; no se mantiene un archivo estático.
