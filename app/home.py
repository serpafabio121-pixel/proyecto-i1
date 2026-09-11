"""Interfaz del MVP de detección orientativa de grietas."""

from __future__ import annotations

import io
import os
import socket
import tempfile
import time
import uuid
from pathlib import Path
from dataclasses import dataclass

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageOps
from aiortc.contrib.media import MediaRecorder
from streamlit_webrtc import WebRtcMode, webrtc_streamer


@dataclass(frozen=True)
class Analysis:
    level: str
    confidence: int
    crack_score: float
    dark_ratio: float
    edge_ratio: float
    findings: list[str]
    recommendation: str
    urgent: bool
    seismic_risk: str = ""
    seismic_reason: str = ""


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1100px; padding-top: 2rem; }
        @media (max-width: 640px) {
            .block-container { padding: 1rem .75rem 2rem; }
            h1 { font-size: 1.7rem !important; }
            h2 { font-size: 1.25rem !important; }
            div[data-testid="stRadio"] > div { gap: .35rem; }
            div[data-testid="stRadio"] label { padding: .45rem .2rem; }
            video { max-height: 55vh; width: 100%; object-fit: contain; }
            button { min-height: 2.75rem; }
        }
        .hero { padding: 1.25rem 1.5rem; border-radius: 1rem;
                background: linear-gradient(135deg, #12324a, #1d6172);
                color: white; margin-bottom: 1.25rem; }
        .hero h1 { margin: 0 0 .35rem; }
        .hero p { margin: 0; color: #e2f4f6; }
        .notice { border-left: 4px solid #e5a000; padding: .8rem 1rem;
                  background: #fff8e5; border-radius: .35rem; }
        .result-card { padding: 1rem; border: 1px solid #dbe4e8;
                       border-radius: .75rem; background: #f8fbfc; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _network_url() -> str | None:
    """Obtiene una IPv4 de la red local para abrir la app desde un celular."""
    try:
        addresses = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
    except OSError:
        return None
    for address in addresses:
        host = address[4][0]
        if not host.startswith("127."):
            return f"http://{host}:8501"
    return None


def _open_image(uploaded_file) -> Image.Image:
    image = Image.open(io.BytesIO(uploaded_file.getvalue()))
    return ImageOps.exif_transpose(image).convert("RGB")


def _store_media(media_bytes: bytes, media_kind: str, original_name: str = "") -> Path:
    """Guarda una copia local con un nombre seguro y único."""
    uploads_dir = Path("data") / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(original_name).suffix.lower() if original_name else ""
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".avi", ".webm", ".m4v"}:
        suffix = ".webm" if media_kind == "video" else ".jpg"
    destination = uploads_dir / f"{media_kind}_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{suffix}"
    destination.write_bytes(media_bytes)
    return destination


def _read_frame(frame: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def _analyze(image: Image.Image) -> Analysis:
    """Calcula indicadores simples de contraste y bordes; no es un diagnóstico."""
    thumbnail = image.copy()
    thumbnail.thumbnail((640, 640))
    gray = np.asarray(thumbnail.convert("L"), dtype=np.float32) / 255.0

    # Una grieta suele ser una región oscura y alargada con cambios de intensidad.
    local_floor = np.minimum.reduce(
        [
            gray,
            np.roll(gray, 1, axis=0),
            np.roll(gray, -1, axis=0),
            np.roll(gray, 1, axis=1),
            np.roll(gray, -1, axis=1),
        ]
    )
    dark = gray < 0.30
    contrast = (gray - local_floor) > 0.10
    horizontal = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
    vertical = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
    edges = (horizontal + vertical) > 0.24
    dark_ratio = float(dark.mean())
    edge_ratio = float(edges.mean())
    crack_score = min(1.0, (dark_ratio * 1.7) + (edge_ratio * 1.25) + float(contrast.mean()) * 0.8)

    if crack_score < 0.12 or (dark_ratio < 0.008 and edge_ratio < 0.12):
        level, recommendation, urgent = "Sin grieta evidente", (
            "No se observan patrones oscuros lineales claros. Revisa la pared con buena "
            "luz y repite la foto si hay dudas."
        ), False
    elif crack_score < 0.28:
        level, recommendation, urgent = "Leve", (
            "Documenta la zona, limpia y sella la fisura con un producto compatible. "
            "Vuelve a revisar si aumenta."
        ), False
    elif crack_score < 0.48:
        level, recommendation, urgent = "Advertencia", (
            "Marca los extremos y mide su evolución. Solicita una revisión de mantenimiento "
            "si reaparece, se ramifica o atraviesa acabados."
        ), False
    elif crack_score < 0.70:
        level, recommendation, urgent = "Media", (
            "Evita cubrirla sin investigar la causa y pide una inspección de un profesional "
            "de obra o ingeniería."
        ), False
    else:
        level, recommendation, urgent = "Severa / grave", (
            "No realices reparaciones cosméticas. Aleja a las personas de la zona y solicita "
            "una inspección profesional prioritaria."
        ), True

    findings = [
        f"Pixeles oscuros: {dark_ratio * 100:.1f}% de la imagen.",
        f"Cambios de borde detectados: {edge_ratio * 100:.1f}%.",
        "La estimación combina oscuridad local, contraste y bordes; puede confundir juntas, sombras o suciedad.",
    ]
    confidence = int(round(55 + min(35, abs(crack_score - 0.35) * 55)))
    if level == "Sin grieta evidente":
        seismic_risk, seismic_reason = "Bajo", "No se observan señales visuales claras; mantén vigilancia preventiva."
    elif level in {"Leve", "Advertencia"}:
        seismic_risk, seismic_reason = "Moderado", "Una fisura visible requiere seguimiento, especialmente tras vibraciones o sismos."
    elif level == "Media":
        seismic_risk, seismic_reason = "Alto", "El patrón podría agravarse con movimiento; solicita revisión antes de intervenir."
    else:
        seismic_risk, seismic_reason = "Crítico", "Grietas marcadas o desprendimientos pueden indicar peligro; aléjate y pide inspección urgente."
    return Analysis(
        level=level,
        confidence=max(55, min(90, confidence)),
        crack_score=crack_score,
        dark_ratio=dark_ratio,
        edge_ratio=edge_ratio,
        findings=findings,
        recommendation=recommendation,
        urgent=urgent,
        seismic_risk=seismic_risk,
        seismic_reason=seismic_reason,
    )


def _combine_video_results(results: list[Analysis]) -> Analysis:
    """Combina fotogramas priorizando persistencia y el peor indicio observado."""
    scores = np.array([item.crack_score for item in results], dtype=np.float32)
    combined_score = float(min(1.0, (np.percentile(scores, 75) * 0.65) + (scores.max() * 0.35)))
    if combined_score < 0.12:
        level, recommendation, urgent = "Sin grieta evidente", (
            "No se observan patrones oscuros lineales persistentes. Repite el video con "
            "mejor iluminación si aún hay dudas."
        ), False
    elif combined_score < 0.28:
        level, recommendation, urgent = "Leve", (
            "Documenta la zona, limpia y sella la fisura con un producto compatible. "
            "Vuelve a revisar si aumenta."
        ), False
    elif combined_score < 0.48:
        level, recommendation, urgent = "Advertencia", (
            "Marca los extremos y mide su evolución. Solicita una revisión de mantenimiento "
            "si reaparece, se ramifica o atraviesa acabados."
        ), False
    elif combined_score < 0.70:
        level, recommendation, urgent = "Media", (
            "Evita cubrirla sin investigar la causa y pide una inspección de un profesional "
            "de obra o ingeniería."
        ), False
    else:
        level, recommendation, urgent = "Severa / grave", (
            "No realices reparaciones cosméticas. Aleja a las personas de la zona y solicita "
            "una inspección profesional prioritaria."
        ), True

    strongest = results[int(scores.argmax())]
    findings = [
        f"Se analizaron {len(results)} fotogramas representativos.",
        f"Índice combinado de los fotogramas: {combined_score:.2f} / 1.00.",
        "La combinación prioriza señales que persisten en el recorrido y el fotograma más marcado.",
        "Puede confundir juntas, sombras, movimiento, suciedad o textura de la pared.",
    ]
    return Analysis(
        level=level,
        confidence=max(55, min(90, int(round(np.mean([item.confidence for item in results]))))),
        crack_score=combined_score,
        dark_ratio=strongest.dark_ratio,
        edge_ratio=strongest.edge_ratio,
        findings=findings,
        recommendation=recommendation,
        urgent=urgent,
        seismic_risk={
            "Sin grieta evidente": "Bajo",
            "Leve": "Moderado",
            "Advertencia": "Moderado",
            "Media": "Alto",
            "Severa / grave": "Crítico",
        }[level],
        seismic_reason="Evaluación combinada de fotogramas; no predice el comportamiento estructural durante un sismo.",
    )


def _analyze_video(video_bytes: bytes, progress_callback=None) -> tuple[Analysis, int, float]:
    """Muestrea hasta ocho fotogramas sin enviar el video a ningún servicio."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temporary:
        temporary.write(video_bytes)
        video_path = temporary.name
    capture = cv2.VideoCapture(video_path)
    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
        if frame_count <= 0:
            raise ValueError("el archivo no contiene fotogramas legibles")
        sample_count = min(8, frame_count)
        sample_indexes = np.linspace(0, frame_count - 1, sample_count, dtype=int)
        results = []
        for position, index in enumerate(sample_indexes, start=1):
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
            success, frame = capture.read()
            if success:
                results.append(_analyze(_read_frame(frame)))
            if progress_callback:
                progress_callback(position / sample_count)
        if not results:
            raise ValueError("no se pudieron decodificar fotogramas")
        return _combine_video_results(results), len(results), (frame_count / fps if fps > 0 else 0)
    finally:
        capture.release()
        try:
            os.unlink(video_path)
        except FileNotFoundError:
            pass


def _remove_recording(path: str) -> bool:
    """Elimina una grabación cuando el navegador ya liberó el archivo."""
    for _ in range(8):
        try:
            os.unlink(path)
            return True
        except FileNotFoundError:
            return True
        except PermissionError:
            time.sleep(0.25)
    return False


def _record_video() -> bytes | None:
    """Muestra controles de cámara y guarda temporalmente la grabación en el servidor local."""
    if "recording_path" not in st.session_state:
        st.session_state.recording_path = os.path.join(
            tempfile.gettempdir(), f"crack_detector_{uuid.uuid4().hex}.webm"
        )
    recording_path = st.session_state.recording_path
    if st.session_state.get("recording_ready") and os.path.exists(recording_path):
        with open(recording_path, "rb") as recording:
            return recording.read()

    st.info(
        "Para grabar desde el celular debes abrir la dirección **https://** que "
        "muestra `python start_mobile.py`. Si la dirección empieza por `http://`, "
        "el navegador bloquea la cámara; como alternativa, carga un video ya grabado."
    )
    context = webrtc_streamer(
        key="crack-video-recorder",
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={"video": True, "audio": False},
        # WebM + VP8 is reliable for video-only recordings on Windows.
        in_recorder_factory=lambda: MediaRecorder(recording_path, format="webm"),
        video_html_attrs={"controls": True, "autoPlay": True, "muted": True},
    )
    if (
        not context.state.playing
        and os.path.exists(recording_path)
        and os.path.getsize(recording_path) > 0
    ):
        st.session_state.recording_ready = True
        with open(recording_path, "rb") as recording:
            return recording.read()
    st.caption("¿No puedes usar HTTPS? Cambia a **Cargar video** para seleccionar una grabación del teléfono.")
    return None


def _show_analysis(result: Analysis) -> None:
    st.subheader("Resultado orientativo")
    left, right = st.columns(2)
    with left:
        st.metric("Clasificación", result.level)
        st.progress(result.confidence / 100, text=f"Confianza heurística: {result.confidence}%")
    with right:
        st.metric("Índice visual", f"{result.crack_score:.2f} / 1.00")
        st.caption("No equivale a una probabilidad clínica o estructural.")
    if result.seismic_risk:
        st.markdown("### Riesgo orientativo ante sismo")
        st.metric("Nivel de precaución", result.seismic_risk)
        st.caption(result.seismic_reason)
        st.info(
            "Este nivel no predice terremotos ni sustituye una evaluación estructural. "
            "Después de un sismo, evacúa si hay daños nuevos, ruidos, deformación o desprendimientos."
        )

    if result.urgent:
        st.error(
            "Señales críticas: prioriza la seguridad, evita acercarte si hay desprendimientos "
            "y contacta a un inspector o ingeniero."
        )
    elif result.level == "Sin grieta evidente":
        st.success("No se detectó una grieta evidente en esta imagen.")
    else:
        st.warning("El patrón merece seguimiento; la foto no permite confirmar su causa.")

    col_findings, col_recommendation = st.columns(2)
    with col_findings:
        st.markdown("**Hallazgos**")
        for finding in result.findings:
            st.write(f"- {finding}")
    with col_recommendation:
        st.markdown("**Recomendación**")
        st.write(result.recommendation)


def show() -> None:
    _inject_styles()
    st.markdown(
        '<section class="hero"><h1>Detector de grietas 🧱</h1>'
        "<p>Evaluación visual preliminar de paredes desde tu móvil o computadora.</p></section>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="notice"><strong>Importante:</strong> este MVP usa una heurística local '
        "de contraste y bordes. No reemplaza a un ingeniero, inspector ni diagnóstico estructural."
        "</div>",
        unsafe_allow_html=True,
    )
    with st.expander("Permisos para usar cámara en el celular"):
        st.write(
            "Concede permiso de **Cámara** al navegador. Para grabar video desde "
            "el celular, usa una URL **HTTPS** y permite el acceso cuando el navegador "
            "lo solicite."
        )
    st.write("")

    st.subheader("1. Toma o carga una foto o video")
    source = st.radio(
        "Origen de la imagen",
        ("Cargar archivo", "Tomar foto", "Cargar video", "Grabar video"),
        horizontal=True,
        label_visibility="collapsed",
    )
    if source == "Tomar foto":
        uploaded = st.camera_input("Toma una foto de la pared")
        if uploaded is None:
            st.caption("Si la cámara no aparece, revisa los permisos del navegador o usa este selector.")
            uploaded = st.file_uploader(
                "Elegir una foto del dispositivo",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=False,
                key="photo-fallback",
            )
        media_kind = "image"
    elif source == "Cargar video":
        uploaded = st.file_uploader(
            "Selecciona o graba un video de la pared",
            type=["mp4", "mov", "avi", "webm", "m4v"],
            accept_multiple_files=False,
            help="En móvil, el selector de video del navegador puede ofrecer grabar con la cámara.",
        )
        media_kind = "video"
    elif source == "Grabar video":
        uploaded = _record_video()
        media_kind = "video"
        if uploaded is not None and st.button("Borrar grabación y volver a grabar", type="secondary"):
            recording_path = st.session_state.get("recording_path", "")
            removed = _remove_recording(recording_path) if recording_path else True
            st.session_state.pop("recording_ready", None)
            if not removed:
                st.warning("La grabación sigue siendo usada por el navegador. Pulsa STOP, espera un segundo y vuelve a intentarlo.")
                return
            st.session_state.pop("recording_path", None)
            st.rerun()
    else:
        uploaded = st.file_uploader(
            "Selecciona una imagen de la pared",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
            help="Usa una imagen nítida, de frente y con buena iluminación.",
        )
        media_kind = "image"

    if uploaded is None:
        st.info("Aún no hay un archivo. Para mejores resultados evita reflejos y sombras fuertes.")
        st.subheader("Qué revisar")
        st.write("Busca cambios de ancho, grietas diagonales, ramificaciones, humedad o desprendimientos.")
        return

    st.subheader("2. Vista previa y análisis")
    max_size = 50 * 1024 * 1024
    uploaded_size = uploaded.size if hasattr(uploaded, "size") else len(uploaded)
    if uploaded_size > max_size:
        st.error("El archivo supera el límite local de 50 MB. Usa un video más corto o comprimido.")
        return

    if media_kind == "video":
        st.video(uploaded)
        st.caption("El video se procesa localmente: solo se leen fotogramas representativos y no se envía a terceros.")
        progress = st.progress(0, text="Esperando análisis…")
        try:
            with st.spinner("Muestreando fotogramas y analizando bordes localmente…"):
                video_bytes = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded
                result, sampled_frames, duration = _analyze_video(
                    video_bytes,
                    progress_callback=lambda value: progress.progress(value, text=f"Procesando fotograma {int(value * 100)}%"),
                )
            progress.progress(1.0, text=f"Listo: {sampled_frames} fotogramas analizados")
            st.caption(f"Duración aproximada: {duration:.1f} s · máximo 8 fotogramas representativos")
        except (OSError, ValueError, cv2.error) as exc:
            progress.empty()
            st.error(f"No se pudo procesar el video. Comprueba que el formato sea compatible: {exc}")
            return
    else:
        try:
            image = _open_image(uploaded)
        except (OSError, ValueError) as exc:
            st.error(f"No se pudo leer la imagen. Comprueba el formato del archivo: {exc}")
            return
        st.image(image, caption=f"Imagen cargada: {image.width} × {image.height}px", use_container_width=True)
        st.info("La foto está lista. Pulsa el botón para iniciar el análisis.")
        if not st.button("Analizar foto", type="primary", use_container_width=True):
            st.caption("El análisis se ejecuta localmente y no sube la imagen a ningún servicio.")
            return
        with st.spinner("Analizando contraste, bordes y zonas oscuras…"):
            result = _analyze(image)
        st.success("Análisis terminado.")
    _show_analysis(result)
    if st.button("Guardar una copia local de este archivo", type="secondary"):
        media_bytes = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded
        original_name = getattr(uploaded, "name", "")
        try:
            saved_path = _store_media(media_bytes, media_kind, original_name)
            st.success(f"Archivo guardado en `{saved_path}`")
            st.download_button(
                "Descargar archivo guardado",
                data=media_bytes,
                file_name=saved_path.name,
                mime="video/webm" if media_kind == "video" else "image/jpeg",
            )
        except OSError as exc:
            st.error(f"No se pudo guardar el archivo: {exc}")
    st.caption(
        "Este análisis de foto o video es preliminar. Repite la toma desde otro ángulo y compara "
        "resultados. Si la grieta crece, hay desnivel, ruidos, filtraciones o partes sueltas, "
        "busca atención profesional urgente."
    )
