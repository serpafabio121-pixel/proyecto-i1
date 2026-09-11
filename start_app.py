"""Inicia el detector por HTTPS para que PC y celular puedan usar la cámara."""

from __future__ import annotations

import subprocess
import sys

from start_mobile import CERT_FILE, KEY_FILE, ensure_certificate, local_ip


if __name__ == "__main__":
    ip = local_ip()
    ensure_certificate(ip)
    print("Detector de grietas")
    print("PC:      https://localhost:8501")
    print(f"Celular: https://{ip}:8501")
    print("Acepta el aviso del certificado en cada dispositivo para habilitar la cámara.")
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
                f"--server.sslCertFile={CERT_FILE}",
                f"--server.sslKeyFile={KEY_FILE}",
            ]
        )
    )
