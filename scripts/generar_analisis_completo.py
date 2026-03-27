#!/usr/bin/env python3
"""Análisis completo para la entrega a profesoras.

Genera todas las pruebas y visualizaciones solicitadas:
1. Entropía con valores numéricos (nats y bits)
2. NPCR y UACI (análisis diferencial)
3. Histogramas de texto original vs encriptado
4. Correlación texto original vs encriptado
5. Sensibilidad de la clave
6. Robustez: sal y pimienta + oclusión
7. Seguridad de la clave
8. Visualizaciones mejoradas (distribución caótica)

Uso:
    python -m scripts.generar_analisis_completo
"""

from __future__ import annotations

import json
import wave
from math import log
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr

from src.encriptado.encriptar import xor_encriptado
from src.utils.caos import generar_llave, generar_posiciones_caoticas
from src.utils.chaos_mod_enum import ChaosMod
from src.esteganografiado.esteganografiar import cargar_archivo_wav
from src.esteganografiado.desesteganografiar import extraer_lsb_caotico

# ============================================================
# CONSTANTES Y ESTILO
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "outputs" / "entrega_profesoras"
SALIDA.mkdir(parents=True, exist_ok=True)

# Parámetros del sistema caótico
X0 = ChaosMod.X0.value        # 0.123456
R = ChaosMod.R.value           # 3.999952
N_WARMUP = ChaosMod.N_WARMUP.value  # 100

# Estilo premium para todas las gráficas
plt.style.use("dark_background")
COLORES = {
    "original": "#00D4AA",
    "modificado": "#FF6B6B",
    "acento": "#4ECDC4",
    "alerta": "#FFE66D",
    "texto": "#E8E8E8",
    "grid": "#333333",
    "exito": "#00D4AA",
    "fallo": "#FF6B6B",
}
DPI = 200
FONT_TITLE = {"fontsize": 14, "fontweight": "bold", "color": COLORES["texto"]}
FONT_LABEL = {"fontsize": 11, "color": COLORES["texto"]}


def _guardar(fig, nombre: str) -> Path:
    ruta = SALIDA / nombre
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [OK] {nombre}")
    return ruta


# ============================================================
# 1. CARGA DE DATOS EXISTENTES
# ============================================================

def cargar_datos():
    """Carga audio y texto comprimido de archivos existentes."""
    ruta_audio_orig = RAIZ / "data" / "audio_test.wav"
    ruta_audio_mod = RAIZ / "data" / "audio_test_modificado.wav"
    ruta_texto_comp = SALIDA / "texto_comprimido.txt"

    # Audio
    audio_original = cargar_archivo_wav(str(ruta_audio_orig))
    audio_modificado = cargar_archivo_wav(str(ruta_audio_mod))

    with wave.open(str(ruta_audio_orig), "rb") as f:
        params = f.getparams()
        sample_rate = f.getframerate()

    # Texto comprimido
    texto_comprimido = ruta_texto_comp.read_text(encoding="utf-8")

    # Re-derivar intermediarios criptográficos
    texto_bytes = np.array(list(texto_comprimido.encode("utf-8")), dtype=np.uint8)
    llave = generar_llave(X0, R, N_WARMUP, len(texto_bytes))
    texto_encriptado = xor_encriptado(texto_bytes, llave)

    # Bits del mensaje encriptado
    mensaje_para_paso = "".join([chr(b) for b in texto_encriptado])
    mensaje_bits = "".join([format(ord(c), "08b") for c in mensaje_para_paso])

    # Generar posiciones caóticas (las mismas usadas en la inserción)
    n_bits = len(mensaje_bits)
    n_muestras = len(audio_original)
    posiciones = generar_posiciones_caoticas(X0, R, N_WARMUP, n_bits, n_muestras)

    print(f"  Audio original:    {n_muestras} muestras")
    print(f"  Audio modificado:  {len(audio_modificado)} muestras")
    print(f"  Texto comprimido:  {len(texto_comprimido)} caracteres")
    print(f"  Payload:           {n_bits} bits ({len(texto_bytes)} bytes)")
    print(f"  Posiciones:        distribuidas en [0, {n_muestras})")
    print(f"    min={posiciones.min()}, max={posiciones.max()}, std={posiciones.std():.0f}")

    return {
        "audio_original": audio_original,
        "audio_modificado": audio_modificado,
        "sample_rate": sample_rate,
        "params": params,
        "texto_bytes": texto_bytes,
        "llave": llave,
        "texto_encriptado": texto_encriptado,
        "mensaje_bits": mensaje_bits,
        "posiciones": posiciones,
        "texto_comprimido": texto_comprimido,
    }


# ============================================================
# 2. ENTROPÍA (Obs. 1)
# ============================================================

