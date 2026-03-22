# Informe para profesoras (ejecución real desde `src/main.py`)

## 1. Alcance
Se ejecutó el flujo principal del repositorio y se consolidaron automáticamente los artefactos de evidencia en `outputs/entrega_profesoras`.

## 2. Trazabilidad de archivos
| Archivo | Origen/Generación | Descripción |
|---|---|---|
| `proceso.log` | Redirección stdout/stderr de `src/main.py` | Log completo de ejecución. |
| `texto_comprimido.txt` | `src.compresion.comprimir.comprimir` | Texto comprimido antes de cifrado. |
| `texto_extraido.txt` | `src.main.extraer_y_verificar_mensaje` | Texto recuperado y desencriptado desde el audio esteganografiado. |
| `texto_descomprimido.txt` | `src.compresion.descomprimir.descomprimir` | Reconstrucción final del texto (si la descompresión fue exitosa). |
| `texto_comprimido_encriptado.json` | `src.main.convertir_mensaje_a_bits` + XOR | Payload cifrado serializado en hex con metadatos. |
| `audio_original.wav` | Copia de `data/audio_test.wav` | Audio base utilizado. |
| `audio_estegano.wav` | Copia de `data/audio_test_modificado.wav` | Audio con mensaje oculto. |
| `*.png` | `src.utils.graficas` | Gráficas y visualizaciones generadas en la corrida. |
| `resumen_ejecucion.json` | `src/main.py` | Resumen técnico estructurado de tiempos, métricas y parámetros. |

## 3. Parámetros de ejecución
- Método de inserción: **LSB aleatorio**
- Inicio del segmento usado: **12549726**
- Fin del segmento usado: **12593826**
- Fecha/hora ejecución: **2026-03-22T12:46:02**

## 4. Métrica BPS
- Bits insertados: **4984**
- Duración del audio: **285.0743 s**
- BPS calculado: **17.4832 bits/s**

Fórmula usada: `BPS = bits_insertados / duración_en_segundos`.

## 5. Nota metodológica sobre entropía
La función `src.utils.metricas.entropia` usa logaritmo natural (`base = e`), por lo que reporta en **nats**.
Para convertir a bits de información: `H_bits = H_nats / ln(2)`.

## 6. Estado de ataques
- Ataques ejecutados: **no**

## 7. Estado de recuperación de texto
- Texto extraído/desencriptado disponible: **sí**
- Texto descomprimido disponible: **sí**
