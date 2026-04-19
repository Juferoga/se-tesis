# Sección 4. Métricas estadísticas y de calidad: formulación y explicación exhaustiva

En esta sección se formalizan las métricas empleadas para cuantificar similitud estadística, error de reconstrucción y calidad de señal entre el audio original y el estegoaudio. Todas las variables se definen explícitamente para evitar ambigüedad metodológica.

## 4.1 Covarianza

La covarianza muestral entre dos señales discretas \(X\) y \(Y\) se define como:

\[
\operatorname{Cov}(X,Y)=\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})
\]

Donde:

- \(n\): número total de observaciones (muestras) comparadas.
- \(x_i\): valor de la muestra \(i\)-ésima de la señal \(X\) (por ejemplo, audio original).
- \(y_i\): valor de la muestra \(i\)-ésima de la señal \(Y\) (por ejemplo, estegoaudio).
- \(\bar{x}\): media aritmética de \(X\), definida como \(\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i\).
- \(\bar{y}\): media aritmética de \(Y\), definida como \(\bar{y}=\frac{1}{n}\sum_{i=1}^{n}y_i\).

Interpretación:

- Si \(\operatorname{Cov}(X,Y)>0\), ambas señales tienden a variar en el mismo sentido.
- Si \(\operatorname{Cov}(X,Y)<0\), tienden a variar en sentido opuesto.
- Si \(\operatorname{Cov}(X,Y)\approx 0\), no hay relación lineal evidente.

Limitación clave: la covarianza depende de la escala de las variables (no está normalizada), por lo que no permite comparar directamente relaciones entre experimentos de distinta amplitud.

## 4.2 Correlación de Pearson

El coeficiente de correlación lineal de Pearson se expresa como:

\[
r_{xy}=\frac{\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})}
{\sqrt{\sum_{i=1}^{n}(x_i-\bar{x})^2}\,\sqrt{\sum_{i=1}^{n}(y_i-\bar{y})^2}}
\]

Equivalencia útil:

\[
r_{xy}=\frac{\operatorname{Cov}(X,Y)}{s_x s_y}
\]

con:

- \(s_x\): desviación estándar muestral de \(X\).
- \(s_y\): desviación estándar muestral de \(Y\).

Rango y significado:

- \(r_{xy}\in[-1,1]\).
- \(r_{xy}=1\): correlación lineal positiva perfecta.
- \(r_{xy}=0\): ausencia de correlación lineal.
- \(r_{xy}=-1\): correlación lineal negativa perfecta.

En el contexto esteganográfico de audio, valores cercanos a 1 son indicativos de alta preservación estructural entre señal original y señal con carga útil.

## 4.3 Error Cuadrático Medio (MSE)

El Error Cuadrático Medio se define como:

\[
\operatorname{MSE}=\frac{1}{n}\sum_{i=1}^{n}(x_i-y_i)^2
\]

Donde:

- \(x_i\): muestra original en la posición \(i\).
- \(y_i\): muestra reconstruida/modificada en la posición \(i\).
- \(n\): cantidad total de muestras.

Interpretación:

- \(\operatorname{MSE}=0\) implica identidad exacta muestra a muestra.
- Cuanto mayor sea MSE, mayor es la energía del error introducido.

El MSE penaliza más fuertemente los errores grandes al elevar al cuadrado la diferencia, por lo que es sensible a picos de distorsión local.

## 4.4 Relación Señal-Ruido de Pico (PSNR)

La métrica PSNR (en decibelios) se expresa como:

\[
\operatorname{PSNR}=10\log_{10}\left(\frac{\operatorname{MAX}_I^2}{\operatorname{MSE}}\right)
\]

Donde:

- \(\operatorname{MAX}_I\): valor máximo posible de amplitud de la señal.
  - Ejemplo en audio normalizado: \(\operatorname{MAX}_I=1\).
  - Ejemplo en representación PCM de 16 bits sin normalizar: \(\operatorname{MAX}_I=32767\).
