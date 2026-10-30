import hashlib
import struct

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
  """Genera el flujo de clave de `length` bytes a partir de la clave K = (x0, r, N).

  Los parámetros de dos órbitas del mapa logístico se derivan de K con SHA-512
  (derivar_parametros); en cada órbita se descartan N iteraciones (transitorio) y cada
  valor se binariza con un umbral en 0.5. El bit del flujo es el XOR de los bits de
  ambas órbitas, de modo que el estado interno del generador (dos órbitas) es mayor
  que el espacio de clave.

  Returns:
      array: Arreglo de bytes (uint8) con el flujo de clave.
  """
  d = derivar_parametros(x0, r, n_warmup)
  bits = np.zeros(length * 8, dtype=np.uint8)
  for x, rr in ((d["x1"], d["r1"]), (d["x2"], d["r2"])):
    for _ in range(n_warmup):
      x = mapa_logistico(x, rr)
    orbita = np.empty(length * 8, dtype=np.uint8)
    for i in range(length * 8):
      x = mapa_logistico(x, rr)
      orbita[i] = x > 0.5
    bits ^= orbita
  return np.packbits(bits)[:length]

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


def _uniforme(b):
  """Convierte 8 bytes en un número de [0, 1) con 53 bits de resolución."""
  return (int.from_bytes(b, "big") >> 11) / float(1 << 53)


def derivar_parametros(x0, r, n_warmup):
  """Deriva los parámetros de las tres órbitas del modelo a partir de la clave K = (x0, r, N).

  Se calcula SHA-512 sobre la representación binaria de la clave (x0 y r en float64 y N en
  entero de 16 bits) y sus 64 bytes se dividen en 8 bloques de 8 bytes, cada uno convertido en
  un número u de [0, 1). Así, cualquier cambio en cualquiera de los tres componentes produce
  órbitas independientes, y N deja de ser un simple desplazamiento de una órbita común.

  Returns:
      dict: (x, r) de las órbitas 1 y 2 del flujo de clave y de la órbita de posiciones.
  """
  h = hashlib.sha512(struct.pack(">ddH", float(x0), float(r), int(n_warmup))).digest()
  u = [_uniforme(h[8 * i:8 * i + 8]) for i in range(8)]
  return {
    "x1": 0.001 + 0.998 * u[0], "r1": 3.99 + 0.01 * u[1],
    "x2": 0.001 + 0.998 * u[2], "r2": 3.99 + 0.01 * u[3],
    "xp": 0.001 + 0.998 * u[4], "rp": 3.99 + 0.0099 * u[5],
  }


def derivar_semillas(x0, r, n_warmup):
  """Semillas de la órbita 1 del flujo de clave y de la órbita de posiciones.

  Returns:
      tuple: ``(x0_k, r_k, n_k, x0_p, r_p, n_p)``; el transitorio de posiciones es N + 1000.
  """
  d = derivar_parametros(x0, r, n_warmup)
  return d["x1"], d["r1"], n_warmup, d["xp"], d["rp"], n_warmup + 1000


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
  """Una clave es válida si el mapa es caótico en las tres órbitas derivadas de ella
  (dos del flujo de clave y una de posiciones), es decir, si los tres exponentes de
  Lyapunov son positivos."""
  d = derivar_parametros(x0, r, n_warmup)
  lam = exponente_lyapunov([d["r1"], d["r2"], d["rp"]])
  return bool(np.all(lam > umbral))
