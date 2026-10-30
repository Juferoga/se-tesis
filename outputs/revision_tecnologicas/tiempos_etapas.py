"""Tiempos por etapa del proceso criptoesteganográfico con el texto comprimido (mediana de 5 corridas)."""
import json, statistics, time, wave
from pathlib import Path
import numpy as np
from src.utils.caos import derivar_semillas, generar_llave
from src.utils.chaos_mod_enum import ChaosMod as C
from src.encriptado.encriptar import xor_encriptado
from src.esteganografiado.esteganografiar import cargar_archivo_wav, guardar_archivo_wav, insertar_lsb_caotico
from src.esteganografiado.desesteganografiar import extraer_lsb_caotico

raiz = Path(__file__).resolve().parents[2]
texto = (raiz / "data" / "data_to_hide_comprimido.txt").read_text(encoding="utf-8").strip()
sem = derivar_semillas(C.X0.value, C.R.value, C.N_WARMUP.value)
tmp = Path(__file__).parent / "_tmp_estego.wav"
with wave.open(str(raiz / "data" / "audio_test.wav")) as w:
    params = w.getparams()
t = {k: [] for k in ["carga", "xor", "insercion", "guardado", "extraccion", "descifrado"]}
for _ in range(5):
    s = time.perf_counter(); a = cargar_archivo_wav(str(raiz / "data" / "audio_test.wav")); t["carga"].append(time.perf_counter() - s)
    s = time.perf_counter()
    m = np.array(list(texto.encode("utf-8")), dtype=np.uint8)
    k = generar_llave(C.X0.value, C.R.value, C.N_WARMUP.value, len(m)); c = xor_encriptado(m, k)
    bits = "".join(np.unpackbits(c).astype(str).tolist()); t["xor"].append(time.perf_counter() - s)
    s = time.perf_counter(); est, _ = insertar_lsb_caotico(a, bits, *sem[3:]); t["insercion"].append(time.perf_counter() - s)
    s = time.perf_counter(); guardar_archivo_wav(str(tmp), est, params); t["guardado"].append(time.perf_counter() - s)
    s = time.perf_counter(); b, _ = extraer_lsb_caotico(est, len(bits), *sem[3:]); t["extraccion"].append(time.perf_counter() - s)
    s = time.perf_counter()
    cb = np.packbits(np.array([int(x) for x in b], dtype=np.uint8))
    k2 = generar_llave(C.X0.value, C.R.value, C.N_WARMUP.value, len(cb))
    rec = bytes(xor_encriptado(cb, k2).tolist()).decode("utf-8"); t["descifrado"].append(time.perf_counter() - s)
    assert rec == texto
tmp.unlink()
res = {k: statistics.median(v) for k, v in t.items()}
(Path(__file__).parent / "tiempos_etapas.json").write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))
