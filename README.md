# Proyecto de grado  Criptosistema esteganográfico de audio, basado en atractores caóticos y compresión de textos por medio de redes neuronales.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Juferoga/se-tesis)

## Artículo para la Revista TecnoLógicas (manuscrito 4098)

La versión del modelo descrita en el artículo comprime el texto **sin pérdida** con una red neuronal (modelo de lenguaje
Qwen2.5-1.5B) y codificación aritmética (`src/compresion/llm_aritmetico.py`), cifra el mensaje con XOR y un flujo de clave
de dos órbitas del mapa logístico, cuyos parámetros se derivan de la clave K = (x0, r, N) con SHA-512 (`src/utils/caos.py`),
y lo oculta con LSB en posiciones elegidas por otra órbita del mapa logístico.

| Qué | Cómo reproducirlo |
|---|---|
| Resultados de la sección 3 (métricas, ataques, figuras) | `./scripts/seccion3_neuronal.sh` → `outputs/revision_neuronal/` |
| Espacio de clave y resolución efectiva (tablas 7 y 8) | `SALIDA_DIR=outputs/revision_neuronal python -m scripts.espacio_clave` y `... scripts.resolucion_clave` |
| Demostración: emisor y receptor en procesos separados | `./demo_recuperacion.sh` (con pausas) o `./demo_recuperacion.sh --seguido` |
| Casos de estudio adicionales (rama `articulo-v5`) | `scripts/casos_estudio_colab.py` en Google Colab con GPU |
| Robustez con Reed-Solomon (rama `articulo-v6`) | `SALIDA_DIR=outputs/revision_neuronal python -m scripts.reed_solomon` |

Requisito: emisor y receptor deben ejecutar la red con la misma configuración (pesos, float32 y tipo de dispositivo).

### Pendiente: archivar el código con un DOI (Zenodo)

- [ ] Crear una versión (tag), por ejemplo `v1.0-tecnologicas`, con el código exacto del artículo.
- [ ] Archivar la versión en Zenodo para obtener un DOI permanente:
  1. Entrar a https://zenodo.org con la cuenta de GitHub.
  2. En la sección *GitHub* de Zenodo, activar el repositorio `Juferoga/se-tesis`.
  3. Publicar la versión (release) en GitHub; Zenodo la archiva y asigna el DOI automáticamente.
  4. Agregar el distintivo del DOI a este README y un archivo `CITATION.cff`.
- [ ] En el apartado 2.8 del artículo, citar el DOI de Zenodo además del enlace a GitHub.

## Descripción

Este proyecto permite la manipulación y procesamiento de señales de audio, incluyendo compresión, encriptación y esteganografía. Además, proporciona herramientas para la visualización y análisis de señales de audio.

## Instalación

Instrucciones para instalar y configurar el proyecto.

```bash
# Clonar el repositorio
git clone https://github.com/jufeoga/tesis.git

# Entrar al directorio del proyecto
cd scripts

# Instalar dependencias
sh install.sh
```

## Uso

Iniciar el proyecto, después de instaladas las dependencias correr el comando

```bash
python -m src.main
```

## Funcionalidades

- **Compresión de texto**: Comprime y descomprime texto utilizando algoritmos específicos de IA.
- **Encriptado de texto**: Encripta mensajes utilizando una función de encriptación XOR.
- **Esteganografía en señales de audio**: Inserta y extrae mensajes ocultos en señales de audio.
- **Graficación de señales de audio**: Visualiza formas de onda, histogramas y espectrogramas de audio.
- **Generación de llaves de encriptación**: Genera llaves de encriptación basadas en caos.

## Pasos siguientes

Convertir el app en una función lambda para aws permitiendo peticiones http desde un front para el use desde cualquier parte.

- **Infraestructura**: S3, para ell almacenamiento estático de archivos que se vayan a manipular a lo largo del proceso. Lambda, para almacenar la función realizada en fast api.
- **Terraform**: Con el uso de terraform crear la infraestructura como código para el despliegue del aplicativo en la nube.
- **API**: Con FastAPI generar los endpoints para realizar el proceso de esteganográfico.
- **Github Actions**: Para el manejo de pruebas y estadísticas automáticas del aplicativo, despliegue y puesta en producción del app.

## Contribución

Guía para contribuir al proyecto.

1. Haz un fork del proyecto.
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -am 'Añadir nueva funcionalidad'`).
4. Sube tus cambios (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

## Licencia

GPL V3.
