"""Tiempos por etapa del cifrado y la esteganografía (mediana de 5 corridas) con el payload neuronal."""
import json, os, statistics, sys, time, wave
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import numpy as np
from src.utils.caos import derivar_semillas, generar_llave
from src.utils.chaos_mod_enum import ChaosMod as C
from src.encriptado.encriptar import xor_encriptado
from src.esteganografiado.esteganografiar import cargar_archivo_wav, guardar_archivo_wav, insertar_lsb_caotico
from src.esteganografiado.desesteganografiar import extraer_lsb_caotico

SALIDA = Path(os.environ.get("SALIDA_DIR", RAIZ / "outputs" / "revision_neuronal"))
payload = (RAIZ / "data" / "data_to_hide_comprimido_neuronal.bin").read_bytes()
sem = derivar_semillas(C.X0.value, C.R.value, C.N_WARMUP.value)
tmp = SALIDA / "_tmp_estego.wav"
with wave.open(str(RAIZ / "data" / "audio_test.wav")) as w:
    params = w.getparams()
t = {k: [] for k in ["carga", "xor", "insercion", "guardado", "extraccion", "descifrado"]}
for _ in range(5):
    s = time.perf_counter(); a = cargar_archivo_wav(str(RAIZ / "data" / "audio_test.wav")); t["carga"].append(time.perf_counter() - s)
    s = time.perf_counter()
    m = np.frombuffer(payload, dtype=np.uint8)
    k = generar_llave(C.X0.value, C.R.value, C.N_WARMUP.value, len(m)); c = xor_encriptado(m, k)
    bits = "".join(np.unpackbits(np.asarray(c, dtype=np.uint8)).astype(str).tolist()); t["xor"].append(time.perf_counter() - s)
    s = time.perf_counter(); est, _ = insertar_lsb_caotico(a, bits, *sem[3:]); t["insercion"].append(time.perf_counter() - s)
    s = time.perf_counter(); guardar_archivo_wav(str(tmp), est, params); t["guardado"].append(time.perf_counter() - s)
    s = time.perf_counter(); b, _ = extraer_lsb_caotico(est, len(bits), *sem[3:]); t["extraccion"].append(time.perf_counter() - s)
    s = time.perf_counter()
    cb = np.packbits(np.array([int(x) for x in b], dtype=np.uint8))
    k2 = generar_llave(C.X0.value, C.R.value, C.N_WARMUP.value, len(cb))
    rec = bytes(np.asarray(xor_encriptado(cb, k2), dtype=np.uint8).tolist()); t["descifrado"].append(time.perf_counter() - s)
    assert rec == payload
tmp.unlink()
res = {k: statistics.median(v) for k, v in t.items()}
(SALIDA / "tiempos_etapas.json").write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))