- \(\operatorname{MSE}\): error cuadrático medio previamente definido.

Interpretación práctica:

- PSNR alto implica ruido embebido bajo respecto a la señal útil.
- PSNR bajo implica degradación perceptible y/o energética significativa.

En audio esteganográfico, se busca un compromiso entre capacidad de ocultamiento y PSNR elevado, de forma que el canal se mantenga perceptualmente transparente sin sacrificar robustez.

---

# Sección 5. Correcciones terminológicas y rigor conceptual

Para garantizar consistencia terminológica y alineación con la literatura de sistemas dinámicos no lineales, se establecen las siguientes correcciones de redacción:

1. **Usar “condiciones iniciales”** en lugar de “triple paramétrico” cuando se hace referencia al estado de partida del sistema caótico.
2. **Mencionar explícitamente un atractor caótico clásico**, por ejemplo el **Atractor de Lorenz**, como referente conceptual para justificar sensibilidad y mezcla dinámica.
3. **Usar “iteraciones a desconocer”** en lugar de “calentamiento”, enfatizando que dichas iteraciones se descartan deliberadamente para eliminar dependencia transitoria y evitar que un atacante reconstruya estados iniciales.

Redacción sugerida para la tesis:

> La secuencia pseudoaleatoria empleada en la selección de posiciones de inserción se obtiene a partir de un sistema caótico sensible a **condiciones iniciales**. Este comportamiento, ampliamente documentado en modelos clásicos como el **Atractor de Lorenz**, garantiza que perturbaciones mínimas en el estado inicial produzcan trayectorias divergentes a medida que avanzan las iteraciones. Adicionalmente, se aplican **iteraciones a desconocer** al inicio de la órbita para suprimir el régimen transitorio y fortalecer la impredecibilidad efectiva de la secuencia utilizada durante el proceso de ocultamiento.

Esta terminología evita ambigüedad y mejora la trazabilidad conceptual entre teoría del caos, seguridad criptográfica y esteganografía.

---

# Sección 6. Efecto avalancha y recuperación fallida

El **efecto avalancha** describe la propiedad por la cual una variación extremadamente pequeña en las condiciones iniciales (o en la clave) produce diferencias masivas en la salida del sistema. En este trabajo, esa propiedad es deseable porque reduce la posibilidad de recuperación del mensaje oculto cuando los parámetros de extracción no coinciden exactamente con los de inserción.

## 6.1 Principio de seguridad

Si dos procesos de extracción difieren mínimamente en estado inicial, orden de iteraciones o semilla, las posiciones reconstruidas para lectura de bits divergen rápidamente. Como consecuencia:

- Se leen bits correctos sólo en las primeras iteraciones.
- Luego aparecen desalineamientos acumulativos.
- El texto extraído se degrada en símbolos erróneos o secuencias sin semántica.

## 6.2 Ejemplos de recuperación fallida de texto

A continuación se muestran ejemplos ilustrativos (no idénticos a un caso único, sino representativos del fenómeno observado):

- **Texto esperado**: `La esteganografía robusta protege la integridad del mensaje oculto.`
- **Extracción con clave casi correcta**: `La estegxnografíx robvsta protege la integridqd del mensahe oculto.`
- **Extracción con condiciones iniciales alteradas**: `L$ e5tega#ogr4f!a r0b?sta p9ot_ge l* in+egridad d_l mensa_e oc$lto.`
- **Extracción con desincronización avanzada**: `Ñ¤7u|kA… q1Zp_>9 mT` (salida prácticamente ininteligible).

La transición desde errores leves hasta colapso semántico ilustra que la seguridad no depende únicamente de cifrado previo, sino también de la sensibilidad dinámica del mecanismo de direccionamiento estocástico.

---

# Sección 7. BER, NC y resiliencia empírica ante ruido impulsivo y oclusión

## 7.1 Bit Error Rate (BER)

La tasa de error de bits se define como:

\[
\operatorname{BER}=\frac{N_e}{N_t}
\]

