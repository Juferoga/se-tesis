import numpy as np
import scipy.io.wavfile as wav
import librosa
import librosa.display
import soundfile as sf
import os
import time
from pydub import AudioSegment
from scipy.signal import butter, lfilter, resample
from scipy import ndimage
from src.utils.metricas import (
    mse_psnr,
    distorsion,
    invisibilidad,
    entropia,
    TimerContextManager,
)
from src.esteganografiado.desesteganografiar import extraer_lsb_caotico


class AudioAttacks:
    """Clase para realizar ataques a audio esteganografiado y evaluar su robustez

    Esta clase contiene métodos para aplicar diferentes tipos de ataques a un
    archivo de audio esteganografiado y evaluar si el mensaje oculto puede ser
    recuperado después del ataque.
    """

    def __init__(self, input_file, output_dir="attacks_output"):
        """Inicializar la clase de ataques de audio

        Args:
            input_file (str): Ruta al archivo de audio esteganografiado
            output_dir (str): Directorio donde se guardarán los archivos de audio atacados
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.sr, self.audio = wav.read(input_file)
        self.original_audio = np.copy(self.audio)

        # Crear directorio de salida si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def add_noise(self, noise_level=0.005):
        """Aplicar ataque de ruido gaussiano

        Args:
            noise_level (float): Nivel de ruido a añadir (como proporción de la amplitud máxima)

        Returns:
            str: Ruta del archivo de audio con ruido
        """
        print("\n=== Aplicando ataque de ruido gaussiano ===")
        with TimerContextManager("Ataque de ruido") as timer:
            # Convertir audio a float para evitar desbordamiento
            audio_float = self.audio.astype(np.float32)
            max_amplitude = np.max(np.abs(audio_float))

            # Generar ruido gaussiano
            noise = np.random.normal(0, noise_level * max_amplitude, self.audio.shape)
            noisy_audio = audio_float + noise

            # Volver a convertir a int16 con clipping
            noisy_audio = np.clip(noisy_audio, -32768, 32767).astype(np.int16)

            # Guardar el audio con ruido
            output_file = os.path.join(
                self.output_dir, f"noisy_audio_{noise_level}.wav"
            )
            wav.write(output_file, self.sr, noisy_audio)

            # Calcular métricas
            mse, psnr = mse_psnr(self.original_audio, noisy_audio)
            dist = distorsion(self.original_audio, noisy_audio)

            print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
            print(f"Nivel de ruido: {noise_level}")
            print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
            print(f"Distorsión: {dist:.4f}")

        return output_file, noisy_audio

    def compress_decompress(self, output_format="mp3", quality=128):
        """Aplicar ataque de compresión lossy

        Comprime el audio a un formato con pérdida y luego lo descomprime de nuevo

        Args:
            output_format (str): Formato de compresión ('mp3', 'ogg', etc.)
            quality (int): Calidad de compresión en kbps

        Returns:
            str: Ruta del archivo de audio comprimido/descomprimido
        """
        print(
            f"\n=== Aplicando ataque de compresión {output_format.upper()} ({quality}kbps) ==="
        )
        with TimerContextManager(f"Ataque de compresión {output_format}") as timer:
            compressed_file = os.path.join(
                self.output_dir, f"compressed_audio.{output_format}"
            )
            decompressed_file = os.path.join(
                self.output_dir, f"decompressed_audio_{output_format}_{quality}.wav"
            )

            # Comprimir el audio
            audio = AudioSegment.from_wav(self.input_file)
            audio.export(compressed_file, format=output_format, bitrate=f"{quality}k")

            # Descomprimir el audio
            decompressed_audio = AudioSegment.from_file(
                compressed_file, format=output_format
            )
            decompressed_audio.export(decompressed_file, format="wav")

            # Cargar el audio descomprimido para análisis
            _, attacked_audio = wav.read(decompressed_file)

            # Si los tamaños difieren, recortar o expandir para hacer la comparación
            if len(attacked_audio) > len(self.original_audio):
                attacked_audio = attacked_audio[: len(self.original_audio)]
            elif len(attacked_audio) < len(self.original_audio):
                pad_width = len(self.original_audio) - len(attacked_audio)
                attacked_audio = np.pad(attacked_audio, (0, pad_width), "constant")

            # Calcular métricas
            mse, psnr = mse_psnr(self.original_audio, attacked_audio)
            dist = distorsion(self.original_audio, attacked_audio)

            print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
            print(f"Formato: {output_format}, Calidad: {quality}kbps")
            print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
            print(f"Distorsión: {dist:.4f}")

        return decompressed_file, attacked_audio

    def low_pass_filter(self, cutoff=3000, order=5):
        """Aplicar ataque de filtro paso bajo

        Args:
            cutoff (int): Frecuencia de corte en Hz
            order (int): Orden del filtro

        Returns:
            str: Ruta del archivo de audio filtrado
        """
        print(f"\n=== Aplicando ataque de filtro paso bajo ({cutoff}Hz) ===")
        with TimerContextManager("Ataque de filtrado") as timer:
            nyquist = 0.5 * self.sr
            normal_cutoff = cutoff / nyquist
            b, a = butter(order, normal_cutoff, btype="low", analog=False)
            filtered_audio = lfilter(b, a, self.audio)

            # Convertir a int16 con clipping
            filtered_audio = np.clip(filtered_audio, -32768, 32767).astype(np.int16)

            # Guardar el audio filtrado
            output_file = os.path.join(
                self.output_dir, f"filtered_audio_{cutoff}Hz.wav"
            )
            wav.write(output_file, self.sr, filtered_audio)

            # Calcular métricas
            mse, psnr = mse_psnr(self.original_audio, filtered_audio)
            dist = distorsion(self.original_audio, filtered_audio)

            print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
            print(f"Frecuencia de corte: {cutoff}Hz, Orden: {order}")
            print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
            print(f"Distorsión: {dist:.4f}")

        return output_file, filtered_audio

    def resampling(self, downsample_factor=2):
        """Aplicar ataque de remuestreo

        Reduce la frecuencia de muestreo y luego la restaura

        Args:
            downsample_factor (int): Factor de submuestreo

        Returns:
            str: Ruta del archivo de audio remuestreado
        """
        print(f"\n=== Aplicando ataque de remuestreo (factor {downsample_factor}) ===")
        with TimerContextManager("Ataque de remuestreo") as timer:
            # Convertir a float para el procesamiento
            audio_float = self.audio.astype(np.float32)

            # Reducir la frecuencia de muestreo
            num_samples = len(audio_float)
            downsampled = resample(audio_float, num_samples // downsample_factor)

            # Restaurar la frecuencia de muestreo original
            resampled = resample(downsampled, num_samples)

            # Convertir a int16 con clipping
            resampled = np.clip(resampled, -32768, 32767).astype(np.int16)

            # Guardar el audio remuestreado
            output_file = os.path.join(
                self.output_dir, f"resampled_audio_x{downsample_factor}.wav"
            )
            wav.write(output_file, self.sr, resampled)

            # Calcular métricas
            mse, psnr = mse_psnr(self.original_audio, resampled)
            dist = distorsion(self.original_audio, resampled)

            print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
            print(f"Factor de submuestreo: {downsample_factor}")
            print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
            print(f"Distorsión: {dist:.4f}")

        return output_file, resampled

    def time_stretching(self, stretch_factor=1.1):
        """Aplicar ataque de estiramiento temporal

        Args:
            stretch_factor (float): Factor de estiramiento (>1 para alargar, <1 para acortar)

        Returns:
            str: Ruta del archivo de audio estirado
        """
        print(
            f"\n=== Aplicando ataque de estiramiento temporal (factor {stretch_factor}) ==="
        )
        with TimerContextManager("Ataque de estiramiento") as timer:
            try:
                # Cargar el audio con librosa para manipulación avanzada
                y, sr = librosa.load(self.input_file, sr=None, mono=False)

                # Determinar si el audio es mono o estéreo
                if len(y.shape) > 1:  # Estéreo (librosa usa formato de canal primero)
                    # Procesar cada canal por separado y asegurar que tengan la misma longitud después
                    ch1_stretched = librosa.effects.time_stretch(
                        y[0], rate=1 / stretch_factor
                    )
                    ch2_stretched = librosa.effects.time_stretch(
                        y[1], rate=1 / stretch_factor
                    )

                    # Encontrar la longitud mínima entre ambos canales
                    min_length = min(len(ch1_stretched), len(ch2_stretched))

                    # Recortar ambos canales a la misma longitud
                    ch1_stretched = ch1_stretched[:min_length]
                    ch2_stretched = ch2_stretched[:min_length]

                    # Combinar los canales en una matriz estéreo
                    stretched = np.stack((ch1_stretched, ch2_stretched))
                else:  # Mono
                    stretched = librosa.effects.time_stretch(y, rate=1 / stretch_factor)

                # Ajustar el audio estirado para que tenga la misma duración que el original
                target_length = (
                    len(self.original_audio)
                    if len(self.original_audio.shape) == 1
                    else len(self.original_audio[:, 0])
                )

                if len(stretched.shape) > 1:  # Estéreo
                    current_length = len(stretched[0])
                    if current_length > target_length:
                        # Recortar si es más largo
                        stretched = stretched[:, :target_length]
                    elif current_length < target_length:
                        # Rellenar con ceros si es más corto
                        pad_width = target_length - current_length
                        stretched = np.pad(
                            stretched, ((0, 0), (0, pad_width)), "constant"
                        )
                else:  # Mono
                    current_length = len(stretched)
                    if current_length > target_length:
                        # Recortar si es más largo
                        stretched = stretched[:target_length]
                    elif current_length < target_length:
                        # Rellenar con ceros si es más corto
                        pad_width = target_length - current_length
                        stretched = np.pad(stretched, (0, pad_width), "constant")

                # Guardar el audio estirado
                output_file = os.path.join(
                    self.output_dir, f"stretched_audio_x{stretch_factor}.wav"
                )
                sf.write(
                    output_file,
                    stretched.T if len(stretched.shape) > 1 else stretched,
                    sr,
                )

                # Convertir a int16 para comparar con original
                if len(stretched.shape) > 1:  # Estéreo
                    # Librosa usa formato de canal primero, wav usa canal último
                    stretched_int16 = np.clip(
                        stretched.T * 32767, -32768, 32767
                    ).astype(np.int16)
                else:  # Mono
                    stretched_int16 = np.clip(stretched * 32767, -32768, 32767).astype(
                        np.int16
                    )

                # Asegurarse de que la forma coincida con el original
                if (
                    len(self.original_audio.shape) > 1
                    and len(stretched_int16.shape) == 1
                ):
                    # Si original es estéreo pero processed es mono, duplicar el canal
                    stretched_int16 = np.column_stack(
                        (stretched_int16, stretched_int16)
                    )
                elif (
                    len(self.original_audio.shape) == 1
                    and len(stretched_int16.shape) > 1
                ):
                    # Si original es mono pero processed es estéreo, usar solo un canal
                    stretched_int16 = stretched_int16[:, 0]

                # Calcular métricas
                mse, psnr = mse_psnr(self.original_audio, stretched_int16)
                dist = distorsion(self.original_audio, stretched_int16)

                print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
                print(f"Factor de estiramiento: {stretch_factor}")
                print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
                print(f"Distorsión: {dist:.4f}")

            except Exception as e:
                print(f"Error en time_stretching: {e}")
                return None, np.copy(self.original_audio)

        return output_file, stretched_int16

    def amplitude_scaling(self, scale_factor=0.8):
        """Aplicar ataque de escalado de amplitud

        Args:
            scale_factor (float): Factor de escalado de amplitud

        Returns:
            str: Ruta del archivo de audio escalado
        """
        print(
            f"\n=== Aplicando ataque de escalado de amplitud (factor {scale_factor}) ==="
        )
        with TimerContextManager("Ataque de escalado") as timer:
            # Convertir a float para el procesamiento
            audio_float = self.audio.astype(np.float32)

            # Escalar la amplitud
            scaled_audio = audio_float * scale_factor

            # Convertir de nuevo a int16 con clipping
            scaled_audio = np.clip(scaled_audio, -32768, 32767).astype(np.int16)

            # Guardar el audio escalado
            output_file = os.path.join(
                self.output_dir, f"scaled_audio_x{scale_factor}.wav"
            )
            wav.write(output_file, self.sr, scaled_audio)

            # Calcular métricas
            mse, psnr = mse_psnr(self.original_audio, scaled_audio)
            dist = distorsion(self.original_audio, scaled_audio)

            print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
            print(f"Factor de escalado: {scale_factor}")
            print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
            print(f"Distorsión: {dist:.4f}")

        return output_file, scaled_audio

    def echo_addition(self, delay=0.3, decay=0.6):
        """Aplicar ataque de adición de eco

        Args:
            delay (float): Retardo del eco en segundos
            decay (float): Factor de decaimiento del eco (0-1)

        Returns:
            str: Ruta del archivo de audio con eco
        """
        print(
            f"\n=== Aplicando ataque de adición de eco (delay={delay}s, decay={decay}) ==="
        )
        with TimerContextManager("Ataque de eco") as timer:
            # Convertir a float para el procesamiento
            audio_float = self.audio.astype(np.float32)

            # Crear eco
            delay_samples = int(delay * self.sr)
            echo = np.zeros_like(audio_float)
            echo[delay_samples:] = audio_float[:-delay_samples] * decay

            # Añadir eco al audio original
            echoed_audio = audio_float + echo

            # Normalizar para evitar clipping
            max_val = np.max(np.abs(echoed_audio))
            if max_val > 32767:
                echoed_audio = echoed_audio * (32767 / max_val)

            # Convertir a int16
            echoed_audio = np.clip(echoed_audio, -32768, 32767).astype(np.int16)

            # Guardar el audio con eco
            output_file = os.path.join(
                self.output_dir, f"echoed_audio_{delay}s_{decay}.wav"
            )
            wav.write(output_file, self.sr, echoed_audio)

            # Calcular métricas
            mse, psnr = mse_psnr(self.original_audio, echoed_audio)
            dist = distorsion(self.original_audio, echoed_audio)

            print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
            print(f"Delay: {delay}s, Decay: {decay}")
            print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
            print(f"Distorsión: {dist:.4f}")

        return output_file, echoed_audio

    def bit_reduction(self, bits=12):
        """Aplicar ataque de reducción de bits

        Args:
            bits (int): Número de bits a utilizar (menos que 16)

        Returns:
            str: Ruta del archivo de audio con reducción de bits
        """
        print(f"\n=== Aplicando ataque de reducción de bits ({bits} bits) ===")
        with TimerContextManager("Ataque de reducción de bits") as timer:
            # Convertir a float para el procesamiento
            audio_float = self.audio.astype(np.float32) / 32768.0

            # Reducir la profundidad de bits
            quant_factor = 2.0**bits
            reduced_audio = np.floor(audio_float * quant_factor) / quant_factor

            # Convertir de nuevo a int16
            reduced_audio = (reduced_audio * 32768).astype(np.int16)

            # Guardar el audio con reducción de bits
            output_file = os.path.join(
                self.output_dir, f"bitreduced_audio_{bits}bits.wav"
            )
            wav.write(output_file, self.sr, reduced_audio)

            # Calcular métricas
            mse, psnr = mse_psnr(self.original_audio, reduced_audio)
            dist = distorsion(self.original_audio, reduced_audio)

            print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
            print(f"Bits: {bits}")
            print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
            print(f"Distorsión: {dist:.4f}")

        return output_file, reduced_audio

    def add_salt_pepper_noise(self, proportion=0.05):
        """Aplicar ataque de sal y pimienta sobre todo el audio."""
        print(f"\n=== Aplicando ataque sal y pimienta ({proportion * 100:.1f}%) ===")
        with TimerContextManager("Ataque sal y pimienta") as timer:
            attacked_audio = np.copy(self.audio)
            n = len(attacked_audio)
            n_afectados = int(n * proportion)

            indices = np.random.choice(n, n_afectados, replace=False)
            mitad = n_afectados // 2
            attacked_audio[indices[:mitad]] = 32767
            attacked_audio[indices[mitad:]] = -32768

            output_file = os.path.join(self.output_dir, f"salt_pepper_{proportion}.wav")
            wav.write(output_file, self.sr, attacked_audio.astype(np.int16))

            mse, psnr = mse_psnr(self.original_audio, attacked_audio)
            dist = distorsion(self.original_audio, attacked_audio)

            print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
            print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
            print(f"Distorsión: {dist:.4f}")

        return output_file, attacked_audio.astype(np.int16)

    def occlusion_attack(self, proportion=0.10):
        """Aplicar ataque de oclusión sobre todo el audio."""
        print(f"\n=== Aplicando ataque de oclusión ({proportion * 100:.1f}%) ===")
        with TimerContextManager("Ataque de oclusión") as timer:
            attacked_audio = np.copy(self.audio)
            n = len(attacked_audio)
            block_size = int(n * proportion)
            start = np.random.randint(0, max(1, n - block_size))
            attacked_audio[start : start + block_size] = 0

            output_file = os.path.join(self.output_dir, f"occlusion_{proportion}.wav")
            wav.write(output_file, self.sr, attacked_audio.astype(np.int16))

            mse, psnr = mse_psnr(self.original_audio, attacked_audio)
            dist = distorsion(self.original_audio, attacked_audio)

            print(f"Tiempo de ataque: {timer.elapsed:.4f} segundos")
            print(f"MSE: {mse:.4f}, PSNR: {psnr:.4f} dB")
            print(f"Distorsión: {dist:.4f}")

        return output_file, attacked_audio.astype(np.int16)

    def evaluate_message_recovery(
        self,
        attacked_audio,
        inicio_segmento,
        fin_segmento,
        mensaje_bits_length,
        sequential=False,
        x0=0.123456,
        r=3.999952,
        n_warmup=100,
    ):
        """Evaluar si el mensaje puede ser recuperado después del ataque

        Args:
            attacked_audio (numpy.array): Audio atacado
            inicio_segmento (int): Posición de inicio del segmento con el mensaje
            fin_segmento (int): Posición final del segmento con el mensaje
            mensaje_bits_length (int): Longitud del mensaje en bits
            sequential (bool): Si el mensaje fue insertado secuencialmente o no

        Returns:
            tuple: (éxito de recuperación (bool), número de bits correctos, porcentaje de bits correctos)
        """
        try:
            print("\n--- Intentando recuperar mensaje ---")

            # Evaluación unificada: extraer SIEMPRE con método caótico sobre TODO el audio
            # (se ignoran inicio_segmento, fin_segmento y sequential por compatibilidad)
            if len(attacked_audio) < mensaje_bits_length:
                print(
                    "Error: El segmento extraído es demasiado corto para contener el mensaje."
                )
                return False, 0, 0

            bits_extraidos, _ = extraer_lsb_caotico(
                attacked_audio, mensaje_bits_length, x0, r, n_warmup
            )

            bits_originales, _ = extraer_lsb_caotico(
                self.original_audio, mensaje_bits_length, x0, r, n_warmup
            )

            # Contar bits correctos
            bits_correctos = sum(
                1 for a, b in zip(bits_originales, bits_extraidos) if a == b
            )
            porcentaje_correctos = (bits_correctos / mensaje_bits_length) * 100

            print(f"Bits totales: {mensaje_bits_length}")
            print(f"Bits correctos: {bits_correctos}")
            print(f"Porcentaje de bits correctos: {porcentaje_correctos:.2f}%")

            # Criterio de éxito: más del 95% de bits correctos
            exito = porcentaje_correctos > 95
            if exito:
                print("✅ Mensaje recuperado exitosamente")
            else:
                print("❌ No se pudo recuperar el mensaje correctamente")

            return exito, bits_correctos, porcentaje_correctos

        except Exception as e:
            print(f"Error al intentar recuperar el mensaje: {e}")
            return False, 0, 0

    def run_all_attacks(
        self,
        inicio_segmento,
        fin_segmento,
        mensaje_bits_length,
        sequential=False,
        x0=0.123456,
        r=3.999952,
        n_warmup=100,
    ):
        """Ejecutar todos los ataques y evaluar la robustez

        Args:
            inicio_segmento (int): Posición de inicio del segmento con el mensaje
            fin_segmento (int): Posición final del segmento con el mensaje
            mensaje_bits_length (int): Longitud del mensaje en bits
            sequential (bool): Si el mensaje fue insertado secuencialmente o no

        Returns:
            dict: Resultados de todos los ataques
        """
        resultados = {}

        print("\n==================================================")
        print("INICIANDO BATERÍA DE ATAQUES")
        print("==================================================")

        # Ataque de ruido
        for nivel in [0.001, 0.005, 0.01, 0.05]:
            _, audio_atacado = self.add_noise(noise_level=nivel)
            exito, bits, porcentaje = self.evaluate_message_recovery(
                audio_atacado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits_length,
                sequential,
                x0,
                r,
                n_warmup,
            )
            resultados[f"ruido_{nivel}"] = {
                "exito": exito,
                "bits_correctos": bits,
                "porcentaje": porcentaje,
            }

        # Ataque de compresión
        for formato, calidad in [("mp3", 128), ("mp3", 64), ("ogg", 64)]:
            _, audio_atacado = self.compress_decompress(
                output_format=formato, quality=calidad
            )
            exito, bits, porcentaje = self.evaluate_message_recovery(
                audio_atacado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits_length,
                sequential,
                x0,
                r,
                n_warmup,
            )
            resultados[f"compresion_{formato}_{calidad}"] = {
                "exito": exito,
                "bits_correctos": bits,
                "porcentaje": porcentaje,
            }

        # Ataque de filtrado
        for cutoff in [8000, 5000, 3000]:
            _, audio_atacado = self.low_pass_filter(cutoff=cutoff)
            exito, bits, porcentaje = self.evaluate_message_recovery(
                audio_atacado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits_length,
                sequential,
                x0,
                r,
                n_warmup,
            )
            resultados[f"filtrado_{cutoff}"] = {
                "exito": exito,
                "bits_correctos": bits,
                "porcentaje": porcentaje,
            }

        # Ataque de remuestreo
        for factor in [2, 4]:
            _, audio_atacado = self.resampling(downsample_factor=factor)
            exito, bits, porcentaje = self.evaluate_message_recovery(
                audio_atacado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits_length,
                sequential,
                x0,
                r,
                n_warmup,
            )
            resultados[f"remuestreo_{factor}"] = {
                "exito": exito,
                "bits_correctos": bits,
                "porcentaje": porcentaje,
            }

        # Ataque de estiramiento temporal
        for factor in [1.05, 1.1]:
            _, audio_atacado = self.time_stretching(stretch_factor=factor)
            exito, bits, porcentaje = self.evaluate_message_recovery(
                audio_atacado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits_length,
                sequential,
                x0,
                r,
                n_warmup,
            )
            resultados[f"estiramiento_{factor}"] = {
                "exito": exito,
                "bits_correctos": bits,
                "porcentaje": porcentaje,
            }

        # Ataque de escalado de amplitud
        for factor in [0.8, 1.2]:
            _, audio_atacado = self.amplitude_scaling(scale_factor=factor)
            exito, bits, porcentaje = self.evaluate_message_recovery(
                audio_atacado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits_length,
                sequential,
                x0,
                r,
                n_warmup,
            )
            resultados[f"escalado_{factor}"] = {
                "exito": exito,
                "bits_correctos": bits,
                "porcentaje": porcentaje,
            }

        # Ataque de eco
        _, audio_atacado = self.echo_addition(delay=0.3, decay=0.6)
        exito, bits, porcentaje = self.evaluate_message_recovery(
            audio_atacado,
            inicio_segmento,
            fin_segmento,
            mensaje_bits_length,
            sequential,
            x0,
            r,
            n_warmup,
        )
        resultados["eco_0.3_0.6"] = {
            "exito": exito,
            "bits_correctos": bits,
            "porcentaje": porcentaje,
        }

        # Ataque de reducción de bits
        for bits in [12, 8]:
            _, audio_atacado = self.bit_reduction(bits=bits)
            exito, bits, porcentaje = self.evaluate_message_recovery(
                audio_atacado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits_length,
                sequential,
                x0,
                r,
                n_warmup,
            )
            resultados[f"reduccion_bits_{bits}"] = {
                "exito": exito,
                "bits_correctos": bits,
                "porcentaje": porcentaje,
            }

        # Ataques solicitados en auditoría estricta
        for proportion in [0.01, 0.05, 0.10, 0.25]:
            _, audio_atacado = self.add_salt_pepper_noise(proportion=proportion)
            exito, bits, porcentaje = self.evaluate_message_recovery(
                audio_atacado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits_length,
                sequential,
                x0,
                r,
                n_warmup,
            )
            resultados[f"sal_pimienta_{proportion}"] = {
                "exito": exito,
                "bits_correctos": bits,
                "porcentaje": porcentaje,
            }

        for proportion in [0.01, 0.05, 0.10, 0.25]:
            _, audio_atacado = self.occlusion_attack(proportion=proportion)
            exito, bits, porcentaje = self.evaluate_message_recovery(
                audio_atacado,
                inicio_segmento,
                fin_segmento,
                mensaje_bits_length,
                sequential,
                x0,
                r,
                n_warmup,
            )
            resultados[f"oclusion_{proportion}"] = {
                "exito": exito,
                "bits_correctos": bits,
                "porcentaje": porcentaje,
            }

        return resultados
