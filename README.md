# Proyecto de grado  Criptosistema esteganográfico de audio, basado en atractores caóticos y compresión de textos por medio de redes neuronales.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Juferoga/se-tesis)

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
