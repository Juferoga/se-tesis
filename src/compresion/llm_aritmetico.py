"""Compresión sin pérdida con un modelo de lenguaje y codificación aritmética.

El modelo (Llama-2-7b) estima la probabilidad del siguiente token y el codificador
aritmético asigna a cada token un número de bits cercano a -log2 p. El receptor, con
el mismo modelo, reproduce las mismas probabilidades y recupera el texto exacto
(Delétang et al., 2023; Valmeekam et al., LLMZip, 2023).

Para que emisor y receptor obtengan probabilidades idénticas, ambos recorren la
secuencia token a token con caché KV, en CPU, con el mismo número de hilos.
"""
from __future__ import annotations

import os

import torch

MODELO = os.environ.get("MODELO_LM", "NousResearch/Llama-2-7b-hf")
HILOS = 4
DISPOSITIVO = os.environ.get("DEVICE_LM", "cpu")  # "cuda" para GPU (emisor y receptor deben usar el mismo)
PRECISION = 62                 # bits del intervalo del codificador
TOTAL_FREC = 1 << 24           # resolución de las frecuencias enteras
_TOPE = (1 << PRECISION) - 1
_MITAD = 1 << (PRECISION - 1)
_CUARTO = 1 << (PRECISION - 2)

_cache = {}


def cargar_modelo(nombre: str = MODELO):
    if nombre not in _cache:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(HILOS)
        torch.use_deterministic_algorithms(True)
        tok = AutoTokenizer.from_pretrained(nombre)
        mod = AutoModelForCausalLM.from_pretrained(nombre, torch_dtype=getattr(torch, os.environ.get("DTYPE_LM", "bfloat16")))
        mod.to(DISPOSITIVO).eval()
        _cache[nombre] = (tok, mod)
    return _cache[nombre]


def _frecuencias(logits: torch.Tensor) -> list[int]:
    """Convierte logits en frecuencias acumuladas enteras (toda frecuencia >= 1)."""
    p = torch.softmax(logits.float().cpu(), dim=-1)
    n = p.shape[0]
    f = (p * (TOTAL_FREC - n)).floor().to(torch.int64) + 1
    acum = torch.zeros(n + 1, dtype=torch.int64)
    acum[1:] = torch.cumsum(f, 0)
    return acum.tolist()


class _Predictor:
    def __init__(self, mod, bos: int):
        self.mod, self.past = mod, None
        self.siguiente(bos)

    @torch.no_grad()
    def siguiente(self, token: int):
        out = self.mod(torch.tensor([[token]], device=DISPOSITIVO), past_key_values=self.past, use_cache=True)
        self.past = out.past_key_values
        self.logits = out.logits[0, -1]
        self.acum = _frecuencias(self.logits)


def _inicio(tok) -> int:
    """Token de contexto inicial (los modelos sin BOS, como Qwen, usan EOS)."""
    return tok.bos_token_id if tok.bos_token_id is not None else tok.eos_token_id


def _tokens(tok, texto: str) -> list[int]:
    ids = tok.encode(texto, add_special_tokens=False)
    if tok.decode(ids) != texto:
        raise ValueError("el tokenizador no reproduce el texto exacto")
    return ids + [tok.eos_token_id]


def comprimir(texto: str, nombre: str = MODELO, registro: list | None = None) -> bytes:
    """Comprime `texto`. Si se pasa `registro`, agrega (token, probabilidad, puesto) por cada token."""
    tok, mod = cargar_modelo(nombre)
    pred = _Predictor(mod, _inicio(tok))
    bajo, alto, pendientes, bits = 0, _TOPE, 0, []

    def emitir(b):
        nonlocal pendientes
        bits.append(b)
        bits.extend([1 - b] * pendientes)
        pendientes = 0

    for t in _tokens(tok, texto):
        a = pred.acum
        if registro is not None:
            puesto = int((pred.logits > pred.logits[t]).sum().item()) + 1
            registro.append((t, (a[t + 1] - a[t]) / a[-1], puesto))
        rango = alto - bajo + 1
        alto = bajo + rango * a[t + 1] // a[-1] - 1
        bajo = bajo + rango * a[t] // a[-1]
        while True:
            if alto < _MITAD:
                emitir(0)
            elif bajo >= _MITAD:
                emitir(1); bajo -= _MITAD; alto -= _MITAD
            elif bajo >= _CUARTO and alto < _MITAD + _CUARTO:
                pendientes += 1; bajo -= _CUARTO; alto -= _CUARTO
            else:
                break
            bajo, alto = 2 * bajo, 2 * alto + 1
        if t != tok.eos_token_id:
            pred.siguiente(t)
    pendientes += 1
    emitir(0 if bajo < _CUARTO else 1)
    bits.extend([0] * (-len(bits) % 8))
    return bytes(int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8))


def descomprimir(datos: bytes, nombre: str = MODELO, max_tokens: int | None = None) -> str:
    """Descomprime `datos`. Con datos corruptos (ataque o clave errónea) el flujo no termina en
    el token de fin: la decodificación se detiene al agotar los bits o al llegar a `max_tokens`."""
    max_tokens = max_tokens if max_tokens is not None else 64 * len(datos) + 256
    tok, mod = cargar_modelo(nombre)
    pred = _Predictor(mod, _inicio(tok))
    flujo = [int(b) for byte in datos for b in f"{byte:08b}"]
    pos = 0

    def bit():
        nonlocal pos
        pos += 1
        return flujo[pos - 1] if pos <= len(flujo) else 0

    bajo, alto, valor = 0, _TOPE, 0
    for _ in range(PRECISION):
        valor = 2 * valor + bit()
    ids = []
    while True:
        a = pred.acum
        rango = alto - bajo + 1
        objetivo = ((valor - bajo + 1) * a[-1] - 1) // rango
        # búsqueda binaria del token cuyo intervalo contiene el objetivo
        i, j = 0, len(a) - 1
        while j - i > 1:
            m = (i + j) // 2
            if a[m] <= objetivo:
                i = m
            else:
                j = m
        t = i
        alto = bajo + rango * a[t + 1] // a[-1] - 1
        bajo = bajo + rango * a[t] // a[-1]
        while True:
            if alto < _MITAD:
                pass
            elif bajo >= _MITAD:
                bajo -= _MITAD; alto -= _MITAD; valor -= _MITAD
            elif bajo >= _CUARTO and alto < _MITAD + _CUARTO:
                bajo -= _CUARTO; alto -= _CUARTO; valor -= _CUARTO
            else:
                break
            bajo, alto, valor = 2 * bajo, 2 * alto + 1, 2 * valor + bit()
        if t == tok.eos_token_id or pos > len(flujo) + PRECISION or len(ids) >= max_tokens:
            break
        ids.append(t)
        pred.siguiente(t)
    return tok.decode(ids)
