import matplotlib.pyplot as plt
import librosa
import librosa.display
import numpy as np
import os


# Función para crear directorio de gráficas si no existe
def ensure_plots_dir():
    """Asegura que exista el directorio para guardar las gráficas"""
    plots_dir = os.path.join(os.getcwd(), "plots")
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
    return plots_dir


# Función para realizar la gráfica del audio
def plot_audio_waveforms(original_audio, modified_audio, start_sample, end_sample):
    # Tamaño de la figura
    plt.figure(figsize=(15, 6))
    # Separación de figuras
    # Gráfica audio original
    plt.subplot(2, 1, 1)
    plt.title("Original Audio")
    plt.plot(original_audio[start_sample:end_sample])
    plt.xlabel("Sample")
    plt.ylabel("Amplitude")
    # Gráfica audio modificaado
    plt.subplot(2, 1, 2)
    plt.title("Modified Audio")
    plt.plot(modified_audio[start_sample:end_sample])
    plt.xlabel("Sample")
    plt.ylabel("Amplitude")
    # Guardar la gráfica
    plt.tight_layout()
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "audio_waveforms.png"))
    plt.close()
    print("Gráfica de formas de onda guardada en: plots/audio_waveforms.png")


# Función para realizar la gráfica de la señal de audio original y la señal de audio modificada en histogramas
def plot_audio_histograms(original_audio, modified_audio, start_sample, end_sample):
    # Tamaño de la figura
    plt.figure(figsize=(15, 6))
    # Separación de figuras
    # Histograma audio original
    plt.subplot(2, 1, 1)
    plt.title("Original Audio")
    plt.hist(original_audio[start_sample:end_sample], bins=100)
    plt.xlabel("Amplitude")
    plt.ylabel("Frequency")
    # Histograma audio modificado
    plt.subplot(2, 1, 2)
    plt.title("Modified Audio")
    plt.hist(modified_audio[start_sample:end_sample], bins=100)
    plt.xlabel("Amplitude")
    plt.ylabel("Frequency")
    # Guardar la gráfica
    plt.tight_layout()
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "audio_histograms.png"))
    plt.close()
    print("Gráfica de histogramas guardada en: plots/audio_histograms.png")


# función para realizar la gráfica de la señal de audio original y la señal de audio modificada en espectrogramas
def plot_audio_spectrograms(original_audio_path, modified_audio_path):

    # Cargar los archivos de audio
    original_audio, o_sr = librosa.load(original_audio_path)
    modified_audio, m_sr = librosa.load(modified_audio_path)

    spectrogram_org = np.abs(librosa.stft(original_audio))
    spectrogram_mod = np.abs(librosa.stft(modified_audio))

    # Tamaño de la figura
    plt.figure(figsize=(15, 6))
    # Separación de figuras
    # Espectrograma audio original
    plt.subplot(2, 1, 1)
    plt.title("Original Audio")
    librosa.display.specshow(
        librosa.amplitude_to_db(spectrogram_org, ref=np.max),
        sr=o_sr,
        y_axis="log",
        x_axis="time",
    )
    plt.colorbar(format="%+2.0f dB")
    plt.tight_layout()
    # Espectrograma audio modificado
    plt.subplot(2, 1, 2)
    plt.title("Modified Audio")
    librosa.display.specshow(
        librosa.amplitude_to_db(spectrogram_mod, ref=np.max),
        sr=m_sr,
        y_axis="log",
        x_axis="time",
    )
    plt.colorbar(format="%+2.0f dB")
    plt.tight_layout()
    # Guardar la gráfica
    plt.suptitle("Spectrogram of Original and Modified Audio")
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "audio_spectrograms.png"))
    plt.close()
    print("Gráfica de espectrogramas guardada en: plots/audio_spectrograms.png")


