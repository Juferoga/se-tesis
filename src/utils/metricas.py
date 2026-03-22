import numpy as np
from scipy.stats import chisquare, ks_2samp, mannwhitneyu
from math import log, e
import psutil
import time
import os
import threading
from dataclasses import dataclass, field
from typing import List, Optional
from contextlib import contextmanager

# Intentar importar pynvml para monitoreo de GPU
try:
    import pynvml

    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    print("⚠️  pynvml no disponible. Instalar con: pip install pynvml")


@dataclass
class ResourceSample:
    """Muestra de recursos en un momento dado."""

    timestamp: float
    cpu_percent: float  # CPU del sistema (todos los cores)
    cpu_percent_process: float  # CPU del proceso Python
    memory_mb_process: float  # RAM del proceso Python (RSS)
    memory_mb_system: float  # RAM total usada del sistema
    memory_percent_system: float  # % RAM del sistema
    gpu_percent: Optional[float] = None  # Utilización GPU
    gpu_memory_mb: Optional[float] = None  # VRAM usada
    gpu_memory_total_mb: Optional[float] = None  # VRAM total
    gpu_temperature: Optional[float] = None  # Temperatura GPU


@dataclass
class ResourceStats:
    """Estadísticas agregadas de recursos."""

    # CPU
    cpu_max: float = 0.0
    cpu_avg: float = 0.0
    cpu_process_max: float = 0.0
    cpu_process_avg: float = 0.0
    # RAM
    memory_mb_max: float = 0.0
    memory_mb_avg: float = 0.0
    memory_system_max: float = 0.0
    memory_system_avg: float = 0.0
    # GPU
    gpu_percent_max: Optional[float] = None
    gpu_percent_avg: Optional[float] = None
    gpu_memory_mb_max: Optional[float] = None
    gpu_memory_mb_avg: Optional[float] = None
    gpu_temperature_max: Optional[float] = None
    # Metadata
    sample_count: int = 0
    duration_seconds: float = 0.0


