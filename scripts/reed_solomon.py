"""Robustez con código corrector de errores: Reed-Solomon RS(255, 175) + repetición de cada bit.

Emisor: mensaje comprimido y cifrado (175 bytes) -> RS(255, 175) -> repetición de cada bit r veces -> LSB caótico.
Receptor: extracción -> decisión por mayoría -> decodificación RS -> descifrado.
Se repiten los ataques de la sección 3 (mismas funciones y semillas) y se compara con el modelo sin corrección.
"""
import json, os, sys
from pathlib import Path
import numpy as np
from reedsolo import RSCodec, ReedSolomonError
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.caos import generar_llave, derivar_semillas, generar_posiciones_caoticas
from src.utils.chaos_mod_enum import ChaosMod as C
from src.encriptado.encriptar import xor_encriptado
from src.esteganografiado.esteganografiar import cargar_archivo_wav
from scripts.generar_analisis_completo import ataque_sal_y_pimienta, ataque_oclusion, ataque_gaussiano

SALIDA = Path(os.environ.get("SALIDA_DIR", "outputs/revision_neuronal"))
X0, R, N = C.X0.value, C.R.value, C.N_WARMUP.value
SP = derivar_semillas(X0, R, N)[3:]
payload = Path("data/data_to_hide_comprimido_neuronal.bin").read_bytes()
k = generar_llave(X0, R, N, len(payload))
cif = bytes(np.asarray(xor_encriptado(np.frombuffer(payload, dtype=np.uint8), k), dtype=np.uint8).tolist())
audio = cargar_archivo_wav("data/audio_test.wav")
ATAQUES = [("Sal y pimienta", "5 %", lambda a: ataque_sal_y_pimienta(a, 0.05)), ("Sal y pimienta", "10 %", lambda a: ataque_sal_y_pimienta(a, 0.10)),
           ("Sal y pimienta", "25 %", lambda a: ataque_sal_y_pimienta(a, 0.25)), ("Oclusión", "5 %", lambda a: ataque_oclusion(a, 0.05)),
           ("Oclusión", "10 %", lambda a: ataque_oclusion(a, 0.10)), ("Oclusión", "25 %", lambda a: ataque_oclusion(a, 0.25)),
           ("Gaussiano", "SNR = 100 dB", lambda a: ataque_gaussiano(a, 100)), ("Gaussiano", "SNR = 90 dB", lambda a: ataque_gaussiano(a, 90)),
           ("Gaussiano", "SNR = 80 dB", lambda a: ataque_gaussiano(a, 80))]


def configuracion(nsym, rep):
    rs = RSCodec(nsym)
    cod = bytes(rs.encode(cif)) if nsym else cif
    bits = np.repeat(np.unpackbits(np.frombuffer(cod, dtype=np.uint8)), rep)
    P = generar_posiciones_caoticas(*SP, len(bits), len(audio))
    est = audio.copy(); u = est.view(np.uint16); u[P] = (u[P] & 0xFFFE) | bits
    d = audio.astype(np.float64) - est.astype(np.float64); mse = float(np.mean(d ** 2))
    out = {"nsym": nsym, "repeticion": rep, "bytes_codificados": len(cod), "L_bits": int(len(bits)),
           "pct_muestras": 100 * len(bits) / len(audio), "modificadas": int((d != 0).sum()), "mse": mse,
           "psnr_db": float(10 * np.log10(32767.0 ** 2 / mse)), "ataques": []}
    for nombre, nivel, f in [("Sin ataque", "—", lambda a: a)] + ATAQUES:
        at = f(est.copy())
        ext = (at.astype(np.int16).view(np.uint16)[P] & 1).astype(np.uint8)
        ber_bruta = float(np.mean(ext != bits))
        dec_bits = (ext.reshape(-1, rep).sum(1) * 2 > rep).astype(np.uint8)
        ref_bits = np.unpackbits(np.frombuffer(cod, dtype=np.uint8))
        ber_mayoria = float(np.mean(dec_bits != ref_bits))
        rec = bytes(np.packbits(dec_bits).tolist())
        bytes_err = int(sum(x != y for x, y in zip(rec, cod)))
        try:
            msg = bytes(rs.decode(rec)[0]) if nsym else rec
        except ReedSolomonError:
            msg = None
        exacto = msg is not None and bytes(np.asarray(xor_encriptado(np.frombuffer(msg, dtype=np.uint8), k), dtype=np.uint8).tolist()) == payload
        out["ataques"].append({"ataque": nombre, "nivel": nivel, "ber_bruta_pct": 100 * ber_bruta, "ber_tras_mayoria_pct": 100 * ber_mayoria,
                               "bytes_erroneos": bytes_err, "recuperacion_exacta": bool(exacto)})
        print(nsym, rep, nombre, nivel, f"{100*ber_bruta:.2f}", f"{100*ber_mayoria:.2f}", bytes_err, exacto, flush=True)
    return out


res = {"payload_bytes": len(payload), "configuraciones": [configuracion(0, 1), configuracion(80, 1), configuracion(80, 5)]}
(SALIDA / "reed_solomon.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
