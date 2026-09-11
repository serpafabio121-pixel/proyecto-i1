# Detector de grietas

MVP web en Streamlit para tomar o cargar una foto o video de una pared y obtener una
clasificación visual **orientativa**: sin grieta evidente, leve, advertencia,
media o severa/grave. El análisis se ejecuta localmente, sin servicios externos
ni claves, usando una heurística explicable de oscuridad, contraste y bordes.
En videos se muestrean hasta ocho fotogramas representativos y se combinan sus
resultados.

## Requisitos

- Python 3.10 o superior
- pip

## Instalación y uso

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

Abre la URL local que muestra Streamlit. En móvil se puede usar **Tomar foto**
(con selector alternativo si el navegador bloquea la cámara) o **Grabar video**:
la cámara aparece en vivo dentro de la página; pulsa `START`, concede permiso a
la cámara y pulsa `STOP` al terminar. También se
puede seleccionar un video existente. Se aceptan JPG, PNG, WebP, MP4, MOV, AVI,
WebM y M4V. El video se previsualiza con controles y se procesa localmente; la
grabación se guarda como WebM temporal en la carpeta temporal del sistema (un
formato de video sin audio compatible con Windows) y no se envía a servicios
externos.

### Uso desde un celular

El celular no debe abrir `http://localhost:8501`, porque `localhost` apunta al
propio celular. Ejecuta Streamlit en el computador con:

```bash
streamlit run app/main.py --server.address 0.0.0.0
```

Conecta el celular a la misma red Wi-Fi y abre en su navegador
`http://IP_DEL_COMPUTADOR:8501`. Para **Grabar video**, los navegadores móviles
normalmente exigen HTTPS; en un despliegue público usa la URL HTTPS del
servicio. La opción **Tomar foto** funciona con el permiso de cámara del
navegador y tiene un selector de archivo alternativo.

Después del análisis puedes pulsar **Guardar una copia local de este archivo**.
La aplicación crea `data/uploads/`, usa un nombre único y ofrece un botón para
descargar la copia. La grabación temporal usada para analizar el video se limpia;
solo permanece la copia que el usuario decide guardar.

## Limitaciones y seguridad

Este MVP no segmenta una grieta con un modelo entrenado ni realiza un diagnóstico
estructural. En video solo se leen hasta ocho fotogramas, por lo que una grieta
que aparece entre muestras puede no detectarse. Sombras, suciedad, juntas,
textura, baja luz, movimiento y perspectiva pueden producir falsos positivos o
negativos. La confianza mostrada describe la
estabilidad del indicador heurístico, no una probabilidad de daño.

El tamaño máximo de foto o video es 50 MB. Los formatos dependen de los
decodificadores disponibles en el equipo donde se ejecuta Streamlit.
En despliegues efímeros, los archivos de `data/uploads/` pueden perderse al
reiniciar el servicio; descarga las copias que necesites conservar.

Las fotografías no reemplazan una inspección presencial de un ingeniero o
inspector calificado. Si hay desprendimientos, deformación, grietas que crecen
rápidamente, filtraciones importantes o riesgo para personas, aléjate de la
zona y solicita atención profesional urgente.

## Estructura

- `app/main.py`: configuración y punto de entrada de Streamlit.
- `app/home.py`: interfaz, validación de medios, muestreo de video y heurística local.
- `requirements.txt`: dependencias de la aplicación existente.
