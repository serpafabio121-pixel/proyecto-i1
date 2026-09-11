"""Inicia la misma app con HTTPS para que los navegadores móviles permitan cámara."""

from __future__ import annotations

import datetime
import ipaddress
import socket
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CERT_DIR = ROOT / ".streamlit"
CERT_FILE = CERT_DIR / "mobile-cert.pem"
KEY_FILE = CERT_DIR / "mobile-key.pem"


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def ensure_certificate(address: str) -> None:
    if CERT_FILE.exists() and KEY_FILE.exists():
        return
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except ImportError as exc:
        raise SystemExit(
            "Falta cryptography. Ejecuta: pip install -r requirements.txt"
        ) from exc

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, address)])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                    x509.IPAddress(ipaddress.ip_address(address)),
                ]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    CERT_DIR.mkdir(exist_ok=True)
    KEY_FILE.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    CERT_FILE.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))


if __name__ == "__main__":
    address = local_ip()
    ensure_certificate(address)
    print("Detector de grietas - modo movil HTTPS")
    print(f"PC:      https://localhost:8501")
    print(f"Celular: https://{address}:8501")
    print("En el celular acepta el aviso del certificado y permite la camara.")
    print("Ambos equipos deben estar en la misma Wi-Fi.")
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