def analisis_entropia(datos):
    """Calcula y grafica la entropía del audio original y modificado."""
    print("\n--- Análisis de Entropía")

    def _entropia(arr):
        _, counts = np.unique(arr, return_counts=True)
        probs = counts / len(arr)
        return -np.sum(probs * np.log(probs))  # nats

    h_orig_nats = _entropia(datos["audio_original"])
    h_mod_nats = _entropia(datos["audio_modificado"])
    h_orig_bits = h_orig_nats / log(2)
    h_mod_bits = h_mod_nats / log(2)
    h_max_bits = 16.0  # audio de 16 bits

    print(f"  Entropía original:   {h_orig_nats:.6f} nats = {h_orig_bits:.4f} bits")
    print(f"  Entropía modificado: {h_mod_nats:.6f} nats = {h_mod_bits:.4f} bits")
    print(f"  Entropía máxima:     {log(2**16):.6f} nats = {h_max_bits:.4f} bits")
    print(f"  Delta entropía:      {abs(h_mod_nats - h_orig_nats):.10f} nats")

    # Gráfica: tabla visual
    fig, ax = plt.subplots(figsize=(10, 4), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.axis("off")

    tabla_data = [
        ["Entropía (nats)", f"{h_orig_nats:.6f}", f"{h_mod_nats:.6f}", f"{abs(h_mod_nats - h_orig_nats):.10f}"],
        ["Entropía (bits)", f"{h_orig_bits:.4f}", f"{h_mod_bits:.4f}", f"{abs(h_mod_bits - h_orig_bits):.10f}"],
        ["Máx. teórica (bits)", f"{h_max_bits:.1f}", f"{h_max_bits:.1f}", "—"],
        ["% del máximo", f"{h_orig_bits/h_max_bits*100:.2f}%", f"{h_mod_bits/h_max_bits*100:.2f}%", "—"],
    ]
    colores_celda = [["#2a2a4a"] * 4] * 4
    tabla = ax.table(
        cellText=tabla_data,
        colLabels=["Métrica", "Audio Original", "Audio Esteganografiado", "Diferencia (Delta)"],
        cellColours=colores_celda,
        colColours=["#3a3a5a"] * 4,
        loc="center",
        cellLoc="center",
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(11)
    for key, cell in tabla.get_celld().items():
        cell.set_edgecolor("#555577")
        cell.set_text_props(color=COLORES["texto"])
        if key[0] == 0:
            cell.set_text_props(color=COLORES["original"], fontweight="bold")
    tabla.scale(1, 1.8)
    ax.set_title("Análisis de Entropía — Audio de 16 bits (PCM WAV)", **FONT_TITLE, pad=20)
    _guardar(fig, "entropia_tabla.png")

    return {
        "h_orig_nats": h_orig_nats, "h_mod_nats": h_mod_nats,
        "h_orig_bits": h_orig_bits, "h_mod_bits": h_mod_bits,
    }


# ============================================================
# 3. MSE, PSNR Y COVARIANZA
# ============================================================

def analisis_mse_covarianza(datos):
    """Calcula MSE, PSNR y covarianza entre audio original y modificado."""
    print("\n--- Error Cuadrático Medio (MSE) y Covarianza")

    orig = datos["audio_original"].astype(np.float64)
    mod = datos["audio_modificado"].astype(np.float64)
    n = len(orig)

    # MSE
    mse = np.mean((orig - mod) ** 2)

    # PSNR (para audio de 16 bits, valor máximo = 32767)
    if mse > 0:
        psnr = 10 * np.log10((32767.0 ** 2) / mse)
    else:
        psnr = float('inf')

    # Covarianza
    cov_matrix = np.cov(orig, mod)
    cov_orig_orig = cov_matrix[0, 0]  # Var(original)
    cov_mod_mod = cov_matrix[1, 1]    # Var(modificado)
    cov_orig_mod = cov_matrix[0, 1]   # Cov(original, modificado)

    # Coeficiente de correlación de Pearson entre señales de audio
    r_audio = cov_orig_mod / np.sqrt(cov_orig_orig * cov_mod_mod)

    print(f"  MSE:                {mse:.6f}")
    print(f"  PSNR:               {psnr:.2f} dB")
    print(f"  Var(original):      {cov_orig_orig:.4f}")
    print(f"  Var(modificado):    {cov_mod_mod:.4f}")
    print(f"  Cov(orig, mod):     {cov_orig_mod:.4f}")
    print(f"  Correlación audio:  {r_audio:.10f}")

    # Gráfica: tabla + barras
    fig, axes = plt.subplots(1, 2, figsize=(16, 5), facecolor="#1a1a2e")
    for ax in axes:
        ax.set_facecolor("#1a1a2e")

    # Tabla
    axes[0].axis("off")
    tabla_data = [
        ["MSE", f"{mse:.6f}"],
        ["PSNR", f"{psnr:.2f} dB"],
        ["Var(original)", f"{cov_orig_orig:.4f}"],
        ["Var(modificado)", f"{cov_mod_mod:.4f}"],
        ["Cov(orig, mod)", f"{cov_orig_mod:.4f}"],
        ["Correlación señales", f"{r_audio:.10f}"],
    ]
    colores_celda = [["#2a2a4a"] * 2] * 6
    tabla = axes[0].table(
        cellText=tabla_data,
        colLabels=["Métrica", "Valor"],
        cellColours=colores_celda,
        colColours=["#3a3a5a"] * 2,
        loc="center",
        cellLoc="center",
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(12)
    for key, cell in tabla.get_celld().items():
        cell.set_edgecolor("#555577")
        cell.set_text_props(color=COLORES["texto"])
        if key[0] == 0:
            cell.set_text_props(color=COLORES["original"], fontweight="bold")
    tabla.scale(1, 2.0)
    axes[0].set_title("MSE, PSNR y Covarianza", **FONT_TITLE, pad=20)

    # Barra visual MSE vs umbral
    cats = ["MSE\nobtenido", "MSE ideal\n(= 0)"]
    vals = [mse, 0.0]
    bars = axes[1].bar(cats, vals, color=[COLORES["original"], COLORES["acento"]], width=0.4, edgecolor="#555577")
    axes[1].set_title("Error Cuadrático Medio (MSE)", **FONT_TITLE)
    axes[1].set_ylabel("MSE", **FONT_LABEL)
    axes[1].grid(axis="y", alpha=0.2, color=COLORES["grid"])
    for bar, val in zip(bars, vals):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
                     f"{val:.6f}", ha="center", va="bottom", color=COLORES["texto"], fontsize=11, fontweight="bold")

    # Anotar PSNR
    axes[1].text(0.95, 0.85, f"PSNR = {psnr:.2f} dB\n(> 30 dB = imperceptible)",
                 transform=axes[1].transAxes, ha="right", va="top",
                 fontsize=11, color=COLORES["alerta"],
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="#2a2a4a", edgecolor=COLORES["alerta"]))

    fig.suptitle("Análisis de Fidelidad — Error Cuadrático Medio y Covarianza",
                 fontsize=16, fontweight="bold", color=COLORES["texto"], y=1.02)
    fig.tight_layout()
    _guardar(fig, "mse_covarianza.png")

    return {
        "mse": float(mse), "psnr_db": float(psnr),
        "var_orig": float(cov_orig_orig), "var_mod": float(cov_mod_mod),
        "cov_orig_mod": float(cov_orig_mod), "r_audio": float(r_audio),
    }


# ============================================================
# 4. NPCR Y UACI (Obs. 2)
# ============================================================

def analisis_npcr_uaci(datos):
    """Calcula NPCR y UACI entre audio original y modificado."""
    print("\n--- Análisis Diferencial: NPCR y UACI")

    orig = datos["audio_original"].astype(np.float64)
    mod = datos["audio_modificado"].astype(np.float64)

    def _npcr_uaci(a, b):
        n = len(a)
        d = (a != b).astype(np.float64)
        npcr = np.sum(d) / n * 100
        uaci = np.sum(np.abs(a - b)) / (n * 65535) * 100
        return npcr, uaci

    # Audio completo
    npcr_total, uaci_total = _npcr_uaci(orig, mod)

    # Analizar distribución por regiones (4 cuartiles)
    n = len(orig)
    cuartil_size = n // 4
    npcr_cuartiles = []
    for q in range(4):
        s = q * cuartil_size
        e = s + cuartil_size
        npcr_q, _ = _npcr_uaci(orig[s:e], mod[s:e])
        npcr_cuartiles.append(npcr_q)
        print(f"  Cuartil Q{q+1} [{s}:{e}] — NPCR: {npcr_q:.6f}%")

    print(f"  Audio completo — NPCR: {npcr_total:.6f}%  UACI: {uaci_total:.8f}%")

    # Gráfica comparativa
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor="#1a1a2e")
    for ax in axes:
        ax.set_facecolor("#1a1a2e")

    # NPCR por cuartiles + total
    cats = ["Q1", "Q2", "Q3", "Q4", "Total"]
    npcr_vals = npcr_cuartiles + [npcr_total]
    colores = [COLORES["acento"]] * 4 + [COLORES["original"]]
    bars1 = axes[0].bar(cats, npcr_vals, color=colores, width=0.5, edgecolor="#555577")
    axes[0].set_title("NPCR por Cuartil del Audio", **FONT_TITLE)
    axes[0].set_ylabel("NPCR (%)", **FONT_LABEL)
    axes[0].grid(axis="y", alpha=0.2, color=COLORES["grid"])
    for bar, val in zip(bars1, npcr_vals):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.0002,
                     f"{val:.4f}%", ha="center", va="bottom", color=COLORES["texto"], fontsize=10, fontweight="bold")

    # UACI total
    uaci_cats = ["Audio\ncompleto"]
    bars2 = axes[1].bar(uaci_cats, [uaci_total], color=[COLORES["original"]], width=0.3, edgecolor="#555577")
    axes[1].set_title("UACI (Unified Average Changing Intensity)", **FONT_TITLE)
    axes[1].set_ylabel("UACI (%)", **FONT_LABEL)
    axes[1].grid(axis="y", alpha=0.2, color=COLORES["grid"])
    for bar, val in zip(bars2, [uaci_total]):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.05,
                     f"{val:.8f}%", ha="center", va="bottom", color=COLORES["texto"], fontsize=11, fontweight="bold")

    fig.suptitle("Análisis Diferencial — Distribución Caótica en Audio Completo", fontsize=16, fontweight="bold", color=COLORES["texto"], y=1.02)
    fig.tight_layout()
    _guardar(fig, "npcr_uaci.png")

    return {"npcr_total": npcr_total, "uaci_total": uaci_total, "npcr_cuartiles": npcr_cuartiles}