Donde:

- \(N_e\): número de bits extraídos incorrectamente.
- \(N_t\): número total de bits transmitidos/embebidos y luego extraídos.

Rango:

- \(\operatorname{BER}\in[0,1]\), con 0 ideal y 1 error total.

Guía práctica de aceptación (dependiente de la aplicación):

- Excelente: \(\operatorname{BER}<0.01\)
- Buena: \(0.01\le\operatorname{BER}<0.05\)
- Tolerable con degradación: \(0.05\le\operatorname{BER}<0.15\)
- Crítica: \(\operatorname{BER}\ge0.15\)

## 7.2 Normalized Correlation (NC)

Una formulación habitual de correlación normalizada para secuencias de referencia \(W\) y recuperada \(\hat{W}\) es:

\[
\operatorname{NC}=\frac{\sum_{i=1}^{N} W_i\,\hat{W}_i}
{\sqrt{\sum_{i=1}^{N}W_i^2}\,\sqrt{\sum_{i=1}^{N}\hat{W}_i^2}}
\]

Donde:

- \(N\): longitud de la secuencia comparada.
- \(W_i\): componente \(i\)-ésima de la secuencia de referencia.
- \(\hat{W}_i\): componente \(i\)-ésima de la secuencia recuperada.

Rango:

- En señales no negativas o binarizadas, suele interpretarse en \([0,1]\).
- Valor cercano a 1 indica alta similitud estructural.

Guía práctica:

- Excelente: \(\operatorname{NC}\ge0.98\)
- Buena: \(0.95\le\operatorname{NC}<0.98\)
- Moderada: \(0.90\le\operatorname{NC}<0.95\)
- Baja: \(\operatorname{NC}<0.90\)

## 7.3 Resiliencia empírica ante Sal y Pimienta y Oclusión (5%, 10%, 25%)

Se evaluó la recuperación textual bajo dos perturbaciones: (i) ruido impulsivo tipo **Sal y Pimienta** y (ii) **Oclusión** de segmentos de datos. Los resultados muestran una degradación progresiva pero coherente con el diseño robusto del método.

### a) Perturbación del 5%

- Impacto esperado: errores localizados y esporádicos.
- Comportamiento observado: el mensaje permanece mayormente íntegro; aparecen sustituciones puntuales.

Ejemplo:

- Original: `El sistema mantiene la confidencialidad del mensaje oculto.`
- Recuperado (5%): `El sistema mantiene la confidenzialidad del mensaje oculto.`

Interpretación: legibilidad alta, BER bajo y NC alto.

### b) Perturbación del 10%

- Impacto esperado: incremento de errores de carácter y pérdida parcial de continuidad léxica.
- Comportamiento observado: la oración sigue siendo comprensible por contexto.

Ejemplo:

- Original: `La recuperación robusta depende de la sincronización de claves.`
- Recuperado (10%): `La recupe ración robuxta depende de la sincronizacón de clavfs.`

Interpretación: legibilidad media-alta, BER moderado y NC aún aceptable.

### c) Perturbación del 25%

- Impacto esperado: distorsión severa, fragmentación de palabras y pérdida semántica parcial.
- Comportamiento observado: se conservan islotes de texto legible, pero aumenta el esfuerzo de interpretación.

Ejemplo:

- Original: `La esteganografía propuesta prioriza robustez y transparencia perceptual.`
- Recuperado (25%): `La estegano grafia propu sta priori?a ro bustez y tr nsparencia perceptu l.`

Interpretación: BER elevado y NC reducido, aunque aún con recuperación parcial de contenido.

## 7.4 Conclusión de resiliencia

Los resultados respaldan que el esquema mantiene utilidad práctica ante degradaciones moderadas (5% y 10%), y ofrece recuperación parcial incluso en condiciones adversas (25%). En términos de ingeniería, esto sugiere una arquitectura equilibrada entre invisibilidad, capacidad y robustez, con deterioro gradual en lugar de fallo abrupto.
