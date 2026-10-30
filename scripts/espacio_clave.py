#!/usr/bin/env python3
"""Espacio de clave efectivo del modelo (revisión TecnoLógicas).

1. Cuenta los valores float64 distintos en el rango admisible de x0 y de r.
2. Estima por Monte Carlo la fracción de pares (x0, r) que producen una clave
   válida, es decir, con exponente de Lyapunov positivo tanto para r (flujo de
   cifrado) como para r_p (selección de posiciones, derivado con derivar_semillas).
3. Verifica sobre claves válidas que un cambio de una sola unidad de redondeo
   (ulp) en x0 o r, o de una unidad en N, altera el flujo de clave y las posiciones.

Uso:
    SALIDA_DIR=outputs/revision_tecnologicas python -m scripts.espacio_clave
"""

import json
import math
import os
from pathlib import Path

import numpy as np

from src.utils.caos import clave_valida, derivar_parametros, derivar_semillas, exponente_lyapunov, generar_llave, generar_posiciones_caoticas
from src.utils.chaos_mod_enum import ChaosMod as C

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = Path(os.environ.get("SALIDA_DIR", RAIZ / "outputs" / "revision_tecnologicas"))
SEG_ANIO = 365.25 * 24 * 3600
X0_MIN, X0_MAX = 1e-3, 1 - 1e-3
R_MIN, R_MAX = 3.99, 4.0


def n_float64(a, b):
    """Número de valores float64 en [a, b) (0 < a < b)."""
    return int(np.array(b, dtype=np.float64).view(np.int64) - np.array(a, dtype=np.float64).view(np.int64))


def main():
    rng = np.random.default_rng(2026)
    res = {}

    # Fracción de claves válidas (Monte Carlo, vectorizado)
    m = 100_000
    x0 = rng.uniform(X0_MIN, X0_MAX, m)
    r = rng.uniform(R_MIN, R_MAX, m)
    nn_mc = rng.integers(100, 10001, m)
    dd = [derivar_parametros(a, b, int(c)) for a, b, c in zip(x0, r, nn_mc)]
    lam_r1 = exponente_lyapunov([d["r1"] for d in dd])
    lam_r2 = exponente_lyapunov([d["r2"] for d in dd])
    lam_rp = exponente_lyapunov([d["rp"] for d in dd])
    ok_r = (lam_r1 > 0) & (lam_r2 > 0)
    ok_rp = lam_rp > 0
    p_valida = float(np.mean(ok_r & ok_rp))
    # Equilibrio del flujo de clave (proporción de unos) en 300 claves válidas
    unos = []
    while len(unos) < 300:
        c = (float(rng.uniform(X0_MIN, X0_MAX)), float(rng.uniform(R_MIN, R_MAX)), int(rng.integers(100, 10001)))
        if clave_valida(*c):
            unos.append(float(np.unpackbits(generar_llave(*c, 175)).mean()))
    res["equilibrio_keystream"] = {"media": float(np.mean(unos)), "min": float(np.min(unos)), "max": float(np.max(unos)),
                                   "frac_entre_045_055": float(np.mean((np.array(unos) >= 0.45) & (np.array(unos) <= 0.55)))}
    res["monte_carlo"] = {"muestras": m, "frac_r_caotico": float(ok_r.mean()), "frac_rp_caotico": float(ok_rp.mean()),
                          "frac_clave_valida": p_valida, "error_estandar": float(math.sqrt(p_valida * (1 - p_valida) / m))}

    nx0, nr = n_float64(X0_MIN, X0_MAX), n_float64(R_MIN, R_MAX)
    nn = C.N_WARMUP_MAX.value - C.N_WARMUP_MIN.value + 1
    total = nx0 * nr * p_valida * nn
    res["componentes"] = {
        "x0": {"rango": [X0_MIN, X0_MAX], "valores_float64": nx0, "bits": math.log2(nx0)},
        "r": {"rango": [R_MIN, R_MAX], "valores_float64": nr, "bits": math.log2(nr)},
        "N": {"rango": [C.N_WARMUP_MIN.value, C.N_WARMUP_MAX.value], "valores": nn, "bits": math.log2(nn)},
        "fraccion_valida": {"valor": p_valida, "bits": math.log2(p_valida)},
    }
    res["total"] = {"claves": total, "bits": math.log2(total)}
    res["almacenamiento_bits"] = {"x0_float64": 64, "r_float64": 64, "N_uint16": 16, "total": 144}
    res["fuerza_bruta_anios"] = {"1e9": total / 1e9 / SEG_ANIO, "1e12": total / 1e12 / SEG_ANIO}

    # Sensibilidad a 1 ulp en claves válidas
    L, M = 1400, 25143552
    sens = {"x0": [], "r": [], "N": []}
    comunes = {"x0": [], "r": [], "N": []}
    invalidas = 0
    while len(sens["x0"]) < 200:
        a, b, n = float(rng.uniform(X0_MIN, X0_MAX)), float(rng.uniform(R_MIN, R_MAX)), int(rng.integers(100, 10001))
        variantes = {"x0": (float(np.nextafter(a, 1.0)), b, n), "r": (a, float(np.nextafter(b, 4.0)), n), "N": (a, b, n + 1)}
        if not clave_valida(a, b, n) or not all(clave_valida(*v) for v in variantes.values()):
            invalidas += 1
            continue
        k0 = generar_llave(a, b, n, L // 8)
        p0 = set(generar_posiciones_caoticas(*derivar_semillas(a, b, n)[3:], 256, M).tolist())
        for comp, v in variantes.items():
            k = generar_llave(*v, L // 8)
            sens[comp].append(float(np.mean(np.unpackbits(k0) != np.unpackbits(k)) * 100))
            comunes[comp].append(len(p0 & set(generar_posiciones_caoticas(*derivar_semillas(*v)[3:], 256, M).tolist())))
    res["sensibilidad"] = {c: {"pct_bits_keystream_media": float(np.mean(v)), "min": float(np.min(v)), "max": float(np.max(v)),
                               "posiciones_comunes_de_256_media": float(np.mean(comunes[c]))} for c, v in sens.items()}
    res["sensibilidad"]["claves_descartadas_por_invalidas"] = invalidas

    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "espacio_clave.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