# ============================================================
# 4. HISTOGRAMAS TEXTO ORIGINAL vs ENCRIPTADO (Obs. 4)
# ============================================================

def analisis_histogramas_texto(datos):
    """Histogramas de distribución de bytes del texto original y encriptado."""
    print("\n--- Histogramas de Texto Original vs Encriptado")

    texto_bytes = datos["texto_bytes"]
    texto_enc = datos["texto_encriptado"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor="#1a1a2e")
    for ax in axes:
        ax.set_facecolor("#1a1a2e")

    axes[0].hist(texto_bytes, bins=range(0, 257), color=COLORES["original"], alpha=0.85, edgecolor="#1a1a2e", linewidth=0.3)
    axes[0].set_title("Distribución de Bytes — Texto Original", **FONT_TITLE)
    axes[0].set_xlabel("Valor del byte (0-255)", **FONT_LABEL)
    axes[0].set_ylabel("Frecuencia", **FONT_LABEL)
    axes[0].grid(axis="y", alpha=0.2, color=COLORES["grid"])
    axes[0].set_xlim(0, 255)

    axes[1].hist(texto_enc, bins=range(0, 257), color=COLORES["modificado"], alpha=0.85, edgecolor="#1a1a2e", linewidth=0.3)
    axes[1].set_title("Distribución de Bytes — Texto Encriptado (XOR Caótico)", **FONT_TITLE)
    axes[1].set_xlabel("Valor del byte (0-255)", **FONT_LABEL)
    axes[1].set_ylabel("Frecuencia", **FONT_LABEL)
    axes[1].grid(axis="y", alpha=0.2, color=COLORES["grid"])
    axes[1].set_xlim(0, 255)

    fig.suptitle("Análisis Estadístico — Distribución de Bytes Pre y Post Encriptación",
                 fontsize=16, fontweight="bold", color=COLORES["texto"], y=1.02)
    fig.tight_layout()
    _guardar(fig, "histograma_texto.png")


