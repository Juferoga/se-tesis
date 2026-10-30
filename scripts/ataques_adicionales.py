"""Ataques adicionales de procesamiento de señal: compresión MP3, remuestreo, filtro pasa bajas y cambio de amplitud.

Se evalúan el modelo sin corrección (1400 bits) y con Reed-Solomon RS(255, 175) y repetición x5 (10 200 bits).
"""
import json, os, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np
from reedsolo import RSCodec, ReedSolomonError
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.caos import generar_llave, derivar_semillas, generar_posiciones_caoticas
from src.utils.chaos_mod_enum import ChaosMod as C
from src.encriptado.encriptar import xor_encriptado
from src.esteganografiado.esteganografiar import cargar_archivo_wav

SALIDA = Path(os.environ.get("SALIDA_DIR", "outputs/revision_neuronal"))
X0, R, N = C.X0.value, C.R.value, C.N_WARMUP.value
SP = derivar_semillas(X0, R, N)[3:]
payload = Path("data/data_to_hide_comprimido_neuronal.bin").read_bytes()
k = generar_llave(X0, R, N, len(payload))
cif = bytes(np.asarray(xor_encriptado(np.frombuffer(payload, dtype=np.uint8), k), dtype=np.uint8).tolist())
audio = cargar_archivo_wav("data/audio_test.wav").astype(np.int16)
with wave.open("data/audio_test.wav") as w:
    FS, CH = w.getframerate(), w.getnchannels()


def a_float(x):
    return x.reshape(-1, CH).astype(np.float64)


def a_int16(y):
    return np.clip(np.rint(y), -32768, 32767).astype(np.int16).reshape(-1)


def mp3(x, kbps):
    with tempfile.TemporaryDirectory() as d:
        wi, mo, wo = f"{d}/i.wav", f"{d}/o.mp3", f"{d}/o.wav"
        with wave.open(wi, "wb") as w:
            w.setnchannels(CH); w.setsampwidth(2); w.setframerate(FS); w.writeframes(x.tobytes())
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wi, "-codec:a", "libmp3lame", "-b:a", f"{kbps}k", mo], check=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mo, "-ar", str(FS), "-ac", str(CH), wo], check=True)
        with wave.open(wo) as w:
            y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    out = np.zeros_like(x); out[: min(len(x), len(y))] = y[: len(x)]
    return out


def remuestreo(x, fs2):
    y = a_float(x); z = resample_poly(resample_poly(y, fs2, FS, axis=0), FS, fs2, axis=0)[: len(y)]
    return a_int16(z)


def pasa_bajas(x, fc):
    sos = butter(8, fc, fs=FS, output="sos")
    return a_int16(sosfiltfilt(sos, a_float(x), axis=0))


def amplitud(x, g):
    return a_int16(a_float(x) * g)


ATAQUES = [("Compresión MP3", "320 kbps", lambda x: mp3(x, 320)), ("Compresión MP3", "128 kbps", lambda x: mp3(x, 128)),
           ("Remuestreo", "44.1 → 22.05 → 44.1 kHz", lambda x: remuestreo(x, 22050)),
           ("Filtro pasa bajas", "fc = 16 kHz", lambda x: pasa_bajas(x, 16000)),
           ("Cambio de amplitud", "× 0.99", lambda x: amplitud(x, 0.99)), ("Cambio de amplitud", "× 1.01", lambda x: amplitud(x, 1.01))]


def evaluar(nsym, rep):
    rs = RSCodec(nsym) if nsym else None
    cod = bytes(rs.encode(cif)) if nsym else cif
    ref = np.unpackbits(np.frombuffer(cod, dtype=np.uint8))
    bits = np.repeat(ref, rep)
    P = generar_posiciones_caoticas(*SP, len(bits), len(audio))
    est = audio.copy(); u = est.view(np.uint16); u[P] = (u[P] & 0xFFFE) | bits
    out = []
    for nombre, nivel, f in ATAQUES:
        at = f(est.copy())
        ext = (at.view(np.uint16)[P] & 1).astype(np.uint8)
        dec = (ext.reshape(-1, rep).sum(1) * 2 > rep).astype(np.uint8)
        rec = bytes(np.packbits(dec).tolist())
        try:
            msg = bytes(rs.decode(rec)[0]) if nsym else rec
        except ReedSolomonError:
            msg = None
        exacto = msg is not None and bytes(np.asarray(xor_encriptado(np.frombuffer(msg, dtype=np.uint8), k), dtype=np.uint8).tolist()) == payload
        d = at.astype(np.float64) - est.astype(np.float64)
        fila = {"ataque": nombre, "nivel": nivel, "ber_pct": 100 * float(np.mean(ext != bits)),
                "ber_tras_mayoria_pct": 100 * float(np.mean(dec != ref)), "muestras_alteradas_pct": 100 * float(np.mean(d != 0)),
                "recuperacion_exacta": bool(exacto)}
        out.append(fila); print(nsym, rep, json.dumps(fila, ensure_ascii=False), flush=True)
    return {"nsym": nsym, "repeticion": rep, "L_bits": int(len(bits)), "ataques": out}


res = {"configuraciones": [evaluar(0, 1), evaluar(80, 5)]}
(SALIDA / "ataques_adicionales.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
