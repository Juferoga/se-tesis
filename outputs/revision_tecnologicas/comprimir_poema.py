import json, time
from pathlib import Path
from llmlingua import PromptCompressor
raiz = Path(__file__).resolve().parents[2]
texto = (raiz / "data" / "data_to_hide.txt").read_text(encoding="utf-8").strip()
target = int(len(texto.split(" ")) * 0.8)  # misma regla que src/compresion/comprimir.py
t0 = time.time(); lc = PromptCompressor(device_map="cpu"); t1 = time.time()
r = lc.compress_prompt(texto, instruction="", question="", target_token=target)
t2 = time.time()
out = {"palabras": len(texto.split(" ")), "target_token": target,
       "bytes_original": len(texto.encode()), "bytes_comprimido": len(r["compressed_prompt"].encode()),
       "t_carga_s": t1 - t0, "t_compresion_s": t2 - t1,
       **{k: v for k, v in r.items() if k != "compressed_prompt"}, "comprimido": r["compressed_prompt"]}
(Path(__file__).parent / "compresion_poema.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