# ============================================================
# 5. CORRELACIÓN TEXTO ORIGINAL vs ENCRIPTADO (Obs. 5)
# ============================================================

def analisis_correlacion_texto(datos):
    """Scatter plot y coeficiente de Pearson entre bytes originales y encriptados."""
    print("\n--- Correlación Texto Original vs Encriptado")

    texto_bytes = datos["texto_bytes"].astype(np.float64)
    texto_enc = datos["texto_encriptado"].astype(np.float64)
    r_pearson, p_valor = pearsonr(texto_bytes, texto_enc)

    print(f"  Coeficiente de Pearson: {r_pearson:.6f}")
    print(f"  P-valor:                {p_valor:.6f}")

    fig, ax = plt.subplots(figsize=(8, 8), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.scatter(texto_bytes, texto_enc, c=COLORES["acento"], alpha=0.6, s=20, edgecolors="none")
    ax.plot([0, 255], [0, 255], "--", color=COLORES["alerta"], alpha=0.5, linewidth=1, label="Correlación perfecta (y=x)")
    ax.set_xlabel("Byte del Texto Original", **FONT_LABEL)
    ax.set_ylabel("Byte del Texto Encriptado", **FONT_LABEL)
    ax.set_title(f"Correlación Texto Original vs Encriptado\nr = {r_pearson:.6f}  (p = {p_valor:.4f})", **FONT_TITLE)
    ax.set_xlim(0, 255)
    ax.set_ylim(0, 255)
    ax.set_aspect("equal")
    ax.grid(alpha=0.15, color=COLORES["grid"])
    ax.legend(loc="upper left", fontsize=10)

    ax.text(0.95, 0.05, f"r = {r_pearson:.6f}\n(sin correlación lineal)",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=12, color=COLORES["alerta"],
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#2a2a4a", edgecolor=COLORES["alerta"], alpha=0.9))

    fig.tight_layout()
    _guardar(fig, "correlacion_texto.png")

    return {"r_pearson": r_pearson, "p_valor": p_valor}


# ============================================================
# 6. SENSIBILIDAD DE LA CLAVE (Obs. 6)
# ============================================================

def analisis_sensibilidad_clave(datos):
    """Análisis de sensibilidad: pequeña perturbación en la clave -> resultado completamente distinto."""
    print("\n--- Análisis de Sensibilidad de la Clave")

    texto_enc = datos["texto_encriptado"]
    longitud = len(datos["texto_bytes"])

    # Clave correcta
    llave_correcta = datos["llave"]
    texto_correcto = xor_encriptado(texto_enc, llave_correcta)

    # Clave perturbada (x0 + 1e-15)
    perturbacion = 1e-15
    x0_perturbado = X0 + perturbacion
    llave_perturbada = generar_llave(x0_perturbado, R, N_WARMUP, longitud)
    texto_perturbado = xor_encriptado(texto_enc, llave_perturbada)

    # Diferencia
    bytes_diferentes = np.sum(texto_correcto != texto_perturbado)
    porcentaje_dif = bytes_diferentes / longitud * 100

    # Bits diferentes (Hamming distance)
    bits_dif = sum(bin(a ^ b).count("1") for a, b in zip(texto_correcto, texto_perturbado))
    total_bits = longitud * 8
    porcentaje_bits = bits_dif / total_bits * 100

    print(f"  Clave original:    x0 = {X0}")
    print(f"  Clave perturbada:  x0 = {x0_perturbado} (Delta = {perturbacion})")
    print(f"  Bytes diferentes:  {bytes_diferentes}/{longitud} ({porcentaje_dif:.2f}%)")
    print(f"  Bits diferentes:   {bits_dif}/{total_bits} ({porcentaje_bits:.2f}%)")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10), facecolor="#1a1a2e")
    for ax in axes.flat:
        ax.set_facecolor("#1a1a2e")

    x = np.arange(longitud)
    axes[0][0].bar(x, texto_correcto, color=COLORES["original"], alpha=0.8, width=1.0)
    axes[0][0].set_title("Texto Desencriptado — Clave Correcta", **FONT_TITLE)
    axes[0][0].set_xlabel("Posición del byte", **FONT_LABEL)
    axes[0][0].set_ylabel("Valor del byte", **FONT_LABEL)
    axes[0][0].grid(axis="y", alpha=0.15, color=COLORES["grid"])

    axes[0][1].bar(x, texto_perturbado, color=COLORES["modificado"], alpha=0.8, width=1.0)
    axes[0][1].set_title(f"Texto Desencriptado — Clave Perturbada (Dx0 = {perturbacion})", **FONT_TITLE)
    axes[0][1].set_xlabel("Posición del byte", **FONT_LABEL)
    axes[0][1].set_ylabel("Valor del byte", **FONT_LABEL)
    axes[0][1].grid(axis="y", alpha=0.15, color=COLORES["grid"])

    diff_abs = np.abs(texto_correcto.astype(np.int16) - texto_perturbado.astype(np.int16))
    axes[1][0].bar(x, diff_abs, color=COLORES["alerta"], alpha=0.85, width=1.0)
    axes[1][0].set_title("Diferencia Absoluta Byte a Byte", **FONT_TITLE)
    axes[1][0].set_xlabel("Posición del byte", **FONT_LABEL)
    axes[1][0].set_ylabel("|correcto - perturbado|", **FONT_LABEL)
    axes[1][0].grid(axis="y", alpha=0.15, color=COLORES["grid"])

    axes[1][1].axis("off")
    info_text = (
        f"Componentes de la Clave\n"
        f"{'_' * 40}\n"
        f"x0 (punto inicial):   {X0}\n"
        f"r  (parametro caos):  {R}\n"
        f"n  (calentamiento):   {N_WARMUP} iteraciones\n\n"
        f"Perturbacion Aplicada\n"
        f"{'_' * 40}\n"
        f"Dx0 = {perturbacion}\n"
        f"x0' = {x0_perturbado}\n\n"
        f"Resultado\n"
        f"{'_' * 40}\n"
        f"Bytes diferentes: {bytes_diferentes}/{longitud} ({porcentaje_dif:.2f}%)\n"
        f"Bits diferentes:  {bits_dif}/{total_bits} ({porcentaje_bits:.2f}%)\n"
        f"Efecto avalancha: {'SI' if porcentaje_bits > 40 else 'NO'}"
    )
    axes[1][1].text(0.1, 0.95, info_text, transform=axes[1][1].transAxes,
                    fontsize=12, color=COLORES["texto"], verticalalignment="top",
                    fontfamily="monospace",
                    bbox=dict(boxstyle="round,pad=0.6", facecolor="#2a2a4a", edgecolor="#555577"))

    fig.suptitle("Análisis de Sensibilidad de la Clave — Efecto Avalancha",
                 fontsize=16, fontweight="bold", color=COLORES["texto"], y=1.02)
    fig.tight_layout()
    _guardar(fig, "sensibilidad_clave.png")

    return {
        "perturbacion": perturbacion,
        "bytes_dif": int(bytes_diferentes),
        "porcentaje_dif": porcentaje_dif,
        "bits_dif": bits_dif,
        "porcentaje_bits": porcentaje_bits,
    }


