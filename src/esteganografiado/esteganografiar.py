import wave
import numpy as np
from src.utils.utils import get_least_significant_bits
from src.utils.caos import mapa_logistico, generar_secuencia_aleatoria
from src.utils.chaos_mod_enum import ChaosMod

def cargar_archivo_wav(filename):
  """Cargar un archivo de audio en formato WAV y retornar un arreglo de numpy con los datos de audio.

  Args:
      filename (str): Ruta del archivo de audio en formato WAV a cargar

  Returns:
      numpy.array: Arreglo de numpy con los datos de audio del archivo WAV
  """
  with wave.open(filename, 'rb') as wav_file:
    # Obtener los parámetros del archivo de audio WAV
    n_frames = wav_file.getnframes()
    # Leer los datos de audio del archivo WAV
    audio_data = wav_file.readframes(n_frames)
    # Convertir los datos de audio a un arreglo de numpy con valores enteros de 16 bits
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
  return audio_array

def guardar_archivo_wav(filename, audio_array, params):
  """Guardar un arreglo de numpy con los datos de audio en un archivo WAV.

  Args:
      filename (str): Ruta del archivo WAV a guardar los datos de audio
      audio_array (numpy.array): Arreglo de numpy con los datos de audio a guardar
      params (any): Parámetros del archivo WAV (número de canales, frecuencia de muestreo, profundidad de bits, etc.)
  """
  with wave.open(filename, 'wb') as wav_file:
    # Establecer los parámetros del archivo WAV (número de canales, frecuencia de muestreo, profundidad de bits, etc.)
    wav_file.setparams(params)
    # Escribir los datos de audio en el archivo WAV (convertir el arreglo de numpy a bytes)
    wav_file.writeframes(audio_array.tobytes())

def insertar_mensaje_segmento_lsb_sequential(segment_array, message_bits, num_least_significant_bits=1):
  """Insertar un mensaje en los bits menos significativos de un arreglo de segmentos de audio.

  Args:
      segment_array (numpy.array): Arreglo de segmentos de audio en formato de 16 bits (int16)
      message_bits (str): Cadena de bits con el mensaje a insertar en los segmentos de audio
      num_least_significant_bits (int, optional): Número de bits menos significativos a utilizar para insertar el mensaje. Defaults to 1.

  Returns:
      numpy.array: Arreglo de segmentos de audio con el mensaje esteganografiado
  
  Raises:
      ValueError: Si el mensaje es muy largo para ser insertado en el audio
  """
  modified_segment_array = np.copy(segment_array)
  # Obtener los bits menos significativos de cada segmento de audio
  least_significant_bits = get_least_significant_bits(segment_array, num_least_significant_bits)
  #print(f"Tamaño arreglo bits menos significativos (Capacidad en bits): {len(least_significant_bits)}")
  
  
  if len(least_significant_bits) < len(message_bits):
    raise ValueError("El mensaje es muy largo para ser insertado en el audio")
  
  for i in range(len(message_bits)):
    # Obtener el i-ésimo segmento de audio y convertirlo a binario de 16 bits
    sample_bin = format(segment_array[i], 'b').zfill(16)
    print(f"Segmento {i} original: {sample_bin}")
    # Obtener los bits menos significativos del i-ésimo segmento de audio
    lsb = least_significant_bits[i]
    # Reemplazar el bit menos significativo del i-ésimo segmento de audio por el i-ésimo bit del mensaje    
    modified_sample_bin = sample_bin[:-len(lsb)] + message_bits[i]
    # Convertir el i-ésimo segmento de audio modificado a entero
    modified_sample = int(modified_sample_bin, 2)
    # Actualizar el i-ésimo segmento de audio en el arreglo de segmentos de audio modificados
    modified_segment_array[i] = modified_sample
  return modified_segment_array

