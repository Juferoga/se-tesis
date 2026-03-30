# Fundamentos Matemáticos para la Evaluación del Sistema de Esteganografía

## Resumen

El presente documento formaliza las métricas matemáticas empleadas para sustentar la calidad criptográfica y perceptual del sistema. Se justifica rigurosamente la interpretación de la entropía en distintas bases logarítmicas, se incorporan los indicadores diferenciales NPCR/UACI, se detallan las métricas de error (MSE, PSNR y covarianza) y se modelan los ataques de ruido impulsivo y oclusión, explicando por qué un esquema LSB guiado por dinámica caótica incrementa la resistencia frente a extracción no autorizada.

---

## 1. Justificación estricta de la entropía: Bits vs Nats

Sea una variable aleatoria discreta $X$ con distribución $p(x_i)$. La entropía de Shannon en base arbitraria $b$ se define como:

$$
H_b(X) = -\sum_{i} p(x_i)\log_b p(x_i).
$$

### 1.1 Conversión de base logarítmica

Por cambio de base,

$$
\log_b(u)=\frac{\ln(u)}{\ln(b)}
$$

y, en consecuencia,

$$
H_b(X)=\frac{H_e(X)}{\ln(b)}.
$$

Casos de interés:

- **Nats** (base $e$):
  $$
  H_{\text{nat}}(X)=H_e(X)=-\sum_i p(x_i)\ln p(x_i).
  $$
- **Bits** (base $2$):
  $$
  H_{\text{bit}}(X)=H_2(X)=-\sum_i p(x_i)\log_2 p(x_i)=\frac{H_e(X)}{\ln(2)}.
  $$

### 1.2 Verificación numérica del valor reportado

Si la entropía medida es $H_e=9.61$ nats, entonces en bits:

$$
H_2=\frac{9.61}{\ln(2)}=\frac{9.61}{0.69314718056}\approx 13.86\ \text{bits}.
$$

Por lo tanto, **$9.61$ nats y $13.86$ bits son el mismo nivel de incertidumbre estadística expresado en unidades distintas**.

### 1.3 Por qué $13.86$ bits es excelente y esperado en PCM de 16 bits

En audio PCM lineal de 16 bits, cada muestra cuantizada pertenece (idealmente) a un alfabeto de hasta $2^{16}$ niveles. El máximo teórico de entropía por muestra es:

$$
H_{\max}=\log_2(2^{16})=16\ \text{bits/muestra}.
$$

No es correcto tomar $8$ como cota superior en este contexto, porque ese límite corresponde a señal de **8 bits** ($2^8$ niveles), no a PCM de 16 bits.

Definiendo eficiencia entrópica:

$$
\eta=\frac{H_{\text{medida}}}{H_{\max}}=\frac{13.86}{16}\approx 0.866\ (86.6\%).
$$

Este resultado es consistente con señales de audio reales: aunque la ocupación del espacio de amplitud es alta, la distribución no es perfectamente uniforme (estructura temporal, contenido armónico, silencios, envolvente dinámica), por lo que $H<16$ en condiciones normales. En consecuencia, **$13.86$ bits/muestra representa un valor alto, técnicamente sólido y esperable para audio PCM 16-bit con alta variabilidad**.

---

## 2. Análisis diferencial: NPCR y UACI

Sean $C_1$ y $C_2$ dos señales/imágenes cifradas o esteganográficas obtenidas con una mínima variación en entrada (p. ej., un bit del mensaje o de la clave), de tamaño $M\times N$.

### 2.1 NPCR (Number of Changing Pixel Rate)

Defínase:

$$
D(i,j)=
\begin{cases}
0, & C_1(i,j)=C_2(i,j),\\
1, & C_1(i,j)\neq C_2(i,j).
\end{cases}
$$

Entonces:

$$
\mathrm{NPCR}=\frac{\sum_{i=1}^{M}\sum_{j=1}^{N} D(i,j)}{MN}\times 100\%.
$$

Un NPCR alto indica fuerte efecto avalancha: pequeñas perturbaciones producen cambios extensivos en la salida.

### 2.2 UACI (Unified Average Changing Intensity)

Para profundidad de cuantización de $L$ niveles (en 8 bits, $L=256$):

$$
\mathrm{UACI}=\frac{1}{MN}\sum_{i=1}^{M}\sum_{j=1}^{N}
\frac{|C_1(i,j)-C_2(i,j)|}{L-1}\times 100\%.
$$

UACI mide la **intensidad promedio** de los cambios, complementando a NPCR (que mide frecuencia de cambio). En conjunto, ambos indicadores validan robustez diferencial frente a ataques que explotan baja sensibilidad de la transformación.

> Nota metodológica: aunque la nomenclatura clásica refiere “pixel”, estas métricas se extienden a muestras de audio o coeficientes transformados mediante la misma formalización discreta.

