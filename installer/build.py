"""Construye GCISCAR: frontend + .exe (PyInstaller) + instalador (Inno Setup).

Uso desde la raiz del repo:
    uv run --project backend python installer/build.py          # todo
    uv run --project backend python installer/build.py --exe    # solo el .exe
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "installer"
BACKEND = ROOT / "backend"


def run(cmd: str, cwd: Path) -> None:
    print(f"\n>>> {cmd}", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True, shell=True)


def find_iscc() -> Path | None:
    direct = shutil.which("ISCC")
    if direct:
        return Path(direct)
    candidatos = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ]
    return next((p for p in candidatos if p.exists()), None)


def main() -> None:
    run(f'npm --prefix "{ROOT / "frontend"}" run build', cwd=ROOT)

    run(
        "uv run pyinstaller --noconfirm --clean "
        f'--distpath "{INSTALLER / "dist"}" --workpath "{INSTALLER / "build"}" '
        f'"{INSTALLER / "giscar.spec"}"',
        cwd=BACKEND,
    )
    print(f"\nExe portatil: {INSTALLER / 'dist' / 'GCISCAR' / 'GCISCAR.exe'}")

    if "--exe" in sys.argv[1:]:
        return

    iscc = find_iscc()
    if iscc is None:
        print("ERROR: no encontre ISCC.exe (Inno Setup 6). Instalalo o usa --exe.")
        sys.exit(1)

    run(f'"{iscc}" "{INSTALLER / "GCISCAR.iss"}"', cwd=INSTALLER)
    print(f"\nInstalador en: {INSTALLER / 'output'}")


if __name__ == "__main__":
    main()
