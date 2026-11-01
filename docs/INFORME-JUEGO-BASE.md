# Correcciones del juego base (Victoria 2 v3.04)

Este repositorio **no contiene archivos del juego ni de ningún mod**: son propiedad de sus autores. Solo guarda scripts, herramientas y documentación. Las correcciones se aplican sobre una copia del juego.

UPM queda fuera de este trabajo: se corregirá aparte, más adelante.

## Cómo se aplica

```bash
python -I paquete/base_fix.py "<juego>" "<copia_de_seguridad>" registro.txt
```

Corrige directamente los archivos del juego: no crea ningún mod ni toca `v2game.exe`. Después el juego se abre como siempre, con el launcher o con `v2game.exe`. Antes de cambiar cada archivo guarda el original en la carpeta de copia de seguridad. Si el juego ya está corregido, se niega a aplicarlo otra vez.

## Qué corrige

| Área | Cambio |
|---|---|
| Interfaz | 42 nombres que salían cortados con « ...» en tecnologías, reformas, militar, población y comercio |
| Textos | Errata «Sistesma», 6 textos sin traducir y título de `form_yugoslavia` |
| Textos rotos | 323 filas de texto cambiadas en total, solo en la columna española: comillas de hoja de cálculo que el juego mostraba tal cual, 3 textos cortados por un `;`, variables mal escritas (`$ target$`, `§COUNTRY§`, `$STR_0_0$`, `$TAG_0_0J$`) y frases que decían otra cosa, como el registro que ponía «nos ha declarado la guerra» cuando la declarabas tú |
| Datos | Rumanía y China empezaban 1861 con un partido fuera de fecha; provincia 1396 con dos historias distintas; `HAI_oob.txt` en UTF-8 |
| Economía | Ayuda de la barra superior: aclara que la cifra es la de ayer |
| Rebeldes | `REDUCTION_AFTER_RISEING` de 0 a 2 y `MIL_TO_AUTORISE` de 9 a 9,5 |
| Rendimiento | 25 condiciones reordenadas para evaluar lo barato antes que los bucles `any_*`; misma lógica |

## Causa de las «varias versiones»

El código del menú, como `V2 v3.04 (YYWO)`, es un checksum calculado al arrancar. Según el propio ejecutable incluye `common`, `poptypes`, `events`, `missions`, `units`, `inventions`, `script`, `technologies`, `decisions`, `history/*`, `battleplans`, `map/default.map`, `cache/time` y `v2game.exe`. No incluye `interface`, `gfx`, `localisation` ni `music`.

`cache/time` es una suma de hashes del mapa, idéntica entre equipos, pero se lee **antes** de crear la caché. Por eso la primera vez que el juego arranca en un equipo sale otro código, y hay que abrirlo y cerrarlo una vez:

| Prueba, juego sin corregir | Código |
|---|---|
| Primer arranque, sin caché | `VKEW` |
| Siguientes arranques | `WNVU` |
| `time` alterado | `AECE` |
| Mod instalado sin activar | `WNVU` |

Con las correcciones aplicadas, y con la caché ya creada, el código es `YYWO`. Para jugar juntos, todos deben tener el mismo `v2game.exe` y los mismos archivos corregidos.

## Pruebas realizadas

- Sintaxis de todos los archivos cambiados: sin errores.
- Arranque con `v2game.exe` sin parámetros y con el launcher original: llega al menú con el código `YYWO`, en unos 15 s de carga.
- 8 minutos a velocidad máxima sin parámetros, jugando como Francia: llegó a agosto de 1843 sin crash, sin entradas en `error.log` y con un pico de 1.716 MB.
- En pantalla: nombres de tecnologías completos y ayuda de la barra superior entera.
- Por hashes: de 8.969 archivos originales cambian 24, los mismos que hay en la copia de seguridad. `v2game.exe`, el launcher y todos los archivos de UPM siguen idénticos.
- UPM arranca hasta el menú con su código nuevo, `AAKT`. Antes era `OWVC`, porque hereda archivos del juego base. No se ha jugado una partida con UPM.

## Sin resolver o sin verificar

- **Mapa en blanco en multijugador:** no reproducido. Parece estar en el ejecutable.
- **Mejora de rendimiento:** no medida de forma fiable.
- **Rebeldes en late game:** el cambio no se ha probado en partidas largas.
- **Multijugador real:** no probado con varios jugadores.
- El presupuesto de la barra superior no se corrige, porque el cálculo está en el ejecutable: solo se aclara.
- Los textos en inglés no se han tocado: las correcciones de texto son para el juego en español.
