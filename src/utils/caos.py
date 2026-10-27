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

  # Generar posiciones únicas. Si r cae en una ventana periódica la órbita se
  # vuelve un ciclo y nunca aparecen índices nuevos: se corta con un límite.
  max_iteraciones = 20 * n_posiciones + 10000
  iteraciones = 0
  while len(posiciones) < n_posiciones:
    iteraciones += 1
    if iteraciones > max_iteraciones:
      raise ValueError(
        f"La órbita (x0={x0}, r={r}) no genera {n_posiciones} posiciones distintas: "
        "r está en una ventana periódica del mapa logístico (clave no válida)."
      )
    x = mapa_logistico(x, r)
    pos = int(x * total_muestras)
    # Asegurar que esté en rango válido
    pos = max(0, min(pos, total_muestras - 1))
    if pos not in usadas:
      usadas.add(pos)
      posiciones.append(pos)

  return np.array(posiciones, dtype=np.int64)


def derivar_semillas(x0, r, n_warmup):
  """Deriva DOS semillas independientes a partir de la clave maestra.

  Resuelve el acoplamiento criptográfico de usar una sola secuencia para el
  cifrado y para las posiciones LSB. A partir de la clave maestra
  ``(x0, r, n_warmup)`` se obtienen:

    - Semilla de keystream (cifrado XOR): la clave maestra tal cual.
    - Semilla de posiciones (LSB): derivada de forma determinista y decorrelada,
      de modo que el flujo de cifrado y la elección de posiciones NO comparten la
      misma órbita del mapa logístico.

  Args:
      x0 (float): condición inicial maestra, en (0, 1)
      r (float): parámetro de caos maestro, en [3.57, 4]
      n_warmup (int): calentamiento maestro (componente secreto)

  Returns:
      tuple: ``(x0_k, r_k, n_k, x0_p, r_p, n_p)`` — semillas de keystream (_k) y
             de posiciones (_p).
  """
  # Keystream: clave maestra directa
  x0_k, r_k, n_k = x0, r, n_warmup

  # Posiciones: derivación determinista decorrelada de la maestra.
  x0_p = (x0 * r) % 1.0
  if x0_p <= 0.0 or x0_p >= 1.0:
    x0_p = (x0 + 0.5) % 1.0

  # r_p se mantiene en el régimen FUERTEMENTE caótico [3.99, 3.9999) para máxima
  # dispersión: a r≈3.63 el mapa logístico concentra los valores en bandas y las
  # posiciones se agrupan; cerca de 4 la densidad invariante cubre casi todo (0,1),
  # logrando posiciones LSB repartidas por TODO el audio.
  r_p = 3.99 + ((r * x0) % 1.0) * 0.0099

  n_p = n_warmup + 1000

  return x0_k, r_k, n_k, x0_p, r_p, n_p

def exponente_lyapunov(r, x0=0.3, n_transitorio=20000, n_iter=4000):
  """Exponente de Lyapunov del mapa logístico para uno o varios valores de r.

  λ = (1/n) Σ ln|r(1 − 2x_k)|. Un valor positivo indica comportamiento caótico;
  un valor menor o igual a cero indica que la órbita converge a un ciclo. El
  transitorio es largo porque, cerca del borde de una ventana periódica, la órbita
  puede parecer caótica durante miles de iteraciones antes de caer en el ciclo.
  """
  r = np.atleast_1d(np.asarray(r, dtype=np.float64))
  x = np.full_like(r, x0)
  for _ in range(n_transitorio):
    x = r * x * (1 - x)
  acum = np.zeros_like(r)
  for _ in range(n_iter):
    x = r * x * (1 - x)
    acum += np.log(np.abs(r * (1 - 2 * x)) + 1e-300)
  return acum / n_iter


def clave_valida(x0, r, n_warmup, umbral=0.0):
  """Una clave es válida si el mapa es caótico tanto para el flujo de cifrado (r)
  como para la selección de posiciones (r_p derivado), es decir, si ambos
  exponentes de Lyapunov son positivos."""
  _, r_k, _, _, r_p, _ = derivar_semillas(x0, r, n_warmup)
  lam = exponente_lyapunov([r_k, r_p])
  return bool(np.all(lam > umbral))
