"""Prueba de ida y vuelta del compresor sin pérdida (Llama-2-7b + codificación aritmética)."""
import json, os, sys, time, zlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.compresion import llm_aritmetico as la

texto = Path(os.environ.get("TEXTO", "data/data_to_hide.txt")).read_text(encoding="utf-8")
texto = texto[: int(os.environ["RECORTE"])] if "RECORTE" in os.environ else texto
t0 = time.time(); la.cargar_modelo(); t_carga = time.time() - t0
t0 = time.time(); c = la.comprimir(texto); t_c = time.time() - t0
t0 = time.time(); d = la.descomprimir(c); t_d = time.time() - t0
b = texto.encode("utf-8")
r = {"bytes_original": len(b), "bytes_llm_aritmetico": len(c), "bits_por_caracter": 8 * len(c) / len(texto),
     "bytes_zlib": len(zlib.compress(b, 9)), "recuperacion_exacta": d == texto,
     "t_carga_s": t_carga, "t_compresion_s": t_c, "t_descompresion_s": t_d, "hex": c.hex()}
print(json.dumps(r, indent=1, ensure_ascii=False))
if "SALIDA" in os.environ:
    Path(os.environ["SALIDA"]).write_text(json.dumps(r, indent=1, ensure_ascii=False))
