"""Pruebas de la batería NIST SP 800-22 Rev. 1a (Rukhin et al., 2010), implementadas según las fórmulas del estándar.

Cada función recibe un arreglo de bits (0/1) y devuelve el valor p (o una lista de valores p)."""
import numpy as np
from scipy.special import erfc, gammaincc
from scipy.stats import norm


def frecuencia(e):
    n = len(e); s = np.sum(2 * e.astype(np.int64) - 1)
    return float(erfc(abs(s) / np.sqrt(n) / np.sqrt(2)))


def frecuencia_bloques(e, M=128):
    N = len(e) // M; pi = e[: N * M].reshape(N, M).mean(1)
    chi = 4 * M * np.sum((pi - 0.5) ** 2)
    return float(gammaincc(N / 2, chi / 2))


def rachas(e):
    n = len(e); pi = e.mean()
    if abs(pi - 0.5) >= 2 / np.sqrt(n):
        return 0.0
    v = 1 + np.count_nonzero(e[1:] != e[:-1])
    return float(erfc(abs(v - 2 * n * pi * (1 - pi)) / (2 * np.sqrt(2 * n) * pi * (1 - pi))))


def racha_mas_larga(e):
    n = len(e)
    if n >= 750000:
        M, K, vmin, pis = 10000, 6, 10, [0.0882, 0.2092, 0.2483, 0.1933, 0.1208, 0.0675, 0.0727]
    elif n >= 6272:
        M, K, vmin, pis = 128, 5, 4, [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]
    else:
        M, K, vmin, pis = 8, 3, 1, [0.2148, 0.3672, 0.2305, 0.2266]
    N = n // M; nu = np.zeros(K + 1)
    for b in e[: N * M].reshape(N, M):
        d = np.diff(np.concatenate(([0], b, [0])))
        L = int((np.where(d == -1)[0] - np.where(d == 1)[0]).max()) if b.any() else 0
        nu[min(max(L - vmin, 0), K)] += 1
    pis = np.array(pis)
    chi = np.sum((nu - N * pis) ** 2 / (N * pis))
    return float(gammaincc(K / 2, chi / 2))


def sumas_acumuladas(e):
    n = len(e); x = 2 * e.astype(np.int64) - 1
    res = []
    for seq in (x, x[::-1]):
        z = np.max(np.abs(np.cumsum(seq)))
        k1 = np.arange(int((-n / z + 1) // 4), int((n / z - 1) // 4) + 1)
        k2 = np.arange(int((-n / z - 3) // 4), int((n / z - 1) // 4) + 1)
        p = 1 - np.sum(norm.cdf((4 * k1 + 1) * z / np.sqrt(n)) - norm.cdf((4 * k1 - 1) * z / np.sqrt(n))) \
              + np.sum(norm.cdf((4 * k2 + 3) * z / np.sqrt(n)) - norm.cdf((4 * k2 + 1) * z / np.sqrt(n)))
        res.append(float(p))
    return res


def fourier(e):
    n = len(e); x = 2 * e.astype(np.float64) - 1
    m = np.abs(np.fft.fft(x))[: n // 2]
    T = np.sqrt(np.log(1 / 0.05) * n)
    N0 = 0.95 * n / 2; N1 = np.count_nonzero(m < T)
    d = (N1 - N0) / np.sqrt(n * 0.95 * 0.05 / 4)
    return float(erfc(abs(d) / np.sqrt(2)))


def _psi2(e, m):
    if m <= 0:
        return 0.0
    n = len(e); ext = np.concatenate((e, e[: m - 1])).astype(np.int64)
    idx = np.zeros(n, dtype=np.int64)
    for i in range(m):
        idx = (idx << 1) | ext[i: i + n]
    c = np.bincount(idx, minlength=2 ** m)
    return float((2 ** m / n) * np.sum(c.astype(np.float64) ** 2) - n)


def _phi(e, m):
    n = len(e); ext = np.concatenate((e, e[: m - 1])).astype(np.int64)
    idx = np.zeros(n, dtype=np.int64)
    for i in range(m):
        idx = (idx << 1) | ext[i: i + n]
    c = np.bincount(idx, minlength=2 ** m) / n
    c = c[c > 0]
    return float(np.sum(c * np.log(c)))


def entropia_aproximada(e, m=10):
    n = len(e); ap = _phi(e, m) - _phi(e, m + 1)
    chi = 2 * n * (np.log(2) - ap)
    return float(gammaincc(2 ** (m - 1), chi / 2))


def serial(e, m=16):
    p0, p1, p2 = _psi2(e, m), _psi2(e, m - 1), _psi2(e, m - 2)
    d1, d2 = p0 - p1, p0 - 2 * p1 + p2
    return [float(gammaincc(2 ** (m - 2), d1 / 2)), float(gammaincc(2 ** (m - 3), d2 / 2))]


PRUEBAS = {"Frecuencia (monobit)": frecuencia, "Frecuencia en bloques": frecuencia_bloques, "Rachas": rachas,
           "Racha más larga de unos en un bloque": racha_mas_larga, "Sumas acumuladas": sumas_acumuladas,
           "Transformada discreta de Fourier": fourier, "Entropía aproximada": entropia_aproximada, "Serial": serial}