# función para mostrar el audio original y modificado en formato de onda con librosa
def plot_audio_waveforms_librosa(original_audio_path, modified_audio_path):

    # Cargar los archivos de audio
    original_audio, o_sr = librosa.load(original_audio_path)
    modified_audio, m_sr = librosa.load(modified_audio_path)

    # Tamaño de la figura
    plt.figure(figsize=(15, 6))
    # Separación de figuras
    # Gráfica audio original
    plt.subplot(2, 1, 1)
    plt.title("Original Audio")
    librosa.display.waveshow(original_audio, sr=o_sr)
    plt.tight_layout()
    # Gráfica audio modificado
    plt.subplot(2, 1, 2)
    plt.title("Modified Audio")
    librosa.display.waveshow(modified_audio, sr=m_sr)
    plt.tight_layout()
    # Guardar la gráfica
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "audio_waveforms_librosa.png"))
    plt.close()
    print(
        "Gráfica de formas de onda con librosa guardada en: plots/audio_waveforms_librosa.png"
    )


# Función para visualizar la diferencia entre el audio original y el modificado
def plot_audio_difference(original_audio, modified_audio, start_sample, end_sample):
    """
    Visualiza la diferencia entre el audio original y el modificado

    Args:
        original_audio (numpy.array): Audio original
        modified_audio (numpy.array): Audio modificado
        start_sample (int): Muestra inicial
        end_sample (int): Muestra final
    """
    difference = np.abs(
        original_audio[start_sample:end_sample]
        - modified_audio[start_sample:end_sample]
    )

    plt.figure(figsize=(15, 5))
    plt.title("Absolute Difference Between Original and Modified Audio")
    plt.plot(difference)
    plt.xlabel("Sample")
    plt.ylabel("Absolute Difference")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "audio_difference.png"))
    plt.close()
    print("Gráfica de diferencia audio guardada en: plots/audio_difference.png")


# Función para visualizar el uso de recursos
def plot_resource_usage(cpu_values, memory_values, timestamps):
    """
    Visualiza el uso de recursos (CPU y memoria) a lo largo del tiempo

    Args:
        cpu_values (list): Lista de valores de uso de CPU
        memory_values (list): Lista de valores de uso de memoria
        timestamps (list): Lista de tiempos de medición
    """
    plt.figure(figsize=(15, 8))

    # Gráfica de uso de CPU
    plt.subplot(2, 1, 1)
    plt.plot(timestamps, cpu_values, marker="o", linestyle="-", color="blue")
    plt.title("CPU Usage Over Time")
    plt.xlabel("Execution Time (s)")
    plt.ylabel("CPU Usage (%)")
    plt.grid(True, alpha=0.3)

    # Gráfica de uso de memoria
    plt.subplot(2, 1, 2)
    plt.plot(timestamps, memory_values, marker="s", linestyle="-", color="green")
    plt.title("Memory Usage Over Time")
    plt.xlabel("Execution Time (s)")
    plt.ylabel("Memory Usage (MB)")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "resource_usage.png"))
    plt.close()
    print("Gráfica de uso de recursos guardada en: plots/resource_usage.png")


