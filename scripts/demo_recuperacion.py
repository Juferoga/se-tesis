"""Demostración de punta a punta del modelo criptoesteganográfico con compresión neuronal sin pérdida.

  emisor:   texto -> compresión neuronal sin pérdida -> cifrado caótico (XOR) -> LSB caótico en el audio
  receptor: estegoaudio + clave -> extracción LSB -> descifrado -> descompresión -> texto

El receptor corre en un proceso aparte y solo recibe el estegoaudio y la clave (x0, r, N).
La longitud del mensaje viaja cifrada en los primeros 16 bits.
"""
import hashlib, math, os, sys, time, wave
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("MODELO_LM", "Qwen/Qwen2.5-1.5B")
os.environ.setdefault("DTYPE_LM", "float32")

import numpy as np
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.compresion import llm_aritmetico as la
from src.encriptado.encriptar import xor_encriptado
from src.esteganografiado.desesteganografiar import extraer_lsb_caotico
from src.esteganografiado.esteganografiar import cargar_archivo_wav, guardar_archivo_wav, insertar_lsb_caotico
from src.utils.caos import derivar_semillas, generar_llave
from src.utils.chaos_mod_enum import ChaosMod

c = Console()
ANCHO = 100
PAUSA = os.environ.get("PAUSA", "1") == "1" and sys.stdin.isatty()
SALIDA = RAIZ / "outputs" / "demo_recuperacion"
SALIDA.mkdir(parents=True, exist_ok=True)
ESTEGO = SALIDA / "estegoaudio.wav"
X0, R, N = ChaosMod.X0.value, ChaosMod.R.value, ChaosMod.N_WARMUP.value
_, _, _, X0_P, R_P, N_P = derivar_semillas(X0, R, N)
MODELO = os.environ["MODELO_LM"].split("/")[-1]

# Colores del mapa de bits por token
ESCALA = [(1, "green", "< 1 bit: la red lo adivinó"), (4, "yellow", "1-4 bits"),
          (8, "dark_orange", "4-8 bits"), (math.inf, "red", "> 8 bits: la red no lo esperaba")]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pausa():
    if PAUSA:
        c.input("[dim]   ⏎ Enter para continuar...[/]")


def explicar(titulo, cuerpo, color="blue"):
    c.print(Panel(cuerpo, title=f"[bold]{titulo}[/]", border_style=color, width=ANCHO, padding=(1, 2)))


def color_bits(b):
    return next(col for lim, col, _ in ESCALA if b < lim)


def _fila(nombre, pasos, color, activo):
    t = Text(f"{nombre:<9}", style=f"bold {color}")
    for i, p in enumerate(pasos):
        t.append(f" {p} ", style=f"bold reverse {color}" if activo == i else color)
        if i < len(pasos) - 1:
            t.append("→")
    return t


def esquema(activo=None):
    """Sin argumento: ambas filas. 0-4: solo la del emisor; 10-14: solo la del receptor."""
    e = _fila("EMISOR", ["Texto", "1. Compresión", "2. Cifrado", "3. LSB caótico", "Estegoaudio"], "cyan",
              activo if activo is not None and activo < 10 else None)
    r = _fila("RECEPTOR", ["Estegoaudio", "3. Extracción", "2. Descifrado", "1. Descompresión", "Texto"], "magenta",
              activo - 10 if activo is not None and activo >= 10 else None)
    if activo is None:
        return Group(e, Text(), r)
    return e if activo < 10 else r


