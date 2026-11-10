#!/usr/bin/env python3
"""Genera la versión HTML de la documentación en `docs/html/`.

Uso (desde la raíz del repo):

    uv run --project backend --with markdown python docs/build_html.py

Requiere `markdown` solo en tiempo de build; no se añade a las dependencias del
proyecto. Los diagramas Mermaid se renderizan con `docs/html/assets/mermaid.min.js`
(auto-hospedado, sin CDN en tiempo de ejecución).
"""

from __future__ import annotations

import html as html_lib
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path

try:
    import markdown
except ModuleNotFoundError:  # pragma: no cover - ayuda de uso
    raise SystemExit(
        "Falta el paquete markdown. Ejecuta:\n"
        "  uv run --project backend --with markdown python docs/build_html.py"
    ) from None

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "html"
ASSETS = OUT / "assets"

DOCS = [
    "README.md",
    "01-arquitectura.md",
    "02-backend.md",
    "03-frontend.md",
    "04-base-de-datos.md",
    "05-api-e-integraciones.md",
    "06-seguridad.md",
    "07-flujos-y-procesos.md",
    "08-infraestructura-y-despliegue.md",
]

LABELS = {
    "README.md": "Inicio",
    "01-arquitectura.md": "Arquitectura",
    "02-backend.md": "Backend",
    "03-frontend.md": "Frontend",
    "04-base-de-datos.md": "Base de datos",
    "05-api-e-integraciones.md": "API e integraciones",
    "06-seguridad.md": "Seguridad",
    "07-flujos-y-procesos.md": "Flujos y procesos",
    "08-infraestructura-y-despliegue.md": "Infraestructura",
}

FONTS = {
    "text-UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2": "inter-latin.woff2",
    "text-tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPxDcwg.woff2": (
        "jetbrains-latin.woff2"
    ),
}

MERMAID_RE = re.compile(
    r'<pre><code class="language-mermaid">(.*?)</code></pre>', re.DOTALL
)


def slugify(value: str, separator: str) -> str:
    """Slug compatible con los enlaces GitHub que ya usan los .md."""
    value = unicodedata.normalize("NFKC", value).strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    return re.sub(r"[-\s]+", separator, value) or "seccion"


def convert(text: str) -> tuple[str, str]:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"slugify": slugify, "permalink": False, "toc_depth": "2-3"}},
        output_format="html5",
    )
    body = md.convert(text)
    toc_match = re.search(r"<ul>.*</ul>", md.toc, re.DOTALL)
    toc = toc_match.group(0) if toc_match else ""
    return body, toc


def mermaid_blocks(body: str) -> str:
    """Convierte los cercados ```mermaid en nodos que Mermaid puede renderizar."""

    def replace(match: re.Match[str]) -> str:
        source = html_lib.unescape(match.group(1)).strip()
        return f'<div class="mermaid">\n{source}\n</div>'

    return MERMAID_RE.sub(replace, body)


def postprocess(body: str) -> str:
    body = mermaid_blocks(body)
    # Enlaces entre documentos Markdown.
    body = body.replace(".md#", ".html#").replace('.md"', '.html"')
    # Enlaces externos en pestaña nueva.
    body = re.sub(
        r'<a href="(https?://[^"]+)"',
        r'<a href="\1" target="_blank" rel="noopener noreferrer"',
        body,
    )
    # Tablas con scroll horizontal sin romper el marcado.
    body = body.replace("<table>", '<div class="table-wrap"><table>')
    body = body.replace("</table>", "</table></div>")
    # Listas de verificación (Markdown no las soporta de serie).
    body = re.sub(r"<li>\[ \] ", '<li class="task"><span class="task-box"></span>', body)
    return re.sub(
        r"<li>\[[xX]\] ",
        '<li class="task"><span class="task-box is-done">✓</span>',
        body,
    )


def page_name(doc: str) -> str:
    return "index.html" if doc == "README.md" else doc.replace(".md", ".html")


