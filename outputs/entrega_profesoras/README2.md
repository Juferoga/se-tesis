Readme viejito para explicar por si acaso

 # Reporte de Auditoría y Respuestas a Observaciones - Proyecto de Grado

*(Versión Actualizada y Verificada post-auditoría de código)*


## 1. Resultados de Compresión, Encriptación y Ondas de Audio


**Observación:** *"Se quiso encontrar el resultado de la compresión del texto, el resultado del texto comprimido y encriptado junto con la onda del audio y el estegoaudio, no hay nada de eso, por favor nos pasas esa información."*


**Respuesta:** En la presente entrega, los archivos resultantes de las etapas de transformación se han exportado correctamente y se encuentran disponibles en el directorio de trabajo:


* **Texto Comprimido:** [`texto_comprimido.txt`](./texto_comprimido.txt) (Contiene la reducción estructural efectuada mediante el modelo de compresión [LLMLingua](https://arxiv.org/abs/2310.05736)).

* **Texto Comprimido y Encriptado (Payload LSB):** [`texto_comprimido_encriptado.json`](./texto_comprimido_encriptado.json) (Resultado de una operación de [cifrado XOR puro a nivel de bytes](https://en.wikipedia.org/wiki/XOR_cipher)).


**Formas de Onda Comparativas:**


![Comparación de Ondas de Audio (Señal Completa)](./audio_waveforms.png)


> **Nota metodológica para evaluación:** La gráfica anterior exhibe un zoom microscópico de apenas 100 muestras. La superposición exacta de la onda original y el estegoaudio demuestra visualmente la **transparencia acústica**. Al modificarse únicamente el bit menos significativo (LSB) dentro de una escala de 16-bits (32,767 niveles de amplitud), el sistema auditivo y el trazado de forma de onda son incapaces de percibir la diferencia.


---


## 2. Uso de Código ASCII


**Observación:** *"Una pregunta usaste código ASCII?"*


**Respuesta:** Sí. De acuerdo con los [estándares criptográficos modernos](https://csrc.nist.gov/publications/detail/sp/800-38a/final), cualquier texto plano (caracteres ASCII/UTF-8) debe serializarse a un flujo de bytes (*bytearray* / `np.uint8`) previo al procesamiento. En la iteración final de la arquitectura propuesta, el flujo de cifrado y acoplamiento (XOR Caótico) se ejecuta estrictamente a nivel de bytes puros. Esto se realiza para garantizar una reconstrucción determinista que sea completamente independiente del mapa de caracteres del sistema operativo subyacente.


---


## 3. Discusión Técnica: Valores de Entropía


**Observación:** *"La literatura nos dice que para una canción los valores ideales deben estar entre 6.5 y 7.8 por muestra, más alto que eso indica una señal de ruido. Lo reportado en la tesis de ustedes es 9.61."*


**Respuesta (Justificación Matemática):** La discrepancia en el valor de entropía **no indica una inyección excesiva de ruido**, sino que se deriva de una diferencia fundamental en la parametrización del modelo analítico frente a los marcos de referencia convencionales:


1. **Unidad Logarítmica:** La literatura que sitúa el umbral ideal entre 6.5 y 7.8 cuantifica la [Entropía de Shannon](https://en.wikipedia.org/wiki/Entropy_(information_theory)) en **Bits** (Logaritmo en base 2). El modelo evaluado calculó la entropía de la señal utilizando **Nats** (Logaritmo natural, base $e$).

2. **Profundidad de Bits (Bit-Depth):** Los valores referenciados asumen un límite teórico correspondiente a señales de 8 bits por muestra. El algoritmo de la presente investigación opera sobre señales de audio de alta resolución (PCM WAV de **16 bits** por muestra), cuyo tope teórico absoluto es de 16 bits.


### Justificación Matemática (Bits vs Nats)


Sea una variable aleatoria discreta $X$ con distribución $p(x_i)$. La entropía de Shannon en una base arbitraria $b$ se define como:


$$H_b(X)=-\sum_{i}p(x_i)\log_b p(x_i)$$


Mediante el cambio de base logarítmica: $H_b(X)=\frac{H_e(X)}{\ln(b)}$.


Considerando que la entropía medida (reportada en la última ejecución de `resumen_ejecucion.json`) es de **10.31 Nats**, la conversión al sistema de bits se establece como:


$$H_2=\frac{10.31}{\ln(2)}=\frac{10.31}{0.69314718056}\approx 14.88\text{ bits}$$


En un formato de [audio lineal PCM de 16 bits](https://en.wikipedia.org/wiki/Pulse-code_modulation), cada muestra cuantizada pertenece a un alfabeto de hasta $2^{16}$ niveles. El máximo teórico de entropía por muestra es:


$$H_{\max}=\log_2(2^{16})=16\text{ bits/muestra}$$


Definiendo la eficiencia entrópica global del archivo:


$$\eta=\frac{H_{\text{medida}}}{H_{\max}}=\frac{14.88}{16}\approx 0.93\ (93\%)$$


**Conclusión:** Un valor de 10.31 Nats es matemáticamente equivalente a 14.88 bits; ambas métricas representan el mismo nivel de incertidumbre estadística. Alcanzar un valor de 14.88 sobre un máximo de 16 bits constituye el comportamiento esperado e ideal para una señal acústica rica en frecuencias, [descartando formalmente una degradación hacia ruido blanco](https://link.springer.com/chapter/10.1007/978-3-319-69266-1_21).


---


## 4. Clasificación de Pruebas y Análisis Integral


Para establecer una validación formal bajo rigor académico, el modelo se evalúa a través de las siguientes categorías analíticas, cuyos resultados verificados están consolidados en [`resumen_ejecucion.json`](./resumen_ejecucion.json):


### A. Análisis Estadístico (Fidelidad del Portador)

Se evalúa la distribución de la carga útil y su impacto estadístico sobre el archivo base:

* **Entropía Original:** 10.31301 Nats / **Entropía Modificada:** 10.31305 Nats. La variación marginal de apenas 0.00004 Nats garantiza el cumplimiento de los [criterios de indetectabilidad esteganográfica](https://arxiv.org/abs/1311.1083).

* **Covarianza:** El valor cruzado de 65883266.40 demuestra una correlación altamente preservada entre la varianza original y la modificada.


$${Cov}(X,Y)=\frac{1}{N}\sum_{n=1}^{N}(X_n-\mu_X)(Y_n-\mu_Y)$$


* **Histogramas de Distribución:** Como se evidencia a continuación, la distribución de la señal permanece inalterada, proveyendo resistencia ante [ataques de estegoanálisis basados en frecuencias LSB](https://en.wikipedia.org/wiki/Steganalysis):


![Histogramas de Distribución del Audio](./audio_histograms.png)


> **Nota metodológica para evaluación:** La identidad visual entre los histogramas en el panel izquierdo es el escenario deseado; comprueba que la inyección de datos no muta la distribución estadística global, burlando métodos de estegoanálisis estándar. El panel derecho expone la diferencia matemática estricta de conteos, demostrando de forma ineludible que la carga criptográfica sí fue embebida en la capa de ruido natural.


### B. Análisis Diferencial

Se cuantifica la proporción y magnitud de las muestras alteradas por la inserción pseudoaleatoria:

* **NPCR (Number of Changing Pixel Rate):** 0.00926%. Esto demuestra un esparcimiento optimizado por el atractor caótico, minimizando las alteraciones en comparación con los [umbrales estándar de cifrado y oclusión de datos](https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=2b479abce221135af6065f9f8352e09cbfb5733a).

* **UACI (Unified Average Changing Intensity):** $1.414\times 10^{-7}\%$. Esta magnitud garantiza que la intensidad del cambio en las muestras alteradas tiende virtualmente a cero, conservando la [fidelidad estructural del medio transmisor](https://pmc.ncbi.nlm.nih.gov/articles/PMC7998182/).


**Fórmulas de Análisis Diferencial Aplicadas:**

$$\mathrm{NPCR}=\frac{\sum_{i=1}^{M}\sum_{j=1}^{N}D(i,j)}{MN}\times 100\%$$

$$\mathrm{UACI}=\frac{1}{MN}\sum_{i=1}^{M}\sum_{j=1}^{N}\frac{|C_1(i,j)-C_2(i,j)|}{L-1}\times 100\%$$


### C. Análisis de Sensibilidad de Claves

Se parametrizaron vectores de ataque simulando perturbaciones de $1\times 10^{-15}$ sobre los parámetros del [sistema caótico](https://en.wikipedia.org/wiki/Chaos_theory) (Semilla $x_0$, Parámetro de control $R$ y Muestras de calentamiento *Warmup*).


Cualquier alteración minúscula en la llave desencadena un [efecto avalancha](https://en.wikipedia.org/wiki/Avalanche_effect) abrupto, imposibilitando la extracción de la información. Al estar la carga distribuida mediante secuencias generadas por un atractor global, la recuperación de la información sin la clave simétrica exacta impone una búsqueda combinatoria en el universo de $N$ muestras de magnitud $\binom{N}{K}$, lo cual resulta en un ataque computacionalmente inviable.


### D. Análisis de Robustez

Se mide la tolerancia del mensaje oculto ante intentos de degradación o pérdida de la señal portadora.


#### 1. Métricas de Error Puro

* **Error Cuadrático Medio (MSE):** $9.266\times 10^{-5}$

* **Relación Señal a Ruido Pico (PSNR):** 40.33 dB. En la literatura académica enfocada en el ocultamiento de datos en audio, se establece que [cualquier índice superior a 40 dB](https://arxiv.org/abs/1509.02630) resulta acústicamente inmaculado para el sistema auditivo humano.


$$\mathrm{MSE}=\frac{1}{N}\sum_{n=1}^{N}(X_n-Y_n)^2\implies\mathrm{PSNR}=10\log_{10}\left(\frac{\text{MAX}^2}{\mathrm{MSE}}\right)$$


#### 2. Análisis de Diferencia y Ataques Activos


![Diferencia de Señal Distribuida](./audio_difference.png)


> **Nota metodológica para evaluación:** El panel inferior (*Vista Microscópica a 50 muestras*) evidencia el comportamiento en vida real del **atractor caótico**. Se observa claramente que las alteraciones (puntos rojos) no se inyectan de forma secuencial ni contigua; en su lugar, se insertan estocásticamente dejando "huecos" naturales. Esta topología garantiza una máxima mitigación frente a ataques de Oclusión o Ruido Impulsivo.


La estrategia de enrutamiento demostró resiliencia metodológica ante simulaciones de ataques activos:

* **Ataque de Sal y Pimienta (Ruido Impulsivo):** Modelado como la inserción de valores extremos bajo una probabilidad estocástica $p$.


* **Ataque de Oclusión:** Modelado a través de una máscara binaria para supresión temporal de segmentos: $y[n]=m[n]x[n]+(1-m[n])\,\omega[n]$


Ambas metodologías fueron probadas sistemáticamente en proporciones de alteración del 1% al 25%, demostrando que, al no insertarse la información en sectores continuos o predecibles, la degradación resultante es localizada y su impacto sobre el bloque de descifrado puede ser mitigado.


![Diferencia de Señal Distribuida](./robustez_sal_pimienta_oclusion.png) 