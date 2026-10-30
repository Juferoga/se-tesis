"""Pruebas NIST SP 800-22 sobre el flujo de clave: 10 claves válidas (incluida la del caso de estudio), 10^6 bits cada una.

Implementación propia de las fórmulas del estándar (src/utils/nist_sp800_22.py), validada con los ejemplos del documento
y con secuencias de os.urandom como control."""
import json, os, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.caos import clave_valida, generar_llave
from src.utils.chaos_mod_enum import ChaosMod as C
from src.utils.nist_sp800_22 import PRUEBAS

SALIDA = Path(os.environ.get("SALIDA_DIR", "outputs/revision_neuronal"))
BYTES = 125000


def claves(m=10):
    rng = np.random.default_rng(800)
    out = [(C.X0.value, C.R.value, C.N_WARMUP.value)]
    while len(out) < m:
        k = (float(rng.uniform(0.001, 0.999)), float(rng.uniform(3.99, 4.0)), int(rng.integers(100, 10001)))
        if clave_valida(*k):
            out.append(k)
    return out


def evaluar(arg):
    tipo, k = arg
    datos = bytes(generar_llave(*k, BYTES)) if tipo == "flujo" else os.urandom(BYTES)
    e = np.unpackbits(np.frombuffer(datos, dtype=np.uint8))
    res = {}
    for nombre, f in PRUEBAS.items():
        v = f(e)
        for i, p in enumerate(v if isinstance(v, list) else [v]):
            res[nombre + (f" ({i + 1})" if isinstance(v, list) else "")] = p
    return {"tipo": tipo, "clave": k, "unos": float(e.mean()), "p": res}


if __name__ == "__main__":
    tareas = [("flujo", k) for k in claves()] + [("control", None)] * 10
    with Pool(7) as pool:
        r = pool.map(evaluar, tareas)
    resumen = {}
    for tipo in ("flujo", "control"):
        rr = [x for x in r if x["tipo"] == tipo]
        resumen[tipo] = {n: {"aprobadas": sum(x["p"][n] >= 0.01 for x in rr), "evaluadas": len(rr), "p_min": min(x["p"][n] for x in rr)} for n in rr[0]["p"]}
    (SALIDA / "nist_sp800_22.json").write_text(json.dumps({"bits_por_secuencia": 8 * BYTES, "secuencias": 10, "alfa": 0.01,
                                                           "resumen": resumen["flujo"], "control_urandom": resumen["control"], "detalle": r},
                                                          indent=1, ensure_ascii=False))
    for n, v in resumen["flujo"].items():
        c = resumen["control"][n]
        print(n, "flujo", v["aprobadas"], round(v["p_min"], 4), "control", c["aprobadas"])
