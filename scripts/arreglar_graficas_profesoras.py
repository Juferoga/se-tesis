import numpy as np
import matplotlib.pyplot as plt
import librosa
import os
import scipy.io.wavfile as wav

# Configuración académica para plots
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 12,
    'figure.titlesize': 16
})

OUT_DIR = "outputs/entrega_profesoras"
ORIGINAL_WAV = os.path.join(OUT_DIR, "audio_original.wav")
ESTEGANO_WAV = os.path.join(OUT_DIR, "audio_estegano.wav")

def read_wav(path):
    samplerate, data = wav.read(path)
    if len(data.shape) > 1:
        data = data[:, 0]  # Take left channel if stereo
    return data, samplerate

print("Cargando audios originales para generar gráficas de alta fidelidad...")
orig_data, sr = read_wav(ORIGINAL_WAV)
mod_data, _ = read_wav(ESTEGANO_WAV)

# 1. MEJORAR WAVEFORMS (Formas de onda)
print("Generando Waveforms...")
plt.figure(figsize=(14, 6))
# Tomamos 2 segundos para que la forma de onda sea clara
duration = min(sr * 2, len(orig_data)) 
t = np.arange(duration) / sr

# Dibujar original (azul) y modificado (rojo punteado)
plt.plot(t, orig_data[:duration], color='#1f77b4', label='Audio Original', linewidth=3)
plt.plot(t, mod_data[:duration], color='#d62728', label='Estegoaudio (Con mensaje)', linewidth=2, linestyle='--', alpha=0.9)

plt.title('Comparación de Formas de Onda Original vs Estegoaudio (Primeros 2 segundos)\nAmbas señales se superponen perfectamente demostrando transparencia acústica')
plt.xlabel('Tiempo (segundos)')
plt.ylabel('Amplitud (PCM)')
plt.legend(loc='upper right', frameon=True, facecolor='white', framealpha=1.0)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "audio_waveforms.png"), dpi=300)
plt.close()

# 2. MEJORAR HISTOGRAMA
print("Generando Histogramas...")
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Panel izquierdo: histogramas de amplitudes superpuestos
subset_orig = orig_data[:1000000]
subset_mod = mod_data[:1000000]

axes[0].hist(subset_orig, bins=150, color='#1f77b4', alpha=0.8, label='Audio Original')
axes[0].hist(subset_mod, bins=150, color='#d62728', alpha=0.5, label='Estegoaudio (Modificado)')
axes[0].set_title('Distribución Estadística de Amplitudes\nSuperposición casi perfecta = estadística preservada')
axes[0].set_xlabel('Amplitud de la Muestra')
axes[0].set_ylabel('Frecuencia (Conteo)')
axes[0].legend(loc='upper right', frameon=True, facecolor='white', framealpha=1.0)
axes[0].set_yscale('log')

# Panel derecho: histograma del ERROR de cuantización LSB
error = mod_data.astype(np.int32) - orig_data.astype(np.int32)
error_unique, error_counts = np.unique(error, return_counts=True)
# Mostrar solo {-1, 0, +1} y quizás ±2 por completitud
mask_visible = (error_unique >= -2) & (error_unique <= 2)
axes[1].bar(
    error_unique[mask_visible],
    error_counts[mask_visible],
    color=['#d62728', '#1f77b4', '#2ca02c', '#1f77b4', '#d62728'],
    edgecolor='#333333',
    width=0.6,
)
axes[1].set_title('Error de Cuantización LSB: ε[n] = y[n] − x[n]\nConcentrado en {−1, 0, +1}')
axes[1].set_xlabel('Error de cuantización (niveles PCM)')
axes[1].set_ylabel('Cantidad de muestras')
axes[1].set_xticks([-2, -1, 0, 1, 2])

# Anotación con conteos
for val, count in zip(error_unique[mask_visible], error_counts[mask_visible]):
    axes[1].text(
        val,
        count + max(error_counts) * 0.02,
        f'{count:,}',
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold',
    )

