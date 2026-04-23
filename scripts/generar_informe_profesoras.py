#!/usr/bin/env python3
"""Genera un paquete aditivo de evidencia en outputs/entrega_profesoras.

Reglas del script:
- No modifica archivos del pipeline principal.
- Reutiliza funciones existentes de compresión, cifrado y esteganografía.
- Evita ataques o procesos pesados.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import wave

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.compresion.comprimir import comprimir
from src.main import convertir_mensaje_a_bits, insertar_mensaje_en_audio
from src.esteganografiado.esteganografiar import (
    cargar_archivo_wav,
    guardar_archivo_wav,
)


@dataclass
class ResultadoProceso:
    ruta_salida: Path
    bits_insertados: int
    duracion_segundos: float
    bps: float
    inicio_segmento: int
    fin_segmento: int


MENSAJE_BASE = """
Este informe de evidencia fue generado en modo aditivo para revisión académica.
Se reutiliza la lógica actual del repositorio: compresión, cifrado XOR,
inserción esteganográfica en audio WAV y generación de artefactos verificables.
El objetivo es entregar trazabilidad de entrada/salida sin modificar el pipeline principal.
""".strip()


def _asegurar_directorio(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _guardar_onda(audio: np.ndarray, titulo: str, ruta_png: Path) -> None:
    plt.figure(figsize=(14, 4))
    plt.plot(audio)
    plt.title(titulo)
    plt.xlabel("Muestra")
    plt.ylabel("Amplitud")
    plt.tight_layout()
    plt.savefig(ruta_png)
    plt.close()


def _bits_a_bytes(bits: str) -> list[int]:
    if not bits:
        return []
    return [int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)]


def generar_paquete() -> ResultadoProceso:
    raiz_repo = Path(__file__).resolve().parent.parent
    ruta_audio_original = raiz_repo / "data" / "audio_test.wav"
    salida = raiz_repo / "outputs" / "entrega_profesoras"

    _asegurar_directorio(salida)

    # 1) Cargar audio original
    audio_original = cargar_archivo_wav(str(ruta_audio_original))
    with wave.open(str(ruta_audio_original), "rb") as wav_file:
        params = wav_file.getparams()
        n_frames = wav_file.getnframes()
        sample_rate = wav_file.getframerate()

    # 2) Comprimir texto
    texto_comprimido = comprimir(MENSAJE_BASE)
    ruta_texto_comprimido = salida / "texto_comprimido.txt"
    ruta_texto_comprimido.write_text(texto_comprimido, encoding="utf-8")

    # 3) Encriptar payload (vía lógica existente en main.convertir_mensaje_a_bits)
    mensaje_bits, llave = convertir_mensaje_a_bits(texto_comprimido)
    payload_bytes = _bits_a_bytes(mensaje_bits)
    payload_hex = "".join(f"{b:02x}" for b in payload_bytes)

    ruta_payload = salida / "texto_comprimido_encriptado.json"
    ruta_payload.write_text(
        json.dumps(
            {
                "formato": "payload_encriptado",
                "longitud_bits": len(mensaje_bits),
                "longitud_bytes": len(payload_bytes),
                "payload_hex": payload_hex,
                "llave_longitud_bytes": int(len(llave)),
                "nota": "Payload generado desde mensaje comprimido usando flujo XOR existente.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # 4) Insertar payload en audio (esteganografía LSB secuencial)
    audio_estegano, inicio_segmento, fin_segmento = insertar_mensaje_en_audio(
        audio_original,
        mensaje_bits,
        audio_total=False,
        sequential=True,
    )

    # 5) Guardar audios solicitados
    ruta_audio_original_out = salida / "audio_original.wav"
    ruta_audio_estegano_out = salida / "audio_estegano.wav"
    shutil.copy2(ruta_audio_original, ruta_audio_original_out)
    guardar_archivo_wav(str(ruta_audio_estegano_out), audio_estegano, params)

    # 6) Generar ondas solicitadas
    _guardar_onda(
        audio_original, "Onda de audio original", salida / "onda_original.png"
    )
    _guardar_onda(
        audio_estegano,
        "Onda de audio esteganografiado",
        salida / "onda_estegoaudio.png",
    )

    # 7) Calcular BPS
    duracion_segundos = n_frames / sample_rate if sample_rate else 0.0
    bits_insertados = len(mensaje_bits)
    bps = (bits_insertados / duracion_segundos) if duracion_segundos > 0 else 0.0

    # 8) Informe principal
    informe = f"""# Informe para profesoras (ejecución real, modo aditivo)

