# GCISCAR — Documentación técnica

Sistema de información interno para empleados (25–100 usuarios) que corre en **una sola PC
local**, sin exposición a internet. Gestiona el ciclo completo de un proyecto comercial:

```
Ventas → Producción (Desarrollo) → Despacho
             ↑
      Tecnología (incidencias transversales)
             ↑
            RRHH (lectura global + gestión de usuarios)
```

## Índice

| Documento | Qué contiene |
|---|---|
| [01 · Arquitectura](01-arquitectura.md) | Capas, reglas de dependencia, patrones (DDD funcional), decisiones y deuda técnica |
| [02 · Backend](02-backend.md) | Módulos de dominio, reglas de negocio, máquinas de estado, routers, tests |
| [03 · Frontend](03-frontend.md) | Atom Design, rutas, estado (Zustand + React Query), cliente API, design system |
| [04 · Base de datos](04-base-de-datos.md) | Modelo entidad-relación, 17 tablas, índices, dinero en centavos, migraciones |
| [05 · API e integraciones](05-api-e-integraciones.md) | 56 endpoints, contratos, códigos HTTP, descargas, Swagger, integraciones |
| [06 · Seguridad](06-seguridad.md) | JWT, Argon2, matriz de permisos, uploads, auditoría, riesgos y checklist |
| [07 · Flujos y procesos](07-flujos-y-procesos.md) | Flujo de datos, secuencias, diagramas de estado y recorridos de usuario |
| [08 · Infraestructura y despliegue](08-infraestructura-y-despliegue.md) | Dev, producción y .exe; build, instalador, backup, variables |

## Ficha rápida

| Aspecto | Valor |
|---|---|
| Nombre | GCISCAR (`app_name`) |
| Versión | 0.1.0 |
| Backend | Python ≥ 3.12 · FastAPI · SQLAlchemy 2 · SQLite (WAL) · `uv` |
| Frontend | React 19 · TypeScript · Vite 8 · Tailwind 4 · React Router 7 · TanStack Query 5 · Zustand 5 |
| PDFs | reportlab, generados en el servidor |
| Despliegue | `127.0.0.1:8000` (API + build) o `.exe` con ventana WebView2 |
| Pruebas | 187 tests de backend en verde (`uv run pytest -q`) |
| Tablas | 17 (`users`, `customers`, `projects`, …) |
| Endpoints | 56 bajo `/api` |
| Idioma de interfaz y documentos | Español |
| Facturación | Registro interno; **sin pasarela de pago** |

## Arranque rápido

```bash
# Desde la raíz del repo
npm run api      # API en http://127.0.0.1:8000  (uvicorn --reload)
npm run dev      # Frontend en http://127.0.0.1:5173 (Vite, proxy /api → 8000)

npm run test     # pytest (backend)
npm run lint     # oxlint + ruff
npm run build    # typecheck + bundle del frontend
npm run check    # build + lint + test
npm run package  # frontend + .exe + instalador Inno Setup
```

## Cuentas semilla

Contraseña común: `giscar1234` (cambiar en producción).

| Departamento | Correo | Nombre |
|---|---|---|
| RRHH (admin) | `rrhh@giscar.com` | Ana Reyes |
| Ventas | `ventas@giscar.com` | Luis Pérez |
| Producción | `produccion@giscar.com` | Marta Gómez |
| Despacho | `despacho@giscar.com` | Carlos Díaz |
| Tecnología | `tecnologia@giscar.com` | Sofía López |

> El departamento se guarda como `desarrollo`; «Producción» es solo la etiqueta visible.
> El seed es idempotente y se ejecuta en cada arranque (`seed()` en `startup`).

## Documentos fuente

- `AGENTS.md` — convenciones obligatorias (DDD, FP, frontend pasivo, Atom Design).
- `.sisyphus/plans/giscar-sistema-informacion-plan.md` — plan aprobado por fases.
- `README.md` (raíz) — guía operativa del repositorio.
- `installer/README.md` — empaquetado y comportamiento en la PC destino.

## Nota sobre el estado del repo

La documentación describe el código **tal como está hoy**, incluidas las desviaciones
respecto al plan (por ejemplo, `application/` está vacío y los routers orquestan
directamente). Cada documento marca esas diferencias en su sección de deuda técnica.
