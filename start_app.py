"""Inicia el detector con una URL válida para el equipo y otra para la red local."""

from __future__ import annotations

import socket
import subprocess
import sys


def _local_ip() -> str:
    try:
        connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        connection.connect(("8.8.8.8", 80))
        address = connection.getsockname()[0]
        connection.close()
        return address
    except OSError:
        return "IP_DEL_COMPUTADOR"


if __name__ == "__main__":
    ip = _local_ip()
    print("Detector de grietas")
    print("PC:      http://localhost:8501")
    print(f"Celular: http://{ip}:8501")
    print("Ambos equipos deben estar en la misma Wi-Fi.")
    print("Para cámara en celular, usa una URL HTTPS de Streamlit Community Cloud.")
    print()
    raise SystemExit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app/main.py",
                "--server.address=0.0.0.0",
                "--server.port=8501",
            ]
        )
    )
