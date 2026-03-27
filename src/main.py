# Compresión de texto
from src.compresion.comprimir import comprimir
from src.compresion.descomprimir import descomprimir

# Encriptado de texto
from src.encriptado.encriptar import xor_encriptado

# Esteganografía en señales de audio
from src.esteganografiado.esteganografiar import (
    cargar_archivo_wav,
    guardar_archivo_wav,
    insertar_mensaje_segmento_lsb_sequential,
    insertar_mensaje_segmento_lsb_random,
    insertar_lsb_caotico,
)
from src.esteganografiado.desesteganografiar import (
    extraer_mensaje_segmento_lsb_sequential,
    extraer_mensaje_segmento_lsb_random,
    extraer_lsb_caotico,
)

# Graficación de señales de audio y métricas
from src.utils.graficas import (
    plot_audio_waveforms,
    plot_audio_histograms,
    plot_audio_spectrograms,
    plot_audio_difference,
    plot_resource_usage,
    plot_resource_usage_detailed,
    plot_execution_times,
    plot_frequency_distribution,
    plot_audio_waveforms_librosa,
    plot_attack_results,
    plot_attack_spectrograms,
)
from src.utils.metricas import (
    mse_psnr,
    distorsion,
    invisibilidad,
    entropia,
    correlacion_cruzada,
    analisis_componentes,
    medir_recursos,
    TimerContextManager,
    ResourceMonitor,
    monitor_resources,
)

# Generar llave de encriptación
from src.utils.caos import generar_llave

# Enums configuraciones
from src.utils.chaos_mod_enum import ChaosMod

# Ataques
from src.utils.ataques import AudioAttacks

import numpy as np
import wave
import os
import sys
import time
import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime


class TeeStream:
    """Replica stdout/stderr en terminal y archivo de log."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def obtener_rutas_repositorio():
    raiz_repo = Path(__file__).resolve().parent.parent
    data_dir = raiz_repo / "data"
    plots_dir = raiz_repo / "plots"
    salida_dir = raiz_repo / "outputs" / "entrega_profesoras"
    salida_dir.mkdir(parents=True, exist_ok=True)
    return raiz_repo, data_dir, plots_dir, salida_dir


def bits_a_bytes(bits):
    if not bits:
        return []
    return [int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)]


def exportar_entrega_profesoras(
    salida_dir,
    data_dir,
    plots_dir,
    ruta_audio,
    ruta_audio_modificado,
    mensaje_comprimido,
    mensaje_extraido,
    mensaje_descomprimido,
    mensaje_bits,
    llave,
    inicio_segmento,
    fin_segmento,
    sample_rate,
    global_execution_time,
    section_names,
    execution_times,
    metrics,
    sequential,
    resultados_ataques,
):
    # Texto comprimido
    ruta_texto_comprimido = salida_dir / "texto_comprimido.txt"
    ruta_texto_comprimido.write_text(mensaje_comprimido, encoding="utf-8")

    # Texto extraído/desencriptado desde el audio
    ruta_texto_extraido = salida_dir / "texto_extraido.txt"
    ruta_texto_extraido.write_text(
        mensaje_extraido if mensaje_extraido else "", encoding="utf-8"
    )

    # Texto descomprimido final (si se pudo reconstruir)
    ruta_texto_descomprimido = salida_dir / "texto_descomprimido.txt"
    ruta_texto_descomprimido.write_text(
        mensaje_descomprimido if mensaje_descomprimido else "",
        encoding="utf-8",
    )

    # Payload cifrado serializado
    payload_bytes = bits_a_bytes(mensaje_bits)
    payload_hex = "".join(f"{b:02x}" for b in payload_bytes)
    ruta_payload = salida_dir / "texto_comprimido_encriptado.json"
    ruta_payload.write_text(
        json.dumps(
            {
                "formato": "payload_encriptado",
                "longitud_bits": len(mensaje_bits),
                "longitud_bytes": len(payload_bytes),
                "payload_hex": payload_hex,
                "llave_longitud_bytes": int(len(llave)),
                "nota": "Payload generado desde mensaje comprimido usando flujo XOR existente.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Copias de audio en carpeta de entrega
    shutil.copy2(ruta_audio, salida_dir / "audio_original.wav")
    shutil.copy2(ruta_audio_modificado, salida_dir / "audio_estegano.wav")

    # Copiar todas las figuras generadas
    if plots_dir.exists():
        for archivo_png in plots_dir.glob("*.png"):
            shutil.copy2(archivo_png, salida_dir / archivo_png.name)

    # Renombrar alias esperados por el informe previo
    if (salida_dir / "audio_waveforms.png").exists():
        shutil.copy2(
            salida_dir / "audio_waveforms.png",
            salida_dir / "onda_original_y_estegano.png",
        )

    # Métrica BPS
    with wave.open(ruta_audio, "rb") as wav_file:
        n_frames = wav_file.getnframes()
    duracion_segundos = n_frames / sample_rate if sample_rate else 0.0
    bits_insertados = len(mensaje_bits)
    bps = (bits_insertados / duracion_segundos) if duracion_segundos > 0 else 0.0
    metodo = "LSB secuencial" if sequential else "LSB aleatorio"

    # Resumen ejecutable en JSON
    resumen_json = {
        "fecha_hora": datetime.now().isoformat(timespec="seconds"),
        "metodo": metodo,
        "inicio_segmento": int(inicio_segmento),
        "fin_segmento": int(fin_segmento),
        "bits_insertados": int(bits_insertados),
        "duracion_segundos": float(duracion_segundos),
        "bps": float(bps),
        "tiempo_global_segundos": float(global_execution_time),
        "secciones": [
            {"nombre": nombre, "tiempo_segundos": float(tiempo)}
            for nombre, tiempo in zip(section_names, execution_times)
        ],
        "metricas": metrics,
        "ataques": resultados_ataques,
    }
    (salida_dir / "resumen_ejecucion.json").write_text(
        json.dumps(resumen_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Informe para profesoras
    informe = f"""# Informe para profesoras (ejecución real desde `src/main.py`)

