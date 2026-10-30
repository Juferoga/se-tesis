#!/usr/bin/env bash
# Regenera todos los resultados de la sección 3 del artículo con la compresión neuronal sin pérdida.
set -euo pipefail
cd "$(dirname "$0")/.."
export SALIDA_DIR=outputs/revision_neuronal MODELO_LM=Qwen/Qwen2.5-1.5B DTYPE_LM=float32
export PYTHONWARNINGS=ignore TRANSFORMERS_VERBOSITY=error
mkdir -p "$SALIDA_DIR"
echo "== 1. Compresión neuronal";  .venv/bin/python -I scripts/comprimir_neuronal.py
echo "== 2. Estegoaudio";          PAYLOAD_BIN=data/data_to_hide_comprimido_neuronal.bin .venv/bin/python -m scripts.regenerar_con_texto_nuevo
echo "== 3. Tiempos por etapa";    .venv/bin/python -I scripts/tiempos_etapas.py
echo "== 4. Análisis completo";    .venv/bin/python -m scripts.generar_analisis_completo
echo "== 5. Figuras del artículo"; .venv/bin/python -m scripts.figuras_articulo
echo "== LISTO"
