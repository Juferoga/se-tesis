import numpy as np
from src.utils.utils import get_least_significant_bits
from src.utils.caos import mapa_logistico, generar_secuencia_aleatoria
from src.utils.chaos_mod_enum import ChaosMod

def extraer_mensaje_segmento_lsb_sequential(segment_array, message_length, num_least_significant_bits=1):
  """Extraer un mensaje de los bits menos significativos de un arreglo de segmentos de audio. 
    Para extraer el mensaje, se obtienen los bits menos significativos de cada segmento de audio 
    y se concatenan en una cadena de bits. 
    Luego, se convierte la cadena de bits a una cadena de caracteres (mensaje).

  Args:
    segment_array (numpy.array): Arreglo de segmentos de audio con el mensaje esteganografiado
    message_length (int): Longitud del mensaje a extraer (número de caracteres)
    num_least_significant_bits (int, optional): Número de bits menos significativos a extraer de cada segmento de audio. Defaults to 1.

  Returns:
    tuple: Tupla con los bits extraídos y el mensaje extraído
  """
  # Extraer un mensaje de los bits menos significativos de un arreglo de segmentos de audio
  least_significant_bits = get_least_significant_bits(segment_array, num_least_significant_bits)
  # Obtener los bits menos significativos de cada segmento de audio y concatenarlos en una cadena de bits
  extracted_bits = ''.join(least_significant_bits[:message_length])
  # Convertir la cadena de bits a una cadena de caracteres (mensaje)
  extracted_message = ''.join([chr(int(extracted_bits[i:i+8], 2)) for i in range(0, len(extracted_bits), 8)])
  # Retornar los bits extraídos y el mensaje extraído
  #print("Bits extraídos", extracted_bits)
  #print("Mensaje extraído", extracted_message)
  return extracted_bits, extracted_message

def extraer_mensaje_segmento_lsb_random(modified_segment_array, message_length, num_least_significant_bits=1):
  """Extraer un mensaje oculto en los bits menos significativos de un arreglo de segmentos de audio,
  utilizando la misma secuencia aleatoria que se usó para insertar el mensaje.
  
  Args:
    modified_segment_array (numpy.array): Arreglo de segmentos de audio modificado con el mensaje oculto
    message_length (int): Longitud del mensaje a extraer en bits
    num_least_significant_bits (int, optional): Número de bits menos significativos usados para ocultar el mensaje. Por defecto es 1.
  
  Returns:
    tuple: Tupla que contiene la cadena de bits extraídos y el mensaje original en texto
  """
  # Obtener los bits menos significativos de cada segmento de audio modificado
  least_significant_bits = get_least_significant_bits(modified_segment_array, num_least_significant_bits)
  
  #print(f"Tamaño arreglo bits menos significativos (Capacidad en bits): {len(least_significant_bits)}")
  # Generar la misma secuencia aleatoria utilizada para insertar el mensaje
  secuencia_aleatoria = generar_secuencia_aleatoria(
    ChaosMod.X0.value,
    ChaosMod.R.value,
    ChaosMod.N_WARMUP.value,
    0,
    message_length,
    'int'
  )
  
  #print("Secuencia aleatoria", secuencia_aleatoria)
  
  # Extraer los bits del mensaje de los segmentos de audio en las posiciones aleatorias
  extracted_bits_list = []
  for i, bit_index in enumerate(secuencia_aleatoria):
    # Asegurarse de que el índice no exceda el tamaño del arreglo
    if bit_index < len(least_significant_bits):
      # Obtener el bit menos significativo en la posición aleatoria
      lsb = least_significant_bits[i]
      # Agregar el bit extraído a la lista
      extracted_bits_list.append(lsb)
      # Imprimir el índice del bit, el LSB y la cadena de bits extraídos hasta el momento
      #print(f"Bit index: {bit_index} - LSB: {lsb} - Sample bin: {''.join(extracted_bits_list)}")
    else:
      #print(f"Índice fuera de rango: {bit_index}")
      break
  #0011110001001101101011000010110100101101011110001101000111011100
  #1001010010000101011100000011110010011111110110101011010011001110
  # Unir los bits extraídos en una cadena
  extracted_bits = ''.join(extracted_bits_list)
  #print("Bits extraídos", extracted_bits)
  
  # Convertir los bits extraídos a caracteres (cada 8 bits forman un carácter)
  extracted_message = ''.join([chr(int(extracted_bits[i:i+8], 2)) for i in range(0, len(extracted_bits), 8)])
  #print("Mensaje extraído", extracted_message)
  
  # Retornar los bits extraídos y el mensaje extraído
  return extracted_bits, extracted_message

def extraer_lsb_caotico(audio_array, message_length_bits, x0, r, n_warmup):
  """Extraer un mensaje oculto en posiciones caóticas del audio COMPLETO.

  Regenera las mismas posiciones caóticas usadas durante la inserción y
  lee el LSB de cada posición para reconstruir el mensaje. Usa operaciones
  bitwise sobre la vista uint16 para manejar correctamente el complemento a dos.

  Args:
      audio_array (numpy.ndarray): Audio completo en formato int16
      message_length_bits (int): Longitud del mensaje en bits
      x0 (float): Punto inicial del mapa logístico (mismo que en inserción)
      r (float): Parámetro de caos (mismo que en inserción)
      n_warmup (int): Iteraciones de calentamiento (mismo que en inserción)

  Returns:
      tuple: (bits_extraidos_str, mensaje_extraido_str)
  """
  from src.utils.caos import generar_posiciones_caoticas

  n_muestras = len(audio_array)

  # Regenerar las mismas posiciones caóticas
  posiciones = generar_posiciones_caoticas(x0, r, n_warmup, message_length_bits, n_muestras)

  # Leer LSBs usando vista uint16 (correcto para complemento a dos)
  audio_uint16 = audio_array.view(np.uint16)

  extracted_bits_list = []
  for pos in posiciones:
    lsb = str(audio_uint16[pos] & 1)
    extracted_bits_list.append(lsb)

  extracted_bits = ''.join(extracted_bits_list)

  # Convertir bits a caracteres (cada 8 bits = 1 byte)
  extracted_message = ''.join([
    chr(int(extracted_bits[i:i+8], 2))
    for i in range(0, len(extracted_bits), 8)
  ])

  return extracted_bits, extracted_message