#!/usr/bin/env python3
"""Resolución efectiva de x0 y r: perturbación mínima (en ulps) con la que el 99 %
de las claves válidas produce un flujo de clave y unas posiciones independientes
(≥ 40 % de bits distintos y < 5 % de posiciones comunes)."""

import json
import math
import os
from pathlib import Path

import numpy as np

from src.utils.caos import clave_valida, derivar_semillas, generar_llave, generar_posiciones_caoticas

SALIDA = Path(os.environ.get("SALIDA_DIR", "outputs/revision_neuronal"))
L_BYTES, M, NPOS = 175, 25143552, 256


def independiente(k0, p0, clave):
    k = generar_llave(*clave, L_BYTES)
    try:
        p = set(generar_posiciones_caoticas(*derivar_semillas(*clave)[3:], NPOS, M).tolist())
    except ValueError:
        return True  # clave no válida: el atacante la descarta, no es equivalente
    return np.mean(np.unpackbits(k0) != np.unpackbits(k)) >= 0.40 and len(p0 & p) < 0.05 * NPOS


def main():
    rng = np.random.default_rng(11)
    claves = []
    while len(claves) < 300:
        c = (float(rng.uniform(1e-3, 1 - 1e-3)), float(rng.uniform(3.99, 4.0)), int(rng.integers(100, 10001)))
        if clave_valida(*c):
            try:
                generar_posiciones_caoticas(*derivar_semillas(*c)[3:], NPOS, M)
            except ValueError:
                continue
            claves.append(c)
    base = [(generar_llave(*c, L_BYTES), set(generar_posiciones_caoticas(*derivar_semillas(*c)[3:], NPOS, M).tolist())) for c in claves]
    res = {}
    for comp in ("x0", "r"):
        filas = []
        for e in range(0, 31):
            k = 2 ** e
            ok = 0
            for (x0, r, n), (k0, p0) in zip(claves, base):
                if comp == "x0":
                    v = (x0 + k * float(np.spacing(x0)), r, n)
                else:
                    v = (x0, r + k * float(np.spacing(r)), n)
                if not clave_valida(*v) or independiente(k0, p0, v):
                    ok += 1
            filas.append({"ulps": k, "frac_independiente": ok / len(claves)})
            print(comp, k, ok / len(claves), flush=True)
            if ok / len(claves) >= 0.99:
                break
        res[comp] = {"tabla": filas, "ulps_efectivos": filas[-1]["ulps"], "bits_perdidos": math.log2(filas[-1]["ulps"])}
    (SALIDA / "resolucion_clave.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({c: {k: v for k, v in d.items() if k != "tabla"} for c, d in res.items()}, indent=2))


if __name__ == "__main__":
    main()
