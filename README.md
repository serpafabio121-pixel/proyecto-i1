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

La misma aplicación funciona en computador y celular: no hay una versión
separada. En el computador abre `http://localhost:8501`. Desde otro dispositivo
de la misma red abre `http://IP_DEL_COMPUTADOR:8501`. El servidor ya está
configurado para escuchar en toda la red (`0.0.0.0`).

En móvil se puede usar **Tomar foto**
(con selector alternativo si el navegador bloquea la cámara) o **Grabar video**:
la cámara aparece en vivo dentro de la página; pulsa `START`, concede permiso a
la cámara y pulsa `STOP` al terminar. También se
puede seleccionar un video existente. Se aceptan JPG, PNG, WebP, MP4, MOV, AVI,
WebM y M4V. El video se previsualiza con controles y se procesa localmente; la
grabación se guarda como WebM temporal en la carpeta temporal del sistema (un
formato de video sin audio compatible con Windows) y no se envía a servicios
externos.

### Acceso desde cualquier equipo

Si la configuración no se carga o quieres indicarla explícitamente, ejecuta:

```bash
streamlit run app/main.py --server.address 0.0.0.0
```

No abras `localhost` desde el celular: allí `localhost` significa el propio
celular. Para **Grabar video** y acceso directo a cámara, los navegadores
móviles exigen normalmente HTTPS. En una URL HTTPS pública funcionarán las
opciones de cámara en computador y celular; en una red local sin HTTPS siempre
se puede usar **Cargar archivo** como alternativa.

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
