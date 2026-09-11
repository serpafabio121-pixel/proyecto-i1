"""Inicia servidores HTTPS independientes para PC y celular."""

from __future__ import annotations

import socket
import subprocess
import sys
import shutil

from start_mobile import CERT_FILE, KEY_FILE, ensure_certificate, local_ip


def port_in_use(port: int) -> bool:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(0.5)
    try:
        return probe.connect_ex(("127.0.0.1", port)) == 0
    finally:
        probe.close()


def streamlit_command(port: int, address: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app/main.py",
        f"--server.address={address}",
        f"--server.port={port}",
        f"--server.sslCertFile={CERT_FILE}",
        f"--server.sslKeyFile={KEY_FILE}",
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
    if shutil.which("cloudflared"):
        print("Se encontró cloudflared: se abrirá una URL HTTPS pública confiable para PC y celular.")
        raise SystemExit(subprocess.call([sys.executable, "start_public.py"]))
    ip = local_ip()
    ensure_certificate(ip)
    print("Detector de grietas")
    print("PC:      https://localhost:8501")
    print(f"Celular: https://{ip}:8502")
    print("Acepta el aviso del certificado en cada dispositivo para habilitar la cámara.")
    print()
    if port_in_use(8501) or port_in_use(8502):
        raise SystemExit("Los puertos 8501 o 8502 ya están ocupados. Cierra otros servidores y vuelve a ejecutar.")

    pc = subprocess.Popen(streamlit_command(8501, "127.0.0.1"))
    mobile = subprocess.Popen(streamlit_command(8502, "0.0.0.0"))
    try:
        print("Servidor PC y servidor celular activos. Mantén esta ventana abierta.")
        pc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for process in (pc, mobile):
            if process.poll() is None:
                process.terminate()