class ResourceMonitor:
    """Monitor de recursos con muestreo en hilo separado.

    Mide CPU, RAM y GPU continuamente durante la ejecución de código.

    Example:
        monitor = ResourceMonitor(interval=0.5)
        monitor.start()
        # ... código pesado ...
        stats = monitor.stop()
        print(f"RAM máxima: {stats.memory_mb_max:.2f} MB")
        print(f"GPU máxima: {stats.gpu_memory_mb_max:.2f} MB")
    """

    def __init__(self, interval: float = 0.5, include_gpu: bool = True):
        """
        Args:
            interval: Intervalo de muestreo en segundos (default: 0.5s)
            include_gpu: Incluir monitoreo de GPU NVIDIA (default: True)
        """
        self.interval = interval
        self.include_gpu = include_gpu and PYNVML_AVAILABLE
        self.samples: List[ResourceSample] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._process = psutil.Process(os.getpid())
        self._start_time: float = 0.0
        self._gpu_handle = None

        # Inicializar GPU si está disponible
        if self.include_gpu:
            try:
                pynvml.nvmlInit()
                self._gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # Primera GPU
            except Exception as e:
                print(f"⚠️  No se pudo inicializar GPU: {e}")
                self.include_gpu = False

    def _sample(self) -> ResourceSample:
        """Tomar una muestra de recursos."""
        timestamp = time.time() - self._start_time

        # CPU del sistema (todos los cores, sin bloqueo)
        cpu_percent = psutil.cpu_percent(interval=None)

        # CPU del proceso
        try:
            cpu_process = self._process.cpu_percent(interval=None)
        except psutil.NoSuchProcess:
            cpu_process = 0.0

        # RAM del proceso
        try:
            mem_info = self._process.memory_info()
            memory_mb_process = mem_info.rss / (1024 * 1024)
        except psutil.NoSuchProcess:
            memory_mb_process = 0.0

        # RAM del sistema
        mem_system = psutil.virtual_memory()
        memory_mb_system = mem_system.used / (1024 * 1024)
        memory_percent_system = mem_system.percent

        # GPU
        gpu_percent = None
        gpu_memory_mb = None
        gpu_memory_total_mb = None
        gpu_temperature = None

        if self.include_gpu and self._gpu_handle:
            try:
                # Utilización GPU
                util = pynvml.nvmlDeviceGetUtilizationRates(self._gpu_handle)
                gpu_percent = util.gpu

                # Memoria GPU
                mem = pynvml.nvmlDeviceGetMemoryInfo(self._gpu_handle)
                gpu_memory_mb = mem.used / (1024 * 1024)
                gpu_memory_total_mb = mem.total / (1024 * 1024)

                # Temperatura GPU
                gpu_temperature = pynvml.nvmlDeviceGetTemperature(
                    self._gpu_handle, pynvml.NVML_TEMPERATURE_GPU
                )
            except Exception:
                pass  # GPU puede estar ocupada

        return ResourceSample(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            cpu_percent_process=cpu_process,
            memory_mb_process=memory_mb_process,
            memory_mb_system=memory_mb_system,
            memory_percent_system=memory_percent_system,
            gpu_percent=gpu_percent,
            gpu_memory_mb=gpu_memory_mb,
            gpu_memory_total_mb=gpu_memory_total_mb,
            gpu_temperature=gpu_temperature,
        )

    def _monitor_loop(self):
        """Loop de monitoreo en hilo separado."""
        # Primera llamada a cpu_percent para inicializar (descarta el resultado)
        psutil.cpu_percent(interval=None)
        self._process.cpu_percent(interval=None)

        while self._running:
            sample = self._sample()
            self.samples.append(sample)
            time.sleep(self.interval)

    def start(self):
        """Iniciar monitoreo en background."""
        if self._running:
            return

        self.samples.clear()
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> ResourceStats:
        """Detener monitoreo y retornar estadísticas."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

        return self._compute_stats()

    def _compute_stats(self) -> ResourceStats:
        """Calcular estadísticas agregadas."""
        if not self.samples:
            return ResourceStats()

        stats = ResourceStats()
        stats.sample_count = len(self.samples)
        stats.duration_seconds = self.samples[-1].timestamp if self.samples else 0.0

        # CPU
        cpu_values = [s.cpu_percent for s in self.samples]
        cpu_process_values = [s.cpu_percent_process for s in self.samples]
        stats.cpu_max = max(cpu_values)
        stats.cpu_avg = sum(cpu_values) / len(cpu_values)
        stats.cpu_process_max = max(cpu_process_values)
        stats.cpu_process_avg = sum(cpu_process_values) / len(cpu_process_values)

        # RAM proceso
        mem_values = [s.memory_mb_process for s in self.samples]
        stats.memory_mb_max = max(mem_values)
        stats.memory_mb_avg = sum(mem_values) / len(mem_values)

        # RAM sistema
        mem_sys_values = [s.memory_mb_system for s in self.samples]
        stats.memory_system_max = max(mem_sys_values)
        stats.memory_system_avg = sum(mem_sys_values) / len(mem_sys_values)

        # GPU
        gpu_values = [s.gpu_percent for s in self.samples if s.gpu_percent is not None]
        gpu_mem_values = [
            s.gpu_memory_mb for s in self.samples if s.gpu_memory_mb is not None
        ]
        gpu_temp_values = [
            s.gpu_temperature for s in self.samples if s.gpu_temperature is not None
        ]

        if gpu_values:
            stats.gpu_percent_max = max(gpu_values)
            stats.gpu_percent_avg = sum(gpu_values) / len(gpu_values)

        if gpu_mem_values:
            stats.gpu_memory_mb_max = max(gpu_mem_values)
            stats.gpu_memory_mb_avg = sum(gpu_mem_values) / len(gpu_mem_values)

        if gpu_temp_values:
            stats.gpu_temperature_max = max(gpu_temp_values)

        return stats

    def get_samples(self) -> List[ResourceSample]:
        """Obtener todas las muestras (para gráficas)."""
        return self.samples.copy()

    def print_stats(self, stats: Optional[ResourceStats] = None):
        """Imprimir estadísticas de forma legible."""
        if stats is None:
            stats = self._compute_stats()

        print("\n" + "=" * 60)
        print("📊 ESTADÍSTICAS DE RECURSOS")
        print("=" * 60)
        print(
            f"⏱️  Duración: {stats.duration_seconds:.2f}s ({stats.sample_count} muestras)"
        )
        print("-" * 60)
        print("🖥️  CPU:")
        print(f"   Sistema  - Máx: {stats.cpu_max:.1f}%  Prom: {stats.cpu_avg:.1f}%")
        print(
            f"   Proceso  - Máx: {stats.cpu_process_max:.1f}%  Prom: {stats.cpu_process_avg:.1f}%"
        )
        print("-" * 60)
        print("🧠 RAM:")
        print(
            f"   Proceso  - Máx: {stats.memory_mb_max:.1f} MB  Prom: {stats.memory_mb_avg:.1f} MB"
        )
        print(
            f"   Sistema  - Máx: {stats.memory_system_max:.1f} MB  Prom: {stats.memory_system_avg:.1f} MB"
        )

        if stats.gpu_percent_max is not None:
            print("-" * 60)
            print("🎮 GPU:")
            print(
                f"   Uso      - Máx: {stats.gpu_percent_max:.1f}%  Prom: {stats.gpu_percent_avg:.1f}%"
            )
            if stats.gpu_memory_mb_max:
                print(
                    f"   VRAM     - Máx: {stats.gpu_memory_mb_max:.1f} MB  Prom: {stats.gpu_memory_mb_avg:.1f} MB"
                )
            if stats.gpu_temperature_max:
                print(f"   Temp     - Máx: {stats.gpu_temperature_max}°C")
        print("=" * 60 + "\n")

    def cleanup(self):
        """Liberar recursos de GPU."""
        if self.include_gpu and PYNVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass


@contextmanager
def monitor_resources(
    interval: float = 0.5, include_gpu: bool = True, print_stats: bool = True
):
    """Context manager para monitorear recursos durante un bloque de código.

    Example:
        with monitor_resources() as monitor:
            # código pesado aquí
            resultado = modelo.generate(...)

        # Las estadísticas se imprimen automáticamente
        # O acceder a los datos:
        stats = monitor.stop()  # Ya llamado automáticamente
        samples = monitor.get_samples()  # Para gráficas
    """
    monitor = ResourceMonitor(interval=interval, include_gpu=include_gpu)
    monitor.start()
    try:
        yield monitor
    finally:
        stats = monitor.stop()
        if print_stats:
            monitor.print_stats(stats)
        monitor.cleanup()


# Mantener la función original para compatibilidad (pero mejorada)
def medir_recursos():
    """Medir el uso de recursos del sistema (versión puntual).

    NOTA: Para mediciones precisas durante ejecución pesada, usar ResourceMonitor.

    Returns:
        dict: Diccionario con el uso de CPU, memoria RAM y espacio en disco
    """
    # Obtener proceso actual
    process = psutil.Process(os.getpid())

    # Medir uso de CPU (del sistema)
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # Medir uso de memoria del proceso
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / (1024 * 1024)  # Convertir a MB

    # Memoria del sistema
    mem_system = psutil.virtual_memory()
    memory_system_mb = mem_system.used / (1024 * 1024)

    # Medir uso de disco
    disk_usage = psutil.disk_usage("/")
    disk_percent = disk_usage.percent

    # GPU (si está disponible)
    gpu_info = {}
    if PYNVML_AVAILABLE:
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_info = {
                "gpu_percent": util.gpu,
                "gpu_memory_mb": mem.used / (1024 * 1024),
                "gpu_memory_total_mb": mem.total / (1024 * 1024),
            }
            pynvml.nvmlShutdown()
        except Exception:
            pass

    print(f"Uso de CPU: {cpu_percent:.2f}%")
    print(f"Uso de memoria RAM (proceso): {memory_mb:.2f} MB")
    print(f"Uso de memoria RAM (sistema): {memory_system_mb:.2f} MB")
    print(f"Uso de disco: {disk_percent:.2f}%")

    if gpu_info:
        print(f"Uso de GPU: {gpu_info['gpu_percent']:.2f}%")
        print(
            f"Uso de VRAM: {gpu_info['gpu_memory_mb']:.2f} / {gpu_info['gpu_memory_total_mb']:.2f} MB"
        )

    return {
        "cpu_percent": cpu_percent,
        "memory_mb": memory_mb,
        "memory_system_mb": memory_system_mb,
        "disk_percent": disk_percent,
        **gpu_info,
    }


# Clase para medir el tiempo de ejecución
class TimerContextManager:
    """Manejador de contexto para medir el tiempo de ejecución de un bloque de código.

    Example:
        with TimerContextManager("Nombre de la sección") as timer:
            # código a medir
        tiempo_transcurrido = timer.elapsed
    """

    def __init__(self, section_name):
        self.section_name = section_name
        self.start_time = None
        self.elapsed = 0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        print(f"Tiempo de ejecución [{self.section_name}]: {self.elapsed:.4f} segundos")
        return False


# función métrica MSE - PSNR de dos audios
def mse_psnr(audio_original, audio_modificado):
    """Calcular la relación señal-ruido de pico (PSNR) entre dos audios.
    docs: https://www.youtube.com/watch?v=XmPfXt9E3VI

    Args:
        audio_original (numpy.array): Arreglo de audio original
        audio_modificado (numpy.array): Arreglo de audio modificado

    Returns:
        float: Valor de la relación señal-ruido de pico (PSNR) entre los dos audios
    """
    try:
        # Verificar las dimensiones y asegurar que sean compatibles para la operación
        if len(audio_original.shape) != len(audio_modificado.shape):
            # Si tienen distinto número de dimensiones, convertir para hacerlos compatibles
            if len(audio_original.shape) > len(audio_modificado.shape):
                # Si original es estéreo y modificado es mono, convertir modificado a estéreo
                audio_modificado = np.column_stack((audio_modificado, audio_modificado))
            else:
                # Si original es mono y modificado es estéreo, tomar solo el canal izquierdo de modificado
                audio_modificado = audio_modificado[:, 0]

        # Si son estéreo, calcular el MSE promediando los canales
        if len(audio_original.shape) > 1:
            mse_values = []
            for ch in range(audio_original.shape[1]):
                mse_ch = np.mean((audio_original[:, ch] - audio_modificado[:, ch]) ** 2)
                mse_values.append(mse_ch)
            mse = np.mean(mse_values)
        else:
            # Para audio mono
            mse = np.mean((audio_original - audio_modificado) ** 2)

        # Calcular el valor máximo de los datos
        max_val = np.max(np.abs(audio_original))

        # Prevenir división por cero
        if mse == 0:
            return 0, float("inf")

        # Calcular el PSNR
        psnr = 10 * np.log10(max_val**2 / mse)

        # MSE : Es el promedio de los errores al cuadrado
        #   entre los valores originales y los valores predichos.
        # PSNR : Aplicado al audio es una medida de la
        #   calidad de la señal de audio, que se mide en decibelios (dB).
        print(f"MSE: {mse:.2f}, PSNR: {psnr:.2f} dB")

        return mse, psnr

    except Exception as e:
        print(f"Error al calcular MSE-PSNR: {e}")
        return 0, 0


# Función calculo de distorsión de audio original y audio modificado
def distorsion(audio_original, audio_modificado):
    """Calcular la distorsión entre dos audios.

    Args:
        audio_original (numpy.array): Arreglo de audio original
        audio_modificado (numpy.array): Arreglo de audio modificado

    Returns:
        float: Valor de la distorsión entre los dos audios
    """
    # Calcular la distorsión
    dist = np.mean(np.abs(audio_original - audio_modificado))
    # Distorsión : Es la diferencia entre la señal original
    #   y la señal de salida de un sistema de procesamiento de señales.
    print(f"Distorsión: {dist:.2f}")

    return dist


# función para determinar la invisibilidad del mensaje en el audio original y el audio modificado usando pruebas estadisticas (Test de chi-cuadrado y komolgorov-smirnov)
def invisibilidad(audio_original, audio_modificado):
    """Determinar la invisibilidad del mensaje en el audio original y el audio modificado utilizando pruebas estadísticas.

    Args:
        audio_original (numpy.array): Arreglo de audio original
        audio_modificado (numpy.array): Arreglo de audio modificado

    Returns:
        float: Valor de la invisibilidad del mensaje en el audio modificado
    """
    # Verificar si hay ceros en audio_modificado y reemplazarlos con un valor pequeño
    audio_modificado = np.where(audio_modificado == 0, 1e-10, audio_modificado)

    # Prueba de chi-cuadrado
    #  Compara dos distribuciones de frecuencias para ver si son estadísticamente diferentes.
    #  En este caso, está comparando la distribución de valores en audio_original con la de audio_modificado.
    # ? formula chi-cuadrado = sum((observed-expected)^2 / expected)
    chi2_stat, chi2_p = chisquare(audio_original, audio_modificado)
    # Prueba de Kolmogorov-Smirnov
    #  También compara dos distribuciones, pero es más sensible a diferencias en
    #  la forma de las distribuciones, no solo en las frecuencias.
    # ? formula ks = max(abs(F1(x) - F2(x)))
    ks_stat, ks_p = ks_2samp(audio_original, audio_modificado)
    # Prueba Mann-Whitney U
    #  Prueba no paramétrica que compara dos muestras independientes para determinar
    #  si una muestra proviene de una población con valores significativamente más altos
    #  que la otra muestra.
    # ? formula U = n1 * n2 + (n1 * (n1 + 1)) / 2 - R1
    # ? formula R1 = sum(rank1)
    # ? formula rank1 = sum(i=1, n1) rank(i)
    # ? formula rank(i) = 1 + sum(j=1, i-1) sign(x_i - x_j)
    # ? formula sign(x) = 1 si x > 0, 0 si x = 0, -1 si x < 0
    U1, p = mannwhitneyu(audio_original, audio_modificado)

    print(f"Chi-cuadrado: estadístico={chi2_stat:.2f}, p-valor={chi2_p:.2f}")
    # ? chi2_stat: Es el estadístico de la prueba de chi-cuadrado.
    #   Indica cuán grande es la diferencia entre las dos distribuciones.
    #   Un valor alto sugiere que las distribuciones son muy diferentes.
    # ? chi2_p: Es el valor p de la prueba.
    #   Indica la probabilidad de obtener un estadístico de chi-cuadrado
    #   tan grande o más grande, asumiendo que las dos distribuciones son iguales.
    #   Un valor p bajo (por ejemplo, menor a 0.05) sugiere que es muy improbable
    #   que las dos distribuciones sean iguales, por lo que rechazamos la hipótesis
    #   nula de que las distribuciones son iguales.
    print(f"Kolmogorov-Smirnov: estadístico={ks_stat:.2f}, p-valor={ks_p:.2f}")
    # ? ks_stat: Es el estadístico de la prueba de Kolmogorov-Smirnov.
    #   Indica la máxima diferencia entre las funciones de distribución acumulada de las dos muestras.
    # ? ks_p: Es el valor p de la prueba.
    #   Similar al chi2_p, indica la probabilidad de obtener un estadístico de Kolmogorov-Smirnov
    #   tan grande o más grande, asumiendo que las dos distribuciones son iguales.
    #   Un valor p bajo sugiere que las distribuciones son diferentes.
    print(f"Mann-Whitney U: estadístico={U1:.2f}, p-valor={p:.2f}")
    # ? U1: Es el estadístico de la prueba de Mann-Whitney U.
    #   Indica cuán diferente son las dos muestras.
    # ? p: Es el valor p de la prueba.
    #   Similar a chi2_p y ks_p, indica la probabilidad de obtener un estadístico de Mann-Whitney U

    return chi2_stat, chi2_p, ks_stat, ks_p, U1, p


# función para la medición de la entropia en el audio original y el audio modificado
def entropia(audio_original, audio_modificado):
    """Calcular la entropía de dos audios.
    formula entropia = -sum(p(x) * log2(p(x)))

    La entropia minima es 0 y la maxima es log2(2^16) = 16

    basado en https://stackoverflow.com/questions/15450192/fastest-way-to-compute-entropy-in-python :)

    Args:
        audio_original (numpy.array): Arreglo de audio original
        audio_modificado (numpy.array): Arreglo de audio modificado

    Returns:
        float: Valor de la entropía de los dos audios
    """

    # LABELS
    n_labels_original = len(audio_original)
    n_labels_modificado = len(audio_modificado)

    # SESGO
    if n_labels_original <= 1:
        return 0
    if n_labels_modificado <= 1:
        return 0

    # Asegúrate de que 'base_original' y 'base_mod' estén definidas antes de usarlas
    if "base_original" not in locals():
        base_original = None
    if "base_mod" not in locals():
        base_mod = None

    # RECUPERAR PROBABILIDADES
    value_original, counts_original = np.unique(audio_original, return_counts=True)
    probs_original = counts_original / n_labels_original
    n_clases_original = np.count_nonzero(probs_original)

    value_modificado, counts_modificado = np.unique(
        audio_modificado, return_counts=True
    )
    probs_modificado = counts_modificado / n_labels_modificado
    n_clases_modificado = np.count_nonzero(probs_modificado)

    # SESGO CLASES
    if n_clases_original <= 1:
        entropia_original = 0
    if n_clases_modificado <= 1:
        entropia_modificado = 0

    ent_original = 0
    ent_modificado = 0

    # CALCULAR ENTROPIA
    if base_original is None:
        base_original = e
    for i in probs_original:
        ent_original -= i * log(i, base_original)

    if base_mod is None:
        base_mod = e
    for i in probs_modificado:
        ent_modificado -= i * log(i, base_mod)

    print(f"Entropía audio original   [0,16]: {ent_original}")
    print(f"Entropía audio modificado [0,16]: {ent_modificado}")

    return ent_original, ent_modificado


# función para la medición de la correlación cruzada en el audio original y el audio modificado
def correlacion_cruzada(audio_original, audio_modificado):
    """Calcular la correlación cruzada entre dos audios.
    formula correlacion_cruzada = sum((x[n] - media_x) * (y[n] - media_y)) / (sqrt(sum((x[n] - media_x)^2) * sqrt(sum((y[n] - media_y)^2)))

    Args:
        audio_original (numpy.array): Arreglo de audio original
        audio_modificado (numpy.array): Arreglo de audio modificado

    Returns:
        float: Valor de la correlación cruzada entre los dos audios
    """
    # Calcular la media de los audios
    media_original = np.mean(audio_original)
    media_modificado = np.mean(audio_modificado)

    # Calcular la correlación cruzada
    correlacion_cruzada = np.sum(
        (audio_original - media_original) * (audio_modificado - media_modificado)
    ) / np.sqrt(
        np.sum((audio_original - media_original) ** 2)
        * np.sqrt(np.sum((audio_modificado - media_modificado) ** 2))
    )

    print(f"Correlación cruzada: {correlacion_cruzada:.2f}")

    return correlacion_cruzada


# función para determinar la autocorrelación en el audio original y el audio modificado
def autocorrelacion(audio_original, audio_modificado):
    """Calcular la autocorrelación de dos audios.

    Args:
        audio_original (numpy.array): Arreglo de audio original
        audio_modificado (numpy.array): Arreglo de audio modificado
    """
    # Calcular la autocorrelación
    autocorrelacion_original = np.correlate(audio_original, audio_original, mode="full")
    autocorrelacion_modificado = np.correlate(
        audio_modificado, audio_modificado, mode="full"
    )

    print(f"Autocorrelación audio original: {autocorrelacion_original}")
    print(f"Autocorrelación audio modificado: {autocorrelacion_modificado}")


# función para el analisis de componentes del audio original y el audio modificado
def analisis_componentes(audio_original, audio_modificado):
    """Realizar un análisis de componentes en dos audios.

    Args:
        audio_original (numpy.array): Arreglo de audio original
        audio_modificado (numpy.array): Arreglo de audio modificado
    """
    # Calcular la media y la desviación estándar de los audios
    media_original = np.mean(audio_original)
    media_modificado = np.mean(audio_modificado)
    std_original = np.std(audio_original)
    std_modificado = np.std(audio_modificado)

    print(f"Media audio original: {media_original:.2f}")
    print(f"Media audio modificado: {media_modificado:.2f}")
    print(f"Desviación estándar audio original: {std_original:.2f}")
    print(f"Desviación estándar audio modificado: {std_modificado:.2f}")

    return media_original, media_modificado, std_original, std_modificado
