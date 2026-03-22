# Clasificación simple de pruebas (basada en funciones existentes)

## Funcionales mínimas
- **Compresión de texto**: `src.compresion.comprimir.comprimir`
- **Encriptación XOR**: `src.encriptado.encriptar.xor_encriptado` (invocada vía `src.main.convertir_mensaje_a_bits`)
- **Inserción esteganográfica**: `src.esteganografiado.esteganografiar.insertar_mensaje_segmento_lsb_sequential` o `_random` (invocada vía `src.main.insertar_mensaje_en_audio`)
- **Persistencia de audio**: `src.esteganografiado.esteganografiar.guardar_archivo_wav`

## Visualización/evidencia
- Gráficas de señal y espectro desde `src.utils.graficas`.
- Log integral de ejecución en `proceso.log`.

## Métricas reportadas
- MSE y PSNR
- Distorsión
- Invisibilidad (Chi-cuadrado, KS, Mann-Whitney)
- Entropía
- Correlación cruzada
- Análisis de componentes
- BPS

## Fuera de alcance opcional
- Ataques robustos intensivos solo cuando se ejecuta `--attacks`.
