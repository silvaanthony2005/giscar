# AGENTS.md

## Project status

Greenfield. As of writing there is **no application code yet** — no git repo, no
`package.json`, no `pyproject.toml`, no build/test/lint config. Do not invent
build/test commands; they do not exist until the project is scaffolded.

Only sources of truth right now:
- `readme.md` — raw requirements, in Spanish, prose only. Treat as the client's intent.
- `.sisyphus/plans/giscar-sistema-informacion-plan.md` — the refined, approved plan.
  **Read this first.** It is more accurate than `readme.md` where they differ.

## What is being built

"GCISCAR" — internal information system for company employees (25–100 users),
running on a **single local PC** (not internet-facing). Login with role-based
access across 5 departments:

- **Ventas** (sales): capture client + project details, charge 50% or 100%,
  emit invoice PDF.
- **Desarrollo** (development): build dev plan, assign people, phases + time
  estimates, track progress, attach docs/images, cancel with written report.
- **Despacho** (dispatch): contact client, collect remaining balance, deliver.
  States: `entregado` / `pendiente_entrega` / `negado`.
- **Tecnología**: cross-department incident queue for hardware/electronic
  failures, ordered by arrival + severity, resolved with report + photo evidence.
- **RRHH**: admin role — full read across all departments, manage/block/reassign
  users.

## Confirmed technical decisions (do not change without asking)

- **Frontend**: React + TypeScript + Vite, **Atom Design** (atoms/molecules/
  organisms/templates), Tailwind CSS, Spanish UI.
- **Backend**: FastAPI, **DDD** layering (domain / application / infrastructure)
  with a functional style — pure functions, immutability, higher-order
  functions, `Result` types over exceptions in the domain layer.
- **Database**: **SQLite** (single file, WAL mode), via SQLAlchemy. Keep it
  lightweight — this is a hard requirement.
- **Billing**: internal record-keeping only. **No** payment gateway integration.
- **PDFs** (invoices, reports): generated **server-side** (reportlab), not in
  the browser.
- **Deployment**: local, single PC. Uvicorn serves the API; FastAPI serves the
  built frontend.

## Functional programming & DDD conventions (MANDATORY)

These rules exist to prevent long-term bugs. Follow them or tests will fail.

### Frontend is passive — the backend does ALL processing (MANDATORY)
- The React client **only** renders data the API returns and sends user input
  back. It must not compute business results.
- No totals, balances, percentages, averages, counts, sorting/filtering by
  business rules, state transitions, permission checks, or derived fields in
  the frontend. Ask the API for an already-computed value.
- Frontend may only do **presentational** helpers: number/currency/date
  formatting (`shared/lib/format.ts`), UI state (open/closed modals), and
  HTML `required`/`minLength` for UX. The server is the single source of truth
  and must re-validate everything anyway.
- If a screen needs a computed value, add an endpoint that returns it — do not
  compute it in a React component or a Zustand selector.

### Design system — Stitch gives tokens, not markup (MANDATORY)
- The visual language comes from the Stitch project **"Enterprise Information
  System UI"** (Material Design 3). From it we extracted **only the design
  system** — palette, type scale, spacing, radii, shadows — into
  `frontend/src/index.css` (`@theme`). **Never copy Stitch's page HTML.**
- Everything is rebuilt as Atom Design components so it is reusable:
  `atoms/` (`Icon`, `Tooltip`, `Badge`, `Button`, `Card`, `Input`),
  `molecules/`, `organisms/`, `templates/` (`TopBar`, `Sidebar`,
  `PageHeader`, `DashboardLayout`). Nav config lives in
  `shared/lib/nav.ts`.
- Icons are Material Symbols via `atoms/Icon.tsx`. Fonts (Inter, JetBrains
  Mono, Material Symbols) are **self-hosted** in `frontend/public/fonts/` —
  the deployment is local and may have no internet, so nothing may be loaded
  from a CDN at runtime.
- New screens must reuse these components and tokens; do not introduce
  one-off colors, `text-*` sizes, or Tailwind palette classes
  (`text-emerald-600` etc.) — use the M3 tokens instead.

### Immutability — never mutate
- Domain models are `@dataclass(frozen=True)`. **Never** assign to a field.
  To "change" a model, return a **new** instance via `dataclasses.replace(...)`.
- Never mutate dicts/lists you received as arguments. Build new ones:
  `{**d, "k": v}`, `[*lst, item]`, `list(map(...))`.
- No `global` state, no module-level mutable singletons in `domain/`.
- Prefer `tuple` over `list` for fixed collections in the domain layer.

