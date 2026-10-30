# Modelo criptoesteganográfico sobre archivos de audio basado en redes neuronales y atractores caóticos

Código del modelo presentado en el artículo homónimo (Revista TecnoLógicas, en revisión), derivado del trabajo de grado
*Criptosistema esteganográfico de audio basado en atractores caóticos y compresión de textos por medio de redes neuronales*
(Universidad Distrital Francisco José de Caldas, Ingeniería de Sistemas).

**Autores:** Juan Felipe Rodríguez-Galindo, Mateo Bohórquez-Rodríguez, Luz Deicy Alvarado-Nieto e Isabel Amaya-Barrera.

## Modelo

El emisor oculta un mensaje de texto en un archivo de audio WAV en tres etapas, y el receptor, con la misma clave, lo recupera de forma exacta:

1. **Compresión sin pérdida con una red neuronal.** El modelo de lenguaje Qwen2.5-1.5B estima la probabilidad de cada token y un codificador aritmético convierte esas probabilidades en bits (`src/compresion/llm_aritmetico.py`).
2. **Cifrado caótico.** Los parámetros de tres órbitas del mapa logístico se derivan de la clave K = (x0, r, N) con SHA-512; el flujo de clave es el XOR de dos órbitas binarizadas y se combina con el mensaje mediante XOR (`src/utils/caos.py`, `src/encriptado/`).
3. **Esteganografía LSB.** Cada bit cifrado reemplaza el bit menos significativo de una muestra elegida por la tercera órbita (`src/esteganografiado/`).

Emisor y receptor deben ejecutar la red con la misma configuración (pesos, punto flotante de 32 bits y tipo de dispositivo).

## Estructura

| Ruta | Contenido |
|---|---|
| `src/` | Implementación del modelo (compresión, cifrado, esteganografía y mapa logístico) |
| `scripts/` | Experimentos del artículo |
| `data/` | Texto de prueba (dominio público), audio portador (CC BY-NC 4.0) y estegoaudio |
| `outputs/revision_neuronal/` | Resultados y figuras de la sección 3 del artículo |
| `demo_recuperacion.sh` | Demostración: emisor y receptor en procesos separados |

## Instalación

```bash
git clone https://github.com/Juferoga/se-tesis.git
cd se-tesis
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

La primera ejecución descarga los pesos de la red (`Qwen/Qwen2.5-1.5B`, unos 3 GB) desde Hugging Face.

## Reproducción

| Resultado del artículo | Comando |
|---|---|
| Sección 3: métricas, ataques y figuras | `./scripts/seccion3_neuronal.sh` |
| Espacio de clave y resolución efectiva (tablas 7 y 8) | `SALIDA_DIR=outputs/revision_neuronal python -m scripts.espacio_clave` y `python -m scripts.resolucion_clave` |
| Demostración de recuperación exacta | `./demo_recuperacion.sh` (o `--seguido`, sin pausas) |

## Versiones del artículo

| Rama | Contenido |
|---|---|
| `main` | Modelo del artículo |
| `articulo-v5` | Casos de estudio adicionales (Google Colab con GPU) |
| `articulo-v6` | Robustez con código Reed-Solomon y repetición de bits |
| `articulo-v7` | Estegoanálisis, pruebas NIST SP 800-22 y ataques de procesamiento de señal |
| `tesis-2025` | Versión completa del trabajo de grado (incluye la compresión con LLMLingua) |

## Datos

- **Texto:** *Nocturno (Oh dulce niña pálida)*, José Asunción Silva, dominio público.
- **Audio:** «Let it go», Rewob (ft. debbizo), https://ccmixter.org/files/rewob/70685, licencia Creative Commons Attribution-NonCommercial 4.0.

## Licencia

GNU General Public License v3.0 (ver `LICENSE`).
