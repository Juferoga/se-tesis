#!/usr/bin/env python3
"""Genera gráficas formales para secciones 4 a 7 de tesis."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def configurar_estilo() -> None:
    plt.rcParams.update(
        {
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
        }
    )


def guardar_figura(fig: plt.Figure, ruta: Path) -> None:
    fig.tight_layout()
    fig.savefig(ruta, dpi=300, bbox_inches="tight")
    plt.close(fig)


def generar_4_histogramas(salida: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # Distribución irregular (texto comprimido)
    bins = np.arange(1, 33)
    irregular = np.array(
        [
            4,
            8,
            3,
            12,
            7,
            16,
            5,
            10,
            6,
            18,
            9,
            4,
            15,
            3,
            11,
            6,
            13,
            5,
            17,
            8,
            7,
            14,
            5,
            9,
            6,
            12,
            4,
            10,
            5,
            15,
            7,
            11,
        ]
    )
    color_oscuro = "#1f77b4"
    color_medio = "#ff7f0e"
    axes[0].bar(bins, irregular, color=color_oscuro, edgecolor="#3a3a3a", linewidth=0.4)
    axes[0].set_title("texto comprimido", loc="left")
    axes[0].set_xlabel("Símbolo/byte")
    axes[0].set_ylabel("Frecuencia")

    # Distribución prácticamente uniforme (texto encriptado)
    uniforme = np.full_like(bins, 10, dtype=float)
    axes[1].bar(bins, uniforme, color=color_medio, edgecolor="#4a4a4a", linewidth=0.4)
    axes[1].set_title("Texto encriptado")
    axes[1].set_xlabel("Símbolo/byte")
    axes[1].set_ylabel("Frecuencia")

    fig.suptitle(
        "Histogramas del texto comprimido y encriptado",
        fontsize=14,
        fontweight="bold",
        y=1.03,
    )

    guardar_figura(fig, salida / "4_histogramas.png")


def generar_4_correlacion(salida: Path) -> None:
    import scipy.io.wavfile as wav

    # Cargar audios reales del proyecto
    raiz = salida.resolve().parent.parent
    ruta_orig = raiz / "data" / "audio_test.wav"
    ruta_esteg = raiz / "data" / "audio_test_modificado.wav"

    if not ruta_orig.exists() or not ruta_esteg.exists():
        print(f"[WARN] Audios no encontrados en {ruta_orig} / {ruta_esteg}")
        print("[WARN] Generando 4_correlacion.png con datos sintéticos.")
        x = np.linspace(-1.0, 1.0, 240)
        y = x.copy()
        r = 1.0
    else:
        _, orig = wav.read(str(ruta_orig))
        _, esteg = wav.read(str(ruta_esteg))
        if orig.ndim > 1:
            orig = orig[:, 0]
        if esteg.ndim > 1:
            esteg = esteg[:, 0]
        n = min(len(orig), len(esteg))
        orig = orig[:n].astype(np.float64)
        esteg = esteg[:n].astype(np.float64)
        # Submuestreo aleatorio para visualización (50 000 puntos)
        np.random.seed(42)
        idx = np.random.choice(n, size=min(50000, n), replace=False)
        x = orig[idx]
        y = esteg[idx]
        r = np.corrcoef(orig, esteg)[0, 1]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    color_puntos = "#2ca02c"
    color_linea = "#d62728"

    # Panel 1: vista global
    ax = axes[0]
    ax.scatter(x, y, s=8, color=color_puntos, alpha=0.4, edgecolors="none", label="Pares de muestras")
    # Línea ideal y=x (escala real del audio)
    lim_min = min(x.min(), y.min())
    lim_max = max(x.max(), y.max())
    ax.plot(
        [lim_min, lim_max],
        [lim_min, lim_max],
        color=color_linea,
        linewidth=1.3,
        linestyle="--",
        label="Línea ideal y = x",
    )
    ax.set_title("Correlación global — Audio Original vs Estegoaudio")
    ax.set_xlabel("Amplitud audio original")
    ax.set_ylabel("Amplitud estegoaudio")
    ax.text(
        0.05,
        0.95,
        f"Pearson r = {r:.10f}",
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "#888888"},
    )
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)

    # Panel 2: zoom microscópico donde se ve la dispersión de ±1
    ax2 = axes[1]
    # Seleccionar solo puntos dentro de un rango pequeño para ver la nube
    mask = (x > -2000) & (x < 2000) & (y > -2000) & (y < 2000)
    if mask.sum() > 100:
        xz = x[mask][:5000]
        yz = y[mask][:5000]
    else:
        xz = x[:5000]
        yz = y[:5000]
    ax2.scatter(xz, yz, s=15, color=color_puntos, alpha=0.5, edgecolors="none")
    ax2.plot([-10, 10], [-10, 10], color=color_linea, linewidth=1.3, linestyle="--")
    ax2.set_xlim(-10, 10)
    ax2.set_ylim(-10, 10)
    ax2.set_title("Zoom microscópico — Dispersión de ±1 nivel LSB")
    ax2.set_xlabel("Amplitud audio original")
    ax2.set_ylabel("Amplitud estegoaudio")
    ax2.text(
        0.05,
        0.95,
        "La nube de puntos se desvía ±1\\nunidad de cuantización",
        transform=ax2.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox={"facecolor": "#fff8dc", "alpha": 0.95, "edgecolor": "#d62728"},
    )
    ax2.grid(alpha=0.3)

    fig.suptitle(
        "Correlación de Pearson — Transparencia acústica del esquema LSB",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    guardar_figura(fig, salida / "4_correlacion.png")


def generar_6_efecto_avalancha(salida: Path) -> None:
    n = 80
    r = 3.99
    x1 = np.zeros(n)
    x2 = np.zeros(n)
    x1[0] = 0.412345678901
    x2[0] = 0.412345678902  # perturbación mínima en condición inicial

    for i in range(1, n):
        x1[i] = r * x1[i - 1] * (1 - x1[i - 1])
        x2[i] = r * x2[i - 1] * (1 - x2[i - 1])

    iteraciones = np.arange(n)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(iteraciones, x1, linewidth=1.8, color="#1f77b4", label="Serie A")
    ax.plot(iteraciones, x2, linewidth=1.3, color="#ff7f0e", label="Serie B")
    ax.axvspan(15, 20, color="#2ca02c", alpha=0.15, label="Zona de divergencia")
    ax.set_title("Efecto avalancha: sensibilidad a condiciones iniciales")
    ax.set_xlabel("Iteración")
    ax.set_ylabel("Estado normalizado")
    ax.legend(loc="upper right")

    guardar_figura(fig, salida / "6_efecto_avalancha.png")


def generar_7_vista_microscopica_50(salida: Path) -> None:
    n = 50
    muestras = np.arange(n)
    original = 0.58 * np.sin(2 * np.pi * muestras / 18.0) + 0.1 * np.cos(
        2 * np.pi * muestras / 7.0
    )

    # Posiciones estocásticas de inserción con huecos prolongados entre alteraciones
    idx_insertados = np.array([2, 3, 11, 24, 25, 40, 47])
    modificada = original.copy()
    deltas = np.array([0.03, -0.02, 0.025, -0.03, 0.02, -0.025, 0.03])
    modificada[idx_insertados] += deltas

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(muestras, original, color="#1f77b4", linewidth=1.8, label="Señal original")
    ax.plot(
        idx_insertados,
        modificada[idx_insertados],
        "*",
        color="#d62728",
        markersize=11,
        label="Puntos de inyección estocástica",
    )
    ax.set_title("Vista microscópica (50 muestras): alteraciones dispersas")
    ax.set_xlabel("Índice de muestra")
    ax.set_ylabel("Amplitud")
    ax.legend(loc="upper right")

    guardar_figura(fig, salida / "7_vista_microscopica_50.png")


def main() -> None:
    configurar_estilo()
    salida = Path(__file__).resolve().parent
    salida.mkdir(parents=True, exist_ok=True)

    generar_4_histogramas(salida)
    generar_4_correlacion(salida)
    generar_6_efecto_avalancha(salida)
    generar_7_vista_microscopica_50(salida)

    print(f"Gráficas generadas en: {salida}")


if __name__ == "__main__":
    main()
