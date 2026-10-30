"""Comprime el texto a ocultar con la red neuronal sin pérdida y guarda el payload binario.

El payload es: 2 bytes con la longitud (big-endian) + salida del codificador aritmético.
Mide además los tiempos de carga, compresión y descompresión (proceso independiente no requerido aquí).
"""
import json, os, sys, time
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.compresion import llm_aritmetico as la

SALIDA = Path(os.environ.get("SALIDA_DIR", RAIZ / "outputs" / "revision_neuronal"))
SALIDA.mkdir(parents=True, exist_ok=True)
texto = (RAIZ / "data" / "data_to_hide.txt").read_text(encoding="utf-8").strip()

t0 = time.time(); tok, _ = la.cargar_modelo(); t_carga = time.time() - t0
registro = []
t0 = time.time(); comp = la.comprimir(texto, registro=registro); t_c = time.time() - t0
t0 = time.time(); rec = la.descomprimir(comp); t_d = time.time() - t0
assert rec == texto, "la descompresión no reproduce el texto"
payload = len(comp).to_bytes(2, "big") + comp
(RAIZ / "data" / "data_to_hide_comprimido_neuronal.bin").write_bytes(payload)
res = {
    "modelo": la.MODELO, "dtype": os.environ.get("DTYPE_LM", "bfloat16"), "hilos": la.HILOS,
    "caracteres": len(texto), "bytes_original": len(texto.encode()), "tokens": len(registro) - 1,
    "bytes_comprimido": len(comp), "bytes_payload": len(payload), "bits_payload": 8 * len(payload),
    "bits_por_caracter": 8 * len(comp) / len(texto),
    "tokens_primer_puesto": sum(1 for _, _, k in registro if k == 1),
    "t_carga_s": t_carga, "t_compresion_s": t_c, "t_descompresion_s": t_d, "recuperacion_exacta": True,
}
(SALIDA / "compresion_neuronal.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps(res, indent=1, ensure_ascii=False))
