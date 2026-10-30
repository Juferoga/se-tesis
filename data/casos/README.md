# Datos de los casos de estudio adicionales

Copias exactas de los textos y audios usados en los casos de estudio adicionales del artículo
(resultados en `outputs/revision_neuronal/casos/casos.json`, generados con `scripts/casos_estudio_colab.py`).
Los textos coinciden byte a byte con los que se descargaron al ejecutar el script.

## Textos (dominio público)

| Archivo | Obra | Fuente |
|---|---|---|
| `textos/T1_nocturno_silva.txt` | José Asunción Silva, *Nocturno (Oh dulce niña pálida)* | Caso de estudio principal (`data/data_to_hide.txt`) |
| `textos/T2_quijote_cap1_parrafo1.txt` | Miguel de Cervantes, *Don Quijote de la Mancha*, cap. I, primer párrafo | Proyecto Gutenberg, libro n.º 2000 |
| `textos/T3_quijote_cap1_parrafos1a2.txt` | Miguel de Cervantes, *Don Quijote de la Mancha*, cap. I, párrafos 1 y 2 | Proyecto Gutenberg, libro n.º 2000 |
| `textos/T4_soneto18_shakespeare.txt` | William Shakespeare, soneto 18 | Proyecto Gutenberg, libro n.º 1041 |

## Audios

| Archivo | Obra | Licencia |
|---|---|---|
| `audios/Hungarian_Dance_number_5_-_Allegro_in_F_sharp_minor_(string_orchestra).ogg` | J. Brahms, *Danza húngara n.º 5*, US Army Strings ([Musopen](https://musopen.org/music/43805-hungarian-dance-no-5-in-f-sharp-minor-woo-1-string-orchestra-arr/)) | Dominio público |
| `audios/Kevin_MacLeod_-_P_I_Tchaikovsky_Dance_of_the_Sugar_Plum_Fairy.ogg` | P. I. Chaikovski, *Danza del hada de azúcar*, versión de Kevin MacLeod ([Free Music Archive](https://freemusicarchive.org/music/Kevin_MacLeod/Classical_Sampler/Dance_of_the_Sugar_Plum_Fairy)) | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) |
| `audios/5703-47212-0000.ogg` | *Ashiel Mystery - A Detective Story*, cap. 2, narrado por Garth Comira ([LibriSpeech SLR12](https://www.openslr.org/12/)) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

Los audios se distribuyen con la biblioteca librosa (`librosa.ex("brahms")`, `librosa.ex("nutcracker")`, `librosa.ex("libri1")`).
El cuarto audio de los casos de estudio es el del caso principal (`data/audio_test.wav`, ver `data/README.md`).
