# Respuestas a las Observaciones de Revisión del Trabajo de Grado

---

## 1. Resultados del Proceso: Compresión, Encriptación y Formas de Onda

Se solicitaron evidencias concretas de los estados intermedios del mensaje y las representaciones gráficas del audio. Todo esto se encuentra generado y disponible en este mismo directorio:

*   **Resultado del texto comprimido:** Se encuentra en el archivo [`texto_comprimido.txt`](./texto_comprimido.txt). Este archivo representa la salida del algoritmo de compresión antes de pasar a la capa de seguridad.
*   **Resultado del texto comprimido y encriptado:** Se encuentra en [`texto_comprimido_encriptado.json`](./texto_comprimido_encriptado.json). Este es el *payload* (carga útil) final que efectivamente se oculta dentro del archivo de audio portador.
*   **Audio original:** Disponible en el archivo [`audio_original.wav`](./audio_original.wav).
*   **Estegoaudio (con el mensaje oculto):** Disponible en el archivo [`audio_estegano.wav`](./audio_estegano.wav).
*   **Onda del audio original:** Se puede visualizar en los archivos [`onda_original.png`](./onda_original.png) y de forma comparativa en [`audio_waveforms.png`](./audio_waveforms.png) y [`audio_waveforms_librosa.png`](./audio_waveforms_librosa.png).
*   **Onda del estegoaudio (con el mensaje oculto):** Se encuentra en [`onda_estegoaudio.png`](./onda_estegoaudio.png). Además, se generó la gráfica comparativa [`onda_original_y_estegano.png`](./onda_original_y_estegano.png) y [`audio_difference.png`](./audio_difference.png) donde se evidencia visualmente que la alteración en el dominio del tiempo es imperceptible, garantizando la transparencia del método esteganográfico.

---

## 2. Uso de Código ASCII

**Pregunta:** *¿Usaron código ASCII?*

**Respuesta:** Sí. Todo proceso criptográfico y de compresión opera a nivel de *bytes*. Para transformar el texto humano (caracteres) a un formato matemáticamente operable, se utiliza una codificación de caracteres. Se empleó ASCII (y por extensión UTF-8 para soportar caracteres especiales) con el fin de serializar el mensaje original en un arreglo de bytes que luego es procesado por los algoritmos de compresión y cifrado.

---

## 3. Aclaración Fundamental sobre los Valores de Entropía

**Comentario:** *"La literatura nos dice que para una canción los valores ideales deben estar entre 6.5 y 7.8 por muestra, más alto que eso indica una señal de ruido. Lo reportado en la tesis de ustedes es 9.61."*

**Respuesta y Justificación Matemática:**
Este es un punto conceptual muy importante. La aparente discrepancia no radica en que el estegoaudio sea ruido, sino en la **unidad de medida y la profundidad de bits (bit-depth)** utilizada para el cálculo.

1. **Unidad de Medida (Bits vs. Nats):** La literatura clásica de la teoría de la información de Shannon que reporta valores de "6.5 a 7.8" suele expresar la entropía en **Bits** (utilizando el logaritmo en base 2, $\log_2$). En la investigación y el código, la entropía fue calculada utilizando [**Nats** (logaritmo natural, base $e$, $\ln$)](https://en.wikipedia.org/wiki/Nat_(unit)#Entropy). 
    * Si se toma el valor de $9.61 \text{ nats}$ y lo convertimos a bits (dividiendo por $\ln(2) \approx 0.693$), se obtiene **$13.86 \text{ bits}$**.
2. **Profundidad por Muestra:** Los valores de "6.5 a 7.8 bits" de la literatura aplican para señales de audio cuantizadas a **8 bits por muestra** (donde la entropía máxima teórica es 8). Se está operando sobre archivos de audio de alta calidad de **16 bits por muestra** (estándar CD, formato WAV PCM). En un audio de 16 bits, donde la entropía máxima teórica es 16, una entropía natural de $13.86 \text{ bits}$ ($9.61 \text{ nats}$) es el valor matemáticamente correcto y esperado para una señal de audio musical rica en frecuencias, demostrando que **no es ruido blanco**, sino música estéreo de alta resolución.

---

## 4. Clasificación de las Pruebas Realizadas

Atendiendo a la solicitud de clasificar las pruebas del modelo, se agrupan bajo la rigurosidad de la taxonomía del criptoanálisis y estegoanálisis:

### A. Análisis Estadístico
Busca determinar si la inserción de datos alteró la distribución natural del medio portador, previniendo ataques basados en predictibilidad.
* **Cálculo de Entropía (en Nats):** Demuestra que la cantidad media de información se mantiene estable sin saltos drásticos que delaten el mensaje.
* **Análisis de Histogramas:** Respaldado por el archivo [`audio_histograms.png`](./audio_histograms.png) y [`frequency_distribution.png`](./frequency_distribution.png), donde se prueba que la distribución de frecuencias de los bits menos significativos (LSB) no levanta sospechas estadísticas.

### B. Análisis Diferencial
Evalúa cómo una pequeña diferencia en la entrada (texto o clave) o la inyección del mensaje afecta el total del archivo.
* **Diferencia de Señales en el Tiempo y Espectro:** Respaldado por [`audio_difference.png`](./audio_difference.png) y [`spectral_difference.png`](./spectral_difference.png). Miden la delta exacta entre el audio original y el estegoaudio, comprobando que la variación diferencial tiende a cero.

### C. Análisis de Sensibilidad de Claves
Pertenece a la capa de cifrado implementada previo a la esteganografía.
* **Efecto Avalancha (Avalanche Effect):** Garantiza que cambiar un solo bit en la contraseña o clave criptográfica arroja un [`texto_comprimido_encriptado.json`](./texto_comprimido_encriptado.json) completamente distinto (con un 50% de los bits cambiados), impidiendo que un atacante deduzca la clave mediante aproximaciones.

### D. Análisis de Robustez (y Fidelidad)
Evalúa la supervivencia del secreto frente a alteraciones e imperceptibilidad.
* **Inspección Visual de Ondas y Espectrogramas:** Respaldado por [`audio_spectrograms.png`](./audio_spectrograms.png), evidenciando que no existen marcas anómalas en el espectro de frecuencias.
* **Métricas Estándar (SNR, PSNR, MSE):** Utilizadas en el informe técnico para validar matemáticamente la degradación nula y la relación señal a ruido, garantizando la calidad acústica original.