## 1. Alcance
Se ejecutó el flujo principal del repositorio y se consolidaron automáticamente los artefactos de evidencia en `outputs/entrega_profesoras`.

## 2. Trazabilidad de archivos
| Archivo | Origen/Generación | Descripción |
|---|---|---|
| `proceso.log` | Redirección stdout/stderr de `src/main.py` | Log completo de ejecución. |
| `texto_comprimido.txt` | `src.compresion.comprimir.comprimir` | Texto comprimido antes de cifrado. |
| `texto_extraido.txt` | `src.main.extraer_y_verificar_mensaje` | Texto recuperado y desencriptado desde el audio esteganografiado. |
| `texto_descomprimido.txt` | `src.compresion.descomprimir.descomprimir` | Reconstrucción final del texto (si la descompresión fue exitosa). |
| `texto_comprimido_encriptado.json` | `src.main.convertir_mensaje_a_bits` + XOR | Payload cifrado serializado en hex con metadatos. |
| `audio_original.wav` | Copia de `data/audio_test.wav` | Audio base utilizado. |
| `audio_estegano.wav` | Copia de `data/audio_test_modificado.wav` | Audio con mensaje oculto. |
| `*.png` | `src.utils.graficas` | Gráficas y visualizaciones generadas en la corrida. |
| `resumen_ejecucion.json` | `src/main.py` | Resumen técnico estructurado de tiempos, métricas y parámetros. |

## 3. Parámetros de ejecución
- Método de inserción: **{metodo}**
- Inicio del segmento usado: **{inicio_segmento}**
- Fin del segmento usado: **{fin_segmento}**
- Fecha/hora ejecución: **{datetime.now().isoformat(timespec="seconds")}**

## 4. Métrica BPS
- Bits insertados: **{bits_insertados}**
- Duración del audio: **{duracion_segundos:.4f} s**
- BPS calculado: **{bps:.4f} bits/s**

Fórmula usada: `BPS = bits_insertados / duración_en_segundos`.

