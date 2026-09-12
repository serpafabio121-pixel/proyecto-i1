"""Inicia una única URL para PC y celular."""

from __future__ import annotations

import socket
import subprocess
import sys


def local_ip() -> str:
    addresses = {
        item[4][0]
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        if not item[4][0].startswith("127.")
    }
    preferred = sorted(
        addresses,
        key=lambda value: (0 if value.startswith("192.168.") else 1, value),
    )
    return preferred[0] if preferred else "IP_DEL_PC"


if __name__ == "__main__":
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f'Instala dependencias con "{sys.executable}" -m pip install -r requirements.txt'
        ) from exc

    ip = local_ip()
    print("Detector de grietas")
    print(f"Celular: http://{ip}:8501")
    print("PC:      http://localhost:8501")
    print("El celular se limita automáticamente a cargar archivos.")
    print("Mantén esta ventana abierta.")
    raise SystemExit(
        subprocess.call(
            [
                sys.executable, "-m", "streamlit", "run", "app/main.py",
                "--server.address=0.0.0.0", "--server.port=8501",
            ]
        )
    )
