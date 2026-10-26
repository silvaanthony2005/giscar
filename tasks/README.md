# Flujo de agentes por fases

Sistema de agentes especializados, cada uno con su modelo, que se comunican **solo** a través de `tasks/current_plan.md`. El objetivo: tokens baratos donde hay que ser barato, modelo potente solo donde aporta.

## Agentes y modelos

| Agente      | Fase    | Modelo                            | Coste (in/out por millón) |
|-------------|---------|-----------------------------------|---------------------------|
| `@planner`  | 1. Plan | `opencode-go/kimi-k3.1-pro#high`  | $2 / $10                  |
| `@structure`| 2. Arq. | `opencode-go/glm-5.3`             | $1.4 / $4.4               |
| `@coder`    | 3. Código | `opencode-go/deepseek-v4-pro`   | $0.66 / $1.98             |
| `@auditor`  | 4. Revisión | `opencode-go/claude-haiku-5-5`| $0.1 / $0.5               |
| `@fixer`    | 3b. Fix | `opencode-go/mimo-v2.6-flash`     | $0.14 / $0.28             |
| `@scout`    | Explor. | `opencode-go/mimo-v2.6-flash`     | $0.14 / $0.28             |

Precios verificados el 26/10/2026; cambian con el tiempo. Si un modelo gratuito (`beam-free`) rechaza por cuota, fallback: `opencode-go/mimo-v2.5` ($0.14/$0.28).

## Cómo ejecutar el flujo

1. **`@planner`** con la petición del usuario → crea/actualiza `tasks/current_plan.md` con tareas `- [ ]`.
2. **`@scout`** (opcional, gratis) → si falta contexto: "¿dónde está X?", "¿qué patrón usa el repo para Y?".
3. **`@structure`** → por cada tarea pendiente, define archivos, firmas y esquemas en la sección `### Estructura`.
4. **`@coder`** → ejecuta **una** tarea `- [ ]` con estructura definida. Valida el criterio de éxito y marca `[x]` o `[!]`.
5. **`@auditor`** → solo lectura. Aprueba `[x]` o marca `[!]` con `archivo:línea` y qué debería ocurrir.
6. **`@fixer`** → si hay `[!]`, corrige lo mínimo y revalida.
7. Repite 3-6 hasta que no queden `- [ ]` ni `[!]`.

En el TUI: escribe `@nombre-agente` seguido de la instrucción. Un subagente corre con contexto fresco — esto es lo que ahorra tokens: el siguiente agente lee el archivo, no el historial de chat.

## Reglas de la casa

- El auditor **nunca** edita código (permisos lo impiden); solo emite veredicto.
- `[x]` exige criterio de éxito ejecutado y verificado. Un `[x]` sin validación se considera mentira.
- `[!]` siempre lleva causa raíz, no síntoma.
- Nadie borra tareas ya `[x]`; el plan solo crece o se corrige.
