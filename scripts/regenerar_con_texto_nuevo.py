#!/usr/bin/env python3
"""Regenera el estegoaudio usando el texto de data/data_to_hide.txt sin LLMLingua.

Flujo:
  1. Lee data/data_to_hide.txt (texto literario)
  2. Encripta con XOR caótico (mismos parámetros de ChaosMod)
  3. Inserta en audio_test.wav con LSB caótico
  4. Guarda audio_test_modificado.wav + intermedios en outputs/entrega_profesoras/

Uso:
    python -m scripts.regenerar_con_texto_nuevo
"""

from __future__ import annotations

import json
import wave
import shutil
from pathlib import Path
from datetime import datetime

import numpy as np

from src.encriptado.encriptar import xor_encriptado
from src.utils.caos import generar_llave
from src.utils.chaos_mod_enum import ChaosMod
from src.esteganografiado.esteganografiar import (
    cargar_archivo_wav,
    guardar_archivo_wav,
    insertar_lsb_caotico,
)
from src.esteganografiado.desesteganografiar import extraer_lsb_caotico

RAIZ = Path(__file__).resolve().parent.parent
DATA_DIR = RAIZ / "data"
SALIDA = RAIZ / "outputs" / "entrega_profesoras"
SALIDA.mkdir(parents=True, exist_ok=True)

X0 = ChaosMod.X0.value
R = ChaosMod.R.value
N_WARMUP = ChaosMod.N_WARMUP.value


