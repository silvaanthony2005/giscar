# 07 · Flujos y procesos

## 1. Flujo de datos

```mermaid
flowchart TB
    subgraph UI["Frontend (React)"]
        P["Página / componente"]
        Q["TanStack Query<br/>caché + mutaciones"]
        C["api/client.ts<br/>Bearer + errores"]
        Z["Zustand<br/>token + user"]
    end

    subgraph BE["Backend (FastAPI)"]
        R["Router delgado"]
        S["Schemas Pydantic"]
        D["Dominio puro<br/>reglas + Result"]
        RP["Repositorios"]
        M["Mappers"]
    end

    DB[("SQLite (WAL)")]
    FS[("uploads/")]

    P -- "useQuery / useMutation" --> Q
    Q --> C
    Z -- "token" --> C
    C -- "HTTP /api" --> R
    R --> S
    S --> R
    R --> RP
    RP --> DB
    RP --> M
    M --> D
    R --> D
    D -- "Ok / Err" --> R
    R -- "JSON ya calculado<br/>pagado, saldo, acciones, grupos" --> Q
    Q -- "datos" --> P
    R -- "multipart" --> FS
    R -- "FileResponse" --> C
```

Principios del flujo:

1. **El cliente no deriva reglas.** Pide datos y acciones; el servidor decide.
2. **Una sola fuente de verdad** por agregado (`Project`).
3. **Transacciones cortas**: cargar → validar en dominio → escribir → `commit`.
4. **Invalidación explícita de caché** tras cada mutación, incluyendo módulos vecinos.

## 2. Ciclo de una petición

```mermaid
sequenceDiagram
    participant UI as React
    participant API as FastAPI
    participant AUTH as security/deps
    participant REPO as Repositorio
    participant DOM as Dominio
    participant DB as SQLite

    UI->>API: HTTP + Bearer
    API->>AUTH: get_current_user
    AUTH->>REPO: usuario por sub
    REPO->>DB: SELECT
    AUTH-->>API: User activo
    API->>AUTH: require_department
    API->>REPO: cargar agregado
    API->>DOM: función pura (command)
    alt Err(DomainError)
        DOM-->>API: error de negocio
        API-->>UI: 4xx {detail}
    else Ok(nuevo estado)
        DOM-->>API: valor inmutable
        API->>REPO: persistir
        REPO->>DB: INSERT/UPDATE
        API->>DB: commit
        API-->>UI: 2xx JSON
        UI->>UI: invalidar queries y repintar
    end
```

## 3. Máquinas de estado

### 3.1 Ventas

```mermaid
stateDiagram-v2
    [*] --> levantamiento
    levantamiento --> cobrado_50: pago parcial
    levantamiento --> cobrado_100: pago total
    cobrado_50 --> cobrado_100: completa el total
    cobrado_50 --> enviado_desarrollo: ≥ 50 % + pasar
    cobrado_100 --> enviado_desarrollo: pasar
    enviado_desarrollo --> cerrado: liquidación en Despacho
    cerrado --> [*]
```

- No existe estado `borrador` ni guardado de borradores: el proyecto nace en
  `levantamiento` cuando Ventas envía el formulario completo.
- `cobrado_50` significa «hay algún pago parcial», no exactamente 50 %.
- `cerrado` se alcanza al liquidar el saldo en Despacho (o al entregar si Ventas seguía
  en `enviado_desarrollo`).

### 3.2 Producción (Desarrollo)

```mermaid
stateDiagram-v2
    [*] --> pendiente
    pendiente --> en_planificacion: crear plan
    pendiente --> cancelado: cancelar
    en_planificacion --> en_desarrollo: iniciar
    en_planificacion --> cancelado: cancelar
    en_desarrollo --> completado: completar (todas las fases)
    en_desarrollo --> cancelado: cancelar
    completado --> enviado_despacho: pasar a Despacho
    cancelado --> [*]
    enviado_despacho --> [*]
```

- Solo se planifica/avanza cuando Ventas ya envió el proyecto.
- Fases y avances solo se editan en `en_desarrollo`.
- La cancelación exige motivo + informe ≥ 30 caracteres y queda en el expediente.

### 3.3 Despacho

```mermaid
stateDiagram-v2
    [*] --> pendiente
    pendiente --> pendiente_cobro: llega con saldo
    pendiente --> pendiente_entrega: llega sin saldo
    pendiente_cobro --> pendiente_entrega: liquidar saldo
    pendiente_cobro --> negado: negar
    pendiente_entrega --> negado: negar
    pendiente_entrega --> entregado: confirmar entrega
    negado --> pendiente_entrega: resolver (sin saldo)
    negado --> pendiente_cobro: resolver (con saldo)
    negado --> entregado: entregar tras resolver
    entregado --> [*]
```

