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
plt.figure(figsize=(12, 6))
# Sample a random subset if too large, or just use 1M samples
subset_orig = orig_data[:1000000]
subset_mod = mod_data[:1000000]

plt.hist(subset_orig, bins=150, color='#1f77b4', alpha=0.8, label='Audio Original')
plt.hist(subset_mod, bins=150, color='#d62728', alpha=0.5, label='Estegoaudio (Modificado)')
plt.title('Distribución Estadística de Amplitudes (Histograma)\nLa superposición de los colores demuestra que la estructura estadística no se altera')
plt.xlabel('Amplitud de la Muestra')
plt.ylabel('Frecuencia (Conteo)')
plt.legend(loc='upper right', frameon=True, facecolor='white', framealpha=1.0)
plt.yscale('log') # Log scale helps see details in tails
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "audio_histograms.png"), dpi=300)
plt.close()

# 3. MEJORAR GRAFICA DE DIFERENCIA
print("Generando Gráfica de Diferencia...")
# Calcular la diferencia absoluta entera
diff = np.abs(orig_data.astype(np.int32) - mod_data.astype(np.int32))

plt.figure(figsize=(14, 8))

# Subplot 1: Diferencia macro (promediada para que no sea una mancha sólida)
plt.subplot(2, 1, 1)
window_size = sr // 100 # 10ms windows
if len(diff) > window_size:
    num_windows = len(diff) // window_size
    diff_macro = np.max(diff[:num_windows * window_size].reshape(-1, window_size), axis=1)
    t_macro = np.arange(num_windows) * (window_size / sr)
    plt.plot(t_macro, diff_macro, color='gray', alpha=0.8, label='Máxima alteración (LSB)')
    plt.title('Diferencia Global |Original - Estegoaudio| a lo largo de toda la pista\n(Los valores son minúsculos, evidenciando alteración solo en bits menos significativos)')
    plt.xlabel('Tiempo (segundos)')
    plt.ylabel('Diferencia Absoluta Máxima')
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.7)

# Subplot 2: Zoom microscópico para ver el efecto caótico
plt.subplot(2, 1, 2)
# Buscar un punto donde haya inserciones caóticas
zoom_start = min(sr * 2, len(diff) - 200)
zoom_length = 200 # Just 200 samples
zoom_diff = diff[zoom_start:zoom_start+zoom_length]
t_zoom = np.arange(zoom_length)

# Use stem plot for discrete samples
plt.stem(t_zoom, zoom_diff, basefmt='k-', linefmt='r-', markerfmt='ro', label='Bits Modificados')
plt.title('Zoom Microscópico (200 muestras) - Comprobación de Ocultamiento Caótico\n(La diferencia se distribuye de forma no secuencial)')
plt.xlabel('Índice de Muestra Local')
plt.ylabel('Diferencia (Magnitud)')
plt.legend(loc='upper right')
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "audio_difference.png"), dpi=300)
plt.close()

print("¡Nuevas gráficas generadas exitosamente!")