# ============================================================
# 7. ROBUSTEZ: SAL Y PIMIENTA + OCLUSIÓN (Obs. 7)
# ============================================================

def _extraer_y_comparar_caotico(audio_mod, n_bits, bits_referencia):
    """Extrae mensaje de audio usando posiciones caóticas y compara con referencia."""
    try:
        bits_ext, _ = extraer_lsb_caotico(audio_mod, n_bits, X0, R, N_WARMUP)
        correctos = sum(1 for a, b in zip(bits_referencia, bits_ext) if a == b)
        return correctos / n_bits * 100
    except Exception:
        return 0.0


def ataque_sal_y_pimienta(audio, proporcion):
    """Sal y pimienta sobre el audio completo."""
    audio_atacado = np.copy(audio)
    n = len(audio_atacado)
    n_afectados = int(n * proporcion)

    np.random.seed(42)
    indices = np.random.choice(n, n_afectados, replace=False)
    mitad = n_afectados // 2
    audio_atacado[indices[:mitad]] = 32767      # sal
    audio_atacado[indices[mitad:]] = -32768     # pimienta

    return audio_atacado


def ataque_oclusion(audio, proporcion):
    """Oclusión: pone a cero un bloque contiguo."""
    audio_atacado = np.copy(audio)
    n = len(audio_atacado)
    tam_bloque = int(n * proporcion)

    np.random.seed(42)
    pos_inicio = np.random.randint(0, max(1, n - tam_bloque))
    audio_atacado[pos_inicio:pos_inicio + tam_bloque] = 0

    return audio_atacado


