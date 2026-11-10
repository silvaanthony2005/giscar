# Assets de la documentación HTML

| Archivo | Origen |
|---|---|
| `mermaid.min.js` | [Mermaid](https://mermaid.js.org/) 11, MIT. Licencia en `mermaid.LICENSE.txt`. Auto-hospedado para que los diagramas funcionen sin internet. |
| `style.css` | Hoja de estilos del sitio, alineada con los tokens M3 de GCISCAR. |
| `docs.js` | Menú móvil, filtro del índice, copiar código, TOC activo y render de Mermaid. |
| `fonts/` | Inter y JetBrains Mono, copiadas de `frontend/public/fonts/` (SIL Open Font License). |

Regenerar el sitio:

```bash
npm run docs
```