- `entregado` exige saldo 0.
- `negado` vuelve a la cola de pendientes (`cerrados` incluye `negado` y `entregado`).

### 3.4 Fases de Producción

```mermaid
stateDiagram-v2
    [*] --> pendiente
    pendiente --> en_curso: iniciar fase
    en_curso --> completada: completar
    completada --> [*]
```

### 3.5 Incidencias

```mermaid
stateDiagram-v2
    [*] --> abierta
    abierta --> en_proceso: tomar / asignar
    abierta --> cerrada: cerrar sin resolver
    en_proceso --> resuelta: reporte de resolución
    en_proceso --> cerrada: cerrar
    resuelta --> cerrada: cerrar
    cerrada --> [*]
```

`POST /reporte` hace automáticamente `abierta → en_proceso → resuelta` si hacía falta.

## 4. Recorrido completo de un proyecto

```mermaid
flowchart LR
    A["Ventas<br/>crea cliente"] --> B["Ventas<br/>crea proyecto<br/>PRJ-2026-0001"]
    B --> C{"¿Cobro?"}
    C -- "parcial" --> D["cobrado_50<br/>+ factura"]
    C -- "total" --> E["cobrado_100<br/>+ factura"]
    D --> F["enviado_desarrollo"]
    E --> F
    F --> G["Producción<br/>plan + fases + equipo"]
    G --> H["en_desarrollo<br/>avances + adjuntos"]
    H --> I{"¿Se cancela?"}
    I -- "sí" --> J["cancelado<br/>informe obligatorio"]
    I -- "no" --> K["completado<br/>(fases cerradas)"]
    K --> L["enviado_despacho"]
    L --> M{"¿Saldo?"}
    M -- "sí" --> N["pendiente_cobro<br/>liquidar"]
    M -- "no" --> O["pendiente_entrega"]
    N --> O
    O --> P{"Cliente"}
    P -- "acepta" --> Q["entregado<br/>Ventas: cerrado"]
    P -- "rechaza" --> R["negado<br/>motivo + detalle"]
    R --> O
```

## 5. Secuencias por caso de uso

### 5.1 Login y enrutado por rol

```mermaid
sequenceDiagram
    actor U as Usuario
    participant L as LoginPage
    participant API as /api/auth/login
    participant ST as Zustand
    participant R as Router

    U->>L: email + contraseña
    L->>API: POST
    API-->>L: token + user
    L->>ST: setAuth(token, user)
    L->>R: navigate('/panel')
    R->>R: PanelRedirect según departamento
    R-->>U: /ventas · /desarrollo · /despacho · /tecnologia · /rrhh
```

### 5.2 Alta de cliente y proyecto (Ventas)

```mermaid
sequenceDiagram
    participant V as Ventas
    participant API as /api/ventas
    participant DOM as Dominio
    participant DB as SQLite

    V->>API: POST /clientes (todos los datos)
    API->>DOM: create_customer
    DOM-->>API: Ok | Err
    API->>DB: INSERT customer
    API-->>V: 201

    V->>API: POST /proyectos
    API->>DB: verificar customer
    API->>DOM: create_project (título derivado, desc ≥ 20, monto > 0)
    API->>DB: INSERT project + código PRJ-YYYY-NNNN
    API-->>V: ProjectOut
```

### 5.3 Cobro y factura (Ventas)

```mermaid
sequenceDiagram
    participant V as Ventas
    participant API as /api/ventas
    participant DOM as Dominio
    participant DB as SQLite

    V->>API: POST /proyectos/{id}/pagos {monto, método}
    API->>DB: proyecto + pagos previos
    API->>DOM: create_payment (saldo, porcentaje)
    alt excede saldo
        DOM-->>API: Err
        API-->>V: 422
    else válido
        API->>DOM: set_estado_ventas (cobrado_50/100)
        API->>DB: INSERT payment + UPDATE project
        API->>DOM: create_invoice (snapshot)
        API->>DB: INSERT invoice FAC-...
        API->>DB: audit pago + factura
        API->>DB: commit
        API-->>V: 201 PaymentOut
        V->>API: GET /facturas/{id}/pdf
        API-->>V: application/pdf
    end
```

### 5.4 Plan, fases y avance (Producción)

