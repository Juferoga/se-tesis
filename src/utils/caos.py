import numpy as np

def mapa_logistico(x=8, r=3.99):
  """Mapa logístico para generar una secuencia de números pseudoaleatorios en el rango [0, 1] utilizando un valor inicial y un parámetro de caos.
    Función utilizada: x_{n+1} = r * x_n * (1 - x_n)

  Args:
      x (int, optional): valor actual. Defaults to 8.
      r (float, optional): parámetro de caos. Defaults to 3.99.

  Returns:
      float: valor siguiente en la secuencia de números pseudoaleatorios
  """
  return r * x * (1 - x)

def generar_secuencia_aleatoria(x0, r, n_warmup, lim_inf, lim_sup, tipo='float'):
  """Generar una secuencia aleatoria en un rango determinado sin repeticiones utilizando el mapa logístico

  Args:
    x0 (float): valor inicial del mapa logístico (rango: [0, 1])
    r (float): parámetro de caos del mapa logístico (rango: [3.57, 4])
    n_warmup (float): Número de iteraciones para calentar el sistema (alcanzar el estado de equilibrio)
    lim_inf (int): Límite inferior del rango de valores aleatorios
    lim_sup (int): Límite superior del rango de valores aleatorios
    tipo (str): Tipo de valores a generar ('float' o 'int'). Defaults to 'float'.

  Returns:
    array: Arreglo de valores aleatorios en el rango [lim_inf, lim_sup] sin repeticiones
  """
  secuencia_aleatoria = []
  valores_generados = set()
  x = x0
  # Calentar el sistema
  for _ in range(n_warmup):
    x = mapa_logistico(x, r)
  # Generar la secuencia aleatoria sin repeticiones
  #print(lim_sup - lim_inf)
  while len(secuencia_aleatoria) < (lim_sup - lim_inf):
    #print(lim_sup - lim_inf)
    #print(len(secuencia_aleatoria))
    x = mapa_logistico(x, r)
    valor = lim_inf + (x * (lim_sup - lim_inf))
    if tipo == 'int':
      valor = int(valor)
    if valor not in valores_generados:
      valores_generados.add(valor)
      secuencia_aleatoria.append(valor)
  #print(secuencia_aleatoria)

  return secuencia_aleatoria

def generar_llave(x0, r, n_warmup, length):
  """Generar una llave aleatoria utilizando el mapa logístico

  Args:
      x0 (float): valor inicial del mapa logístico (rango: [0, 1])
      r (float): parámetro de caos del mapa logístico (rango: [3.57, 4])
      n_warmup (float): Número de iteraciones para calentar el sistema (alcanzar el estado de equilibrio)
      length (int): Longitud de la llave en bytes

  Returns:
      array: Arreglo de bytes con la llave aleatoria generada por el mapa logístico.
  """
  key_bits = []
  x = x0
  # Calentar el sistema, descartar los primeros valores para que el sistema alcance el estado de equilibrio (caos)
  for _ in range(n_warmup):
    # Calcular el siguiente valor del mapa logístico
    x = mapa_logistico(x, r)
  # Generar la llave aleatoria
  for _ in range(length * 8):
    # Calcular el siguiente valor del mapa logístico
    x = mapa_logistico(x, r)
    # Convertir el valor del mapa logístico a un bit (0 o 1)
    bit = int(x > 0.5)
    # Agregar el bit a la llave
    key_bits.append(bit)
  # Convertir los bits a bytes (para XOR con los bytes del mensaje)
  # packbits: Convierte una matriz de bits en una matriz de bytes (8 bits) (uint8)
  key = np.packbits(key_bits)[:length]
  return key

def generar_posiciones_caoticas(x0, r, n_warmup, n_posiciones, total_muestras):
  """Generar n_posiciones índices ÚNICOS distribuidos en [0, total_muestras)
  usando el mapa logístico.

  A diferencia de generar_secuencia_aleatoria, esta función está optimizada
  para generar posiciones en rangos muy grandes (millones de muestras) y
  retorna un array numpy para mejor rendimiento.

  Args:
      x0 (float): Punto inicial del mapa logístico (rango: (0, 1))
      r (float): Parámetro de caos (rango: [3.57, 4])
      n_warmup (int): Iteraciones de calentamiento
      n_posiciones (int): Cantidad de posiciones únicas a generar
      total_muestras (int): Tamaño total del audio (límite superior exclusivo)

  Returns:
      numpy.ndarray: Array de int64 con n_posiciones índices únicos en [0, total_muestras)
  """
  posiciones = []
  usadas = set()
  x = x0

  # Calentar el sistema
  for _ in range(n_warmup):
    x = mapa_logistico(x, r)

  # Generar posiciones únicas
  while len(posiciones) < n_posiciones:
    x = mapa_logistico(x, r)
    pos = int(x * total_muestras)
    # Asegurar que esté en rango válido
    pos = max(0, min(pos, total_muestras - 1))
    if pos not in usadas:
      usadas.add(pos)
      posiciones.append(pos)

  return np.array(posiciones, dtype=np.int64)