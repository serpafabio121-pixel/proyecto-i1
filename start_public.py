"""Inicia Streamlit y crea una URL HTTPS pública para PC y celular.

Requiere el ejecutable ``cloudflared`` en PATH:
https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import threading


PUBLIC_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def forward_urls(process: subprocess.Popen) -> None:
    for raw_line in iter(process.stdout.readline, ""):
        line = raw_line.strip()
        if line:
            print(f"[tunnel] {line}", flush=True)
        match = PUBLIC_URL.search(line)
        if match:
            print("\nURL pública para PC y celular:", flush=True)
            print(match.group(0), flush=True)
            print("Mantén esta ventana abierta mientras uses la app.\n", flush=True)


if __name__ == "__main__":
    if shutil.which("cloudflared") is None:
        raise SystemExit(
            "No se encontró cloudflared. Instálalo desde "
            "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ "
            "y vuelve a ejecutar este archivo."
        )

    app = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app/main.py",
            "--server.address=127.0.0.1",
            "--server.port=8501",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    tunnel = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://127.0.0.1:8501"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    try:
        forward_urls(tunnel)
    except KeyboardInterrupt:
        pass
    finally:
        tunnel.terminate()
        app.terminate()