### Pure functions — same input, same output, no side effects
- Everything in `domain/**/service.py` must be **pure**: no DB, no file I/O,
  no network, no `print`, no reading env/time directly.
- Time and IDs are **passed in** as arguments (`now: datetime`, `id: str`), never
  generated inside a pure function. Side-effectful wrappers in
  `infrastructure/` supply them.
- A pure function may only: read its arguments, call other pure functions, and
  return a value. Nothing else.

### Higher-order functions — use them, don't reinvent loops
- Transform with `map`, select with `filter`/`any`/`all`, aggregate with
  `functools.reduce` or `sum`. Avoid manual `for` + index mutation.
- Prefer comprehension (`[f(x) for x in xs if p(x)]`) when clearer than
  `list(map(f, filter(p, xs)))`. Both are fine; be consistent per module.
- Write your own small HOFs where it removes duplication, e.g. `pipe`,
  `curry`, `partial`-style helpers in `domain/shared/functions.py`.
- Never use HOFs to hide side effects — a `map` that writes to disk is a bug.

### `Result` over exceptions in the domain layer
- Domain functions return `Result[Ok, Err]` (see `domain/shared/types.py`).
  **Never** `raise` for expected business failures (invalid state, insufficient
  payment, blocked user, etc.).
- `raise` only for truly unexpected programmer errors (assertion/invariant
  violation). Infrastructure may translate `Result` to HTTP 2xx/4xx.
- Always `match`/`unwrap` results explicitly — never ignore a `Result`.

### Single source of truth & explicit state
- The **Project** aggregate owns its state machine. All transitions go through
  the pure state machine — never set `estado_*` fields ad hoc.
- Business invariants live in the domain model/service, **not** in routes or UI.
  The same rule enforced twice (client + server) must agree; the server wins.

### Dependency direction — never invert
- `domain/` imports **nothing** from FastAPI, SQLAlchemy, Pydantic, or
  `infrastructure/`. Only stdlib + `domain/shared`.
- `application/` imports `domain/`; it orchestrates use cases and receives
  repositories as injected `Protocol`s.
- `infrastructure/` implements `Protocol`s (repos, clock, id gen, storage) and
  wires FastAPI. Routes stay thin: parse → call use case → map `Result` → respond.
- When adding a dependency, ask: "does the domain need to know about this?" If
  no, it belongs in infrastructure.

### Testing shape
- Domain tests import **only** domain code — they must run with no DB, no server.
- Because domain is pure, test via plain function calls with constructed inputs
  and asserted `Result` outputs. No mocks needed for the domain layer.

## Repository layout (target)

```
backend/app/
  domain/            # PURE. frozen dataclasses, pure services, Result types
    shared/          #   types.py (Result, Money), functions.py (HOFs), state_machine.py
    user/ customer/ project/ payment/ invoice/
    development/ dispatch/ incidence/ attachment/
  application/       # use cases; depends on domain only
  infrastructure/    # FastAPI routers, SQLAlchemy, security, storage
  main.py
frontend/src/
  atoms/ molecules/ organisms/ templates/ pages/ entities/ shared/ app/
backend/uploads/     # runtime file storage (gitignored)
```

## Working agreement

- Follow the plan's 6 phases in order (scaffold → auth/domain → ventas →
  desarrollo → despacho+tecnología → RRHH/polish).
- Domain logic stays pure and framework-free. Persistence and I/O in
  `infrastructure/`.
- Model the **Project** aggregate state machine explicitly (Ventas → Desarrollo
  → Despacho).
- User-facing text, labels, and documents are in **Spanish**.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

## agent-skills (installed globally in ~/.config/opencode/skills)

25 engineering skills (Addy Osmani's pack). Before acting, check whether one
applies and load it with the `skill` tool; follow the skill's workflow to the
end — do not partially apply it or skip its spec/plan/test steps.

Intent → skill:
- New feature → `spec-driven-development` → `planning-and-task-breakdown` → `incremental-implementation` + `test-driven-development`
- Bug / unexpected behavior → `debugging-and-error-recovery`
- Review before merge → `code-review-and-quality`
- Simplify existing code → `code-simplification`
- UI work → `frontend-ui-engineering`; API/interface design → `api-and-interface-design`
- Auth, user input, data storage → `security-and-hardening`
- Ship/deploy → `shipping-and-launch`; git commits → `git-workflow-and-versioning`

Project-specific rules above (DDD, FP, Spanish UI) always win over a skill's
generic advice when they conflict.