def analisis_robustez(datos):
    """Ejecuta ataques de sal/pimienta y oclusión con múltiples proporciones."""
    print("\n--- Análisis de Robustez: Sal y Pimienta + Oclusión")

    audio = datos["audio_modificado"]
    n_bits = len(datos["mensaje_bits"])

    # Extraer bits de referencia (del audio sin atacar)
    bits_ref, _ = extraer_lsb_caotico(audio, n_bits, X0, R, N_WARMUP)

    proporciones = [0.01, 0.05, 0.10, 0.25]
    resultados_sp = []
    resultados_oc = []

    for p in proporciones:
        # Sal y pimienta
        audio_sp = ataque_sal_y_pimienta(audio, p)
        pct_sp = _extraer_y_comparar_caotico(audio_sp, n_bits, bits_ref)
        resultados_sp.append(pct_sp)
        print(f"  Sal y Pimienta {p*100:.0f}%: {pct_sp:.2f}% bits correctos")

        # Oclusión
        audio_oc = ataque_oclusion(audio, p)
        pct_oc = _extraer_y_comparar_caotico(audio_oc, n_bits, bits_ref)
        resultados_oc.append(pct_oc)
        print(f"  Oclusión       {p*100:.0f}%: {pct_oc:.2f}% bits correctos")

    # Gráfica
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor="#1a1a2e")
    for ax in axes:
        ax.set_facecolor("#1a1a2e")

    labels = [f"{p*100:.0f}%" for p in proporciones]
    x_pos = np.arange(len(proporciones))

    # Sal y pimienta
    colores_sp = [COLORES["exito"] if v >= 95 else COLORES["fallo"] for v in resultados_sp]
    bars1 = axes[0].bar(x_pos, resultados_sp, color=colores_sp, width=0.5, edgecolor="#555577")
    axes[0].axhline(y=95, color=COLORES["alerta"], linestyle="--", alpha=0.7, label="Umbral éxito (95%)")
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(labels)
    axes[0].set_title("Ataque Sal y Pimienta", **FONT_TITLE)
    axes[0].set_xlabel("Proporción de ataque", **FONT_LABEL)
    axes[0].set_ylabel("Bits correctos (%)", **FONT_LABEL)
    axes[0].set_ylim(0, 105)
    axes[0].grid(axis="y", alpha=0.2, color=COLORES["grid"])
    axes[0].legend(fontsize=10)
    for bar, val in zip(bars1, resultados_sp):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f"{val:.1f}%", ha="center", va="bottom", color=COLORES["texto"], fontsize=10, fontweight="bold")

    # Oclusión
    colores_oc = [COLORES["exito"] if v >= 95 else COLORES["fallo"] for v in resultados_oc]
    bars2 = axes[1].bar(x_pos, resultados_oc, color=colores_oc, width=0.5, edgecolor="#555577")
    axes[1].axhline(y=95, color=COLORES["alerta"], linestyle="--", alpha=0.7, label="Umbral éxito (95%)")
    axes[1].set_xticks(x_pos)
    axes[1].set_xticklabels(labels)
    axes[1].set_title("Ataque de Oclusión", **FONT_TITLE)
    axes[1].set_xlabel("Proporción de ataque", **FONT_LABEL)
    axes[1].set_ylabel("Bits correctos (%)", **FONT_LABEL)
    axes[1].set_ylim(0, 105)
    axes[1].grid(axis="y", alpha=0.2, color=COLORES["grid"])
    axes[1].legend(fontsize=10)
    for bar, val in zip(bars2, resultados_oc):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f"{val:.1f}%", ha="center", va="bottom", color=COLORES["texto"], fontsize=10, fontweight="bold")

    fig.suptitle("Análisis de Robustez — Resistencia del Estegoaudio a Ataques",
                 fontsize=16, fontweight="bold", color=COLORES["texto"], y=1.02)
    fig.tight_layout()
    _guardar(fig, "robustez_sal_pimienta_oclusion.png")

    return {"sal_pimienta": dict(zip(labels, resultados_sp)), "oclusion": dict(zip(labels, resultados_oc))}


# ============================================================
# 8. SEGURIDAD DE LA CLAVE (Obs. 8)
# ============================================================

