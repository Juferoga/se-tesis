from enum import Enum

class ChaosMod(Enum):
  """Enum for chaos module. 

  Attributes:
    X0 (float): Punto inicial
    R (float): Parámetro de caos
    N_WARMUP (int): Número de iteraciones para 'calentar' el sistema, 
      descartar los primeros valores para que el 
      sistema alcance el estado de equilibrio (caos)
  """
  X0 = 0.123456
  R = 3.999952
  N_WARMUP = 100
  