def emisor():
    c.clear()
    c.rule("[bold]Modelo criptoesteganográfico sobre audio · demostración[/]")
    explicar("¿Qué se va a demostrar?", Group(
        "El emisor oculta un poema dentro de un archivo de audio. El receptor, en un programa aparte que "
        "solo recibe el audio y la clave, debe recuperar el poema [bold]exacto, byte a byte[/].\n",
        esquema(), Text("\nLa clave K = (x₀, r, N) la comparten emisor y receptor por un canal seguro, "
        "igual que la red neuronal, que debe ser la misma en ambos lados.", style="dim")))
    pausa()

    original = (RAIZ / "data" / "data_to_hide.txt").read_bytes()
    texto = original.decode("utf-8")
    c.print(Panel(texto, title=f"Mensaje original · {len(original)} bytes · {len(texto)} caracteres",
                  border_style="cyan", width=ANCHO))
    pausa()

    # ---------- 1. Compresión ----------
    c.rule("[bold cyan]EMISOR · 1. Compresión neuronal sin pérdida[/]")
    c.print(esquema(1))
    explicar("¿Cómo comprime la red neuronal?", (
        f"[bold]1.[/] Se usa un modelo de lenguaje ({MODELO}, una red neuronal tipo Transformer entrenada con texto). "
        "Lee el mensaje token a token (un token es una palabra o un trozo de palabra) y, [bold]antes de cada token, "
        "estima la probabilidad de todos los tokens posibles[/].\n\n"
        "[bold]2.[/] Un [bold]codificador aritmético[/] convierte esas probabilidades en bits: un token con "
        "probabilidad p cuesta cerca de −log₂(p) bits. Si la red lo esperaba (p = 0.9) cuesta 0.15 bits; "
        "si la sorprendió (p = 0.001) cuesta 10 bits.\n\n"
        "[bold]3.[/] El receptor tiene [bold]la misma red[/]: reproduce las mismas probabilidades y, con los bits, "
        "sabe exactamente qué token era. Por eso [bold green]no se pierde nada[/].\n\n"
        "[dim]Diferencia con LLMLingua: LLMLingua [bold]borra[/] los tokens predecibles (se pierden y no se pueden "
        "recuperar); aquí esos mismos tokens se [bold]conservan[/] y cuestan muy pocos bits.\n"
        "Referencia: Delétang et al. (2023), «Language Modeling Is Compression», ICLR 2024.[/]"))
    pausa()

    with c.status("[bold]Cargando la red neuronal..."):
        tok, _ = la.cargar_modelo()
    registro = []
    with c.status("[bold]Comprimiendo: la red evalúa cada token del poema..."):
        t0 = time.time(); comprimido = la.comprimir(texto, registro=registro); t_c = time.time() - t0

    ids = [t for t, _, _ in registro[:-1]]          # el último es el token de fin
    piezas, previo = [], ""
    for i in range(len(ids)):
        actual = tok.decode(ids[: i + 1])
        piezas.append(actual[len(previo):]); previo = actual
    bits = [-math.log2(p) for _, p, _ in registro]

    mapa = Text()
    for pieza, b in zip(piezas, bits):
        mapa.append(pieza, style=f"bold {color_bits(b)}")
    leyenda = Text("\n")
    for _, col, desc in ESCALA:
        leyenda.append("■ ", style=col); leyenda.append(desc + "   ")
    c.print(Panel(Group(mapa, leyenda), title="Costo de cada token en bits (mapa del poema)", border_style="cyan", width=ANCHO))
    pausa()

    t = Table(title="Primeros 15 tokens: lo que «pensó» la red", header_style="bold", width=ANCHO)
    t.add_column("Token"); t.add_column("Probabilidad que le dio la red", justify="right")
    t.add_column("Puesto entre los " + f"{len(tok):,}" + " posibles", justify="right"); t.add_column("Bits usados", justify="right")
    for pieza, (_, p, puesto), b in list(zip(piezas, registro, bits))[:15]:
        t.add_row(repr(pieza), f"{100*p:.2f} %", f"{puesto}°", f"[{color_bits(b)}]{b:.2f}[/]")
    c.print(t)
    primeros = sum(1 for _, _, k in registro if k == 1)
    resumen = Table(show_header=False, width=ANCHO, box=None)
    resumen.add_row("Tokens del poema", f"{len(ids)}")
    resumen.add_row("Tokens que la red adivinó en primer lugar", f"{primeros} ({100*primeros/len(registro):.0f} %)")
    resumen.add_row("Bits promedio por carácter", f"{8*len(comprimido)/len(texto):.2f}  [dim](sin comprimir: 8 bits por byte UTF-8)[/]")
    resumen.add_row("[bold]Resultado[/]", f"[bold]{len(original)} → {len(comprimido)} bytes ({100*len(comprimido)/len(original):.1f} % del original) en {t_c:.0f} s[/]")
    c.print(Panel(resumen, border_style="green", width=ANCHO))
    pausa()

    # ---------- 2. Cifrado ----------
    c.rule("[bold cyan]EMISOR · 2. Cifrado caótico[/]")
    c.print(esquema(2))
    carga = len(comprimido).to_bytes(2, "big") + comprimido
    llave = generar_llave(X0, R, N, len(carga))
    cifrado = np.asarray(xor_encriptado(np.frombuffer(carga, dtype=np.uint8), llave), dtype=np.uint8)
    explicar("Cifrado con el mapa logístico", (
        f"Con la clave K = (x₀ = {X0}, r = {R}, N = {N}) el mapa logístico x ← r·x·(1−x) genera un flujo de bits "
        "pseudoaleatorio; cada byte se combina con él mediante XOR. Se agregan 2 bytes al inicio con la longitud del mensaje.\n\n"
        f"Comprimido: [cyan]{comprimido[:16].hex( )} …[/]\n"
        f"Cifrado:    [yellow]{bytes(cifrado[2:18]).hex( )} …[/]"))
    pausa()

    # ---------- 3. Esteganografía ----------
    c.rule("[bold cyan]EMISOR · 3. Esteganografía LSB en posiciones caóticas[/]")
    c.print(esquema(3))
    bits_msg = "".join(np.unpackbits(cifrado).astype(str).tolist())
    ruta = RAIZ / "data" / "audio_test.wav"
    audio = cargar_archivo_wav(str(ruta))
    with wave.open(str(ruta), "rb") as wf:
        params = wf.getparams()
    with c.status("[bold]Ocultando los bits en el audio..."):
        estego, _ = insertar_lsb_caotico(audio, bits_msg, X0_P, R_P, N_P)
        guardar_archivo_wav(str(ESTEGO), estego, params)
    cambiadas = int((audio.astype(np.int64) != estego.astype(np.int64)).sum())
    explicar("Ocultamiento en el audio", (
        "Cada bit cifrado reemplaza el bit menos significativo (LSB) de una muestra del audio, en posiciones "
        "elegidas por otra órbita del mapa logístico derivada de la misma clave.\n\n"
        f"Bits ocultos: [bold]{len(bits_msg)}[/] · muestras del audio: {len(audio):,} · "
        f"muestras modificadas: [bold]{cambiadas}[/] ({100*cambiadas/len(audio):.4f} %), cada una en ±1."), "cyan")
    c.print(f"[bold]Se envía solo:[/] {ESTEGO.relative_to(RAIZ)}   [dim](el receptor ya conoce la clave)[/]")
    (SALIDA / "sha256_original.txt").write_text(sha(original))
    pausa()