def plot_resource_usage_detailed(all_samples, section_markers=None):
    """
    Visualiza el uso de recursos con muestras continuas del ResourceMonitor.
    Muestra CPU, RAM (proceso y sistema) y GPU en gráficas separadas.

    Args:
        all_samples (list): Lista de ResourceSample del monitor
        section_markers (dict, optional): Diccionario {nombre_seccion: timestamp} para marcar secciones
    """
    if not all_samples:
        print("No hay muestras para graficar")
        return

    # Extraer datos de las muestras
    timestamps = [s.timestamp for s in all_samples]
    cpu_system = [s.cpu_percent for s in all_samples]
    cpu_process = [s.cpu_percent_process for s in all_samples]
    mem_process = [s.memory_mb_process for s in all_samples]
    mem_system = [s.memory_mb_system for s in all_samples]

    # GPU (puede ser None)
    gpu_percent = [
        s.gpu_percent if s.gpu_percent is not None else 0 for s in all_samples
    ]
    gpu_memory = [
        s.gpu_memory_mb if s.gpu_memory_mb is not None else 0 for s in all_samples
    ]
    has_gpu = any(s.gpu_percent is not None for s in all_samples)

    # Determinar número de subplots
    n_plots = 4 if has_gpu else 2
    fig_height = 12 if has_gpu else 8

    fig, axes = plt.subplots(n_plots, 1, figsize=(16, fig_height), sharex=True)

    # Colores
    colors = {
        "cpu_system": "#2196F3",  # Azul
        "cpu_process": "#1976D2",  # Azul oscuro
        "mem_process": "#4CAF50",  # Verde
        "mem_system": "#81C784",  # Verde claro
        "gpu": "#FF9800",  # Naranja
        "gpu_mem": "#FFB74D",  # Naranja claro
    }

    # --- CPU ---
    ax_cpu = axes[0]
    ax_cpu.fill_between(
        timestamps,
        cpu_system,
        alpha=0.3,
        color=colors["cpu_system"],
        label="CPU Sistema",
    )
    ax_cpu.plot(timestamps, cpu_system, color=colors["cpu_system"], linewidth=1.5)
    ax_cpu.fill_between(
        timestamps,
        cpu_process,
        alpha=0.5,
        color=colors["cpu_process"],
        label="CPU Proceso",
    )
    ax_cpu.plot(timestamps, cpu_process, color=colors["cpu_process"], linewidth=1.5)
    ax_cpu.set_ylabel("CPU (%)")
    ax_cpu.set_title("Uso de CPU durante la ejecución", fontsize=12, fontweight="bold")
    ax_cpu.legend(loc="upper right")
    ax_cpu.grid(True, alpha=0.3)
    ax_cpu.set_ylim(0, max(max(cpu_system), max(cpu_process)) * 1.1)

    # Añadir estadísticas
    max_cpu = max(cpu_system)
    avg_cpu = sum(cpu_system) / len(cpu_system)
    ax_cpu.axhline(y=max_cpu, color="red", linestyle="--", alpha=0.5, linewidth=1)
    ax_cpu.text(
        timestamps[-1] * 0.02,
        max_cpu * 1.02,
        f"Máx: {max_cpu:.1f}%",
        fontsize=9,
        color="red",
    )

    # --- RAM ---
    ax_mem = axes[1]
    ax_mem.fill_between(
        timestamps,
        mem_system,
        alpha=0.3,
        color=colors["mem_system"],
        label="RAM Sistema",
    )
    ax_mem.plot(timestamps, mem_system, color=colors["mem_system"], linewidth=1.5)
    ax_mem.fill_between(
        timestamps,
        mem_process,
        alpha=0.5,
        color=colors["mem_process"],
        label="RAM Proceso",
    )
    ax_mem.plot(timestamps, mem_process, color=colors["mem_process"], linewidth=1.5)
    ax_mem.set_ylabel("Memoria (MB)")
    ax_mem.set_title(
        "Uso de Memoria RAM durante la ejecución", fontsize=12, fontweight="bold"
    )
    ax_mem.legend(loc="upper right")
    ax_mem.grid(True, alpha=0.3)

    # Añadir estadísticas
    max_mem = max(mem_system)
    ax_mem.axhline(y=max_mem, color="red", linestyle="--", alpha=0.5, linewidth=1)
    ax_mem.text(
        timestamps[-1] * 0.02,
        max_mem * 1.01,
        f"Máx: {max_mem / 1024:.2f} GB",
        fontsize=9,
        color="red",
    )

    if has_gpu:
        # --- GPU Utilization ---
        ax_gpu = axes[2]
        ax_gpu.fill_between(timestamps, gpu_percent, alpha=0.4, color=colors["gpu"])
        ax_gpu.plot(
            timestamps,
            gpu_percent,
            color=colors["gpu"],
            linewidth=1.5,
            label="GPU Utilización",
        )
        ax_gpu.set_ylabel("GPU (%)")
        ax_gpu.set_title(
            "Uso de GPU durante la ejecución", fontsize=12, fontweight="bold"
        )
        ax_gpu.legend(loc="upper right")
        ax_gpu.grid(True, alpha=0.3)
        ax_gpu.set_ylim(0, 105)

        max_gpu = max(gpu_percent)
        ax_gpu.axhline(y=max_gpu, color="red", linestyle="--", alpha=0.5, linewidth=1)
        ax_gpu.text(
            timestamps[-1] * 0.02,
            max_gpu + 2,
            f"Máx: {max_gpu:.1f}%",
            fontsize=9,
            color="red",
        )

        # --- GPU Memory ---
        ax_gpu_mem = axes[3]
        ax_gpu_mem.fill_between(
            timestamps, gpu_memory, alpha=0.4, color=colors["gpu_mem"]
        )
        ax_gpu_mem.plot(
            timestamps, gpu_memory, color=colors["gpu_mem"], linewidth=1.5, label="VRAM"
        )
        ax_gpu_mem.set_ylabel("VRAM (MB)")
        ax_gpu_mem.set_xlabel("Tiempo de ejecución (s)")
        ax_gpu_mem.set_title(
            "Uso de VRAM durante la ejecución", fontsize=12, fontweight="bold"
        )
        ax_gpu_mem.legend(loc="upper right")
        ax_gpu_mem.grid(True, alpha=0.3)

        max_vram = max(gpu_memory)
        ax_gpu_mem.axhline(
            y=max_vram, color="red", linestyle="--", alpha=0.5, linewidth=1
        )
        ax_gpu_mem.text(
            timestamps[-1] * 0.02,
            max_vram * 1.01,
            f"Máx: {max_vram / 1024:.2f} GB",
            fontsize=9,
            color="red",
        )
    else:
        axes[-1].set_xlabel("Tiempo de ejecución (s)")

        # Añadir marcadores de secciones si se proporcionan
        has_section_markers = bool(section_markers)
        if has_section_markers:
            sorted_markers = sorted(section_markers.items(), key=lambda item: item[1])

            # Dibujar líneas verticales de referencia en todos los subplots.
            for _, ts in sorted_markers:
                for ax in axes:
                    ax.axvline(x=ts, color="gray", linestyle=":", alpha=0.7)

            # Colocar etiquetas completas fuera del área del gráfico para evitar solapamiento.
            ax_labels = axes[0]
            n_markers = len(sorted_markers)
            for idx, (name, ts) in enumerate(sorted_markers):
                y_frac = 0.9 if n_markers == 1 else 0.92 - idx * (0.8 / (n_markers - 1))
                ax_labels.annotate(
                    name,
                    xy=(ts, 0.97),
                    xycoords=("data", "axes fraction"),
                    xytext=(1.02, y_frac),
                    textcoords="axes fraction",
                    ha="left",
                    va="center",
                    fontsize=8,
                    bbox={"facecolor": "white", "edgecolor": "lightgray", "alpha": 0.85},
                    arrowprops={"arrowstyle": "-", "color": "gray", "lw": 0.8},
                    annotation_clip=False,
                )

        if has_section_markers:
            plt.tight_layout(rect=[0, 0, 0.82, 1])
        else:
            plt.tight_layout()

    plt.tight_layout()
    plots_dir = ensure_plots_dir()
    filepath = os.path.join(plots_dir, "resource_usage_detailed.png")
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Gráfica detallada de recursos guardada en: {filepath}")