## 5. Nota metodológica sobre entropía
La función `src.utils.metricas.entropia` usa logaritmo natural (`base = e`), por lo que reporta en **nats**.
Para convertir a bits de información: `H_bits = H_nats / ln(2)`.

## 6. Estado de ataques
- Ataques ejecutados: **{"sí" if resultados_ataques else "no"}**

## 7. Estado de recuperación de texto
- Texto extraído/desencriptado disponible: **{"sí" if mensaje_extraido else "no"}**
- Texto descomprimido disponible: **{"sí" if mensaje_descomprimido else "no"}**
"""
    (salida_dir / "informe_profesoras.md").write_text(informe, encoding="utf-8")

    clasificacion = """# Clasificación simple de pruebas (basada en funciones existentes)

## Funcionales mínimas
- **Compresión de texto**: `src.compresion.comprimir.comprimir`
- **Encriptación XOR**: `src.encriptado.encriptar.xor_encriptado` (invocada vía `src.main.convertir_mensaje_a_bits`)
- **Inserción esteganográfica**: `src.esteganografiado.esteganografiar.insertar_mensaje_segmento_lsb_sequential` o `_random` (invocada vía `src.main.insertar_mensaje_en_audio`)
- **Persistencia de audio**: `src.esteganografiado.esteganografiar.guardar_archivo_wav`

## Visualización/evidencia
- Gráficas de señal y espectro desde `src.utils.graficas`.
- Log integral de ejecución en `proceso.log`.

## Métricas reportadas
- MSE y PSNR
- Distorsión
- Invisibilidad (Chi-cuadrado, KS, Mann-Whitney)
- Entropía
- Correlación cruzada
- Análisis de componentes
- BPS

