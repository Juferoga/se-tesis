"""Estegoanálisis del estegoaudio: prueba chi-cuadrado (Westfeld y Pfitzmann) y análisis RS (Fridrich, Goljan y Du).

Se evalúan el audio original, el estegoaudio de la versión sin corrección (1400 bits), el de la versión con Reed-Solomon
y repetición (10 200 bits) y cargas sintéticas crecientes (bits aleatorios en posiciones elegidas al azar), para
estimar a partir de qué proporción de muestras modificadas los detectores identifican la inserción.
"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.stats import chi2
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.caos import derivar_semillas, generar_posiciones_caoticas
from src.utils.chaos_mod_enum import ChaosMod as C
from src.esteganografiado.esteganografiar import cargar_archivo_wav

SALIDA = Path(os.environ.get("SALIDA_DIR", "outputs/revision_neuronal"))
audio = cargar_archivo_wav("data/audio_test.wav").astype(np.int16)
M = len(audio)
SP = derivar_semillas(C.X0.value, C.R.value, C.N_WARMUP.value)[3:]
rng = np.random.default_rng(2026)


def insertar(a, pos, bits):
    e = a.copy(); u = e.view(np.uint16); u[pos] = (u[pos] & 0xFFFE) | bits
    return e


def chi_cuadrado(x):
    h = np.bincount(x.astype(np.int64) + 32768, minlength=65536).astype(float)
    par, impar = h[0::2], h[1::2]
    esp = (par + impar) / 2
    m = esp > 4
    est = float(np.sum((par[m] - esp[m]) ** 2 / esp[m]))
    gl = int(m.sum() - 1)
    return est, gl, float(chi2.sf(est, gl))  # p: probabilidad de que haya inserción


def rs(x, mascara=np.array([0, 1, 1, 0])):
    G = x.astype(np.int64)[: len(x) // 4 * 4].reshape(-1, 4)
    f = lambda H: np.abs(np.diff(H, axis=1)).sum(1)
    F1 = lambda v: v ^ 1
    Fm1 = lambda v: ((v + 1) ^ 1) - 1
    def grupos(H):
        f0 = f(H); out = []
        for Ff in (F1, Fm1):
            K = H.copy(); K[:, mascara == 1] = Ff(H[:, mascara == 1]); fk = f(K)
            out += [float(np.mean(fk > f0)), float(np.mean(fk < f0))]
        return out  # Rm, Sm, R-m, S-m
    Rm, Sm, Rn, Sn = grupos(G)
    Rm1, Sm1, Rn1, Sn1 = grupos(G ^ 1)
    d0, d1, dn0, dn1 = Rm - Sm, Rm1 - Sm1, Rn - Sn, Rn1 - Sn1
    a, b, c = 2 * (d1 + d0), (dn0 - dn1 - d1 - 3 * d0), (d0 - dn0)
    raices = np.roots([a, b, c]) if a != 0 else np.array([-c / b])
    raices = raices[np.isreal(raices)].real
    z = raices[np.argmin(np.abs(raices))] if len(raices) else float("nan")
    p = float(z / (z - 0.5)) if z == z else float("nan")
    return {"Rm": Rm, "Sm": Sm, "R-m": Rn, "S-m": Sn, "tasa_estimada": p}


casos = [("Audio original", None, None)]
L4, L6 = 1400, 10200
casos.append(("Estegoaudio sin corrección (1400 bits)", generar_posiciones_caoticas(*SP, L4, M), rng.integers(0, 2, L4, dtype=np.uint16)))
casos.append(("Estegoaudio con Reed-Solomon y repetición (10 200 bits)", generar_posiciones_caoticas(*SP, L6, M), rng.integers(0, 2, L6, dtype=np.uint16)))
for frac in (0.001, 0.01, 0.05, 0.10, 0.25, 0.50, 1.0):
    n = int(frac * M)
    casos.append((f"Carga sintética del {100 * frac:g} %", rng.choice(M, n, replace=False) if frac < 1 else np.arange(M), rng.integers(0, 2, n, dtype=np.uint16)))
res = []
for nombre, pos, bits in casos:
    x = audio if pos is None else insertar(audio, pos, bits)
    est, gl, p = chi_cuadrado(x)
    r = rs(x)
    fila = {"caso": nombre, "proporcion_muestras": 0.0 if pos is None else len(pos) / M, "chi2": est, "gl": gl, "p_chi2": p, **r}
    res.append(fila); print(json.dumps(fila, ensure_ascii=False), flush=True)
(SALIDA / "estegoanalisis.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