# Función para visualizar tiempos de ejecución por sección
def plot_execution_times(section_names, execution_times):
    """
    Visualiza los tiempos de ejecución de diferentes secciones del algoritmo

    Args:
        section_names (list): Lista con nombres de las secciones
        execution_times (list): Lista con los tiempos de ejecución
    """
    plt.figure(figsize=(12, 6))

    # Crear gráfico de barras horizontales
    y_pos = np.arange(len(section_names))
    bars = plt.barh(y_pos, execution_times, align="center", alpha=0.7, color="skyblue")
    plt.yticks(y_pos, section_names)

    # Añadir etiquetas y título
    plt.xlabel("Execution Time (s)")
    plt.title("Execution Time by Algorithm Section")

    # Añadir los valores en las barras
    for i, bar in enumerate(bars):
        plt.text(
            bar.get_width() + 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{execution_times[i]:.4f}s",
            va="center",
        )

    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "execution_times.png"))
    plt.close()
    print("Gráfica de tiempos de ejecución guardada en: plots/execution_times.png")


# Función para visualizar distribución espectral de frecuencias
def plot_frequency_distribution(original_audio, modified_audio, sample_rate):
    """
    Visualiza la distribución espectral de frecuencias del audio original y modificado

    Args:
        original_audio (numpy.array): Audio original
        modified_audio (numpy.array): Audio modificado
        sample_rate (int): Tasa de muestreo del audio
    """
    # Calcular FFT y magnitudes
    fft_original = np.fft.rfft(original_audio)
    fft_modified = np.fft.rfft(modified_audio)

    magnitude_original = np.abs(fft_original)
    magnitude_modified = np.abs(fft_modified)

    # Crear vector de frecuencias
    freqs = np.fft.rfftfreq(len(original_audio), 1 / sample_rate)

    # Graficar
    plt.figure(figsize=(15, 10))

    # Magnitud de Frecuencia - Original
    plt.subplot(2, 1, 1)
    plt.plot(freqs, magnitude_original, alpha=0.8)
    plt.title("Original Audio - Frequency Spectrum")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    plt.xlim([0, sample_rate / 2])  # Mitad del sample rate (Nyquist)
    plt.grid(alpha=0.3)

    # Magnitud de Frecuencia - Modificado
    plt.subplot(2, 1, 2)
    plt.plot(freqs, magnitude_modified, alpha=0.8, color="orange")
    plt.title("Modified Audio - Frequency Spectrum")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    plt.xlim([0, sample_rate / 2])
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "frequency_distribution.png"))
    plt.close()
    print(
        "Gráfica de distribución espectral guardada en: plots/frequency_distribution.png"
    )

    # Graficar diferencia espectral
    plt.figure(figsize=(12, 6))
    plt.plot(freqs, np.abs(magnitude_original - magnitude_modified), color="red")
    plt.title("Spectral Difference Between Original and Modified Audio")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude Difference")
    plt.xlim([0, sample_rate / 2])
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "spectral_difference.png"))
    plt.close()
    print("Gráfica de diferencia espectral guardada en: plots/spectral_difference.png")