def insertar_mensaje_segmento_lsb_random(segment_array, message_bits, num_least_significant_bits=1):
  """Insertar un mensaje en los bits menos significativos de un arreglo de segmentos de audio.

  Args:
      segment_array (numpy.array): Arreglo de segmentos de audio en formato de 16 bits (int16)
      message_bits (str): Cadena de bits con el mensaje a insertar en los segmentos de audio
      num_least_significant_bits (int, optional): Número de bits menos significativos a utilizar para insertar el mensaje. Defaults to 1.

  Returns:
      numpy.array: Arreglo de segmentos de audio con el mensaje esteganografiado
  
  Raises:
      ValueError: Si el mensaje es muy largo para ser insertado en el audio
  """
  #print("Mensaje original", message_bits)
  modified_segment_array = np.copy(segment_array)
  
  # Obtener los bits menos significativos de cada segmento de audio
  least_significant_bits = get_least_significant_bits(segment_array, num_least_significant_bits)
  #print(f"Tamaño arreglo bits menos significativos (Capacidad en bits): {len(least_significant_bits)}")
  #print(f"Tamaño mensaje: {len(message_bits)}")
  #print("Least significant bits", type(least_significant_bits))
  
  secuencia_aleatoria = generar_secuencia_aleatoria(
                              ChaosMod.X0.value,
                              ChaosMod.R.value,
                              ChaosMod.N_WARMUP.value,
                              0,
                              len(message_bits),
                              'int')
  
  # print("Secuencia aleatoria generada", secuencia_aleatoria)
  # print("Tamaño secuencia aleatoria", len(secuencia_aleatoria))
  
  if len(least_significant_bits) < len(message_bits):
    raise ValueError("El mensaje es muy largo para ser insertado en el audio")
  
  # Insertar el mensaje en los bits menos significativos de los segmentos de audio
  # en las posiciones aleatorias generadas de la secuencia aleatoria
  for i, bit_index in enumerate(secuencia_aleatoria):
    # Obtener el i-ésimo segmento de audio y convertirlo a binario de 16 bits
    sample_bin = format(segment_array[i], 'b').zfill(16)
    # Obtener los bits menos significativos del i-ésimo segmento de audio
    lsb = least_significant_bits[bit_index]
    # Reemplazar el bit menos significativo del i-ésimo segmento de audio por el i-ésimo bit del mensaje    
    modified_sample_bin = sample_bin[:-len(lsb)] + message_bits[i]
    # Convertir el i-ésimo segmento de audio modificado a entero
    modified_sample = int(modified_sample_bin, 2)
    # Actualizar el i-ésimo segmento de audio en el arreglo de segmentos de audio modificados
    modified_segment_array[i] = modified_sample
    # print(f"Posicion aleatoria: {bit_index} - Sample bin: {sample_bin} - bit menos significativo actual: {lsb} - bit menos significativo nuevo: {message_bits[bit_index]} - segmento modificado: {modified_sample_bin}")
    
  # print("SEGMENTO MODIFICADO",modified_segment_array)
  
  return modified_segment_array

def insertar_lsb_caotico(audio_array, message_bits, x0, r, n_warmup):
  """Insertar mensaje en el audio COMPLETO usando posiciones caóticas.

  El mapa logístico genera posiciones únicas distribuidas en todo el audio.
  Para cada bit del mensaje, se modifica el LSB de la muestra en la posición
  caótica correspondiente. Usa operaciones bitwise directas para manejar
  correctamente valores negativos en complemento a dos (int16).

  Args:
      audio_array (numpy.ndarray): Audio completo en formato int16
      message_bits (str): Cadena de bits del mensaje a insertar
      x0 (float): Punto inicial del mapa logístico
      r (float): Parámetro de caos
      n_warmup (int): Iteraciones de calentamiento

  Returns:
      tuple: (audio_modificado, posiciones) donde posiciones es el array de
             índices usados para la inserción

  Raises:
      ValueError: Si el mensaje es más largo que el audio
  """
  from src.utils.caos import generar_posiciones_caoticas

  n_bits = len(message_bits)
  n_muestras = len(audio_array)

  if n_bits > n_muestras:
    raise ValueError(
      f"El mensaje ({n_bits} bits) es más largo que el audio ({n_muestras} muestras)"
    )

  # Generar posiciones caóticas distribuidas en todo el audio
  posiciones = generar_posiciones_caoticas(x0, r, n_warmup, n_bits, n_muestras)

  # Copiar audio para no modificar el original
  audio_mod = np.copy(audio_array)

  # Insertar cada bit del mensaje en la posición caótica correspondiente
  # Usar operaciones bitwise sobre uint16 para manejar correctamente
  # el complemento a dos de int16
  audio_uint16 = audio_mod.view(np.uint16)

  for i in range(n_bits):
    pos = posiciones[i]
    bit = int(message_bits[i])
    # Limpiar LSB y poner el bit del mensaje
    audio_uint16[pos] = (audio_uint16[pos] & 0xFFFE) | bit

  # La vista uint16 modifica el array subyacente, así que audio_mod ya está actualizado
  return audio_mod, posiciones