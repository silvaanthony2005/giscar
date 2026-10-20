# Empaquetado de GCISCAR

Requisitos en la PC de compilación: Node.js, `uv` (Python 3.12) e Inno Setup 6.

```bash
uv run --project backend python installer/build.py          # frontend + .exe + instalador
uv run --project backend python installer/build.py --exe    # solo el .exe portátil
```

## Salidas

| Archivo | Qué es |
|---|---|
| `installer/dist/GCISCAR/GCISCAR.exe` | Portable: carpeta completa con todas las dependencias. |
| `installer/output/GCISCAR-Setup-0.1.0.exe` | Instalador Inno Setup. |

También disponible como `npm run package` desde la raíz.

## Comportamiento en la PC destino

- Instalación por usuario (sin administrador) en `%LOCALAPPDATA%\Programs\GCISCAR`.
- Al ejecutar abre una **ventana nativa «GCISCAR»** (WebView2 de Windows, sin barra
  de navegador); al cerrar la ventana se apaga el servidor. Puerto `127.0.0.1:8000`.
- Los datos se guardan en `%LOCALAPPDATA%\GCISCAR` (`giscar.db`, `uploads/`), fuera
  de la carpeta de instalación: sobreviven a actualizaciones y desinstalaciones.
- Primera ejecución crea los usuarios iniciales (`rrhh@giscar.com`, `ventas@giscar.com`,
  `desarrollo@giscar.com`, `despacho@giscar.com`, `tecnologia@giscar.com`),
  todos con contraseña `giscar1234`.