# Función para visualizar los resultados de los ataques
def plot_attack_results(results_dict):
    """
    Visualiza los resultados de los ataques en un gráfico

    Args:
        results_dict (dict): Diccionario con los resultados de los ataques
    """
    # Extraer los nombres de los ataques y los porcentajes de bits correctos
    attack_names = []
    percentages = []
    success_status = []

    for attack_name, result in results_dict.items():
        attack_names.append(attack_name)
        percentages.append(result["porcentaje"])
        success_status.append(result["exito"])

    # Ordenar por porcentaje
    sorted_indices = np.argsort(percentages)
    attack_names = [attack_names[i] for i in sorted_indices]
    percentages = [percentages[i] for i in sorted_indices]
    colors = [
        "green" if success else "red"
        for success in [success_status[i] for i in sorted_indices]
    ]

    plt.figure(figsize=(12, 8))
    bars = plt.barh(
        attack_names,
        percentages,
        color=[
            ("green" if s else "red")
            for s in [success_status[i] for i in sorted_indices]
        ],
    )
    plt.xlabel("Porcentaje de bits correctos (%)")
    plt.title("Resistencia a Ataques")
    plt.axvline(x=95, color="black", linestyle="--", label="Umbral de éxito (95%)")
    plt.legend()
    plt.grid(axis="x", alpha=0.3)

    # Añadir los valores en las barras
    for i, bar in enumerate(bars):
        plt.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{percentages[i]:.1f}%",
            va="center",
        )

    plt.tight_layout()
    plots_dir = ensure_plots_dir()
    plt.savefig(os.path.join(plots_dir, "attack_results.png"))
    plt.close()
    print("Gráfica de resultados de ataques guardada en: plots/attack_results.png")


