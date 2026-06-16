#!/usr/bin/env python3
"""Gráficas complementarias para la tesis — VERSIÓN LIMPIA (sin datos sintéticos).

Las figuras 4_histogramas.png, 6_efecto_avalancha.png y 7_vista_microscopica_50.png
fueron ELIMINADAS por contener datos hardcodeados/sintéticos detectados por las
profesoras (observaciones del 5-may y 8-may de 2026).

Las figuras de correlación ahora se generan en 2 archivos independientes:
  - 4_correlacion_audio_original.png
  - 4_correlacion_audio_estego.png

Para regenerar todas las figuras usar:
    python -m scripts.generar_analisis_completo
"""

from pathlib import Path
import scipy.io.wavfile as wav
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def configurar_estilo() -> None:
    plt.rcParams.update({
        "figure.figsize": (10, 5),
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "legend.fontsize": 10,
        "grid.alpha": 0.30,
        "axes.grid": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def guardar_figura(fig: plt.Figure, ruta: Path) -> None:
    fig.tight_layout()
    fig.savefig(ruta, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta.name}")


def generar_4_correlacion_separadas(salida: Path) -> None:
    """Genera DOS figuras independientes de correlación lag-1 (audio real)."""
    raiz = salida.resolve().parent.parent
    ruta_orig = raiz / "data" / "audio_test.wav"
    ruta_esteg = raiz / "data" / "audio_test_modificado.wav"

    if not ruta_orig.exists() or not ruta_esteg.exists():
        print("[WARN] Audios no encontrados. Omitiendo correlación.")
        return

    _, orig = wav.read(str(ruta_orig))
    _, esteg = wav.read(str(ruta_esteg))
    if orig.ndim > 1:
        orig = orig[:, 0]
    if esteg.ndim > 1:
        esteg = esteg[:, 0]

    color_orig = "#1f77b4"
    color_esteg = "#ff7f0e"
    color_ref = "#d62728"

    def _plot_correlacion(arr, label, color, fname):
        x_lag = arr[:-1].astype(np.float64)
        y_lag = arr[1:].astype(np.float64)
        np.random.seed(42)
        idx = np.random.choice(len(x_lag), size=min(40000, len(x_lag)), replace=False)
        xs, ys = x_lag[idx], y_lag[idx]
        r = float(np.corrcoef(xs, ys)[0, 1])

        fig, ax = plt.subplots(figsize=(8, 8), facecolor="white")
        ax.set_facecolor("white")
        ax.scatter(xs, ys, s=4, color=color, alpha=0.3, edgecolors="none",
                   label="Pares de muestras adyacentes")
        lim = max(abs(float(xs.min())), abs(float(xs.max())))
        ax.plot([-lim, lim], [-lim, lim], "--", color=color_ref, linewidth=1,
                alpha=0.7, label="Referencia y=x")
        ax.set_title(f"Correlación de Amplitudes (lag-1) — {label}", fontsize=12,
                     fontweight="bold")
        ax.set_xlabel("Muestra n  (amplitud PCM)")
        ax.set_ylabel("Muestra n+1  (amplitud PCM)")
        ax.text(0.05, 0.95, f"ρ(lag-1) = {r:.10f}", transform=ax.transAxes,
                fontsize=11, va="top",
                bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "#888"})
        ax.legend(fontsize=9)
        ax.grid(alpha=0.2)
        guardar_figura(fig, salida / fname)

    _plot_correlacion(orig,  "Audio Original", color_orig,  "4_correlacion_audio_original.png")
    _plot_correlacion(esteg, "Estegoaudio",    color_esteg, "4_correlacion_audio_estego.png")


def main() -> None:
    configurar_estilo()
    salida = Path(__file__).resolve().parent
    salida.mkdir(parents=True, exist_ok=True)

    print("Generando figuras de correlación de audio (datos reales)...")
    generar_4_correlacion_separadas(salida)
    print(f"Figuras generadas en: {salida}")
    print("\nNOTA: Para el análisis completo usar:")
    print("  python -m scripts.generar_analisis_completo")


if __name__ == "__main__":
    main()
