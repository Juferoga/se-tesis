"""Receptor independiente: descomprime en un proceso nuevo a partir de los bytes guardados."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.compresion import llm_aritmetico as la

r = json.loads(Path(sys.argv[1]).read_text())
original = Path("data/data_to_hide.txt").read_text(encoding="utf-8")
t0 = time.time(); d = la.descomprimir(bytes.fromhex(r["hex"])); t = time.time() - t0
print(json.dumps({"recuperacion_exacta_proceso_independiente": d == original, "t_descompresion_s": t}))