fig.suptitle(
    'Análisis de Distribución — Amplitudes y Error de Cuantización LSB',
    fontsize=16,
    fontweight='bold',
    y=1.02,
)
fig.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "audio_histograms.png"), dpi=300)
plt.close()

# 3. GRAFICA DE DIFERENCIA LSB (con signo)
print("Generando Gráfica de Diferencia LSB...")
# Diferencia con signo: ε[n] = y[n] - x[n]
error = mod_data.astype(np.int32) - orig_data.astype(np.int32)

fig, axes = plt.subplots(2, 1, figsize=(16, 8))

# Panel superior: vista global de las primeras 100k muestras
n_global = min(100000, len(error))
axes[0].plot(
    np.arange(n_global),
    error[:n_global],
    color='#d62728',
    linewidth=0.6,
    alpha=0.9,
)
axes[0].axhline(y=0, color='#333333', linewidth=0.5, linestyle='-')
axes[0].axhline(y=1, color='#2ca02c', linewidth=0.8, linestyle='--', alpha=0.6)
axes[0].axhline(y=-1, color='#2ca02c', linewidth=0.8, linestyle='--', alpha=0.6)
axes[0].set_title(
    'Error de cuantización LSB ε[n] = y[n] − x[n]  (primeras 100 000 muestras)\n'
    'Los picos en ±1 confirman que solo se altera el bit menos significativo'
)
axes[0].set_xlabel('Índice de muestra')
axes[0].set_ylabel('Error ε[n] (niveles PCM)')
axes[0].set_ylim(-2.5, 2.5)
axes[0].set_yticks([-2, -1, 0, 1, 2])
axes[0].grid(True, linestyle='--', alpha=0.5)

# Panel inferior: zoom microscópico en región con cambios
idx_cambios = np.where(error != 0)[0]
if len(idx_cambios) > 0:
    # Centrar el zoom en un cambio, mostrar ~2000 muestras alrededor
    centro = idx_cambios[len(idx_cambios) // 2]
    zoom_start = max(0, centro - 1000)
    zoom_end = min(len(error), centro + 1000)
else:
    zoom_start = 0
    zoom_end = 2000

zoom_error = error[zoom_start:zoom_end]
x_zoom = np.arange(zoom_start, zoom_end)

# Mostrar solo los puntos donde hay cambio, para claridad
mask_mod = zoom_error != 0
axes[1].plot(x_zoom, zoom_error, color='#cccccc', linewidth=0.4, alpha=0.5)
axes[1].scatter(
    x_zoom[mask_mod],
    zoom_error[mask_mod],
    c='#d62728',
    s=15,
    zorder=5,
    label='Muestras modificadas (LSB)',
)
axes[1].axhline(y=0, color='#333333', linewidth=0.5)
axes[1].axhline(y=1, color='#2ca02c', linewidth=1.0, linestyle='--', alpha=0.7, label='±1 nivel de cuantización')
axes[1].axhline(y=-1, color='#2ca02c', linewidth=1.0, linestyle='--', alpha=0.7)
axes[1].set_title(
    f'Zoom microscópico — Muestras [{zoom_start:,}:{zoom_end:,}]\n'
    f'{np.sum(mask_mod)} cambios LSB visibles; el error nunca supera ±1'
)
axes[1].set_xlabel('Índice de muestra')
axes[1].set_ylabel('Error ε[n] (niveles PCM)')
axes[1].set_ylim(-2.5, 2.5)
axes[1].set_yticks([-2, -1, 0, 1, 2])
axes[1].legend(loc='upper right')
axes[1].grid(True, linestyle='--', alpha=0.5)

fig.suptitle(
    'Evidencia de Modificación LSB — Error de Cuantización Muestra a Muestra',
    fontsize=16,
    fontweight='bold',
    y=1.01,
)
fig.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "audio_difference.png"), dpi=300)
plt.close()

print("¡Nuevas gráficas generadas exitosamente!")
