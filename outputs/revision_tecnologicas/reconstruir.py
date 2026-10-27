import json, time, difflib
from pathlib import Path
from src.compresion.descomprimir import descomprimir
raiz = Path(__file__).resolve().parents[2]
comp = (raiz / "data" / "data_to_hide_comprimido.txt").read_text(encoding="utf-8")
orig = (raiz / "data" / "data_to_hide.txt").read_text(encoding="utf-8").strip()
descomprimir("hola")  # calentamiento: carga del modelo en Ollama
t0 = time.time(); rec = descomprimir(comp); t = time.time() - t0
sim = difflib.SequenceMatcher(None, orig, rec).ratio()
out = {"modelo": "gemma3:4b", "t_reconstruccion_s": t, "similitud_vs_original_seqmatcher": sim,
       "bytes_reconstruido": len(rec.encode()), "reconstruido": rec}
(Path(__file__).parent / "reconstruccion_gemma.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