def main() -> None:
    print("=" * 60)
    print("REGENERACIÓN CON TEXTO NUEVO (sin LLMLingua)")
    print("=" * 60)

    # 1. Leer texto literario
    ruta_texto = DATA_DIR / "data_to_hide.txt"
    texto_original = ruta_texto.read_text(encoding="utf-8").strip()
    print(f"\n[1] Texto leído: {len(texto_original)} caracteres")
    print(f"    Primeros 80 chars: {texto_original[:80]!r}")

    # El texto se usa directamente como "comprimido" (sin LLMLingua)
    # para mantener coherencia con el pipeline: texto_comprimido.txt = texto a ocultar
    texto_comprimido = texto_original

    # 2. Encriptar con XOR caótico
    texto_bytes = np.array(list(texto_comprimido.encode("utf-8")), dtype=np.uint8)
    llave = generar_llave(X0, R, N_WARMUP, len(texto_bytes))
    texto_encriptado = xor_encriptado(texto_bytes, llave)

    # Convertir a bits
    mensaje_bits = "".join(np.unpackbits(texto_encriptado).astype(str).tolist())

    print(f"\n[2] Encriptado: {len(texto_bytes)} bytes → {len(mensaje_bits)} bits")

    # 3. Cargar audio
    ruta_audio = DATA_DIR / "audio_test.wav"
    audio_original = cargar_archivo_wav(str(ruta_audio))
    with wave.open(str(ruta_audio), "rb") as wf:
        params = wf.getparams()
        sample_rate = wf.getframerate()

    print(f"\n[3] Audio cargado: {len(audio_original)} muestras, {sample_rate} Hz")
    print(f"    Capacidad: {len(audio_original)} bits disponibles")
    print(f"    Payload:   {len(mensaje_bits)} bits necesarios")

    if len(mensaje_bits) > len(audio_original):
        raise ValueError(
            f"Payload ({len(mensaje_bits)} bits) > capacidad ({len(audio_original)} bits)"
        )

    # 4. Insertar con LSB caótico
    audio_modificado, posiciones = insertar_lsb_caotico(
        audio_original, mensaje_bits, X0, R, N_WARMUP
    )
    print(f"\n[4] Inserción LSB caótica:")
    print(f"    Posiciones generadas: {len(posiciones)}")
    print(f"    min={posiciones.min()}, max={posiciones.max()}, std={posiciones.std():.0f}")

    # 5. Guardar audio modificado
    ruta_audio_mod = DATA_DIR / "audio_test_modificado.wav"
    guardar_archivo_wav(str(ruta_audio_mod), audio_modificado, params)
    print(f"\n[5] Audio guardado: {ruta_audio_mod}")

    # 6. Verificar extracción
    bits_extraidos, _ = extraer_lsb_caotico(audio_modificado, len(mensaje_bits), X0, R, N_WARMUP)
    extraccion_ok = mensaje_bits == bits_extraidos
    print(f"\n[6] Verificación extracción: {'✓ OK' if extraccion_ok else '✗ FALLO'}")

    if extraccion_ok:
        # Reconstruir texto
        n_bytes = len(bits_extraidos) // 8
        bits_arr = np.array([int(b) for b in bits_extraidos[:n_bytes * 8]], dtype=np.uint8)
        bytes_rec = np.packbits(bits_arr)
        texto_desencriptado = bytes(xor_encriptado(bytes_rec, llave).tolist()).decode("utf-8")
        print(f"    Texto recuperado (primeros 80): {texto_desencriptado[:80]!r}")
    else:
        texto_desencriptado = None

    # 7. Exportar intermedios a outputs/entrega_profesoras/
    (SALIDA / "texto_comprimido.txt").write_text(texto_comprimido, encoding="utf-8")
    (SALIDA / "texto_extraido.txt").write_text(texto_desencriptado or "", encoding="utf-8")
    (SALIDA / "texto_descomprimido.txt").write_text(texto_desencriptado or "", encoding="utf-8")

    payload_hex = "".join(f"{b:02x}" for b in texto_encriptado.tolist())
    (SALIDA / "texto_comprimido_encriptado.json").write_text(
        json.dumps({
            "formato": "payload_encriptado",
            "longitud_bits": len(mensaje_bits),
            "longitud_bytes": len(texto_bytes),
            "payload_hex": payload_hex,
            "llave_longitud_bytes": int(len(llave)),
            "nota": "Texto literario (José Asunción Silva) encriptado con XOR caótico.",
            "texto_original_chars": len(texto_original),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Copiar audios
    shutil.copy2(ruta_audio, SALIDA / "audio_original.wav")
    shutil.copy2(ruta_audio_mod, SALIDA / "audio_estegano.wav")

    # Guardar resumen básico
    n_cambios = int(np.sum(audio_modificado.astype(np.int32) - audio_original.astype(np.int32) != 0))
    mse_val = float(np.mean((audio_original.astype(np.float64) - audio_modificado.astype(np.float64)) ** 2))
    psnr_val = float(10 * np.log10(32767.0**2 / mse_val)) if mse_val > 0 else float("inf")

    resumen = {
        "fecha_hora": datetime.now().isoformat(timespec="seconds"),
        "texto_fuente": "José Asunción Silva — poema (dominio público, 1896)",
        "metodo": "LSB caótico (mapa logístico)",
        "bits_insertados": len(mensaje_bits),
        "bytes_payload": int(len(texto_bytes)),
        "muestras_audio": int(len(audio_original)),
        "sample_rate": int(sample_rate),
        "muestras_modificadas": n_cambios,
        "extraccion_verificada": extraccion_ok,
        "metricas": {
            "mse": mse_val,
            "psnr_db": psnr_val,
        },
        "parametros_caoticos": {
            "x0": X0,
            "r": R,
            "n_warmup": N_WARMUP,
        },
    }
    (SALIDA / "resumen_ejecucion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print("REGENERACIÓN COMPLETADA")
    print("=" * 60)
    print(f"  Texto:         {len(texto_original)} chars → {len(mensaje_bits)} bits")
    print(f"  MSE:           {mse_val:.6e}")
    print(f"  PSNR:          {psnr_val:.4f} dB")
    print(f"  Cambios LSB:   {n_cambios}")
    print(f"  Salida:        {SALIDA}")


if __name__ == "__main__":
    main()