def analisis_seguridad_clave(datos):
    """Análisis del espacio de claves y componentes."""
    print("\n--- Análisis de Seguridad de la Clave")

    long_llave_bytes = len(datos["llave"])
    long_llave_bits = long_llave_bytes * 8

    espacio_x0 = 2**52
    espacio_r = 2**48
    espacio_total = espacio_x0 * espacio_r  # ~2^100

    velocidad = 1e9
    segundos = espacio_total / velocidad
    anios = segundos / (365.25 * 24 * 3600)

    print(f"  Longitud de la llave:     {long_llave_bytes} bytes ({long_llave_bits} bits)")
    print(f"  Espacio de claves:        ~2^100 ({espacio_total:.2e})")
    print(f"  Fuerza bruta a {velocidad:.0e} claves/s: {anios:.2e} anos")

    fig, ax = plt.subplots(figsize=(12, 7), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.axis("off")

    info = (
        "ANALISIS DE SEGURIDAD DE LA CLAVE CRIPTOGRAFICA\n"
        "=" * 50 + "\n\n"
        f"  Estructura de la Clave\n"
        f"  {'_' * 45}\n"
        f"  Tipo:          Secuencia pseudoaleatoria caotica\n"
        f"  Generador:     Mapa Logistico  x(n+1) = r*x(n)*(1 - x(n))\n"
        f"  Longitud:      {long_llave_bytes} bytes ({long_llave_bits} bits)\n\n"
        f"  Componentes (Secretos del Receptor)\n"
        f"  {'_' * 45}\n"
        f"  x0 (punto inicial):       {X0}  (float64, 52 bits mantisa)\n"
        f"  r  (parametro de caos):   {R}  (float64, regimen caotico [3.57, 4])\n"
        f"  n  (calentamiento):       {N_WARMUP} iteraciones (entero fijo)\n\n"
        f"  Espacio de Claves\n"
        f"  {'_' * 45}\n"
        f"  x0 in (0, 1):    ~2^52 valores posibles\n"
        f"  r  in [3.57, 4]:  ~2^48 valores posibles\n"
        f"  Espacio total:   ~2^100 = {espacio_total:.2e} combinaciones\n\n"
        f"  Resistencia a Fuerza Bruta\n"
        f"  {'_' * 45}\n"
        f"  Velocidad supuesta:  10^9 claves/segundo\n"
        f"  Tiempo estimado:     {anios:.2e} anos\n"
        f"  Edad del universo:   ~1.38 x 10^10 anos\n"
        f"  Factor de seguridad: {anios / 1.38e10:.2e}x la edad del universo"
    )
    ax.text(0.05, 0.95, info, transform=ax.transAxes,
            fontsize=11, color=COLORES["texto"], verticalalignment="top",
            fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.8", facecolor="#2a2a4a", edgecolor=COLORES["original"], linewidth=2))

    _guardar(fig, "seguridad_clave.png")

    return {"long_bytes": long_llave_bytes, "espacio_claves": "2^100", "anios_bruta": anios}


# ============================================================
# 9. VISUALIZACIONES — DISTRIBUCIÓN CAÓTICA
# ============================================================

def visualizaciones_mejoradas(datos):
    """Genera gráficas: overlay con posiciones caóticas distribuidas."""
    print("\n--- Visualizaciones Mejoradas")

    orig = datos["audio_original"]
    mod = datos["audio_modificado"]
    posiciones = datos["posiciones"]

    # --- Onda original vs esteganografiado (overlay) ---
    fig, axes = plt.subplots(3, 1, figsize=(16, 10), facecolor="#1a1a2e")
    for ax in axes:
        ax.set_facecolor("#1a1a2e")

    axes[0].plot(orig, color=COLORES["original"], alpha=0.7, linewidth=0.3)
    axes[0].set_title("Audio Original", **FONT_TITLE)
    axes[0].set_ylabel("Amplitud", **FONT_LABEL)
    axes[0].grid(axis="y", alpha=0.1, color=COLORES["grid"])

    axes[1].plot(mod, color=COLORES["modificado"], alpha=0.7, linewidth=0.3)
    axes[1].set_title("Audio Esteganografiado", **FONT_TITLE)
    axes[1].set_ylabel("Amplitud", **FONT_LABEL)
    axes[1].grid(axis="y", alpha=0.1, color=COLORES["grid"])

    # Diferencia (audio completo) — ahora muestra distribución
    diff = np.abs(orig.astype(np.int32) - mod.astype(np.int32))
    axes[2].plot(diff, color=COLORES["alerta"], alpha=0.8, linewidth=0.3)
    axes[2].set_title("Diferencia Absoluta |original - esteganografiado|", **FONT_TITLE)
    axes[2].set_xlabel("Muestra", **FONT_LABEL)
    axes[2].set_ylabel("Delta Amplitud", **FONT_LABEL)
    axes[2].grid(axis="y", alpha=0.1, color=COLORES["grid"])

    n_cambios = np.sum(diff > 0)
    axes[2].text(0.02, 0.85, f"Total cambios LSB: {n_cambios} distribuidos en todo el audio",
                 transform=axes[2].transAxes, fontsize=10, color=COLORES["alerta"],
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="#2a2a4a", edgecolor=COLORES["alerta"], alpha=0.8))

    fig.suptitle("Comparación de Formas de Onda — Distribución Caótica en Audio Completo",
                 fontsize=16, fontweight="bold", color=COLORES["texto"], y=1.02)
    fig.tight_layout()
    _guardar(fig, "onda_original_y_estegano.png")

    # --- Mapa de distribución de posiciones caóticas ---
    fig2, axes2 = plt.subplots(2, 1, figsize=(16, 8), facecolor="#1a1a2e")
    for ax in axes2:
        ax.set_facecolor("#1a1a2e")

    # Scatter de posiciones
    axes2[0].scatter(posiciones, np.ones(len(posiciones)), c=COLORES["acento"],
                     alpha=0.5, s=2, marker="|")
    axes2[0].set_title("Distribución de Posiciones Caóticas en el Audio", **FONT_TITLE)
    axes2[0].set_xlabel("Posición en el audio (muestras)", **FONT_LABEL)
    axes2[0].set_xlim(0, len(orig))
    axes2[0].set_yticks([])
    axes2[0].grid(axis="x", alpha=0.15, color=COLORES["grid"])

    # Histograma de posiciones por segmentos del audio
    n_bins = 50
    axes2[1].hist(posiciones, bins=n_bins, color=COLORES["acento"], alpha=0.85, edgecolor="#1a1a2e")
    axes2[1].set_title(f"Histograma de Posiciones Caóticas ({n_bins} segmentos del audio)", **FONT_TITLE)
    axes2[1].set_xlabel("Posición en el audio", **FONT_LABEL)
    axes2[1].set_ylabel("Cantidad de bits inseridos", **FONT_LABEL)
    axes2[1].set_xlim(0, len(orig))
    axes2[1].grid(axis="y", alpha=0.2, color=COLORES["grid"])

    # Línea de distribución uniforme ideal
    ideal = len(posiciones) / n_bins
    axes2[1].axhline(y=ideal, color=COLORES["alerta"], linestyle="--", alpha=0.7,
                     label=f"Distribución uniforme ideal ({ideal:.1f})")
    axes2[1].legend(fontsize=10)

    fig2.suptitle("Posiciones de Inserción LSB — Generadas por el Mapa Logístico",
                  fontsize=16, fontweight="bold", color=COLORES["texto"], y=1.02)
    fig2.tight_layout()
    _guardar(fig2, "distribucion_posiciones_caoticas.png")

    # --- Zoom a diferencia en una sección del audio ---
    # Tomar una sección del 30-35% del audio donde haya cambios
    seccion_inicio = int(len(orig) * 0.30)
    seccion_fin = int(len(orig) * 0.35)
    diff_zoom = diff[seccion_inicio:seccion_fin]
    x_zoom = np.arange(seccion_inicio, seccion_fin)

    fig3, ax3 = plt.subplots(figsize=(16, 4), facecolor="#1a1a2e")
    ax3.set_facecolor("#1a1a2e")
    ax3.plot(x_zoom, diff_zoom, color=COLORES["alerta"], linewidth=0.5, alpha=0.9)
    n_zoom = np.sum(diff_zoom > 0)
    ax3.set_title(f"Zoom — Diferencia en Muestras [{seccion_inicio:,}:{seccion_fin:,}] — {n_zoom} cambios LSB", **FONT_TITLE)
    ax3.set_xlabel("Muestra", **FONT_LABEL)
    ax3.set_ylabel("Delta Amplitud", **FONT_LABEL)
    ax3.grid(alpha=0.1, color=COLORES["grid"])

    fig3.tight_layout()
    _guardar(fig3, "audio_difference_zoom.png")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("ANALISIS COMPLETO — OBSERVACIONES PROFESORAS")
    print("=" * 60)

    print("\nCargando datos existentes...")
    datos = cargar_datos()

    # Ejecutar todos los análisis
    res_entropia = analisis_entropia(datos)
    res_mse = analisis_mse_covarianza(datos)
    res_npcr = analisis_npcr_uaci(datos)
    analisis_histogramas_texto(datos)
    res_corr = analisis_correlacion_texto(datos)
    res_sens = analisis_sensibilidad_clave(datos)
    res_rob = analisis_robustez(datos)
    res_seg = analisis_seguridad_clave(datos)
    visualizaciones_mejoradas(datos)

    # Resumen final
    print("\n" + "=" * 60)
    print("ANALISIS COMPLETO FINALIZADO")
    print("=" * 60)
    print(f"\nArchivos generados en: {SALIDA}")
    for archivo in sorted(SALIDA.glob("*.png")):
        print(f"  {archivo.name}")

    # Guardar resumen JSON
    resumen = {
        "entropia": res_entropia,
        "mse_covarianza": res_mse,
        "npcr_uaci": res_npcr,
        "correlacion_texto": res_corr,
        "sensibilidad_clave": res_sens,
        "robustez": res_rob,
        "seguridad_clave": res_seg,
    }
    (SALIDA / "analisis_completo.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"  analisis_completo.json")


if __name__ == "__main__":
    main()
