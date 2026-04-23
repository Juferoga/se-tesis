import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.io.wavfile as wav

# Configuración académica limpia
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12, 'axes.titlesize': 14, 'axes.labelsize': 12,
    'xtick.labelsize': 10, 'ytick.labelsize': 10, 'legend.fontsize': 12
})

OUT_DIR = "outputs/entrega_profesoras"
ORIGINAL_WAV = os.path.join(OUT_DIR, "audio_original.wav")
ESTEGANO_WAV = os.path.join(OUT_DIR, "audio_estegano.wav")

def read_wav(path):
    samplerate, data = wav.read(path)
    if len(data.shape) > 1: data = data[:, 0]
    return data, samplerate

orig_data, sr = read_wav(ORIGINAL_WAV)
mod_data, _ = read_wav(ESTEGANO_WAV)

# 1. WAVEFORMS (Limpio)
plt.figure(figsize=(14, 5))
zoom_start = sr * 5
zoom_len = 100
t_zoom = np.arange(zoom_len)

plt.plot(t_zoom, orig_data[zoom_start:zoom_start+zoom_len], marker='o', color='#1f77b4', linestyle='-', linewidth=3, markersize=8, label='Audio Original')
plt.plot(t_zoom, mod_data[zoom_start:zoom_start+zoom_len], marker='x', color='#d62728', linestyle='--', linewidth=2, markersize=8, label='Estegoaudio')

plt.title('Vista Microscópica de la Forma de Onda (100 muestras)')
plt.xlabel('Índice de Muestra Local')
plt.ylabel('Amplitud (PCM 16-bits)')
plt.legend(loc='upper right', frameon=True, facecolor='white')
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "audio_waveforms.png"), dpi=300)
plt.close()

# 2. HISTOGRAMAS (Limpio)
plt.figure(figsize=(16, 6))
subset_orig = orig_data[:1000000]
subset_mod = mod_data[:1000000]

plt.subplot(1, 2, 1)
plt.hist(subset_orig, bins=100, color='#1f77b4', alpha=0.8, label='Audio Original')
plt.hist(subset_mod, bins=100, color='#d62728', alpha=0.4, label='Estegoaudio')
plt.title('Histograma de Amplitudes (Distribución Visual)')
plt.xlabel('Amplitud')
plt.ylabel('Frecuencia')
plt.legend()

plt.subplot(1, 2, 2)
counts_orig, bins = np.histogram(subset_orig, bins=100)
counts_mod, _ = np.histogram(subset_mod, bins=bins)
diff_counts = counts_orig - counts_mod
plt.bar(bins[:-1], diff_counts, width=(bins[1]-bins[0]), color='#ff7f0e', edgecolor='black')
plt.title('Diferencia Matemática de Frecuencias (Original - Estegoaudio)')
plt.xlabel('Amplitud')
plt.ylabel('Diferencia (Cantidad de Muestras)')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "audio_histograms.png"), dpi=300)
plt.close()

# 3. GRAFICA DE DIFERENCIA CAOTICA (Limpio)
diff = np.abs(orig_data.astype(np.int32) - mod_data.astype(np.int32))
plt.figure(figsize=(14, 8))

plt.subplot(2, 1, 1)
window_size = sr // 100 
if len(diff) > window_size:
    num_windows = len(diff) // window_size
    diff_macro = np.max(diff[:num_windows * window_size].reshape(-1, window_size), axis=1)
    t_macro = np.arange(num_windows) * (window_size / sr)
    plt.plot(t_macro, diff_macro, color='gray', alpha=0.8)
    plt.title('Vista Global: Diferencia Absoluta |Original - Estegoaudio|')
    plt.xlabel('Tiempo (segundos)')
    plt.ylabel('Modificación Máxima (Bits)')

plt.subplot(2, 1, 2)
zoom_len = 50 
valid_starts = np.where(diff > 0)[0]
if len(valid_starts) > 0:
    zoom_start = valid_starts[len(valid_starts)//2]
else:
    zoom_start = sr * 2

zoom_diff = diff[zoom_start:zoom_start+zoom_len]
t_zoom = np.arange(zoom_len)

markerline, stemlines, baseline = plt.stem(t_zoom, zoom_diff, basefmt='k-', label='Bit modificado')
plt.setp(stemlines, 'color', '#d62728', 'linewidth', 2)
plt.setp(markerline, 'color', '#d62728', 'markersize', 10, 'marker', 'o')
plt.setp(baseline, 'color', 'black', 'linewidth', 1.5)

plt.title('Vista Microscópica (50 muestras): Ocultamiento Caótico LSB')
plt.xlabel('Índice de Muestras')
plt.ylabel('Cambio de Bit (Magnitud)')
plt.yticks([0, 1])
plt.legend(loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "audio_difference.png"), dpi=300)
plt.close()
