# -*- mode: python ; coding: utf-8 -*-
# PyInstaller de GCISCAR (Windows, onedir: carpeta con el .exe + _internal).
# Se invoca desde installer/build.py; no hace falta tocar nada más.
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).parent  # noqa: F821 - SPECPATH lo define PyInstaller
BACKEND = ROOT / "backend"
FRONTEND_DIST = ROOT / "frontend" / "dist"

if not FRONTEND_DIST.is_dir():
    raise SystemExit("Falta frontend/dist: ejecuta `npm run build` en la raiz antes de empaquetar.")

a = Analysis(
    [str(Path(SPECPATH) / "entry.py")],  # noqa: F821
    pathex=[str(BACKEND)],
    binaries=[],
    datas=[
        # El frontend se sirve desde el bundle (main.py lee sys._MEIPASS en modo frozen).
        (str(FRONTEND_DIST), "frontend/dist"),
        # Fuentes y datos que reportlab busca junto a su paquete.
        *collect_data_files("reportlab"),
        # DLLs de WebView2 que pywebview carga en tiempo de ejecucion.
        *collect_data_files("webview"),
    ],
    hiddenimports=[
        # uvicorn elige loop/protocolo por import dinamico: sin esto el .exe no arranca.
        *collect_submodules("uvicorn"),
        # SQLAlchemy resuelve el dialecto por nombre en tiempo de ejecucion.
        *collect_submodules("sqlalchemy.dialects.sqlite"),
        # pywebview carga su backend de plataforma dinamicamente.
        *collect_submodules("webview"),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # mypy entra de rebote por pydantic.mypy (plugin de análisis); en runtime no se usa.
    excludes=["mypy"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GCISCAR",
    debug=False,
    strip=False,
    upx=True,
    # App de escritorio: sin ventana de consola; los logs del servidor se descartan.
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="GCISCAR",
)
