"""Lanzador de escritorio de GCISCAR.exe (PyInstaller): servidor + ventana nativa.

Abre una ventana "GCISCAR" (WebView2 de Windows, sin barra de navegador) apuntando
al servidor local; al cerrar la ventana se apaga el servidor.
"""

from __future__ import annotations

import socket
import sys
import threading
import time
import urllib.request

# En modo ventana Python deja stdout/stderr en None; sin esto el logging revienta.
if sys.stdout is None:
    sys.stdout = open("nul", "w")
if sys.stderr is None:
    sys.stderr = open("nul", "w")

import webview  # noqa: E402

from app.main import app  # noqa: E402

URL = "http://127.0.0.1:8000"


def _puerto_libre() -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", 8000)) != 0


def _aviso(texto: str) -> None:
    import ctypes

    ctypes.windll.user32.MessageBoxW(None, texto, "GCISCAR", 0x10)  # MB_ICONERROR


def _servidor_listo(limite_s: float = 20.0) -> bool:
    fin = time.time() + limite_s
    while time.time() < fin:
        try:
            urllib.request.urlopen(f"{URL}/api/health", timeout=2)
            return True
        except OSError:
            time.sleep(0.4)
    return False


def main() -> None:
    if not _puerto_libre():
        _aviso("Ya hay otra instancia de GCISCAR abierta.")
        return

    from uvicorn import Config, Server

    servidor = Server(Config(app, host="127.0.0.1", port=8000, log_level="warning"))
    threading.Thread(target=servidor.run, daemon=True).start()
    if not _servidor_listo():
        _aviso("No se pudo iniciar el servidor local (puerto 8000).")
        return

    # La app descarga facturas PDF y adjuntos desde la ventana.
    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.create_window("GCISCAR", URL, width=1440, height=900, min_size=(1024, 640))
    webview.start()  # bloquea hasta que se cierre la ventana

    servidor.should_exit = True


if __name__ == "__main__":
    main()
