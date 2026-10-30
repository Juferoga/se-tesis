#!/usr/bin/env python3
"""Figuras de la sección 3 del artículo (TecnoLógicas 4098), un panel por archivo.

Reutiliza la carga de datos, los ataques y la extracción de
``scripts.generar_analisis_completo`` para que las figuras coincidan con los
valores de ``analisis_completo.json``.

Uso:
    SALIDA_DIR=outputs/revision_tecnologicas python -m scripts.figuras_articulo
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from scripts import generar_analisis_completo as gac
from src.utils.caos import derivar_semillas, generar_llave
from src.encriptado.encriptar import xor_encriptado
from src.esteganografiado.esteganografiar import insertar_lsb_caotico
from src.esteganografiado.desesteganografiar import extraer_lsb_caotico

DPI = 300
FIG = gac.SALIDA / "figuras_articulo"
FIG.mkdir(parents=True, exist_ok=True)
C_ORIG, C_MOD, C_ALERTA = "#1f77b4", "#ff7f0e", "#d62728"
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11})


def guardar(fig, nombre):
    fig.savefig(FIG / nombre, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  [OK]", nombre)


def main():
    datos = gac.cargar_datos()
    a = datos["audio_original"]
    b = datos["audio_modificado"]
    n_bits = len(datos["mensaje_bits"])
    resumen = {}

    # Figura 2: histogramas de amplitud
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
    for k, (sig, tit, col) in enumerate(((a, "Audio original", C_ORIG), (b, "Estegoaudio", C_MOD))):
        ax[k].hist(sig, bins=200, color=col)
        ax[k].set_title(tit)
        ax[k].set_xlabel("Amplitud (niveles PCM de 16 bits)")
        ax[k].grid(alpha=0.2)
    ax[0].set_ylabel("Frecuencia")
    guardar(fig, "fig2_histogramas.png")

    # Figura 3: error de cuantización
    eps = b.astype(np.int32) - a.astype(np.int32)
    valores, cuentas = np.unique(eps, return_counts=True)
    resumen["eps"] = {int(v): int(c) for v, c in zip(valores, cuentas)}
    fig, ax = plt.subplots(figsize=(7, 4.5))
    barras = ax.bar([str(v) for v in valores], cuentas, color=[C_ALERTA, C_ORIG, "#2ca02c"][: len(valores)], edgecolor="black")
    ax.set_yscale("log")
    ax.set_ylim(1, cuentas.max() * 20)
    for br, c in zip(barras, cuentas):
        ax.text(br.get_x() + br.get_width() / 2, c * 1.4, f"{c:,}".replace(",", " "), ha="center", fontweight="bold")
    ax.set_xlabel("Valor de ε(n) = x(n) − y(n)")
    ax.set_ylabel("Frecuencia (escala logarítmica)")
    ax.grid(alpha=0.2, axis="y")
    guardar(fig, "fig3_error_cuantizacion.png")

    # Figura 4: correlación de muestras adyacentes (canal izquierdo)
    rng = np.random.default_rng(42)
    resumen["rho_lag1"] = {}
    for sig, tit, col, nombre in ((a, "Audio original", C_ORIG, "fig4a_correlacion_original.png"),
                                  (b, "Estegoaudio", C_MOD, "fig4b_correlacion_estego.png")):
        izq = sig.reshape(-1, 2)[:, 0].astype(np.float64)
        rho = float(np.corrcoef(izq[:-1], izq[1:])[0, 1])
        resumen["rho_lag1"][tit] = rho
        idx = rng.choice(len(izq) - 1, 40000, replace=False)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(izq[idx], izq[idx + 1], s=3, alpha=0.3, color=col, edgecolors="none")
        ax.set_title(f"{tit} (canal izquierdo)")
        ax.set_xlabel("Amplitud de la muestra n")
        ax.set_ylabel("Amplitud de la muestra n + 1")
        ax.text(0.04, 0.95, f"ρ = {rho:.4f}", transform=ax.transAxes, va="top",
                bbox={"facecolor": "white", "edgecolor": "#888"})
        ax.grid(alpha=0.2)
        guardar(fig, nombre)

    # Figura 5: 500 tramas del canal de una muestra modificada
    pos = datos["posiciones"]
    p0 = int(pos[np.argmax(eps[pos] != 0)])
    canal, trama = p0 % 2, p0 // 2
    ca, cb = a.reshape(-1, 2)[:, canal], b.reshape(-1, 2)[:, canal]
    ini = max(0, trama - 250)
    x = np.arange(ini, ini + 500)
    fig, ax = plt.subplots(figsize=(13, 3.6))
    ax.plot(x, ca[x], color=C_ORIG, lw=1.8, label="Audio original")
    ax.plot(x, cb[x], color=C_MOD, lw=1.0, ls="--", label="Estegoaudio")
    ax.ticklabel_format(useOffset=False, style="plain", axis="x")
    ax.set_xlabel("Índice de trama (canal " + ("izquierdo" if canal == 0 else "derecho") + ")")
    ax.set_ylabel("Amplitud")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.2)
    guardar(fig, "fig5_similitud_amplitudes.png")
    resumen["fig5_rango_tramas"] = [ini, ini + 500, int(canal)]

    # Figura 7: bits extraídos con clave correcta y perturbada
    dx = 1e-15
    *_, x0p, rp, npp = derivar_semillas(gac.X0, gac.R, gac.N_WARMUP)
    *_, x0q, rq, npq = derivar_semillas(gac.X0 + dx, gac.R, gac.N_WARMUP)
    bits_ok, _ = extraer_lsb_caotico(b, n_bits, x0p, rp, npp)
    bits_mal, _ = extraer_lsb_caotico(b, n_bits, x0q, rq, npq)
    v_ok = np.array([int(c) for c in bits_ok])
    v_mal = np.array([int(c) for c in bits_mal])
    resumen["pct_bits_distintos"] = float((v_ok != v_mal).mean() * 100)
    m = 200
    for vec, nombre, col, lab in ((v_ok, "fig7a_bits_correcta.png", C_ORIG, "Clave correcta"),
                                  (v_mal, "fig7b_bits_perturbada.png", C_MOD, "Clave perturbada"),
                                  (np.abs(v_ok - v_mal), "fig7c_bits_diferencia.png", C_ALERTA, "Diferencia")):
        fig, ax = plt.subplots(figsize=(13, 2.5))
        ax.step(np.arange(m), vec[:m], where="mid", color=col, lw=1.1, label=lab)
        ax.set_ylim(-0.2, 1.3)
        ax.set_yticks([0, 1])
        ax.set_xlabel("Índice de bit")
        ax.set_ylabel("Bit")
        ax.legend(loc="upper right")
        ax.grid(alpha=0.2)
        guardar(fig, nombre)

    # Figura 8: dos estegoaudios con claves que difieren en dx
    # La clave B cambia tanto el flujo de cifrado como las posiciones
    llave_b = generar_llave(gac.X0 + dx, gac.R, gac.N_WARMUP, len(datos["texto_bytes"]))
    cifrado_b = xor_encriptado(datos["texto_bytes"], llave_b)
    bits_b = "".join(np.unpackbits(cifrado_b).astype(str).tolist())
    est_b, _ = insertar_lsb_caotico(a, bits_b, x0q, rq, npq)
    d = b.astype(np.int32) - est_b.astype(np.int32)
    nz = np.nonzero(d)[0]
    resumen["fig8_muestras_distintas"] = int(len(nz))
    fuerte = nz[np.abs(b[nz].astype(np.int32)) > 2000]
    elegido = int(fuerte[0]) if len(fuerte) else int(nz[0])
    canal, trama = elegido % 2, elegido // 2
    ca, cb = b.reshape(-1, 2)[:, canal], est_b.reshape(-1, 2)[:, canal]
    seg = np.arange(trama - 40, trama + 40)
    fig, ax = plt.subplots(figsize=(13, 2.6))
    ax.plot(seg, ca[seg], color=C_ORIG, lw=1.8, label="Estegoaudio A (clave correcta)")
    ax.plot(seg, cb[seg], color=C_MOD, lw=1.0, ls="--", label="Estegoaudio B (x₀ + 10⁻¹⁵)")
    dif = seg[ca[seg] != cb[seg]]
    ax.scatter(dif, ca[dif], s=40, facecolors="none", edgecolors=C_ALERTA, label="Muestras distintas", zorder=3)
    ax.ticklabel_format(useOffset=False, style="plain", axis="x")
    ax.set_xlabel("Índice de trama")
    ax.set_ylabel("Amplitud")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.2)
    guardar(fig, "fig8a_superposicion.png")
    fig, ax = plt.subplots(figsize=(13, 2.6))
    ax.vlines(nz, 0, d[nz], color=C_ALERTA, lw=0.6)
    ax.set_xlim(0, len(d))
    ax.set_xlabel("Índice de muestra")
    ax.set_ylabel("Diferencia A − B")
    ax.grid(alpha=0.2)
    guardar(fig, "fig8b_diferencia.png")
    vv, cc = np.unique(d, return_counts=True)
    resumen["fig8_hist"] = {int(v): int(c) for v, c in zip(vv, cc)}
    fig, ax = plt.subplots(figsize=(13, 2.6))
    ax.bar([str(v) for v in vv], cc, color=C_ORIG, edgecolor="black")
    ax.set_yscale("log")
    for i, c in enumerate(cc):
        ax.text(i, c * 1.3, f"{c:,}".replace(",", " "), ha="center", fontsize=9)
    ax.set_ylim(1, cc.max() * 30)
    ax.set_xlabel("Diferencia A − B")
    ax.set_ylabel("Frecuencia (log)")
    guardar(fig, "fig8c_histograma_diferencia.png")

    # Figuras 9-11: estegoaudio atacado en cada nivel + textos recuperados
    ataques = {
        "fig9_sal_pimienta": [(f"{int(p*100)} %", gac.ataque_sal_y_pimienta(b, p)) for p in (0.05, 0.10, 0.25)],
        "fig10_oclusion": [(f"{int(p*100)} %", gac.ataque_oclusion(b, p)) for p in (0.05, 0.10, 0.25)],
        "fig11_gaussiano": [(f"SNR = {s} dB", gac.ataque_gaussiano(b, s)) for s in (100, 90, 80)],
    }
    ref = datos["texto_comprimido"]
    resumen["ataques"] = {}
    for base, specs in ataques.items():
        for k, (lab, at) in enumerate(specs):
            texto = gac._recuperar_texto_desde_audio(at, datos)
            bits, _ = extraer_lsb_caotico(at, n_bits, x0p, rp, npp)
            ber = float(np.mean(np.array(list(bits)) != np.array(list(datos["mensaje_bits"]))) * 100)
            resumen["ataques"][f"{base}_{k}"] = {
                "nivel": lab, "muestras_afectadas": int(np.sum(at != b)), "ber_pct": ber,
                "similitud_pct": gac._similitud_textual(ref, texto), "texto": texto}
            fig, ax = plt.subplots(figsize=(8, 3))
            xs = np.arange(0, len(b), 25)  # submuestreo solo para graficar
            if base == "fig11_gaussiano":
                # el ruido es del orden de 1 nivel PCM: se grafica la diferencia
                z = np.arange(len(b) // 2, len(b) // 2 + 300)
                dz = at[z].astype(np.int32) - b[z].astype(np.int32)
                ax.vlines(z, 0, dz, color=C_ALERTA, lw=1.2)
                ax.ticklabel_format(useOffset=False, style="plain", axis="x")
                ax.set_ylim(-2.5, 2.5)
                ax.set_ylabel("Atacado − estegoaudio")
            else:
                ax.plot(xs, b[xs], color=C_ORIG, lw=0.4, label="Estegoaudio")
                ax.plot(xs, at[xs], color=C_ALERTA, lw=0.4, alpha=0.6, label="Atacado")
                ax.set_ylabel("Amplitud")
                ax.legend(loc="upper right", fontsize=8)
            ax.set_xlabel("Índice de muestra")
            ax.set_title(lab)
            ax.grid(alpha=0.2)
            guardar(fig, f"{base}_{'abc'[k]}.png")

    (FIG / "resumen_figuras.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in resumen.items() if k != "ataques"}, ensure_ascii=False, indent=1))
    for k, v in resumen["ataques"].items():
        print(k, v["nivel"], v["muestras_afectadas"], round(v["ber_pct"], 2), round(v["similitud_pct"], 2))


if __name__ == "__main__":
    main()
