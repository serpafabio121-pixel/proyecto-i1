# Detector de grietas

Aplicación Streamlit para analizar fotos y videos de paredes con una heurística
local. Entrega una clasificación orientativa, hallazgos, recomendación y nivel
de precaución ante sismo. No reemplaza a un ingeniero o inspector.

## Ejecutar en Visual Studio Code (Windows)

Abre la terminal en la carpeta del proyecto y ejecuta exactamente:

```powershell
python -m pip install -r requirements.txt
python start_app.py
```

Si usas un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python start_app.py
```

El lanzador inicia un único servidor para ambos dispositivos:

```text
Celular: http://IP_DEL_COMPUTADOR:8501
PC:      http://localhost:8501
```

Usa la primera dirección en el celular y la segunda en el PC. El PC conserva todas las funciones:
tomar foto, grabar video, cargar archivos y analizar. El celular se detecta
automáticamente por el navegador y queda limitado a **Cargar archivo** y
**Cargar video**, sin permisos de cámara ni grabación directa.
La detección móvil requiere Streamlit 1.37 o superior; el instalador la fija
automáticamente para que no aparezcan los controles de cámara en el teléfono
ni se oculten por una versión antigua.

Para que el celular abra `http://IP_DEL_COMPUTADOR:8501`, ambos dispositivos
deben estar en la misma red y Windows debe permitir Python en redes privadas.
GitHub no es la URL de la aplicación: solo almacena el código.

## Qué hace el análisis

- Muestrea hasta ocho fotogramas de un video.
- Combina oscuridad local, morfología, bordes y componentes alargados para
  encontrar patrones compatibles con grietas.
- Informa `Sin grieta evidente`, `Leve`, `Advertencia`, `Media` o
  `Severa / grave`.
- Añade riesgo orientativo ante sismo: `Bajo`, `Moderado`, `Alto` o `Crítico`.
- Permite guardar y descargar una copia del medio analizado.

El resultado es preliminar: sombras, juntas, humedad, suciedad y textura pueden
generar falsos positivos o negativos. Después de un sismo, evacúa si hay
deformación, desprendimientos, ruidos o daños nuevos y solicita una inspección.