```mermaid
sequenceDiagram
    participant P as Producción
    participant API as /api/desarrollo
    participant DOM as Dominio
    participant DB as SQLite

    P->>API: POST /proyectos/{id}/plan
    API->>DOM: create_plan + create_phase × N
    API->>DB: INSERT plan, fases, miembros
    API->>DOM: estado → en_planificacion
    API-->>P: 201

    P->>API: POST /proyectos/{id}/iniciar
    API->>DOM: en_planificacion → en_desarrollo
    API-->>P: estado

    P->>API: POST /fases/{fid}/estado {target}
    API->>DOM: set_phase_state
    API-->>P: PhaseOut

    P->>API: POST /avance {porcentaje, notas}
    API->>DOM: record_progress
    API-->>P: ProgressOut

    P->>API: POST /completar
    API->>DOM: validar fases
    alt fases abiertas
        API-->>P: 422 con nombres
    else todas completadas
        API->>DOM: en_desarrollo → completado
        API-->>P: estado
    end
```

### 5.5 Liquidación y entrega (Despacho)

```mermaid
sequenceDiagram
    participant D as Despacho
    participant API as /api/despacho
    participant DOM as Dominio
    participant DB as SQLite

    API-->>D: tablero {pendientes, cerrados} + acciones por proyecto

    D->>API: POST /proyectos/{id}/liquidar
    API->>DOM: create_payment(saldo) + ventas → cerrado
    API->>DOM: pendiente_cobro → pendiente_entrega
    API->>DOM: create_invoice (snapshot)
    API->>DB: INSERT payment + invoice + UPDATE project
    API->>DB: audit pago + factura
    API-->>D: 201 + factura (PDF descargable)

    D->>API: POST /proyectos/{id}/confirmar-entrega
    API->>DOM: puede_entregar (saldo 0)
    API->>DB: INSERT dispatch + UPDATE project
    API->>DB: audit entrega_confirmada
    API-->>D: 201 acta interna

    Note over D,API: Si el cliente rechaza:
    D->>API: POST /negar {motivo, detalle}
    API->>DOM: → negado
    D->>API: POST /resolver-negacion
    API->>DOM: → pendiente_cobro / pendiente_entrega
```

### 5.6 Incidencia (cualquier departamento → Tecnología)

```mermaid
sequenceDiagram
    participant U as Cualquier depto
    participant T as Tecnología
    participant API as /api/tecnologia
    participant DB as SQLite

    U->>API: POST /incidencias
    API->>DB: INSERT INC-YYYY-NNNN (orden_llegada)
    API-->>U: 201

    T->>API: GET /incidencias
    API-->>T: cola ordenada + resumen por estado

    T->>API: POST /incidencias/{id}/asignar {user_ids}
    T->>API: POST /incidencias/{id}/estado {target}
    T->>API: POST /incidencias/{id}/reporte
    API->>DB: INSERT report + estado resuelta
    T->>API: POST /adjuntos/incidencia/{id} (evidencia)
    API->>DB: INSERT attachment + archivo en uploads/
```

### 5.7 Adjunto

```mermaid
sequenceDiagram
    participant UI
    participant API as /api/desarrollo
    participant FS as uploads/

    UI->>API: multipart file
    API->>API: validar tipo, MIME, tamaño, nombre
    API->>FS: escribir <id>_<nombre>
    API-->>UI: 201 AttachmentOut

    UI->>API: GET /adjuntos/{id}/descargar (Bearer)
    API->>FS: leer bytes
    API-->>UI: FileResponse
    Note over UI: el cliente crea un blob y dispara la descarga
```

### 5.8 Búsqueda global

```mermaid
sequenceDiagram
    participant U as Usuario
    participant B as Buscador
    participant API as /api/buscar
    participant DOM as dominio/search

    U->>B: escribe ≥ 2 caracteres
    B->>B: debounce 300 ms
    B->>API: GET ?q=
    API->>DOM: validar + tipos_buscables(departamento)
    API->>DOM: buscar_* por categoría permitida
    DOM-->>API: resultados recortados (8/tipo)
    API-->>B: {tipos, resultados}
    B-->>U: grupos con navegación
```

## 6. Flujo de usuarios por rol

### 6.1 Vista general

