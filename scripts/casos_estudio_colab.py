"""Casos de estudio adicionales: varios textos (dominio público) y varios audios (licencias libres)."""
import os, sys, subprocess, json, time, hashlib, zlib, bz2, lzma, urllib.request, tarfile, re
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers==4.48.0"], check=True)
os.makedirs("/content/se", exist_ok=True)
tarfile.open("/content/se_src.tgz").extractall("/content/se")
os.environ.update(MODELO_LM="Qwen/Qwen2.5-1.5B", DTYPE_LM="float32", DEVICE_LM="cuda", CUBLAS_WORKSPACE_CONFIG=":4096:8")
sys.path.insert(0, "/content/se")
import numpy as np, librosa, torch
from src.compresion import llm_aritmetico as la
from src.utils.caos import generar_llave, derivar_semillas, generar_posiciones_caoticas
from src.encriptado.encriptar import xor_encriptado

X0, R, N = 0.123456, 3.999952, 6173
SP = derivar_semillas(X0, R, N)[3:]

def gut(n):
    for u in (f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt", f"https://www.gutenberg.org/files/{n}/{n}-0.txt"):
        try:
            return urllib.request.urlopen(u, timeout=60).read().decode("utf-8-sig")
        except Exception as e:
            print("fallo", u, e)
    raise RuntimeError(n)

def parrafos(t):
    t = t.replace("\r\n", "\n")
    return [re.sub(r"\s+", " ", p).strip() for p in t.split("\n\n") if p.strip()]

textos = {"Nocturno (J. A. Silva), español": open("/content/texto_original.txt", encoding="utf-8").read()}
q = gut(2000); ps = parrafos(q)
i = next(k for k, p in enumerate(ps) if p.startswith("En un lugar de la Mancha"))
textos["Don Quijote, cap. I, párrafo 1, español"] = ps[i]
frag = ""
for p in ps[i:]:
    if len((frag + "\n" + p).encode()) > 3000:
        break
    frag = (frag + "\n" + p).strip()
textos["Don Quijote, cap. I, párrafos 1 a %d, español" % (frag.count("\n") + 1)] = frag
s = gut(1041).replace("\r\n", "\n")
j = s.index("Shall I compare thee to a summer")
lineas = [l.strip() for l in s[j:].split("\n")[:14]]
textos["Soneto 18 (W. Shakespeare), inglés"] = "\n".join(lineas)

audios = {}
for ex, desc in (("brahms", "Música orquestal (Brahms, Danza húngara n.º 5; dominio público)"),
                 ("nutcracker", "Música (Chaikovski, Cascanueces; versión de K. MacLeod, CC BY 3.0)"),
                 ("libri1", "Voz (LibriSpeech, CC BY 4.0)")):
    y, sr = librosa.load(librosa.ex(ex), sr=None, mono=False)
    y = np.atleast_2d(y)
    a = np.clip(np.rint(y.T.reshape(-1) * 32767), -32768, 32767).astype(np.int16)
    audios[desc] = (a, sr, y.shape[0])
import wave
with wave.open("/content/audio_test.wav", "rb") as w:
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).copy()
    audios["Música («Let it go», Rewob; CC), caso de estudio principal"] = (a, w.getframerate(), w.getnchannels())

res = {"gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "textos": [], "audios": [], "pares": []}
for desc, (a, sr, ch) in audios.items():
    res["audios"].append({"audio": desc, "fs_hz": sr, "canales": ch, "muestras": int(len(a)), "duracion_s": len(a) / ch / sr})
la.cargar_modelo()
for tdesc, t in textos.items():
    b = t.encode("utf-8"); reg = []
    t0 = time.time(); comp = la.comprimir(t, registro=reg); tc = time.time() - t0
    payload = len(comp).to_bytes(2, "big") + comp
    k = generar_llave(X0, R, N, len(payload))
    c = np.asarray(xor_encriptado(np.frombuffer(payload, dtype=np.uint8), k), dtype=np.uint8)
    bits = np.unpackbits(c)
    rec_payloads = []
    for adesc, (a, sr, ch) in audios.items():
        P = generar_posiciones_caoticas(*SP, len(bits), len(a))
        e = a.copy(); u = e.view(np.uint16); u[P] = (u[P] & 0xFFFE) | bits
        ext = (e.view(np.uint16)[P] & 1).astype(np.uint8)
        kp = generar_llave(X0, R, N, len(ext) // 8)
        pr = bytes(np.asarray(xor_encriptado(np.packbits(ext), kp), dtype=np.uint8).tolist())
        rec_payloads.append(pr)
        d = a.astype(np.float64) - e.astype(np.float64); mse = float(np.mean(d ** 2))
        res["pares"].append({"texto": tdesc, "audio": adesc, "L_bits": int(len(bits)), "pct_muestras": 100 * len(bits) / len(a),
                             "modificadas": int((d != 0).sum()), "mse": mse, "psnr_db": float(10 * np.log10(32767.0 ** 2 / mse)) if mse else None,
                             "payload_exacto": pr == payload})
    t0 = time.time(); txt = la.descomprimir(rec_payloads[0][2:2 + int.from_bytes(rec_payloads[0][:2], "big")]); td = time.time() - t0
    res["textos"].append({"texto": tdesc, "caracteres": len(t), "bytes": len(b), "tokens": len(reg) - 1, "bytes_comprimido": len(comp),
                          "bits_por_caracter": 8 * len(comp) / len(t), "pct": 100 * len(comp) / len(b),
                          "zlib": len(zlib.compress(b, 9)), "bzip2": len(bz2.compress(b, 9)),
                          "lzma": len(lzma.compress(b, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}])),
                          "t_comp_s": tc, "t_desc_s": td, "recuperacion_exacta": txt == t,
                          "sha_igual": hashlib.sha256(txt.encode()).hexdigest() == hashlib.sha256(b).hexdigest(),
                          "todos_payloads_iguales": all(p == payload for p in rec_payloads), "inicio": t[:60]})
    print(json.dumps(res["textos"][-1], ensure_ascii=False), flush=True)
json.dump(res, open("/content/casos.json", "w"), ensure_ascii=False, indent=1)
print("FIN", json.dumps(res, ensure_ascii=False))
