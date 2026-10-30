from enum import Enum

class ChaosMod(Enum):
  """Enum for chaos module.

  Attributes:
    X0 (float): Punto inicial (componente secreto de la clave).
    R (float): Parámetro de caos (componente secreto de la clave).
    N_WARMUP (int): Número de iteraciones de calentamiento del mapa logístico.
      A diferencia de versiones previas, N_WARMUP es un **componente secreto de
      la clave** (no un valor público fijo): el emisor lo elige dentro del rango
      [N_WARMUP_MIN, N_WARMUP_MAX]. El valor aquí definido es el usado en esta
      corrida reproducible del artículo; en producción sería aleatorio y secreto.
    N_WARMUP_MIN / N_WARMUP_MAX (int): rango admisible del componente secreto
      N_warmup, usado para cuantificar su aporte al espacio de claves
      (~log2(N_WARMUP_MAX - N_WARMUP_MIN) bits).
  """
  X0 = 0.123456
  R = 3.999952
  # N_warmup como parte secreta de la clave (valor de ejemplo, rango [100, 10000])
  N_WARMUP = 6173
  N_WARMUP_MIN = 100
  N_WARMUP_MAX = 10000