def title_of(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Documentación"


def nav_html(current: str) -> str:
    items = []
    for doc in DOCS:
        label = LABELS[doc]
        number = "◎" if doc == "README.md" else doc[:2]
        active = " is-active" if doc == current else ""
        aria = ' aria-current="page"' if doc == current else ""
        items.append(
            f'<a class="nav-link{active}" href="{page_name(doc)}"{aria}'
            f' data-keywords="{html_lib.escape(label.lower())}">'
            f'<span class="nav-num">{number}</span>'
            f"<span>{html_lib.escape(label)}</span></a>"
        )
    return "\n        ".join(items)


def pager_html(doc: str) -> str:
    index = DOCS.index(doc)
    parts = []
    if index > 0:
        prev = DOCS[index - 1]
        parts.append(
            f'<a class="page-link prev" href="{page_name(prev)}">'
            f"<small>Anterior</small><span>← {html_lib.escape(LABELS[prev])}</span></a>"
        )
    else:
        parts.append("<span></span>")
    if index < len(DOCS) - 1:
        nxt = DOCS[index + 1]
        parts.append(
            f'<a class="page-link next" href="{page_name(nxt)}">'
            f"<small>Siguiente</small><span>{html_lib.escape(LABELS[nxt])} →</span></a>"
        )
    else:
        parts.append("<span></span>")
    return "\n      ".join(parts)


def render(doc: str, title: str, body: str, toc: str, generated: str) -> str:
    label = LABELS[doc]
    crumbs = (
        '<nav class="crumbs" aria-label="Ruta"><a href="index.html">Documentación</a>'
        f"<span>/</span><span>{html_lib.escape(label)}</span></nav>"
    )
    toc_block = (
        f'<aside class="toc" aria-label="En esta página">'
        f'<p class="toc-title">En esta página</p>{toc}</aside>'
        if toc
        else ""
    )
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <meta name="description" content="{html_lib.escape(title)} — documentación técnica de GCISCAR">
  <title>{html_lib.escape(title)} · GCISCAR</title>
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <a class="skip-link" href="#contenido">Saltar al contenido</a>

  <header class="topbar">
    <button class="menu-btn" type="button" data-menu aria-label="Abrir menú"
            aria-expanded="false" aria-controls="sidebar">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="2"
              stroke-linecap="round"/>
      </svg>
    </button>
    <a class="brand" href="index.html">
      <span class="logo" aria-hidden="true">G</span>
      <span class="brand-text"><strong>GCISCAR</strong><small>Documentación técnica</small></span>
    </a>
    <div class="topbar-right">
      <span class="pill">v0.1.0</span>
      <span class="pill pill-soft">Sistema local</span>
    </div>
  </header>

  <div class="layout">
    <aside class="sidebar" id="sidebar" aria-label="Documentación">
      <div class="nav-search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/>
          <path d="m20 20-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <input type="search" placeholder="Filtrar secciones…" aria-label="Filtrar secciones"
               data-nav-filter autocomplete="off">
      </div>
      <nav class="nav" aria-label="Documentos">
        <p class="nav-heading">Documentación</p>
        {nav_html(doc)}
      </nav>
      <div class="sidebar-foot">
        <span class="status-dot" aria-hidden="true"></span>
        <span>GCISCAR v0.1.0<br>Actualizado {generated}<br>
        <a href="../{doc}">Markdown fuente</a></span>
      </div>
    </aside>

    <div class="scrim" data-scrim hidden></div>

    <main class="content" id="contenido">
      {crumbs}
      <article class="prose">
{body}
      </article>
      <footer class="page-foot">
      {pager_html(doc)}
        <p class="source">Documento generado desde
          <a href="../{doc}">{doc}</a> · {generated}</p>
      </footer>
    </main>

    {toc_block}
  </div>

  <script defer src="assets/mermaid.min.js"></script>
  <script defer src="assets/docs.js"></script>
</body>
</html>
"""


def copy_fonts() -> None:
    fonts_dir = ASSETS / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    origin = REPO / "frontend" / "public" / "fonts"
    for source_name, target_name in FONTS.items():
        source = origin / source_name
        target = fonts_dir / target_name
        if source.exists():
            shutil.copy2(source, target)
        else:
            print(f"AVISO: no encontrada la fuente {source}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    copy_fonts()

    favicon = REPO / "frontend" / "public" / "favicon.svg"
    if favicon.exists():
        shutil.copy2(favicon, OUT / "favicon.svg")

    if not (ASSETS / "mermaid.min.js").exists():
        print("AVISO: falta assets/mermaid.min.js; los diagramas se verán como código.")

    generated = date.today().isoformat()
    for doc in DOCS:
        text = (HERE / doc).read_text(encoding="utf-8")
        title = title_of(text)
        body, toc = convert(text)
        page = render(doc, title, postprocess(body), toc, generated)
        (OUT / page_name(doc)).write_text(page, encoding="utf-8")
        print(f"  {page_name(doc)}")

    print(f"\nOK: {len(DOCS)} paginas generadas en {OUT}")


if __name__ == "__main__":
    main()