## 1. Alcance
Se ejecutó el flujo actual del repositorio reutilizando funciones existentes, sin modificar archivos del pipeline principal.

## 2. Trazabilidad de archivos
| Archivo | Origen/Generación | Descripción |
|---|---|---|
| `texto_comprimido.txt` | `src.compresion.comprimir.comprimir` | Texto comprimido desde mensaje base. |
| `texto_comprimido_encriptado.json` | `src.main.convertir_mensaje_a_bits` + `src.encriptado.encriptar.xor_encriptado` | Payload cifrado serializado en hex y metadatos. |
| `audio_original.wav` | Copia de `data/audio_test.wav` | Audio base utilizado en el experimento. |
| `audio_estegano.wav` | `src.main.insertar_mensaje_en_audio` + `src.esteganografiado.esteganografiar.guardar_archivo_wav` | Audio con el payload insertado en LSB secuencial. |
| `onda_original.png` | script auxiliar | Visualización de la onda del audio original. |
| `onda_estegoaudio.png` | script auxiliar | Visualización de la onda del audio esteganografiado. |
| `clasificacion_pruebas.md` | script auxiliar | Clasificación simple de pruebas por tipo y función existente. |

## 3. Métrica BPS
- Bits insertados: **{bits_insertados}**
- Duración del audio: **{duracion_segundos:.4f} s**
- BPS calculado: **{bps:.4f} bits/s**

Fórmula usada: `BPS = bits_insertados / duración_en_segundos`.

## 4. Nota metodológica sobre entropía
La función `src.utils.metricas.entropia` calcula con logaritmo natural (`base = e`), por lo que el resultado queda en **nats**.
Si se requiere expresarlo en bits de información, se convierte con: `H_bits = H_nats / ln(2)`.
Esta nota es documental; **no se modificó código existente**.

## 5. Parámetros de ejecución
- Método de inserción: LSB secuencial
- Inicio del segmento usado: {inicio_segmento}
- Fin del segmento usado: {fin_segmento}
- Fecha/hora ejecución: {datetime.now().isoformat(timespec="seconds")}
"""
    (salida / "informe_profesoras.md").write_text(informe, encoding="utf-8")

    # 9) Clasificación simple de pruebas (sin ataques pesados)
    clasificacion = """# Clasificación simple de pruebas (basada en funciones existentes)

## Funcionales mínimas
- **Compresión de texto**: `src.compresion.comprimir.comprimir`
- **Encriptación XOR**: `src.encriptado.encriptar.xor_encriptado` (invocada vía `src.main.convertir_mensaje_a_bits`)
- **Inserción esteganográfica**: `src.esteganografiado.esteganografiar.insertar_mensaje_segmento_lsb_sequential` (invocada vía `src.main.insertar_mensaje_en_audio`)
- **Persistencia de audio**: `src.esteganografiado.esteganografiar.guardar_archivo_wav`

## Visualización/evidencia
- **Ondas de señal**: generadas en `onda_original.png` y `onda_estegoaudio.png`.

## Métricas reportables sin carga pesada
- **BPS** (capacidad efectiva de inserción por segundo) calculado en el script auxiliar.
- **Entropía (nota metodológica)**: la implementación actual reporta en nats por usar log base *e*.

## Fuera de alcance en esta corrida
- Ataques robustos y pruebas intensivas de estrés (omitidos por restricción de cómputo).
"""
    (salida / "clasificacion_pruebas.md").write_text(clasificacion, encoding="utf-8")

    return ResultadoProceso(
        ruta_salida=salida,
        bits_insertados=bits_insertados,
        duracion_segundos=duracion_segundos,
        bps=bps,
        inicio_segmento=inicio_segmento,
        fin_segmento=fin_segmento,
    )


def main() -> None:
    resultado = generar_paquete()
    print("Paquete generado correctamente.")
    print(f"Salida: {resultado.ruta_salida}")
    print(f"Bits insertados: {resultado.bits_insertados}")
    print(f"Duración (s): {resultado.duracion_segundos:.4f}")
    print(f"BPS: {resultado.bps:.4f}")
    print(f"Segmento: [{resultado.inicio_segmento}, {resultado.fin_segmento}]")


if __name__ == "__main__":
    main()