# Función para visualizar los espectrogramas de diferentes ataques
def plot_attack_spectrograms(original_audio, attacked_audios_dict, sample_rate):
    """
    Visualiza los espectrogramas de los diferentes ataques en comparación con el original

    Args:
        original_audio (numpy.array): Audio original
        attacked_audios_dict (dict): Diccionario con los audios atacados {nombre_ataque: audio_array}
        sample_rate (int): Tasa de muestreo del audio
    """
    # Seleccionar los primeros 5 ataques para no saturar la visualización
    max_attacks = min(5, len(attacked_audios_dict))
    selected_attacks = list(attacked_audios_dict.items())[:max_attacks]

    # Limitar la duración del audio para evitar errores de memoria
    max_duration_seconds = 10  # Limitar a 10 segundos
    max_samples = max_duration_seconds * sample_rate

    # Recortar el audio original si es demasiado largo
    if len(original_audio) > max_samples:
        print(
            f"Audio original demasiado largo, limitando a {max_duration_seconds} segundos para visualización"
        )
        original_audio_segment = original_audio[:max_samples]
    else:
        original_audio_segment = original_audio

    # Convertir a float de forma segura para evitar desbordamiento de memoria
    if original_audio_segment.dtype != np.float32:
        original_audio_segment = original_audio_segment.astype(np.float32) / 32768.0

    # Parámetros STFT para reducir el tamaño
    n_fft = 1024  # Tamaño más pequeño de ventana FFT
    hop_length = n_fft // 4  # 75% de solapamiento

    try:
        plt.figure(figsize=(15, 10))

        # Espectrograma del audio original
        plt.subplot(max_attacks + 1, 1, 1)
        plt.title("Original Audio")
        spectrogram_orig = np.abs(
            librosa.stft(original_audio_segment, n_fft=n_fft, hop_length=hop_length)
        )
        librosa.display.specshow(
            librosa.amplitude_to_db(spectrogram_orig, ref=np.max),
            sr=sample_rate,
            y_axis="log",
            x_axis="time",
            hop_length=hop_length,
            n_fft=n_fft,
        )
        plt.colorbar(format="%+2.0f dB", pad=0.01, fraction=0.05)

        # Espectrogramas de los audios atacados
        for i, (attack_name, audio) in enumerate(selected_attacks, 2):
            # Recortar el audio atacado si es demasiado largo
            if len(audio) > max_samples:
                audio = audio[:max_samples]

            # Asegurarse de que el audio esté en formato float
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32) / 32768.0

            plt.subplot(max_attacks + 1, 1, i)
            plt.title(f"Attack: {attack_name}")

            try:
                spectrogram = np.abs(
                    librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
                )
                librosa.display.specshow(
                    librosa.amplitude_to_db(spectrogram, ref=np.max),
                    sr=sample_rate,
                    y_axis="log",
                    x_axis="time",
                    hop_length=hop_length,
                    n_fft=n_fft,
                )
                plt.colorbar(format="%+2.0f dB", pad=0.01, fraction=0.05)
            except Exception as e:
                print(f"Error generando espectrograma para {attack_name}: {str(e)}")
                plt.text(
                    0.5,
                    0.5,
                    f"No se pudo generar el espectrograma: {str(e)}",
                    horizontalalignment="center",
                    verticalalignment="center",
                )

        plt.tight_layout()
        plots_dir = ensure_plots_dir()
        plt.savefig(os.path.join(plots_dir, "attack_spectrograms.png"))
        plt.close()
        print(
            "Gráfica de espectrogramas de ataques guardada en: plots/attack_spectrograms.png"
        )

    except Exception as e:
        print(f"Error al generar los espectrogramas: {str(e)}")
        print(
            "Se omite la generación de espectrogramas para evitar problemas de memoria"
        )
