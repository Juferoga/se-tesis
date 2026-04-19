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
    color_oscuro = "#5f5f5f"
    color_medio = "#8c8c8c"
    axes[0].bar(bins, irregular, color=color_oscuro, edgecolor="#3a3a3a", linewidth=0.4)
    axes[0].set_title("texto comprimido", loc="left")
    axes[0].set_xlabel("Símbolo/byte")
    axes[0].set_ylabel("Frecuencia")

    # Distribución prácticamente uniforme (texto encriptado)
    uniforme = np.full_like(bins, 10, dtype=float)
    axes[1].bar(bins, uniforme, color=color_medio, edgecolor="#4a4a4a", linewidth=0.4)
    axes[1].set_title("Representación uniforme (plana)")
    axes[1].set_xlabel("Símbolo/byte")
    axes[1].set_ylabel("Frecuencia")

    guardar_figura(fig, salida / "4_histogramas.png")


def generar_4_correlacion(salida: Path) -> None:
    x = np.linspace(-1.0, 1.0, 240)
    y = x.copy()  # correlación perfecta
    r = np.corrcoef(x, y)[0, 1]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    color_puntos = "#666666"
    color_linea = "#404040"
    ax.scatter(x, y, s=20, color=color_puntos, alpha=0.9, label="Pares de muestras")
    ax.plot(
        x,
        x,
        color=color_linea,
        linewidth=1.3,
        linestyle="--",
        label="Línea ideal y = x",
    )
    ax.set_title("Correlación de Pearson: Audio Original vs Estegoaudio")
    ax.set_xlabel("Audio Original")
    ax.set_ylabel("Estegoaudio")
    ax.text(
        -0.95,
        0.8,
        f"r = {r:.4f}",
        fontsize=11,
        bbox={"facecolor": "white", "alpha": 0.8},
    )
    ax.legend(loc="lower right")

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
    ax.plot(iteraciones, x1, linewidth=1.8, color="#4d4d4d", label="Serie A")
    ax.plot(iteraciones, x2, linewidth=1.3, color="#8f8f8f", label="Serie B")
    ax.axvspan(15, 20, color="#bdbdbd", alpha=0.20, label="Zona de divergencia")
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
    ax.plot(muestras, original, color="#4f4f4f", linewidth=1.8, label="Señal original")
    ax.plot(
        idx_insertados,
        modificada[idx_insertados],
        "*",
        color="#9c9c9c",
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
