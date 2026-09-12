"""Inicia servidores independientes para PC y celular."""

from __future__ import annotations

import subprocess
import sys
import socket

from start_mobile import local_ip


def port_in_use(port: int) -> bool:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(0.5)
    try:
        return probe.connect_ex(("127.0.0.1", port)) == 0
    finally:
        probe.close()


def streamlit_command(port: int, address: str, device_mode: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app/main.py",
        f"--server.address={address}",
        f"--server.port={port}",
    ]


def check_dependencies() -> None:
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Faltan dependencias en este entorno de Python. Ejecuta primero:\n"
            f'  "{sys.executable}" -m pip install -r requirements.txt\n'
            "Después vuelve a ejecutar: python start_app.py"
        ) from exc


if __name__ == "__main__":
    check_dependencies()
    ip = local_ip()
    print("Detector de grietas")
    print("PC:      http://localhost:8501")
    print(f"Celular: http://{ip}:8502")
    print("Usa la IP actual impresa aquí; no reutilices una URL de una ejecución anterior.")
    print("El celular queda limitado a cargar fotos y videos; no usa cámara directa.")
    print()
    if port_in_use(8501) or port_in_use(8502):
        raise SystemExit("Los puertos 8501 o 8502 ya están ocupados. Cierra otros servidores y vuelve a ejecutar.")

    pc_environment = None
    mobile_environment = dict(__import__("os").environ)
    mobile_environment["CRACK_DEVICE_MODE"] = "mobile"
    pc = subprocess.Popen(streamlit_command(8501, "127.0.0.1", "pc"), env=pc_environment)
    mobile = subprocess.Popen(
        streamlit_command(8502, "0.0.0.0", "mobile"),
        env=mobile_environment,
    )
    try:
        print("Servidor PC y servidor celular activos. Mantén esta ventana abierta.")
        pc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for process in (pc, mobile):
            if process.poll() is None:
                process.terminate()