```mermaid
flowchart TD
    A["Login"] --> B{"Rol"}
    B --> V["Ventas"]
    B --> P["Producción"]
    B --> D["Despacho"]
    B --> T["Tecnología"]
    B --> R["RRHH"]

    V --> V1["Clientes"]
    V --> V2["Proyectos / levantamiento"]
    V --> V3["Cobros + factura PDF"]
    V --> V4["Enviar a Producción"]
    V --> V5["Reportar incidencia"]

    P --> P1["Tablero recibidos/en curso/historial"]
    P --> P2["Plan + fases + equipo"]
    P --> P3["Avances + adjuntos"]
    P --> P4["Completar / enviar a Despacho"]
    P --> P5["Cancelar con informe"]

    D --> D1["Cola pendientes/cerrados"]
    D --> D2["Contacto y saldo"]
    D --> D3["Liquidar"]
    D --> D4["Confirmar entrega / negar"]

    T --> T1["Cola por prioridad + llegada"]
    T --> T2["Asignar técnicos"]
    T --> T3["Reporte + evidencia"]

    R --> R1["Panel global (KPIs)"]
    R --> R2["Usuarios: alta/edición/bloqueo"]
    R --> R3["Proyectos globales"]
    R --> R4["Bitácora"]
```

### 6.2 Ventas

1. Entra y ve la lista de proyectos y clientes.
2. Da de alta el cliente (todos los datos obligatorios).
3. Crea el proyecto con monto y detalles.
4. Registra el pago (50 %, 100 % o parcial); el sistema emite factura PDF.
5. Cuando el cobro alcanza el 50 %, aparece «Enviar a Producción».
6. Tras enviarlo, deja de gestionarlo (sus acciones quedan vacías).
7. En cualquier momento puede reportar una incidencia de Tecnología.

### 6.3 Producción

1. Ve columnas **Recibidos**, **En curso**, **Historial**.
2. En «Recibidos» crea el plan, fases y asigna miembros de Producción.
3. Inicia el desarrollo.
4. Actualiza fases y registra avances con notas.
5. Adjunta documentos/imágenes al proyecto, fases o plan.
6. Cuando todas las fases están completadas, marca «Completado».
7. Envía a Despacho (el saldo decide si espera cobro o entrega).
8. Si el proyecto se frustra, cancela con motivo + informe.

### 6.4 Despacho

1. Ve **Pendientes** y **Cerrados**.
2. Abre el proyecto y contacta al cliente con los datos del levantamiento.
3. Si hay saldo, «Liquidar saldo» (cobro total del resto, genera factura PDF).
4. Con saldo 0, «Confirmar entrega»: fecha, destinatario, detalle.
5. Si el cliente rechaza, «Negar» con motivo y detalle.
6. Una negación se puede resolver y volver a la cola.

### 6.5 Tecnología

1. Ve la cola ordenada por prioridad y luego llegada.
2. Consulta el resumen por estado.
3. Asigna uno o varios técnicos.
4. Mueve estado (`abierta → en_proceso`).
5. Registra diagnóstico, solución y horas; pasa a `resuelta`.
6. Adjunta evidencia fotográfica a la incidencia.
7. Cierra (`resuelta → cerrada`).

### 6.6 RRHH

1. Panel general con KPIs de todos los departamentos.
2. Usuarios: alta, edición, cambio de departamento, bloqueo/desactivación,
   restablecimiento de contraseña.
3. Proyectos: vista global de solo lectura.
4. Bitácora: últimas acciones sensibles.
5. Puede reportar incidencias.

## 7. Flujos alternativos y errores

| Situación | Comportamiento |
|---|---|
| Credenciales inválidas | 401, mensaje genérico, auditoría `login_fallido` |
| Usuario bloqueado/desactivado | 403 con motivo; el token deja de servir |
| Token expirado | 401 → el cliente limpia sesión y vuelve a login |
| Intento de acción de otro módulo | 403 con departamento requerido |
| Proyecto sin cliente válido | 404 al crear |
| Cliente con proyectos | 422 al intentar borrarlo |
| Descripción corta / monto ≤ 0 | 422 |
| Pago mayor al saldo | 422 |
| Pasar a Producción sin 50 % | 422 |
| Completar con fases abiertas | 422 con lista de pendientes |
| Cancelar sin informe suficiente | 422 |
| Entregar con saldo | 422 con el saldo formateado |
| Incidencia cerrada → asignar | 422 |
| Archivo > 20 MB o MIME no permitido | 422 |
| Archivo físico desaparecido | 404 al descargar |
| Servidor caído | `ApiError(0, 'No hay conexión con el servidor')` |
| Plan ya creado | 409 |

## 8. Trazabilidad

- Cada acción sensible deja una fila en `audit_logs` (best-effort).
- Cada proyecto conserva su historia: pagos, facturas, plan, fases, avances, miembros,
  cancelación, entrega y negación.
- Los adjuntos son polimórficos y cuelgan de la entidad correspondiente.
- RRHH es el único que puede leer la bitácora completa.