---

## 3. Métricas de error para imperceptibilidad

Sean $X$ la señal original y $Y$ la señal esteganográfica, ambas de longitud $N$.

### 3.1 MSE (Mean Squared Error)

$$
\mathrm{MSE}=\frac{1}{N}\sum_{n=1}^{N}\big(X_n-Y_n\big)^2.
$$

Un MSE bajo implica distorsión energética reducida introducida por el embebido.

### 3.2 PSNR (Peak Signal-to-Noise Ratio)

Si $MAX$ es el valor máximo representable (p. ej., $MAX=2^{15}-1$ para PCM signed de 16 bits):

$$
\mathrm{PSNR}=10\log_{10}\left(\frac{MAX^2}{\mathrm{MSE}}\right)
=20\log_{10}\left(\frac{MAX}{\sqrt{\mathrm{MSE}}}\right)\ \text{dB}.
$$

PSNR alto indica que el error se mantiene muy por debajo del rango dinámico útil, reforzando la imperceptibilidad.

### 3.3 Covarianza

Sea $\mu_X$ y $\mu_Y$ las medias de $X$ y $Y$:

$$
\operatorname{Cov}(X,Y)=\frac{1}{N}\sum_{n=1}^{N}(X_n-\mu_X)(Y_n-\mu_Y).
$$

Covarianza alta y positiva (acompañada típicamente por alta correlación normalizada) indica preservación de estructura global entre señal original y esteganográfica. Esto respalda que la inserción LSB no altera de forma macroscópica la morfología estadística de la señal portadora.

---

## 4. Modelos matemáticos de ataque y mitigación mediante LSB caótico

## 4.1 Ataque de Sal y Pimienta (ruido impulsivo)

Para una señal discreta $x[n]$, el canal atacado $y[n]$ puede modelarse como:

$$
y[n]=
\begin{cases}
x_{\min}, & \text{con probabilidad } p/2,\\
x_{\max}, & \text{con probabilidad } p/2,\\
x[n], & \text{con probabilidad } 1-p.
\end{cases}
$$

donde $p$ es la densidad de impulsos y $(x_{\min},x_{\max})$ son niveles extremos de cuantización. El ataque corrompe localmente muestras/coeficientes, afectando bits embebidos en posiciones impactadas.

### 4.2 Ataque de oclusión

La oclusión se modela como una máscara binaria $m[n]\in\{0,1\}$:

$$
y[n]=m[n]x[n]+(1-m[n])\,\omega[n],
$$

donde $m[n]=0$ en el segmento ocluido y $\omega[n]$ representa relleno (cero, ruido o valor constante). Equivale a pérdida localizada de información útil para decodificación.

### 4.3 Por qué el LSB guiado por atractor caótico mitiga extracción no autorizada

Sea una secuencia pseudoaleatoria $\{k_t\}$ generada por un sistema caótico inicializado con clave secreta (condiciones iniciales y parámetros). El mapeo de posiciones de embebido se expresa como:

$$
\pi_t = f(k_t) \in \{1,\dots,N\},
$$

donde $\pi_t$ define qué muestra/coeficiente modifica cada bit del mensaje.

La mitigación se sustenta en:

1. **Dispersión espacial/temporal del payload**: el mensaje no queda contiguo ni en posiciones triviales.
2. **Sensibilidad a la clave**: variaciones ínfimas en condiciones iniciales producen secuencias $\{k_t\}$ no correlacionadas (propiedad de sistemas caóticos), imposibilitando reconstrucción sin clave exacta.
3. **Resistencia a análisis estadístico directo de LSB**: la pseudoaleatorización de ubicaciones reduce patrones detectables en ventanas locales fijas.
4. **Tolerancia parcial a ataques locales**: sal-pimienta y oclusión dañan subconjuntos; al estar el mensaje distribuido, la recuperación puede mantenerse si se incorpora redundancia/codificación de canal.

Formalmente, sin conocimiento de la clave, el adversario enfrenta una búsqueda combinatoria sobre subconjuntos de posiciones de tamaño $K$ en un universo de $N$ muestras:

$$
\binom{N}{K},
$$

con complejidad prohibitiva para parámetros realistas, especialmente cuando se añade cifrado del payload previo al embebido.

---

## Conclusión

Las métricas presentadas permiten sostener, con base matemática verificable, que: (i) la entropía observada es coherente con audio PCM de 16 bits y está correctamente expresada tanto en nats como en bits; (ii) NPCR/UACI respaldan sensibilidad diferencial adecuada; (iii) MSE, PSNR y covarianza confirman imperceptibilidad; y (iv) el esquema LSB con direccionamiento caótico ofrece una barrera efectiva frente a extracción no autorizada y degradación local por ataques impulsivos u oclusivos.