def receptor():
    c.rule("[bold magenta]RECEPTOR · programa independiente: recibe solo el estegoaudio y la clave[/]")
    estego = cargar_archivo_wav(str(ESTEGO))
    c.print(esquema(11))
    bits_l, _ = extraer_lsb_caotico(estego, 16, X0_P, R_P, N_P)
    cab = xor_encriptado(np.packbits(np.array([int(b) for b in bits_l], dtype=np.uint8)), generar_llave(X0, R, N, 2))
    n = int.from_bytes(bytes(np.asarray(cab, dtype=np.uint8).tolist()), "big")
    bits, _ = extraer_lsb_caotico(estego, 8 * (n + 2), X0_P, R_P, N_P)
    c.print(f"[green]✓[/] 3. Extracción LSB: con la clave se regeneran las mismas posiciones y se leen {len(bits)} bits")
    c.print(esquema(12))
    cifrado = np.packbits(np.array([int(b) for b in bits], dtype=np.uint8))
    comprimido = bytes(np.asarray(xor_encriptado(cifrado, generar_llave(X0, R, N, n + 2)), dtype=np.uint8).tolist())[2:]
    c.print(f"[green]✓[/] 2. Descifrado: el mismo flujo caótico con XOR devuelve los {len(comprimido)} bytes comprimidos")
    c.print(esquema(13))
    with c.status("[bold]Cargando la misma red neuronal..."):
        la.cargar_modelo()
    with c.status("[bold]Descomprimiendo: la red reproduce sus predicciones y el decodificador elige cada token..."):
        t0 = time.time(); texto = la.descomprimir(comprimido); t_d = time.time() - t0
    recuperado = texto.encode("utf-8")
    c.print(f"[green]✓[/] 1. Descompresión: {len(comprimido)} → {len(recuperado)} bytes en {t_d:.0f} s")
    c.print(Panel(texto, title=f"Mensaje recuperado · {len(recuperado)} bytes", border_style="magenta", width=ANCHO))
    pausa()

    original = (RAIZ / "data" / "data_to_hide.txt").read_bytes()
    h_o, h_r = (SALIDA / "sha256_original.txt").read_text(), sha(recuperado)
    t = Table(title="Verificación (el original solo se usa aquí, para comparar)", header_style="bold", show_lines=True, width=ANCHO)
    t.add_column("Prueba"); t.add_column("Resultado")
    t.add_row("SHA-256 del original", h_o)
    t.add_row("SHA-256 del recuperado", h_r)
    t.add_row("Bytes diferentes", str(sum(x != y for x, y in zip(original, recuperado)) + abs(len(original) - len(recuperado))))
    c.print(t)
    c.print("[dim]SHA-256 es una huella digital: si cambia un solo bit del texto, la huella es completamente distinta.[/]")
    if recuperado == original and h_o == h_r:
        c.print(Panel("[bold green]MENSAJE RECUPERADO AL 100 %: idéntico al original, byte a byte[/]", border_style="green", width=ANCHO))
    else:
        c.print(Panel("[bold red]EL MENSAJE RECUPERADO NO ES IDÉNTICO[/]", border_style="red", width=ANCHO))
        sys.exit(1)


if __name__ == "__main__":
    {"emisor": emisor, "receptor": receptor}[sys.argv[1]]()