## Fuera de alcance opcional
- Ataques robustos intensivos solo cuando se ejecuta `--attacks`.
"""
    (salida_dir / "clasificacion_pruebas.md").write_text(
        clasificacion, encoding="utf-8"
    )

    print(f"\nEvidencias exportadas en: {salida_dir}")


def cargar_audio(ruta_audio):
    return cargar_archivo_wav(ruta_audio)


def convertir_mensaje_a_bits(mensaje):
    # Codificar a UTF-8 para manejar caracteres Unicode (emojis, acentos, comillas tipográficas, etc.)
    mensaje_en_bytes = np.array(list(mensaje.encode("utf-8")), dtype=np.uint8)
    longitud_de_llave = len(mensaje_en_bytes)
    llave = generar_llave(
        ChaosMod.X0.value, ChaosMod.R.value, ChaosMod.N_WARMUP.value, longitud_de_llave
    )
    mensaje_encriptado = xor_encriptado(mensaje_en_bytes, llave)
    mensaje_para_paso = "".join([chr(b) for b in mensaje_encriptado])
    mensaje_bits = "".join(
        [format(ord(char), "08b") for char in str(mensaje_para_paso)]
    )
    return mensaje_bits, llave


def insertar_mensaje_en_audio(
    arreglo_audio_original, mensaje_bits, audio_total=False, sequential=True,
    chaotic_full=True
):
    """Insertar mensaje en audio usando posiciones caóticas distribuidas en todo el audio.

    Args:
        arreglo_audio_original: Audio original en formato int16
        mensaje_bits: Cadena de bits del mensaje
        audio_total: Si usar todo el audio como segmento (legacy)
        sequential: Si usar inserción secuencial o aleatoria (legacy)
        chaotic_full: Si True, usa distribución caótica en todo el audio (nuevo método)

    Returns:
        tuple: (audio_modificado, inicio_segmento, fin_segmento)
               Con chaotic_full=True, inicio=0 y fin=len(audio)
    """
    # Nuevo método: distribución caótica en todo el audio
    if chaotic_full:
        try:
            arreglo_audio_modificado, posiciones = insertar_lsb_caotico(
                arreglo_audio_original,
                mensaje_bits,
                ChaosMod.X0.value,
                ChaosMod.R.value,
                ChaosMod.N_WARMUP.value,
            )
            print(f"  Posiciones caóticas generadas: {len(posiciones)} en rango [0, {len(arreglo_audio_original)})")
            print(f"  Distribución: min={posiciones.min()}, max={posiciones.max()}, std={posiciones.std():.0f}")
            return arreglo_audio_modificado, 0, len(arreglo_audio_original)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Legacy: inserción en segmento
    if audio_total:
        arreglo_segmento_original = arreglo_audio_original
        inicio_segmento = 0
        fin_segmento = len(arreglo_audio_original)
    else:
        punto_medio = len(arreglo_audio_original) // 2
        inicio_segmento = punto_medio - 22050
        fin_segmento = punto_medio + 22050
        arreglo_segmento_original = arreglo_audio_original[inicio_segmento:fin_segmento]

    try:
        if sequential:
            arreglo_segmento_modificado = insertar_mensaje_segmento_lsb_sequential(
                arreglo_segmento_original, mensaje_bits
            )
        else:
            arreglo_segmento_modificado = insertar_mensaje_segmento_lsb_random(
                arreglo_segmento_original, mensaje_bits
            )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    arreglo_audio_modificado = np.concatenate(
        (
            arreglo_audio_original[:inicio_segmento],
            arreglo_segmento_modificado,
            arreglo_audio_original[fin_segmento:],
        )
    )
    return arreglo_audio_modificado, inicio_segmento, fin_segmento


def guardar_audio_modificado(ruta_audio_modificado, arreglo_audio_modificado, params):
    guardar_archivo_wav(ruta_audio_modificado, arreglo_audio_modificado, params)


def extraer_y_verificar_mensaje(
    arreglo_audio_modificado,
    inicio_segmento,
    fin_segmento,
    mensaje_bits,
    llave,
    sequential=True,
    chaotic_full=True,
):
    """Extraer y verificar mensaje oculto en el audio.

    Args:
        arreglo_audio_modificado: Audio con mensaje oculto
        inicio_segmento: Inicio del segmento (0 si chaotic_full)
        fin_segmento: Fin del segmento (len(audio) si chaotic_full)
        mensaje_bits: Bits originales para verificación
        llave: Clave de encriptación
        sequential: Si usar extracción secuencial (legacy)
        chaotic_full: Si True, usa extracción caótica de todo el audio
    """
    if chaotic_full:
        bits_extraidos, mensaje_extraido = extraer_lsb_caotico(
            arreglo_audio_modificado,
            len(mensaje_bits),
            ChaosMod.X0.value,
            ChaosMod.R.value,
            ChaosMod.N_WARMUP.value,
        )
    else:
        arreglo_segmento_extraido = arreglo_audio_modificado[inicio_segmento:fin_segmento]
        if sequential:
            bits_extraidos, mensaje_extraido = extraer_mensaje_segmento_lsb_sequential(
                arreglo_segmento_extraido, len(mensaje_bits)
            )
        else:
            bits_extraidos, mensaje_extraido = extraer_mensaje_segmento_lsb_random(
                arreglo_segmento_extraido, len(mensaje_bits)
            )

    extraccion_correcta = mensaje_bits == bits_extraidos

    if extraccion_correcta:
        mensaje_original_bytes = np.array(
            [ord(c) for c in mensaje_extraido], dtype=np.uint8
        )
        mensaje_desencriptado_bytes = xor_encriptado(mensaje_original_bytes, llave)
        # Decodificar desde UTF-8 para recuperar caracteres Unicode correctamente
        mensaje_desencriptado = bytes(mensaje_desencriptado_bytes).decode("utf-8")
        return mensaje_desencriptado
    else:
        return None


def ejecutar_ataques(
    ruta_audio_modificado,
    inicio_segmento,
    fin_segmento,
    mensaje_bits_length,
    sequential=False,
):
    """Ejecutar la batería de ataques sobre el audio esteganografiado y evaluar su robustez

    Args:
        ruta_audio_modificado (str): Ruta del archivo de audio esteganografiado
        inicio_segmento (int): Inicio del segmento donde está oculto el mensaje
        fin_segmento (int): Fin del segmento donde está oculto el mensaje
        mensaje_bits_length (int): Longitud en bits del mensaje oculto
        sequential (bool): Si el mensaje fue insertado secuencialmente o no

    Returns:
        dict: Resultados de los ataques
    """
    print("\n==============================================")
    print("INICIANDO MÓDULO DE EVALUACIÓN DE ATAQUES")
    print("==============================================")

    # Crear directorio para los resultados de los ataques
    output_dir = os.path.join(os.getcwd(), "attacks_output")

    # Inicializar el módulo de ataques
    with TimerContextManager("Inicialización módulo de ataques") as timer:
        attacks = AudioAttacks(ruta_audio_modificado, output_dir)

    # Ejecutar todos los ataques
    with TimerContextManager("Ejecución de ataques") as timer:
        resultados = attacks.run_all_attacks(
            inicio_segmento, fin_segmento, mensaje_bits_length, sequential
        )

    print("\n--- Resumen de resultados de ataques ---")
    ataques_exitosos = sum(1 for resultado in resultados.values() if resultado["exito"])
    total_ataques = len(resultados)
    print(
        f"Ataques superados: {ataques_exitosos} de {total_ataques} ({ataques_exitosos / total_ataques * 100:.1f}%)"
    )

    # Generar gráficas de resultados
    plot_attack_results(resultados)

    # Generar gráficas de espectrogramas para algunos ataques seleccionados
    attacked_audios = {
        "ruido_0.01": attacks.add_noise(0.01)[1],
        "mp3_64kbps": attacks.compress_decompress("mp3", 64)[1],
        "filtrado_3000Hz": attacks.low_pass_filter(3000)[1],
    }
    plot_attack_spectrograms(attacks.original_audio, attacked_audios, attacks.sr)

    return resultados


def main():
    _, data_dir, plots_dir, salida_dir = obtener_rutas_repositorio()

    # Log persistente de toda la ejecución
    log_path = salida_dir / "proceso.log"
    stdout_original = sys.stdout
    stderr_original = sys.stderr
    log_file = open(log_path, "w", encoding="utf-8")
    sys.stdout = TeeStream(stdout_original, log_file)
    sys.stderr = TeeStream(stderr_original, log_file)

    try:
        # Parsear argumentos de línea de comandos
        parser = argparse.ArgumentParser(
            description="Esteganografía en audio con evaluación de robustez."
        )
        parser.add_argument(
            "--attacks",
            action="store_true",
            help="Ejecutar módulo de ataques para evaluar la robustez",
        )
        parser.add_argument(
            "--sequential",
            action="store_true",
            help="Usar esteganografía secuencial (por defecto usa aleatoria)",
        )
        args = parser.parse_args()

        # Variables para medir rendimiento
        section_names = []
        execution_times = []
        global_start_time = time.time()
        resultados_ataques = None
        mensaje_descomprimido = None

        # Diccionario para guardar timestamps de inicio de cada sección
        section_markers = {}

        # Ruta del archivo de audio
        ruta_audio = str(data_dir / "audio_test.wav")

        # ============================================================
        # MONITOR GLOBAL - captura recursos durante TODA la ejecución
        # ============================================================
        print("\n--- Iniciando monitor de recursos global ---")
        global_monitor = ResourceMonitor(interval=0.5)
        global_monitor.start()

        # Registrar el uso inicial de recursos
        print("\n--- Recursos iniciales ---")
        recursos = medir_recursos()

        # Cargar el audio con medición de tiempo
        section_markers["Carga audio"] = time.time() - global_start_time
        with TimerContextManager("Carga de audio") as timer:
            arreglo_audio_original = cargar_audio(ruta_audio)
        section_names.append("Carga de audio")
        execution_times.append(timer.elapsed)

        # Obtener parámetros del archivo de audio original
        with wave.open(ruta_audio, "rb") as wav_file:
            params = wav_file.getparams()
            sample_rate = wav_file.getframerate()

        # Mensaje a insertar
        mensaje = """
    En el principio creó Dios los cielos y la tierra.
    Y la tierra estaba desordenada y vacía, y las tinieblas estaban sobre la faz del abismo, y el Espíritu de Dios se movía sobre la faz de las aguas.
    Y dijo Dios: Sea la luz; y fue la luz.
    Y vio Dios que la luz era buena; y separó Dios la luz de las tinieblas.
    Y llamó Dios a la luz Día, y a las tinieblas llamó Noche. Y fue la tarde y la mañana un día.
    Luego dijo Dios: Haya expansión en medio de las aguas, y separe las aguas de las aguas.
    E hizo Dios la expansión, y separó las aguas que estaban debajo de la expansión, de las aguas que estaban sobre la expansión. Y fue así.
    Y llamó Dios a la expansión Cielos. Y fue la tarde y la mañana el día segundo.
    Dijo también Dios: Júntense las aguas que están debajo de los cielos en un lugar, y descúbrase lo seco. Y fue así.
    """

        # Comprimir mensaje con medición de tiempo
        section_markers["Compresión"] = time.time() - global_start_time
        with TimerContextManager("Compresión de texto") as timer:
            mensaje_comprimido = comprimir(mensaje)
            mensaje = mensaje_comprimido
        section_names.append("Compresión de texto")
        execution_times.append(timer.elapsed)

        # Convertir mensaje a bits y encriptar con medición de tiempo
        section_markers["Encriptación"] = time.time() - global_start_time
        with TimerContextManager("Encriptación") as timer:
            mensaje_bits, llave = convertir_mensaje_a_bits(mensaje)
        section_names.append("Encriptación")
        execution_times.append(timer.elapsed)

        # Determinar el método de esteganografía
        sequential = args.sequential
        metodo = "secuencial" if sequential else "aleatorio"
        print(f"\nUtilizando método de esteganografía: {metodo}")

        # Insertar mensaje en el audio con medición de tiempo
        section_markers["Esteganografía"] = time.time() - global_start_time
        with TimerContextManager("Esteganografía") as timer:
            arreglo_audio_modificado, inicio_segmento, fin_segmento = (
                insertar_mensaje_en_audio(
                    arreglo_audio_original, mensaje_bits, False, sequential
                )
            )
        section_names.append("Esteganografía")
        execution_times.append(timer.elapsed)

        # Guardar el archivo de audio modificado con medición de tiempo
        ruta_audio_modificado = str(data_dir / "audio_test_modificado.wav")
        section_markers["Guardar"] = time.time() - global_start_time
        with TimerContextManager("Guardar audio") as timer:
            guardar_audio_modificado(
                ruta_audio_modificado, arreglo_audio_modificado, params
            )
        section_names.append("Guardar audio")
        execution_times.append(timer.elapsed)

        # Extraer y verificar el mensaje con medición de tiempo
        section_markers["Extracción"] = time.time() - global_start_time
        with TimerContextManager("Extracción mensaje") as timer:
            mensaje_desencriptado = extraer_y_verificar_mensaje(
                arreglo_audio_modificado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits,
                llave,
                sequential,
            )
        section_names.append("Extracción mensaje")
        execution_times.append(timer.elapsed)

        if mensaje_desencriptado:
            try:
                section_markers["Descompresión"] = time.time() - global_start_time
                with TimerContextManager("Descompresión") as timer:
                    mensaje_descomprimido = descomprimir(mensaje_desencriptado)
                section_names.append("Descompresión")
                execution_times.append(timer.elapsed)
            except Exception as exc:
                print(f"Advertencia: no fue posible descomprimir el mensaje: {exc}")
        else:
            print("Error al extraer el mensaje.")

        # ============================================================
        # DETENER MONITOR GLOBAL Y OBTENER ESTADÍSTICAS
        # ============================================================
        global_stats = global_monitor.stop()
        all_samples = global_monitor.get_samples()

        print("\n" + "=" * 70)
        print("📊 RESUMEN DE RECURSOS - EJECUCIÓN COMPLETA")
        print("=" * 70)
        global_monitor.print_stats(global_stats)
        global_monitor.cleanup()

        # Tiempo de ejecución global
        global_execution_time = time.time() - global_start_time
        print(f"\nTiempo de ejecución global: {global_execution_time:.4f} segundos")

        # Métricas
        print("\n------------Métricas------------")
        mse_val, psnr_val = mse_psnr(arreglo_audio_original, arreglo_audio_modificado)
        distorsion_val = distorsion(arreglo_audio_original, arreglo_audio_modificado)
        chi2_stat, chi2_p, ks_stat, ks_p, mann_u, mann_p = invisibilidad(
            arreglo_audio_original, arreglo_audio_modificado
        )
        entropia_original, entropia_modificada = entropia(
            arreglo_audio_original, arreglo_audio_modificado
        )
        correlacion_val = correlacion_cruzada(
            arreglo_audio_original, arreglo_audio_modificado
        )
        media_orig, media_mod, std_orig, std_mod = analisis_componentes(
            arreglo_audio_original, arreglo_audio_modificado
        )

        print("\n------------Visualizaciones------------")
        print("Generando gráficas...")

        # Visualizaciones
        plot_audio_waveforms(
            arreglo_audio_original,
            arreglo_audio_modificado,
            0,
            len(arreglo_audio_original),
        )
        plot_audio_histograms(
            arreglo_audio_original,
            arreglo_audio_modificado,
            0,
            len(arreglo_audio_original),
        )
        plot_audio_spectrograms(ruta_audio, ruta_audio_modificado)
        plot_audio_difference(
            arreglo_audio_original,
            arreglo_audio_modificado,
            0,
            len(arreglo_audio_original),
        )

        # Gráfica de recursos detallada con todas las muestras
        plot_resource_usage_detailed(all_samples, section_markers)

        plot_execution_times(section_names, execution_times)
        plot_frequency_distribution(
            arreglo_audio_original, arreglo_audio_modificado, sample_rate
        )
        plot_audio_waveforms_librosa(ruta_audio, ruta_audio_modificado)

        # Ejecutar ataques si se solicita
        if args.attacks:
            with TimerContextManager("Módulo de ataques") as timer:
                resultados_ataques = ejecutar_ataques(
                    ruta_audio_modificado,
                    inicio_segmento,
                    fin_segmento,
                    len(mensaje_bits),
                    sequential,
                )
            section_names.append("Módulo de ataques")
            execution_times.append(timer.elapsed)

        metrics = {
            "mse": float(mse_val),
            "psnr_db": float(psnr_val),
            "distorsion": float(distorsion_val),
            "invisibilidad": {
                "chi2_stat": float(chi2_stat),
                "chi2_p": float(chi2_p),
                "ks_stat": float(ks_stat),
                "ks_p": float(ks_p),
                "mann_whitney_u": float(mann_u),
                "mann_whitney_p": float(mann_p),
            },
            "entropia_nats": {
                "original": float(entropia_original),
                "modificado": float(entropia_modificada),
            },
            "correlacion_cruzada": float(correlacion_val),
            "analisis_componentes": {
                "media_original": float(media_orig),
                "media_modificado": float(media_mod),
                "std_original": float(std_orig),
                "std_modificado": float(std_mod),
            },
        }

        exportar_entrega_profesoras(
            salida_dir=salida_dir,
            data_dir=data_dir,
            plots_dir=plots_dir,
            ruta_audio=ruta_audio,
            ruta_audio_modificado=ruta_audio_modificado,
            mensaje_comprimido=mensaje_comprimido,
            mensaje_extraido=mensaje_desencriptado,
            mensaje_descomprimido=mensaje_descomprimido,
            mensaje_bits=mensaje_bits,
            llave=llave,
            inicio_segmento=inicio_segmento,
            fin_segmento=fin_segmento,
            sample_rate=sample_rate,
            global_execution_time=global_execution_time,
            section_names=section_names,
            execution_times=execution_times,
            metrics=metrics,
            sequential=sequential,
            resultados_ataques=resultados_ataques,
        )
    finally:
        sys.stdout = stdout_original
        sys.stderr = stderr_original
        log_file.close()


if __name__ == "__main__":
    main()
